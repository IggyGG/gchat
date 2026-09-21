#!/usr/bin/env python3
"""Forgejo dispatches Mac builds, retrieves one exact run, and verifies source hashes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import time
import uuid

from release_evidence import file_reference, validate_sources, validate_report
from paired_sources import verify_native_ci_inputs, verify_retained_inputs

REPO='IggyGG/gchat'
GCOMS_REPO='IggyGG/gcoms'


def gh(*args):
    return subprocess.check_output(['gh',*args],text=True).strip()


def release_ref(value):
    """Only explicitly selected release branches/tags can receive signing access."""
    if value == 'main':
        value = 'refs/heads/main'
    elif value.startswith('release/'):
        value = 'refs/heads/' + value
    elif re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?', value):
        value = 'refs/tags/' + value
    allowed = (value == 'refs/heads/main' or
               re.fullmatch(r'refs/heads/release/gchat-[A-Za-z0-9][A-Za-z0-9._-]*', value) or
               re.fullmatch(r'refs/tags/v[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?', value))
    if not allowed or '..' in value or value.endswith(('.', '.lock')):
        raise ValueError('select main, a release/gchat-* branch, or an approved version tag')
    return value


def source_commit(value):
    if not re.fullmatch('[0-9a-f]{40}', value):
        raise ValueError('full source commit IDs required')
    return value


def remote_ref_commit(repository, ref):
    obj = json.loads(gh('api', f'repos/{repository}/git/ref/{ref.removeprefix("refs/")}'))['object']
    for _ in range(8):
        if obj['type'] == 'commit':
            return source_commit(obj['sha'])
        if obj['type'] != 'tag':
            break
        obj = json.loads(gh('api', f'repos/{repository}/git/tags/{source_commit(obj["sha"])}'))['object']
    raise ValueError('release ref must resolve to a commit')


def verify_remote_sources(gchat_commit, gcoms_commit, gchat_ref, gcoms_ref):
    if remote_ref_commit(REPO, gchat_ref) != gchat_commit:
        raise ValueError('selected GChat ref must equal the frozen workflow/source commit')
    paired_tip = remote_ref_commit(GCOMS_REPO, gcoms_ref)
    if paired_tip != gcoms_commit:
        if gcoms_ref.startswith('refs/tags/'):
            raise ValueError('selected GComs tag must equal the frozen source commit')
        comparison = json.loads(gh('api', f'repos/{GCOMS_REPO}/compare/{gcoms_commit}...{paired_tip}'))
        if comparison['status'] != 'ahead':
            raise ValueError('frozen GComs source must belong to the selected release branch')


def verify_checkouts(gchat, gcoms, gchat_commit, gcoms_commit, gchat_ref, gcoms_ref, environment):
    """Repeat ref checks on the signing worker; dispatcher checks are not authority."""
    if (environment.get('GITHUB_SHA') != gchat_commit or
        environment.get('GITHUB_WORKFLOW_SHA') != gchat_commit or
        environment.get('GITHUB_REF') != gchat_ref or
        environment.get('GITHUB_WORKFLOW_REF') != f'{REPO}/.github/workflows/macos-release.yml@{gchat_ref}'):
        raise ValueError('workflow must run from the selected frozen GChat ref and commit')
    for root, commit, ref in ((gchat, gchat_commit, gchat_ref), (gcoms, gcoms_commit, gcoms_ref)):
        source_commit(commit)
        actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        if actual != commit:
            raise ValueError('checkout differs from source input')
        local_ref = (ref.replace('refs/heads/', 'refs/remotes/origin/', 1)
                     if ref.startswith('refs/heads/') else ref)
        tip = subprocess.check_output(['git', 'rev-parse', '--verify', local_ref + '^{commit}'],
                                      cwd=root, text=True).strip()
        if root == gchat or ref.startswith('refs/tags/'):
            if tip != commit:
                raise ValueError('selected release ref moved from the frozen source commit')
        else:
            subprocess.run(['git', 'merge-base', '--is-ancestor', commit, tip], cwd=root, check=True)


def selected_targets(target):
    if target == 'both':
        return {'macos-x86_64', 'macos-aarch64'}
    if target in ('macos-x86_64', 'macos-aarch64'):
        return {target}
    raise ValueError('select both, macos-x86_64 or macos-aarch64')


def verify_collected_targets(actual, target):
    if actual != selected_targets(target):
        raise ValueError('collected native Mac targets differ from the requested architectures')


def dispatch(gchat_commit, gcoms_commit, gchat_ref, gcoms_ref, request_id, target='both'):
    selected_targets(target)
    verify_remote_sources(gchat_commit, gcoms_commit, gchat_ref, gcoms_ref)
    dispatch_ref = gchat_ref.removeprefix('refs/heads/').removeprefix('refs/tags/')
    gh('workflow', 'run', 'macos-release.yml', '--repo', REPO, '--ref', dispatch_ref,
       '-f', 'gchat_commit=' + gchat_commit, '-f', 'gcoms_commit=' + gcoms_commit,
       '-f', 'gchat_ref=' + gchat_ref, '-f', 'gcoms_ref=' + gcoms_ref,
       '-f', 'request_id=' + request_id, '-f', 'target=' + target)


def verify_run(run, gchat_commit):
    if run['head_sha'] != gchat_commit or run['event'] != 'workflow_dispatch':
        raise ValueError('workflow ran from a different commit or event')



def verify_reference(path, reference):
    """Bind a retained local artifact without following the worker's absolute path."""
    if not isinstance(reference, dict) or not path.is_file():
        raise ValueError('missing Mac application evidence')
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if (reference.get('sha256') != actual or
        type(reference.get('size')) is not int or reference['size'] != path.stat().st_size):
        raise ValueError('Mac application evidence digest/size mismatch')


def verify_archived_file(archive, name, reference):
    with tarfile.open(archive) as source:
        member = source.getmember(name)
        if not member.isfile():
            raise ValueError('Mac harness/publication input is not a source file')
        data = source.extractfile(member).read()
    if (not isinstance(reference, dict) or reference.get('size') != len(data) or
        reference.get('sha256') != hashlib.sha256(data).hexdigest()):
        raise ValueError('Mac harness/publication differs from frozen source archive')
    return data


def verify_application_smoke(directory, build, source_archive):
    smoke = directory / 'application-smoke'
    report = json.loads((smoke / 'report.json').read_text())
    if (report.get('schema') != 1 or
        report.get('scope') != 'macos_dmg_private_copy_install_service_lifecycle' or
        report.get('passed') is not True or report.get('inputs_unchanged') is not True or
        report.get('target') != build['target'] or
        report.get('sources') != build['dependency_inputs']['sources']):
        raise ValueError('Mac copied-application scope, result or source binding mismatch')
    cleanup = report.get('cleanup', {})
    if any(cleanup.get(name) is not True for name in
           ('passed', 'detached', 'installation_removed', 'service_children_stopped')):
        raise ValueError('Mac copied-application cleanup is incomplete')
    if any(report.get(name) is not False for name in
           ('gui_tested', 'gatekeeper_tested', 'notarization_tested',
            'system_applications_modified', 'production_network_requested')):
        raise ValueError('Mac copied-application receipt exceeds its qualified scope')
    artifact = build['files'][0]
    inputs = report['inputs']
    for key, path in (('dmg', directory / artifact['name']), ('build_manifest', directory / 'build.json'),
                      ('native_receipt', directory / 'provenance/native-ci.json')):
        verify_reference(path, inputs.get(key))
    verify_archived_file(source_archive, 'scripts/test-macos-bundle.py', report.get('harness'))
    publication = json.loads(verify_archived_file(source_archive, 'release/publication.json',
                                                 inputs.get('publication')))
    publisher = publication['publisher_identities']['macos']
    if build['publisher'] != publisher:
        raise ValueError('Mac application publisher differs from frozen source')
    expected_pin = publisher['certificate_fingerprint'].replace(' ', '').upper()
    for kind in ('dmg', 'application'):
        signature = report[kind + '_signature']
        certificate = smoke / (kind + '-leaf-0')
        verify_reference(certificate, signature.get('certificate'))
        data = certificate.read_bytes()
        actual_pin = hashlib.new('sha256' if len(expected_pin) == 64 else 'sha1', data).hexdigest().upper()
        sha256 = hashlib.sha256(data).hexdigest()
        if (actual_pin != expected_pin or signature.get('fingerprint') != expected_pin or
            signature.get('sha256') != sha256 or
            (publisher.get('certificate_sha256') and publisher['certificate_sha256'].lower() != sha256)):
            raise ValueError('Mac application/DMG signature certificate differs from publisher pin')
    service_path = smoke / 'service/report.json'
    verify_reference(service_path, report.get('service_receipt'))
    service = json.loads(service_path.read_text())
    if (service.get('schema') != 1 or service.get('scope') != 'packaged_executable_offline_service_lifecycle' or
        any(service.get(name) is not True for name in
            ('passed', 'inputs_unchanged', 'children_stopped', 'temporary_profile_removed'))):
        raise ValueError('Mac packaged service lifecycle failed or cleanup is incomplete')
    verify_archived_file(source_archive, 'scripts/test-native-application.py', service.get('harness'))
    application_inputs = report['application_inputs']
    if (service.get('inputs') != application_inputs or
        application_inputs.get('sources') != build['dependency_inputs']['sources'] or
        application_inputs.get('target') != build['target'] or
        application_inputs.get('native_ci') != build['native_ci'] or
        application_inputs.get('build_manifest') != inputs['build_manifest'] or
        application_inputs.get('native_receipt') != inputs['native_receipt'] or
        application_inputs.get('binary') != report['application']['executable']):
        raise ValueError('Mac service tested different application/native inputs')
    binary = application_inputs['binary']
    matches = [entry for entry in build.get('executables', []) if entry.get('name') == Path(binary['path']).name]
    if (len(matches) != 1 or matches[0].get('sha256') != binary.get('sha256') or
        matches[0].get('size') != binary.get('size')):
        raise ValueError('Mac installed executable differs from signed build manifest')
    steps = service.get('steps', [])
    identity = service.get('protocol_identity_sha256')
    if (len(steps) != 2 or [step.get('phase') for step in steps] != ['create', 'reopen'] or
        not isinstance(identity, str) or not re.fullmatch('[0-9a-f]{64}', identity)):
        raise ValueError('Mac service receipt omits fresh/reopen identity evidence')
    for step in steps:
        stopped = step.get('cleanup', {})
        if (step.get('passed') is not True or step.get('disconnected') is not True or
            step.get('protocol_identity_sha256') != identity or
            stopped.get('stopped') is not True or stopped.get('forced') is not False or
            stopped.get('exit_code') != 0):
            raise ValueError('Mac service did not retain identity and shut down cleanly')
        verify_reference(smoke / 'service' / (step['phase'] + '.log'), step.get('log'))
    if steps[1].get('wrong_passphrase_rejected') is not True:
        raise ValueError('Mac service receipt omits rejected-unlock protection')
    gui_path = smoke / 'gui/report.json'
    if report.get('gui_startup_passed') is not True:
        raise ValueError('Mac native graphical startup did not pass')
    verify_reference(gui_path, report.get('gui_startup'))
    gui = json.loads(gui_path.read_text())
    if (gui.get('scope') != 'native_window_and_ui_autostarted_ipc' or gui.get('passed') is not True or
        gui.get('rendered_interaction_tested') is not False or gui.get('network_journey_tested') is not False or
        gui.get('profile_locked') is not True or gui.get('protocol_locked') is not True or
        gui.get('network_state') != 'locked'):
        raise ValueError('Mac native graphical startup scope/state mismatch')
    command = gui.get('command', [])
    if (len(command) != 4 or command[0] != binary['path'] or command[1] != '--home' or
        command[2] != gui.get('temporary_profile') or command[3] != '--no-network-bootstrap'):
        raise ValueError('Mac graphical startup did not exercise the copied application default')
    daemon_command = gui.get('service', {}).get('command', '')
    if (gui.get('protocol_selection_observed') is not True or
        gui.get('carrier_selection') != 'official_application_default' or
        not isinstance(daemon_command, str) or
        not daemon_command.startswith(binary['path'] + ' --interactive ') or
        not re.search(r'(?:^|\s)--gc2-carrier(?:\s|$)', daemon_command)):
        raise ValueError('Mac GUI did not observe its default GC/2 daemon selection')
    windows = gui.get('windows', [])
    pid = gui.get('pid')
    if (type(pid) is not int or pid <= 0 or not windows or
        any(window.get('owner_pid') != pid or window.get('width', 0) <= 0 or
            window.get('height', 0) <= 0 for window in windows)):
        raise ValueError('Mac graphical startup has no owned native window')
    stopped = gui.get('cleanup', {})
    services = stopped.get('services', [])
    if (any(stopped.get(name) is not True for name in
            ('passed', 'children_stopped', 'endpoints_removed', 'temporary_profile_removed')) or
        stopped.get('forced') is not False or
        stopped.get('gui', {}).get('pid') != pid or
        stopped.get('gui', {}).get('stopped') is not True or
        stopped.get('gui', {}).get('forced') is not False or
        len(services) != 1 or services[0].get('pid') != gui.get('service', {}).get('pid') or
        services[0].get('stopped') is not True or services[0].get('forced') is not False):
        raise ValueError('Mac native graphical startup cleanup is incomplete')
    verify_reference(smoke / 'gui/gui.log', gui.get('log'))
    if gui.get('service_log'):
        verify_reference(smoke / 'gui/service.log', gui['service_log'])
    commands = report.get('commands', [])
    expected_commands = {'dmg-integrity', 'dmg-certificate', 'attach', 'copy',
                         'application-integrity', 'application-certificate', 'service', 'detach'}
    if len(commands) != len(expected_commands) or {command.get('name') for command in commands} != expected_commands:
        raise ValueError('Mac installation receipt omits required copy/signature/cleanup commands')
    for command in commands:
        name = command.get('name', '')
        if not re.fullmatch('[a-z][a-z-]*', name) or command.get('exit_code') != 0:
            raise ValueError('Mac installation command did not complete successfully')
        for stream in ('stdout', 'stderr'):
            verify_reference(smoke / (name + '.' + stream), command.get(stream))
    return report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gchat-commit', required=True, type=source_commit)
    p.add_argument('--gcoms-commit', required=True, type=source_commit)
    p.add_argument('--gchat-ref', default='main', type=release_ref)
    p.add_argument('--gcoms-ref', default='main', type=release_ref)
    p.add_argument('--output', type=Path)
    p.add_argument('--target', choices=('both', 'macos-x86_64', 'macos-aarch64'), default='both')
    p.add_argument('--verify-checkouts', action='store_true')
    p.add_argument('--gchat', type=Path)
    p.add_argument('--gcoms', type=Path)
    a = p.parse_args()
    if a.verify_checkouts:
        if not a.gchat or not a.gcoms:
            p.error('--verify-checkouts requires --gchat and --gcoms')
        verify_checkouts(a.gchat, a.gcoms, a.gchat_commit, a.gcoms_commit,
                         a.gchat_ref, a.gcoms_ref, os.environ)
        print('Verified frozen workflow, selected release refs and both source checkouts')
        return
    if not a.output:
        p.error('--output is required when dispatching')
    request_id = uuid.uuid4().hex
    dispatch(a.gchat_commit, a.gcoms_commit, a.gchat_ref, a.gcoms_ref, request_id, a.target)
    deadline=time.monotonic()+21600;run=None
    while time.monotonic()<deadline:
        if run is None:
            runs=json.loads(gh('api',f'repos/{REPO}/actions/workflows/macos-release.yml/runs?event=workflow_dispatch&per_page=100'))['workflow_runs']
            run=next((r for r in runs if r['display_title']=='Forgejo macOS '+request_id),None)
        else:
            run=json.loads(gh('api',f'repos/{REPO}/actions/runs/{run["id"]}'))
            verify_run(run, a.gchat_commit)
            if run['status']=='completed': break
        time.sleep(15)
    if not run or run['status']!='completed' or run['conclusion']!='success': raise RuntimeError('macOS build failed or timed out; retain the GitHub run for diagnosis')
    verify_run(run, a.gchat_commit)
    output=a.output.resolve();output.mkdir(parents=True,exist_ok=False)
    gh('run','download',str(run['id']),'--repo',REPO,'--dir',str(output))
    expected={'gchat':a.gchat_commit,'gcoms':a.gcoms_commit};targets=set()
    for report in output.glob('macos-*/build.json'):
        data=json.loads(report.read_text())
        if data['sources']!=expected or data['target'] in targets: raise ValueError('Mac artifact source binding mismatch')
        inputs=data.get('dependency_inputs', {})
        if (inputs.get('kind') != 'frozen_source_pair' or
            inputs.get('rust_sources_verified') is not True or
            inputs.get('npm_sources_verified') is not True or
            {name:value.get('commit') for name,value in inputs.get('sources',{}).items()} != expected):
            raise ValueError('Mac dependency inputs do not bind the frozen source pair')
        if json.loads((report.parent/'provenance/inputs.json').read_text()) != inputs:
            raise ValueError('Mac retained dependency provenance mismatch')
        native_ci = verify_native_ci_inputs(report.parent/'provenance/native-ci.json', inputs)
        verify_retained_inputs(report.parent/'provenance', inputs)
        if data.get('native_ci') != native_ci:
            raise ValueError('Mac build does not bind qualified dependency inputs')
        targets.add(data['target'])
        evidence = report.parent / 'evidence'
        if verify_native_ci_inputs(evidence/'paired-gchat/native-ci.json', inputs) != native_ci:
            raise ValueError('Mac build and qualification receipts differ')
        ci_inputs = json.loads((evidence/'paired-gchat/inputs.json').read_text())
        verify_retained_inputs(evidence/'paired-gchat', ci_inputs)
        candidate = json.loads((evidence / 'candidate.json').read_text())
        validate_sources(candidate, evidence)
        if {name:value['commit'] for name,value in candidate['sources'].items()} != expected:
            raise ValueError('native evidence source binding mismatch')
        for project in ('gchat', 'gcoms'):
            check = f'native.{project}.{data["target"]}'
            result = json.loads(file_reference(evidence, candidate['checks'][check]).read_text())
            validate_report(check, result, candidate, evidence, candidate['artifacts'])
        if len(data['files']) != 1 or data['files'][0]['format'] != 'dmg':
            raise ValueError('expected exactly one qualified DMG per Mac architecture')
        for item in data['files']:
            path=report.parent/item['name']
            if path.name!=item['name'] or not path.resolve().is_relative_to(report.parent.resolve()): raise ValueError('unsafe artifact name')
            with path.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
            if digest!=item['sha256'] or item['signing_verified'] is not True: raise ValueError('Mac artifact digest/signing mismatch')
        verify_application_smoke(report.parent, data, file_reference(evidence, candidate['sources']['gchat']['archive']))
    verify_collected_targets(targets, a.target)
    (output/'github-run.json').write_text(json.dumps({'run_id':run['id'],'url':run['html_url'],'workflow_commit':run['head_sha'],'refs':{'gchat':a.gchat_ref,'gcoms':a.gcoms_ref},'sources':expected,'targets':sorted(targets)},indent=2)+'\n')
    print('Retrieved verified source-bound macOS artifacts: '+str(output))


if __name__=='__main__': main()
