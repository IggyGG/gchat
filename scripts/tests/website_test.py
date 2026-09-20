import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest

spec = importlib.util.spec_from_file_location('website', Path(__file__).resolve().parents[1] / 'website.py')
site = importlib.util.module_from_spec(spec); spec.loader.exec_module(site)

class WebsiteTests(unittest.TestCase):
    def manifest(self):
        base = 'https://github.com/IggyGG/gchat/releases/download/v0.1.0/'
        return {'schema':1, 'version':'0.1.0', 'channel':'developer-preview', 'release_key':{'url':base+'gchat-release-key.asc','sha256':'b'*64,'fingerprint':'C'*40}, 'artifacts':[
            {'target':target, 'format':fmt, 'url':base+target+'.'+fmt, 'signature_url':base+target+'.'+fmt+'.asc', 'sha256':'a'*64, 'signature_sha256':'b'*64, 'signing_verified':True}
            for target,fmt in site.TARGETS]}

    def test_no_release_has_no_fabricated_downloads(self):
        data = site.validate({'schema':1,'version':None,'channel':'developer-preview','artifacts':[]})
        with tempfile.TemporaryDirectory() as temp:
            site.build(Path(temp), data)
            page = (Path(temp)/'index.html').read_text()
            self.assertNotIn('/releases/download/', page)
            self.assertNotIn('@@', page)
            self.assertTrue('Network and conversation invitations are separate' in page)
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
