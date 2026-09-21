#!/usr/bin/env python3
"""Build exact-pair Android APKs, pin their signer, and smoke-test an emulator.

Only generated, retained build inputs are changed. Never publishes or dispatches.
A startup/profile/lifecycle smoke does not qualify remote messaging or live push.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import tomllib
import xml.etree.ElementTree as ET
import zipfile

from paired_sources import prepare_pair, verify_resolved_protocol
from release_evidence import digest, source_identity

PACKAGE = 'boo.gchat.app'
NDK = '28.2.13676358'
BUILD_TOOLS = '36.0.0'
TARGETS = {'arm64-v8a': ('aarch64', 'aarch64-linux-android'),
           'x86_64': ('x86_64', 'x86_64-linux-android')}
SPEC = importlib.util.spec_from_file_location('android_source_policy', Path(__file__).with_name('macos-build.py'))
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
            'retained artifact or receipt changed: ' + path.name)
    return path


def verify_copy(path, item):
    require(path.is_file() and digest(path) == item['sha256'] and path.stat().st_size == item['size'],
            'retained artifact or receipt changed: ' + path.name)
    return path


def run(command, cwd=None, env=None, timeout=3600):
    subprocess.run([str(x) for x in command], cwd=cwd, env=env, check=True, timeout=timeout)


def output(command, **kwargs):
    return subprocess.check_output([str(x) for x in command], text=True, **kwargs).strip()


def sdk(require_ndk=True):
    root = Path(os.environ.get('ANDROID_HOME', os.environ.get('ANDROID_SDK_ROOT', ''))).resolve()
    require((root / 'platform-tools/adb').is_file(), 'set ANDROID_HOME to an installed Android SDK')
    if require_ndk:
        require((root / f'ndk/{NDK}/source.properties').is_file(), f'install exact NDK {NDK}')
    require((root / f'build-tools/{BUILD_TOOLS}/apksigner').is_file(), f'install build-tools {BUILD_TOOLS}')
    return root


def tauri_command(*arguments):
    # Tauri persists its launcher in Gradle's Rust callback. The package script
    # is resolvable from both apps/client and src-tauri; a direct `node tauri.js`
    # launch gets rewritten to `node tauri` and fails after native compilation.
    npm = 'npm.cmd' if os.name == 'nt' else 'npm'
    return [npm, 'run', 'tauri', '--', *arguments]


def verify_checkouts(args):
    chat, coms = args.gchat.resolve(), args.gcoms.resolve()
    chat_ref, coms_ref = policy.release_ref(args.gchat_ref), policy.release_ref(args.gcoms_ref)
    env = os.environ
    require(env.get('GITHUB_SHA') == args.gchat_commit and env.get('GITHUB_WORKFLOW_SHA') == args.gchat_commit
            and env.get('GITHUB_REF') == chat_ref
            and env.get('GITHUB_WORKFLOW_REF') == f'{policy.REPO}/.github/workflows/android-release.yml@{chat_ref}',
            'workflow/source/ref identity differs from the selected protected GChat source')
    for root, commit, ref in ((chat, args.gchat_commit, chat_ref), (coms, args.gcoms_commit, coms_ref)):
        policy.source_commit(commit)
        require(source_identity(root)['commit'] == commit, 'source checkout does not match the frozen commit')
        local = ref.replace('refs/heads/', 'refs/remotes/origin/', 1) if ref.startswith('refs/heads/') else ref
        tip = output(['git', 'rev-parse', local + '^{commit}'], cwd=root)
        if root == chat or ref.startswith('refs/tags/'):
            require(tip == commit, 'selected protected ref moved from the frozen source')
        else:
            run(['git', 'merge-base', '--is-ancestor', commit, tip], cwd=root)


def feature_graph(text):
    """Read cargo tree's normal-edge package/features format, without dev unification."""
    found = {}
    for line in text.splitlines():
        if '|' not in line:
            continue
        package, features = line.split('|', 1)
        name = package.split()[0]
        if name == 'gcoms' or name.startswith('gcoms-'):
            found.setdefault(name, set()).update(x.strip() for x in features.replace(' (*)', '').split(',') if x.strip())
    require('network-client' in found.get('gcoms', set()), 'Android application is missing network-client')
    require('gcoms-node' in found and 'gcoms-runtime' in found, 'Android graph omits the actual runtime')
    require('relay-host' not in found['gcoms-node'], 'Android application enables relay-host')
    require(not ({'embedded', 'launch'} & found['gcoms']), 'Android application includes a desktop host backend')
    return {name: sorted(features) for name, features in sorted(found.items())}


def verify_elf_alignment(data):
    require(data[:4] == b'\x7fELF' and data[4] == 2 and data[5] == 1, 'expected little-endian ELF64 library')
    offset = struct.unpack_from('<Q', data, 32)[0]
    entry_size, count = struct.unpack_from('<HH', data, 54)
    require(entry_size >= 56 and count > 0 and offset + entry_size * count <= len(data), 'invalid ELF program headers')
    loads = []
    for index in range(count):
        pos = offset + index * entry_size
        if struct.unpack_from('<I', data, pos)[0] == 1:
            alignment = struct.unpack_from('<Q', data, pos + 48)[0]
            require(alignment >= 16384 and alignment & (alignment - 1) == 0, 'native library lacks 16 KiB segment alignment')
            loads.append(alignment)
    require(loads, 'native library has no load segments')
    return loads


def inspect_apk(path, tools):
    badging = output([tools / 'aapt', 'dump', 'badging', path])
    require(re.search(r"^package: name='boo\.gchat\.app'", badging, re.M), 'APK package identity mismatch')
    require("sdkVersion:'26'" in badging, 'APK minimum SDK differs from API 26')
    launch = re.search(r"^launchable-activity: name='([^']+)'", badging, re.M)
    require(launch is not None, 'APK has no launchable activity')
    native = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.startswith('lib/') and name.endswith('.so'):
                data = archive.read(name)
                native.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest(),
                               'size': len(data), 'load_alignment': verify_elf_alignment(data)})
    abis = {item['path'].split('/')[1] for item in native}
    require(len(abis) == 1 and abis <= TARGETS.keys(), 'expected one supported ABI per APK')
    abi = next(iter(abis))
    require(any(x['path'] == f'lib/{abi}/libgchat_native.so' for x in native), 'APK omits actual GChat native application')
    run([tools / 'zipalign', '-c', '-P', '16', '4', path])
    return {'abi': abi, 'activity': launch.group(1), 'native_libraries': native, 'min_sdk': 26}


def build(args):
    original = {'gchat': args.gchat.resolve(), 'gcoms': args.gcoms.resolve()}
    before = {name: source_identity(root) for name, root in original.items()}
    dest = args.output.resolve()
    dest.mkdir(parents=True, exist_ok=False)
    report = {'schema': 1, 'scope': 'android_exact_pair_release_build', 'passed': False, 'sources': before,
              'package': PACKAGE, 'ndk': NDK, 'physical_device_qualified': False, 'push_qualified': False,
              'harness': reference(Path(__file__))}
    try:
        android = sdk()
        env = dict(os.environ, NDK_HOME=str(android / 'ndk' / NDK), ANDROID_NDK_HOME=str(android / 'ndk' / NDK),
                   CARGO_INCREMENTAL='0', CARGO_PROFILE_DEV_DEBUG='0', CARGO_PROFILE_RELEASE_DEBUG='0', CI='true')
        java = subprocess.run(['java', '-version'], text=True, capture_output=True, check=True)
        require(re.search(r'version "17[.\"]', java.stderr + java.stdout), 'Android release build requires Java 17')
        report['java'] = (java.stderr + java.stdout).strip()
        report['rustc'] = output(['rustc', '-vV'])
        report['node'] = output(['node', '--version'])
        report['npm'] = output(['npm', '--version'])
        require(report['node'] == 'v22.23.2' and report['npm'] == '11.6.2', 'use pinned Node 22.23.2 and npm 11.6.2')
        for root in original.values():
            toolchain = tomllib.loads((root / 'rust-toolchain.toml').read_text())['toolchain']['channel']
            require(report['rustc'].splitlines()[0].startswith('rustc ' + toolchain), 'Rust compiler does not match pinned source')
        for _, triple in TARGETS.values():
            run(['rustup', 'target', 'add', triple], env=env)
        chat, pair = prepare_pair(original['gchat'], original['gcoms'], dest / 'paired', 'aarch64-linux-android', env)
        report['dependency_inputs'] = pair
        publication = json.loads((chat / 'release/publication.json').read_text())
        publisher = publication.get('publisher_identities', {}).get('android', {})
        require(publisher.get('name') == 'Gh0st' and
                re.fullmatch('[0-9a-fA-F]{64}', publisher.get('certificate_sha256', '')),
                'frozen publication policy must name the Gh0st Android certificate')
        report['publisher'] = publisher
        report['publication'] = reference(chat / 'release/publication.json')
        coms = chat.parent / 'gcoms'
        native = chat / 'apps/client/src-tauri'
        manifest = native / 'Cargo.toml'
        config = dest / 'android-config.json'
        write_json(config, {'identifier': PACKAGE, 'bundle': {'android': {'minSdkVersion': 26}}})
        run(tauri_command('android', 'init', '--ci', '--skip-targets-install', '--config', config), cwd=chat / 'apps/client', env=env)
        generated = native / 'gen/android'
        gradle = generated / 'app/build.gradle.kts'
        with gradle.open('a') as stream:
            stream.write('\n// Exact release toolchain chosen by android-build.py.\nandroid { ndkVersion = "' + NDK + '" }\n')
        # Firebase client configuration is public app metadata, never a service-account key.
        firebase = env.pop('GOOGLE_SERVICES_JSON_BASE64', '')
        if firebase:
            decoded = base64.b64decode(firebase, validate=True)
            value = json.loads(decoded)
            require('private_key' not in value and value.get('type') != 'service_account', 'server credential is forbidden in the APK')
            require(any(c.get('client_info', {}).get('android_client_info', {}).get('package_name') == PACKAGE
                        for c in value.get('client', [])), 'Firebase client config does not include boo.gchat.app')
            client_config = generated / 'app/google-services.json'
            client_config.write_bytes(decoded)
            client_config.chmod(0o600)
            report['firebase_client_config_sha256'] = digest(client_config)
        report['feature_graphs'] = {}
        metadata_paths = []
        for abi, (_, triple) in TARGETS.items():
            metadata = json.loads(output(['cargo', 'metadata', '--manifest-path', manifest, '--filter-platform', triple,
                                          '--format-version=1'], cwd=chat, env=env))
            verify_resolved_protocol(metadata, coms)
            metadata_path = dest / f'metadata-{abi}.json'
            write_json(metadata_path, metadata)
            metadata_paths.append(metadata_path)
            tree = output(['cargo', 'tree', '--locked', '--manifest-path', manifest, '--target', triple,
                           '--edges', 'normal', '--prefix', 'none', '--format', '{p}|{f}'], cwd=chat, env=env)
            (dest / f'features-{abi}.txt').write_text(tree + '\n')
            report['feature_graphs'][abi] = feature_graph(tree)
        notices = ['python3', chat / 'scripts/collect-notices.py']
        for metadata_path in metadata_paths:
            notices.extend(['--rust-metadata', metadata_path])
        run(notices, cwd=chat, env=env)
        run(tauri_command('android', 'build', '--ci', '--apk', '--split-per-abi', '--target', 'aarch64', 'x86_64',
                          '--config', config), cwd=chat / 'apps/client', env=env)
        candidates = sorted(generated.glob('app/build/outputs/apk/**/*.apk'))
        artifacts = dest / 'unsigned'
        artifacts.mkdir()
        entries = []
        for apk in candidates:
            if 'release' not in str(apk.relative_to(generated)).lower():
                continue
            inspected = inspect_apk(apk, android / 'build-tools' / BUILD_TOOLS)
            target = artifacts / f'gchat-{inspected["abi"]}.apk'
            require(not target.exists(), 'multiple release APKs claim the same ABI')
            shutil.copyfile(apk, target)
            entries.append({**reference(target), **inspected})
        require({x['abi'] for x in entries} == set(TARGETS), 'release build did not produce both ARM64 and x86_64 APKs')
        report['artifacts'] = entries
        report['generated_gradle_sha256'] = digest(gradle)
        report['passed'] = True
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        try:
            report['sources_unchanged'] = all(source_identity(root) == before[name] for name, root in original.items())
        except Exception:
            report['sources_unchanged'] = False
        report['passed'] = report['passed'] and report['sources_unchanged']
        write_json(dest / 'build.json', report)


def signing_pin():
    pin = os.environ.get('ANDROID_SIGNING_CERT_SHA256', '').replace(':', '').lower()
    require(re.fullmatch('[0-9a-f]{64}', pin), 'set the pinned ANDROID_SIGNING_CERT_SHA256')
    return pin


def verify_signature(apk, tools, pin):
    result = output([tools / 'apksigner', 'verify', '--verbose', '--print-certs', apk])
    found = re.findall(r'^Signer #[0-9]+ certificate SHA-256 digest: ([0-9a-fA-F]+)$', result, re.M)
    require(len(found) == 1 and found[0].lower() == pin, 'APK signature does not match the single pinned publisher certificate')
    require('Verified using v2 scheme (APK Signature Scheme v2): true' in result,
            'APK does not have a valid v2 signature')
    return pin


def sign(args):
    root = args.output.resolve()
    build_path = root / 'build.json'
    build = json.loads(build_path.read_text())
    require(build.get('passed') and build.get('sources_unchanged'), 'only a completed unchanged exact-pair build may be signed')
    tools = sdk() / 'build-tools' / BUILD_TOOLS
    pin = signing_pin()
    publication = json.loads(verify_reference(build['publication']).read_text())
    publisher = publication.get('publisher_identities', {}).get('android', {})
    require(publisher == build.get('publisher') and publisher.get('certificate_sha256', '').lower() == pin,
            'signing pin differs from frozen source publication policy')
    for key in ('ANDROID_KEYSTORE_BASE64', 'ANDROID_KEYSTORE_PASSWORD', 'ANDROID_KEY_PASSWORD', 'ANDROID_KEY_ALIAS'):
        require(bool(os.environ.get(key)), 'missing signing input: ' + key)
    target = root / 'signed'
    target.mkdir(exist_ok=False)
    report = {'schema': 1, 'scope': 'android_pinned_apk_signing', 'passed': False,
              'build': reference(build_path), 'certificate_sha256': pin, 'sources': build['sources'], 'artifacts': []}
    # Private key material is outside the retained artifacts and removed on every exit.
    with tempfile.TemporaryDirectory(prefix='gchat-android-sign-') as private:
        key = Path(private) / 'publisher.jks'
        try:
            key.write_bytes(base64.b64decode(os.environ['ANDROID_KEYSTORE_BASE64'], validate=True))
            key.chmod(0o600)
            for item in build['artifacts']:
                apk = verify_reference(item)
                result = target / apk.name
                run([tools / 'apksigner', 'sign', '--ks', key, '--ks-key-alias', os.environ['ANDROID_KEY_ALIAS'],
                     '--ks-pass', 'env:ANDROID_KEYSTORE_PASSWORD', '--key-pass', 'env:ANDROID_KEY_PASSWORD',
                     '--out', result, apk])
                verify_signature(result, tools, pin)
                inspected = inspect_apk(result, tools)
                require(inspected['native_libraries'] == item['native_libraries'], 'signing changed native library contents')
                report['artifacts'].append({**reference(result), **inspected})
            report['passed'] = True
        finally:
            key.unlink(missing_ok=True)
            report['private_keystore_removed'] = not key.exists()
            write_json(root / 'signing.json', report)


def listener_rows(text, uid):
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) > 9 and parts[0].rstrip(':').isdigit() and parts[7] == str(uid) and parts[3] == '0A':
            rows.append({'local_address': parts[1], 'inode': parts[9]})
    return rows


def cleanup_emulator(shell, adb, installed, uid, firewall):
    errors = []
    if installed:
        for command in firewall:
            try:
                shell(command, '-D', 'OUTPUT', '-m', 'owner', '--uid-owner', str(uid), '!', '-o', 'lo', '-j', 'REJECT')
            except Exception:
                errors.append('failed to remove owned emulator firewall rule')
        try:
            shell('am', 'force-stop', PACKAGE)
            run([*adb, 'uninstall', PACKAGE], timeout=60)
            require(not shell('pm', 'path', PACKAGE, absent_ok=True), 'app package remains installed')
        except Exception:
            errors.append('failed to uninstall owned emulator app')
    try:
        shell('rm', '-f', '/sdcard/gchat-fixture-ui.xml')
    except Exception:
        errors.append('failed to remove owned UI dump')
    return {'passed': not errors, 'errors': errors}


def smoke(args):
    root = args.output.resolve()
    signed_path = root / 'signing.json'
    signed = json.loads(signed_path.read_text())
    require(signed.get('passed') and signed.get('private_keystore_removed'), 'signing/cleanup receipt did not pass')
    build_path = verify_copy(root / 'build.json', signed['build'])
    build = json.loads(build_path.read_text())
    require(build.get('passed') and build.get('sources_unchanged') and signed['sources'] == build['sources'],
            'signing receipt differs from its build/source binding')
    artifact = next(x for x in signed['artifacts'] if x['abi'] == 'x86_64')
    apk = verify_copy(root / 'signed/gchat-x86_64.apk', artifact)
    android = sdk(require_ndk=False)
    verify_signature(apk, android / 'build-tools' / BUILD_TOOLS, signed['certificate_sha256'])
    adb = [android / 'platform-tools/adb', '-s', args.serial]
    require(re.fullmatch(r'emulator-[0-9]+', args.serial), 'smoke is restricted to an explicit emulator serial')
    def shell(*cmd, absent_ok=False):
        result = subprocess.run([str(x) for x in [*adb, 'shell', *cmd]], text=True,
                                capture_output=True, timeout=30)
        if absent_ok and result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip():
            return ''
        result.check_returncode()
        return result.stdout.strip()
    require(shell('getprop', 'ro.kernel.qemu') == '1', 'physical devices are outside this automated destructive fixture')
    require(not shell('pm', 'path', PACKAGE, absent_ok=True), 'emulator already contains GChat; use a fresh AVD')
    dest = root / 'emulator-smoke'
    dest.mkdir(exist_ok=False)
    report = {'schema': 1, 'scope': 'android_x86_64_installed_profile_lifecycle_no_listener', 'passed': False,
              'artifact': artifact, 'tested_artifact': reference(apk), 'signing': reference(signed_path), 'sources': signed['sources'],
              'controller': reference(Path(__file__)),
              'physical_device_qualified': False, 'network_delivery_qualified': False, 'push_qualified': False,
              'observations': []}
    installed = False
    uid = None
    firewall = []
    try:
        run([*adb, 'root'], timeout=30)
        run([*adb, 'wait-for-device'], timeout=60)
        report['api'] = int(shell('getprop', 'ro.build.version.sdk'))
        report['abi'] = shell('getprop', 'ro.product.cpu.abi')
        require(report['api'] >= 26 and report['abi'] == 'x86_64', 'unexpected emulator API/ABI')
        run([*adb, 'install', '--no-streaming', apk], timeout=120)
        installed = True
        package = shell('dumpsys', 'package', PACKAGE)
        match = re.search(r'\buserId=([0-9]+)', package)
        require(match is not None, 'could not identify installed app UID')
        uid = int(match.group(1))
        # This fresh disposable emulator is rooted. Block only this app UID's
        # non-loopback traffic; adb and host networking are untouched.
        for command in ('iptables', 'ip6tables'):
            shell(command, '-I', 'OUTPUT', '-m', 'owner', '--uid-owner', str(uid), '!', '-o', 'lo', '-j', 'REJECT')
            firewall.append(command)
        def launch():
            result = shell('am', 'start', '-W', '-n', PACKAGE + '/' + artifact['activity'])
            require('Status: ok' in result, 'Android did not start GChat successfully')
        def nodes():
            shell('uiautomator', 'dump', '/sdcard/gchat-fixture-ui.xml')
            return ET.fromstring(shell('cat', '/sdcard/gchat-fixture-ui.xml')).iter('node')
        def wait_node(predicate, timeout=60):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                for node in nodes():
                    if predicate(node):
                        return node
                time.sleep(1)
            raise ValueError('expected app UI state was not observed before the fixture deadline')
        def tap(node):
            points = [int(x) for x in re.findall('[0-9]+', node.attrib['bounds'])]
            require(len(points) == 4, 'UI node lacks tappable bounds')
            shell('input', 'tap', str((points[0] + points[2]) // 2), str((points[1] + points[3]) // 2))
        def text(value):
            return lambda node: node.attrib.get('text') == value or node.attrib.get('content-desc') == value
        def no_listener(phase):
            tcp = shell('cat', '/proc/net/tcp', '/proc/net/tcp6')
            listeners = listener_rows(tcp, uid)
            report['observations'].append({'phase': phase, 'app_uid': uid, 'tcp_listeners': listeners})
            require(not listeners, 'outbound mobile app opened a TCP listening socket')
        launch()
        wait_node(text('Create identity'))
        no_listener('fresh_locked')
        password = wait_node(lambda n: n.attrib.get('password') == 'true')
        tap(password)
        shell('input', 'text', 'gchat-emulator-fixture-only-42')
        shell('input', 'keyevent', '111')  # Escape closes the software keyboard.
        tap(wait_node(text('Create identity')))
        wait_node(text('Connect to GChat'), timeout=120)
        no_listener('created_unlocked_without_network_invitation')
        shell('input', 'keyevent', '3')
        time.sleep(3)
        no_listener('background')
        launch()
        wait_node(text('Reconnect'))
        password = wait_node(lambda n: n.attrib.get('password') == 'true')
        tap(password)
        shell('input', 'text', 'gchat-emulator-fixture-only-42')
        shell('input', 'keyevent', '111')
        tap(wait_node(text('Reconnect')))
        wait_node(text('Connect to GChat'), timeout=120)
        no_listener('foreground_reopened')
        shell('am', 'force-stop', PACKAGE)
        require(not shell('pidof', PACKAGE, absent_ok=True), 'app processes survived force-stop')
        launch()
        wait_node(text('Reconnect'))
        no_listener('process_restart_retained_profile_locked')
        report['profile_lifecycle_passed'] = True
        if getattr(args, 'probe_picker', False):
            password = wait_node(lambda n: n.attrib.get('password') == 'true')
            tap(password)
            shell('input', 'text', 'gchat-emulator-fixture-only-42')
            shell('input', 'keyevent', '111')
            tap(wait_node(text('Reconnect')))
            wait_node(text('Connect to GChat'), timeout=120)
            tap(wait_node(text('Or choose an invitation file')))
            picker = wait_node(lambda n: n.attrib.get('package', '').endswith('.documentsui'), timeout=30)
            report['picker'] = {'opened': True, 'package': picker.attrib['package'], 'selected_file': False}
            no_listener('invitation_picker_open')
            shell('input', 'keyevent', '4')
            returned = wait_node(lambda n: text('Reconnect')(n) or text('Connect to GChat')(n), timeout=30)
            report['picker']['returned_locked'] = text('Reconnect')(returned)
            report['picker']['passed'] = not report['picker']['returned_locked']
            no_listener('invitation_picker_cancel_return')
            require(report['picker']['passed'], 'invitation picker cancellation locked the profile')
        report['passed'] = True
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        if installed and uid is not None:
            try:
                (dest / 'app-logcat.txt').write_text(shell('logcat', '-d', '-v', 'threadtime', '--uid=' + str(uid)))
                (dest / 'final-ui.xml').write_text(shell('cat', '/sdcard/gchat-fixture-ui.xml'))
            except Exception as error:
                report['diagnostic_error'] = type(error).__name__
        report['cleanup'] = cleanup_emulator(shell, adb, installed, uid, firewall)
        report['inputs_unchanged'] = digest(apk) == artifact['sha256']
        report['passed'] = report['passed'] and report['cleanup']['passed'] and report['inputs_unchanged']
        write_json(dest / 'report.json', report)
        if not report['cleanup']['passed']:
            raise ValueError('Android fixture cleanup failed; see retained report')



def emulator_environment(root, inherited):
    environment = dict(inherited)
    user = root / 'android-user'
    avds = user / 'avd'
    avds.mkdir(parents=True, exist_ok=False)
    environment['ANDROID_USER_HOME'] = str(user)
    environment['ANDROID_EMULATOR_HOME'] = str(user)
    environment['ANDROID_AVD_HOME'] = str(avds)
    # Legacy SDK settings must not send avdmanager to a different directory.
    environment.pop('ANDROID_SDK_HOME', None)
    return environment, avds


def emulator(args):
    root = args.output.resolve()
    android = sdk(require_ndk=False)
    environment, avds = emulator_environment(root, os.environ)
    name = 'gchat-release-fixture'
    avd_path = avds / (name + '.avd')
    report = {'schema': 1, 'scope': 'android_disposable_emulator_driver', 'passed': False,
              'controller': reference(Path(__file__)), 'avd_home': str(avds), 'started': False}
    process = None
    adb = [android / 'platform-tools/adb', '-s', 'emulator-5554']
    try:
        with (root / 'avd-create.log').open('w') as log:
            subprocess.run([str(android / 'cmdline-tools/latest/bin/avdmanager'), 'create', 'avd', '--force',
                            '--name', name, '--path', str(avd_path), '--package',
                            'system-images;android-35;google_apis;x86_64'],
                           input='no\n', text=True, env=environment, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=120)
        require((avd_path / 'config.ini').is_file(), 'avdmanager did not create the requested AVD directory')
        require((avds / (name + '.ini')).is_file(), 'avdmanager did not register AVD in the explicit shared AVD home')
        with (root / 'emulator.log').open('w') as log:
            process = subprocess.Popen([str(android / 'emulator/emulator'), '-avd', name,
                                        '-port', '5554', '-no-window', '-no-audio', '-no-boot-anim',
                                        '-no-snapshot', '-wipe-data', '-gpu', 'swiftshader_indirect'],
                                       env=environment, stdout=log, stderr=log)
            report['started'] = True
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                require(process.poll() is None, 'emulator exited before startup')
                try:
                    result = subprocess.run([str(x) for x in [*adb, 'shell', 'getprop', 'sys.boot_completed']],
                                            capture_output=True, text=True, timeout=10)
                except subprocess.TimeoutExpired:
                    continue
                if result.returncode == 0 and result.stdout.strip() == '1':
                    break
                time.sleep(2)
            else:
                raise ValueError('emulator failed its bounded boot deadline')
            run([*adb, 'shell', 'input', 'keyevent', '82'], timeout=30)
            smoke(argparse.Namespace(output=root, serial='emulator-5554', probe_picker=getattr(args, 'probe_picker', False)))
            report['passed'] = True
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        if process is not None:
            if process.poll() is None:
                try:
                    subprocess.run([str(x) for x in [*adb, 'emu', 'kill']], check=False, timeout=30)
                    process.wait(timeout=30)
                except (OSError, subprocess.TimeoutExpired):
                    process.kill()
                    process.wait(timeout=10)
            report['process_stopped'] = process.poll() is not None
        else:
            report['process_stopped'] = True
        report['passed'] = report['passed'] and report['process_stopped']
        write_json(root / 'emulator-driver.json', report)


def verify_original_artifact(args, original, artifacts):
    require(original.get('id') == args.build_run and original.get('head_sha') == args.gchat_commit and
            original.get('event') == 'workflow_dispatch' and original.get('status') == 'completed' and
            original.get('head_repository', {}).get('full_name') == policy.REPO and
            original.get('path') == '.github/workflows/android-release.yml', 'original build run identity differs')
    policy.release_ref(original['head_branch'])
    matches = [x for x in artifacts if x['id'] == args.artifact_id]
    require(len(matches) == 1, 'artifact does not belong to the original Android run')
    item = matches[0]
    require(not item.get('expired') and item['name'] == f'android-{args.gchat_commit}-{args.gcoms_commit}' and
            item.get('digest') == 'sha256:' + args.artifact_sha256, 'original artifact name or digest differs')
    return item


def extract_artifact(archive, destination):
    destination.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.infolist()
        require(len(members) < 50000 and sum(x.file_size for x in members) < 750 * 1024 * 1024,
                'artifact archive exceeds extraction bounds')
        names = set()
        for member in members:
            path = Path(member.filename)
            require(not path.is_absolute() and '..' not in path.parts and '\\' not in member.filename and
                    ':' not in member.filename and (member.external_attr >> 16) & 0o170000 != 0o120000 and
                    member.filename not in names, 'unsafe artifact archive member')
            names.add(member.filename)
        bundle.extractall(destination)


def download_smoke(args):
    """Fetch one bound original artifact; preserve every original receipt byte."""
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    controller = Path(__file__).resolve().parents[1]
    identity = source_identity(controller)
    env = os.environ
    ref = policy.release_ref(env.get('GITHUB_REF', ''))
    require(env.get('GITHUB_SHA') == identity['commit'] == env.get('GITHUB_WORKFLOW_SHA') and
            env.get('GITHUB_WORKFLOW_REF') == f'{policy.REPO}/.github/workflows/android-smoke.yml@{ref}',
            'smoke controller must run from its own exact protected source')
    policy.source_commit(args.gchat_commit)
    policy.source_commit(args.gcoms_commit)
    require(re.fullmatch('[0-9a-f]{64}', args.artifact_sha256), 'exact artifact ZIP digest is required')
    def api(path):
        return json.loads(output(['gh', 'api', f'repos/{policy.REPO}/' + path]))
    original = api(f'actions/runs/{args.build_run}')
    artifacts = api(f'actions/runs/{args.build_run}/artifacts')['artifacts']
    item = verify_original_artifact(args, original, artifacts)
    archive = root / 'original-artifact.zip'
    with archive.open('wb') as stream:
        subprocess.run(['gh', 'api', f'repos/{policy.REPO}/actions/artifacts/{args.artifact_id}/zip'],
                       stdout=stream, check=True, timeout=300)
    require(digest(archive) == args.artifact_sha256, 'downloaded ZIP digest differs')
    original_root = root / 'original'
    extract_artifact(archive, original_root)
    # Original reports (including the failed driver log) remain untouched.
    # Copies retain original absolute paths inside JSON; hashes bind relocated bytes.
    for name in ('build.json', 'signing.json'):
        shutil.copy2(original_root / name, root / name)
    shutil.copytree(original_root / 'signed', root / 'signed')
    signing_path, build_path = root / 'signing.json', root / 'build.json'
    signing = json.loads(signing_path.read_text())
    build = json.loads(verify_copy(build_path, signing['build']).read_text())
    expected = {'gchat': args.gchat_commit, 'gcoms': args.gcoms_commit}
    require(build.get('passed') and build.get('sources_unchanged') and signing.get('passed') and
            signing.get('private_keystore_removed') and signing['sources'] == build['sources'] and
            {name: value['commit'] for name, value in build['sources'].items()} == expected,
            'original source/build/signature receipts do not match completed gates')
    pin = signing_pin()
    publisher = json.loads((controller / 'release/publication.json').read_text())['publisher_identities']['android']
    require(publisher['certificate_sha256'].lower() == signing['certificate_sha256'] == pin,
            'retained signer differs from the current pinned publisher')
    tools = sdk(require_ndk=False) / 'build-tools' / BUILD_TOOLS
    for artifact in signing['artifacts']:
        require(artifact['abi'] in TARGETS, 'unexpected signed ABI')
        apk = verify_copy(root / 'signed' / f'gchat-{artifact["abi"]}.apk', artifact)
        verify_signature(apk, tools, pin)
        actual = inspect_apk(apk, tools)
        require(all(actual[k] == artifact[k] for k in ('abi', 'activity', 'native_libraries', 'min_sdk')),
                'retained APK metadata differs from signed receipt')
    require({x['abi'] for x in signing['artifacts']} == set(TARGETS), 'retained artifact lacks both signed ABIs')
    write_json(root / 'reuse.json', {'schema': 1, 'passed': True, 'scope': 'original_signed_android_artifact_reuse',
                                   'original_run': original, 'artifact': item, 'archive': reference(archive),
                                   'controller': identity, 'harness': reference(Path(__file__)),
                                   'sources': build['sources'], 'build': reference(build_path),
                                   'signing': reference(signing_path)})


def self_test():
    # Pure guards can run without an SDK, build, emulator or publisher secrets.
    import unittest
    class Guards(unittest.TestCase):
        def test_feature_boundary(self):
            good = 'gcoms v0.1.0|files,network-client\ngcoms-node v0.1.0|client-persist\ngcoms-runtime v0.1.0|network-client'
            self.assertIn('gcoms-node', feature_graph(good))
            for bad in (good.replace('client-persist', 'client-persist,relay-host'), good.replace('files,', 'files,embedded,')):
                with self.assertRaises(ValueError): feature_graph(bad)
        def test_listener_scope(self):
            rows = ' 0: 0100007F:1234 00000000:0000 0A 0:0 0:0 0 10123 0 42\n'
            self.assertEqual(len(listener_rows(rows, 10123)), 1)
            self.assertEqual(listener_rows(rows, 10124), [])
            self.assertEqual(listener_rows(rows.replace(' 0A ', ' 01 '), 10123), [])
        def test_segment_alignment(self):
            elf = bytearray(120)
            elf[:6] = b'\x7fELF\x02\x01'
            struct.pack_into('<Q', elf, 32, 64)
            struct.pack_into('<HH', elf, 54, 56, 1)
            struct.pack_into('<I', elf, 64, 1)
            struct.pack_into('<Q', elf, 112, 16384)
            self.assertEqual(verify_elf_alignment(elf), [16384])
            struct.pack_into('<Q', elf, 112, 4096)
            with self.assertRaises(ValueError): verify_elf_alignment(elf)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Guards))
    return 0 if result.wasSuccessful() else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    verify = commands.add_parser('verify-checkouts')
    compile_app = commands.add_parser('build')
    for sub in (verify, compile_app):
        sub.add_argument('--gchat', type=Path, required=True)
        sub.add_argument('--gcoms', type=Path, required=True)
    for name in ('gchat-commit', 'gcoms-commit', 'gchat-ref', 'gcoms-ref'):
        verify.add_argument('--' + name, required=True)
    compile_app.add_argument('--output', type=Path, required=True)
    for name in ('sign', 'smoke', 'emulator'):
        sub = commands.add_parser(name)
        sub.add_argument('--output', type=Path, required=True)
        if name == 'smoke': sub.add_argument('--serial', required=True)
        if name in ('smoke', 'emulator'): sub.add_argument('--probe-picker', action='store_true')
    download = commands.add_parser('download-smoke')
    download.add_argument('--output', type=Path, required=True)
    download.add_argument('--build-run', type=int, required=True)
    download.add_argument('--artifact-id', type=int, required=True)
    for name in ('gchat-commit', 'gcoms-commit', 'artifact-sha256'):
        download.add_argument('--' + name, required=True)
    commands.add_parser('self-test')
    args = parser.parse_args()
    if args.command == 'verify-checkouts': verify_checkouts(args)
    elif args.command == 'build': build(args)
    elif args.command == 'sign': sign(args)
    elif args.command == 'smoke': smoke(args)
    elif args.command == 'emulator': emulator(args)
    elif args.command == 'download-smoke': download_smoke(args)
    else: return self_test()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
