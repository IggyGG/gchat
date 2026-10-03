"""Reconcile registered retained iOS follow-ups and preserve original verdicts."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import zipfile
import time
import re

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


def validate_run(manifest, run, artifact, rule=RULE):
    require(manifest['release_id'] == rule['release_id'], 'no reviewed iOS recovery for this candidate')
    require(run.get('id') == rule['run'] and run.get('head_sha') == rule['controller']
            and run.get('path') == '.github/workflows/ios-verify.yml'
            and run.get('head_repository', {}).get('full_name') == 'IggyGG/gchat'
            and run.get('display_title') == 'iOS retained verification ' + rule['request']
            and run.get('event') == 'workflow_dispatch' and run.get('status') == 'completed'
            and run.get('conclusion') == 'success', 'iOS follow-up identity or result differs')
    require(artifact.get('id') == rule['artifact'] and artifact.get('expired') is False
            and artifact.get('workflow_run', {}).get('id') == rule['run']
            and artifact.get('digest') == 'sha256:' + rule['sha256']
            and artifact.get('size_in_bytes') == rule.get('size', 316898149), 'iOS follow-up archive differs')


def registered(manifest):
    from release_macos_recovery import REGISTRY
    path = Path(os.environ.get('GCHAT_NATIVE_RECOVERIES', str(REGISTRY)))
    if not path.exists(): return None
    value = json.loads(path.read_text())
    require(value.get('schema') == 1 and isinstance(value.get('recoveries'), list), 'invalid native recovery registry')
    matches = [v for v in value['recoveries'] if v.get('release_id') == manifest['release_id'] and v.get('target') == 'ios']
    require(len(matches) <= 1, 'ambiguous iOS recovery registration')
    if not matches: return None
    config = matches[0]
    require(config.get('kind') == 'ios-retained' and config.get('sources') == manifest['sources'],
            'iOS recovery source differs')
    require(all(type(config.get(k)) is int and config[k] > 0 for k in ('original_run', 'original_artifact'))
            and all(re.fullmatch('[0-9a-f]{64}', str(config.get(k, ''))) for k in ('original_sha256', 'ipa')),
            'iOS recovery original identity differs')
    return config


def verification_marker(manifest, work, config, intent, api):
    marker = work / 'ios-retained-verification-dispatch.json'
    if not marker.exists() or json.loads(marker.read_text())['intent'] == intent:
        return marker
    old = json.loads(marker.read_text())['intent']
    previous = config.get('previous_verification', {})
    require(previous.get('controller') == old.get('controller') and previous.get('request') == old.get('request')
            and previous.get('ref') == old.get('ref') and type(previous.get('run')) is int
            and previous['run'] > 0 and old.get('inputs') == intent['inputs']
            and intent['controller'] != old['controller']
            and intent['request'] == hashlib.sha256(__import__('release_pair').canonical(
                ['ios-retained-verification-followup', old['request'], intent['controller']])).hexdigest(),
            'iOS retained verification intent changed without a reviewed failed predecessor')
    failed = api(f'actions/runs/{previous["run"]}')
    require(failed.get('id') == previous['run'] and failed.get('head_sha') == old['controller']
            and failed.get('head_branch') == old['ref'] and failed.get('path') == '.github/workflows/ios-verify.yml'
            and failed.get('display_title') == 'iOS retained verification ' + old['request']
            and failed.get('head_repository', {}).get('full_name') == 'IggyGG/gchat'
            and failed.get('event') == 'workflow_dispatch' and failed.get('status') == 'completed'
            and failed.get('conclusion') in ('failure', 'cancelled', 'timed_out', 'startup_failure', 'action_required'),
            'iOS verification predecessor is unknown or did not fail on its frozen source')
    directory = work / 'ios-retained-verification-followups' / intent['controller']
    directory.mkdir(parents=True, exist_ok=True)
    failure = directory / 'original-failure.json'
    if failure.exists():
        proof = json.loads(failure.read_text())
        require(proof.get('passed') is False and proof.get('release_id') == manifest['release_id']
                and proof.get('sources') == manifest['sources'] and proof.get('original_intent_sha256') == sha(marker)
                and proof.get('run_sha256') == sha(directory/'original-failed-run.json')
                and proof.get('artifacts_sha256') == sha(directory/'original-failed-artifacts.json'),
                'retained iOS verification failure evidence changed')
    else:
        inventory = api(f'actions/runs/{previous["run"]}/artifacts?per_page=100')
        require(isinstance(inventory.get('artifacts'), list) and len(inventory['artifacts']) < 100,
                'iOS failed verification artifact inventory is incomplete')
        atomic_json(directory / 'original-failed-run.json', failed)
        atomic_json(directory / 'original-failed-artifacts.json', inventory)
        atomic_json(failure, {'passed':False, 'release_id':manifest['release_id'],
                    'sources':manifest['sources'], 'original_intent_sha256':sha(marker),
                    'run_sha256':sha(directory/'original-failed-run.json'),
                    'artifacts_sha256':sha(directory/'original-failed-artifacts.json')})
    replacement = directory / 'dispatch.json'
    require(not replacement.exists() or json.loads(replacement.read_text())['intent'] == intent,
            'iOS verification follow-up intent changed')
    return replacement


def retained_followup(manifest, work, original, config):
    from release_jobs import gh
    require(original.get('id') == config['original_run'] and original.get('status') == 'completed'
            and original.get('conclusion') == 'failure' and original.get('head_sha') == manifest['sources']['gchat']['commit']
            and original.get('path') == '.github/workflows/ios-release.yml'
            and original.get('event') == 'workflow_dispatch'
            and original.get('head_repository', {}).get('full_name') == 'IggyGG/gchat', 'unexpected original iOS failure')
    lifecycle = config['lifecycle']
    run = gh(f'actions/runs/{lifecycle["run"]}')
    require(run.get('id') == lifecycle['run'] and run.get('head_sha') == lifecycle['controller']
            and run.get('path') == '.github/workflows/ios-lifecycle.yml' and run.get('event') == 'workflow_dispatch'
            and run.get('head_repository', {}).get('full_name') == 'IggyGG/gchat'
            and run.get('display_title') == 'iOS lifecycle ' + lifecycle['request'], 'iOS lifecycle identity differs')
    if run.get('status') != 'completed': return None
    require(run.get('conclusion') == 'success', 'retained iOS lifecycle did not pass')
    candidates = gh(f'actions/runs/{run["id"]}/artifacts?per_page=100')['artifacts']
    matches = [a for a in candidates if a.get('name') == 'ios-lifecycle-' + lifecycle['request'] and a.get('expired') is False]
    require(len(matches) == 1, 'retained iOS lifecycle artifact is missing or ambiguous')
    artifact = gh(f'actions/artifacts/{matches[0]["id"]}')
    require(artifact.get('workflow_run', {}).get('id') == run['id'] and artifact.get('expired') is False
            and artifact.get('name') == 'ios-lifecycle-' + lifecycle['request']
            and re.fullmatch('sha256:[0-9a-f]{64}', artifact.get('digest', ''))
            and 0 < artifact.get('size_in_bytes', 0) <= 1024 ** 3, 'iOS lifecycle artifact differs')
    simulator = {'mode': 'retained_original', 'run_id': run['id'], 'artifact_id': artifact['id'],
                 'artifact_sha256': artifact['digest'].split(':', 1)[1],
                 'controller_commit': lifecycle['controller'], 'request_id': lifecycle['request']}
    inputs = {'artifact_sha256': config['original_sha256'],
              'gchat_commit': manifest['sources']['gchat']['commit'], 'gcoms_commit': manifest['sources']['gcoms']['commit'],
              'build_number': manifest['versions']['ios'], 'run_id': config['original_run'],
              'artifact_id': config['original_artifact'], 'simulator': simulator}
    verification = config['verification']
    intent = {'controller': verification['controller'], 'ref': verification['ref'],
              'request': verification['request'], 'inputs': inputs}
    marker = verification_marker(manifest, work, config, intent, gh)
    runs = []
    for page in range(1, 11):
        items = gh(f'actions/workflows/ios-verify.yml/runs?event=workflow_dispatch&per_page=100&page={page}')['workflow_runs']
        runs.extend(r for r in items if r.get('display_title') == 'iOS retained verification ' + intent['request'])
        if runs or len(items) < 100: break
    require(len(runs) <= 1, 'duplicate iOS retained verification request requires reconciliation')
    if not runs:
        if marker.exists():
            require(time.time() - json.loads(marker.read_text())['at'] <= 1800,
                    'iOS verification dispatch outcome is unknown; no blind resubmission')
            return None
        ref = gh('git/ref/heads/' + verification['ref'])
        require(ref.get('object', {}).get('sha') == verification['controller'], 'iOS verification frozen helper ref differs')
        body = {'original_run_id': str(inputs['run_id']), 'artifact_id': str(inputs['artifact_id']),
                'artifact_sha256': inputs['artifact_sha256'], 'simulator_input': json.dumps(simulator),
                'gchat_commit': inputs['gchat_commit'], 'gcoms_commit': inputs['gcoms_commit'],
                'build_number': inputs['build_number'], 'request_id': intent['request'], 'upload_testflight': False}
        atomic_json(marker, {'at': int(time.time()), 'intent': intent})
        try:
            gh('actions/workflows/ios-verify.yml/dispatches', method='POST', body={'ref': verification['ref'], 'inputs': body})
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass  # Preserve intent and read the same request; a lost reply is not a new dispatch.
        return None
    followup = runs[0]
    require(followup.get('head_sha') == verification['controller'] and followup.get('path') == '.github/workflows/ios-verify.yml'
            and followup.get('event') == 'workflow_dispatch' and followup.get('head_repository', {}).get('full_name') == 'IggyGG/gchat',
            'iOS verification provider differs')
    if followup.get('status') != 'completed': return None
    require(followup.get('conclusion') == 'success', 'retained signed iOS verification did not pass')
    candidates = gh(f'actions/runs/{followup["id"]}/artifacts?per_page=100')['artifacts']
    matches = [a for a in candidates if a.get('name') == 'ios-verified-' + intent['request'] and a.get('expired') is False]
    require(len(matches) == 1, 'iOS verification archive missing or ambiguous')
    verified = gh(f'actions/artifacts/{matches[0]["id"]}')
    require(re.fullmatch('sha256:[0-9a-f]{64}', verified.get('digest', ''))
            and verified.get('name') == 'ios-verified-' + intent['request'] and verified.get('expired') is False
            and 0 < verified.get('size_in_bytes', 0) <= 1024 ** 3, 'iOS verification archive is not immutable or bounded')
    rule = {'release_id': manifest['release_id'], 'run': followup['id'], 'artifact': verified['id'],
            'sha256': verified['digest'].split(':', 1)[1], 'size': verified['size_in_bytes'],
            'controller': verification['controller'], 'request': verification['request'],
            'original_run': config['original_run'], 'ipa': config['ipa'], 'inputs': inputs, 'registration': config}
    validate_run(manifest, followup, verified, rule)
    return rule


def collect(manifest, work, original):
    from release_jobs import gh, extract
    config = registered(manifest)
    rule = retained_followup(manifest, work, original, config) if config else RULE
    if rule is None: return None
    require(original.get('id') == rule['original_run'] and original.get('conclusion') == 'failure',
            'unexpected original iOS failure')
    run = gh(f"actions/runs/{rule['run']}"); artifact = gh(f"actions/artifacts/{rule['artifact']}")
    validate_run(manifest, run, artifact, rule)
    archive = work / 'native.zip'
    if not archive.exists():
        cache = work.parent.parent / 'recovery-cache' / (rule['sha256'] + '.zip')
        if cache.exists():
            require(sha(cache) == rule['sha256'], 'cached iOS artifact changed')
            os.link(cache, archive)
        else:
            partial = work / 'native.partial'
            with partial.open('wb') as stream:
                subprocess.run(['gh', 'api', f"repos/IggyGG/gchat/actions/artifacts/{rule['artifact']}/zip"],
                               stdout=stream, stderr=subprocess.PIPE, check=True, timeout=600)
            require(sha(partial) == rule['sha256'], 'iOS follow-up download differs')
            partial.replace(archive)
    require(sha(archive) == rule['sha256'] and archive.stat().st_size == artifact['size_in_bytes'],
            'retained iOS archive changed')
    if not (work / 'ios-recovery.json').exists():
        if (work / 'native').exists(): shutil.rmtree(work / 'native')
        extract(archive, work / 'native')
        atomic_json(work / 'ios-followup-run.json', run)
        atomic_json(work / 'ios-followup-artifact.json', artifact)
        atomic_json(work / 'ios-recovery.json', rule)
    names = ('native.zip', 'ios-followup-run.json', 'ios-followup-artifact.json', 'ios-recovery.json')
    return {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
            'platform': 'ios', 'stage': 'build', 'passed': True, 'source_unchanged': True,
            'external_id': str(rule['run']), 'original_workflow_conclusion': 'failure',
            'retained_ios_followup': True,
            'evidence': [{'path': name, 'sha256': sha(work / name)} for name in names]}


def validate_report(manifest, report, rule=RULE, inputs=INPUTS):
    require(report.get('scope') == 'ios_retained_pair_simulator_and_signed_ipa'
            and report.get('passed') is True and report.get('sources_unchanged') is True
            and report.get('sources') == manifest['sources'] and report.get('inputs') == inputs,
            'iOS native follow-up scope/source differs')
    require(all(report.get(k) is False for k in ('application_recompiled', 'device_resigned',
            'original_build_passed', 'physical_device_qualified', 'push_qualified'))
            and all(report.get(k) is True for k in ('original_build_verdict_unchanged',
            'simulator_reused_from_original')), 'iOS original artifact/verdict was not preserved')
    app = report['application']
    require(app['ipa']['sha256'] == rule['ipa'] and app['bundle'] == 'boo.gchat.app'
            and app['build_number'] == manifest['versions']['ios'] == inputs['build_number']
            and app['marketing_version'] == manifest['versions']['linux-x86_64']
            and app['profile']['certificate_sha256'] == manifest['policy']['ios_certificate_sha256'],
            'iOS signed identity or version differs')


def reviewed_inputs(manifest, rule):
    inputs = INPUTS
    if rule != RULE:
        config = registered(manifest)
        require(config is not None and rule.get('registration') == config and rule.get('original_run') == config['original_run']
                and rule.get('ipa') == config['ipa'] and rule.get('controller') == config['verification']['controller']
                and rule.get('request') == config['verification']['request'], 'iOS recovery registry differs')
        inputs = rule['inputs']
        require(inputs['run_id'] == config['original_run'] and inputs['artifact_id'] == config['original_artifact']
                and inputs['artifact_sha256'] == config['original_sha256']
                and inputs['build_number'] == manifest['versions']['ios']
                and all(inputs[p + '_commit'] == manifest['sources'][p]['commit'] for p in ('gchat', 'gcoms'))
                and inputs['simulator']['run_id'] == config['lifecycle']['run']
                and inputs['simulator']['controller_commit'] == config['lifecycle']['controller']
                and inputs['simulator']['request_id'] == config['lifecycle']['request']
                and inputs['simulator']['mode'] == 'retained_original', 'iOS recovery inputs differ')
    return inputs


def reference(item, root):
    parts = PurePosixPath(item['path']).parts
    require(parts.count('ios-verification') == 1, 'unexpected iOS reference root')
    relative = Path(*parts[parts.index('ios-verification') + 1:])
    require(relative.parts and '..' not in relative.parts and '\\' not in item['path'], 'unsafe iOS reference')
    path = root / relative
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve())
            and sha(path) == item['sha256'] and path.stat().st_size == item['size'],
            'iOS native reference changed')
    return path


def verify(manifest, directory, output):
    work = directory.parent
    rule = json.loads((work / 'ios-recovery.json').read_text())
    inputs = reviewed_inputs(manifest, rule)
    validate_run(manifest, json.loads((work / 'ios-followup-run.json').read_text()),
                 json.loads((work / 'ios-followup-artifact.json').read_text()), rule)
    require(sha(work / 'native.zip') == rule['sha256'], 'iOS native archive changed')
    root = directory / 'ios-verification'; report_path = root / 'build.json'
    report = json.loads(report_path.read_text()); validate_report(manifest, report, rule, inputs)
    ipa = reference(report['application']['ipa'], root)
    retained = [report_path, ipa, reference(report['original_build'], root), reference(report['signing_cleanup'], root),
                reference(report['simulator'], root), reference(report['simulator_binding']['verification'], root)]
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
