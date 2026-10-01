#!/usr/bin/env python3
"""Retain Linux qualification and verify its same-run handoff before signing."""
import argparse
import hashlib
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

from paired_sources import verify_native_ci_inputs, verify_retained_inputs
from release_evidence import digest, file_reference, read_json, require, source_identity
from release_jobs import extract, gh
from release_pair import canonical, validate


ARTIFACT = 'linux-qualification'
TARGET = 'x86_64-unknown-linux-gnu'
COMMANDS = (
    ['python3', 'gchat/scripts/ci.py', '--gcoms', 'gcoms',
     '--provenance-output', 'native-evidence/paired-gchat'],
    ['python3', 'gcoms/scripts/ci.py'],
)


def context(manifest, environment):
    require(environment.get('GITHUB_ACTIONS') == 'true' and
            environment.get('GITHUB_REPOSITORY') == 'IggyGG/gchat' and
            environment.get('GITHUB_WORKFLOW_SHA') == manifest['sources']['gchat']['commit'] and
            environment.get('GITHUB_SHA') == manifest['sources']['gchat']['commit'],
            'qualification requires the frozen protected workflow')
    run = environment.get('GITHUB_RUN_ID', '')
    attempt = environment.get('GITHUB_RUN_ATTEMPT', '')
    require(re.fullmatch(r'[1-9][0-9]*', run) is not None and
            re.fullmatch(r'[1-9][0-9]*', attempt) is not None,
            'qualification requires an actual workflow run')
    return {'repository': 'IggyGG/gchat', 'run_id': run, 'run_attempt': int(attempt),
            'workflow_commit': environment['GITHUB_WORKFLOW_SHA']}


def verify(root, manifest, environment):
    """Failed, stale, relocated or modified evidence cannot authorize signing."""
    manifest = validate(manifest)
    expected = context(manifest, environment)
    root = Path(root).resolve()
    report = read_json(root / 'qualification.json')
    require(type(report.get('schema')) is int and report['schema'] == 1 and
            report.get('kind') == 'linux_native_qualification' and
            report.get('platform') == 'linux-x86_64' and report.get('native_target') == TARGET,
            'wrong Linux qualification schema/platform')
    require(report.get('passed') is True and report.get('source_unchanged') is True,
            'Linux qualification did not pass unchanged')
    require(report.get('sources') == manifest['sources'] and
            report.get('release_id') == manifest['release_id'] and
            report.get('manifest_sha256') == hashlib.sha256(canonical(manifest)).hexdigest(),
            'Linux qualification belongs to different release inputs')
    provider = report.get('provider', {})
    require(all(provider.get(key) == expected[key]
                for key in ('repository', 'run_id', 'workflow_commit')) and
            type(provider.get('run_attempt')) is int and
            1 <= provider['run_attempt'] <= expected['run_attempt'],
            'Linux qualification belongs to another workflow run')
    steps = report.get('steps', [])
    require(isinstance(steps, list) and len(steps) == len(COMMANDS),
            'both native CI gates are required')
    for step, command in zip(steps, COMMANDS):
        require(step.get('command') == command and type(step.get('exit_code')) is int and
                step['exit_code'] == 0, 'a native CI gate did not pass')
        require(file_reference(root, step.get('log')).stat().st_size > 0,
                'native CI log is empty')
    native = file_reference(root, report.get('native_ci'))
    inputs_path = file_reference(root, report.get('inputs'))
    require(native == root / 'paired-gchat/native-ci.json' and
            inputs_path == root / 'paired-gchat/inputs.json',
            'unexpected paired evidence location')
    inputs = read_json(inputs_path)
    require(inputs.get('sources') == manifest['sources'] and inputs.get('target') == TARGET,
            'native dependency inputs belong to another source/platform')
    verify_native_ci_inputs(native, inputs)
    verify_retained_inputs(root / 'paired-gchat', inputs)
    return report


def checked_sources(workspace, manifest):
    actual = {name: source_identity(workspace / name) for name in ('gchat', 'gcoms')}
    require(actual == manifest['sources'], 'qualification checkout differs from release inputs')


def execute(command, workspace, log):
    with log.open('xb') as stream:
        with subprocess.Popen([sys.executable, '-u', *command[1:]], cwd=workspace,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as process:
            for chunk in iter(lambda: process.stdout.read1(65536), b''):
                stream.write(chunk)
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
            return process.wait()


def qualify(workspace, manifest, environment):
    manifest = validate(manifest)
    provider = context(manifest, environment)
    checked_sources(workspace, manifest)
    require(platform.system() == 'Linux' and platform.machine() == 'x86_64',
            'Linux qualification must execute on native x86_64 Linux')
    version = subprocess.check_output(['rustc', '-vV'], text=True)
    require('host: ' + TARGET in version.splitlines(), 'wrong native Rust toolchain host')
    root = workspace / 'native-evidence'
    root.mkdir(exist_ok=False)
    report = {'schema': 1, 'kind': 'linux_native_qualification',
              'platform': 'linux-x86_64', 'native_target': TARGET,
              'sources': manifest['sources'], 'release_id': manifest['release_id'],
              'manifest_sha256': hashlib.sha256(canonical(manifest)).hexdigest(),
              'provider': provider, 'passed': False, 'source_unchanged': False, 'steps': []}
    code = 1
    try:
        for index, command in enumerate(COMMANDS):
            log = root / ('native-' + str(index) + '.log')
            code = execute(command, workspace, log)
            report['steps'].append({'command': command, 'exit_code': code,
                                   'log': {'path': log.name, 'sha256': digest(log)}})
            if code != 0:
                break
        checked_sources(workspace, manifest)
        report['source_unchanged'] = True
        if code == 0 and len(report['steps']) == len(COMMANDS):
            for key, name in [('native_ci', 'native-ci.json'), ('inputs', 'inputs.json')]:
                path = root / 'paired-gchat' / name
                report[key] = {'path': path.relative_to(root).as_posix(), 'sha256': digest(path)}
            report['passed'] = True
    finally:
        (root / 'qualification.json').write_bytes(canonical(report))
    if report['passed']:
        verify(root, manifest, environment)
    return code


def validate_artifact(artifact, artifact_id, sha, manifest, environment):
    expected = context(manifest, environment)
    name = artifact.get('name', '')
    match = re.fullmatch(ARTIFACT + r'-([1-9][0-9]*)', name)
    require(type(artifact.get('id')) is int and str(artifact['id']) == artifact_id and
            match is not None and int(match[1]) <= expected['run_attempt'] and
            artifact.get('expired') is False,
            'qualification artifact is missing, expired or ambiguous')
    require(re.fullmatch(r'[0-9a-f]{64}', sha) is not None and
            artifact.get('digest') == 'sha256:' + sha,
            'qualification artifact digest differs from the qualifying job')
    run = artifact.get('workflow_run', {})
    require(type(run.get('id')) is int and str(run['id']) == expected['run_id'] and
            run.get('head_sha') == manifest['sources']['gchat']['commit'],
            'qualification artifact belongs to another workflow run')
    size = artifact.get('size_in_bytes')
    require(type(size) is int and 0 < size <= 12 * 1024 ** 3,
            'qualification artifact exceeds download budget')


def fetch(workspace, manifest, environment, artifact_id, sha):
    require(re.fullmatch(r'[1-9][0-9]*', artifact_id) is not None, 'invalid qualification artifact ID')
    checked_sources(workspace, manifest)
    artifact = gh('actions/artifacts/' + artifact_id)
    validate_artifact(artifact, artifact_id, sha, manifest, environment)
    archive = workspace / 'qualification.zip'
    with archive.open('xb') as stream:
        subprocess.run(['gh', 'api', 'repos/IggyGG/gchat/actions/artifacts/' + artifact_id + '/zip'],
                       stdout=stream, stderr=subprocess.PIPE, check=True, timeout=600)
    require(archive.stat().st_size == artifact['size_in_bytes'] and digest(archive) == sha,
            'qualification archive download hash mismatch')
    root = workspace / 'native-evidence'
    root.mkdir(exist_ok=False)
    extract(archive, root)
    report = verify(root, manifest, environment)
    require(artifact['name'] == ARTIFACT + '-' + str(report['provider']['run_attempt']),
            'qualification artifact attempt differs from the native receipt')
    checked_sources(workspace, manifest)
    (root / 'handoff.json').write_bytes(canonical({
        'schema': 1, 'artifact_id': int(artifact_id), 'archive_sha256': sha,
        'provider': context(manifest, environment), 'release_id': manifest['release_id'],
    }))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['qualify', 'fetch'])
    parser.add_argument('--artifact-id')
    parser.add_argument('--sha256')
    args = parser.parse_args()
    manifest = validate(read_json(os.environ['GCHAT_RELEASE_MANIFEST']))
    if args.action == 'qualify':
        raise SystemExit(qualify(Path.cwd(), manifest, os.environ))
    if not args.artifact_id or not args.sha256:
        parser.error('fetch requires the qualifying job artifact ID and digest')
    fetch(Path.cwd(), manifest, os.environ, args.artifact_id, args.sha256)


if __name__ == '__main__':
    main()
