#!/usr/bin/env python3
"""Verify retained signed Windows bytes with a separately bound lifecycle fixture."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from release_evidence import source_identity

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


package = load('verification_package_inputs', ROOT / 'scripts/windows-package.py')


def verify_fixture_boundary(original, updated):
    def outside_directory_setup(text):
        start = text.index('def private_directory(path):')
        end = text.index('def isolated_environment(home):', start)
        return (text[:start] + text[end:]).replace('import csv\n', '').replace('import base64\n', '')
    if outside_directory_setup(original) != outside_directory_setup(updated):
        raise ValueError('lifecycle recovery changed behavior outside private fixture-directory setup')


def verify_package(directory, config):
    package.verify_native(directory, config)
    receipt = package.read(directory / 'recovery.json')
    if (receipt.get('passed') is not True or receipt.get('source_unchanged') is not True or
        receipt.get('controller', {}).get('commit') != config['package_controller'] or
        receipt.get('sources') != config['sources'] or package.digest(directory / 'build.json') != config['build_sha256']):
        raise ValueError('retained signed package lacks its exact successful build binding')
    build = package.read(directory / 'build.json')
    if build.get('sources') != config['sources'] or build.get('target') != 'windows-x86_64':
        raise ValueError('retained build source or target differs')
    files = build.get('files', [])
    if (len(files) != 1 or files[0].get('format') != 'nsis' or
        files[0].get('sha256') != config['installer_sha256'] or files[0].get('signing_verified') is not True):
        raise ValueError('retained installer differs from the successful signed package')
    name = files[0]['name']
    if Path(name).name != name or '\\' in name or package.digest(directory / name) != config['installer_sha256']:
        raise ValueError('retained installer bytes/path differ')
    return build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'verify', 'verify-existing'))
    parser.add_argument('--prior', type=Path, required=True)
    parser.add_argument('--gchat', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    config = package.read(ROOT / 'release/windows-installer-verification.json')
    if args.action == 'verify-existing':
        verify_package(args.prior, config)
        print('Original signed package and both native passes verified')
        return
    if os.name != 'nt' or os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('installer verification requires the isolated native Windows worker')
    controller = source_identity(ROOT)
    if any(os.environ.get(key) != controller['commit'] for key in ('GITHUB_SHA', 'GITHUB_WORKFLOW_SHA')):
        raise ValueError('verification controller differs from executing workflow')
    if not args.gchat or source_identity(args.gchat)['commit'] != config['sources']['gchat']:
        raise ValueError('original application source checkout differs')
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=args.gchat).strip():
        raise ValueError('original application source changed')
    helper = ROOT / 'scripts/test-native-application.py'
    verify_fixture_boundary((args.gchat / 'scripts/test-native-application.py').read_text(), helper.read_text())
    if args.action == 'prepare':
        args.prior.mkdir(parents=True, exist_ok=False)
        run = package.api(f"repos/IggyGG/gchat/actions/runs/{config['package_run_id']}")
        artifact = package.api(f"repos/IggyGG/gchat/actions/artifacts/{config['package_artifact_id']}")
        if (run['status'] != 'completed' or run['head_sha'] != config['package_controller'] or
            artifact['workflow_run']['id'] != run['id'] or artifact['expired'] or
            artifact['digest'] != 'sha256:' + config['package_artifact_sha256']):
            raise ValueError('original package workflow/artifact binding changed')
        archive = args.prior / 'original-artifact.zip'
        with archive.open('wb') as out:
            subprocess.run(['gh', 'api', f"repos/IggyGG/gchat/actions/artifacts/{artifact['id']}/zip"], stdout=out, check=True)
        if package.digest(archive) != config['package_artifact_sha256'] or archive.stat().st_size != artifact['size_in_bytes']:
            raise ValueError('downloaded package archive differs')
        package.extract(archive, args.prior / 'original')
        verify_package(args.prior / 'original', config)
        package.write(args.prior / 'verification-inputs.json', {'controller': controller, 'config': config,
                      'original_run': run, 'original_artifact': artifact})
        return
    if not args.output:
        parser.error('verify requires --output')
    previous = package.read(args.prior / 'verification-inputs.json')
    if previous['controller'] != controller or previous['config'] != config:
        raise ValueError('verification inputs changed since preparation')
    verify_package(args.prior / 'original', config)
    shutil.copytree(args.prior / 'original', args.output)
    (args.output / 'application-smoke').rename(args.output / 'prior-application-smoke')
    receipt = {'schema': 1, 'scope': 'unchanged_signed_nsis_with_corrected_private_directory_fixture',
               'controller': controller, 'sources': config['sources'], 'config': config, 'passed': False,
               'helper_sha256': package.digest(helper), 'harness_sha256': package.digest(__file__),
               'application_rebuilt': False, 'native_ci_repeated': False}
    try:
        # Keep installer behavior, publication and signature policy from the
        # frozen application. Only owned temporary-directory setup is corrected.
        original = load('original_windows_installer', args.gchat / 'scripts/test-windows-installer.py')
        original.smoke = load('corrected_private_directory_smoke', helper)
        original.SMOKE_SCRIPT = helper
        arguments = argparse.Namespace(build_manifest=args.output / 'build.json',
            native_receipt=args.output / 'provenance/native-ci.json', installer=None,
            publication=args.gchat / 'release/publication.json', output=args.output / 'application-smoke',
            temp_parent=None, timeout=30)
        if original.run(arguments) != 0:
            raise ValueError('unchanged installed application lifecycle failed')
        receipt['passed'] = True
    finally:
        receipt['source_unchanged'] = not subprocess.check_output(['git', 'status', '--porcelain'], cwd=args.gchat).strip()
        receipt['passed'] = receipt['passed'] and receipt['source_unchanged']
        verify_package(args.output, config)
        package.write(args.output / 'verification.json', receipt)
    if not receipt['passed']:
        raise ValueError('original application source changed')


if __name__ == '__main__':
    main()
