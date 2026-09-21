"""Publisher display names and native signing identities are distinct."""
import importlib.util
import json
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


if __name__ == "__main__":
    unittest.main()
