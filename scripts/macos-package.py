#!/usr/bin/env python3
"""Retry Mac packaging against an unchanged, already native-qualified source pair.

The controller has its own protected commit. It never substitutes its source
identity for the original native application inputs or edits their installer.
"""
import argparse
import fnmatch
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tarfile
import tomllib
import zipfile

from paired_sources import verify_native_ci_inputs, verify_retained_inputs
from release_evidence import (bindings, digest, file_reference, read_json, require,
                              source_identity, validate_report, validate_sources)

ROOT = Path(__file__).resolve().parents[1]
REPO = 'IggyGG/gchat'
TARGETS = {'macos-aarch64': 'aarch64-apple-darwin', 'macos-x86_64': 'x86_64-apple-darwin'}


def script(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def reference(path):
    return {'sha256': digest(path), 'size': path.stat().st_size}


def gh_json(endpoint):
    return json.loads(subprocess.check_output(['gh', 'api', endpoint], text=True))


def verify_controller(root, environment):
    identity = source_identity(root)
    macos = script('macos-build')
    ref = macos.release_ref(environment.get('GITHUB_REF', ''))
    require(environment.get('GITHUB_SHA') == identity['commit'] and
            environment.get('GITHUB_WORKFLOW_SHA') == identity['commit'] and
            environment.get('GITHUB_WORKFLOW_REF') == f'{REPO}/.github/workflows/macos-package.yml@{ref}',
            'package controller must run from its own frozen protected workflow commit')
    remote = ref.replace('refs/heads/', 'refs/remotes/origin/', 1) if ref.startswith('refs/heads/') else ref
    tip = subprocess.check_output(['git', 'rev-parse', '--verify', remote + '^{commit}'], cwd=root, text=True).strip()
    require(tip == identity['commit'], 'package controller release ref moved')
    return {**identity, 'ref': ref}


def verify_origin(run, artifact, run_id, artifact_id, archive_sha, target, gchat_commit):
    require(run.get('id') == run_id and run.get('head_sha') == gchat_commit and
            run.get('event') == 'workflow_dispatch' and run.get('path') == '.github/workflows/macos-release.yml' and
            run.get('repository', {}).get('full_name') == REPO,
            'original native run belongs to different sources, workflow or repository')
    # One architecture may still be executing; its already uploaded sibling is
    # eligible only if that sibling's complete native reports passed below.
    require(artifact.get('id') == artifact_id and artifact.get('name') == target and
            artifact.get('expired') is False and artifact.get('digest') == 'sha256:' + archive_sha and
            artifact.get('workflow_run', {}).get('id') == run_id and
            artifact.get('workflow_run', {}).get('head_sha') == gchat_commit,
            'original native artifact identity/digest mismatch')


def extract_archive(archive, destination):
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive) as source:
        entries = source.infolist()
        require(sum(entry.file_size for entry in entries) <= 1024 ** 3, 'native evidence archive is too large')
        names = set()
        for entry in entries:
            name = PurePosixPath(entry.filename)
            require(not name.is_absolute() and '..' not in name.parts and '\\' not in entry.filename and
                    bool(name.parts) and name.parts[0] not in ('', '.') and name.as_posix() not in names and
                    not stat.S_ISLNK(entry.external_attr >> 16), 'unsafe native evidence archive member')
            names.add(name.as_posix())
        source.extractall(destination)


def restore_omitted_config(evidence, candidate, inputs, target):
    """Recover an upload-filtered hidden file only when its original hash proves it.

    The failed native worker uploaded dot-directories without include-hidden-files.
    Its immutable source archive and log retain every deterministic input needed
    for this file. No checkout path is substituted and no receipt is changed.
    """
    provenance = evidence / 'paired-gchat'
    destination = provenance / 'derived/.cargo/config.toml'
    if destination.exists():
        return
    report_path = file_reference(evidence, candidate['checks'][f'native.gchat.{target}'])
    native_report = read_json(report_path)
    logs = [file_reference(evidence, step['log']) for step in native_report['steps']]
    original_roots = set()
    for log in logs:
        original_roots.update(re.findall(r'/[^\s()"<>]+/target/paired-ci/[0-9a-f]{32}/inputs/gcoms',
                                         log.read_text(encoding='utf-8')))
    require(len(original_roots) == 1, 'missing Cargo configuration has no unique original path in bound native log')
    original_root = next(iter(original_roots))
    archive_path = file_reference(evidence, candidate['sources']['gcoms']['archive'])
    with tarfile.open(archive_path) as archive:
        manifests = {member.name: tomllib.loads(archive.extractfile(member).read().decode('utf-8'))
                     for member in archive.getmembers() if member.isfile() and
                     (member.name == 'Cargo.toml' or member.name.endswith('/Cargo.toml'))}
    patches = ['[patch.crates-io]']
    for member in manifests['Cargo.toml']['workspace']['members']:
        matches = sorted(name for name in manifests if fnmatch.fnmatchcase(str(PurePosixPath(name).parent), member))
        for name in matches:
            package = manifests[name]['package']['name']
            if package.startswith('gcoms-'):
                directory = original_root + '/' + str(PurePosixPath(name).parent)
                patches.append(f'{json.dumps(package)} = {{ path = {json.dumps(directory)} }}')
    content = ('\n'.join(patches) + '\n').encode('utf-8')
    require(hashlib.sha256(content).hexdigest() == inputs['cargo_config_sha256'],
            'reconstructed Cargo configuration does not match the original native hash')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    write_json(provenance / 'cargo-config-reconstruction.json', {
        'reason': 'original GitHub artifact omitted hidden directory',
        'exact_original_hash_matched': True, 'original_path': original_root,
        'sha256': inputs['cargo_config_sha256'], 'source_archive': reference(archive_path),
        'bound_native_logs': [reference(path) for path in logs]})


def verify_native(directory, target, expected, repositories=None, recover_omitted_config=False):
    evidence = directory / 'evidence'
    candidate = read_json(evidence / 'candidate.json')
    validate_sources(candidate, evidence, repositories)
    require({name: value['commit'] for name, value in candidate['sources'].items()} == expected,
            'native evidence source pair differs from requested package inputs')
    require(candidate.get('targets') == [target], 'native evidence target differs')
    for project in ('gchat', 'gcoms'):
        check = f'native.{project}.{target}'
        report = read_json(file_reference(evidence, candidate['checks'][check]))
        validate_report(check, report, candidate, evidence, candidate['artifacts'])
    provenance = evidence / 'paired-gchat'
    inputs = read_json(provenance / 'inputs.json')
    require(inputs.get('sources') == bindings(candidate) and inputs.get('target') == TARGETS[target],
            'paired native provenance differs from requested target/sources')
    for project, source in candidate['sources'].items():
        require(inputs.get('source_archive_sha256', {}).get(project) == source['archive']['sha256'],
                'paired native source archive differs from candidate')
        if repositories:
            archive = subprocess.check_output(['git', 'archive', '--format=tar', source['commit']], cwd=repositories[project])
            require(hashlib.sha256(archive).hexdigest() == source['archive']['sha256'],
                    'retained source archive differs from committed source bytes')
    native = verify_native_ci_inputs(provenance / 'native-ci.json', inputs)
    if recover_omitted_config:
        restore_omitted_config(evidence, candidate, inputs, target)
    verify_retained_inputs(provenance, inputs)
    result = {'sources': bindings(candidate), 'native_ci': native,
              'candidate': reference(evidence / 'candidate.json'),
              'native_receipt': reference(provenance / 'native-ci.json')}
    reconstruction = provenance / 'cargo-config-reconstruction.json'
    if reconstruction.exists():
        result['cargo_config_reconstruction'] = reference(reconstruction)
    return result


def prepare(args):
    controller = verify_controller(ROOT, os.environ)
    expected = {'gchat': args.gchat_commit, 'gcoms': args.gcoms_commit}
    repositories = {'gchat': args.gchat.resolve(), 'gcoms': args.gcoms.resolve()}
    for name, repo in repositories.items():
        require(source_identity(repo)['commit'] == expected[name], 'package source checkout differs')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    run = gh_json(f'repos/{REPO}/actions/runs/{args.native_run_id}')
    artifact = gh_json(f'repos/{REPO}/actions/artifacts/{args.artifact_id}')
    verify_origin(run, artifact, args.native_run_id, args.artifact_id, args.artifact_sha256,
                  args.target, args.gchat_commit)
    write_json(output / 'original-run.json', run)
    write_json(output / 'original-artifact.json', artifact)
    archive = output / 'original-native.zip'
    with archive.open('wb') as stream:
        subprocess.run(['gh', 'api', f'repos/{REPO}/actions/artifacts/{args.artifact_id}/zip', '--allow-escape-sequences'],
                       stdout=stream, check=True)
    require(digest(archive) == args.artifact_sha256, 'downloaded native artifact digest differs')
    retained = output / 'original-native'
    extract_archive(archive, retained)
    native = verify_native(retained, args.target, expected, repositories, recover_omitted_config=True)
    report = {'schema': 1, 'scope': 'macos_package_retry_existing_native', 'target': args.target,
              'controller': controller, 'sources': native['sources'], 'native': native,
              'original_run': reference(output / 'original-run.json'),
              'original_artifact': reference(output / 'original-artifact.json'),
              'original_archive': reference(archive), 'prepared': True}
    write_json(output / 'prepared.json', report)
    print('Verified original native reports and exact package sources; no native tests relabeled or rerun')


def load_prepared(args):
    output = args.output.resolve()
    report = read_json(output / 'prepared.json')
    require(report.get('prepared') is True and report.get('target') == args.target,
            'package retry preparation did not pass')
    require(verify_controller(ROOT, os.environ) == report['controller'], 'package controller changed')
    for name, repo in (('gchat', args.gchat), ('gcoms', args.gcoms)):
        require(source_identity(repo) == report['sources'][name], 'frozen package sources changed')
    for name, filename in (('original_archive', 'original-native.zip'), ('original_run', 'original-run.json'),
                           ('original_artifact', 'original-artifact.json')):
        require(reference(output / filename) == report[name], 'retained original native inputs changed')
    expected = {name: value['commit'] for name, value in report['sources'].items()}
    require(verify_native(output / 'original-native', args.target, expected) == report['native'],
            'original native evidence changed after preparation')
    return output, report


def preflight(args):
    output, report = load_prepared(args)
    installer = script('build-installer')
    # Only this import preflight uses the new diagnostics. The actual installer
    # remains the unchanged script committed with the qualified application.
    installer.ROOT = args.gchat.resolve()
    identity = installer.configured_identity('Darwin')
    policy = installer.signing_policy()
    with installer.apple_keychain(policy):
        pass
    write_json(output / 'signing-preflight.json', {
        'passed': True, 'scope': 'protected_certificate_import_and_temporary_keychain_cleanup',
        'controller': report['controller'], 'sources': report['sources'],
        'publisher': identity, 'signing_policy': policy,
        'helper': reference(ROOT / 'scripts/build-installer.py'),
        'application_signing_tested': False})
    print('Protected signing certificate imported; ready to build the unchanged qualified application')


def finish(args):
    output, report = load_prepared(args)
    preflight_report = read_json(output / 'signing-preflight.json')
    require(preflight_report.get('passed') is True and preflight_report.get('sources') == report['sources'] and
            preflight_report.get('controller') == report['controller'], 'signing import preflight differs')
    signed = args.signed.resolve()
    build = read_json(signed / 'build.json')
    expected = {name: value['commit'] for name, value in report['sources'].items()}
    require(build.get('sources') == expected and build.get('target') == args.target and
            build.get('dependency_inputs', {}).get('sources') == report['sources'], 'signed bundle source/target mismatch')
    inputs = build['dependency_inputs']
    native = verify_native_ci_inputs(signed / 'provenance/native-ci.json', inputs)
    verify_retained_inputs(signed / 'provenance', inputs)
    require(native == report['native']['native_ci'] and native == build.get('native_ci'),
            'signed bundle does not use the original native inputs')
    require(read_json(signed / 'provenance/inputs.json') == inputs, 'signed bundle input provenance differs')
    files = build.get('files', [])
    require(len(files) == 1 and files[0].get('format') == 'dmg', 'one signed DMG is required')
    artifact = files[0]
    name = artifact.get('name')
    require(isinstance(name, str) and Path(name).name == name and '/' not in name and '\\' not in name,
            'unsafe signed artifact name')
    require(artifact.get('signing_verified') is True and digest(signed / name) == artifact.get('sha256'),
            'signed DMG digest/verification mismatch')
    candidate = read_json(output / 'original-native/evidence/candidate.json')
    archive = file_reference(output / 'original-native/evidence', candidate['sources']['gchat']['archive'])
    script('macos-build').verify_application_smoke(signed, build, archive)
    report.update(passed=True, native_tests_rerun=False, build=reference(signed / 'build.json'),
                  application_smoke=reference(signed / 'application-smoke/report.json'),
                  signing_preflight=reference(output / 'signing-preflight.json'))
    write_json(output / 'report.json', report)
    print('Signed DMG and copied-application service/GUI smoke passed against original native-qualified sources')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'preflight', 'finish'))
    parser.add_argument('--target', choices=TARGETS, required=True)
    parser.add_argument('--gchat', type=Path, required=True)
    parser.add_argument('--gcoms', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--signed', type=Path)
    parser.add_argument('--native-run-id', type=int)
    parser.add_argument('--artifact-id', type=int)
    parser.add_argument('--artifact-sha256')
    parser.add_argument('--gchat-commit')
    parser.add_argument('--gcoms-commit')
    args = parser.parse_args()
    if args.phase == 'prepare':
        for name in ('native_run_id', 'artifact_id'):
            require(getattr(args, name) and getattr(args, name) > 0, 'positive run/artifact IDs required')
        for name, length in (('artifact_sha256', 64), ('gchat_commit', 40), ('gcoms_commit', 40)):
            require(re.fullmatch('[0-9a-f]{' + str(length) + '}', getattr(args, name) or ''), 'full immutable hashes required')
        prepare(args)
    elif args.phase == 'preflight':
        preflight(args)
    else:
        require(args.signed is not None, '--signed required for finish')
        finish(args)


if __name__ == '__main__':
    main()
