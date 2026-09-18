import importlib.util
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


class DeploymentTests(unittest.TestCase):
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
            home = Path(temp); home.chmod(0o700)
            command = ['gpg', '--homedir', str(home), '--batch']
            subprocess.run(command + ['--passphrase', '', '--quick-generate-key', 'GChat disposable test key', 'ed25519', 'sign', '1d'], check=True, capture_output=True)
            listing = subprocess.check_output(command + ['--with-colons', '--list-keys'], text=True, stderr=subprocess.DEVNULL)
            key = next(line.split(':')[9] for line in listing.splitlines() if line.startswith('fpr:'))
            path = home/'artifact'; path.write_bytes(b'qualified fixture')
            sig = home/'artifact.asc'
            subprocess.run(command + ['--armor', '--detach-sign', str(path)], check=True, capture_output=True)
            verify(sig, path, key, home)
            with self.assertRaises(ValueError): verify(sig, path, 'B'*40, home)
            path.write_bytes(b'tampered bytes')
            with self.assertRaises(ValueError): verify(sig, path, key, home)
