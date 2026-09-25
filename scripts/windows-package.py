#!/usr/bin/env python3
"""Package exact native-qualified Windows sources with a separately bound controller."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tomllib
import zipfile

from paired_sources import verify_native_ci_inputs, verify_retained_inputs
from release_evidence import file_reference, source_identity, validate_report, validate_sources

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], text=True))


def reconstruct_config(evidence, candidate, report):
    logs = [file_reference(evidence, step['log']).read_text(encoding='utf-8')
            for step in report['steps']]
    paths = {line.removeprefix('Paired native evidence: ').strip()
             for log in logs for line in log.splitlines() if line.startswith('Paired native evidence: ')}
    if len(paths) != 1:
        raise ValueError('cannot bind generated config to one original native checkout')
    original = PureWindowsPath(paths.pop())
    if not original.is_absolute() or original.name != 'provenance':
        raise ValueError('invalid original native provenance path')
    protocol = original.parent / 'inputs/gcoms'
    archive = file_reference(evidence, candidate['sources']['gcoms']['archive'])
    patches = ['[patch.crates-io]']
    with tarfile.open(archive) as stream:
        workspace = tomllib.loads(stream.extractfile('Cargo.toml').read().decode())['workspace']
        for member in workspace['members']:
            # This recovery is for the exact retained manifests with explicit
            # member paths; refuse a different generation algorithm.
            if re.search(r'[*?\[\]]', member) or '..' in PurePosixPath(member).parts:
                raise ValueError('cannot reconstruct wildcard/outside workspace members')
            package = tomllib.loads(stream.extractfile(member + '/Cargo.toml').read().decode())['package']
            if package['name'] == 'gcoms' or package['name'].startswith('gcoms-'):
                patches.append(f'{json.dumps(package["name"])} = {{ path = {json.dumps(str(protocol / member))} }}')
    return ('\r\n'.join(patches) + '\r\n').encode()


def verify_native(directory, config, repositories=None, restore=False):
    evidence = Path(directory) / 'native-evidence'
    candidate = read(evidence / 'candidate.json')
    validate_sources(candidate, evidence, repositories)
    actual = {name: value['commit'] for name, value in candidate['sources'].items()}
    if actual != config['sources']:
        raise ValueError('native source pair differs from approved recovery inputs')
    chat_report = None
    for project in ('gchat', 'gcoms'):
        name = f'native.{project}.windows-x86_64'
        report = read(file_reference(evidence, candidate['checks'][name]))
        validate_report(name, report, candidate, evidence, candidate['artifacts'])
        if project == 'gchat':
            chat_report = report
    provenance = evidence / 'paired-gchat'
    inputs = read(provenance / 'inputs.json')
    qualified = verify_native_ci_inputs(provenance / 'native-ci.json', inputs)
    generated = provenance / 'derived/.cargo/config.toml'
    if generated.exists():
        verify_retained_inputs(provenance, inputs)
    else:
        # The original upload excluded hidden directories. Recover only bytes
        # that exactly match the native receipt's pre-existing content hash.
        data = reconstruct_config(evidence, candidate, chat_report)
        if hashlib.sha256(data).hexdigest() != inputs['cargo_config_sha256']:
            raise ValueError('reconstructed native Cargo config does not match original hash')
        for name, sha in inputs['derived_lock_sha256'].items():
            file_reference(provenance, {'path': 'derived/' + name, 'sha256': sha})
        for name, sha in inputs['npm_archives'].items():
            file_reference(provenance, {'path': 'npm/' + name, 'sha256': sha})
        if restore:
            generated.parent.mkdir(parents=True)
            generated.write_bytes(data)
            verify_retained_inputs(provenance, inputs)
            write(Path(directory) / 'reconstructed-native-config.json', {
                'original_upload_omitted_hidden_file': True, 'reconstructed': True,
                'original_sha256': inputs['cargo_config_sha256'], 'size': len(data),
                'basis': 'original hash-bound native log path and frozen workspace manifests',
                'native_receipt_modified': False, 'original_zip_modified': False})
    if inputs['sources'] != {name: {k: value[k] for k in ('commit', 'tree')}
                            for name, value in candidate['sources'].items()}:
        raise ValueError('native dependency provenance differs from candidate source pair')
    if inputs['source_archive_sha256'] != {name: value['archive']['sha256']
                                          for name, value in candidate['sources'].items()}:
        raise ValueError('native dependency archives differ from candidate source archives')
    return qualified


def extract(archive, output):
    with zipfile.ZipFile(archive) as stream:
        if sum(row.file_size for row in stream.infolist()) > 2 * 1024**3:
            raise ValueError('native evidence archive exceeds extraction bound')
        for row in stream.infolist():
            original = row.orig_filename
            path = PurePosixPath(original)
            if path.is_absolute() or '..' in path.parts or '\\' in original or '\0' in original or ':' in original or stat.S_ISLNK(row.external_attr >> 16):
                raise ValueError('unsafe native evidence archive member')
        stream.extractall(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'build', 'verify-existing'))
    parser.add_argument('--prior', type=Path, required=True)
    parser.add_argument('--gchat', type=Path)
    parser.add_argument('--gcoms', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    config = read(ROOT / 'release/windows-package-recovery.json')
    repositories = ({'gchat': args.gchat.resolve(), 'gcoms': args.gcoms.resolve()}
                    if args.gchat and args.gcoms else None)
    if args.action == 'verify-existing':
        print(json.dumps(verify_native(args.prior, config, repositories)))
        return
    if not repositories or os.name != 'nt' or os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('packaging recovery requires the native isolated Windows worker and exact checkouts')
    controller = source_identity(ROOT)
    if os.environ.get('GITHUB_SHA') != controller['commit'] or os.environ.get('GITHUB_WORKFLOW_SHA') != controller['commit']:
        raise ValueError('recovery controller must match its executing workflow commit')
    for name, path in repositories.items():
        if source_identity(path)['commit'] != config['sources'][name] or subprocess.check_output(['git', 'status', '--porcelain'], cwd=path).strip():
            raise ValueError('packaging recovery source checkout changed')
    if args.action == 'prepare':
        args.prior.mkdir(parents=True, exist_ok=False)
        run = api(f"repos/IggyGG/gchat/actions/runs/{config['native_run_id']}")
        artifact = api(f"repos/IggyGG/gchat/actions/artifacts/{config['native_artifact_id']}")
        if run['status'] != 'completed' or run['head_sha'] != config['sources']['gchat'] or artifact['workflow_run']['id'] != run['id'] or artifact['expired'] or artifact['digest'] != 'sha256:' + config['native_artifact_sha256']:
            raise ValueError('original native workflow/artifact binding changed')
        archive = args.prior / 'original-artifact.zip'
        with archive.open('wb') as out:
            subprocess.run(['gh', 'api', f"repos/IggyGG/gchat/actions/artifacts/{artifact['id']}/zip"], stdout=out, check=True)
        if digest(archive) != config['native_artifact_sha256'] or archive.stat().st_size != artifact['size_in_bytes']:
            raise ValueError('downloaded original native artifact differs')
        extract(archive, args.prior / 'original')
        qualified = verify_native(args.prior / 'original', config, repositories, restore=True)
        write(args.prior / 'recovery-inputs.json', {'controller': controller, 'config': config,
              'native_ci': qualified, 'original_run': run, 'original_artifact': artifact})
        print('Original native passes verified; original packaging failure remains failed')
        return
    if args.output is None:
        parser.error('build needs a fresh --output')
    verify_native(args.prior / 'original', config, repositories)
    previous = read(args.prior / 'recovery-inputs.json')
    if previous['controller'] != controller or previous['config'] != config:
        raise ValueError('packaging controller/input binding changed since prepare')
    specification = importlib.util.spec_from_file_location('packaged_installer', ROOT / 'scripts/build-installer.py')
    installer = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(installer)
    # Only the packaging harness comes from this controller. All application,
    # dependency, publication and signature-verifier inputs remain native-bound.
    installer.ROOT = repositories['gchat']
    receipt = {'schema': 1, 'scope': 'windows_packaging_with_reused_exact_native_checks',
               'controller': controller, 'sources': config['sources'], 'passed': False,
               'native_run_id': config['native_run_id'], 'native_artifact_sha256': config['native_artifact_sha256'],
               'harness_sha256': digest(__file__), 'installer_harness_sha256': digest(ROOT / 'scripts/build-installer.py')}
    try:
        installer.main(['--target', 'windows-x86_64', '--gcoms', str(repositories['gcoms']),
            '--native-ci-report', str(args.prior / 'original/native-evidence/paired-gchat/native-ci.json'),
            '--output', str(args.output)])
        receipt['passed'] = True
    finally:
        args.output.mkdir(parents=True, exist_ok=True)
        # Keep actual outputs on failure, before verification can prevent the
        # normal copy. They remain diagnostic until signatures/lifecycle pass.
        diagnostics = args.output / 'retained-build-outputs'
        diagnostics.mkdir()
        build = args.output / 'build/x86_64-pc-windows-msvc/release'
        for path in [build / 'gchat-desktop.exe', *build.glob('bundle/nsis/*.exe')]:
            if path.is_file():
                shutil.copyfile(path, diagnostics / path.name)
        receipt['source_unchanged'] = all(source_identity(path)['commit'] == config['sources'][name] and
            not subprocess.check_output(['git', 'status', '--porcelain'], cwd=path).strip()
            for name, path in repositories.items())
        receipt['passed'] = receipt['passed'] and receipt['source_unchanged']
        write(args.output / 'recovery.json', receipt)
    if not receipt['passed']:
        raise ValueError('packaging recovery source changed')


if __name__ == '__main__':
    main()
