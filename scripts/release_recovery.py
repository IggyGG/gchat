"""Admit a reviewed follow-up for an immutable failed-worker artifact.

This registry is deliberately narrow. It is not a retry loop, does not mutate
original reports, and does not grant application, rollback or fleet acceptance.
"""
import hashlib
import json
from pathlib import Path
import subprocess

from release_coordinator import atomic_json
from release_pair import canonical

WINDOWS36 = {
    'release_id': 'c6165120748d3adc093e7a0cfff84f6ad99546e3b48a08eb980b1758b34b637b',
    'original_run': 36413216786, 'original_artifact': 10970753773,
    'original_sha256': '4d567ce80b4bb813570f2c5439f74b4e0fc5512fef56f2e4bd77d76c007172b2',
    'followup_run': 36471307753, 'followup_artifact': 10992341339,
    'followup_sha256': '86db70076e391635391b3e1a3692ccfdb95cf61f21636c39d50b3dde19eb1fea',
    'controller_commit': '5b8a728df36e8cd4a5c0a8295547b74b5e0b64df',
    'request_id': 'windows36-4mib-20260928-5b8a728d',
}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_runs(manifest, target, original, followup):
    rule = WINDOWS36
    require(target == 'windows-x86_64' and manifest['release_id'] == rule['release_id'],
            'no retained recovery is registered for this candidate/platform')
    for run, run_id, commit, workflow, conclusion in (
        (original, rule['original_run'], manifest['sources']['gchat']['commit'], 'windows-release.yml', 'failure'),
        (followup, rule['followup_run'], rule['controller_commit'], 'windows-verify.yml', 'success')):
        require(run.get('id') == run_id and run.get('head_sha') == commit
                and run.get('path') == '.github/workflows/' + workflow
                and run.get('event') == 'workflow_dispatch' and run.get('status') == 'completed'
                and run.get('conclusion') == conclusion
                and run.get('head_repository', {}).get('full_name') == 'IggyGG/gchat',
                'retained recovery run identity/result differs')
    require(followup.get('display_title') == 'Windows retained installer verification ' + rule['request_id'],
            'retained recovery request identity differs')


def collect(manifest, target, work, original):
    if target.startswith('macos'):
        from release_macos_recovery import rule_for, collect as collect_macos
        rule = rule_for(manifest, target)
        if rule is not None:
            return collect_macos(manifest, target, work, original, rule)
    if target == 'ios':
        from release_ios_recovery import collect as collect_ios
        return collect_ios(manifest, work, original)
    from release_jobs import gh, extract
    rule = WINDOWS36
    if target != 'windows-x86_64' or manifest['release_id'] != rule['release_id']:
        raise ValueError('native worker failed; no reviewed retained recovery')
    followup = gh(f"actions/runs/{rule['followup_run']}")
    validate_runs(manifest, target, original, followup)
    recovery = work / 'recovery'
    recovery.mkdir(exist_ok=True)
    references = []
    for prefix, run in (('original', original), ('followup', followup)):
        artifact_id = rule[prefix + '_artifact']
        expected = rule[prefix + '_sha256']
        artifact = gh(f'actions/artifacts/{artifact_id}')
        require(artifact.get('id') == artifact_id and artifact.get('workflow_run', {}).get('id') == run['id']
                and artifact.get('expired') is False and artifact.get('digest') == 'sha256:' + expected
                and type(artifact.get('size_in_bytes')) is int and 0 < artifact['size_in_bytes'] <= 12 * 1024**3,
                'retained recovery artifact binding differs')
        archive = recovery / (prefix + '.zip')
        if not archive.exists():
            partial = recovery / (prefix + '.partial')
            with partial.open('wb') as stream:
                subprocess.run(['gh', 'api', f'repos/IggyGG/gchat/actions/artifacts/{artifact_id}/zip'],
                               stdout=stream, stderr=subprocess.PIPE, check=True, timeout=600)
            require(partial.stat().st_size == artifact['size_in_bytes'] and sha(partial) == expected,
                    'retained recovery download differs')
            partial.replace(archive)
        require(sha(archive) == expected and archive.stat().st_size == artifact['size_in_bytes'],
                'retained recovery archive changed')
        destination = work / 'native' if prefix == 'original' else recovery / 'followup'
        marker = recovery / (prefix + '-extracted.json')
        if not marker.exists():
            # Only incomplete derived files inside this job are replaced.
            import shutil
            if destination.exists():
                shutil.rmtree(destination)
            extract(archive, destination)
            atomic_json(marker, {'sha256': expected})
        atomic_json(recovery / (prefix + '-run.json'), run)
        for file in (archive, recovery / (prefix + '-run.json')):
            references.append({'path': file.relative_to(work).as_posix(), 'sha256': sha(file)})
    # Archive the exact qualification source independently of the artifact's
    # source. An immutable Git object is required; a moving checkout is never used.
    mirror = work.parent.parent / 'mirrors/gchat.git'
    require(subprocess.check_output(['git', '-C', str(mirror), 'rev-parse', '--is-bare-repository'],
                                    text=True).strip() == 'true', 'expected isolated bare source mirror')
    commit = rule['controller_commit']
    subprocess.run(['git', '-C', str(mirror), 'fetch', '--no-tags', 'origin', commit],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
    archive = recovery / 'qualification-source.tar'
    source = subprocess.check_output(['git', '-C', str(mirror), 'archive', '--format=tar', commit])
    if archive.exists():
        require(archive.read_bytes() == source, 'qualification archive changed')
    else:
        archive.write_bytes(source)
    references.append({'path': archive.relative_to(work).as_posix(), 'sha256': sha(archive)})
    atomic_json(recovery / 'binding.json', rule)
    references.append({'path': 'recovery/binding.json', 'sha256': sha(recovery / 'binding.json')})
    # This stage binds collected evidence. The separate native/signature verifier
    # must check every original gate and the replacement installed journey.
    return {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
            'platform': target, 'stage': 'build', 'passed': True, 'source_unchanged': True,
            'external_id': str(original['id']), 'original_workflow_conclusion': 'failure',
            'followup_run_id': followup['id'], 'recovery_requires_verification': True, 'evidence': references}


def verify_windows(manifest, root, recovery, worker):
    from release_verify import load_module
    rule = WINDOWS36
    require(manifest['release_id'] == rule['release_id']
            and json.loads((recovery / 'binding.json').read_text()) == rule,
            'retained recovery registry differs')
    validate_runs(manifest, 'windows-x86_64', json.loads((recovery / 'original-run.json').read_text()),
                  json.loads((recovery / 'followup-run.json').read_text()))
    require(sha(recovery / 'original.zip') == rule['original_sha256']
            and sha(recovery / 'followup.zip') == rule['followup_sha256'], 'retained archives changed')
    # Compare every extracted member with its authenticated archive before use.
    import zipfile
    for archive, directory in ((recovery / 'original.zip', root), (recovery / 'followup.zip', recovery / 'followup')):
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                if member.is_dir():
                    continue
                path = directory / member.filename
                require(path.is_file() and path.stat().st_size == member.file_size
                        and sha(path) == hashlib.sha256(bundle.read(member)).hexdigest(), 'extracted recovery evidence changed')
    followup = recovery / 'followup'
    summary = json.loads((followup / 'summary.json').read_text())
    expected = {k: v['commit'] for k, v in manifest['sources'].items()}
    require(summary.get('passed') is True and summary.get('sources') == expected
            and summary.get('application_rebuilt') is False and summary.get('native_ci_repeated') is False
            and summary.get('invitation_removed') is True and summary.get('original_workflow_conclusion') == 'failure'
            and summary.get('run_id') == rule['original_run'] and summary.get('artifact_id') == rule['original_artifact']
            and summary.get('archive_sha256') == rule['original_sha256'], 'follow-up does not qualify the original artifact')
    network_tool = load_module('windows-network')
    network_tool.original_network_failure(root)
    require(summary.get('original_failed_network_receipt_sha256') == sha(root / 'application-smoke/network/report.json'),
            'original failed evidence differs')
    policy = network_tool.qualification_policy('windows36', summary.get('file_qualification_bytes'))
    require(policy is not None and sha(policy) == summary.get('qualification_policy_sha256')
            and sha(followup / 'qualification-policy.json') == sha(policy), 'qualification policy differs')
    build = worker.collect(root, expected, lifecycle_source_archive=recovery / 'qualification-source.tar',
                           qualification_source_archive=recovery / 'qualification-source.tar',
                           smoke_directory=followup / 'execution')
    return build
