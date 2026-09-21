#!/usr/bin/env python3
"""Build and exercise a source-bound iOS simulator app without a device signer.

Xcode links simulated entitlements before applying its host ad-hoc signature.
This command neither rebuilds nor qualifies a device IPA.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import plistlib
import shlex
import shutil
import subprocess
import sys
import tomllib

SPEC = importlib.util.spec_from_file_location('ios_lifecycle', Path(__file__).with_name('ios-lifecycle.py'))
lifecycle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lifecycle)
ios = lifecycle.ios
TARGET = 'aarch64-apple-ios-sim'


def configure_simulator(destination):
    destination.mkdir(parents=True, exist_ok=False)
    entitlements = destination / 'Simulator.entitlements'
    entitlements.write_bytes(plistlib.dumps({'application-identifier': ios.BUNDLE,
        'keychain-access-groups': [ios.BUNDLE], 'get-task-allow': True}))
    config = destination / 'simulator.xcconfig'
    config.write_text('CODE_SIGNING_ALLOWED = YES\nCODE_SIGN_STYLE = Manual\nCODE_SIGN_IDENTITY = -\n'
        'DEVELOPMENT_TEAM =\nPROVISIONING_PROFILE_SPECIFIER =\nPROVISIONING_PROFILE =\n'
        'CODE_SIGN_ENTITLEMENTS = ' + str(entitlements) + '\n')
    return config, entitlements


def verify_settings(settings, entitlements):
    targets = [item['buildSettings'] for item in settings
               if item.get('buildSettings', {}).get('PRODUCT_BUNDLE_IDENTIFIER') == ios.BUNDLE]
    ios.require(len(targets) == 1, 'expected one GChat simulator target')
    value = targets[0]
    ios.require(value.get('CODE_SIGNING_ALLOWED') == 'YES' and value.get('CODE_SIGN_IDENTITY') == '-'
                and value.get('CODE_SIGN_STYLE') == 'Manual'
                and value.get('CODE_SIGN_ENTITLEMENTS') == str(entitlements),
                'Xcode did not enable the exact simulator signing/link settings')
    ios.require(all(not value.get(key) for key in
                ('DEVELOPMENT_TEAM', 'PROVISIONING_PROFILE_SPECIFIER', 'PROVISIONING_PROFILE')),
                'simulator cannot require a distribution team or provisioning profile')
    ios.require('/Xcode_26.2.app/' in value.get('SDKROOT', '') and 'iPhoneSimulator' in value['SDKROOT'],
                'simulator did not select the pinned Xcode simulator SDK')
    return value


def simulator_environment(destination, environment, config, executable='/usr/bin/xcodebuild'):
    """Tauri adds provisioning flags by default; never forward them to Xcode."""
    destination.mkdir(parents=True, exist_ok=False)
    driver = destination / 'invoke.py'
    driver.write_text('import json, os, pathlib, sys\n'
        'args = sys.argv[1:]\n'
        'if "-exportArchive" in args or any(x.startswith("-authenticationKey") for x in args):\n'
        '    raise ValueError("simulator worker refuses export or account credentials")\n'
        'if any(x == "iphoneos" or x == "generic/platform=iOS" for x in args):\n'
        '    raise ValueError("simulator worker refuses a device SDK")\n'
        'if "CODE_SIGNING_ALLOWED=NO" in args:\n'
        '    raise ValueError("simulator entitlements require signing during link; --no-sign is invalid")\n'
        'expected = {"CODE_SIGNING_ALLOWED": "YES", "CODE_SIGN_IDENTITY": "-", "DEVELOPMENT_TEAM": "",\n'
        '            "PROVISIONING_PROFILE_SPECIFIER": "", "PROVISIONING_PROFILE": ""}\n'
        'for item in args:\n'
        '    key, separator, value = item.partition("=")\n'
        '    if separator and key in expected and value != expected[key]:\n'
        '        raise ValueError("command-line signing override conflicts with simulator policy")\n'
        'removed = [x for x in args if x in ("-allowProvisioningUpdates", "-allowProvisioningDeviceRegistration")]\n'
        'args = [x for x in args if x not in removed]\n'
        'with open(' + repr(str(destination / 'invocations.jsonl')) + ', "a") as stream:\n'
        '    stream.write(json.dumps({"arguments": args, "account_access_flags_removed": removed}) + "\\n")\n'
        'os.environ["DEVELOPER_DIR"] = ' + repr(environment['DEVELOPER_DIR']) + '\n'
        'os.environ["XCODE_XCCONFIG_FILE"] = ' + repr(str(config)) + '\n'
        'os.execv(' + repr(executable) + ', [' + repr(executable) + ', *args])\n')
    wrapper = destination / 'xcodebuild'
    wrapper.write_text('#!/bin/sh\nexec ' + shlex.quote(sys.executable) + ' ' + shlex.quote(str(driver)) + ' "$@"\n')
    wrapper.chmod(0o700)
    return dict(environment, PATH=str(destination) + os.pathsep + environment['PATH'])


def verify_app(app, destination):
    destination.mkdir(parents=True, exist_ok=False)
    info = plistlib.loads((app / 'Info.plist').read_bytes())
    ios.require(info.get('CFBundleIdentifier') == ios.BUNDLE
                and info.get('CFBundleSupportedPlatforms') == ['iPhoneSimulator'], 'invalid simulator app identity')
    name = info.get('CFBundleExecutable', '')
    ios.require(name and Path(name).name == name, 'invalid simulator executable name')
    binary = app / name
    ios.require(ios.output(['lipo', '-archs', binary]) == 'arm64', 'expected ARM64 simulator app')
    ios.require('IOSSIMULATOR' in ios.output(['xcrun', 'vtool', '-show-build', binary]), 'expected simulator platform')
    ios.require(not (app / 'embedded.mobileprovision').exists(), 'simulator cannot contain a device profile')
    linked = ios.simulator_linked_entitlements(binary)
    ios.run(['codesign', '--verify', '--deep', '--strict', app], timeout=120)
    encoded = subprocess.check_output(['codesign', '-d', '--entitlements', ':-', str(app)],
                                      stderr=subprocess.DEVNULL, timeout=30)
    host = plistlib.loads(encoded) if encoded.strip() else {}
    ios.require(host in ({}, {'com.apple.security.get-task-allow': True}),
                'host simulator signature cannot claim iOS Keychain or distribution authority')
    details = ios.output(['codesign', '-d', '--verbose=2', app], stderr=subprocess.STDOUT, timeout=30)
    ios.require('Signature=adhoc' in details.splitlines(), 'simulator must use an ad-hoc Xcode signature')
    report = {'schema': 1, 'scope': 'ios_xcode_linked_simulator_authority', 'passed': True,
              'device_qualified': False, 'executable': ios.reference(binary),
              'linked_simulator_authority': linked, 'host_entitlements': host, 'signature_details': details}
    ios.write_json(destination / 'report.json', report)
    return ios.reference(destination / 'report.json')


def build(args):
    ios.require(platform.system() == 'Darwin' and platform.machine() == 'arm64', 'use an Apple Silicon Mac worker')
    roots = {'gchat': args.gchat.resolve(), 'gcoms': args.gcoms.resolve()}
    before = {name: ios.source_identity(path) for name, path in roots.items()}
    for name in roots:
        ios.policy.source_commit(getattr(args, name + '_commit'))
        ios.require(before[name]['commit'] == getattr(args, name + '_commit'), 'source checkout mismatch')
    version = ios.build_number(args.build_number)
    destination = args.output.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    report = {'schema': 1, 'scope': 'ios_exact_pair_xcode_simulator_lifecycle', 'passed': False,
              'sources': before, 'build_number': version, 'bundle': ios.BUNDLE,
              'controller': ios.source_identity(Path(__file__).resolve().parents[1]),
              'harness': ios.reference(Path(__file__)), 'device_rebuilt': False,
              'device_qualified': False, 'distribution_signer_used': False,
              'physical_device_qualified': False, 'messaging_qualified': False, 'push_qualified': False}
    environment = {key: value for key, value in os.environ.items() if not key.startswith(
        ('APP_STORE_CONNECT_', 'IOS_CERTIFICATE', 'IOS_PROVISIONING_', 'IOS_MOBILE_', 'APPLE_API_', 'APPLE_DEVELOPMENT_TEAM'))
        and key not in ('GH_TOKEN', 'GITHUB_TOKEN')}
    environment.update(CARGO_INCREMENTAL='0', CI='true')
    try:
        report['xcode'] = ios.output(['xcodebuild', '-version'])
        ios.require(report['xcode'].splitlines()[0] == 'Xcode 26.2', 'unexpected Xcode version')
        report['rustc'] = ios.output(['rustc', '-vV'])
        for path in roots.values():
            pin = tomllib.loads((path / 'rust-toolchain.toml').read_text())['toolchain']['channel']
            ios.require(report['rustc'].splitlines()[0].startswith('rustc ' + pin), 'Rust source pin mismatch')
        ios.run(['rustup', 'target', 'add', TARGET], env=environment)
        chat, inputs = ios.prepare_pair(roots['gchat'], roots['gcoms'], destination / 'paired', TARGET, environment)
        report['dependency_inputs'] = inputs
        report['source_archives'] = {name: ios.reference(destination / 'paired/inputs' / (name + '.tar'))
                                     for name in roots}
        client, native = chat / 'apps/client', chat / 'apps/client/src-tauri'
        ios.run(['python3', chat / 'scripts/collect-notices.py'], cwd=chat, env=environment)
        config = destination / 'ios-config.json'
        ios.write_json(config, {'identifier': ios.BUNDLE, 'bundle': {'iOS': {
            'minimumSystemVersion': '15.0', 'bundleVersion': version}}})
        (native / 'Info.ios.plist').write_bytes(plistlib.dumps({'ITSAppUsesNonExemptEncryption': True}))
        ios.run(['npm', 'run', 'tauri', '--', 'ios', 'init', '--ci', '--skip-targets-install', '--config', config],
                cwd=client, env=environment)
        generated = native / 'gen/apple'
        project = ios.generated_project(generated)
        settings_file, entitlement_file = configure_simulator(destination / 'link-settings')
        environment = simulator_environment(destination / 'xcode-wrapper', environment, settings_file)
        report['generated_config'] = ios.reference(config)
        report['simulator_xcconfig'] = ios.reference(settings_file)
        report['simulator_entitlements'] = ios.reference(entitlement_file)
        settings = json.loads(ios.output(['xcodebuild', '-showBuildSettings', '-json', '-project', project,
            '-scheme', project.stem + '_iOS', '-configuration', 'release', '-sdk', 'iphonesimulator'],
            env=environment, timeout=120))
        ios.write_json(destination / 'simulator-build-settings.json', settings)
        verify_settings(settings, entitlement_file)
        report['effective_settings'] = ios.reference(destination / 'simulator-build-settings.json')
        metadata = json.loads(ios.output(['cargo', 'metadata', '--locked', '--manifest-path', native / 'Cargo.toml',
            '--filter-platform', TARGET, '--format-version=1'], cwd=chat, env=environment))
        ios.verify_resolved_protocol(metadata, chat.parent / 'gcoms')
        tree = ios.output(['cargo', 'tree', '--locked', '--manifest-path', native / 'Cargo.toml', '--target', TARGET,
            '--edges', 'normal', '--prefix', 'none', '--format', '{p}|{f}'], cwd=chat, env=environment)
        (destination / 'features.txt').write_text(tree + '\n')
        report['feature_graph'] = ios.feature_graph(tree)
        report['feature_graph_file'] = ios.reference(destination / 'features.txt')
        ios.run(['npm', 'run', 'tauri', '--', 'ios', 'build', '--ci', '--target', 'aarch64-sim',
                 '--archive-only', '--config', config], cwd=client, env=environment, timeout=5400)
        apps = list((generated / 'build').glob('**/*.xcarchive/Products/Applications/*.app'))
        ios.require(len(apps) == 1, 'expected exactly one simulator archive app')
        app = apps[0]
        report['linked_authority'] = verify_app(app, destination / 'authority')
        info = plistlib.loads((app / 'Info.plist').read_bytes())
        ios.require(info['CFBundleVersion'] == version, 'simulator version mismatch')
        report['executable'] = ios.reference(app / info['CFBundleExecutable'])
        archive = destination / 'simulator-app.zip'
        ios.run(['ditto', '-c', '-k', '--keepParent', app, archive])
        report['simulator_archive'] = ios.reference(archive)
        shutil.copyfile(project / 'project.pbxproj', destination / 'generated-project.pbxproj')
        report['generated_project'] = ios.reference(destination / 'generated-project.pbxproj')
        report['xcode_invocations'] = ios.reference(destination / 'xcode-wrapper/invocations.jsonl')
        report['lifecycle'] = lifecycle.run_application(app, destination / 'lifecycle')
        ios.verify_derived_inputs(chat, inputs)
        report['passed'] = True
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        lifecycle_receipt = destination / 'lifecycle/report.json'
        if lifecycle_receipt.exists():
            report['lifecycle'] = ios.reference(lifecycle_receipt)
        report['sources_unchanged'] = all(ios.source_identity(path) == before[name] for name, path in roots.items())
        report['passed'] = report['passed'] and report['sources_unchanged']
        ios.write_json(destination / 'report.json', report)
    ios.require(report['passed'], 'simulator source changed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('gchat', 'gcoms', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('gchat-commit', 'gcoms-commit', 'build-number'):
        parser.add_argument('--' + name, required=True)
    build(parser.parse_args())
