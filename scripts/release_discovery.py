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

from release_pair import canonical, identity, validate
from release_coordinator import atomic_json


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
    for row in ledger.db.execute('SELECT manifest FROM candidates'):
        previous = json.loads(row[0])
        if previous.get('upstream') == upstream and previous['policy'] == policy:
            push(previous)
            atomic_json(Path(state) / 'incoming' / (previous['release_id'] + '.json'), previous)
            return previous['release_id']
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
    ios = '.'.join(map(str, (*ios[:2], ios[2] + 1)))
    from release_ledger import PLATFORMS
    versions = {p: android if p == 'android' else ios if p == 'ios' else desktop for p in PLATFORMS}
    pair = hashlib.sha256(canonical({'sources': upstream, 'policy': policy})).hexdigest()
    branch = 'refs/heads/release/gchat-' + pair[:20]
    commit = prepare(root, sources['gchat']['commit'], sources['gcoms']['commit'], versions, branch)
    sources['gchat'] = identity(root, commit)
    candidate = {'schema': 1, 'sources': sources, 'upstream': upstream, 'versions': versions, 'policy': policy,
                 'refs': {'gchat': branch, 'gcoms': branch}}
    candidate['release_id'] = hashlib.sha256(canonical(candidate)).hexdigest()
    validate(candidate)
    # Reserve before any remote push. A restart reuses this exact candidate;
    # the dispatcher reconciles immutable branch visibility before building.
    ledger.add(candidate)
    atomic_json(Path(state) / 'incoming' / (candidate['release_id'] + '.json'), candidate)
    push(candidate)
    return candidate['release_id']
