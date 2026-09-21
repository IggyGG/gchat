#!/usr/bin/env python3
"""Run an XCTest UI journey against a hash-bound, already-built simulator app.

Only the XCTest runner is compiled. An explicit simulator-only mode signs an
owned application copy for its private Keychain group; the retained application
is immutable. No device signing, provisioning or TestFlight submission occurs.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import platform
import plistlib
import re
import secrets
import shutil
import subprocess
import zipfile

SPEC = importlib.util.spec_from_file_location('ios_build', Path(__file__).with_name('ios-build.py'))
ios = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ios)
require = ios.require
TEST = 'testProfileBackgroundAndReopen'


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', 'repos/IggyGG/gchat/' + path]))


def run_binding(run, artifact, spec):
    require(run.get('id') == spec['run_id'] and run.get('head_sha') == spec['gchat_commit']
            and run.get('head_repository', {}).get('full_name') == 'IggyGG/gchat'
            and run.get('event') == 'workflow_dispatch' and run.get('status') == 'completed'
            and run.get('conclusion') in ('success', 'failure')
            and run.get('path') == '.github/workflows/ios-release.yml', 'original workflow binding mismatch')
    ios.policy.release_ref(run['head_branch'])
    expected = 'ios-' + spec['gchat_commit'] + '-' + spec['gcoms_commit'] + '-' + spec['build_number']
    require(artifact.get('id') == spec['artifact_id'] and artifact.get('name') == expected
            and artifact.get('expired') is False and artifact.get('workflow_run', {}).get('id') == spec['run_id']
            and artifact.get('digest') == 'sha256:' + spec['artifact_sha256'], 'original artifact binding mismatch')


def relocated(item, root):
    parts = PurePosixPath(item['path']).parts
    require(parts.count('ios-output') == 1, 'unexpected original artifact location')
    relative = PurePosixPath(*parts[parts.index('ios-output') + 1:])
    require(relative.parts and '..' not in relative.parts, 'unsafe original artifact location')
    path = root.joinpath(*relative.parts)
    require(path.is_file() and ios.digest(path) == item['sha256'] and path.stat().st_size == item['size'],
            'retained evidence hash mismatch')
    return path


def build_binding(report, spec):
    # An unrelated device/signing failure does not erase a completed simulator
    # build. Its failed verdict is retained and never promoted by this journey.
    require(report.get('scope') == 'ios_exact_pair_simulator_and_signed_ipa'
            and report.get('sources_unchanged') is True and report.get('bundle') == ios.BUNDLE
            and report.get('team') == ios.TEAM and report.get('build_number') == spec['build_number'],
            'original build scope/source identity mismatch')
    for name in ('gchat', 'gcoms'):
        require(report['sources'][name]['commit'] == spec[name + '_commit'], 'original build source mismatch')


def runner_project():
    return {'name': 'GChatLifecycle', 'options': {'deploymentTarget': {'iOS': '15.0'}},
        'targets': {'LifecycleTests': {'type': 'bundle.ui-testing', 'platform': 'iOS',
            'sources': ['LifecycleTests.swift'], 'settings': {'base': {
                'PRODUCT_BUNDLE_IDENTIFIER': 'boo.gchat.lifecycle-tests', 'GENERATE_INFOPLIST_FILE': 'YES',
                'SWIFT_VERSION': '5.0', 'CODE_SIGNING_ALLOWED': 'NO', 'IPHONEOS_DEPLOYMENT_TARGET': '15.0'}}}},
        'schemes': {'GChatLifecycle': {'build': {'targets': {'LifecycleTests': ['test']}},
            'test': {'targets': [{'name': 'LifecycleTests', 'parallelizable': False,
                                 'randomExecutionOrder': False}], 'gatherCoverageData': False,
                     'deleteScreenshotsWhenEachTestSucceeds': False}}}}


def test_result(summary):
    require(summary.get('result') == 'Passed' and summary.get('passedTests') == 1
            and summary.get('failedTests') == 0 and summary.get('skippedTests') == 0,
            'XCTest must complete exactly one passing lifecycle test with no failure or skip')


def application_for_journey(app, destination, keychain_fixture=False):
    """Retain the exact input; only an explicit simulator fixture may be derived."""
    info = plistlib.loads((app / 'Info.plist').read_bytes())
    name = info.get('CFBundleExecutable', '')
    require(name and Path(name).name == name, 'invalid simulator executable name')
    original = ios.reference(app / name)
    binding = {'original_application': original, 'application': original, 'application_resigned': False}
    if not keychain_fixture:
        return app, binding
    before = {str(path.relative_to(app)): ios.digest(path) for path in app.rglob('*') if path.is_file()}
    derived = destination / 'keychain-fixture' / app.name
    shutil.copytree(app, derived)
    signing = ios.sign_simulator(derived, destination / 'simulator-keychain-signing')
    signed = json.loads(Path(signing['path']).read_text())
    require(ios.digest(Path(signing['path'])) == signing['sha256']
            and signed.get('scope') == 'ios_simulator_adhoc_private_keychain_signing'
            and signed.get('passed') is True and signed.get('device_qualified') is False
            and signed.get('resources_unchanged') is True, 'simulator signing receipt is incomplete')
    require(all(signed['original_executable'][key] == original[key] for key in ('sha256', 'size')),
            'simulator signing did not preserve the original executable binding')
    actual = ios.reference(derived / name)
    require(signed.get('derived_executable') == actual, 'derived simulator executable binding mismatch')
    after = {str(path.relative_to(app)): ios.digest(path) for path in app.rglob('*') if path.is_file()}
    require(after == before, 'original simulator application changed during fixture signing')
    binding.update(application=actual, application_resigned=True, simulator_keychain_signing=signing,
                   original_application_unchanged=True, derived_simulator_only=True)
    return derived, binding


def cleanup_device(device, report):
    errors = []
    for command in (['xcrun', 'simctl', 'terminate', device, ios.BUNDLE],
                    ['xcrun', 'simctl', 'shutdown', device]):
        try:
            subprocess.run(command, capture_output=True, timeout=60)
        except Exception as error:
            errors.append(type(error).__name__ + ': ' + str(error))
    try:
        ios.run(['xcrun', 'simctl', 'delete', device], timeout=60)
    except Exception as error:
        errors.append(type(error).__name__ + ': ' + str(error))
    try:
        report['cleanup_complete'] = device not in ios.output(['xcrun', 'simctl', 'list', 'devices', '--json'])
    except Exception as error:
        report['cleanup_complete'] = False
        errors.append(type(error).__name__ + ': ' + str(error))
    report['cleanup_errors'] = errors
    report['cleanup_complete'] = report['cleanup_complete'] and not errors


def run_application(app, destination):
    """Exercise an already-built app without compiling or re-signing it."""
    destination.mkdir(parents=True, exist_ok=False)
    info = plistlib.loads((app / 'Info.plist').read_bytes())
    require(info.get('CFBundleIdentifier') == ios.BUNDLE
            and info.get('CFBundleSupportedPlatforms') == ['iPhoneSimulator'], 'expected GChat simulator app')
    name = info.get('CFBundleExecutable', '')
    require(name and Path(name).name == name, 'invalid simulator executable name')
    binary = app / name
    swift_source = Path(__file__).with_name('fixtures') / 'ios-lifecycle' / 'LifecycleTests.swift'
    report = {'schema': 1, 'scope': 'ios_installed_simulator_profile_background_reopen', 'passed': False,
              'application_recompiled': False, 'application_resigned': False,
              'application': ios.reference(binary), 'harness': ios.reference(Path(__file__)),
              'swift_test': ios.reference(swift_source), 'cleanup_complete': False,
              'network_onboarding_qualified': False, 'messaging_qualified': False,
              'push_qualified': False, 'physical_device_qualified': False}
    device = None
    try:
        report['xcode'] = ios.output(['xcodebuild', '-version'])
        require(report['xcode'].splitlines()[0] == 'Xcode 26.2', 'use the original pinned Xcode')
        runtime = ios.simulator_runtime()
        types = json.loads(ios.output(['xcrun', 'simctl', 'list', 'devicetypes', '--json']))['devicetypes']
        devices = json.loads(ios.output(['xcrun', 'simctl', 'list', 'devices', 'available', '--json']))['devices']
        phone = ios.simulator_phone(runtime, types, devices)
        device = ios.output(['xcrun', 'simctl', 'create', 'GChatLifecycle-' + secrets.token_hex(6), phone, runtime])
        require(re.fullmatch('[0-9A-Fa-f-]{36}', device), 'unexpected created simulator ID')
        report.update(device=device, runtime=runtime, device_type=phone)
        ios.run(['xcrun', 'simctl', 'boot', device], timeout=120)
        ios.run(['xcrun', 'simctl', 'bootstatus', device, '-b'], timeout=180)
        ios.run(['xcrun', 'simctl', 'install', device, app], timeout=120)
        runner = destination / 'runner'
        runner.mkdir()
        shutil.copyfile(swift_source, runner / swift_source.name)
        ios.write_json(runner / 'project.json', runner_project())
        ios.run(['xcodegen', 'generate', '--spec', 'project.json'], cwd=runner, timeout=120)
        results = destination / 'journey.xcresult'
        command = ['xcodebuild', 'test', '-project', runner / 'GChatLifecycle.xcodeproj', '-scheme', 'GChatLifecycle',
            '-destination', 'platform=iOS Simulator,id=' + device, '-derivedDataPath', destination / 'runner-derived',
            '-resultBundlePath', results, '-parallel-testing-enabled', 'NO', '-maximum-concurrent-test-simulator-destinations', '1',
            '-only-testing:LifecycleTests/GChatLifecycleTests/' + TEST, 'CODE_SIGNING_ALLOWED=NO']
        with (destination / 'xctest.log').open('wb') as log:
            # Artifact access is needed only by the downloader, never the app
            # or its native UI runner.
            environment = {key: value for key, value in os.environ.items()
                           if key not in ('GH_TOKEN', 'GITHUB_TOKEN')}
            completed = subprocess.run([str(value) for value in command], stdout=log,
                stderr=subprocess.STDOUT, env=environment, timeout=900)
        report['xctest_exit_code'] = completed.returncode
        report['xctest_log'] = ios.reference(destination / 'xctest.log')
        require(completed.returncode == 0, 'retained application lifecycle XCTest failed; see xctest.log')
        summary = json.loads(ios.output(['xcrun', 'xcresulttool', 'get', 'test-results', 'summary', '--path', results]))
        ios.write_json(destination / 'test-summary.json', summary)
        test_result(summary)
        report['test_summary'] = ios.reference(destination / 'test-summary.json')
        require(ios.digest(binary) == report['application']['sha256'], 'application changed during journey')
        report['passed'] = True
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        if device:
            cleanup_device(device, report)
        else:
            report['cleanup_complete'] = True
        report['passed'] = report['passed'] and report['cleanup_complete']
        ios.write_json(destination / 'report.json', report)
    require(report['passed'], 'lifecycle journey cleanup failed')
    return ios.reference(destination / 'report.json')


def main(args):
    require(platform.system() == 'Darwin' and platform.machine() == 'arm64', 'use an Apple Silicon Mac worker')
    spec = json.loads(args.spec.read_text())
    for name in ('gchat', 'gcoms'):
        ios.policy.source_commit(spec[name + '_commit'])
    ios.build_number(spec['build_number'])
    require(type(spec['run_id']) is int and type(spec['artifact_id']) is int
            and re.fullmatch('[0-9a-f]{64}', spec['artifact_sha256']), 'invalid original artifact identifiers')
    destination = args.output.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    swift_source = Path(__file__).with_name('fixtures') / 'ios-lifecycle' / 'LifecycleTests.swift'
    report = {'schema': 1, 'scope': 'ios_retained_simulator_profile_background_reopen', 'passed': False,
        'application_recompiled': False, 'original_build_verdict_unchanged': True,
        'simulator_keychain_fixture': args.simulator_keychain_fixture,
        'cryptographic_identity_comparison': False, 'network_onboarding_qualified': False,
        'messaging_qualified': False, 'push_qualified': False, 'physical_device_qualified': False,
        'cleanup_complete': False, 'harness': ios.reference(Path(__file__)),
        'swift_test': ios.reference(swift_source), 'inputs': spec}
    device = None
    try:
        original_run = api('actions/runs/' + str(spec['run_id']))
        artifact = api('actions/artifacts/' + str(spec['artifact_id']))
        run_binding(original_run, artifact, spec)
        ios.write_json(destination / 'original-run.json', original_run)
        ios.write_json(destination / 'original-artifact.json', artifact)
        archive = destination / 'original-artifact.zip'
        with archive.open('wb') as stream:
            subprocess.run(['gh', 'api', 'repos/IggyGG/gchat/actions/artifacts/' + str(spec['artifact_id']) + '/zip'],
                           stdout=stream, check=True, timeout=300)
        require(ios.digest(archive) == spec['artifact_sha256'], 'downloaded artifact digest mismatch')
        retained = destination / 'original'
        with zipfile.ZipFile(archive) as zipped:
            ios.inspect_zip(zipped)
            zipped.extractall(retained)
        root = retained / 'ios-output'
        original = json.loads((root / 'build.json').read_text())
        build_binding(original, spec)
        report['original_build'] = ios.reference(root / 'build.json')
        report['original_build_passed'] = original.get('passed')
        for name, checkout in (('gchat', args.gchat), ('gcoms', args.gcoms)):
            tree = ios.output(['git', 'rev-parse', spec[name + '_commit'] + '^{tree}'], cwd=checkout)
            require(original['sources'][name]['tree'] == tree, 'original source tree mismatch')
            source = subprocess.check_output(['git', 'archive', '--format=tar', spec[name + '_commit']], cwd=checkout)
            require(hashlib.sha256(source).hexdigest() == original['dependency_inputs']['source_archive_sha256'][name],
                    'original source archive mismatch')
        harness = subprocess.check_output(['git', 'show', spec['gchat_commit'] + ':scripts/ios-build.py'], cwd=args.gchat)
        require(hashlib.sha256(harness).hexdigest() == original['harness']['sha256'], 'original harness mismatch')
        smoke_path = relocated(original['simulator'], root)
        smoke = json.loads(smoke_path.read_text())
        require(smoke.get('passed') is True and smoke.get('cleanup_complete') is True,
                'original simulator startup/cleanup did not pass')
        report['original_simulator'] = ios.reference(smoke_path)
        app_zip = relocated(original['simulator_archive'], root)
        with zipfile.ZipFile(app_zip) as zipped:
            ios.inspect_zip(zipped)
        app_root = destination / 'application'
        ios.run(['ditto', '-x', '-k', app_zip, app_root])
        apps = list(app_root.glob('*.app'))
        require(len(apps) == 1, 'simulator archive must contain one application')
        app = apps[0]
        info = plistlib.loads((app / 'Info.plist').read_bytes())
        require(info.get('CFBundleIdentifier') == ios.BUNDLE and info.get('CFBundleVersion') == spec['build_number'],
                'retained simulator app identity mismatch')
        executable = info.get('CFBundleExecutable', '')
        require(executable and Path(executable).name == executable, 'invalid simulator executable name')
        binary = app / executable
        require(ios.digest(binary) == smoke['executable']['sha256']
                and binary.stat().st_size == smoke['executable']['size'], 'retained executable mismatch')
        app, binding = application_for_journey(app, destination, args.simulator_keychain_fixture)
        report.update(binding)
        binary = app / executable
        if args.simulator_keychain_fixture:
            derived_archive = destination / 'simulator-keychain-app.zip'
            ios.run(['ditto', '-c', '-k', '--keepParent', app, derived_archive])
            report['derived_simulator_archive'] = ios.reference(derived_archive)
        report['xcode'] = ios.output(['xcodebuild', '-version'])
        require(report['xcode'].splitlines()[0] == 'Xcode 26.2', 'use the original pinned Xcode')
        runtime = ios.simulator_runtime()
        types = json.loads(ios.output(['xcrun', 'simctl', 'list', 'devicetypes', '--json']))['devicetypes']
        devices = json.loads(ios.output(['xcrun', 'simctl', 'list', 'devices', 'available', '--json']))['devices']
        phone = ios.simulator_phone(runtime, types, devices)
        device = ios.output(['xcrun', 'simctl', 'create', 'GChatLifecycle-' + secrets.token_hex(6), phone, runtime])
        require(re.fullmatch('[0-9A-Fa-f-]{36}', device), 'unexpected created simulator ID')
        report.update(device=device, runtime=runtime, device_type=phone)
        ios.run(['xcrun', 'simctl', 'boot', device], timeout=120)
        ios.run(['xcrun', 'simctl', 'bootstatus', device, '-b'], timeout=180)
        ios.run(['xcrun', 'simctl', 'install', device, app], timeout=120)
        runner = destination / 'runner'
        runner.mkdir()
        shutil.copyfile(swift_source, runner / swift_source.name)
        ios.write_json(runner / 'project.json', runner_project())
        ios.run(['xcodegen', 'generate', '--spec', 'project.json'], cwd=runner, timeout=120)
        results = destination / 'journey.xcresult'
        command = ['xcodebuild', 'test', '-project', runner / 'GChatLifecycle.xcodeproj', '-scheme', 'GChatLifecycle',
            '-destination', 'platform=iOS Simulator,id=' + device, '-derivedDataPath', destination / 'runner-derived',
            '-resultBundlePath', results, '-parallel-testing-enabled', 'NO', '-maximum-concurrent-test-simulator-destinations', '1',
            '-only-testing:LifecycleTests/GChatLifecycleTests/' + TEST, 'CODE_SIGNING_ALLOWED=NO']
        with (destination / 'xctest.log').open('wb') as log:
            # Artifact access is needed only by the downloader, never the app
            # or its native UI runner.
            environment = {key: value for key, value in os.environ.items()
                           if key not in ('GH_TOKEN', 'GITHUB_TOKEN')}
            completed = subprocess.run([str(value) for value in command], stdout=log,
                stderr=subprocess.STDOUT, env=environment, timeout=900)
        report['xctest_exit_code'] = completed.returncode
        report['xctest_log'] = ios.reference(destination / 'xctest.log')
        require(completed.returncode == 0, 'retained application lifecycle XCTest failed; see xctest.log')
        summary = json.loads(ios.output(['xcrun', 'xcresulttool', 'get', 'test-results', 'summary', '--path', results]))
        ios.write_json(destination / 'test-summary.json', summary)
        test_result(summary)
        report['test_summary'] = ios.reference(destination / 'test-summary.json')
        require(ios.digest(binary) == report['application']['sha256'], 'retained application changed during journey')
        require(ios.digest(Path(report['original_application']['path'])) == report['original_application']['sha256'],
                'original simulator application changed during journey')
        report['passed'] = True
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        if device:
            cleanup_device(device, report)
        else:
            report['cleanup_complete'] = True
        report['passed'] = report['passed'] and report['cleanup_complete']
        ios.write_json(destination / 'report.json', report)
    require(report['passed'], 'lifecycle journey cleanup failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('spec', 'gchat', 'gcoms', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--simulator-keychain-fixture', action='store_true',
                        help='ad-hoc sign only an owned simulator copy with its private Keychain group')
    main(parser.parse_args())
