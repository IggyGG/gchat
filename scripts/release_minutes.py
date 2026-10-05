"""The existing minutes publication policy, separate from deep qualification."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

from release_coordinator import atomic_json, read_receipt
from release_pair import validate
from release_publish import job

POLICY = 'production-minutes-v1'
LIMIT_SECONDS = 3600


def enabled(config):
    policy = config.get('publication_policy')
    if policy not in (None, POLICY):
        raise ValueError('unsupported routine publication policy')
    return policy == POLICY


def budget(state, manifest, platform, stage, now=None, paused=False, phase='build'):
    """A restart or retry never starts another hour for the same routine run."""
    now = int(time.time()) if now is None else now
    if phase not in ('build', 'publication'):
        raise ValueError('unknown routine budget phase')
    folder = 'routine-runs' if phase == 'build' else 'publication-runs'
    path = Path(state) / folder / manifest['release_id'] / (platform + '.json')
    if path.is_file():
        run = json.loads(path.read_text())
        if (run.get('release_id') != manifest['release_id'] or run.get('platform') != platform
                or run.get('sources') != manifest['sources'] or type(run.get('started_at')) is not int
                or type(run.get('paused_seconds', 0)) is not int or run.get('paused_seconds', 0) < 0
                or ('paused_at' in run and (type(run['paused_at']) is not int
                    or not run['started_at'] <= run['paused_at'] <= now))
                or run.get('deadline_at') != run['started_at'] + LIMIT_SECONDS + run.get('paused_seconds', 0)):
            raise ValueError('routine release budget identity changed')
    else:
        run = {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
               'platform': platform, 'started_at': now, 'deadline_at': now + LIMIT_SECONDS,
               'paused_seconds': 0}
        atomic_json(path, run)
    run.setdefault('paused_seconds', 0)
    if paused:
        if 'paused_at' not in run:
            run['paused_at'] = now
            atomic_json(path, run)
        return run
    if 'paused_at' in run:
        waited = max(0, now - run.pop('paused_at'))
        run['paused_seconds'] += waited
        run['deadline_at'] += waited
        atomic_json(path, run)
    if now >= run['deadline_at']:
        raise ValueError('routine release exceeded 60 minutes at ' + stage + '; retained requests require reconciliation')
    return run


def verify(state, manifest, platform, now=None):
    """Use original native verification and fresh running-relay observations."""
    if platform not in ('android', 'ios'):
        raise ValueError('minutes mobile verification requires Android or iOS')
    state = Path(state)
    now = int(time.time()) if now is None else now
    verified = job(state, manifest, platform, 'verify') / 'receipt.json'
    proof, verification_sha = read_receipt(verified, manifest, platform, 'verify')
    # The native verify worker checks actual protected source bindings,
    # certificate, entitlements and original startup/lifecycle reports.
    deployment = state / 'deployment' / manifest['release_id'] / 'journal.json'
    value = json.loads(deployment.read_text())
    if (value.get('state') != 'deployed' or value.get('sources') != manifest['sources']
            or type(value.get('observed_at')) is not int
            or not 0 <= now - value['observed_at'] <= 300):
        raise ValueError('fresh deployed source-bound relay observations required')
    relays = [value.get('targets', {}).get('relay-' + str(i)) for i in range(1, 9)]
    if any(not isinstance(row, dict) or row.get('state') != 'deployed'
           or row.get('observed', {}).get('healthy') is not True
           or row.get('observed', {}).get('matches') is not True for row in relays):
        raise ValueError('all eight healthy matching relays required')
    return {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
            'platform': platform, 'stage': 'compatibility', 'passed': True,
            'source_unchanged': True, 'relay_compatible': True, 'publication_policy': POLICY,
            'qualification_complete': False, 'qualified_scopes': ['native_verification', 'startup_lifecycle',
                'running_relay_compatibility'], 'unqualified_scopes': ['full_installed_gui_upgrade_rollback',
                'full_installed_gui_file_recovery', 'physical_devices', 'live_push'],
            'verification_sha256': verification_sha, 'deployment_sha256': hashlib.sha256(deployment.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    args = parser.parse_args()
    manifest = validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()))
    platform = os.environ['GCHAT_RELEASE_TARGET']
    report = verify(args.state, manifest, platform)
    output = Path(os.environ['GCHAT_RELEASE_RECEIPT'])
    output.parent.mkdir(parents=True, exist_ok=True)
    refs = []
    verified = job(args.state, manifest, platform, 'verify') / 'receipt.json'
    proof, _ = read_receipt(verified, manifest, platform, 'verify')
    paths = [verified, args.state / 'deployment' / manifest['release_id'] / 'journal.json']
    paths += [verified.parent / item['path'] for item in proof['evidence']]
    for path in paths:
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        destination = output.parent / ('original-' + digest)
        if not destination.exists():
            try:
                os.link(path, destination)
            except OSError:
                shutil.copyfile(path, destination)
        refs.append({'path': destination.name, 'sha256': digest})
    report['evidence'] = refs
    atomic_json(output, report)


if __name__ == '__main__':
    main()
