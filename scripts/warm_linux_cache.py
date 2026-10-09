"""Compile trusted main sources for cache reuse; never run or certify a release."""
import argparse
import os
from pathlib import Path
import subprocess

from linux_build_artifacts import CLI_COMMAND, DESKTOP_COMMAND, SERVICE_COMMAND, TARGET
from paired_sources import prepare_pair
from release_cache import SCOPES


def trusted_main(environment):
    if (environment.get('GITHUB_ACTIONS') != 'true'
            or environment.get('GITHUB_REPOSITORY') != 'IggyGG/gchat'
            or environment.get('GITHUB_REF') != 'refs/heads/main'
            or environment.get('GITHUB_EVENT_NAME') not in ('push', 'schedule', 'workflow_dispatch')):
        raise ValueError('compiler cache warming requires a trusted main workflow')


def compile_commands(scope):
    if scope == 'gcoms':
        return [('gcoms', ['cargo', 'test', '--workspace', '--all-features', '--locked', '--no-run'])]
    if scope == 'services':
        return [('gcoms', SERVICE_COMMAND), ('paired', [
            'cargo', 'build', '--locked', '--release', '-p', 'gcoms-node', '-p', 'gchat-tui', '-p', 'gchat-core',
            '--bin', 'gchat', '--example', 'fleet_probe', '--example', 'turnover_daemon',
            '--features', 'gc2-carrier,gcoms-node/client-persist,gcoms-node/experimental-gc2'])]
    if scope == 'gchat':
        return [('paired', command) for command in (
            ['npm', 'run', 'build'], ['python3', 'scripts/collect-notices.py'],
            ['cargo', 'test', '--workspace', '--all-features', '--locked', '--no-run'],
            ['cargo', 'test', '--manifest-path', 'apps/client/src-tauri/Cargo.toml',
             '--lib', '--locked', '--no-run'], DESKTOP_COMMAND, CLI_COMMAND)]
    raise ValueError('unknown compiler scope')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path.cwd())
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--scope', choices=SCOPES, required=True)
    args = parser.parse_args()
    trusted_main(os.environ)
    root = args.workspace.resolve()
    environment = dict(os.environ, CARGO_TARGET_DIR=str(root / SCOPES[args.scope]),
                       CARGO_INCREMENTAL='0', CARGO_PROFILE_DEV_DEBUG='0',
                       CARGO_PROFILE_TEST_DEBUG='0', RUSTFLAGS='')
    environment.setdefault('CARGO_BUILD_JOBS', '3')
    locations = {'gcoms': root / 'gcoms'}
    if args.scope != 'gcoms':
        checkout, _ = prepare_pair(root / 'gchat', root / 'gcoms', args.work, TARGET, environment)
        locations['paired'] = checkout
    for location, command in compile_commands(args.scope):
        subprocess.run(command, cwd=locations[location], env=environment, check=True)
    print('Compiler cache populated; no tests executed or release qualification produced.')


if __name__ == '__main__':
    main()
