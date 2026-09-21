import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from release_signatures import verify, check_status
import website


def module(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), SCRIPTS / (name + '.py'))
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


deploy = module('deploy-website')
publish = module('publish-release')


def gpg_fixture_path(path, executable, windows=os.name == 'nt'):
    # Git for Windows bundles MSYS GnuPG, whose native API rejects C:\ paths.
    # Use that same installation's converter; native Gpg4win needs no conversion.
    converter = Path(executable).with_name('cygpath.exe')
    if windows and converter.is_file():
        result = subprocess.run([str(converter), '--unix', '--absolute', str(path)],
                                capture_output=True, timeout=15)
        converted = result.stdout.decode('utf-8').strip()
        if result.returncode or not converted.startswith('/'):
            raise RuntimeError('GnuPG fixture path conversion failed: '
                               + result.stderr.decode('utf-8', errors='replace'))
        return converted
    return str(path)


class GnuPGFixturePathTests(unittest.TestCase):
    def test_msys_paths_use_the_matching_installation_converter(self):
        source = r'C:\Users\Test User\keyring'
        result = subprocess.CompletedProcess([], 0, b'/c/Users/Test User/keyring\n', b'')
        with patch.object(Path, 'is_file', return_value=True), \
             patch.object(subprocess, 'run', return_value=result) as run:
            self.assertEqual(gpg_fixture_path(source, '/git/usr/bin/gpg.exe', True),
                             '/c/Users/Test User/keyring')
        self.assertEqual(run.call_args.args[0],
                         [str(Path('/git/usr/bin/cygpath.exe')), '--unix', '--absolute', source])

    def test_native_tool_paths_are_not_rewritten(self):
        with patch.object(Path, 'is_file', return_value=False), \
             patch.object(subprocess, 'run') as run:
            self.assertEqual(gpg_fixture_path(r'C:\keys', '/native/gpg.exe', True), r'C:\keys')
            self.assertEqual(gpg_fixture_path('/keys', '/usr/bin/gpg', False), '/keys')
        run.assert_not_called()

    def test_converter_error_is_not_replaced_with_a_guessed_path(self):
        result = subprocess.CompletedProcess([], 1, b'', b'conversion refused')
        with patch.object(Path, 'is_file', return_value=True), \
             patch.object(subprocess, 'run', return_value=result):
            with self.assertRaisesRegex(RuntimeError, 'conversion refused'):
                gpg_fixture_path(r'C:\keys', '/git/usr/bin/gpg.exe', True)


class DeploymentTests(unittest.TestCase):
    def test_website_is_utf8_with_hash_bound_bytes_under_non_utf8_locale(self):
        open_path = Path.open
        def cp1252_default(path, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
            if 'b' not in mode and encoding in (None, 'locale'):
                encoding = 'cp1252'
            return open_path(path, mode, buffering, encoding, errors, newline)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(Path, 'open', cp1252_default):
                website.build(root, {'schema': 1, 'version': None, 'artifacts': []})
            rendered = (root / 'index.html').read_bytes()
            self.assertIn('GChat', rendered.decode('utf-8'))
            self.assertNotIn(b'\r\n', rendered)
            report = json.loads((root / 'build.json').read_text(encoding='utf-8'))
            self.assertEqual(report['index_sha256'], hashlib.sha256(rendered).hexdigest())
            deploy.bundle(root, 'a' * 40)

    def test_changed_content_cannot_reuse_active_version_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            website.build(root, {'schema':1, 'version':None, 'artifacts':[]})
            first = deploy.bundle(root, 'a'*40)[0]
            self.assertEqual(first, deploy.bundle(root, 'a'*40)[0])
            (root/'fonts/LICENSE-CC0').write_text('different retained license')
            self.assertNotEqual(first, deploy.bundle(root, 'a'*40)[0])

    def test_unexpected_files_symlinks_and_stale_reports_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            website.build(root, {'schema':1, 'version':None, 'artifacts':[]})
            extra = root/'credential.txt'; extra.write_text('fixture')
            with self.assertRaises(ValueError): deploy.bundle(root, 'a'*40)
            extra.unlink()
            link = root/'fonts/link'; link.symlink_to(root/'index.html')
            with self.assertRaises(ValueError): deploy.bundle(root, 'a'*40)
            link.unlink()
            (root/'index.html').write_text('changed after rendering')
            with self.assertRaises(ValueError): deploy.bundle(root, 'a'*40)


class PublicationTests(unittest.TestCase):
    def test_authenticated_assets_cannot_change_origin_or_downgrade(self):
        with patch.dict(os.environ, {'FORGEJO_TOKEN':'test-placeholder', 'FORGEJO_API_URL':'https://forgejo.example/api/v1'}):
            client = publish.Forgejo()
            for url in ('http://forgejo.example/file', 'https://other.example/file', 'https://user@forgejo.example/file'):
                with self.assertRaises(ValueError): client.asset_hash(url)

    def test_authenticated_redirects_are_refused(self):
        with self.assertRaises(ValueError):
            publish.NoRedirect().redirect_request(None, None, 302, None, {}, 'https://other.example/')

    def test_expired_signatures_and_unconfigured_keys_fail_closed(self):
        key = 'A'*40
        valid = '[GNUPG:] VALIDSIG '+key+' 2026-09-18 1 0 4 0 22 8 00 '+key+'\n'
        result = subprocess.CompletedProcess([], 0, valid, '')
        check_status(result, key)
        for status in ('EXPKEYSIG', 'REVKEYSIG', 'BADSIG', 'KEYEXPIRED'):
            result.stdout = valid + '[GNUPG:] '+status+' fixture\n'
            with self.assertRaises(ValueError): check_status(result, key)
        result.stdout = valid
        with self.assertRaises(ValueError): check_status(result, 'B'*40)
        with self.assertRaises(ValueError): check_status(result, None)


@unittest.skipUnless(shutil.which('gpg'), 'GnuPG required for signature verification integration')
class SignatureTests(unittest.TestCase):
    def test_real_signature_rejects_tampered_bytes_and_other_publisher(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp).resolve(); home.chmod(0o700)
            executable = shutil.which('gpg')
            version = subprocess.run([executable, '--version'], capture_output=True, timeout=15)
            diagnostics = (f'GnuPG executable: {executable}\n'
                           + version.stdout.decode('utf-8', errors='replace')
                           + version.stderr.decode('utf-8', errors='replace'))
            self.assertEqual(version.returncode, 0, diagnostics)
            print(diagnostics, file=sys.stderr)
            tool_home = gpg_fixture_path(home, executable)
            command = [executable, '--homedir', tool_home, '--batch', '--pinentry-mode', 'loopback']
            def require_success(result):
                self.assertEqual(result.returncode, 0, diagnostics + '\n'
                                 + result.stderr.decode('utf-8', errors='replace'))
            # Batch parameters avoid empty-passphrase argv parsing differences
            # in Windows GnuPG. This unprotected key is disposable test data.
            parameters = ("Key-Type: eddsa\nKey-Curve: ed25519\nKey-Usage: sign\n"
                          "Name-Real: GChat disposable test key\nExpire-Date: 1d\n"
                          "%no-protection\n%commit\n")
            try:
                result = subprocess.run(command + ['--generate-key'], input=parameters.encode('ascii'),
                                        capture_output=True, timeout=60)
                require_success(result)
                result = subprocess.run(command + ['--with-colons', '--list-keys'],
                                        capture_output=True, timeout=30)
                require_success(result)
                key = next(line.split(':')[9] for line in result.stdout.decode('utf-8').splitlines()
                           if line.startswith('fpr:'))
                path = home/'artifact'; path.write_bytes(b'qualified fixture')
                sig = home/'artifact.asc'
                tool_path = gpg_fixture_path(path, executable)
                tool_sig = gpg_fixture_path(sig, executable)
                result = subprocess.run(command + ['--armor', '--detach-sign', tool_path],
                                        capture_output=True, timeout=30)
                require_success(result)
                verify(tool_sig, tool_path, key, tool_home)
                with self.assertRaises(ValueError): verify(tool_sig, tool_path, 'B'*40, tool_home)
                path.write_bytes(b'tampered bytes')
                with self.assertRaises(ValueError): verify(tool_sig, tool_path, key, tool_home)
            finally:
                # Windows cannot remove keyring files held by our test agent.
                sibling = Path(executable).with_name('gpgconf.exe' if os.name == 'nt' else 'gpgconf')
                gpgconf = str(sibling) if sibling.is_file() else shutil.which('gpgconf')
                if gpgconf:
                    result = subprocess.run([gpgconf, '--homedir', tool_home, '--kill', 'gpg-agent'],
                                            capture_output=True, timeout=15)
                    require_success(result)
