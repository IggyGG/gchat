#!/usr/bin/env python3
"""Dispatch retained native acceptance after rollout; retain grants and lost replies.

Only bootstrap canary authority reaches a verified running native worker through
encrypted delivery. Existing requests retain their original repository secret.
Deployment SSH/signing credentials remain in the coordinator.
Platform receipts require that platform's current/baseline and actual journey.
"""
import argparse
from contextlib import closing
import base64
import hashlib
import json
import os
import math
from pathlib import Path
import re
import sqlite3
import subprocess
import time
import zipfile

from release_coordinator import atomic_json, read_receipt
from release_deployment import inventory, invoke
from release_host_worker import ssh
from release_jobs import gh, extract
from release_network_canary import module, verify_journey
from release_pair import canonical, validate
from release_publish import job
from release_compatibility import verify as verify_compatibility
import release_acceptance_delivery as delivery
from acceptance_delivery import delivery_url, PROTOCOL

WORKFLOW = 'native-acceptance.yml'
MOBILE_WORKFLOW = 'mobile-acceptance.yml'
PREFIX = 'Native acceptance '
TARGETS = ('linux-x86_64', 'windows-x86_64', 'macos-aarch64', 'macos-x86_64', 'android', 'ios')


def qualification_revision(config, manifest):
    value = config.get('qualification_commit', os.environ.get('GCHAT_CONTROLLER_REVISION'))
    if value is None:
        return None  # Reconcile workers dispatched before separate qualification sources.
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{40}', value):
        raise ValueError('acceptance qualification needs a full immutable source object')
    return value


def qualification_ref(commit):
    if not isinstance(commit, str) or not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('acceptance qualification needs a full immutable source object')
    name = 'release/qualification-' + commit
    reference = 'refs/heads/' + name
    matches = gh('git/matching-refs/heads/' + name)
    if not matches:
        try:
            gh('git/refs', method='POST', body={'ref': reference, 'sha': commit})
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            # Publication can succeed before its response is lost. Read the same
            # immutable reference; never update or force-push an existing one.
            pass
        matches = [gh('git/ref/heads/' + name)]
    if (len(matches) != 1 or matches[0].get('ref') != reference
            or matches[0].get('object', {}).get('type') != 'commit'
            or matches[0]['object']['sha'] != commit):
        raise ValueError('acceptance qualification reference differs from its frozen source')
    return name


def verify_worker(binding, intent, manifest, target):
    if (binding.get('schema') != 1 or binding.get('request') != intent['request']
            or binding.get('release_id') != manifest['release_id']
            or binding.get('sources') != manifest['sources'] or binding.get('target') != target
            or binding.get('commit') != intent['qualification_commit']
            or binding.get('tree') != intent['qualification_tree']
            or binding.get('source_unchanged') is not True):
        raise ValueError('native acceptance qualification source or retained application binding differs')


def failed_followup(state, config, manifest, target, work, request, intent, revision):
    failed = work / 'acceptance-failed.json'
    if not failed.exists():
        return False, None
    proof = json.loads(failed.read_text())
    run_path, archive = work / 'acceptance-run.json', work / 'acceptance.zip'
    run = json.loads(run_path.read_text())
    expected = intent.get('qualification_commit', manifest['sources']['gchat']['commit'])
    workflow = MOBILE_WORKFLOW if target in ('android', 'ios') else WORKFLOW
    if (intent.get('request') != request or intent.get('sources') != manifest['sources']
            or intent.get('target') != target
            or proof.get('request') != request or proof.get('sources') != manifest['sources']
            or proof.get('release_id') != manifest['release_id'] or proof.get('target') != target
            or proof.get('qualification_commit') != expected or proof.get('passed') is not False
            or proof.get('run_sha256') != digest(run_path) or proof.get('archive_sha256') != digest(archive)
            or proof.get('intent_sha256') != digest(work / 'acceptance-intent.json')
            or run.get('status') != 'completed' or run.get('head_sha') != expected
            or run.get('conclusion') not in ('failure', 'cancelled', 'timed_out', 'startup_failure', 'action_required')
            or run.get('event') != 'workflow_dispatch' or run.get('path') != '.github/workflows/' + workflow
            or run.get('display_title') != PREFIX + request
            or run.get('head_repository', {}).get('full_name') != 'IggyGG/gchat'
            or intent.get('cleaned') is not True):
        raise ValueError('retained failed acceptance outcome changed; no follow-up may be dispatched')
    pointer = work / 'acceptance-followup.json'
    if pointer.exists():
        followup = json.loads(pointer.read_text())
    elif revision is not None and revision != expected:
        followup = {'commit': revision, 'request': hashlib.sha256(canonical(
            ['native-acceptance-followup', request, revision])).hexdigest()}
        atomic_json(pointer, followup)
    else:
        raise ValueError('native acceptance failed; original reports retained')
    commit = followup.get('commit', '')
    if (not re.fullmatch('[0-9a-f]{40}', commit) or commit == expected
            or followup.get('request') != hashlib.sha256(canonical(
                ['native-acceptance-followup', request, commit])).hexdigest()):
        raise ValueError('acceptance follow-up pointer differs')
    directory = work / 'followups' / commit
    directory.mkdir(parents=True, exist_ok=True)
    # A recorded follow-up keeps its worker even if the controller changes while
    # dispatch is unknown. collect() reconciles it before considering another one.
    result = collect(state, dict(config, qualification_commit=revision), manifest,
                     target, directory, followup['request'], frozen_revision=commit)
    if result is not None:
        result = dict(result, evidence=[dict(item, path='followups/' + commit + '/' + item['path'])
                                       for item in result['evidence']])
    return True, result


def digest(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def provider(state, manifest, target):
    directory = job(state, manifest, target, 'build')
    for stage in ('build', 'verify'):
        receipt = job(state, manifest, target, stage) / 'receipt.json'
        if not receipt.is_file(): return None
        read_receipt(receipt, manifest, target, stage)
    proof, _ = read_receipt(directory / 'receipt.json', manifest, target, 'build')
    archive = directory / 'native.zip'
    sha = digest(archive)
    if not any(ref['path'] == 'native.zip' and ref['sha256'] == sha for ref in proof['evidence']):
        raise ValueError('acceptance provider archive is not source-bound')
    with zipfile.ZipFile(archive) as source:
        reports = [name for name in source.namelist() if name.endswith('build.json') and not any(
            part in ('inputs', 'build', 'native-tests', 'infrastructure') for part in Path(name).parts[:-1])]
        if len(reports) != 1: raise ValueError('acceptance provider build report is ambiguous')
        build = json.loads(source.read(reports[0]))
    expected = {k: v['commit'] for k, v in manifest['sources'].items()}
    if target in ('android', 'ios'):
        sources = {key: value.get('commit') for key, value in build.get('sources', {}).items()}
        if build.get('passed') is not True or build.get('sources_unchanged') is not True or sources != expected:
            raise ValueError('mobile acceptance provider source/native verdict differs')
    else:
        sources = build.get('sources')
    if sources != expected or (target not in ('android', 'ios') and build.get('target') != target):
        raise ValueError('acceptance provider target/source differs')
    result = {'run': int(proof['external_id']), 'artifact': proof['worker']['artifact_id'],
              'controller': proof['worker']['workflow_commit'], 'archive': sha,
              'sources': sources, 'manifest': reports[0], 'conclusion': 'success'}
    if target == 'windows-x86_64':
        executables = [item for item in build['executables'] if item['name'] == 'gchat-desktop.exe']
        if len(executables) != 1: raise ValueError('acceptance needs one Windows executable')
        result['executable'] = executables[0]
    return result


def baseline(state, target, config, current):
    # Initial operator-bound seeds are a fallback. Each successful release can
    # supply the next baseline; do not pin every future upgrade to an old seed
    # or select this candidate/a newer release as its own predecessor.
    with closing(sqlite3.connect('file:' + str(state / 'ledger.sqlite') + '?mode=ro', uri=True)) as database:
        rows = database.execute("""SELECT c.manifest FROM platforms p JOIN candidates c ON c.id=p.candidate
            WHERE p.platform=? AND p.state='available'
              AND c.seq < (SELECT seq FROM candidates WHERE id=?) ORDER BY c.seq DESC""",
            (target, current['release_id'])).fetchall()
    expected = {key: value['commit'] for key, value in current['sources'].items()}
    for row in rows:
        try: result = provider(state, validate(json.loads(row[0])), target)
        except (KeyError, FileNotFoundError): continue
        if result is not None and result['sources'] != expected: return result
    seed = config.get('baselines', {}).get(target)
    return seed if seed is not None and seed['sources'] != expected else None


def cleanup(marker, intent, grant, state):
    if intent.get('cleaned') is True: return
    revoked = json.loads(ssh(grant, 'canary revoke ' + intent['operation'], b''))
    if revoked.get('revoked') is not True: raise ValueError('native acceptance grant was not revoked')
    if intent.get('delivery_protocol'):
        delivery.cleanup(state, intent['request'])
    else:
        names = json.loads(subprocess.check_output(['gh', 'secret', 'list', '--repo', 'IggyGG/gchat', '--json', 'name'], stderr=subprocess.PIPE))
        if any(item['name'] == intent['secret'] for item in names):
            gh('actions/secrets/' + intent['secret'], method='DELETE')
    intent['cleaned'] = True; atomic_json(marker, intent)


def qualify_native(report, rollback, network, manifest, target, specs, now):
    driver = module('test-mobile-upgrade' if target in ('android', 'ios') else 'test-native-upgrade')
    driver.validate_inputs(specs)
    if (report.get('schema') != 1 or report.get('passed') is not True
            or report.get('platform') != target or report.get('sources') != manifest['sources']
            or report.get('release_id') != manifest['release_id']
            or report.get('application_rebuilt') is not False or report.get('personal_profiles_accessed') is not False
            or report.get('invitation_removed') is not True
            or type(report.get('completed_at')) is not int or not 0 <= now - report['completed_at'] <= 3000
            or any(item.get('passed') is not True for item in report.get('installation_cleanup', []))):
        raise ValueError('native acceptance source, platform, cleanup or freshness failed')
    if target in ('android', 'ios') and (
            report.get('application_resigned') is not False or report.get('ui_driven') is not True
            or report.get('physical_device_qualified') is not False or not report.get('installation_cleanup')):
        raise ValueError('mobile acceptance needs the unchanged retained app and actual native UI')
    for name in ('current', 'baseline'):
        item = report.get('artifacts', {}).get(name, {})
        if (item.get('archive_sha256') != specs[name]['archive'] or item.get('sources') != specs[name]['sources']
                or not re.fullmatch('[0-9a-f]{64}', item.get('binary_sha256', ''))):
            raise ValueError('native acceptance used a different retained artifact')
    phases = rollback.get('phases', [])
    elapsed = rollback.get('elapsed_seconds')
    acknowledgments = [e for e in rollback.get('events', []) if e.get('event') == 'authenticated_ack']
    if (rollback.get('passed') is not True or rollback.get('cleanup_complete') is not True
            or rollback.get('profiles_removed') is not True or rollback.get('binaries_unchanged') is not True
            or type(elapsed) not in (int, float) or not math.isfinite(elapsed) or not 0 < elapsed <= 600
            or [phase.get('phase') for phase in phases] != ['upgraded', 'baseline', 'restored']
            or len(acknowledgments) < 8 or {e.get('sender') for e in acknowledgments} != {0, 1}):
        raise ValueError('actual native rollback and authenticated delivery did not pass')
    if report['artifacts']['current']['binary_sha256'] == report['artifacts']['baseline']['binary_sha256']:
        raise ValueError('native upgrade used the same installed binary for both releases')
    for phase, name in zip(phases, ('current', 'baseline', 'current')):
        if phase.get('binary_sha256') != report['artifacts'][name]['binary_sha256'] or any(
                phase.get(field) is not True for field in ('same_identity', 'history_retained', 'authenticated_bidirectional_ack')):
            raise ValueError('rollback phase changed identity, history or installed binary')
    if (not re.fullmatch('[0-9a-f]{64}', phases[0].get('cache_sha256', ''))
            or any(phase.get('cache_sha256') != phases[0]['cache_sha256'] for phase in phases[1:])):
        raise ValueError('retained encrypted cache hash changed across rollback')
    if target in ('android', 'ios') and (
            not re.fullmatch('[0-9a-f]{64}', phases[0].get('encrypted_cache_sha256', ''))
            or phases[0]['encrypted_cache_sha256'] == phases[0]['cache_sha256']
            or any(phase.get('encrypted_cache_sha256') != phases[0]['encrypted_cache_sha256']
                   for phase in phases[1:])):
        raise ValueError('actual retained mobile ciphertext changed across replacement')
    if network.get('inputs', {}).get('sources') != manifest['sources'] or network.get('binary_sha256') != report['artifacts']['current']['binary_sha256']:
        raise ValueError('installed-network journey used a different native application')
    verify_journey(network, manifest)
    if not re.fullmatch('[0-9a-f]{64}', network.get('file_check', {}).get('sha256', '')):
        raise ValueError('installed-network verified hash is missing')
    return report


def collect(state, config, manifest, target, work, request, *, frozen_revision=None):
    if target not in TARGETS: raise ValueError('native acceptance cannot qualify a different platform')
    marker = work / 'acceptance-intent.json'
    workflow = MOBILE_WORKFLOW if target in ('android', 'ios') else WORKFLOW
    grant = json.loads(Path(config['grant_config']).read_text())
    intent = json.loads(marker.read_text()) if marker.exists() else None
    revision = qualification_revision(config, manifest)
    if intent is not None:
        handled, result = failed_followup(state, config, manifest, target, work, request, intent, revision)
        if handled:
            return result
    if intent is None:
        current = provider(state, manifest, target); previous = baseline(state, target, config, manifest)
        if current is None or previous is None: return None
        driver = module('test-mobile-upgrade' if target in ('android', 'ios') else 'test-native-upgrade')
        inputs = {'target': target, 'current': current, 'baseline': previous}
        if target in ('android', 'ios'):
            inputs['peer_target'] = 'linux-x86_64' if target == 'android' else 'macos-aarch64'
            inputs['peer'] = provider(state, manifest, inputs['peer_target'])
            if inputs['peer'] is None: return None
        inputs = driver.validate_inputs(inputs)
        operation = hashlib.sha256(canonical(['native-acceptance', request])).hexdigest()
        intent = {'request': request, 'sources': manifest['sources'], 'target': target, 'inputs': inputs,
                  'operation': operation, 'secret': 'GCHAT_ACCEPTANCE_' + operation.upper(), 'created_at': int(time.time())}
        selected_revision = frozen_revision or revision
        if selected_revision is not None:
            reference = qualification_ref(selected_revision)
            source = gh('git/commits/' + selected_revision)
            tree = source.get('tree', {}).get('sha')
            if (source.get('sha') != selected_revision or not isinstance(tree, str)
                    or not re.fullmatch('[0-9a-f]{40}', tree)):
                raise ValueError('acceptance qualification tree differs from its source object')
            intent.update(qualification_commit=selected_revision,
                          qualification_tree=tree, qualification_ref=reference)
        if config.get('delivery_url'):
            if selected_revision is None:
                raise ValueError('encrypted acceptance delivery requires a frozen qualification worker')
            delivery_url(config['delivery_url'], request, 'response.json')
            intent.update(release_id=manifest['release_id'], delivery_protocol=PROTOCOL,
                          delivery_url=config['delivery_url'])
            intent['delivery_archives'] = delivery.prepare(state, intent, gh)
        atomic_json(marker, intent)
    if intent['sources'] != manifest['sources'] or intent['target'] != target or intent['request'] != request:
        raise ValueError('native acceptance intent changed while its worker was active')
    if intent.get('rejected_before_dispatch'):
        cleanup(marker, intent, grant, state)
        raise ValueError('native acceptance invitation exceeded the provider secret bound; grant revoked')
    runs = []
    for page in range(1, 11):
        values = gh(f'actions/workflows/{workflow}/runs?event=workflow_dispatch&per_page=100&page={page}')['workflow_runs']
        runs += [run for run in values if run.get('display_title') == PREFIX + request]
        if runs or len(values) < 100: break
    if len(runs) > 1: raise ValueError('native acceptance request has duplicate provider runs')
    if not runs:
        if intent.get('dispatch_reserved'):
            if time.time() - intent['created_at'] > 1800:
                cleanup(marker, intent, grant, state)
                raise ValueError('native acceptance dispatch is still unknown; do not resubmit blindly')
            return None
        reference = manifest['refs']['gchat'].removeprefix('refs/heads/')
        if 'qualification_commit' in intent:
            reference = intent['qualification_ref']
            if qualification_ref(intent['qualification_commit']) != reference:
                raise ValueError('acceptance qualification reference changed before dispatch')
        inputs = {'request_id': request, 'target': target, 'gchat_commit': manifest['sources']['gchat']['commit'],
                  'release_manifest': base64.b64encode(canonical(manifest)).decode(),
                  'artifacts': base64.b64encode(canonical(intent['inputs'])).decode()}
        if intent.get('delivery_protocol'):
            inputs['delivery_url'] = intent['delivery_url']
        else:
            issued = json.loads(ssh(grant, 'canary grant ' + intent['operation'], b''))
            value = issued['invitation'].encode()
            if len(value) > 48000:
                intent['rejected_before_dispatch'] = True; atomic_json(marker, intent)
                cleanup(marker, intent, grant, state)
                raise ValueError('bootstrap-only native invitation exceeds the private provider secret bound; grant revoked')
            subprocess.run(['gh', 'secret', 'set', intent['secret'], '--repo', 'IggyGG/gchat'],
                           input=value, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, timeout=60)
            inputs['invitation_secret'] = intent['secret']
        if 'qualification_commit' in intent:
            inputs['qualification_commit'] = intent['qualification_commit']
        intent['dispatch_reserved'] = True; atomic_json(marker, intent)
        gh(f'actions/workflows/{workflow}/dispatches', method='POST', body={'ref': reference, 'inputs': inputs})
        return None
    run = runs[0]
    expected_worker = intent.get('qualification_commit', manifest['sources']['gchat']['commit'])
    if (run.get('head_sha') != expected_worker or run.get('event') != 'workflow_dispatch'
            or run.get('path') != '.github/workflows/' + workflow
            or run.get('head_repository', {}).get('full_name') != 'IggyGG/gchat'):
        raise ValueError('native acceptance workflow/source differs')
    if run['status'] != 'completed':
        if intent.get('delivery_protocol'):
            if intent.get('cleaned') is True:
                raise ValueError('closed acceptance request cannot issue new authority')
            delivery.ready(state, intent, work, run, gh,
                           lambda: json.loads(ssh(grant, 'canary grant ' + intent['operation'], b'')))
        return None
    cleanup(marker, intent, grant, state)
    atomic_json(work / 'acceptance-run.json', run)
    artifacts = gh(f'actions/runs/{run["id"]}/artifacts?per_page=100')['artifacts']
    selected = [item for item in artifacts if item['name'] == 'acceptance-' + request and not item['expired']]
    if len(selected) != 1: raise ValueError('native acceptance report is missing or ambiguous')
    artifact = selected[0]; archive = work / 'acceptance.zip'
    if not re.fullmatch('sha256:[0-9a-f]{64}', artifact.get('digest', '')) or type(artifact.get('size_in_bytes')) is not int or not 0 < artifact['size_in_bytes'] <= 256 * 1024**2:
        raise ValueError('native acceptance archive identity or size is invalid')
    if not archive.exists():
        partial = work / 'acceptance.partial'
        with partial.open('wb') as stream:
            subprocess.run(['gh', 'api', f'repos/IggyGG/gchat/actions/artifacts/{artifact["id"]}/zip'],
                           stdout=stream, stderr=subprocess.PIPE, check=True, timeout=300)
        if 'sha256:' + digest(partial) != artifact['digest']: raise ValueError('native acceptance archive changed in transit')
        os.replace(partial, archive)
    if 'sha256:' + digest(archive) != artifact['digest']: raise ValueError('retained native acceptance archive changed')
    destination = work / 'acceptance'
    if not (work / 'acceptance-extracted.json').exists():
        if destination.exists():
            import shutil
            shutil.rmtree(destination)  # derived report extraction only
        extract(archive, destination); atomic_json(work / 'acceptance-extracted.json', {'sha256': digest(archive)})
    if run['conclusion'] != 'success':
        atomic_json(work / 'acceptance-failed.json', {
            'request': request, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
            'target': target, 'qualification_commit': expected_worker, 'passed': False,
            'run_sha256': digest(work / 'acceptance-run.json'), 'archive_sha256': digest(archive),
            'intent_sha256': digest(marker)})
        raise ValueError('native acceptance failed; original reports retained')
    if 'qualification_commit' in intent:
        verify_worker(json.loads((destination / 'worker.json').read_text()), intent, manifest, target)
    if intent.get('delivery_protocol'):
        delivery.verify_receipt(json.loads((destination / 'delivery.json').read_text()), intent, work)
    report = json.loads((destination / 'report.json').read_text())
    rollback = json.loads((destination / 'rollback/report.json').read_text())
    network = json.loads((destination / 'network/report.json').read_text())
    qualify_native(report, rollback, network, manifest, target, intent['inputs'], int(time.time()))
    relays = []
    for relay in [item for item in inventory(json.loads(Path(config['deployment_file']).read_text())) if item.get('binary_name') == 'gcnode']:
        proof = invoke(relay, 'observe', manifest, work / 'relays' / relay['id'])
        if proof is None: return None
        if not (proof['healthy'] and proof['matches']): raise ValueError('compatible native relay is not running')
        relays.append({'id': relay['id'], 'healthy': True, 'gcoms_commit': manifest['sources']['gcoms']['commit'],
                       'carrier_profile': manifest['policy']['carrier_profile']})
    check = network['file_check']; elapsed = network['elapsed_seconds']
    proof = {'schema': 1, 'passed': True, 'sources': manifest['sources'], 'release_id': manifest['release_id'],
             'platform': target, 'completed_at': int(time.time()), 'carrier_profile': manifest['policy']['carrier_profile'],
             'checks': {name: True for name in ('authentication', 'durable_delivery', 'files', 'reopen_recovery', 'upgrade_rollback', 'relay_compatibility')},
             'rollback_state_compatible': True, 'relays': relays,
             'file_check': {'mode': 'file-recovery', 'bytes': check['bytes'], 'completion_elapsed_seconds': check['completion_elapsed_seconds'],
                'total_elapsed_seconds': elapsed, 'source_sha256': check['sha256'], 'export_sha256': check['sha256'],
                'abrupt_stop': True, 'verified_pieces_retained': True, 'same_identity': True, 'authenticated_chat_ack': True,
                'hash_verified_after_reopen': True, 'cleanup_complete': True}}
    verify_compatibility(proof, manifest, int(time.time()), target)
    receipts = state / 'acceptance' / target; retained = receipts / manifest['release_id']; retained.mkdir(parents=True, exist_ok=True)
    import shutil
    saved = retained / 'native.zip'; shutil.copyfile(archive, saved)
    proof['evidence'] = [{'path': saved.relative_to(receipts).as_posix(), 'sha256': digest(saved)}]
    atomic_json(receipts / (manifest['release_id'] + '.json'), proof)
    return {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'], 'platform': target,
            'stage': 'acceptance', 'passed': True, 'source_unchanged': True, 'completed_at': proof['completed_at'],
            'qualification_commit': expected_worker, 'external_id': str(run['id']),
            'evidence': [{'path': 'acceptance.zip', 'sha256': digest(archive)}]}


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True); args = parser.parse_args(); os.umask(0o077)
    output = Path(os.environ['GCHAT_RELEASE_RECEIPT'])
    result = collect(args.state, json.loads(args.config.read_text()), validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text())),
        os.environ['GCHAT_RELEASE_TARGET'], output.parent, os.environ['GCHAT_RELEASE_REQUEST_ID'])
    if result is None: raise SystemExit(75)
    atomic_json(output, result)


if __name__ == '__main__': main()
