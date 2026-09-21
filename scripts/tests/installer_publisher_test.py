"""Publisher display names and native signing identities are distinct."""
import importlib.util
import json
import hashlib
import plistlib
from types import SimpleNamespace
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("installer", SCRIPTS / "build-installer.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class PublisherTest(unittest.TestCase):
    def configuration(self, root, fingerprint):
        (root / "release").mkdir()
        identity = {"name": "Gh0st", "certificate_fingerprint": fingerprint}
        (root / "release/publication.json").write_text(json.dumps({
            "publisher_identities": {platform: identity for platform in ("linux", "windows", "macos")}
        }))

    def test_missing_certificate_is_an_explicit_prerequisite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.configuration(root, None)
            with patch.object(installer, "ROOT", root):
                for system in ("Linux", "Windows", "Darwin"):
                    with self.assertRaisesRegex(ValueError, "verified public signing fingerprint"):
                        installer.configured_identity(system)

    def test_individual_name_matches_apple_certificate_cn(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.configuration(root, "A" * 64)
            environment = {"APPLE_TEAM_ID": "0123456789",
                           "APPLE_SIGNING_IDENTITY": "Developer ID Application: Gh0st (0123456789)"}
            with patch.object(installer, "ROOT", root), patch.dict(installer.os.environ, environment, clear=True):
                self.assertEqual(installer.configured_identity("Darwin")["name"], "Gh0st")
                installer.os.environ["APPLE_SIGNING_IDENTITY"] = "Developer ID Application: Other Person (0123456789)"
                with self.assertRaisesRegex(ValueError, "differs"):
                    installer.configured_identity("Darwin")

    def test_windows_certificate_must_match_configured_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.configuration(root, "A" * 40)
            with patch.object(installer, "ROOT", root), patch.dict(installer.os.environ, {"WINDOWS_CERTIFICATE_THUMBPRINT": "B" * 40}, clear=True):
                with self.assertRaisesRegex(ValueError, "differs"):
                    installer.configured_identity("Windows")

    def test_developer_id_identity_is_separate_from_brand_and_other_platforms(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.configuration(root, "A" * 40)
            path = root / "release/publication.json"
            value = json.loads(path.read_text())
            value["signing_policy"] = "self-signed"
            value["publisher_identities"]["macos"].update(
                signing_policy="publicly-trusted", team_id="0123456789",
                signing_identity="Developer ID Application: Example Company AB (0123456789)")
            path.write_text(json.dumps(value))
            environment = {"APPLE_TEAM_ID": "0123456789",
                           "APPLE_SIGNING_IDENTITY": "Developer ID Application: Example Company AB (0123456789)"}
            with patch.object(installer, "ROOT", root), patch.dict(installer.os.environ, environment, clear=True):
                self.assertEqual(installer.signing_policy("Darwin"), "publicly-trusted")
                for system in ("Linux", "Windows"):
                    self.assertEqual(installer.signing_policy(system), "self-signed")
                self.assertEqual(installer.configured_identity("Darwin")["name"], "Gh0st")
                with patch.object(installer.platform, "system", return_value="Darwin"):
                    self.assertEqual(installer.signing_policy(), "publicly-trusted")
                installer.os.environ["APPLE_SIGNING_IDENTITY"] = "Developer ID Application: Other Company (0123456789)"
                with self.assertRaisesRegex(ValueError, "differs"):
                    installer.configured_identity("Darwin")
                installer.os.environ["APPLE_TEAM_ID"] = "9999999999"
                with self.assertRaisesRegex(ValueError, "team differs"):
                    installer.configured_identity("Darwin")

    def test_apple_identity_override_cannot_select_other_certificate_kind_or_team(self):
        for name in ("Apple Distribution: Gh0st (0123456789)",
                     "Developer ID Application: Gh0st (9999999999)",
                     "Developer ID Application: Gh0st (0123456789)\n", None):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.configuration(root, "A" * 40)
                path = root / "release/publication.json"
                value = json.loads(path.read_text())
                value["publisher_identities"]["macos"]["signing_identity"] = name
                path.write_text(json.dumps(value))
                with patch.object(installer, "ROOT", root), patch.dict(installer.os.environ, {
                        "APPLE_TEAM_ID": "0123456789", "APPLE_SIGNING_IDENTITY": name or "missing"}, clear=True):
                    with self.assertRaisesRegex(ValueError, "exact Developer ID Application"):
                        installer.configured_identity("Darwin")

    def test_platform_policy_cannot_bypass_preview_restriction_or_allow_unknown_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.configuration(root, "A" * 40)
            path = root / "release/publication.json"
            value = json.loads(path.read_text())
            value.update(signing_policy="self-signed", channel="production")
            for policy, message in (("self-signed-preview", "limited to developer previews"),
                                    ("unchecked", "unknown signing policy")):
                value["publisher_identities"]["macos"]["signing_policy"] = policy
                path.write_text(json.dumps(value))
                with self.subTest(policy=policy), patch.object(installer, "ROOT", root):
                    with self.assertRaisesRegex(ValueError, message):
                        installer.signing_policy("Darwin")

    def test_self_signed_apple_uses_pin_without_developer_account(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.configuration(root, "A" * 40)
            path = root / "release/publication.json"
            value = json.loads(path.read_text())
            value.update(signing_policy="self-signed-preview", channel="developer-preview")
            path.write_text(json.dumps(value))
            with patch.object(installer, "ROOT", root), patch.dict(installer.os.environ, {"APPLE_SIGNING_IDENTITY": "A" * 40}, clear=True):
                self.assertEqual(installer.configured_identity("Darwin")["name"], "Gh0st")
                value["channel"] = "stable"
                path.write_text(json.dumps(value))
                with self.assertRaisesRegex(ValueError, "limited to developer previews"):
                    installer.configured_identity("Darwin")


class SigningDiagnosticsTest(unittest.TestCase):
    def test_pkcs12_error_reports_cause_without_arguments_or_raw_output(self):
        command = ['security', 'import', '/private/secret-file.p12', '-P', 'secret-passphrase']
        for stderr in (
            b'security: SecKeychainItemImport: MAC verification failed during PKCS12 import (wrong password?) secret-passphrase',
            'MAC verification failed during PKCS12 import /private/secret-file.p12',
        ):
            with self.subTest(stderr_type=type(stderr).__name__):
                result = subprocess.CompletedProcess(command, 1, stderr=stderr)
                with patch.object(installer.subprocess, 'run', return_value=result):
                    with self.assertRaises(RuntimeError) as caught:
                        installer.run(command, capture_output=True)
                message = str(caught.exception)
                self.assertIn('PKCS#12 MAC verification failed', message)
                self.assertIn('container algorithm compatibility', message)
                self.assertNotIn('secret-passphrase', message)
                self.assertNotIn('secret-file', message)
                self.assertNotIn('SecKeychainItemImport', message)

    def test_unknown_errors_and_other_tools_do_not_echo_output(self):
        for tool, stderr in (
            ('security', b'unknown diagnostic with secret-passphrase'),
            ('security', None),
            ('codesign', b'MAC verification failed during PKCS12 import secret-passphrase'),
        ):
            with self.subTest(tool=tool, stderr=stderr):
                result = subprocess.CompletedProcess([tool], 7, stderr=stderr)
                with patch.object(installer.subprocess, 'run', return_value=result):
                    with self.assertRaisesRegex(RuntimeError, '^' + tool + r' failed \(7\)$'):
                        installer.run([tool, '-P', 'secret-passphrase'], capture_output=True)

    def test_success_returns_the_original_result(self):
        result = subprocess.CompletedProcess(['security'], 0, stdout=b'imported')
        with patch.object(installer.subprocess, 'run', return_value=result):
            self.assertIs(installer.run(['security', 'import'], capture_output=True), result)

    def test_failed_import_restores_keychain_search_list_and_deletes_temporary_keychain(self):
        commands = []

        def execute(command, **kwargs):
            commands.append(command)
            if command[:2] == ['security', 'import']:
                return subprocess.CompletedProcess(command, 1, stderr=b'MAC verification failed during PKCS12 import')
            return subprocess.CompletedProcess(command, 0)

        environment = {'APPLE_CERTIFICATE_BASE64': 'dGVzdA==', 'APPLE_CERTIFICATE_PASSWORD': 'private-passphrase'}
        with patch.dict(installer.os.environ, environment, clear=True), \
             patch.object(installer.subprocess, 'check_output', return_value='"/existing/login.keychain-db"\n'), \
             patch.object(installer.subprocess, 'run', side_effect=execute):
            with self.assertRaisesRegex(RuntimeError, 'PKCS#12 MAC verification failed'):
                with installer.apple_keychain('self-signed'):
                    self.fail('failed import must not yield a signing environment')
        self.assertEqual(commands[-2], ['security', 'list-keychains', '-d', 'user', '-s', '/existing/login.keychain-db'])
        self.assertEqual(commands[-1][:2], ['security', 'delete-keychain'])
        self.assertFalse(Path(commands[-1][2]).parent.exists())

    def test_failed_keychain_cleanup_cannot_report_success(self):
        for failing in ('list-keychains', 'delete-keychain'):
            commands = []

            def execute(command, **kwargs):
                commands.append(command)
                restore = command[:5] == ['security', 'list-keychains', '-d', 'user', '-s'] and len(command) == 6
                failed = command[1] == failing and (restore or failing == 'delete-keychain')
                return subprocess.CompletedProcess(command, 1 if failed else 0, stderr=b'private detail')

            environment = {'APPLE_CERTIFICATE_BASE64': 'dGVzdA==', 'APPLE_CERTIFICATE_PASSWORD': 'private-passphrase'}
            with self.subTest(failing=failing), patch.dict(installer.os.environ, environment, clear=True), \
                 patch.object(installer.subprocess, 'check_output', return_value='"/existing/login.keychain-db"\n'), \
                 patch.object(installer.subprocess, 'run', side_effect=execute):
                with self.assertRaisesRegex(RuntimeError, r'^security failed \(1\)$'):
                    with installer.apple_keychain('self-signed'):
                        pass
            self.assertEqual(commands[-1][:2], ['security', 'delete-keychain'])


class DiskImageApplicationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bundle_dir = self.root / 'bundle'
        (self.bundle_dir / 'dmg').mkdir(parents=True)
        (self.bundle_dir / 'dmg/GChat.dmg').write_bytes(b'signed image')
        self.commands = []
        self.mount = None
        self.readonly = True
        self.wrong_mount = False
        self.detach_failure = False

    def execute(self, command, **kwargs):
        self.commands.append(command)
        if command[:2] == ['hdiutil', 'attach']:
            self.mount = Path(command[command.index('-mountpoint') + 1])
            app = self.mount / 'GChat.app'
            (app / 'Contents/MacOS').mkdir(parents=True)
            (app / 'Contents/Info.plist').write_bytes(plistlib.dumps({'CFBundleExecutable': 'gchat-desktop'}))
            (app / 'Contents/MacOS/gchat-desktop').write_bytes(b'signed executable')
            info = {'system-entities': [{'mount-point': str(self.root if self.wrong_mount else self.mount),
                                         'dev-entry': '/dev/disk7s1'}]}
            return subprocess.CompletedProcess(command, 0, stdout=plistlib.dumps(info))
        if command[:2] == ['hdiutil', 'detach'] and self.detach_failure:
            raise RuntimeError('hdiutil detach failed')
        if any(part.startswith('--extract-certificates=') for part in command):
            self.assertNotIn('--extract-certificates', command)
            prefix = next(part.split('=', 1)[1] for part in command if part.startswith('--extract-certificates='))
            Path(prefix + '0').write_bytes(b'pinned certificate')
        return subprocess.CompletedProcess(command, 0)

    def test_verifies_actual_shipped_application_and_detaches(self):
        with patch.object(installer, 'run', side_effect=self.execute), \
             patch.object(installer.os, 'statvfs', return_value=SimpleNamespace(f_flag=1), create=True), \
             patch.object(installer.os, 'ST_RDONLY', 1, create=True):
            with installer.application_from_dmg(self.bundle_dir) as app:
                self.assertEqual(app, self.mount / 'GChat.app')
                self.assertTrue((app / 'Contents/MacOS/gchat-desktop').is_file())
                self.assertFalse((self.bundle_dir / 'macos').exists())
        self.assertEqual(self.commands[0][:3], ['codesign', '--verify', '--strict'])
        self.assertIn('-readonly', self.commands[1])
        self.assertEqual(self.commands[-1], ['hdiutil', 'detach', str(self.mount)])
        self.assertFalse(self.mount.parent.exists())

    def test_bad_mount_writable_mount_and_verification_error_always_detach(self):
        for mode in ('wrong_mount', 'writable', 'verification_failure'):
            self.wrong_mount = mode == 'wrong_mount'
            with self.subTest(mode=mode), patch.object(installer, 'run', side_effect=self.execute), \
                 patch.object(installer.os, 'statvfs', return_value=SimpleNamespace(f_flag=0 if mode == 'writable' else 1), create=True), \
                 patch.object(installer.os, 'ST_RDONLY', 1, create=True):
                with self.assertRaisesRegex(ValueError, 'mountpoint|read-only|bad signature'):
                    with installer.application_from_dmg(self.bundle_dir):
                        raise ValueError('bad signature')
            self.assertEqual(self.commands[-1], ['hdiutil', 'detach', str(self.mount)])
            self.assertFalse(self.mount.parent.exists())

    def test_detach_failure_cannot_pass_or_remove_mounted_tree(self):
        self.detach_failure = True
        with patch.object(installer, 'run', side_effect=self.execute), \
             patch.object(installer.os, 'statvfs', return_value=SimpleNamespace(f_flag=1), create=True), \
             patch.object(installer.os, 'ST_RDONLY', 1, create=True):
            with self.assertRaisesRegex(RuntimeError, 'detach failed'):
                with installer.application_from_dmg(self.bundle_dir):
                    pass
        self.assertTrue(self.mount.is_dir())
        installer.shutil.rmtree(self.mount.parent)  # Only a fake mount in this fixture.

    def test_missing_or_multiple_images_are_refused_before_mount(self):
        for count in (0, 2):
            for item in (self.bundle_dir / 'dmg').iterdir():
                item.unlink()
            for index in range(count):
                (self.bundle_dir / f'dmg/{index}.dmg').write_bytes(b'image')
            with self.subTest(count=count), patch.object(installer, 'run') as run:
                with self.assertRaisesRegex(ValueError, 'one signed disk image'):
                    with installer.application_from_dmg(self.bundle_dir):
                        pass
                run.assert_not_called()

    def test_bundle_binds_mounted_executable_and_requires_pinned_leaf(self):
        for correct_pin in (True, False):
            output = self.root / str(correct_pin)
            output.mkdir()
            bundle_dir = output / 'build/aarch64-apple-darwin/release/bundle'
            identity = {'name': 'Gh0st', 'certificate_fingerprint':
                        hashlib.sha256(b'pinned certificate' if correct_pin else b'wrong').hexdigest()}

            def execute(command, **kwargs):
                if command[:3] == ['npm', 'run', 'tauri']:
                    (bundle_dir / 'dmg').mkdir(parents=True)
                    (bundle_dir / 'dmg/GChat.dmg').write_bytes(b'signed image')
                return self.execute(command, **kwargs)

            details = subprocess.CompletedProcess(['codesign'], 0, stderr='Authority=Gh0st\n')
            with self.subTest(correct_pin=correct_pin), patch.object(installer, 'run', side_effect=execute), \
                 patch.object(installer.subprocess, 'check_output', return_value=b'{}'), \
                 patch.object(installer.subprocess, 'run', return_value=details), \
                 patch.object(installer, 'verify_resolved_protocol'), \
                 patch.object(installer.os, 'statvfs', return_value=SimpleNamespace(f_flag=1), create=True), \
                 patch.object(installer.os, 'ST_RDONLY', 1, create=True):
                if correct_pin:
                    files, executables = installer.bundle('macos-aarch64', output, {}, identity, 'self-signed', self.root)
                    self.assertEqual(executables, [{'name': 'gchat-desktop',
                        'sha256': hashlib.sha256(b'signed executable').hexdigest(), 'size': 17}])
                    self.assertTrue(files[0]['signing_verified'])
                    self.assertEqual((output / 'GChat.dmg').read_bytes(), b'signed image')
                else:
                    with self.assertRaisesRegex(ValueError, 'certificate differs'):
                        installer.bundle('macos-aarch64', output, {}, identity, 'self-signed', self.root)
                    self.assertFalse((output / 'GChat.dmg').exists())
                self.assertFalse(self.mount.parent.exists())


class NsisApplicationTest(unittest.TestCase):
    def test_bundle_uses_shipped_signed_executable_instead_of_restored_unsigned_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'output'
            output.mkdir()
            target = output / 'build/x86_64-pc-windows-msvc/release'
            extracted = []

            def execute(command, **kwargs):
                if command[:3] == ['npm.cmd', 'run', 'tauri']:
                    (target / 'bundle/nsis').mkdir(parents=True)
                    (target / 'bundle/nsis/GChat.exe').write_bytes(b'signed installer')
                    (target / 'gchat-desktop.exe').write_bytes(b'unsigned restored build copy')
                elif command[:2] == ['7z.exe', 'x']:
                    destination = Path(next(x[2:] for x in command if x.startswith('-o')))
                    binary = destination / 'gchat-desktop.exe'
                    binary.write_bytes(b'actual signed packaged executable')
                    extracted.append(binary)
                return subprocess.CompletedProcess(command, 0)

            def verify(path, policy):
                self.assertNotEqual(path, target / 'gchat-desktop.exe')
                self.assertIn(path.read_bytes(), (b'signed installer', b'actual signed packaged executable'))

            with patch.object(installer, 'run', side_effect=execute), \
                 patch.object(installer.shutil, 'which', return_value='7z.exe'), \
                 patch.object(installer, 'fingerprint', return_value='A' * 40), \
                 patch.object(installer, 'verify_windows', side_effect=verify), \
                 patch.object(installer, 'verify_resolved_protocol'), \
                 patch.object(installer.subprocess, 'check_output', return_value=b'{}'):
                files, executables = installer.bundle('windows-x86_64', output, {},
                    {'name': 'Gh0st'}, 'self-signed', root)
            self.assertEqual(executables, [{'name': 'gchat-desktop.exe',
                'sha256': hashlib.sha256(b'actual signed packaged executable').hexdigest(),
                'size': len(b'actual signed packaged executable')}])
            self.assertEqual((output / files[0]['name']).read_bytes(), b'signed installer')
            self.assertFalse(extracted[0].exists())

    def test_missing_duplicate_or_bad_signature_cannot_substitute_build_copy(self):
        for count in (0, 2):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / 'nsis').mkdir()
                (root / 'nsis/GChat.exe').write_bytes(b'installer')

                def extract(command, **kwargs):
                    destination = Path(next(x[2:] for x in command if x.startswith('-o')))
                    for n in range(count):
                        path = destination / str(n) / 'gchat-desktop.exe'
                        path.parent.mkdir()
                        path.write_bytes(b'executable')

                with patch.object(installer, 'verify_windows'), \
                     patch.object(installer.shutil, 'which', return_value='7z.exe'), \
                     patch.object(installer, 'run', side_effect=extract):
                    with self.assertRaisesRegex(ValueError, 'exactly one'):
                        with installer.application_from_nsis(root, 'self-signed'):
                            self.fail('invalid NSIS contents accepted')
                with patch.object(installer, 'verify_windows', side_effect=ValueError('bad signature')), \
                     patch.object(installer, 'run') as run:
                    with self.assertRaisesRegex(ValueError, 'bad signature'):
                        with installer.application_from_nsis(root, 'self-signed'):
                            self.fail('invalid NSIS signature accepted')
                    run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
