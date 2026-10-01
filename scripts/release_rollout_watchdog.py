#!/usr/bin/env python3
"""Restore a failed release-controller update independently of that controller."""
import argparse
import json
from pathlib import Path
import time
import re
import subprocess

from release_coordinator import atomic_json
from release_deployment import invoke
from release_pair import validate


def recover(state, *, worker=invoke, now=None):
    import fcntl
    state = Path(state)
    now = int(time.time()) if now is None else now
    root = state / 'deployment'
    if not (root / 'owner.json').is_file(): return False
    with (root / 'rollout.lock').open('a') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return False
        if not (root / 'owner.json').is_file(): return False
        owner = json.loads((root / 'owner.json').read_text())
        if not re.fullmatch('[0-9a-f]{64}', owner['release_id']):
            raise ValueError('invalid controller recovery release identity')
        directory = root / owner['release_id']
        journal = directory / 'journal.json'
        if not journal.is_file(): return False
        report = json.loads(journal.read_text())
        targets = [t for t in report['inventory']['targets'] if t.get('kind') == 'deployment'
                   and t.get('namespace') == 'ghost-com' and t.get('name') == 'gchat-release'
                   and t.get('image') == 'controller']
        if len(targets) != 1: return False
        target = targets[0]
        item = report['targets'].get(target['id'], {})
        if item.get('state') not in ('activating', 'rollback_pending', 'rollback_failed'): return False
        work = directory / target['id']
        manifest = validate(json.loads((work / 'candidate.json').read_text()))
        if manifest['release_id'] != owner['release_id'] or manifest['sources'] != report['sources']:
            raise ValueError('controller recovery source binding differs from original rollout')
        if now < item.get('retry_at', 0): return False
        if item['state'] == 'activating':
            age = now - item['started_at']
            if age < 120: return False
            observed = worker(target, 'observe', manifest, work)
            if observed is None: return False
            if observed['healthy'] and age <= target.get('activation_deadline_seconds', 900): return False
        # Persist recovery intent before the mutation. The worker itself checks
        # the original workload UID and previous image, and refuses operator drift.
        item.update(state='rollback_pending', retry_at=now + 60)
        report.update(state='blocked', reason='Controller update failed; independent rollback is restoring the prior image')
        atomic_json(journal, report)
        try:
            proof = worker(target, 'rollback', manifest, work, item['previous'])
            if proof is not None: item['state'] = 'rolled_back'
        except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
            item['state'] = 'rollback_failed'
            atomic_json(directory / ('watchdog-failure-' + str(time.time_ns()) + '.json'), {'type': type(error).__name__})
        finally:
            atomic_json(journal, report)
            if not any(t.get('state') in ('activating', 'rollback_pending', 'rollback_failed')
                       for t in report['targets'].values()):
                (root / 'owner.json').unlink(missing_ok=True)
            atomic_json(state / 'public/deployment.json', {'schema': 1, 'release_id': manifest['release_id'],
                'sources': manifest['sources'], 'state': 'blocked', 'reason': report['reason'],
                'observed_at': now, 'controller_recovery': item['state']})
        return item['state'] == 'rolled_back'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    args = parser.parse_args()
    recover(args.state)


if __name__ == '__main__': main()
