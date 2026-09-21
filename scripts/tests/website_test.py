import copy
import hashlib
import io
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
from unittest.mock import patch
from urllib.error import HTTPError
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest

spec = importlib.util.spec_from_file_location('website', Path(__file__).resolve().parents[1] / 'website.py')
site = importlib.util.module_from_spec(spec); spec.loader.exec_module(site)

class WebsiteTests(unittest.TestCase):
    def test_source_head_retry_preserves_method(self):
        url = 'https://github.com/IggyGG/gchat'
        with patch.object(site, 'urlopen', side_effect=[HTTPError(url, 504, 'fixture', {}, None), io.BytesIO()]) as fetch:
            with site.open_public(url, timeout=30, method='HEAD'):
                pass
            self.assertEqual([call.args[0].get_method() for call in fetch.call_args_list], ['HEAD', 'HEAD'])
            self.assertTrue(fetch.call_args_list[1].args[0].full_url.startswith(url + '?gchat-verification='))

    def test_gateway_retry_keeps_exact_asset_digest(self):
        url = 'https://github.com/IggyGG/gchat/releases/download/v0.1.4/key.asc'
        raw = b'public fixture bytes'
        with tempfile.TemporaryDirectory() as temp, patch.object(site, 'urlopen', side_effect=[
                HTTPError(url, 504, 'cached gateway error', {}, None), io.BytesIO(raw)]) as fetch:
            output = Path(temp) / 'asset'
            site.fetch(url, hashlib.sha256(raw).hexdigest(), output)
            self.assertEqual(output.read_bytes(), raw)
            self.assertEqual(fetch.call_args_list[0].args[0], url)
            self.assertTrue(fetch.call_args_list[1].args[0].startswith(url + '?gchat-verification='))
            self.assertEqual(fetch.call_count, 2)

    def test_gateway_retry_is_bounded_and_other_errors_stay_failures(self):
        for code, calls in ((504, 2), (404, 1), (401, 1)):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as temp, patch.object(
                    site, 'urlopen', side_effect=HTTPError('https://github.com/asset', code, 'fixture', {}, None)) as fetch:
                with self.assertRaises(HTTPError): site.fetch('https://github.com/asset', '0' * 64, Path(temp) / 'asset')
                self.assertEqual(fetch.call_count, calls)

    def test_checksum_mismatch_is_not_retried(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(site, 'urlopen', return_value=io.BytesIO(b'wrong')) as fetch:
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                site.fetch('https://github.com/asset', '0' * 64, Path(temp) / 'asset')
            self.assertEqual(fetch.call_count, 1)

    def manifest(self):
        base = 'https://github.com/IggyGG/gchat/releases/download/v0.1.0/'
        return {'schema':1, 'version':'0.1.0', 'channel':'developer-preview', 'release_key':{'url':base+'gchat-release-key.asc','sha256':'b'*64,'fingerprint':'C'*40}, 'artifacts':[
            {'target':target, 'format':fmt, 'url':base+target+'.'+fmt, 'signature_url':base+target+'.'+fmt+'.asc', 'sha256':'a'*64, 'signature_sha256':'b'*64, 'signing_verified':True}
            for target,fmt in site.TARGETS if (target,fmt) in site.DESKTOP_TARGETS]}

    def test_no_release_has_no_fabricated_downloads(self):
        data = site.validate({'schema':1,'version':None,'channel':'developer-preview','artifacts':[]})
        with tempfile.TemporaryDirectory() as temp:
            site.build(Path(temp), data)
            page = (Path(temp)/'index.html').read_text()
            self.assertNotIn('/releases/download/', page)
            self.assertNotIn('@@', page)
            self.assertIn('network and channel together', page)
            self.assertTrue((Path(temp)/'fonts/LICENSE-CC0').is_file())

    def test_partial_unsigned_mutable_and_injected_downloads_fail(self):
        for mutate in [lambda d:d['artifacts'].pop(), lambda d:d['artifacts'][0].update(signing_verified=False),
                       lambda d:d['artifacts'][0].update(url='https://evil.example/a'),
                       lambda d:d['artifacts'][0].update(url=d['artifacts'][0]['url']+'?x=1'),
                       lambda d:d['artifacts'][0].update(sha256='bad'),
                       lambda d:d.update(version='<script>')]:
            data=self.manifest();mutate(data)
            with self.assertRaises(ValueError): site.validate(data)

    def test_complete_release_has_explicit_platforms_and_signatures(self):
        data=site.validate(self.manifest()); page=site.downloads(data)
        self.assertEqual(page.count('>Download '), 5)
        self.assertEqual(page.count('>Signature</a>'), 5)

    def test_production_linux_scope_is_explicit_and_keeps_signature_checks(self):
        data=self.manifest();data['channel']='production'
        data['artifacts']=[a for a in data['artifacts'] if a['target']=='linux-x86_64']
        site.validate(data)
        self.assertIn('Production 0.1.0',site.downloads(data))
        data['artifacts'][0]['signing_verified']=False
        with self.assertRaises(ValueError):site.validate(data)

    def test_production_adds_verified_platforms_without_hiding_linux(self):
        data = self.manifest(); data['channel'] = 'production'
        data['artifacts'].append({**data['artifacts'][0], 'target': 'android-arm64', 'format': 'apk',
            'url': 'https://github.com/IggyGG/gchat/releases/download/v0.1.0/GChat-arm64.apk',
            'signature_url': 'https://github.com/IggyGG/gchat/releases/download/v0.1.0/GChat-arm64.apk.asc'})
        site.validate(data)
        with tempfile.TemporaryDirectory() as temp:
            site.build(Path(temp), data)
            page = (Path(temp) / 'index.html').read_text(encoding='utf-8')
            self.assertIn('Linux, macOS, Windows, Android', page)
            self.assertIn('Android · ARM64 APK', page)
            self.assertNotIn('packages are deferred', page)
        for mutation in ('unverified', 'duplicate', 'incomplete_linux', 'unknown_target'):
            changed = copy.deepcopy(data)
            if mutation == 'unverified': changed['artifacts'][-1]['signing_verified'] = False
            elif mutation == 'duplicate': changed['artifacts'].append(changed['artifacts'][-1])
            elif mutation == 'incomplete_linux': changed['artifacts'] = [a for a in changed['artifacts'] if a['format'] != 'deb']
            else: changed['artifacts'][-1]['target'] = 'ios-arm64'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): site.validate(changed)

    def test_status_names_only_available_downloads(self):
        data = self.manifest(); data['channel'] = 'production'
        data['artifacts'] = [a for a in data['artifacts'] if a['target'] == 'linux-x86_64']
        status = site.client_status(site.validate(data))
        self.assertIn('for Linux.', status)
        self.assertNotIn('macOS', status)
        self.assertNotIn('Android', status)
