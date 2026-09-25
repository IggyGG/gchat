import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from release_coordinator import Coordinator, atomic_json, read_receipt
from release_jobs import extract
from release_compatibility import verify
from release_automation_test import candidate

class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.manifest=candidate()
    def receipt(self,folder,stage='build'):
        folder.mkdir(parents=True,exist_ok=True);(folder/'evidence').write_text('checked')
        report={'schema':1,'release_id':self.manifest['release_id'],'sources':self.manifest['sources'],
                'platform':'android','stage':stage,'passed':True,'source_unchanged':True,
                'evidence':[{'path':'evidence','sha256':hashlib.sha256(b'checked').hexdigest()}]}
        atomic_json(folder/'receipt.json',report);return report
    def test_hash_tamper_and_escape_fail(self):
        report=self.receipt(self.root)
        read_receipt(self.root/'receipt.json',self.manifest,'android','build')
        (self.root/'evidence').write_text('changed')
        with self.assertRaises(ValueError):read_receipt(self.root/'receipt.json',self.manifest,'android','build')
        report['evidence'][0]['path']='../outside';atomic_json(self.root/'receipt.json',report)
        with self.assertRaises(ValueError):read_receipt(self.root/'receipt.json',self.manifest,'android','build')
    def test_completed_receipt_after_crash_confirms_without_dispatch(self):
        c=Coordinator(self.root,{'minimum_free_bytes':0,'workers':{'android':{'build':{'run':['must-not-run']}}}});self.addCleanup(c.ledger.close)
        release=c.ledger.add(self.manifest);effect=c.ledger.effect(release,'android','build')
        self.receipt(self.root/'jobs'/effect['id'])
        with patch('release_coordinator.subprocess.run',side_effect=AssertionError('duplicate external request')):
            c.step(release,'android')
        self.assertEqual(c.ledger.target(release,'android')['state'],'verifying')
        self.assertEqual(c.ledger.effect(release,'android','build')['state'],'confirmed')
    def test_lost_worker_reply_uses_reconcile_only(self):
        c=Coordinator(self.root,{'minimum_free_bytes':0,'workers':{'android':{'build':{'run':['first'],'reconcile':['recover']}}}});self.addCleanup(c.ledger.close)
        release=c.ledger.add(self.manifest);seen=[]
        def launch(argv,**kwargs):
            seen.append(argv)
            if len(seen)==1:raise TimeoutError('lost reply')
            return type('Result',(),{'returncode':75})()
        with patch('release_coordinator.subprocess.run',side_effect=launch):
            c.step(release,'android')
            self.assertEqual(c.ledger.target(release,'android')['state'],'blocked')
            c.ledger.transition(release,'android','building');c.step(release,'android')
        self.assertEqual(seen,[['first'],['recover']])
    def test_archive_traversal_and_symlink_rejected(self):
        import zipfile
        for name in ('../escape','/absolute','C:/windows','back\\slash','file:stream','file\0hidden'):
            archive=self.root/'bad.zip'
            entry=zipfile.ZipInfo('fixture');entry.filename=name
            with zipfile.ZipFile(archive,'w') as z:z.writestr(entry,b'bad')
            with self.assertRaises(ValueError):extract(archive,self.root/'out')
            self.assertFalse((self.root.parent/'escape').exists())
    def test_component_pass_cannot_qualify_production(self):
        manifest=self.manifest
        manifest['policy']={'carrier_profile':46,'required_checks':['durable_delivery','reopen_recovery']}
        with self.assertRaises(ValueError):verify({'schema':1,'passed':True},manifest,100)
        proof={'schema':1,'passed':True,'sources':manifest['sources'],'release_id':manifest['release_id'],
               'carrier_profile':46,'completed_at':100,'checks':{'durable_delivery':True,'reopen_recovery':True},
               'relays':[{'id':str(i),'gcoms_commit':manifest['sources']['gcoms']['commit'],'carrier_profile':46,'healthy':True} for i in range(8)],
               'rollback_state_compatible':True}
        verify(proof,manifest,101)
        proof['checks']['reopen_recovery']=False
        with self.assertRaises(ValueError):verify(proof,manifest,101)

    def test_bad_incoming_manifest_does_not_block_other_candidates(self):
        c=Coordinator(self.root,{'workers':{}});self.addCleanup(c.ledger.close)
        incoming=self.root/'incoming';incoming.mkdir();(incoming/'bad.json').write_text('{invalid')
        atomic_json(incoming/'good.json',self.manifest)
        c.tick()
        self.assertEqual(len(list((self.root/'rejected').glob('*'))),1)
        self.assertEqual(c.ledger.target(self.manifest['release_id'],'android')['state'],'blocked')
        self.assertTrue((self.root/'public/status.json').exists())
