"""Explicit Intel test-only successors against an unchanged, live deployment.

This creates a separate provenance receipt. It never relabels an old deployment,
load result or failed native qualification as a result for the new source pair.
"""
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import time
from contextlib import closing

from release_pair import canonical, validate


TEST_ONLY = frozenset({
    'crates/node/src/node/persist/machine_scope_tests.rs',
    '.github/workflows/rust-integrations.yml',
    'scripts/check-machine-scope-recovery.py',
    'scripts/tests/machine_scope_recovery_test.py',
    'docs/evidence/gc2-flow-control-20261007/machine-scope-checkpoint.json',
    'PLAN.md', 'TESTPLAN.md', 'README.md',
})


def baseline(state, manifest):
    release = manifest.get('deployment_baseline')
    if (manifest.get('selected_platforms') != ['macos-x86_64']
            or not isinstance(release, str) or not re.fullmatch('[0-9a-f]{64}', release)
            or release == manifest['release_id']):
        raise ValueError('deployment reuse requires an explicit Intel-only successor')
    with closing(sqlite3.connect((Path(state) / 'ledger.sqlite').resolve().as_uri() + '?mode=ro', uri=True)) as db:
        row = db.execute('SELECT manifest FROM candidates WHERE id=?', (release,)).fetchone()
    if row is None:
        raise ValueError('deployment baseline is not retained')
    old = validate(json.loads(row[0]))
    if old['policy'] != manifest['policy']:
        raise ValueError('platform-only successor changed release policy')
    return old


def changed(root, before, after):
    data = subprocess.check_output(['git', '-C', str(root), 'diff', '--name-only', '-z',
                                    before, after, '--'], timeout=30)
    return sorted(filter(None, data.decode().split('\0')))


def qualify_sources(repositories, manifest, old):
    """Compare committed upstream trees, then verify exact version preparation."""
    from release_inputs import CONTROL_FILES, GCOMS_STATUS_FILES, CONTROLLER_FILES, controller_only
    from release_prepare import prepare
    if 'upstream' not in manifest or 'upstream' not in old:
        raise ValueError('deployment reuse requires retained upstream provenance')
    differences = {}
    for project in ('gchat', 'gcoms'):
        root = repositories[project]
        before, after = old['upstream'][project], manifest['upstream'][project]
        for source in (before, after):
            tree = subprocess.check_output(['git', '-C', str(root), 'rev-parse',
                source['commit'] + '^{tree}'], text=True, timeout=15).strip()
            if tree != source['tree']:
                raise ValueError('upstream source tree differs')
        paths = changed(root, before['commit'], after['commit'])
        allowed = TEST_ONLY | GCOMS_STATUS_FILES if project == 'gcoms' else CONTROL_FILES | CONTROLLER_FILES
        rejected = [path for path in paths if path not in allowed
                    and not (project == 'gchat' and controller_only(path))]
        if rejected:
            raise ValueError(project + ' production inputs changed; normal deployment is required')
        differences[project] = paths
    if manifest['sources']['gcoms'] != manifest['upstream']['gcoms']:
        raise ValueError('GComs artifact does not match reviewed upstream')
    expected = prepare(repositories['gchat'], manifest['upstream']['gchat']['commit'],
                       manifest['sources']['gcoms']['commit'], manifest['versions'], manifest['refs']['gchat'])
    if expected != manifest['sources']['gchat']['commit']:
        raise ValueError('prepared application differs from its exact version-only source')
    tree = subprocess.check_output(['git', '-C', str(repositories['gchat']), 'rev-parse',
                                   expected + '^{tree}'], text=True, timeout=15).strip()
    if tree != manifest['sources']['gchat']['tree']:
        raise ValueError('prepared application tree differs')
    # The only Rust exception must remain under the unchanged cfg(test) module.
    for source in (old['upstream']['gcoms'], manifest['upstream']['gcoms']):
        data = subprocess.check_output(['git', '-C', str(repositories['gcoms']), 'show',
            source['commit'] + ':crates/node/src/node/persist.rs'], text=True, timeout=15)
        if not re.search(r'#\[cfg\(test\)\]\s*(?:pub\(in crate::node\)\s+)?mod tests\s*\{', data):
            raise ValueError('persistence fixture is not confined to the test module')
        if 'include!("persist/machine_scope_tests.rs")' not in data:
            raise ValueError('persistence fixture inclusion changed')
    return differences


def evidence_path(state, manifest):
    return Path(state) / 'deployment-reuse' / (manifest['release_id'] + '.json')


def binding(proof):
    """Stable provenance identity; fresh health observations remain separate."""
    return hashlib.sha256(canonical({key: proof[key] for key in (
        'release_id', 'sources', 'baseline_release_id', 'baseline_sources',
        'changed_paths', 'inventory_revision', 'relay_load_receipt_sha256')})).hexdigest()


def ready(state, config, ledger, manifest, now=None):
    from release_coordinator import atomic_json
    from release_control import deployment_config
    state = Path(state)
    now = int(time.time()) if now is None else now
    proof = {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
             'baseline_release_id': manifest.get('deployment_baseline'), 'observed_at': now,
             'passed': False}
    try:
        old = baseline(state, manifest)
        repositories = {p: config['discovery'][p]['mirror'] for p in ('gchat', 'gcoms')}
        differences = qualify_sources(repositories, manifest, old)
        desired = json.loads((state / 'deployment/desired.json').read_text())
        raw = (state / 'deployment' / old['release_id'] / 'journal.json').read_bytes()
        journal = json.loads(raw)
        inventory = deployment_config(state, old, json.loads(Path(config['deployment_file']).read_text()))
        revision = hashlib.sha256(canonical(inventory)).hexdigest()
        targets = journal.get('targets', {})
        if (desired['release_id'] != old['release_id'] or journal.get('state') != 'deployed'
                or journal.get('sources') != old['sources'] or journal.get('revision') != revision
                or not 0 <= now - journal.get('observed_at', 0) <= 300
                or set(targets) != {t['id'] for t in inventory['targets']}
                or not targets or any(t.get('observed', {}).get('healthy') is not True
                    or t.get('observed', {}).get('matches') is not True for t in targets.values())):
            raise ValueError('baseline deployment is not freshly healthy and matching')
        load = json.loads((state / 'relay-load' / old['release_id'] / 'status.json').read_text())
        if (load.get('state') != 'passed' or load.get('sources') != old['sources']
                or load.get('release_id') != old['release_id']):
            raise ValueError('baseline has no source-bound relay load qualification')
        from release_coordinator import read_receipt
        from release_publish import job
        report, digest = read_receipt(job(state, old, 'linux-x86_64', 'relay_load') / 'receipt.json',
                                      old, 'linux-x86_64', 'relay_load')
        if report.get('relay_load_verified') is not True or digest != load.get('receipt_sha256'):
            raise ValueError('baseline relay load receipt differs')
        proof.update(passed=True, baseline_sources=old['sources'], changed_paths=differences,
                     inventory_revision=revision, baseline_journal_sha256=hashlib.sha256(raw).hexdigest(),
                     relay_load_receipt_sha256=digest)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        proof['reason'] = str(error)[:240] if isinstance(error, ValueError) else 'Deployment reuse provenance is unavailable'
    atomic_json(evidence_path(state, manifest), proof)
    return proof['passed']


def retained(state, manifest, now=None):
    old = baseline(state, manifest)
    now = int(time.time()) if now is None else now
    proof = json.loads(evidence_path(state, manifest).read_text())
    if (proof.get('passed') is not True or proof.get('release_id') != manifest['release_id']
            or proof.get('sources') != manifest['sources'] or proof.get('baseline_sources') != old['sources']
            or proof.get('baseline_release_id') != old['release_id']
            or not 0 <= now - proof.get('observed_at', 0) <= 300):
        raise ValueError('platform-only deployment provenance is unavailable or stale')
    return old, proof
