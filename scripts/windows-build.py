#!/usr/bin/env python3
"""Dispatch and collect exact-source Windows Server 2022 MSVC/NSIS qualification.

Server evidence does not qualify Windows 11 GUI or real-network operation.
The isolated worker uses the existing pinned signing identity, never a new one.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path, PureWindowsPath
import platform
import re
import subprocess
import sys
import time
import urllib.request
import uuid

from paired_sources import verify_native_ci_inputs, verify_retained_inputs
from release_evidence import digest, file_reference, validate_report, validate_sources

# Reuse reviewed platform-independent source/artifact guards without changing the
# frozen Mac workflow. Windows workflow identity and installer scope are separate.
SPEC = importlib.util.spec_from_file_location('desktop_release_sources', Path(__file__).with_name('macos-build.py'))
source = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(source)
REPO = source.REPO
WORKFLOW = 'windows-release.yml'
WEBVIEW_ID = '{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True).strip()


def verify_checkouts(gchat, gcoms, gchat_commit, gcoms_commit, gchat_ref, gcoms_ref, environment):
    if (environment.get('GITHUB_SHA') != gchat_commit or
        environment.get('GITHUB_WORKFLOW_SHA') != gchat_commit or
        environment.get('GITHUB_REF') != gchat_ref or
        environment.get('GITHUB_WORKFLOW_REF') != f'{REPO}/.github/workflows/{WORKFLOW}@{gchat_ref}'):
        raise ValueError('workflow must run from the selected frozen GChat ref and commit')
    for root, commit, ref in ((gchat, gchat_commit, gchat_ref), (gcoms, gcoms_commit, gcoms_ref)):
        source.source_commit(commit)
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


def dispatch(gchat_commit, gcoms_commit, gchat_ref, gcoms_ref, request_id):
    source.verify_remote_sources(gchat_commit, gcoms_commit, gchat_ref, gcoms_ref)
    ref = gchat_ref.removeprefix('refs/heads/').removeprefix('refs/tags/')
    gh('workflow', 'run', WORKFLOW, '--repo', REPO, '--ref', ref,
       '-f', 'gchat_commit=' + gchat_commit, '-f', 'gcoms_commit=' + gcoms_commit,
       '-f', 'gchat_ref=' + gchat_ref, '-f', 'gcoms_ref=' + gcoms_ref,
       '-f', 'request_id=' + request_id)


def webview_version():
    import winreg
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
            try:
                with winreg.OpenKey(hive, r'SOFTWARE\Microsoft\EdgeUpdate\Clients' + '\\' + WEBVIEW_ID,
                                    access=winreg.KEY_READ | view) as key:
                    version = winreg.QueryValueEx(key, 'pv')[0]
                    if isinstance(version, str) and re.fullmatch(r'[1-9][0-9]*(?:\.[0-9]+){3}', version):
                        return version
            except OSError:
                continue
    return None


def prepare_webview(output):
    if (os.name != 'nt' or os.environ.get('GITHUB_ACTIONS') != 'true' or
        platform.machine().lower() not in ('amd64', 'x86_64') or sys.getwindowsversion().build != 20348):
        raise ValueError('prerequisite installation is limited to isolated Windows Server 2022 x64 workers')
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {'schema': 1, 'scope': 'windows_server_2022_x64_prerequisites', 'passed': False,
              'os_build': sys.getwindowsversion().build, 'platform': platform.platform(),
              'target': 'windows-x86_64', 'windows_11_qualified': False}
    try:
        rust = subprocess.check_output(['rustc', '-vV'], text=True)
        if 'host: x86_64-pc-windows-msvc' not in rust:
            raise ValueError('Windows release worker requires native x64 MSVC')
        report['rustc'] = rust.strip()
        report['python'] = platform.python_version()
        report['node'] = subprocess.check_output(['node', '--version'], text=True).strip()
        report['npm'] = subprocess.check_output(['npm.cmd', '--version'], text=True).strip()
        version = webview_version()
        report['webview_preinstalled'] = version is not None
        if version is None:
            bootstrapper = output / 'MicrosoftEdgeWebview2Setup.exe'
            url = 'https://go.microsoft.com/fwlink/p/?LinkId=2124703'
            with urllib.request.urlopen(url, timeout=120) as response:
                if not response.geturl().startswith('https://'):
                    raise ValueError('WebView bootstrapper redirect must retain HTTPS')
                data = response.read(20 * 1024 * 1024 + 1)
                if len(data) > 20 * 1024 * 1024:
                    raise ValueError('WebView bootstrapper exceeds its download bound')
                bootstrapper.write_bytes(data)
            environment = {**os.environ, 'GCHAT_WEBVIEW_BOOTSTRAPPER': str(bootstrapper)}
            script = "$s=Get-AuthenticodeSignature -LiteralPath $env:GCHAT_WEBVIEW_BOOTSTRAPPER; if ($s.Status -ne 'Valid' -or $s.SignerCertificate.Subject -notmatch '(^|, )CN=Microsoft Corporation(,|$)') { throw 'WebView bootstrapper is not a trusted Microsoft signature' }; $s.SignerCertificate.Thumbprint"
            pin = subprocess.check_output(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                                          env=environment, text=True).strip()
            report['webview_bootstrapper'] = {'sha256': digest(bootstrapper), 'size': bootstrapper.stat().st_size,
                                            'certificate_fingerprint': pin, 'url': url}
            subprocess.run([str(bootstrapper), '/silent', '/install'], check=True, timeout=300)
            version = webview_version()
        if version is None:
            raise ValueError('Evergreen WebView2 prerequisite did not register a usable version')
        report['webview_version'] = version
        report['passed'] = True
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
        raise
    finally:
        (output / 'prerequisites.json').write_text(json.dumps(report, indent=2) + '\n')


def verify_signing_cleanup(directory, publisher, source_archive):
    evidence = directory / 'signing-evidence'
    imported = json.loads((evidence / 'import.json').read_text(encoding='utf-8-sig'))
    cleanup = json.loads((evidence / 'cleanup.json').read_text(encoding='utf-8-sig'))
    for receipt in (imported, cleanup):
        source.verify_archived_file(source_archive, 'scripts/windows-signing.ps1', receipt.get('harness'))
    publication = json.loads(source.verify_archived_file(source_archive, 'release/publication.json',
                                                        imported.get('publication')))
    if publication['publisher_identities']['windows'] != publisher:
        raise ValueError('Windows signer differs from frozen publication identity')
    pin = publisher['certificate_fingerprint'].replace(' ', '').upper()
    if (imported.get('scope') != 'isolated_current_user_signer_import' or imported.get('passed') is not True or
        imported.get('store') != 'CurrentUser/My' or imported.get('certificate_fingerprint') != pin or
        imported.get('persistent_trust_stores_unchanged') is not True or
        imported.get('certificate_sha256') != publisher['certificate_sha256'].lower()):
        raise ValueError('Windows signer import did not use the pinned identity without trust changes')
    if (cleanup.get('scope') != 'isolated_current_user_signer_cleanup' or cleanup.get('certificate_fingerprint') != pin or
        any(cleanup.get(name) is not True for name in ('passed', 'imported', 'private_key_removed', 'pfx_removed',
                                                       'my_store_restored', 'persistent_trust_stores_unchanged'))):
        raise ValueError('Windows signing key/trust cleanup did not pass')


def verify_installer_smoke(directory, build, source_archive):
    smoke = directory / 'application-smoke'
    report = json.loads((smoke / 'report.json').read_text())
    if (report.get('schema') != 1 or
        report.get('scope') != 'windows_server_2022_current_user_nsis_service_lifecycle' or
        report.get('passed') is not True or report.get('inputs_unchanged') is not True or
        report.get('target') != build['target'] or
        report.get('sources') != build['dependency_inputs']['sources'] or
        report.get('persistent_certificate_stores_unchanged') is not True):
        raise ValueError('Windows installed application scope, result or source binding mismatch')
    if any(report.get(name) is not False for name in
           ('gui_tested', 'windows_11_qualified', 'production_network_requested')):
        raise ValueError('Windows installer receipt exceeds its qualified scope')
    host = report.get('host', {})
    if (host.get('system') != 'Windows' or host.get('architecture') != 'x86_64' or
        str(host.get('CurrentBuildNumber')) != '20348' or
        not str(host.get('InstallationType', '')).startswith('Server') or not report.get('webview_runtime')):
        raise ValueError('Windows installer receipt omits native Server 2022/WebView evidence')
    cleanup = report.get('cleanup', {})
    if any(cleanup.get(name) is not True for name in
           ('passed', 'uninstalled', 'registration_removed', 'installation_removed', 'children_stopped')):
        raise ValueError('Windows installed application cleanup is incomplete')
    inputs = report['inputs']
    for key, path in (('installer', directory / build['files'][0]['name']),
                      ('build_manifest', directory / 'build.json'),
                      ('native_receipt', directory / 'provenance/native-ci.json')):
        source.verify_reference(path, inputs.get(key))
    source.verify_archived_file(source_archive, 'scripts/test-windows-installer.py', report.get('harness'))
    source.verify_archived_file(source_archive, 'scripts/verify-windows-signature.ps1', report.get('signature_verifier'))
    publication = json.loads(source.verify_archived_file(source_archive, 'release/publication.json', inputs.get('publication')))
    publisher = publication['publisher_identities']['windows']
    if build['publisher'] != publisher or build['signing_policy'] != publication['signing_policy']:
        raise ValueError('Windows application publisher differs from frozen source')
    pin = publisher['certificate_fingerprint'].replace(' ', '').upper()
    signatures = [(report.get('installer_signature', {}), inputs['installer']),
                  (report.get('application_signature', {}), report['application_inputs']['binary']),
                  (cleanup.get('uninstaller_signature', {}), None)]
    for signature, artifact in signatures:
        if (signature.get('thumbprint') != pin or signature.get('verification') != 'pinned_authenticode' or
            signature.get('public_trust_claimed') != (build['signing_policy'] == 'publicly-trusted') or
            (artifact is not None and signature.get('artifact') != artifact)):
            raise ValueError('Windows installer/application/uninstaller signature binding differs')
    service_path = smoke / 'service/report.json'
    source.verify_reference(service_path, report.get('service_receipt'))
    service = json.loads(service_path.read_text())
    if (service.get('schema') != 1 or service.get('scope') != 'packaged_executable_offline_service_lifecycle' or
        any(service.get(name) is not True for name in
            ('passed', 'inputs_unchanged', 'children_stopped', 'temporary_profile_removed'))):
        raise ValueError('Windows packaged service lifecycle failed or cleanup is incomplete')
    source.verify_archived_file(source_archive, 'scripts/test-native-application.py', service.get('harness'))
    application = report['application_inputs']
    if (service.get('inputs') != application or application.get('sources') != report['sources'] or
        application.get('target') != build['target'] or application.get('native_ci') != build['native_ci'] or
        application.get('build_manifest') != inputs['build_manifest'] or
        application.get('native_receipt') != inputs['native_receipt']):
        raise ValueError('Windows service tested different installed/native inputs')
    binary = application['binary']
    executable = build.get('executables', [])
    if (len(executable) != 1 or executable[0].get('name') != PureWindowsPath(binary['path']).name or
        executable[0].get('name') != 'gchat-desktop.exe' or
        any(executable[0].get(name) != binary.get(name) for name in ('size', 'sha256'))):
        raise ValueError('Windows installed executable differs from signed build manifest')
    installation = PureWindowsPath(report['installation_directory'])
    registration = report.get('registration', {})
    if (not installation.is_absolute() or PureWindowsPath(binary['path']).parent != installation or
        registration.get('root') != 'HKCU' or
        PureWindowsPath(registration.get('location', '')) != installation or
        PureWindowsPath(registration.get('uninstall', '')) != installation / 'uninstall.exe' or
        PureWindowsPath(signatures[2][0].get('artifact', {}).get('path', '')) != installation / 'uninstall.exe'):
        raise ValueError('Windows application registration/uninstaller escaped the owned installation')
    identity, steps = service.get('protocol_identity_sha256'), service.get('steps', [])
    if (not isinstance(identity, str) or not re.fullmatch('[0-9a-f]{64}', identity) or
        len(steps) != 2 or [step.get('phase') for step in steps] != ['create', 'reopen']):
        raise ValueError('Windows service receipt omits fresh/reopen identity evidence')
    for step in steps:
        stopped = step.get('cleanup', {})
        if (step.get('passed') is not True or step.get('disconnected') is not True or
            step.get('protocol_identity_sha256') != identity or
            stopped.get('stopped') is not True or stopped.get('forced') is not False or stopped.get('exit_code') != 0):
            raise ValueError('Windows service did not retain identity and shut down cleanly')
        source.verify_reference(smoke / 'service' / (step['phase'] + '.log'), step.get('log'))
    if steps[1].get('wrong_passphrase_rejected') is not True:
        raise ValueError('Windows service receipt omits rejected-unlock protection')
    commands = report.get('commands', [])
    required = {'initial-processes', 'trust-before', 'installer-signature', 'install', 'application-signature',
                'service', 'cleanup-processes', 'uninstaller-signature', 'uninstall', 'trust-after'}
    if len(commands) != len(required) or {command.get('name') for command in commands} != required:
        raise ValueError('Windows installer receipt omits required install/signature/cleanup commands')
    for command in commands:
        name = command['name']
        if command.get('exit_code') != 0 or command.get('timed_out'):
            raise ValueError('Windows installation command did not complete successfully')
        for stream in ('stdout', 'stderr'):
            source.verify_reference(smoke / (name + '.' + stream), command.get(stream))
    before = json.loads((smoke / 'trust-before.stdout').read_text(encoding='utf-8-sig'))
    after = json.loads((smoke / 'trust-after.stdout').read_text(encoding='utf-8-sig'))
    expected_stores = {scope + '/' + name for scope in ('CurrentUser', 'LocalMachine')
                       for name in ('Root', 'CA', 'TrustedPublisher', 'My')}
    if before != after or set(before) != expected_stores:
        raise ValueError('Windows persistent certificate store snapshots differ or are incomplete')
    return report


def collect(directory, expected):
    manifest = directory / 'build.json'
    build = json.loads(manifest.read_text())
    if build.get('sources') != expected or build.get('target') != 'windows-x86_64':
        raise ValueError('Windows artifact source/target binding mismatch')
    inputs = build.get('dependency_inputs', {})
    if (inputs.get('kind') != 'frozen_source_pair' or inputs.get('rust_sources_verified') is not True or
        inputs.get('npm_sources_verified') is not True or
        {name: value.get('commit') for name, value in inputs.get('sources', {}).items()} != expected):
        raise ValueError('Windows dependency inputs do not bind the frozen source pair')
    if json.loads((directory / 'provenance/inputs.json').read_text()) != inputs:
        raise ValueError('Windows retained dependency provenance mismatch')
    native = verify_native_ci_inputs(directory / 'provenance/native-ci.json', inputs)
    verify_retained_inputs(directory / 'provenance', inputs)
    if build.get('native_ci') != native:
        raise ValueError('Windows build differs from native-qualified dependency inputs')
    evidence = directory / 'native-evidence'
    if verify_native_ci_inputs(evidence / 'paired-gchat/native-ci.json', inputs) != native:
        raise ValueError('Windows build and native receipts differ')
    verify_retained_inputs(evidence / 'paired-gchat', json.loads((evidence / 'paired-gchat/inputs.json').read_text()))
    candidate = json.loads((evidence / 'candidate.json').read_text())
    validate_sources(candidate, evidence)
    if {name: value['commit'] for name, value in candidate['sources'].items()} != expected:
        raise ValueError('Windows native candidate source binding mismatch')
    for project in ('gchat', 'gcoms'):
        check = f'native.{project}.windows-x86_64'
        result = json.loads(file_reference(evidence, candidate['checks'][check]).read_text())
        validate_report(check, result, candidate, evidence, candidate['artifacts'])
    artifacts = build.get('files', [])
    if len(artifacts) != 1 or artifacts[0].get('format') != 'nsis':
        raise ValueError('Windows worker must retain exactly one NSIS installer')
    item = artifacts[0]
    name = item.get('name', '')
    if (not name or PureWindowsPath(name).name != name or Path(name).name != name or
        not name.lower().endswith('.exe') or item.get('signing_verified') is not True or
        not (directory / name).resolve().is_relative_to(directory.resolve()) or digest(directory / name) != item['sha256']):
        raise ValueError('Windows installer path, digest or signing mismatch')
    archived_source = file_reference(evidence, candidate['sources']['gchat']['archive'])
    verify_installer_smoke(directory, build, archived_source)
    verify_signing_cleanup(directory, build['publisher'], archived_source)
    prereqs = json.loads((directory / 'worker-evidence/prerequisites.json').read_text())
    if (prereqs.get('scope') != 'windows_server_2022_x64_prerequisites' or prereqs.get('passed') is not True or
        prereqs.get('os_build') != 20348 or prereqs.get('target') != 'windows-x86_64' or
        prereqs.get('windows_11_qualified') is not False or not prereqs.get('webview_version')):
        raise ValueError('Windows worker scope/prerequisite evidence is incomplete')
    return build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gchat-commit', type=source.source_commit)
    parser.add_argument('--gcoms-commit', type=source.source_commit)
    parser.add_argument('--gchat-ref', type=source.release_ref, default='main')
    parser.add_argument('--gcoms-ref', type=source.release_ref, default='main')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify-checkouts', action='store_true')
    parser.add_argument('--gchat', type=Path)
    parser.add_argument('--gcoms', type=Path)
    parser.add_argument('--prepare-webview', action='store_true')
    parser.add_argument('--worker-evidence', type=Path)
    args = parser.parse_args()
    if args.prepare_webview:
        if not args.worker_evidence:
            parser.error('--prepare-webview requires --worker-evidence')
        prepare_webview(args.worker_evidence)
        return
    if not args.gchat_commit or not args.gcoms_commit:
        parser.error('both full source commits are required')
    if args.verify_checkouts:
        if not args.gchat or not args.gcoms:
            parser.error('--verify-checkouts requires both checkout paths')
        verify_checkouts(args.gchat, args.gcoms, args.gchat_commit, args.gcoms_commit,
                         args.gchat_ref, args.gcoms_ref, os.environ)
        print('Verified Windows workflow, release refs and frozen paired sources')
        return
    if not args.output:
        parser.error('--output is required for dispatch and collection')
    request_id = uuid.uuid4().hex
    dispatch(args.gchat_commit, args.gcoms_commit, args.gchat_ref, args.gcoms_ref, request_id)
    deadline = time.monotonic() + 21600
    run = None
    while time.monotonic() < deadline:
        if run is None:
            runs = json.loads(gh('api', f'repos/{REPO}/actions/workflows/{WORKFLOW}/runs?event=workflow_dispatch&per_page=100'))['workflow_runs']
            run = next((entry for entry in runs if entry['display_title'] == 'Forgejo Windows ' + request_id), None)
        else:
            run = json.loads(gh('api', f'repos/{REPO}/actions/runs/{run["id"]}'))
            source.verify_run(run, args.gchat_commit)
            if run['status'] == 'completed':
                break
        time.sleep(15)
    if not run or run['status'] != 'completed' or run['conclusion'] != 'success':
        raise RuntimeError('Windows build failed or timed out; keep its native run/evidence for diagnosis')
    source.verify_run(run, args.gchat_commit)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    gh('run', 'download', str(run['id']), '--repo', REPO, '--dir', str(output))
    expected = {'gchat': args.gchat_commit, 'gcoms': args.gcoms_commit}
    collect(output / 'windows-x86_64', expected)
    (output / 'github-run.json').write_text(json.dumps({
        'run_id': run['id'], 'url': run['html_url'], 'workflow_commit': run['head_sha'],
        'sources': expected, 'refs': {'gchat': args.gchat_ref, 'gcoms': args.gcoms_ref},
        'scope': 'windows_server_2022_native_msvc_and_nsis_service_lifecycle', 'windows_11_qualified': False,
    }, indent=2) + '\n')
    print('Retrieved verified Windows Server 2022 MSVC/NSIS artifacts: ' + str(output))


if __name__ == '__main__':
    main()
