#!/usr/bin/env python3
"""Inspect, resume or roll back the production release through one command."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, help='local controller state; default uses the existing Kubernetes controller')
    parser.add_argument('action', choices=('status', 'resume', 'rollback', 'qualify', 'handoff'), nargs='?', default='status')
    parser.add_argument('--release', help='full immutable release ID; default is the selected deployment')
    parser.add_argument('--platform', help='resume only this platform')
    parser.add_argument('--json', action='store_true', help='machine-readable status')
    parser.add_argument('--observed', action='append', help='handoff only: target=running-sha256; repeat per target')
    parser.add_argument('--reason', help='handoff only: why the external hotfix must be retained')
    args = parser.parse_args()
    if args.state is None:
        argv = ['kubectl', '-n', 'ghost-com', 'exec', 'deployment/gchat-release', '-c', 'coordinator', '--',
                'python3', '/opt/gchat/scripts/release.py', '--state', '/state', args.action]
        if args.release: argv.extend(['--release', args.release])
        if args.platform: argv.extend(['--platform', args.platform])
        if args.json: argv.append('--json')
        for observation in args.observed or []: argv.extend(['--observed', observation])
        if args.reason: argv.extend(['--reason', args.reason])
        return subprocess.run(argv, check=False).returncode
    from release_control import request, status
    if args.action == 'status':
        if args.platform: parser.error('--platform is only available for resume')
        if args.observed or args.reason: parser.error('--observed and --reason require handoff')
        value = status(args.state, args.release)
        if args.json:
            print(json.dumps(value, indent=2))
        else:
            print(f"Release {value['sequence']}  {value['release_id']}")
            if value.get('flight'):
                print(f"Pending release: {value['flight'].get('pending') or 'none'}")
            progress = value.get('deployment_progress')
            if progress:
                print(f"Active stage: {progress['target']}/{progress['stage']}  deadline={progress['deadline_at']}")
            for worker in value.get('running_workers', []):
                print(f"Worker: {worker['platform']}/{worker['stage']}")
            load = value.get('relay_load')
            if load:
                print(f"Relay load: {load['state']}  {load.get('reason', '')}")
            deployment = value['deployment']
            print(f"Deployment: {deployment['state']}  {deployment['reason']}")
            for target in deployment['targets']:
                running = target['running'].get('sha256', '')
                print(f"  {target['id']}: {target['state']}  healthy={target['healthy']}  matches={target['matches']}  {running}")
            for item in value['platforms']:
                print(f"  {item['platform']}: {item['state']}  age={item['state_age_seconds']}s  {item['reason']}")
                for name, check in item.get('native_checks', {}).get('jobs', {}).items():
                    outcome = check.get('conclusion') or check.get('status', 'unknown')
                    step = (' / ' + check['step']) if check.get('step') else ''
                    print(f"    {name}: {outcome} (attempt {check['attempt']}){step}")
    else:
        observations = None
        if args.observed:
            observations = {}
            for item in args.observed:
                target, separator, sha = item.partition('=')
                if not separator or target in observations: parser.error('each --observed needs a unique target=sha256')
                observations[target] = sha
        print(json.dumps(request(args.state, args.action, args.release, args.platform,
                                 observed=observations, reason=args.reason)))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
