import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from release_feed import minisign_verify, publish
from release_pair import canonical
from release_automation_test import candidate

@unittest.skipUnless(os.name == 'posix' and shutil.which('minisign'), 'POSIX publisher and native minisign required for signed-feed qualification')
class FeedTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.key=self.root/'key';public=self.root/'key.pub'
        subprocess.run(['minisign','-G','-W','-s',str(self.key),'-p',str(public)],check=True,capture_output=True)
        self.public=base64.b64encode(public.read_bytes()).decode()
        self.payload=self.root/'GChat.AppImage';self.payload.write_bytes(b'qualified immutable app')
        self.signature=self.sign(self.payload)
        self.manifest=candidate();self.manifest['versions']['linux-x86_64']='1.0.1'
        self.manifest['release_id']=hashlib.sha256(canonical({k:v for k,v in self.manifest.items() if k!='release_id'})).hexdigest()
        for stage in ['verify','compatibility']:
            (self.root/(stage+'.json')).write_text(json.dumps({'schema':1,'stage':stage,'release_id':self.manifest['release_id'],
                'sources':self.manifest['sources'],'platform':'linux-x86_64','passed':True,'source_unchanged':True,'relay_compatible':True,
                'evidence':[{'path':self.payload.name,'sha256':hashlib.sha256(self.payload.read_bytes()).hexdigest()}]}))
        self.signer=self.root/'sign.py'
        self.signer.write_text('import base64,pathlib,subprocess,sys\np=pathlib.Path(sys.argv[1]);subprocess.run(["minisign","-S","-s",'+repr(str(self.key))+',"-m",str(p)],check=True,capture_output=True);p.with_suffix(p.suffix+".sig").write_bytes(base64.b64encode(pathlib.Path(str(p)+".minisig").read_bytes()))\n')
    def sign(self,path):
        subprocess.run(['minisign','-S','-s',str(self.key),'-m',str(path)],check=True,capture_output=True)
        return base64.b64encode(Path(str(path)+'.minisig').read_bytes()).decode()
    def publish(self):
        return publish(self.manifest,'linux-x86_64',self.payload,self.signature,self.root/'public','https://gchat.example/updates',
                       self.public,[sys.executable,str(self.signer)],self.root/'verify.json',self.root/'compatibility.json')
    def test_verified_feed_is_idempotent_and_metadata_is_signed(self):
        first=self.publish();self.assertEqual(first,self.publish())
        binding=self.root/'binding';binding.write_text(first['binding'])
        minisign_verify(binding,first['binding_signature'],self.public)
        binding.write_text(first['binding'].replace('1.0.1','9.0.1'))
        with self.assertRaises(subprocess.CalledProcessError):minisign_verify(binding,first['binding_signature'],self.public)
    def test_artifact_substitution_and_missing_compatibility_fail(self):
        self.payload.write_bytes(b'changed')
        with self.assertRaises(ValueError):self.publish()
    def test_same_version_different_release_never_replaces_pointer(self):
        self.publish();path=self.root/'public/desktop/linux/x86_64/latest.json';before=path.read_bytes()
        self.manifest['policy']['new']='policy';self.manifest['release_id']=hashlib.sha256(canonical({k:v for k,v in self.manifest.items() if k!='release_id'})).hexdigest()
        for stage in ['verify','compatibility']:
            p=self.root/(stage+'.json');v=json.loads(p.read_text());v['release_id']=self.manifest['release_id'];p.write_text(json.dumps(v))
        with self.assertRaises(ValueError):self.publish()
        self.assertEqual(path.read_bytes(),before)
    def test_idempotent_retry_detects_missing_public_payload(self):
        self.publish()
        next((self.root/'public/artifacts').rglob('*.AppImage')).unlink()
        with self.assertRaisesRegex(ValueError,'missing or changed'):self.publish()
