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


class ArtifactTests(unittest.TestCase):
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
