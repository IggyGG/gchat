"""Reconcile a registered Mac package follow-up without changing native verdicts."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

from release_coordinator import atomic_json

REGISTRY = Path(__file__).resolve().parents[1] / 'release/automation/qualification/native-recoveries.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def rule_for(manifest, target):
    path = Path(os.environ.get('GCHAT_NATIVE_RECOVERIES', str(REGISTRY)))
    if not path.exists():
        return None
    value = json.loads(path.read_text())
    require(value.get('schema') == 1 and isinstance(value.get('recoveries'), list), 'invalid native recovery registry')
    rules = [r for r in value['recoveries'] if r.get('release_id') == manifest['release_id'] and r.get('target') == target]
    require(len(rules) <= 1, 'ambiguous native recovery registration')
    if not rules:
        return None
    rule = rules[0]
    require(rule.get('kind') == 'macos-package' and target in ('macos-aarch64', 'macos-x86_64')
            and rule.get('sources') == manifest['sources'], 'Mac recovery source or target differs')
    for name in ('original_run', 'original_artifact', 'followup_run'):
        require(type(rule.get(name)) is int and rule[name] > 0, 'invalid Mac provider identity')
    for name, length in (('original_sha256', 64), ('controller_commit', 40), ('controller_tree', 40)):
        require(re.fullmatch('[0-9a-f]{' + str(length) + '}', str(rule.get(name, ''))), 'invalid Mac recovery source/hash')
    require(isinstance(rule.get('request_id'), str) and bool(rule['request_id']), 'Mac recovery has no request identity')
    return rule


def validate_runs(manifest, target, rule, original, followup):
    for run, expected, commit, workflow in (
            (original, rule['original_run'], manifest['sources']['gchat']['commit'], 'macos-release.yml'),
            (followup, rule['followup_run'], rule['controller_commit'], 'macos-package.yml')):
        require(run.get('id') == expected and run.get('head_sha') == commit
                and run.get('event') == 'workflow_dispatch' and run.get('path') == '.github/workflows/' + workflow
                and run.get('head_repository', {}).get('full_name') == 'IggyGG/gchat',
                'Mac recovery provider source, workflow or repository differs')
    require(original.get('status') == 'completed' and original.get('conclusion') == 'failure',
            'Mac recovery must preserve the original failed workflow')
    require(followup.get('display_title') == 'Forgejo macOS package ' + rule['request_id'],
            'Mac recovery request differs')
    if followup.get('status') != 'completed':
        return False
    require(followup.get('conclusion') == 'success', 'Mac packaging follow-up did not pass')
    return True


def validate_artifact(artifact, run, target):
    require(type(artifact.get('id')) is int and artifact['id'] > 0 and artifact.get('expired') is False
            and artifact.get('name') == target + '-package'
            and artifact.get('workflow_run', {}).get('id') == run['id']
            and artifact.get('workflow_run', {}).get('head_sha') == run['head_sha']
            and re.fullmatch('sha256:[0-9a-f]{64}', artifact.get('digest', ''))
            and 0 < artifact.get('size_in_bytes', 0) <= 1024 ** 3, 'Mac follow-up artifact identity differs')


def verify_extraction(archive, directory):
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            if entry.is_dir():
                continue
            path = directory / entry.filename
            require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(directory.resolve()),
                    'Mac follow-up extraction contains an unsafe path')
            with bundle.open(entry) as stream:
                require(path.stat().st_size == entry.file_size and
                        sha(path) == hashlib.file_digest(stream, 'sha256').hexdigest(),
                        'Mac extracted evidence differs from the immutable provider ZIP')


def collect(manifest, target, work, original, rule):
    from release_jobs import gh, extract
    followup = gh(f'actions/runs/{rule["followup_run"]}')
    if not validate_runs(manifest, target, rule, original, followup):
        return None
    artifacts = gh(f'actions/runs/{followup["id"]}/artifacts?per_page=100')['artifacts']
    selected = [a for a in artifacts if a.get('name') == target + '-package' and a.get('expired') is False]
    require(len(selected) == 1, 'Mac package artifact is missing or ambiguous')
    artifact = gh(f'actions/artifacts/{selected[0]["id"]}')
    validate_artifact(artifact, followup, target)
    archive = work / 'native.zip'
    if not archive.exists():
        partial = work / 'native.partial'
        with partial.open('wb') as stream:
            subprocess.run(['gh', 'api', f'repos/IggyGG/gchat/actions/artifacts/{artifact["id"]}/zip'],
                           stdout=stream, stderr=subprocess.PIPE, check=True, timeout=600)
        require('sha256:' + sha(partial) == artifact['digest'] and partial.stat().st_size == artifact['size_in_bytes'],
                'Mac package download differs')
        partial.replace(archive)
    require('sha256:' + sha(archive) == artifact['digest'] and archive.stat().st_size == artifact['size_in_bytes'],
            'retained Mac package archive changed')
    extracted = work / 'native'
    marker = work / 'macos-extracted.json'
    if not marker.exists():
        require(not extracted.exists(), 'retain the original extraction separately before admitting its Mac follow-up')
        extract(archive, extracted)
        atomic_json(marker, {'sha256': sha(archive)})
    require(json.loads(marker.read_text()) == {'sha256': sha(archive)}, 'Mac extraction identity changed')
    verify_extraction(archive, extracted)
    recovery = work / 'macos-recovery'
    recovery.mkdir(exist_ok=True)
    for name, value in (('rule.json', rule), ('original-run.json', original), ('followup-run.json', followup),
                        ('followup-artifact.json', artifact)):
        atomic_json(recovery / name, value)
    mirror = work.parent.parent / 'mirrors/gchat.git'
    subprocess.run(['git', '-C', str(mirror), 'fetch', '--no-tags', 'origin', rule['controller_commit']],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
    controller = subprocess.check_output(['git', '-C', str(mirror), 'archive', '--format=tar', rule['controller_commit']])
    (recovery / 'controller-source.tar').write_bytes(controller)
    atomic_json(work / 'macos-recovery.json', rule)
    paths = [archive, work / 'macos-recovery.json', *sorted(recovery.iterdir())]
    return {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
            'platform': target, 'stage': 'build', 'passed': True, 'source_unchanged': True,
            'external_id': str(followup['id']), 'original_workflow_conclusion': 'failure',
            'retained_macos_followup': True,
            'evidence': [{'path': p.relative_to(work).as_posix(), 'sha256': sha(p)} for p in paths]}


def verify(manifest, target, directory, root, helper):
    work = directory.parent
    rule = rule_for(manifest, target)
    require(rule is not None and json.loads((work / 'macos-recovery.json').read_text()) == rule,
            'Mac recovery registration changed')
    recovery = work / 'macos-recovery'
    original = json.loads((recovery / 'original-run.json').read_text())
    followup = json.loads((recovery / 'followup-run.json').read_text())
    require(validate_runs(manifest, target, rule, original, followup), 'Mac package provider is not complete')
    artifact = json.loads((recovery / 'followup-artifact.json').read_text())
    validate_artifact(artifact, followup, target)
    require('sha256:' + sha(work / 'native.zip') == artifact['digest'], 'Mac provider ZIP changed')
    verify_extraction(work / 'native.zip', directory)
    retry = directory / 'retry-evidence'
    report = json.loads((retry / 'report.json').read_text())
    expected = {p: v['commit'] for p, v in manifest['sources'].items()}
    native = helper.verify_native(retry / 'original-native', target, expected)
    require(report.get('schema') == 1 and report.get('scope') == 'macos_package_retry_existing_native'
            and report.get('passed') is True and report.get('native_tests_rerun') is False
            and report.get('sources') == manifest['sources'] and report.get('target') == target
            and report.get('native') == native and report.get('controller', {}).get('commit') == rule['controller_commit']
            and report['controller'].get('tree') == rule['controller_tree'], 'Mac retained native/package binding differs')
    helper.verify_origin(json.loads((retry / 'original-run.json').read_text()),
                         json.loads((retry / 'original-artifact.json').read_text()),
                         rule['original_run'], rule['original_artifact'], rule['original_sha256'], target, expected['gchat'])
    require(sha(retry / 'original-native.zip') == rule['original_sha256'], 'original Mac failure archive changed')
    require(report.get('build') == helper.reference(root / 'build.json')
            and report.get('application_smoke') == helper.reference(root / 'application-smoke/report.json'),
            'Mac package or installed smoke changed')
    require(json.loads((retry / 'original-release.json').read_text()) == manifest,
            'Mac packaging reserved a different candidate')
    packaging = json.loads((retry / 'packaging-helper.json').read_text())
    preflight = json.loads((retry / 'signing-preflight.json').read_text())
    require(packaging.get('passed') is True and preflight.get('passed') is True
            and packaging.get('sources') == preflight.get('sources') == manifest['sources']
            and packaging.get('controller') == preflight.get('controller') == report['controller']
            and packaging.get('build') == report['build'], 'Mac signing/package controller differs')
    entries = helper.archive_entries(recovery / 'controller-source.tar')
    for name in ('macos-package.py', 'build-installer.py', 'release_evidence.py'):
        require(packaging.get('controller_helpers', {}).get(name, {}).get('sha256') == entries['scripts/' + name][1],
                'Mac packaging helper differs from its frozen source')
    return native
