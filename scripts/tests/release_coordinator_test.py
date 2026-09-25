import copy
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

    def test_bounded_file_gate_rejects_missing_late_or_incomplete_recovery(self):
        from release_compatibility import verify_file_check
        policy=json.loads((Path(__file__).resolve().parents[2]/'release/automation/policy.json').read_text())['file_qualification']
        proof={'mode':'file-recovery','bytes':16777216,'completion_elapsed_seconds':30,
               'total_elapsed_seconds':120,'source_sha256':'a'*64,'export_sha256':'a'*64,
               'abrupt_stop':True,'verified_pieces_retained':True,'same_identity':True,
               'authenticated_chat_ack':True,'hash_verified_after_reopen':True,'cleanup_complete':True}
        verify_file_check(proof,policy)
        for field, bad in [('bytes',1073741824),('bytes',True),('mode','smoke'),
                           ('completion_elapsed_seconds',181),('total_elapsed_seconds',601),
                           ('completion_elapsed_seconds',float('nan')),('total_elapsed_seconds',float('inf')),
                           ('completion_elapsed_seconds',True),('completion_elapsed_seconds',0),
                           ('export_sha256','b'*64),('source_sha256','invalid')]:
            with self.subTest(field=field,value=bad),self.assertRaises(ValueError):
                verify_file_check({**proof,field:bad},policy)
        for field in ('abrupt_stop','verified_pieces_retained','same_identity',
                      'authenticated_chat_ack','hash_verified_after_reopen','cleanup_complete'):
            with self.subTest(field=field),self.assertRaises(ValueError):
                verify_file_check({**proof,field:False},policy)
        with self.assertRaises(ValueError):verify_file_check(None,policy)
        with self.assertRaises(ValueError):verify_file_check({**proof,'total_elapsed_seconds':10},policy)
        manifest=copy.deepcopy(self.manifest)
        manifest['policy']={'carrier_profile':46,'required_checks':['files'],'file_qualification':policy}
        acceptance={'schema':1,'passed':True,'sources':manifest['sources'],'release_id':manifest['release_id'],
                    'carrier_profile':46,'completed_at':100,'checks':{'files':True},
                    'relays':[{'id':str(i),'gcoms_commit':manifest['sources']['gcoms']['commit'],
                               'carrier_profile':46,'healthy':True} for i in range(8)],
                    'rollback_state_compatible':True,'large_file_campaign':{'passed':False,'failure':'deadline'}}
        with self.assertRaises(ValueError):verify(acceptance,manifest,101)
        acceptance['file_check']=proof
        verify(acceptance,manifest,101)  # Separate capacity failure does not veto the bounded pass.

    def test_bad_incoming_manifest_does_not_block_other_candidates(self):
        c=Coordinator(self.root,{'workers':{}});self.addCleanup(c.ledger.close)
        incoming=self.root/'incoming';incoming.mkdir();(incoming/'bad.json').write_text('{invalid')
        atomic_json(incoming/'good.json',self.manifest)
        c.tick()
        self.assertEqual(len(list((self.root/'rejected').glob('*'))),1)
        self.assertEqual(c.ledger.target(self.manifest['release_id'],'android')['state'],'blocked')
        self.assertTrue((self.root/'public/status.json').exists())

    def test_busy_platform_coalesces_updates_without_blocking_other_platforms(self):
        c=Coordinator(self.root,{'workers':{'android':{},'ios':{}}})
        self.addCleanup(c.ledger.close)
        first=c.ledger.add(candidate(1));c.ledger.transition(first,'android','building')
        second=c.ledger.add(candidate(2))
        with patch.object(c,'execute',return_value=None) as execute:
            c.step(second,'android')
            execute.assert_not_called()
            self.assertEqual(c.ledger.target(second,'android')['state'],'queued')
            third=c.ledger.add(candidate(3));c.ledger.coalesce()
            self.assertEqual(c.ledger.target(second,'android')['state'],'superseded')
            self.assertEqual(c.ledger.target(first,'android')['state'],'building')
            c.step(third,'ios')
            self.assertEqual(execute.call_args.args[1:3],('ios','build'))
            execute.reset_mock()
            c.ledger.transition(first,'android','verifying');c.step(third,'android')
            execute.assert_not_called()
            c.ledger.transition(first,'android','verified',evidence='a'*64)
            c.step(third,'android')
            self.assertEqual(execute.call_args.args[0]['release_id'],third)
            self.assertEqual(execute.call_args.args[1:3],('android','build'))
