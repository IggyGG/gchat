#!/usr/bin/env python3
"""Frozen-pair iOS build, simulator startup, pinned IPA verification and upload.

Only retained derived inputs are changed. The simulator scope is startup/relaunch;
it does not qualify messaging, device persistence, live APNs or physical devices.
"""
import argparse
import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import platform
import plistlib
import re
import secrets
import shlex
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import time
import tomllib
import zipfile

from paired_sources import prepare_pair, verify_derived_inputs, verify_resolved_protocol
from release_evidence import digest, source_identity

BUNDLE = 'boo.gchat.app'
TEAM = 'U93DVTJ3T5'
APP_STORE_ID = '6814308446'
TARGETS = ('aarch64-apple-ios', 'aarch64-apple-ios-sim')
SPEC = importlib.util.spec_from_file_location('ios_source_policy', Path(__file__).with_name('macos-build.py'))
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def reference(path):
    return {'path': str(path.resolve()), 'sha256': digest(path), 'size': path.stat().st_size}


def verify_reference(item):
    path = Path(item['path'])
    require(path.is_file() and digest(path) == item['sha256'] and path.stat().st_size == item['size'],
            'retained artifact no longer matches its receipt')
    return path


def run(command, cwd=None, env=None, timeout=3600):
    subprocess.run([str(x) for x in command], cwd=cwd, env=env, check=True, timeout=timeout)


def output(command, **kwargs):
    return subprocess.check_output([str(x) for x in command], text=True, **kwargs).strip()


def secret_command(command):
    # security's password arguments must never appear in an exception or log.
    try:
        result = subprocess.run([str(x) for x in command], capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        raise ValueError('private signing command timed out') from None
    require(result.returncode == 0, 'private signing setup/cleanup command failed')


def build_number(value):
    require(re.fullmatch(r'[1-9][0-9]{0,3}\.[0-9]{1,2}\.[0-9]{1,2}', value),
            'build number must use Apple numeric major.minor.patch (four/two/two digits)')
    return value


def signing_pin():
    value = os.environ.get('IOS_SIGNING_CERT_SHA256', '').replace(':', '').lower()
    require(re.fullmatch('[0-9a-f]{64}', value), 'set the reviewed IOS_SIGNING_CERT_SHA256 pin')
    return value


def publisher_policy(path, pin):
    value = json.loads(path.read_text()).get('publisher_identities', {}).get('ios', {})
    require(value.get('name') == 'Gh0st' and value.get('team_id') == TEAM
            and value.get('distribution') == 'app-store' and value.get('certificate_sha256') == pin,
            'signing pin differs from the frozen Gh0st iOS publication policy')
    return value


def verify_checkouts(args):
    chat, coms = args.gchat.resolve(), args.gcoms.resolve()
    chat_ref, coms_ref = policy.release_ref(args.gchat_ref), policy.release_ref(args.gcoms_ref)
    env = os.environ
    require(env.get('GITHUB_SHA') == args.gchat_commit and env.get('GITHUB_WORKFLOW_SHA') == args.gchat_commit
            and env.get('GITHUB_REF') == chat_ref
            and env.get('GITHUB_WORKFLOW_REF') == f'{policy.REPO}/.github/workflows/ios-release.yml@{chat_ref}',
            'workflow/source/ref identity differs from the selected protected GChat source')
    for root, commit, ref in ((chat, args.gchat_commit, chat_ref), (coms, args.gcoms_commit, coms_ref)):
        policy.source_commit(commit)
        require(source_identity(root)['commit'] == commit, 'checkout differs from frozen source')
        local = ref.replace('refs/heads/', 'refs/remotes/origin/', 1) if ref.startswith('refs/heads/') else ref
        tip = output(['git', 'rev-parse', local + '^{commit}'], cwd=root)
        if root == chat or ref.startswith('refs/tags/'):
            require(tip == commit, 'protected release ref moved from frozen source')
        else:
            run(['git', 'merge-base', '--is-ancestor', commit, tip], cwd=root)


def feature_graph(text):
    found = {}
    for line in text.splitlines():
        if '|' not in line:
            continue
        package, features = line.split('|', 1)
        name = package.split()[0]
        if name == 'gcoms' or name.startswith('gcoms-'):
            found.setdefault(name, set()).update(x.strip() for x in features.replace(' (*)', '').split(',') if x.strip())
    require('network-client' in found.get('gcoms', set()), 'iOS application must enable network-client')
    require('gcoms-node' in found and 'gcoms-runtime' in found, 'iOS graph omits the actual runtime')
    require('relay-host' not in found['gcoms-node'], 'iOS application must compile out relay hosting')
    # RPC can compile IPC types; this is distinct from the embedded/launch host backends.
    require(not ({'embedded', 'launch'} & found['gcoms']), 'iOS graph enables a desktop host backend')
    return {name: sorted(features) for name, features in sorted(found.items())}


def validate_profile(value, pin, now=None):
    now = now or datetime.now(timezone.utc)
    expiry = value.get('ExpirationDate')
    require(isinstance(expiry, datetime), 'provisioning profile has no expiry')
    require(expiry.replace(tzinfo=timezone.utc) > now, 'provisioning profile expired')
    require(value.get('TeamIdentifier') == [TEAM], 'provisioning profile team mismatch')
    require('ProvisionedDevices' not in value and value.get('ProvisionsAllDevices') is not True,
            'expected App Store distribution profile, not device/ad-hoc/enterprise')
    entitlements = value.get('Entitlements', {})
    validate_entitlements(entitlements, profile=True)
    certificates = value.get('DeveloperCertificates', [])
    require(len(certificates) == 1 and hashlib.sha256(certificates[0]).hexdigest() == pin,
            'profile certificate does not match the single pinned distribution signer')
    uuid = value.get('UUID', '')
    require(re.fullmatch('[0-9a-fA-F-]{36}', uuid), 'invalid provisioning profile UUID')
    return {'uuid': uuid, 'name': value.get('Name'), 'expires': expiry.isoformat(),
            'team': TEAM, 'bundle': BUNDLE, 'certificate_sha256': pin}


def validate_entitlements(value, profile=False):
    require(value.get('application-identifier') == TEAM + '.' + BUNDLE, 'application entitlement mismatch')
    require(value.get('com.apple.developer.team-identifier') == TEAM, 'team entitlement mismatch')
    require(value.get('get-task-allow') is False, 'debugger entitlement must be explicitly disabled')
    require(value.get('aps-environment') == 'production', 'production APNs entitlement missing')
    groups = value.get('keychain-access-groups', [])
    allowed = {TEAM + '.' + BUNDLE}
    if profile:
        # Apple's TN3125 profiles include this system token group in their
        # allowlist. The signed application still claims only its exact group.
        allowed.update({TEAM + '.*', 'com.apple.token'})
    require(isinstance(groups, list) and set(groups) <= allowed, 'unexpected shared Keychain access group')


def decode_profile(path):
    return plistlib.loads(subprocess.check_output(['security', 'cms', '-D', '-i', str(path)]))


def keychains():
    return shlex.split(output(['security', 'list-keychains', '-d', 'user']))


def profile_files():
    result = {}
    for relative in ('Library/MobileDevice/Provisioning Profiles',
                     'Library/Developer/Xcode/UserData/Provisioning Profiles'):
        root = Path.home() / relative
        if root.exists():
            result.update({str(path): digest(path) for path in root.glob('*.mobileprovision')})
    return result


@contextmanager
def signer(destination, profile, pin, profile_bytes=None):
    """Import only our key in an isolated keychain; restore the exact search list."""
    before_keys, before_profiles = keychains(), profile_files()
    require(not any(Path(path).name == profile['uuid'] + '.mobileprovision' for path in before_profiles),
            'a profile with this UUID already exists; use a fresh isolated worker')
    cleanup = {'passed': False, 'original_keychain_search_restored': False,
               'temporary_keychain_removed': False, 'original_profiles_unchanged': False,
               'private_certificate_removed': False, 'errors': []}
    with tempfile.TemporaryDirectory(prefix='gchat-ios-sign-') as temporary:
        private = Path(temporary)
        private.chmod(0o700)
        keychain = private / 'signing.keychain-db'
        p12 = private / 'publisher.p12'
        password = secrets.token_urlsafe(32)
        created = False
        try:
            if profile_bytes is not None:
                # Xcode versions use both locations. Install only the exact
                # validated UUID and never overwrite an existing profile.
                for relative in ('Library/MobileDevice/Provisioning Profiles',
                                 'Library/Developer/Xcode/UserData/Provisioning Profiles'):
                    directory = Path.home() / relative
                    directory.mkdir(parents=True, exist_ok=True)
                    target = directory / (profile['uuid'] + '.mobileprovision')
                    with target.open('xb') as stream:
                        stream.write(profile_bytes)
                    target.chmod(0o600)
                    require(validate_profile(decode_profile(target), pin) == profile,
                            'installed profile differs from the validated input')
            p12.write_bytes(base64.b64decode(os.environ['IOS_CERTIFICATE_BASE64'], validate=True))
            p12.chmod(0o600)
            secret_command(['security', 'create-keychain', '-p', password, keychain])
            created = True
            secret_command(['security', 'set-keychain-settings', '-lut', '7200', keychain])
            secret_command(['security', 'unlock-keychain', '-p', password, keychain])
            secret_command(['security', 'import', p12, '-k', keychain, '-P', os.environ['IOS_CERTIFICATE_PASSWORD'],
                            '-T', '/usr/bin/codesign', '-T', '/usr/bin/security'])
            secret_command(['security', 'set-key-partition-list', '-S', 'apple-tool:,apple:,codesign:',
                            '-s', '-k', password, keychain])
            secret_command(['security', 'list-keychains', '-d', 'user', '-s', keychain, *before_keys])
            pem = subprocess.check_output(['security', 'find-certificate', '-a', '-p', str(keychain)])
            certificates = re.findall(rb'-----BEGIN CERTIFICATE-----\s*(.*?)\s*-----END CERTIFICATE-----', pem, re.S)
            matching = [base64.b64decode(re.sub(rb'\s', b'', cert), validate=True) for cert in certificates]
            matching = [cert for cert in matching if hashlib.sha256(cert).hexdigest() == pin]
            require(len(matching) == 1, 'imported keychain does not contain the pinned distribution certificate')
            sha1 = hashlib.sha1(matching[0]).hexdigest().upper()
            identities = output(['security', 'find-identity', '-v', '-p', 'codesigning', keychain])
            require(sha1 in identities, 'pinned certificate has no valid signing private key')
            (destination / 'distribution-certificate.der').write_bytes(matching[0])
            yield keychain, sha1
        finally:
            original_error = sys.exc_info()[1]

            def attempt(step, action):
                try:
                    return action()
                except BaseException as error:
                    # Do not serialize subprocess arguments or private material.
                    cleanup['errors'].append({'step': step, 'error_type': type(error).__name__})
                    return None

            # Every removal/restore is independent: a malformed profile must not
            # strand the signing key or prevent a terminal cleanup receipt.
            current_profiles = attempt('enumerate_profiles', profile_files) or {}
            for path in current_profiles:
                if path not in before_profiles:
                    candidate = Path(path)

                    def remove_profile():
                        value = decode_profile(candidate)
                        if value.get('UUID') != profile['uuid']:
                            return
                        validate_profile(value, pin)
                        candidate.unlink()

                    attempt('remove_owned_profile', remove_profile)
            if created:
                attempt('restore_keychain_search', lambda: secret_command(
                    ['security', 'list-keychains', '-d', 'user', '-s', *before_keys]))
                attempt('delete_temporary_keychain', lambda: secret_command(['security', 'delete-keychain', keychain]))
            attempt('remove_private_certificate', lambda: p12.unlink(missing_ok=True))
            cleanup['temporary_keychain_removed'] = attempt('verify_keychain_removed', lambda: not keychain.exists()) is True
            cleanup['private_certificate_removed'] = attempt('verify_certificate_removed', lambda: not p12.exists()) is True
            cleanup['original_keychain_search_restored'] = attempt('verify_keychain_search', keychains) == before_keys
            cleanup['original_profiles_unchanged'] = attempt('verify_profiles', profile_files) == before_profiles
            cleanup['passed'] = not cleanup['errors'] and all(
                cleanup[name] for name in cleanup if name not in {'passed', 'errors'})
            attempt('write_cleanup_receipt', lambda: write_json(destination / 'signing-cleanup.json', cleanup))
            if cleanup['errors'] or not cleanup['passed']:
                if original_error is not None:
                    original_error.add_note('iOS signing cleanup also failed; see signing-cleanup.json where writable')
                else:
                    raise ValueError('iOS signer did not restore its keychain/profile boundary')


def xcode_environment(destination, environment, xcconfig=None, executable='/usr/bin/xcodebuild', export_options=None):
    """Restore public tool selection after cargo-mobile2 clears child env vars."""
    developer = environment.get('DEVELOPER_DIR', '')
    require(Path(developer).is_absolute(), 'an explicit absolute Xcode developer directory is required')
    destination.mkdir()
    wrapper = destination / 'xcodebuild'
    text = '#!/bin/sh\nexport DEVELOPER_DIR=' + shlex.quote(developer) + '\n'
    text += ('export XCODE_XCCONFIG_FILE=' + shlex.quote(str(xcconfig.resolve())) + '\n'
             if xcconfig else 'unset XCODE_XCCONFIG_FILE\n')
    if export_options:
        # cargo-mobile2 generates its own export plist. Keep archive compilation
        # untouched, but make the final export use our already validated manual
        # distribution identity rather than its default development identity.
        expected = plistlib.loads(export_options.read_bytes())
        require(expected.get('method') == 'app-store-connect'
                and expected.get('signingStyle') == 'manual' and expected.get('teamID') == TEAM
                and set(expected.get('provisioningProfiles', {})) == {BUNDLE}, 'invalid pinned export policy')
        dispatcher = destination / 'export.py'
        dispatcher.write_text('import os, pathlib, plistlib, sys\n'
            'args = sys.argv[1:]\n'
            'if "-exportArchive" in args:\n'
            '    indices = [i for i, value in enumerate(args) if value == "-exportOptionsPlist"]\n'
            '    if len(indices) != 1 or indices[0] + 1 >= len(args):\n'
            '        raise ValueError("expected exactly one export options argument")\n'
            '    index = indices[0] + 1\n'
            '    original = pathlib.Path(args[index])\n'
            '    if original.stat().st_size > 1048576:\n'
            '        raise ValueError("unexpected export options size")\n'
            '    pathlib.Path(' + repr(str((destination / 'original-export-options.plist').resolve())) + ').write_bytes(original.read_bytes())\n'
            '    pinned = pathlib.Path(' + repr(str(export_options.resolve())) + ')\n'
            '    if plistlib.loads(pinned.read_bytes()) != ' + repr(expected) + ':\n'
            '        raise ValueError("pinned export policy changed")\n'
            '    args[index] = str(pinned)\n'
            'os.execv(' + repr(executable) + ', [' + repr(executable) + ', *args])\n')
        text += 'exec ' + shlex.quote(sys.executable) + ' ' + shlex.quote(str(dispatcher.resolve())) + ' "$@"\n'
    else:
        text += 'exec ' + shlex.quote(executable) + ' "$@"\n'
    wrapper.write_text(text)
    wrapper.chmod(0o700)
    return dict(environment, PATH=str(destination.resolve()) + os.pathsep + environment['PATH'])


def verify_device_settings(settings, profile, identity):
    targets = [item['buildSettings'] for item in settings
               if item.get('buildSettings', {}).get('PRODUCT_BUNDLE_IDENTIFIER') == BUNDLE]
    require(len(targets) == 1, 'device build settings must identify exactly one GChat target')
    value = targets[0]
    require(value.get('CODE_SIGN_STYLE') == 'Manual' and value.get('DEVELOPMENT_TEAM') == TEAM
            and value.get('PROVISIONING_PROFILE_SPECIFIER') == profile['uuid']
            and value.get('CODE_SIGN_IDENTITY') == identity, 'manual signing settings did not reach xcodebuild')
    require('/Xcode_26.2.app/' in value.get('SDKROOT', '') and 'iPhoneOS' in value['SDKROOT'],
            'device build did not select the pinned Xcode iOS SDK')


def configure_project(generated):
    files = sorted(generated.glob('*_iOS/*.entitlements'))
    require(len(files) == 1, 'expected exactly one generated iOS entitlements file')
    path = files[0]
    value = plistlib.loads(path.read_bytes())
    value.update({'application-identifier': TEAM + '.' + BUNDLE,
                  'com.apple.developer.team-identifier': TEAM, 'aps-environment': 'production',
                  'get-task-allow': False, 'keychain-access-groups': [TEAM + '.' + BUNDLE]})
    path.write_bytes(plistlib.dumps(value))
    return path


def simulator_linked_entitlements(binary):
    """Read Xcode's simulator authority from Mach-O sections, not its signature."""
    require(binary.stat().st_size <= 256 * 1024 * 1024, 'unexpected simulator executable size')
    data = binary.read_bytes()
    require(len(data) >= 32, 'truncated simulator Mach-O')
    magic, cpu, _, kind, count, commands, _, _ = struct.unpack_from('<8I', data)
    require(magic == 0xfeedfacf and cpu == 0x100000c and kind == 2
            and count <= 4096 and 32 + commands <= len(data), 'expected ARM64 executable Mach-O')
    position, sections = 32, {}
    for _ in range(count):
        require(position + 8 <= 32 + commands, 'truncated Mach-O command')
        command, size = struct.unpack_from('<II', data, position)
        require(size >= 8 and position + size <= 32 + commands, 'invalid Mach-O command size')
        if command == 0x19:
            require(size >= 72, 'truncated Mach-O segment')
            segment = struct.unpack_from('<II16s4Q4I', data, position)
            section_count = segment[-2]
            require(section_count <= 1024 and 72 + section_count * 80 <= size, 'invalid Mach-O sections')
            for index in range(section_count):
                row = struct.unpack_from('<16s16sQQ8I', data, position + 72 + index * 80)
                name, owner = row[0].rstrip(b'\0'), row[1].rstrip(b'\0')
                if name not in (b'__entitlements', b'__ents_der'):
                    continue
                length, offset = row[3], row[4]
                require(owner == b'__TEXT' and segment[2].rstrip(b'\0') == b'__TEXT'
                        and name not in sections and 0 < length <= 65536
                        and segment[5] <= offset and offset + length <= segment[5] + segment[6]
                        and offset + length <= len(data), 'invalid simulator entitlement section')
                sections[name] = data[offset:offset + length]
        position += size
    require(position == 32 + commands, 'Mach-O command count mismatch')
    require(set(sections) == {b'__entitlements', b'__ents_der'},
            'simulator must be linked with Xcode entitlement sections; post-link signing cannot add them')
    value = plistlib.loads(sections[b'__entitlements'].rstrip(b'\0'))
    expected = {'application-identifier': BUNDLE, 'keychain-access-groups': [BUNDLE], 'get-task-allow': True}
    require(value == expected, 'unexpected linked simulator Keychain or application authority')
    return {'entitlements': value, 'sections': {name.decode(): {
        'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)} for name, raw in sections.items()}}


def sign_simulator(app, destination):
    """Ad-hoc sign only a derived simulator app, never a device distribution."""
    require(platform.system() == 'Darwin', 'simulator signing requires macOS')
    info = plistlib.loads((app / 'Info.plist').read_bytes())
    require(info.get('CFBundleIdentifier') == BUNDLE
            and info.get('CFBundleSupportedPlatforms') == ['iPhoneSimulator'],
            'simulator signing refuses device or other application bundles')
    name = info.get('CFBundleExecutable', '')
    require(name and Path(name).name == name, 'invalid simulator executable name')
    binary = app / name
    require(output(['lipo', '-archs', binary]) == 'arm64', 'expected ARM64 simulator application')
    settings = output(['xcrun', 'vtool', '-show-build', binary])
    require(re.search(r'platform\s+IOSSIMULATOR\b', settings)
            and not re.search(r'platform\s+IOS\b', settings), 'refusing to ad-hoc sign a device binary')
    require(not (app / 'embedded.mobileprovision').exists()
            and not list(app.glob('PlugIns/*.appex')), 'simulator must not contain device provisioning or extensions')
    linked = simulator_linked_entitlements(binary)
    destination.mkdir(parents=True, exist_ok=False)
    # Simulator iOS authority is embedded by Xcode while linking. The outer
    # signature is checked by host macOS and must not claim iOS Keychain groups.
    # Lifecycle04/05 demonstrated taskgated rejection of that invalid shape.
    entitlements = {'com.apple.security.get-task-allow': True}
    entitlement_file = destination / 'entitlements.plist'
    entitlement_file.write_bytes(plistlib.dumps(entitlements))
    # Preserve the unsigned/ad-hoc compiler output separately. Adding the
    # entitlements changes executable bytes; it is a derived artifact, not the
    # original retained simulator artifact or a distribution-signed app.
    original = destination / 'input-executable'
    shutil.copyfile(binary, original)
    report = {'schema': 1, 'scope': 'ios_simulator_adhoc_private_keychain_signing',
              'passed': False, 'bundle': BUNDLE, 'device_qualified': False,
              'original_executable': reference(original), 'entitlements': entitlements,
              'linked_simulator_authority': linked}
    def resources():
        return {str(path.relative_to(app)): digest(path) for path in app.rglob('*')
                if path.is_file() and path != binary and '_CodeSignature' not in path.relative_to(app).parts}
    before = resources()
    try:
        run(['codesign', '--force', '--sign', '-', '--generate-entitlement-der',
             '--entitlements', entitlement_file, app], timeout=120)
        run(['codesign', '--verify', '--deep', '--strict', app], timeout=120)
        actual = plistlib.loads(subprocess.check_output(
            ['codesign', '-d', '--entitlements', ':-', str(app)], stderr=subprocess.DEVNULL, timeout=30))
        require(actual == entitlements, 'simulator signature has unexpected Keychain or application authority')
        require(simulator_linked_entitlements(binary) == linked, 'signing changed linked simulator authority')
        details = output(['codesign', '-d', '--verbose=2', app], stderr=subprocess.STDOUT, timeout=30)
        require('Signature=adhoc' in details.splitlines(), 'simulator fixture must use ad-hoc signing only')
        require(resources() == before, 'simulator signing changed application resources')
        report.update(passed=True, derived_executable=reference(binary), verified_entitlements=actual,
                      signature_details=details, resources_unchanged=True)
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        write_json(destination / 'report.json', report)
    return reference(destination / 'report.json')


def generated_project(generated):
    # Pinned Tauri/XcodeGen emits gchat-desktop.xcodeproj. Its built-in
    # project.xcworkspace is nested, not a sibling *.xcworkspace.
    projects = list(generated.glob('*.xcodeproj'))
    require(len(projects) == 1 and (projects[0] / 'project.pbxproj').is_file(),
            'expected exactly one generated Xcode project')
    return projects[0]


def simulator_runtime():
    runtimes = json.loads(output(['xcrun', 'simctl', 'list', 'runtimes', '--json']))['runtimes']
    ios = [item for item in runtimes if item.get('isAvailable') and '.iOS-' in item.get('identifier', '')]
    require(ios, 'install an available iOS simulator runtime before building')
    return max(ios, key=lambda item: tuple(int(x) for x in item['version'].split('.')))['identifier']


def simulator_phone(runtime, types, devices):
    # Device type order is not a compatibility order: Xcode 26 lists older
    # iPhone 6s models after recent phones. Reuse the type of an available
    # device already instantiated for this runtime, but create our own device.
    phones = {item['identifier']: item for item in types if item['name'].startswith('iPhone')}
    for device in devices.get(runtime, []):
        if not device.get('isAvailable'):
            continue
        identifier = device.get('deviceTypeIdentifier')
        if identifier in phones:
            return identifier
        if identifier is None:
            for identifier, kind in phones.items():
                if kind['name'] == device.get('name'):
                    return identifier
    raise ValueError('no available iPhone device type is known compatible with the selected iOS runtime')


def cleanup_simulator(device, report):
    """Try every owned-device cleanup step without masking a build failure."""
    errors = []
    commands = (
        ('terminate', ['xcrun', 'simctl', 'terminate', device, BUNDLE], 30, False),
        ('shutdown', ['xcrun', 'simctl', 'shutdown', device], 60, False),
        ('delete', ['xcrun', 'simctl', 'delete', device], 60, True),
    )
    for step, command, timeout, check in commands:
        try:
            subprocess.run(command, capture_output=True, timeout=timeout, check=check)
        except Exception as error:
            errors.append({'step': step, 'error_type': type(error).__name__})
    try:
        remaining = output(['xcrun', 'simctl', 'list', 'devices', '--json'], timeout=30)
        report['owned_device_removed'] = device not in remaining
    except Exception as error:
        report['owned_device_removed'] = False
        errors.append({'step': 'verify_removal', 'error_type': type(error).__name__})
    report['cleanup_errors'] = errors
    report['cleanup_complete'] = report['owned_device_removed'] and not errors


def simulator_smoke(app, destination):
    destination.mkdir()
    report = {'schema': 1, 'scope': 'ios_simulator_native_startup_relaunch', 'passed': False,
              'physical_device_qualified': False, 'profile_journey_qualified': False,
              'messaging_qualified': False, 'push_qualified': False, 'cleanup_complete': False}
    device = None
    try:
        info = plistlib.loads((app / 'Info.plist').read_bytes())
        require(info.get('CFBundleIdentifier') == BUNDLE, 'simulator bundle identity mismatch')
        report['executable'] = reference(app / info['CFBundleExecutable'])
        runtime = simulator_runtime()
        types = json.loads(output(['xcrun', 'simctl', 'list', 'devicetypes', '--json']))['devicetypes']
        devices = json.loads(output(['xcrun', 'simctl', 'list', 'devices', 'available', '--json']))['devices']
        phone = simulator_phone(runtime, types, devices)
        write_json(destination / 'selection.json', {'runtime': runtime, 'device_type': phone,
                                                   'device_types': types, 'available_devices': devices})
        created = output(['xcrun', 'simctl', 'create', 'GChat-' + secrets.token_hex(6), phone, runtime])
        require(re.fullmatch('[0-9A-Fa-f-]{36}', created), 'unexpected created simulator ID')
        device = created
        report.update(device=device, runtime=runtime, device_type=phone)
        run(['xcrun', 'simctl', 'boot', device], timeout=120)
        run(['xcrun', 'simctl', 'bootstatus', device, '-b'], timeout=180)
        run(['xcrun', 'simctl', 'install', device, app], timeout=120)
        report['launches'] = []
        for phase in ('fresh', 'relaunch'):
            line = output(['xcrun', 'simctl', 'launch', '--terminate-running-process', device, BUNDLE], timeout=60)
            match = re.fullmatch(re.escape(BUNDLE) + r': ([1-9][0-9]*)', line)
            require(match is not None, 'simulator did not report the actual app PID')
            pid = int(match.group(1))
            # A native crash or immediate shutdown must fail startup qualification.
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                os.kill(pid, 0)
                time.sleep(1)
            command = output(['ps', '-p', str(pid), '-o', 'command='])
            require(str(app.name) + '/' in command, 'simulator PID no longer belongs to the installed app')
            screenshot = destination / (phase + '.png')
            run(['xcrun', 'simctl', 'io', device, 'screenshot', screenshot], timeout=30)
            require(screenshot.stat().st_size > 1000, 'simulator screenshot is empty')
            report['launches'].append({'phase': phase, 'pid': pid, 'alive_seconds': 15,
                                       'screenshot': reference(screenshot)})
            run(['xcrun', 'simctl', 'terminate', device, BUNDLE], timeout=30)
        report['passed'] = True
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        if device:
            cleanup_simulator(device, report)
        else:
            report['cleanup_complete'] = True
        report['passed'] = report['passed'] and report['cleanup_complete']
        write_json(destination / 'report.json', report)
    require(report['passed'], 'simulator startup or teardown did not complete')
    return reference(destination / 'report.json')


def inspect_zip(archive):
    require(archive.infolist(), 'empty IPA')
    names = set()
    for entry in archive.infolist():
        # ZipInfo normalizes the host separator and truncates NULs. Validate
        # the original spelling as well, including on Windows CI workers.
        for spelling in (entry.orig_filename, entry.filename):
            name = PurePosixPath(spelling)
            require(not name.is_absolute() and '..' not in name.parts and '\\' not in spelling
                    and '\0' not in spelling, 'unsafe IPA archive path')
        require(entry.filename not in names, 'duplicate IPA archive entry')
        names.add(entry.filename)
        if stat.S_ISLNK(entry.external_attr >> 16):
            target = PurePosixPath(archive.read(entry).decode())
            require(not target.is_absolute() and '..' not in target.parts, 'unsafe IPA symlink')


def verify_ipa(ipa, destination, pin, version):
    with zipfile.ZipFile(ipa) as archive:
        inspect_zip(archive)
    destination.mkdir()
    run(['ditto', '-x', '-k', ipa, destination])
    apps = list((destination / 'Payload').glob('*.app'))
    require(len(apps) == 1, 'expected one main iOS application in IPA')
    app = apps[0]
    require(not list(app.glob('PlugIns/*.appex')), 'new app extensions require their own profile validation')
    info = plistlib.loads((app / 'Info.plist').read_bytes())
    require(info.get('CFBundleIdentifier') == BUNDLE, 'IPA bundle identifier mismatch')
    require(info.get('CFBundleVersion') == version, 'IPA build number mismatch')
    require(info.get('MinimumOSVersion') == '15.0', 'IPA minimum iOS version mismatch')
    executable = info.get('CFBundleExecutable', '')
    require(executable and Path(executable).name == executable, 'invalid IPA executable name')
    binary = app / executable
    require(output(['lipo', '-archs', binary]) == 'arm64', 'device IPA must contain only arm64')
    build = output(['xcrun', 'vtool', '-show-build', binary])
    require(re.search(r'platform\s+IOS\b', build) and 'IOSSIMULATOR' not in build,
            'IPA executable is not an iOS device binary')
    run(['codesign', '--verify', '--deep', '--strict', app])
    entitlements = plistlib.loads(subprocess.check_output(['codesign', '-d', '--entitlements', ':-', str(app)],
                                                         stderr=subprocess.DEVNULL))
    validate_entitlements(entitlements)
    leaf_prefix = destination / 'signer-'
    run(['codesign', '-d', '--extract-certificates=' + str(leaf_prefix), app])
    certificate = Path(str(leaf_prefix) + '0')
    require(digest(certificate) == pin, 'IPA signer differs from pinned distribution certificate')
    profile = validate_profile(decode_profile(app / 'embedded.mobileprovision'), pin)
    # The executable and certificate remain recoverable from the retained IPA;
    # avoid implying a separately uploaded extracted application exists.
    executable_receipt = {key: value for key, value in reference(binary).items() if key != 'path'}
    executable_receipt['ipa_member'] = str(binary.relative_to(destination))
    certificate_copy = destination.parent / 'ipa-signer.der'
    shutil.copyfile(certificate, certificate_copy)
    return {'ipa': reference(ipa), 'executable': executable_receipt, 'certificate': reference(certificate_copy),
            'entitlements': entitlements, 'profile': profile, 'build_number': version,
            'bundle': BUNDLE, 'architectures': ['arm64'], 'minimum_ios': '15.0'}


def build(args):
    require(platform.system() == 'Darwin' and platform.machine() == 'arm64', 'use an Apple Silicon Mac worker')
    originals = {'gchat': args.gchat.resolve(), 'gcoms': args.gcoms.resolve()}
    before = {name: source_identity(root) for name, root in originals.items()}
    destination = args.output.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    version = build_number(args.build_number)
    pin = signing_pin()
    report = {'schema': 1, 'scope': 'ios_exact_pair_simulator_and_signed_ipa', 'passed': False,
              'sources': before, 'bundle': BUNDLE, 'team': TEAM, 'app_store_id': APP_STORE_ID,
              'build_number': version, 'harness': reference(Path(__file__)),
              'physical_device_qualified': False, 'messaging_qualified': False, 'push_qualified': False}
    environment = dict(os.environ, CARGO_INCREMENTAL='0', CI='true', APPLE_DEVELOPMENT_TEAM=TEAM)
    # Build subprocesses never receive App Store upload credentials or raw key material.
    for key in list(environment):
        if key.startswith(('APP_STORE_CONNECT_', 'IOS_CERTIFICATE', 'IOS_PROVISIONING_', 'APPLE_API_')):
            environment.pop(key)
    try:
        # Reject bad provisioning inputs before spending time compiling either
        # target. This public profile allowlist is not the app's entitlement set.
        profile_bytes = base64.b64decode(os.environ['IOS_PROVISIONING_PROFILE_BASE64'], validate=True)
        with tempfile.TemporaryDirectory(prefix='gchat-ios-profile-') as temporary:
            profile_path = Path(temporary) / 'input.mobileprovision'
            profile_path.write_bytes(profile_bytes)
            profile_path.chmod(0o600)
            profile = validate_profile(decode_profile(profile_path), pin)
        report['provisioning_profile'] = profile
        report['xcode'] = output(['xcodebuild', '-version'])
        require(report['xcode'].splitlines()[0] == 'Xcode 26.2', 'unexpected Xcode version')
        environment = xcode_environment(destination / 'simulator-xcode', environment)
        report['simulator_xcode_wrapper'] = reference(destination / 'simulator-xcode/xcodebuild')
        report['rustc'] = output(['rustc', '-vV'])
        for root in originals.values():
            pinned = tomllib.loads((root / 'rust-toolchain.toml').read_text())['toolchain']['channel']
            require(report['rustc'].splitlines()[0].startswith('rustc ' + pinned), 'Rust does not match pinned sources')
        run(['rustup', 'target', 'add', *TARGETS], env=environment)
        chat, pair = prepare_pair(originals['gchat'], originals['gcoms'], destination / 'paired', TARGETS[0], environment)
        report['dependency_inputs'] = pair
        report['publisher'] = publisher_policy(chat / 'release/publication.json', pin)
        report['publication'] = reference(chat / 'release/publication.json')
        native = chat / 'apps/client/src-tauri'
        client = chat / 'apps/client'
        run(['python3', chat / 'scripts/collect-notices.py'], cwd=chat, env=environment)
        config = destination / 'ios-config.json'
        write_json(config, {'identifier': BUNDLE, 'bundle': {'iOS': {
            'developmentTeam': TEAM, 'minimumSystemVersion': '15.0', 'bundleVersion': version}}})
        # GChat uses encryption; never silently declare an exemption for App Store review.
        (native / 'Info.ios.plist').write_bytes(plistlib.dumps({'ITSAppUsesNonExemptEncryption': True}))
        # npm supplies the runner context used by Tauri's generated Xcode Rust
        # callback. Direct `node tauri.js` produces an unusable `node tauri`
        # callback relative to gen/apple instead of this package's script.
        run(['npm', 'run', 'tauri', '--', 'ios', 'init', '--ci', '--skip-targets-install', '--config', config],
            cwd=client, env=environment)
        generated = native / 'gen/apple'
        entitlement_path = configure_project(generated)
        project = generated_project(generated)
        with signer(destination, profile, pin, profile_bytes) as (keychain, identity):
            signing = dict(environment, IOS_MOBILE_PROVISION=base64.b64encode(profile_bytes).decode())
            exports = destination / 'ExportOptions-app-store.plist'
            export_options = {'method': 'app-store-connect', 'signingStyle': 'manual',
                                   'teamID': TEAM, 'signingCertificate': identity,
                                   'provisioningProfiles': {BUNDLE: profile['uuid']}}
            exports.write_bytes(plistlib.dumps(export_options))
            report['export_options'] = reference(exports)
            xcconfig = destination / 'signing.xcconfig'
            xcconfig.write_text('CODE_SIGN_STYLE = Manual\nDEVELOPMENT_TEAM = ' + TEAM + '\n'
                'CODE_SIGN_IDENTITY[sdk=iphoneos*] = ' + identity + '\n'
                'PROVISIONING_PROFILE_SPECIFIER[sdk=iphoneos*] = ' + profile['uuid'] + '\n'
                'CODE_SIGN_ENTITLEMENTS = ' + str(entitlement_path) + '\n'
                'OTHER_CODE_SIGN_FLAGS = --keychain "' + str(keychain) + '"\n')
            signing['XCODE_XCCONFIG_FILE'] = str(xcconfig)
            signing = xcode_environment(destination / 'device-xcode', signing, xcconfig, export_options=exports)
            report['device_xcode_wrapper'] = reference(destination / 'device-xcode/xcodebuild')
            report['signing_settings'] = reference(xcconfig)
            # Check the actual generated project and effective SDK/signing
            # settings before either expensive application compilation.
            settings = json.loads(output(['xcodebuild', '-showBuildSettings', '-json', '-project', project,
                '-scheme', project.stem + '_iOS', '-configuration', 'release', '-sdk', 'iphoneos'],
                env={'HOME': os.environ['HOME'], 'PATH': signing['PATH']}, timeout=120))
            write_json(destination / 'device-build-settings.json', settings)
            verify_device_settings(settings, profile, identity)
            report['device_build_settings'] = reference(destination / 'device-build-settings.json')
            report['feature_graphs'] = {}
            for triple in TARGETS:
                metadata = json.loads(output(['cargo', 'metadata', '--locked', '--manifest-path', native / 'Cargo.toml',
                                              '--filter-platform', triple, '--format-version=1'], cwd=chat, env=environment))
                verify_resolved_protocol(metadata, chat.parent / 'gcoms')
                tree = output(['cargo', 'tree', '--locked', '--manifest-path', native / 'Cargo.toml', '--target', triple,
                               '--edges', 'normal', '--prefix', 'none', '--format', '{p}|{f}'], cwd=chat, env=environment)
                (destination / ('features-' + triple + '.txt')).write_text(tree + '\n')
                report['feature_graphs'][triple] = feature_graph(tree)
            run(['npm', 'run', 'tauri', '--', 'ios', 'build', '--ci', '--target', 'aarch64-sim', '--no-sign', '--config', config],
                cwd=client, env=environment, timeout=5400)
            simulator_apps = list((generated / 'build').glob('**/*.app'))
            simulator_apps = [app for app in simulator_apps if '.xcarchive' not in str(app)]
            require(len(simulator_apps) == 1, 'expected one simulator app output before the device build')
            simulator_app = simulator_apps[0]
            info = plistlib.loads((simulator_app / 'Info.plist').read_bytes())
            require(info.get('CFBundleIdentifier') == BUNDLE, 'simulator application identifier mismatch')
            report['simulator_signing'] = sign_simulator(simulator_app, destination / 'simulator-signing')
            report['simulator_executable'] = reference(simulator_app / info['CFBundleExecutable'])
            simulator_archive = destination / 'simulator-app.zip'
            run(['ditto', '-c', '-k', '--keepParent', simulator_app, simulator_archive])
            report['simulator_archive'] = reference(simulator_archive)
            run(['npm', 'run', 'tauri', '--', 'ios', 'build', '--ci', '--target', 'aarch64', '--export-method', 'app-store-connect',
                 '--config', config], cwd=client, env=signing, timeout=5400)
            candidates = list((generated / 'build').glob('**/*.ipa'))
            require(len(candidates) == 1, 'expected one signed IPA output')
            artifact = destination / ('GChat-' + version + '.ipa')
            shutil.copyfile(candidates[0], artifact)
            report['application'] = verify_ipa(artifact, destination / 'ipa-verification', pin, version)
        report['signing_cleanup'] = reference(destination / 'signing-cleanup.json')
        # Retain both compiled artifacts and remove the signer before exercising
        # CoreSimulator. A runner installation failure must not erase a verified
        # device artifact, but still prevents upload and a passing build verdict.
        report['simulator'] = simulator_smoke(simulator_app, destination / 'simulator-smoke')
        verify_derived_inputs(chat, pair)
        report['passed'] = True
    except Exception as error:
        # CalledProcessError from build commands contains no private key/password args.
        report['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        report['sources_unchanged'] = all(source_identity(root) == before[name] for name, root in originals.items())
        report['passed'] = report['passed'] and report['sources_unchanged']
        write_json(destination / 'build.json', report)
    require(report['passed'], 'iOS build source changed')


def validate_upload_build(report):
    require(report.get('scope') in ('ios_exact_pair_simulator_and_signed_ipa',
                                   'ios_retained_pair_simulator_and_signed_ipa')
            and report.get('passed') is True and report.get('sources_unchanged') is True,
            'upload requires a passed unchanged iOS build or retained-artifact verification')
    if report['scope'] == 'ios_retained_pair_simulator_and_signed_ipa':
        require(report.get('application_recompiled') is False and report.get('device_resigned') is False
                and report.get('original_build_verdict_unchanged') is True,
                'retained verification must preserve original device artifact and verdict')
        original = json.loads(verify_reference(report['original_build']).read_text())
        archive = verify_reference(report['original_archive'])
        require(digest(archive) == report['inputs']['artifact_sha256'], 'original archive binding differs')
        require(original.get('scope') == 'ios_exact_pair_simulator_and_signed_ipa'
                and original.get('sources_unchanged') is True
                and original.get('sources') == report.get('sources')
                and original.get('passed') is report.get('original_build_passed')
                and original.get('build_number') == report.get('build_number'),
                'original build source, identity or verdict differs')
        for key in ('sha256', 'size'):
            require(original['application']['ipa'][key] == report['application']['ipa'][key],
                    'retained IPA differs from the original device artifact')
            require(original['signing_cleanup'][key] == report['signing_cleanup'][key],
                    'retained original signing cleanup differs')
        spec = importlib.util.spec_from_file_location('ios_retained_verify', Path(__file__).with_name('ios-verify-retained.py'))
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        verifier.validate_linked_upload(report, original)


def upload(args):
    destination = args.output.resolve()
    build_path = destination / 'build.json'
    build_report = json.loads(build_path.read_text())
    validate_upload_build(build_report)
    require(build_report.get('bundle') == BUNDLE and build_report.get('team') == TEAM,
            'upload build identity mismatch')
    cleanup = json.loads(verify_reference(build_report['signing_cleanup']).read_text())
    smoke = json.loads(verify_reference(build_report['simulator']).read_text())
    require(cleanup.get('passed') is True and smoke.get('passed') is True and smoke.get('cleanup_complete') is True,
            'upload requires completed simulator and signing cleanup')
    ipa = verify_reference(build_report['application']['ipa'])
    pin = signing_pin()
    require(publisher_policy(verify_reference(build_report['publication']), pin) == build_report.get('publisher'),
            'upload publisher binding changed')
    require(build_report['application']['profile']['certificate_sha256'] == pin, 'upload signer pin mismatch')
    key_id = os.environ.get('APP_STORE_CONNECT_KEY_ID', '')
    issuer = os.environ.get('APP_STORE_CONNECT_ISSUER_ID', '')
    require(re.fullmatch('[A-Z0-9]{10}', key_id) and re.fullmatch('[0-9a-fA-F-]{36}', issuer),
            'missing App Store Connect key/issuer IDs')
    report = {'schema': 1, 'scope': 'app_store_connect_testflight_upload', 'passed': False,
              'build': reference(build_path), 'ipa': reference(ipa), 'app_store_id': APP_STORE_ID,
              'public_app_store_submission': False, 'apple_processing_qualified': False,
              'export_compliance_review': 'required; no encryption exemption asserted'}
    try:
        with tempfile.TemporaryDirectory(prefix='gchat-ios-upload-') as temporary:
            private = Path(temporary) / 'private_keys'
            private.mkdir(mode=0o700)
            key = private / ('AuthKey_' + key_id + '.p8')
            key.write_text(os.environ['APP_STORE_CONNECT_PRIVATE_KEY'])
            key.chmod(0o600)
            # altool searches cwd/private_keys. Do not change HOME or install credentials globally.
            command = ['xcrun', 'altool', '--upload-app', '--type', 'ios', '--file', ipa,
                       '--apiKey', key_id, '--apiIssuer', issuer, '--output-format', 'json']
            with (destination / 'upload.log').open('wb') as log:
                result = subprocess.run([str(x) for x in command], cwd=temporary, stdout=log,
                                        stderr=subprocess.STDOUT, timeout=1200)
            report['exit_code'] = result.returncode
            report['log'] = reference(destination / 'upload.log')
            require(result.returncode == 0, 'App Store Connect did not accept the IPA upload')
            report['passed'] = True
    finally:
        write_json(destination / 'upload.json', report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    verify = commands.add_parser('verify-checkouts')
    for name in ('gchat', 'gcoms'):
        verify.add_argument('--' + name, type=Path, required=True)
        verify.add_argument('--' + name + '-commit', required=True)
        verify.add_argument('--' + name + '-ref', required=True)
    compile_command = commands.add_parser('build')
    for name in ('gchat', 'gcoms', 'output'):
        compile_command.add_argument('--' + name, type=Path, required=True)
    compile_command.add_argument('--build-number', required=True)
    publish = commands.add_parser('upload')
    publish.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    {'verify-checkouts': verify_checkouts, 'build': build, 'upload': upload}[args.command](args)


if __name__ == '__main__':
    main()
