"""iOS release rejects source, signing, entitlement and artifact substitution."""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import plistlib
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('ios_build', SCRIPTS / 'ios-build.py')
ios = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ios)
PIN = hashlib.sha256(b'fixture distribution certificate').hexdigest()


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.profile = {
            'UUID': 'b1f0e52b-6dbd-4378-959b-0a20ec709078', 'Name': 'Fixture distribution',
            'TeamIdentifier': [ios.TEAM], 'ExpirationDate': self.now + timedelta(days=30),
            'DeveloperCertificates': [b'fixture distribution certificate'],
            'Entitlements': {'application-identifier': ios.TEAM + '.' + ios.BUNDLE,
                             'com.apple.developer.team-identifier': ios.TEAM,
                             'get-task-allow': False, 'aps-environment': 'production',
                             'keychain-access-groups': [ios.TEAM + '.*']},
        }

    def test_exact_unexpired_distribution_profile(self):
        self.assertEqual(ios.validate_profile(self.profile, PIN, self.now)['bundle'], ios.BUNDLE)

    def test_wildcard_application_cannot_sign_exact_bundle(self):
        self.profile['Entitlements']['application-identifier'] = ios.TEAM + '.boo.gchat.*'
        with self.assertRaisesRegex(ValueError, 'application entitlement'):
            ios.validate_profile(self.profile, PIN)

    def test_wrong_team_and_expired_profile_rejected(self):
        for name, value in [('TeamIdentifier', ['OTHERTEAM1']), ('ExpirationDate', self.now - timedelta(seconds=1))]:
            with self.subTest(name=name), patch.dict(self.profile, {name: value}):
                with self.assertRaises(ValueError):
                    ios.validate_profile(self.profile, PIN)

    def test_development_adhoc_and_enterprise_profiles_rejected(self):
        for name, value in [('ProvisionedDevices', ['device']), ('ProvisionsAllDevices', True)]:
            with self.subTest(name=name), patch.dict(self.profile, {name: value}):
                with self.assertRaisesRegex(ValueError, 'App Store'):
                    ios.validate_profile(self.profile, PIN)

    def test_profile_certificate_pin_must_match(self):
        with self.assertRaisesRegex(ValueError, 'pinned'):
            ios.validate_profile(self.profile, '0' * 64)
        self.profile['DeveloperCertificates'].append(b'other signer')
        with self.assertRaisesRegex(ValueError, 'single pinned'):
            ios.validate_profile(self.profile, PIN)

    def test_device_entitlements_reject_debug_and_nonproduction_push(self):
        for key, value in [('get-task-allow', True), ('aps-environment', 'development'),
                           ('com.apple.developer.team-identifier', 'OTHERTEAM1')]:
            with self.subTest(key=key), patch.dict(self.profile['Entitlements'], {key: value}):
                with self.assertRaises(ValueError):
                    ios.validate_profile(self.profile, PIN)

    def test_absent_debugger_entitlement_is_not_assumed_safe(self):
        del self.profile['Entitlements']['get-task-allow']
        with self.assertRaisesRegex(ValueError, 'explicitly disabled'):
            ios.validate_profile(self.profile, PIN)

    def test_keychain_wildcard_allowed_in_profile_but_not_app(self):
        ios.validate_profile(self.profile, PIN)
        with self.assertRaisesRegex(ValueError, 'Keychain'):
            ios.validate_entitlements(self.profile['Entitlements'])

    def test_apple_profile_token_allowance_is_never_granted_to_signed_app(self):
        self.profile['Entitlements']['keychain-access-groups'] = [ios.TEAM + '.*', 'com.apple.token']
        ios.validate_profile(self.profile, PIN)
        for group in ('com.apple.token', ios.TEAM + '.*', 'another.app'):
            self.profile['Entitlements']['keychain-access-groups'] = [ios.TEAM + '.' + ios.BUNDLE, group]
            with self.subTest(group=group), self.assertRaisesRegex(ValueError, 'Keychain'):
                ios.validate_entitlements(self.profile['Entitlements'])
        self.profile['Entitlements']['keychain-access-groups'] = [ios.TEAM + '.*', 'another.app']
        with self.assertRaisesRegex(ValueError, 'Keychain'):
            ios.validate_profile(self.profile, PIN)
        self.profile['Entitlements']['keychain-access-groups'] = [ios.TEAM + '.' + ios.BUNDLE]
        ios.validate_entitlements(self.profile['Entitlements'])
        self.profile['Entitlements']['keychain-access-groups'].append('another.app')
        with self.assertRaisesRegex(ValueError, 'Keychain'):
            ios.validate_entitlements(self.profile['Entitlements'])

    def test_existing_profile_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(ios, 'keychains', return_value=[]), \
                patch.object(ios, 'profile_files', return_value={'/fixture/' + self.profile['UUID'] + '.mobileprovision': PIN}), \
                patch.object(ios, 'secret_command') as command:
            with self.assertRaisesRegex(ValueError, 'fresh isolated worker'):
                with ios.signer(Path(temporary), ios.validate_profile(self.profile, PIN), PIN):
                    self.fail('must refuse before import')
            command.assert_not_called()

    def test_ipa_certificate_extraction_uses_codesign_optional_argument_syntax(self):
        # macOS codesign accepts an optional prefix only joined with '='. A
        # separate prefix is parsed as an additional code object and fails.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ipa = root / 'fixture.ipa'
            with zipfile.ZipFile(ipa, 'w') as archive:
                archive.writestr('Payload/GChat.app/Info.plist', plistlib.dumps({
                    'CFBundleIdentifier': ios.BUNDLE, 'CFBundleVersion': '1.0.4',
                    'MinimumOSVersion': '15.0', 'CFBundleExecutable': 'GChat'}))
                archive.writestr('Payload/GChat.app/GChat', b'fixture executable')
            entitlements = dict(self.profile['Entitlements'],
                                **{'keychain-access-groups': [ios.TEAM + '.' + ios.BUNDLE]})

            def native(command):
                if command[0] == 'ditto':
                    with zipfile.ZipFile(command[-2]) as archive:
                        archive.extractall(command[-1])
                elif command[:2] == ['codesign', '-d']:
                    self.assertEqual(len(command), 4)
                    self.assertTrue(command[2].startswith('--extract-certificates='))
                    Path(command[2].split('=', 1)[1] + '0').write_bytes(b'fixture distribution certificate')

            with patch.object(ios, 'run', side_effect=native), \
                    patch.object(ios, 'output', side_effect=['arm64', 'platform IOS']), \
                    patch.object(ios.subprocess, 'check_output', return_value=plistlib.dumps(entitlements)), \
                    patch.object(ios, 'decode_profile', return_value=self.profile):
                result = ios.verify_ipa(ipa, root / 'verified', PIN, '1.0.4')
            self.assertEqual(result['certificate']['sha256'], PIN)

    def test_profile_cleanup_failure_still_removes_private_key_and_preserves_build_error(self):
        certificate = b'fixture distribution certificate'
        pem = b'-----BEGIN CERTIFICATE-----\n' + base64.b64encode(certificate) + b'\n-----END CERTIFICATE-----\n'
        original = RuntimeError('original build failure')
        commands = []
        private_paths = []

        def security(command):
            commands.append([str(part) for part in command])
            if command[1] == 'create-keychain':
                keychain = Path(command[-1])
                keychain.touch()
                private_paths.extend((keychain, keychain.parent / 'publisher.p12'))
            elif command[1] == 'delete-keychain':
                Path(command[-1]).unlink()

        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)
            residual = {str(destination / (self.profile['UUID'] + '.mobileprovision')): PIN}
            with patch.dict(os.environ, {'IOS_CERTIFICATE_BASE64': base64.b64encode(b'private fixture').decode(),
                                         'IOS_CERTIFICATE_PASSWORD': 'fixture password'}), \
                    patch.object(ios, 'keychains', return_value=['/original/keychain']), \
                    patch.object(ios, 'profile_files', side_effect=[{}, residual, residual]), \
                    patch.object(ios, 'secret_command', side_effect=security), \
                    patch.object(ios.subprocess, 'check_output', return_value=pem), \
                    patch.object(ios, 'output', return_value=hashlib.sha1(certificate).hexdigest().upper()), \
                    patch.object(ios, 'decode_profile', side_effect=ValueError('malformed profile')):
                with self.assertRaises(RuntimeError) as raised:
                    with ios.signer(destination, ios.validate_profile(self.profile, PIN), PIN):
                        self.assertTrue(all(path.exists() for path in private_paths))
                        raise original
            self.assertIs(raised.exception, original)
            self.assertIn(['security', 'list-keychains', '-d', 'user', '-s', '/original/keychain'], commands)
            self.assertTrue(any(command[1] == 'delete-keychain' for command in commands))
            self.assertTrue(all(not path.exists() for path in private_paths))
            cleanup = json.loads((destination / 'signing-cleanup.json').read_text())
            self.assertFalse(cleanup['passed'])
            self.assertTrue(cleanup['original_keychain_search_restored'])
            self.assertTrue(cleanup['temporary_keychain_removed'])
            self.assertTrue(cleanup['private_certificate_removed'])
            self.assertFalse(cleanup['original_profiles_unchanged'])
            self.assertEqual(cleanup['errors'], [{'step': 'remove_owned_profile', 'error_type': 'ValueError'}])

    def test_installed_and_tauri_random_named_profiles_are_removed_by_validated_uuid(self):
        certificate = b'fixture distribution certificate'
        pem = b'-----BEGIN CERTIFICATE-----\n' + base64.b64encode(certificate) + b'\n-----END CERTIFICATE-----\n'

        def security(command):
            if command[1] == 'create-keychain':
                Path(command[-1]).touch()
            elif command[1] == 'delete-keychain':
                Path(command[-1]).unlink()

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(Path, 'home', return_value=root), \
                    patch.dict(os.environ, {'IOS_CERTIFICATE_BASE64': base64.b64encode(b'fixture key').decode(),
                                             'IOS_CERTIFICATE_PASSWORD': 'fixture'}), \
                    patch.object(ios, 'keychains', return_value=[]), \
                    patch.object(ios, 'secret_command', side_effect=security), \
                    patch.object(ios.subprocess, 'check_output', return_value=pem), \
                    patch.object(ios, 'output', return_value=hashlib.sha1(certificate).hexdigest().upper()), \
                    patch.object(ios, 'decode_profile', return_value=self.profile):
                with ios.signer(root, ios.validate_profile(self.profile, PIN), PIN, b'profile bytes'):
                    self.assertEqual(len(ios.profile_files()), 2)
                    random_copy = root / 'Library/MobileDevice/Provisioning Profiles/randomTauriCopy.mobileprovision'
                    random_copy.write_bytes(b'profile bytes')
                    self.assertEqual(len(ios.profile_files()), 3)
                self.assertEqual(ios.profile_files(), {})
            cleanup = json.loads((root / 'signing-cleanup.json').read_text())
            self.assertTrue(cleanup['passed'])
            self.assertTrue(cleanup['original_profiles_unchanged'])

    def test_unrelated_new_profile_is_preserved_and_fails_cleanup(self):
        certificate = b'fixture distribution certificate'
        pem = b'-----BEGIN CERTIFICATE-----\n' + base64.b64encode(certificate) + b'\n-----END CERTIFICATE-----\n'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            unrelated = root / 'unrelated.mobileprovision'
            unrelated.write_bytes(b'other profile')
            residual = {str(unrelated): hashlib.sha256(unrelated.read_bytes()).hexdigest()}
            with patch.dict(os.environ, {'IOS_CERTIFICATE_BASE64': base64.b64encode(b'fixture key').decode(),
                                         'IOS_CERTIFICATE_PASSWORD': 'fixture'}), \
                    patch.object(ios, 'keychains', return_value=[]), \
                    patch.object(ios, 'profile_files', side_effect=[{}, residual, residual]), \
                    patch.object(ios, 'secret_command'), \
                    patch.object(ios.subprocess, 'check_output', return_value=pem), \
                    patch.object(ios, 'output', return_value=hashlib.sha1(certificate).hexdigest().upper()), \
                    patch.object(ios, 'decode_profile', return_value={'UUID': 'another-owner'}):
                with self.assertRaisesRegex(ValueError, 'boundary'):
                    with ios.signer(root, ios.validate_profile(self.profile, PIN), PIN):
                        pass
            self.assertTrue(unrelated.exists())
            self.assertFalse(json.loads((root / 'signing-cleanup.json').read_text())['passed'])


class ArtifactTests(unittest.TestCase):
    def test_device_preflight_requires_effective_profile_identity_and_xcode(self):
        value = dict(PRODUCT_BUNDLE_IDENTIFIER=ios.BUNDLE, CODE_SIGN_STYLE='Manual', DEVELOPMENT_TEAM=ios.TEAM,
                     PROVISIONING_PROFILE_SPECIFIER='profile-uuid', CODE_SIGN_IDENTITY='certificate-sha1',
                     SDKROOT='/Applications/Xcode_26.2.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS26.2.sdk')
        ios.verify_device_settings([{'buildSettings': value}], {'uuid': 'profile-uuid'}, 'certificate-sha1')
        for key, replacement in [('CODE_SIGN_STYLE', 'Automatic'), ('DEVELOPMENT_TEAM', 'other'),
                                  ('PROVISIONING_PROFILE_SPECIFIER', ''), ('CODE_SIGN_IDENTITY', 'other'),
                                  ('SDKROOT', '/Applications/Xcode_16.4.app/SDKs/iPhoneOS18.5.sdk')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                ios.verify_device_settings([{'buildSettings': dict(value, **{key: replacement})}],
                                           {'uuid': 'profile-uuid'}, 'certificate-sha1')

    @unittest.skipIf(os.name == 'nt', 'executes the macOS-compatible POSIX build wrapper')
    def test_xcode_selection_survives_cargo_mobile_explicit_environment(self):
        with tempfile.TemporaryDirectory() as temporary:
            # Exercise macOS's /var -> /private/var spelling difference on
            # every POSIX test host, rather than relying on its temp layout.
            physical = Path(temporary) / 'physical'
            physical.mkdir()
            root = Path(temporary) / 'alias'
            root.symlink_to(physical, target_is_directory=True)
            native = root / 'real xcodebuild'
            native.write_text('#!/bin/sh\nprintf "%s\\n" "$DEVELOPER_DIR" "${XCODE_XCCONFIG_FILE-unset}" "$@"\n')
            native.chmod(0o700)
            config = root / 'manual signing.xcconfig'
            config.write_text('CODE_SIGN_STYLE = Manual\n')
            environment = dict(PATH=os.environ['PATH'], DEVELOPER_DIR='/Applications/Xcode_26.2.app/Contents/Developer')
            for label, signing in [('simulator', None), ('device', config)]:
                wrapped = ios.xcode_environment(root / label, environment, signing, str(native))
                # Matches cargo-mobile2: only PATH and a small base env survive.
                result = subprocess.check_output(['xcodebuild', '-showBuildSettings'],
                    env={'PATH': wrapped['PATH']}, text=True).splitlines()
                self.assertEqual(result, [environment['DEVELOPER_DIR'],
                    str(config.resolve()) if signing else 'unset', '-showBuildSettings'])

    def test_simulator_uses_an_available_runtime_compatible_phone_not_type_list_order(self):
        types = [{'identifier': 'iphone17', 'name': 'iPhone 17'},
                 {'identifier': 'iphone6s', 'name': 'iPhone 6s Plus'}]
        devices = {'ios26': [{'name': 'iPhone 17', 'deviceTypeIdentifier': 'iphone17', 'isAvailable': True}],
                   'ios15': [{'name': 'iPhone 6s Plus', 'deviceTypeIdentifier': 'iphone6s', 'isAvailable': True}]}
        self.assertEqual(ios.simulator_phone('ios26', types, devices), 'iphone17')
        del devices['ios26'][0]['deviceTypeIdentifier']
        self.assertEqual(ios.simulator_phone('ios26', types, devices), 'iphone17')
        devices['ios26'][0]['isAvailable'] = False
        with self.assertRaisesRegex(ValueError, 'compatible'):
            ios.simulator_phone('ios26', types, devices)
        with self.assertRaisesRegex(ValueError, 'compatible'):
            ios.simulator_phone('absent', types, devices)

    def test_simulator_cleanup_attempts_all_steps_after_timeouts(self):
        device = '12345678-1234-1234-1234-123456789abc'
        report = {}
        with patch.object(ios.subprocess, 'run', side_effect=[
                subprocess.TimeoutExpired(['terminate'], 30),
                subprocess.TimeoutExpired(['shutdown'], 60),
                subprocess.CalledProcessError(1, ['delete'])]) as commands, \
                patch.object(ios, 'output', side_effect=OSError('simulator unavailable')):
            ios.cleanup_simulator(device, report)
        self.assertEqual([call.args[0][2] for call in commands.call_args_list],
                         ['terminate', 'shutdown', 'delete'])
        self.assertTrue(all(call.args[0][3] == device for call in commands.call_args_list))
        self.assertEqual([row['step'] for row in report['cleanup_errors']],
                         ['terminate', 'shutdown', 'delete', 'verify_removal'])
        self.assertFalse(report['cleanup_complete'])

    def test_simulator_install_failure_survives_cleanup_timeout_with_receipt(self):
        device = '12345678-1234-1234-1234-123456789abc'
        original = subprocess.TimeoutExpired(['simctl', 'install'], 120)

        def execute(command, **_):
            if command[2] == 'install':
                raise original

        def result(command, **_):
            if command[2] == 'create':
                return device
            if 'devicetypes' in command:
                return json.dumps({'devicetypes': []})
            return json.dumps({'devices': {}})

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = root / 'GChat.app'
            app.mkdir()
            (app / 'Info.plist').write_bytes(plistlib.dumps(
                {'CFBundleIdentifier': ios.BUNDLE, 'CFBundleExecutable': 'GChat'}))
            (app / 'GChat').write_bytes(b'fixture executable; never executed')
            with patch.object(ios, 'simulator_runtime', return_value='ios26'), \
                    patch.object(ios, 'simulator_phone', return_value='iphone17'), \
                    patch.object(ios, 'output', side_effect=result), \
                    patch.object(ios, 'run', side_effect=execute), \
                    patch.object(ios.subprocess, 'run', side_effect=[
                        subprocess.TimeoutExpired(['terminate'], 30), None, None]):
                with self.assertRaises(subprocess.TimeoutExpired) as caught:
                    ios.simulator_smoke(app, root / 'smoke')
            self.assertIs(caught.exception, original)
            report = json.loads((root / 'smoke/report.json').read_text())
            self.assertIn('install', report['error'])
            self.assertEqual(report['cleanup_errors'], [{'step': 'terminate', 'error_type': 'TimeoutExpired'}])
            self.assertTrue(report['owned_device_removed'])
            self.assertFalse(report['cleanup_complete'])
            self.assertFalse(report['passed'])

    def test_tauri_generated_project_does_not_require_a_sibling_workspace(self):
        # iOS06's actual generation log names gen/apple/gchat-desktop.xcodeproj;
        # the built-in workspace belongs inside that project directory.
        with tempfile.TemporaryDirectory() as temporary:
            generated = Path(temporary)
            project = generated / 'gchat-desktop.xcodeproj'
            (project / 'project.xcworkspace').mkdir(parents=True)
            (project / 'project.pbxproj').write_text('// generated project fixture\n')
            self.assertEqual(ios.generated_project(generated), project)
            self.assertEqual(list(generated.glob('*.xcworkspace')), [])
            (generated / 'other.xcodeproj').mkdir()
            with self.assertRaisesRegex(ValueError, 'exactly one generated Xcode project'):
                ios.generated_project(generated)

    def test_missing_or_incomplete_generated_project_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            generated = Path(temporary)
            for create in (False, True):
                if create:
                    (generated / 'gchat-desktop.xcodeproj').mkdir()
                with self.subTest(project_directory=create), self.assertRaisesRegex(ValueError, 'generated Xcode project'):
                    ios.generated_project(generated)

    def test_mobile_graph_rejects_relay_and_desktop_hosts(self):
        graph = 'gcoms v0.1.0|files,ipc,network-client,rpc\ngcoms-node v0.1.0|client-persist\ngcoms-runtime v0.1.0|\n'
        self.assertIn('network-client', ios.feature_graph(graph)['gcoms'])
        for extra in ('embedded', 'launch'):
            with self.subTest(feature=extra), self.assertRaisesRegex(ValueError, 'desktop'):
                ios.feature_graph(graph.replace('files,', extra + ',files,'))
        with self.assertRaisesRegex(ValueError, 'relay hosting'):
            ios.feature_graph(graph.replace('client-persist', 'client-persist,relay-host'))
        with self.assertRaisesRegex(ValueError, 'network-client'):
            ios.feature_graph(graph.replace('network-client,', ''))

    def test_apple_numeric_build_number_limits(self):
        self.assertEqual(ios.build_number('42.1.3'), '42.1.3')
        for number in ('0.1.1', '20260921', '1.0.1.2', '1.100.1', '1.0.1-beta', '1.0.1\n'):
            with self.subTest(number=number), self.assertRaises(ValueError):
                ios.build_number(number)

    def test_artifact_rehash_rejects_changed_content_and_size(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'app.ipa'
            path.write_bytes(b'actual ipa fixture')
            receipt = ios.reference(path)
            self.assertEqual(ios.verify_reference(receipt), path.resolve())
            path.write_bytes(b'changed ipa fixture')
            with self.assertRaisesRegex(ValueError, 'receipt'):
                ios.verify_reference(receipt)

    def test_archive_traversal_and_symlink_escape_rejected(self):
        for name in ('/outside', '../outside', 'Payload/../../outside', 'Payload\\outside'):
            with self.subTest(name=name), io.BytesIO() as data:
                with zipfile.ZipFile(data, 'w') as archive:
                    archive.writestr(name, b'bad')
                    with self.assertRaisesRegex(ValueError, 'archive path'):
                        ios.inspect_zip(archive)
        with io.BytesIO() as data, zipfile.ZipFile(data, 'w') as archive:
            link = zipfile.ZipInfo('Payload/GChat.app/link')
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(link, '../../outside')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                ios.inspect_zip(archive)

    def test_safe_ipa_paths(self):
        with io.BytesIO() as data, zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('Payload/GChat.app/Info.plist', b'plist')
            archive.writestr('Payload/GChat.app/GChat', b'binary')
            ios.inspect_zip(archive)

    def test_zip_original_spelling_remains_checked_after_host_normalization(self):
        for original in ('Payload\\outside', 'Payload/GChat.app\0ignored'):
            with self.subTest(original=original), io.BytesIO() as data, zipfile.ZipFile(data, 'w') as archive:
                entry = zipfile.ZipInfo('Payload/GChat.app')
                entry.orig_filename = original
                archive.writestr(entry, b'fixture')
                with self.assertRaisesRegex(ValueError, 'archive path'):
                    ios.inspect_zip(archive)

    def test_environment_pin_and_frozen_policy_must_agree(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'publication.json'
            policy = {'name': 'Gh0st', 'team_id': ios.TEAM, 'distribution': 'app-store', 'certificate_sha256': PIN}
            path.write_text(json.dumps({'publisher_identities': {'ios': policy}}))
            self.assertEqual(ios.publisher_policy(path, PIN), policy)
            with self.assertRaisesRegex(ValueError, 'publication policy'):
                ios.publisher_policy(path, '0' * 64)
        with patch.dict(os.environ, {'IOS_SIGNING_CERT_SHA256': PIN}):
            self.assertEqual(ios.signing_pin(), PIN)
        with patch.dict(os.environ, {'IOS_SIGNING_CERT_SHA256': ''}):
            with self.assertRaisesRegex(ValueError, 'pin'):
                ios.signing_pin()

    def test_failed_build_cannot_upload(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(ios, 'run') as command:
            path = Path(temporary)
            (path / 'build.json').write_text(json.dumps({'passed': False, 'sources_unchanged': True}))
            with self.assertRaisesRegex(ValueError, 'passed unchanged'):
                ios.upload(argparse.Namespace(output=path))
            command.assert_not_called()

    def test_private_command_timeout_does_not_print_password(self):
        with patch.object(ios.subprocess, 'run', side_effect=subprocess.TimeoutExpired(['security', 'secret'], 60)):
            with self.assertRaisesRegex(ValueError, '^private signing command timed out$'):
                ios.secret_command(['security', 'secret'])


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.ref = 'refs/heads/release/gchat-ios-0.1.4'
        self.roots = [self.root / 'gchat', self.root / 'gcoms']
        self.commits = []
        for root in self.roots:
            root.mkdir()
            self.git(root, 'init', '-q')
            self.git(root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                     'commit', '-qm', 'Frozen', '--allow-empty')
            commit = self.git(root, 'rev-parse', 'HEAD')
            self.commits.append(commit)
            self.git(root, 'update-ref', self.ref.replace('refs/heads/', 'refs/remotes/origin/'), commit)
        self.args = argparse.Namespace(gchat=self.roots[0], gcoms=self.roots[1],
            gchat_commit=self.commits[0], gcoms_commit=self.commits[1], gchat_ref=self.ref, gcoms_ref=self.ref)
        self.environment = {'GITHUB_SHA': self.commits[0], 'GITHUB_WORKFLOW_SHA': self.commits[0],
                            'GITHUB_REF': self.ref,
                            'GITHUB_WORKFLOW_REF': f'{ios.policy.REPO}/.github/workflows/ios-release.yml@{self.ref}'}

    @staticmethod
    def git(root, *arguments):
        return subprocess.check_output(['git', *arguments], cwd=root, text=True, stderr=subprocess.PIPE).strip()

    def verify(self):
        with patch.dict(os.environ, self.environment):
            ios.verify_checkouts(self.args)

    def test_exact_protected_workflow_pair_passes(self):
        self.verify()

    def test_wrong_workflow_commit_ref_or_file_rejected(self):
        for field in ('GITHUB_SHA', 'GITHUB_WORKFLOW_SHA', 'GITHUB_REF', 'GITHUB_WORKFLOW_REF'):
            with self.subTest(field=field), patch.dict(self.environment, {field: 'other'}):
                with self.assertRaisesRegex(ValueError, 'workflow/source/ref'):
                    self.verify()

    def test_ref_advance_refused_for_gchat(self):
        root = self.roots[0]
        self.git(root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 'commit', '-qm', 'Moved', '--allow-empty')
        self.git(root, 'update-ref', self.ref.replace('refs/heads/', 'refs/remotes/origin/'),
                 self.git(root, 'rev-parse', 'HEAD'))
        self.git(root, 'checkout', '-q', '--detach', self.commits[0])
        with self.assertRaisesRegex(ValueError, 'ref moved'):
            self.verify()

    def test_frozen_gcoms_ancestor_remains_valid(self):
        root = self.roots[1]
        self.git(root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 'commit', '-qm', 'Branch advances', '--allow-empty')
        self.git(root, 'update-ref', self.ref.replace('refs/heads/', 'refs/remotes/origin/'),
                 self.git(root, 'rev-parse', 'HEAD'))
        self.git(root, 'checkout', '-q', '--detach', self.commits[1])
        self.verify()


if __name__ == '__main__':
    unittest.main()
