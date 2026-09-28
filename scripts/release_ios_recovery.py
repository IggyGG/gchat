"""One reviewed iOS follow-up; preserve the original failed build verdict."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import zipfile

from release_coordinator import atomic_json

RULE = {
    'release_id': 'c6165120748d3adc093e7a0cfff84f6ad99546e3b48a08eb980b1758b34b637b',
    'run': 36480227371, 'artifact': 10996271684,
    'sha256': '4c5907a7f8a0ac6c7889feed729a27a0abf0ab1302df2052c346814eb60bf0b0',
    'controller': 'e4670448f1f9c0160a158e5e760001eb4bf57ab3',
    'request': 'ios36-verified-retained-20260928-e4670448',
    'original_run': 36413233114,
    'ipa': '60727be1e1e3712ca646d5825e00305f53a8e612363537c40db2a3a5e3d2aaf3',
}
INPUTS = {
    'artifact_sha256': '728f35cb68fe4d42304d17c391a4d2c79595ea714a887e119875d70590fc8560',
    'gchat_commit': '21ad84ed266fdc237fd745e4b1aca6139b6d6728',
    'gcoms_commit': '8cdfd3fee2ab7809f1c348dc3a60ef24393b4101',
    'build_number': '1.0.59', 'run_id': 36413233114, 'artifact_id': 10970232512,
    'simulator': {'mode': 'retained_original', 'run_id': 36478326361, 'artifact_id': 10996880637,
        'artifact_sha256': '864f727c9715ca4538dabb6f5a087e2f8060af4dd4f4cd472a6118df35030beb',
        'controller_commit': RULE['controller'], 'request_id': 'ios36-keyboard-fixed-20260928-e4670448'},
}


def require(value, message):
    if not value: raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_run(manifest, run, artifact):
    require(manifest['release_id'] == RULE['release_id'], 'no reviewed iOS recovery for this candidate')
    require(run.get('id') == RULE['run'] and run.get('head_sha') == RULE['controller']
            and run.get('path') == '.github/workflows/ios-verify.yml'
            and run.get('head_repository', {}).get('full_name') == 'IggyGG/gchat'
            and run.get('display_title') == 'iOS retained verification ' + RULE['request']
            and run.get('event') == 'workflow_dispatch' and run.get('status') == 'completed'
            and run.get('conclusion') == 'success', 'iOS follow-up identity or result differs')
    require(artifact.get('id') == RULE['artifact'] and artifact.get('expired') is False
            and artifact.get('workflow_run', {}).get('id') == RULE['run']
            and artifact.get('digest') == 'sha256:' + RULE['sha256']
            and artifact.get('size_in_bytes') == 316898149, 'iOS follow-up archive differs')


def collect(manifest, work, original):
    from release_jobs import gh, extract
    require(original.get('id') == RULE['original_run'] and original.get('conclusion') == 'failure',
            'unexpected original iOS failure')
    run = gh(f"actions/runs/{RULE['run']}"); artifact = gh(f"actions/artifacts/{RULE['artifact']}")
    validate_run(manifest, run, artifact)
    archive = work / 'native.zip'
    if not archive.exists():
        cache = work.parent.parent / 'recovery-cache' / (RULE['sha256'] + '.zip')
        if cache.exists():
            require(sha(cache) == RULE['sha256'], 'cached iOS artifact changed')
            os.link(cache, archive)
        else:
            partial = work / 'native.partial'
            with partial.open('wb') as stream:
                subprocess.run(['gh', 'api', f"repos/IggyGG/gchat/actions/artifacts/{RULE['artifact']}/zip"],
                               stdout=stream, stderr=subprocess.PIPE, check=True, timeout=600)
            require(sha(partial) == RULE['sha256'], 'iOS follow-up download differs')
            partial.replace(archive)
    require(sha(archive) == RULE['sha256'] and archive.stat().st_size == artifact['size_in_bytes'],
            'retained iOS archive changed')
    if not (work / 'ios-recovery.json').exists():
        if (work / 'native').exists(): shutil.rmtree(work / 'native')
        extract(archive, work / 'native')
        atomic_json(work / 'ios-followup-run.json', run)
        atomic_json(work / 'ios-followup-artifact.json', artifact)
        atomic_json(work / 'ios-recovery.json', RULE)
    names = ('native.zip', 'ios-followup-run.json', 'ios-followup-artifact.json', 'ios-recovery.json')
    return {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
            'platform': 'ios', 'stage': 'build', 'passed': True, 'source_unchanged': True,
            'external_id': str(RULE['run']), 'original_workflow_conclusion': 'failure',
            'retained_ios_followup': True,
            'evidence': [{'path': name, 'sha256': sha(work / name)} for name in names]}


def validate_report(manifest, report):
    require(report.get('scope') == 'ios_retained_pair_simulator_and_signed_ipa'
            and report.get('passed') is True and report.get('sources_unchanged') is True
            and report.get('sources') == manifest['sources'] and report.get('inputs') == INPUTS,
            'iOS native follow-up scope/source differs')
    require(all(report.get(k) is False for k in ('application_recompiled', 'device_resigned',
            'original_build_passed', 'physical_device_qualified', 'push_qualified'))
            and all(report.get(k) is True for k in ('original_build_verdict_unchanged',
            'simulator_reused_from_original')), 'iOS original artifact/verdict was not preserved')
    app = report['application']
    require(app['ipa']['sha256'] == RULE['ipa'] and app['bundle'] == 'boo.gchat.app'
            and app['build_number'] == manifest['versions']['ios'] == INPUTS['build_number']
            and app['marketing_version'] == manifest['versions']['linux-x86_64']
            and app['profile']['certificate_sha256'] == manifest['policy']['ios_certificate_sha256'],
            'iOS signed identity or version differs')


def verify(manifest, directory, output):
    work = directory.parent
    require(json.loads((work / 'ios-recovery.json').read_text()) == RULE, 'iOS recovery registry differs')
    validate_run(manifest, json.loads((work / 'ios-followup-run.json').read_text()),
                 json.loads((work / 'ios-followup-artifact.json').read_text()))
    require(sha(work / 'native.zip') == RULE['sha256'], 'iOS native archive changed')
    root = directory / 'ios-verification'; report_path = root / 'build.json'
    report = json.loads(report_path.read_text()); validate_report(manifest, report)
    def reference(item):
        parts = PurePosixPath(item['path']).parts
        require(parts.count('ios-verification') == 1, 'unexpected iOS reference root')
        relative = Path(*parts[parts.index('ios-verification') + 1:])
        require(relative.parts and '..' not in relative.parts, 'unsafe iOS reference')
        path = root / relative
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve())
                and sha(path) == item['sha256'] and path.stat().st_size == item['size'],
                'iOS native reference changed')
        return path
    ipa = reference(report['application']['ipa'])
    retained = [report_path, ipa, reference(report['original_build']), reference(report['signing_cleanup']),
                reference(report['simulator']), reference(report['simulator_binding']['verification'])]
    require(json.loads(retained[2].read_text())['passed'] is False, 'original failed iOS verdict changed')
    for path in retained[3:]: require(json.loads(path.read_text()).get('passed') is True, 'iOS follow-up gate failed')
    with zipfile.ZipFile(work / 'native.zip') as archive:
        for path in retained:
            require(sha(path) == hashlib.sha256(archive.read(path.relative_to(directory).as_posix())).hexdigest(),
                    'extracted iOS verification evidence changed')
    destination = output.parent / 'verified'; destination.mkdir(exist_ok=True)
    evidence = []
    for path in [*retained, work / 'ios-recovery.json', work / 'ios-followup-run.json', work / 'ios-followup-artifact.json']:
        target = destination / (sha(path) + '-' + path.name)
        if not target.exists(): shutil.copyfile(path, target)
        require(sha(target) == sha(path), 'retained iOS verification changed')
        evidence.append({'path': target.relative_to(output.parent).as_posix(), 'sha256': sha(target)})
    result = {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
              'platform': 'ios', 'stage': 'verify', 'passed': True, 'source_unchanged': True,
              'retained_ios_followup': True, 'evidence': evidence}
    atomic_json(output, result); return result
