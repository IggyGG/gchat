"""Discover source changes without building moving branch names.

The controller queues exact clean production source pairs. Version changes are
committed by the normal release preparation workflow; source-only commits do not
silently reuse an existing store version or overwrite a published artifact.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import time

from release_pair import canonical, identity, next_ios_build_number, validate
from release_coordinator import atomic_json


def coalesce_equivalent_queued(config, ledger):
    """Reclassify undispatched work after the reviewed input inventory changes.

    Only upstream inputs are compared; generated version commits stay immutable.
    A preserved earlier worker/artifact owns its original qualification. This
    neither moves receipts nor promotes an unqualified candidate.
    Called only by the coordinator while it holds its exclusive state lock.
    """
    from release_inputs import fingerprints
    repositories = {p: config[p]['mirror'] for p in ('gchat', 'gcoms')}
    rows = ledger.db.execute('''SELECT c.seq,c.manifest,p.* FROM platforms p
        JOIN candidates c ON c.id=p.candidate ORDER BY c.seq DESC''').fetchall()
    cache = {}
    def inputs(manifest):
        upstream = manifest.get('upstream')
        if not upstream:
            return None  # Manually frozen sources are never inferred equivalent.
        key = canonical(upstream)
        if key not in cache:
            value = fingerprints(repositories, upstream)
            cache[key] = (value['artifacts'], value.get('infrastructure'))
        return cache[key]
    retained = {'building', 'verifying', 'verified', 'publishing', 'submitting',
                'processing', 'in_review', 'available'}
    for row in rows:
        if row['state'] != 'queued':
            continue
        # Even an anomalous queued row with a reserved effect must reconcile it.
        if ledger.db.execute('SELECT 1 FROM effects WHERE candidate=? AND platform=?',
                             (row['candidate'], row['platform'])).fetchone():
            continue
        current = json.loads(row['manifest'])
        current_inputs = inputs(current)
        if current_inputs is None:
            continue
        for previous in rows:
            if (previous['seq'] >= row['seq'] or previous['platform'] != row['platform']
                    or previous['state'] not in retained):
                continue
            baseline = json.loads(previous['manifest'])
            if (baseline['policy'] == current['policy']
                    and inputs(baseline) == current_inputs):
                ledger.transition(row['candidate'], row['platform'], 'superseded',
                    reason='Reviewed application inputs unchanged; retain ' + previous['candidate'])
                break


def discover(config, state, ledger):
    """Read contained mirror clones, fetch main, then freeze exact object IDs.

    Each mirror must be a dedicated bare repository, never a user's checkout.
    These clones contain only GChat/GComs. No reset, rebase or working-tree edits.
    """
    sources = {}
    for project in ('gchat', 'gcoms'):
        root = Path(config[project]['mirror']).resolve()
        if not root.exists():
            root.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(['git', 'clone', '--bare', config[project]['url'], str(root)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
        bare = subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--is-bare-repository'], text=True, timeout=15).strip()
        if bare != 'true': raise ValueError('release discovery requires dedicated bare mirrors')
        subprocess.run(['git', '-C', str(root), 'fetch', '--no-tags', 'origin',
                        'refs/heads/main:refs/heads/main'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
        sources[project] = identity(root, 'refs/heads/main')
    root = Path(config['gchat']['mirror'])
    def read(path):
        return json.loads(subprocess.check_output(['git', '-C', str(root), 'show', sources['gchat']['commit'] + ':' + path]))
    policy = read('release/automation/policy.json')
    upstream = sources.copy()
    def push(candidate):
        for destination in config.get('candidate_remotes', []):
            subprocess.run(['git', '-C', str(root), 'push', destination,
                            candidate['sources']['gchat']['commit'] + ':' + candidate['refs']['gchat']],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
        for destination in config.get('companion_remotes', []):
            subprocess.run(['git', '-C', config['gcoms']['mirror'], 'push', destination,
                            candidate['sources']['gcoms']['commit'] + ':' + candidate['refs']['gcoms']],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
    def reusable(candidate):
        try:
            validate(candidate)
        except ValueError:
            # Earlier controllers reserved overflowing iOS versions. Preserve
            # those rows and refs, but never replay them as new build inputs.
            # Verify the original digest and every other field before accepting
            # this one historical validation exception.
            from release_feed import version
            major, minor, patch = version(candidate['versions']['ios'])
            if major < 1 or not (major > 9999 or minor > 99 or patch > 99):
                raise
            unsigned = {k: v for k, v in candidate.items() if k != 'release_id'}
            if candidate['release_id'] != hashlib.sha256(canonical(unsigned)).hexdigest():
                raise ValueError('release manifest digest mismatch')
            checked = dict(unsigned, versions=dict(candidate['versions'], ios='1.0.1'))
            checked['release_id'] = hashlib.sha256(canonical(checked)).hexdigest()
            validate(checked)
            return False
        return True

    for row in ledger.db.execute('SELECT manifest FROM candidates'):
        previous = json.loads(row[0])
        if not reusable(previous):
            continue
        if previous.get('upstream') == upstream and previous['policy'] == policy:
            push(previous)
            atomic_json(Path(state) / 'incoming' / (previous['release_id'] + '.json'), previous)
            return previous['release_id']
    # New qualification/controller bytes do not reserve new application versions.
    # Keep the original artifact sources and record the new verification revision
    # separately; this observation is not a successful qualification receipt.
    from release_inputs import fingerprints
    repositories = {p: config[p]['mirror'] for p in ('gchat', 'gcoms')}
    current_inputs = fingerprints(repositories, upstream)
    latest = ledger.db.execute('SELECT manifest FROM candidates ORDER BY seq DESC LIMIT 1').fetchone()
    if latest:
        baseline = json.loads(latest[0])
        prior_inputs = fingerprints(repositories, baseline.get('upstream', baseline['sources']))
        if (reusable(baseline) and baseline['policy'] == policy and prior_inputs['artifacts'] == current_inputs['artifacts']
                and prior_inputs.get('infrastructure') == current_inputs.get('infrastructure')):
            atomic_json(Path(state) / 'qualification-needed.json', {
                'schema': 1, 'artifact_release_id': baseline['release_id'],
                'sources': upstream, 'inputs': current_inputs,
                'artifact_inputs_unchanged': True, 'qualification_passed': False,
                'reason': 'Qualification/controller revision; retain original artifact source bindings'})
            if prior_inputs['controller'] != current_inputs['controller']:
                from release_controller import queue, qualification_ref
                observed = Path(state) / 'controller-observed.json'
                previous = json.loads(observed.read_text()) if observed.exists() else {}
                if previous.get('sources') != upstream:
                    atomic_json(observed, {'sources': upstream, 'since': int(time.time())})
                    return baseline['release_id']
                if time.time() - previous['since'] < config.get('settle_seconds', 60):
                    return baseline['release_id']
                intent = queue(state, baseline, upstream, prior_inputs, current_inputs)
                published = Path(state) / 'controller-updates' / intent['id'] / 'ref-published.json'
                if not published.exists():
                    for destination in config.get('candidate_remotes', []):
                        subprocess.run(['git', '-C', str(root), 'push', destination,
                            upstream['gchat']['commit'] + ':' + qualification_ref(intent)],
                            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
                    atomic_json(published, {'source': upstream['gchat'], 'ref': qualification_ref(intent)})
            return baseline['release_id']
    observed_path = Path(state) / 'observed-sources.json'
    observation = {'sources': upstream, 'policy': policy}
    previous_observation = json.loads(observed_path.read_text()) if observed_path.exists() else {}
    if previous_observation.get('identity') != observation:
        atomic_json(observed_path, {'identity': observation, 'since': int(time.time())})
        return None
    if time.time() - previous_observation['since'] < config.get('settle_seconds', 60):
        return None
    from release_prepare import prepare
    from release_feed import version
    previous = [json.loads(row[0]) for row in ledger.db.execute('SELECT manifest FROM candidates')]
    baseline = config['version_floor']
    desktop = max([version(baseline['desktop']), *[version(p['versions']['linux-x86_64']) for p in previous]])
    desktop = '.'.join(map(str, (*desktop[:2], desktop[2] + 1)))
    android = str(max([int(baseline['android']), *[int(p['versions']['android']) for p in previous]]) + 1)
    ios = max([version(baseline['ios']), *[version(p['versions']['ios']) for p in previous]])
    ios = next_ios_build_number('.'.join(map(str, ios)))
    from release_ledger import PLATFORMS
    versions = {p: android if p == 'android' else ios if p == 'ios' else desktop for p in PLATFORMS}
    # A corrected reservation needs a new immutable ref even if its source and
    # policy match an invalid reservation from an earlier controller.
    pair = hashlib.sha256(canonical({'sources': upstream, 'policy': policy, 'versions': versions})).hexdigest()
    branch = 'refs/heads/release/gchat-' + pair[:20]
    commit = prepare(root, sources['gchat']['commit'], sources['gcoms']['commit'], versions, branch)
    sources['gchat'] = identity(root, commit)
    candidate = {'schema': 1, 'sources': sources, 'upstream': upstream, 'versions': versions, 'policy': policy,
                 'input_fingerprints': current_inputs,
                 'refs': {'gchat': branch, 'gcoms': branch}}
    candidate['release_id'] = hashlib.sha256(canonical(candidate)).hexdigest()
    validate(candidate)
    # Reserve before any remote push. A restart reuses this exact candidate;
    # the dispatcher reconciles immutable branch visibility before building.
    ledger.add(candidate)
    atomic_json(Path(state) / 'incoming' / (candidate['release_id'] + '.json'), candidate)
    push(candidate)
    return candidate['release_id']
