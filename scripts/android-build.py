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
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import tomllib
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

from paired_sources import prepare_pair, verify_resolved_protocol
from release_evidence import digest, source_identity

PACKAGE = 'boo.gchat.app'
PICKER_FIXTURE_PATH = '/sdcard/Download/gchat-fixture.txt'
PICKER_FIXTURE_TEXT = 'GCNI1-local-emulator-fixture-not-a-real-invitation'
NDK = '28.2.13676358'
BUILD_TOOLS = '36.0.0'
BUNDLETOOL_VERSION = '1.18.2'
BUNDLETOOL_SHA256 = '378b5434cd1378bef6b2bc527b8c7f0ff2584b273830335bce54d6d0813c8584'
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


def bundletool(root):
    """Fetch only Google's pinned tool; never accept a different cached JAR."""
    target = root / ('bundletool-all-' + BUNDLETOOL_VERSION + '.jar')
    if not target.exists():
        url = 'https://github.com/google/bundletool/releases/download/' + BUNDLETOOL_VERSION + '/' + target.name
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read(64 * 1024 * 1024 + 1)
        require(len(data) <= 64 * 1024 * 1024 and hashlib.sha256(data).hexdigest() == BUNDLETOOL_SHA256,
                'downloaded bundletool hash differs from the pinned release')
        target.write_bytes(data)
    require(digest(target) == BUNDLETOOL_SHA256, 'cached bundletool hash differs from the pinned release')
    return target


def bundle_native_libraries(path):
    native = []
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), 'bundle contains duplicate ZIP entries')
        require('BundleConfig.pb' in names and 'base/manifest/AndroidManifest.xml' in names,
                'bundle lacks its configuration or base manifest')
        for name in names:
            if name.endswith('.so'):
                require(re.fullmatch(r'base/lib/(arm64-v8a|x86_64)/[^/]+\.so', name),
                        'unexpected native library in app bundle')
                data = archive.read(name)
                native.append({'path': name.removeprefix('base/'), 'sha256': hashlib.sha256(data).hexdigest(),
                               'size': len(data), 'load_alignment': verify_elf_alignment(data)})
    require({x['path'].split('/')[1] for x in native} == set(TARGETS),
            'bundle must contain both supported ABIs')
    for abi in TARGETS:
        require(any(x['path'] == f'lib/{abi}/libgchat_native.so' for x in native),
                'bundle omits the actual GChat native application')
    return sorted(native, key=lambda x: x['path'])


def inspect_bundle(path, jar, apk_entries):
    run(['java', '-jar', jar, 'validate', '--bundle=' + str(path)])
    manifest = ET.fromstring(output(['java', '-jar', jar, 'dump', 'manifest', '--bundle=' + str(path), '--module=base']))
    namespace = '{http://schemas.android.com/apk/res/android}'
    require(manifest.attrib.get('package') == PACKAGE, 'bundle package identity mismatch')
    uses_sdk = manifest.find('uses-sdk')
    require(uses_sdk is not None and uses_sdk.attrib.get(namespace + 'minSdkVersion') == '26',
            'bundle minimum SDK differs from API 26')
    version_code = manifest.attrib.get(namespace + 'versionCode', '')
    require(version_code.isdecimal() and 0 < int(version_code) <= 2100000000, 'invalid bundle version code')
    native = bundle_native_libraries(path)
    expected = sorted([lib for item in apk_entries for lib in item['native_libraries']], key=lambda x: x['path'])
    require(native == expected, 'app bundle native libraries differ from the exact APK builds')
    return {'package': PACKAGE, 'min_sdk': 26, 'version_code': int(version_code), 'native_libraries': native}


def firebase_resources(value):
    """Generate the Firebase resource subset documented by Google's plugin.

    Tauri generates Gradle projects at build time. The native plugin supplies
    its pinned Messaging dependency; these public values initialize that SDK.
    """
    require(isinstance(value, dict) and 'private_key' not in value and value.get('type') != 'service_account',
            'server credential is forbidden in the APK')
    project = value.get('project_info', {})
    require(project.get('project_id') == 'gchat-23115', 'unexpected Firebase project')
    matches = [x for x in value.get('client', []) if x.get('client_info', {}).get('android_client_info', {}).get('package_name') == PACKAGE]
    require(len(matches) == 1, 'Firebase config must identify exactly one boo.gchat.app client')
    client = matches[0]
    keys = client.get('api_key', [])
    require(len(keys) == 1 and isinstance(keys[0].get('current_key'), str), 'Firebase client API key is missing or ambiguous')
    values = {'google_app_id': client['client_info'].get('mobilesdk_app_id'),
              'gcm_defaultSenderId': project.get('project_number'), 'project_id': project['project_id'],
              'google_api_key': keys[0]['current_key']}
    require(isinstance(values['gcm_defaultSenderId'], str) and values['gcm_defaultSenderId'].isdecimal(),
            'Firebase project number is missing')
    require(isinstance(values['google_app_id'], str) and
            re.fullmatch(r'1:' + re.escape(values['gcm_defaultSenderId']) + r':android:[a-zA-Z0-9]+', values['google_app_id']),
            'Firebase app ID differs from its project')
    require(re.fullmatch(r'[A-Za-z0-9_-]{20,}', values['google_api_key']), 'invalid Firebase public client API key')
    resources = ET.Element('resources')
    for name, data in values.items():
        ET.SubElement(resources, 'string', {'name': name, 'translatable': 'false'}).text = data
    return ET.tostring(resources, encoding='utf-8', xml_declaration=True)


def derive_bundle_apks(root, bundle, jar, key, private, tools, pin, expected):
    """Build and verify the actual x86 emulator split set from the signed AAB."""
    device = {'supportedAbis': ['x86_64'], 'supportedLocales': ['en'], 'screenDensity': 420, 'sdkVersion': 35}
    spec = root / 'bundle-device.json'
    write_json(spec, device)
    passwords = []
    try:
        for name in ('ANDROID_KEYSTORE_PASSWORD', 'ANDROID_KEY_PASSWORD'):
            path = private / (name + '.txt')
            path.write_text(os.environ[name]); path.chmod(0o600)
            passwords.append(path)
        archive = root / 'signed/gchat-x86_64.apks'
        run(['java', '-jar', jar, 'build-apks', '--bundle=' + str(bundle), '--output=' + str(archive),
             '--device-spec=' + str(spec), '--ks=' + str(key), '--ks-key-alias=' + os.environ['ANDROID_KEY_ALIAS'],
             '--ks-pass=file:' + str(passwords[0]), '--key-pass=file:' + str(passwords[1])])
        extracted = root / 'signed/bundle-apks'
        extract_artifact(archive, extracted)
        entries, native, activity = [], [], None
        for apk in sorted(extracted.rglob('*.apk')):
            verify_signature(apk, tools, pin)
            badging = output([tools / 'aapt', 'dump', 'badging', apk])
            require(re.search(r"^package: name='boo\.gchat\.app'", badging, re.M), 'split APK package differs')
            launch = re.search(r"^launchable-activity: name='([^']+)'", badging, re.M)
            if launch:
                require(activity is None or activity == launch.group(1), 'split APK activities disagree')
                activity = launch.group(1)
            with zipfile.ZipFile(apk) as zipped:
                for name in zipped.namelist():
                    if name.startswith('lib/') and name.endswith('.so'):
                        data = zipped.read(name)
                        native.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data),
                                       'load_alignment': verify_elf_alignment(data)})
            run([tools / 'zipalign', '-c', '-P', '16', '4', apk])
            entries.append({**reference(apk), 'relative_path': apk.relative_to(root).as_posix()})
        require(entries and activity, 'bundle-derived split set lacks the actual launchable app')
        require(sorted(native, key=lambda x: x['path']) == sorted(expected, key=lambda x: x['path']),
                'bundle-derived native payload differs from the x86 APK')
        return {'archive': reference(archive), 'bundle': reference(bundle), 'device': device, 'activity': activity,
                'abi': 'x86_64', 'artifacts': entries, 'native_libraries': native}
    finally:
        for path in passwords: path.unlink(missing_ok=True)


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
            resource = generated / 'app/src/main/res/values/gchat_firebase.xml'
            resource.parent.mkdir(parents=True, exist_ok=True)
            resource.write_bytes(firebase_resources(value))
            report['firebase_resources_sha256'] = digest(resource)
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
        if getattr(args, 'bundle', False):
            # A single Play bundle holds both ABIs. Never combine --aab with
            # --split-per-abi: separate bundles cannot represent one Play version.
            run(tauri_command('android', 'build', '--ci', '--aab', '--target', 'aarch64', 'x86_64',
                              '--config', config), cwd=chat / 'apps/client', env=env)
            bundles = sorted(generated.glob('app/build/outputs/bundle/**/*release*.aab'))
            require(len(bundles) == 1, 'expected one release app bundle containing both ABIs')
            jar = bundletool(dest)
            bundle = artifacts / 'gchat.aab'
            shutil.copyfile(bundles[0], bundle)
            report['bundle'] = {**reference(bundle), **inspect_bundle(bundle, jar, entries)}
            report['bundletool'] = reference(jar)
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
            if build.get('bundle'):
                bundle = verify_reference(build['bundle'])
                jar = verify_reference(build['bundletool'])
                require(digest(jar) == BUNDLETOOL_SHA256, 'bundletool signing input is not the pinned release')
                result = target / bundle.name
                run(['jarsigner', '-keystore', key, '-storepass:env', 'ANDROID_KEYSTORE_PASSWORD',
                     '-keypass:env', 'ANDROID_KEY_PASSWORD', '-digestalg', 'SHA-256',
                     '-signedjar', result, bundle, os.environ['ANDROID_KEY_ALIAS']])
                verifier = Path(__file__).with_name('VerifyAndroidBundle.java')
                verification = json.loads(output(['java', verifier, result, pin]))
                require(verification.get('passed') is True and verification.get('certificate_sha256') == pin,
                        'bundle signature verification failed')
                inspected = inspect_bundle(result, jar, build['artifacts'])
                require(inspected['native_libraries'] == build['bundle']['native_libraries'],
                        'signing changed app bundle native libraries')
                report['bundle'] = {**reference(result), **inspected, 'signature': verification,
                                    'verifier': reference(verifier)}
                expected = next(x['native_libraries'] for x in build['artifacts'] if x['abi'] == 'x86_64')
                report['bundle_apks'] = derive_bundle_apks(root, result, jar, key, Path(private), tools, pin, expected)
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


def root_emulator(adb, receipt, timeout=45):
    """ADB root may close its transport while restarting; require real UID 0."""
    deadline = time.monotonic() + timeout
    report = {'passed': False, 'attempts': []}
    try:
        for _ in range(3):
            attempt = []
            report['attempts'].append(attempt)
            def command(*args):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                item = {'command': list(args)}
                attempt.append(item)
                try:
                    result = subprocess.run([str(x) for x in [*adb, *args]], text=True,
                                            capture_output=True, timeout=min(15, remaining))
                    item.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
                    return result
                except subprocess.TimeoutExpired:
                    item['timed_out'] = True
                    return None
            command('root')
            ready = command('wait-for-device')
            if ready is not None and ready.returncode == 0:
                identity = command('shell', 'id', '-u')
                if identity is not None and identity.returncode == 0 and identity.stdout.strip() == '0':
                    report['passed'] = True
                    return
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(1, remaining))
        raise ValueError('fixture ADB did not reconnect with verified root privileges')
    finally:
        write_json(receipt, report)


def cleanup_emulator(shell, adb, installed, uid, firewall, ui_dump_created=True, picker_file_created=False):
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
    if ui_dump_created:
        try:
            shell('rm', '-f', '/sdcard/gchat-fixture-ui.xml')
        except Exception:
            errors.append('failed to remove owned UI dump')
    if picker_file_created:
        try:
            shell('rm', '-f', PICKER_FIXTURE_PATH)
            shell('test', '!', '-e', PICKER_FIXTURE_PATH)
        except Exception:
            errors.append('failed to remove owned picker fixture')
    return {'passed': not errors, 'errors': errors}


def installed_package_uid(text):
    # PackageManager's UID listing is stable across releases; dumpsys field names
    # (userId/appId) are human diagnostics and changed on the API 35 fixture.
    rows = [line.strip() for line in text.splitlines() if line.strip()]
    require(len(rows) == 1, 'installed package UID lookup is ambiguous')
    match = re.fullmatch(r'package:' + re.escape(PACKAGE) + r'\s+uid:([0-9]+)', rows[0])
    require(match is not None, 'package manager did not return the exact installed app UID')
    uid = int(match.group(1))
    require(10000 <= uid < 100000, 'fixture app UID is outside Android user 0 application range')
    return uid


def resumed_packages(text):
    packages = set()
    for line in text.splitlines():
        if re.search(r'\b(?:topResumedActivity|mResumedActivity|ResumedActivity)\s*[:=]', line):
            match = re.search(r'\b([A-Za-z][A-Za-z0-9_.]*)/[A-Za-z0-9_.$]+', line)
            if match:
                packages.add(match.group(1))
    require(packages, 'activity manager did not report any resumed fixture activity')
    return sorted(packages)


def keyboard_shown(text):
    values = re.findall(r'\bmInputShown=(true|false)\b', text)
    require(values, 'input method did not expose fixture keyboard visibility')
    return any(value == 'true' for value in values)


def wait_keyboard(shell, expected, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if keyboard_shown(shell('dumpsys', 'input_method')) == expected:
            # Let Android's IME animation and the app visualViewport settle before
            # obtaining new accessibility bounds. Escape does not dismiss Gboard.
            time.sleep(0.4)
            if keyboard_shown(shell('dumpsys', 'input_method')) == expected:
                return
        time.sleep(0.2)
    raise ValueError('fixture keyboard did not reach expected visibility')


def ui_nodes(shell, diagnostics):
    # uiautomator can exit zero without writing a dump while a newly launched
    # WebView is busy. Never consume an older screen or fail before the caller's
    # existing observation deadline has elapsed.
    path = '/sdcard/gchat-fixture-ui.xml'
    shell('rm', '-f', path)
    dump = ''
    try:
        dump = shell('uiautomator', 'dump', path)
        return list(ET.fromstring(shell('cat', path)).iter('node'))
    except (subprocess.CalledProcessError, ET.ParseError) as error:
        diagnostics.append({'monotonic': time.monotonic(), 'dump_output': dump,
                            'error': type(error).__name__,
                            'stderr': getattr(error, 'stderr', None)})
        return []


def select_picker_fixture(wait_node, tap):
    """Select one exact harmless Downloads file through the real Documents UI."""
    name = PurePosixPath(PICKER_FIXTURE_PATH).name
    def label(value):
        return lambda node: (node.attrib.get('package', '').endswith('.documentsui')
                             and value in (node.attrib.get('text'), node.attrib.get('content-desc')))
    node = wait_node(lambda n: label(name)(n) or label('Show roots')(n) or label('Downloads')(n), timeout=30)
    if not label(name)(node):
        if label('Show roots')(node):
            tap(node)
            node = wait_node(label('Downloads'), timeout=15)
        tap(node)
        node = wait_node(label(name), timeout=30)
    tap(node)


def bundle_smoke_inputs(root, signed):
    artifact = signed.get('bundle_apks', {})
    require(artifact.get('artifacts') and signed.get('bundle'), 'no qualified bundle-derived split set')
    require(artifact['bundle']['sha256'] == signed['bundle']['sha256'], 'split set belongs to another bundle')
    archive = verify_copy(root / 'signed/gchat-x86_64.apks', artifact['archive'])
    paths = []
    for item in artifact['artifacts']:
        path = root / item['relative_path']
        require(path.resolve().is_relative_to((root / 'signed/bundle-apks').resolve()), 'split APK path escapes signed set')
        require(path not in paths, 'duplicate split APK')
        paths.append(verify_copy(path, item))
    return artifact, archive, paths


def smoke(args):
    root = args.output.resolve()
    signed_path = root / 'signing.json'
    signed = json.loads(signed_path.read_text())
    require(signed.get('passed') and signed.get('private_keystore_removed'), 'signing/cleanup receipt did not pass')
    build_path = verify_copy(root / 'build.json', signed['build'])
    build = json.loads(build_path.read_text())
    require(build.get('passed') and build.get('sources_unchanged') and signed['sources'] == build['sources'],
            'signing receipt differs from its build/source binding')
    android = sdk(require_ndk=False)
    from_bundle = getattr(args, 'from_bundle', False)
    if from_bundle:
        artifact, apk, apk_paths = bundle_smoke_inputs(root, signed)
    else:
        artifact = next(x for x in signed['artifacts'] if x['abi'] == 'x86_64')
        apk = verify_copy(root / 'signed/gchat-x86_64.apk', artifact)
        apk_paths = [apk]
    for path in apk_paths:
        verify_signature(path, android / 'build-tools' / BUILD_TOOLS, signed['certificate_sha256'])
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
              'from_bundle': from_bundle, 'installed_apks': [reference(path) for path in apk_paths],
              'physical_device_qualified': False, 'network_delivery_qualified': False, 'push_qualified': False,
              'observations': [], 'ui_observation_errors': []}
    installed = False
    ui_dump_created = False
    picker_file_created = False
    uid = None
    firewall = []
    try:
        root_emulator(adb, dest / 'adb-root.json')
        report['api'] = int(shell('getprop', 'ro.build.version.sdk'))
        report['abi'] = shell('getprop', 'ro.product.cpu.abi')
        require(report['api'] >= 26 and report['abi'] == 'x86_64', 'unexpected emulator API/ABI')
        run([*adb, 'install-multiple' if from_bundle else 'install', '--no-streaming', *apk_paths], timeout=120)
        installed = True
        package = shell('pm', 'list', 'packages', '-U', '--user', '0', PACKAGE)
        (dest / 'package-uid.txt').write_text(package + '\n')
        uid = installed_package_uid(package)
        # This fresh disposable emulator is rooted. Block only this app UID's
        # non-loopback traffic; adb and host networking are untouched.
        for command in ('iptables', 'ip6tables'):
            shell(command, '-I', 'OUTPUT', '-m', 'owner', '--uid-owner', str(uid), '!', '-o', 'lo', '-j', 'REJECT')
            firewall.append(command)
        def launch():
            result = shell('am', 'start', '-W', '-n', PACKAGE + '/' + artifact['activity'])
            require('Status: ok' in result, 'Android did not start GChat successfully')
        def nodes():
            nonlocal ui_dump_created
            ui_dump_created = True  # A failed dump may still leave a partial file.
            return ui_nodes(shell, report['ui_observation_errors'])
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
        def fill_passphrase():
            expected = 'gchat-emulator-fixture-only-42'
            password = wait_node(lambda n: n.attrib.get('password') == 'true')
            tap(password)
            wait_keyboard(shell, True)
            shell('input', 'text', expected)
            password = wait_node(lambda n: n.attrib.get('password') == 'true')
            require(password.attrib.get('text') == expected, 'fixture passphrase input differs before submission')
            shell('input', 'keyevent', '4')  # Android Back dismisses the shown IME.
            wait_keyboard(shell, False)
            password = wait_node(lambda n: n.attrib.get('password') == 'true')
            require(password.attrib.get('text') == expected, 'fixture passphrase changed during keyboard dismissal')
        def activity_state(phase, expected_foreground):
            state = shell('dumpsys', 'activity', 'activities')
            (dest / (phase + '-activities.txt')).write_text(state)
            packages = resumed_packages(state)
            report.setdefault('activity_observations', []).append({
                'phase': phase, 'resumed_packages': packages, 'monotonic': time.monotonic(),
            })
            require((PACKAGE in packages) == expected_foreground, 'app activity did not reach requested foreground/background state')
        def no_listener(phase):
            tcp = shell('cat', '/proc/net/tcp', '/proc/net/tcp6')
            listeners = listener_rows(tcp, uid)
            report['observations'].append({'phase': phase, 'app_uid': uid, 'tcp_listeners': listeners})
            require(not listeners, 'outbound mobile app opened a TCP listening socket')
        launch()
        wait_node(text('Create identity'))
        no_listener('fresh_locked')
        fill_passphrase()
        tap(wait_node(text('Create identity')))
        wait_node(text('Connect to GChat'), timeout=120)
        no_listener('created_unlocked_without_network_invitation')
        activity_state('created', True)
        shell('input', 'keyevent', '3')
        time.sleep(3)
        activity_state('background', False)
        no_listener('background')
        launch()
        activity_state('foreground', True)
        wait_node(text('Reconnect'))
        fill_passphrase()
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
            fill_passphrase()
            tap(wait_node(text('Reconnect')))
            wait_node(text('Connect to GChat'), timeout=120)
            tap(wait_node(text('Or choose an invitation file')))
            picker = wait_node(lambda n: n.attrib.get('package', '').endswith('.documentsui'), timeout=30)
            report['picker'] = {'opened': True, 'package': picker.attrib['package'], 'selected_file': False}
            activity_state('picker_cancel_open', False)
            time.sleep(2)  # Cross Android's process-background debounce.
            no_listener('invitation_picker_open')
            shell('input', 'keyevent', '4')
            wait_node(text('Reconnect'), timeout=30)
            report['picker']['cancel_returned_locked'] = True
            activity_state('picker_cancel_return', True)
            no_listener('invitation_picker_cancel_return')
            fill_passphrase()
            tap(wait_node(text('Reconnect')))
            wait_node(text('Connect to GChat'), timeout=120)
            require(not any(text('Continue selected file')(n) for n in nodes()),
                    'cancelled picker retained a selected file')
            report['picker']['cancel_manual_reopen_passed'] = True
            # Only a public, invalid fixture string is placed in the disposable
            # emulator. Do not click Connect or provision any network afterward.
            fixture = dest / 'gchat-fixture.txt'
            fixture.write_text(PICKER_FIXTURE_TEXT)
            shell('mkdir', '-p', '/sdcard/Download')
            shell('test', '!', '-e', PICKER_FIXTURE_PATH)
            picker_file_created = True  # A failed push can leave a partial file.
            run([*adb, 'push', fixture, PICKER_FIXTURE_PATH], timeout=30)
            shell('am', 'broadcast', '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE',
                  '-d', 'file://' + PICKER_FIXTURE_PATH)
            tap(wait_node(text('Or choose an invitation file')))
            wait_node(lambda n: n.attrib.get('package', '').endswith('.documentsui'), timeout=30)
            activity_state('picker_select_open', False)
            time.sleep(2)
            select_picker_fixture(wait_node, tap)
            wait_node(text('Reconnect'), timeout=30)
            report['picker']['selected_file'] = True
            report['picker']['selection_returned_locked'] = True
            activity_state('picker_select_return', True)
            wait_node(text('A selected file is waiting for this profile. Reconnect to continue.'), timeout=30)
            require(not any(text(PICKER_FIXTURE_TEXT)(n) for n in nodes()),
                    'invitation contents were exposed while the profile was locked')
            fill_passphrase()
            tap(wait_node(text('Reconnect')))
            wait_node(text('Connect to GChat'), timeout=120)
            tap(wait_node(text('Continue selected file')))
            wait_node(lambda n: n.attrib.get('class') == 'android.widget.EditText'
                      and n.attrib.get('text') == PICKER_FIXTURE_TEXT, timeout=30)
            report['picker'].update({'same_profile_selection_continued': True,
                                    'provider_submission_performed': False, 'passed': True})
            no_listener('invitation_picker_selection_continued')
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
        report['cleanup'] = cleanup_emulator(shell, adb, installed, uid, firewall, ui_dump_created, picker_file_created)
        original = artifact['archive'] if from_bundle else artifact
        report['inputs_unchanged'] = digest(apk) == original['sha256'] and all(
            digest(path) == item['sha256'] for path, item in zip(apk_paths, report['installed_apks']))
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
            smoke(argparse.Namespace(output=root, serial='emulator-5554', probe_picker=getattr(args, 'probe_picker', False),
                                     from_bundle=getattr(args, 'from_bundle', False)))
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
            # ZipInfo normalizes backslashes on Windows and truncates NULs.
            # Reject changes to the raw archived name before trusting it.
            require(member.orig_filename == member.filename, 'unsafe artifact archive member')
            # ZIP member names have POSIX semantics on every host; WindowsPath
            # considers /absolute drive-relative and would miss this guard.
            path = PurePosixPath(member.filename)
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
    compile_app.add_argument('--bundle', action='store_true', help='also build the single two-ABI Google Play AAB')
    for name in ('sign', 'smoke', 'emulator'):
        sub = commands.add_parser(name)
        sub.add_argument('--output', type=Path, required=True)
        if name == 'smoke': sub.add_argument('--serial', required=True)
        if name in ('smoke', 'emulator'): sub.add_argument('--probe-picker', action='store_true')
        if name in ('smoke', 'emulator'): sub.add_argument('--from-bundle', action='store_true')
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
