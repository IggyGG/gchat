import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from release_coordinator import Coordinator, StorageHeadroomError, STORAGE_HEADROOM_REASON, atomic_json, read_receipt
from release_pair import canonical
from release_jobs import extract
from release_compatibility import verify
from release_automation_test import candidate

class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.manifest=candidate()

    @unittest.skipUnless(os.name == 'posix', 'controller uses POSIX process groups')
    def test_nonblocking_worker_does_not_prevent_another_platform_and_reconciles_same_effect(self):
        import sys
        import time
        script = self.root / 'async.py'
        release_worker = self.root / 'release-worker'
        script.write_text('import time\nfrom pathlib import Path\nwhile not Path(' +
                          repr(str(release_worker)) + ').exists(): time.sleep(0.01)\nraise SystemExit(75)\n')
        recipe = {'run': [sys.executable, str(script)], 'reconcile': [sys.executable, str(script)], 'timeout': 10}
        c = Coordinator(self.root, {'nonblocking_workers': True, 'maximum_workers': 2,
            'workers': {p: {'build': recipe} for p in ('linux-x86_64', 'windows-x86_64')}})
        self.addCleanup(c.ledger.close)
        self.addCleanup(c.close_workers)
        c.ledger.add(self.manifest)
        started = time.monotonic()
        self.assertIsNone(c.execute(self.manifest, 'linux-x86_64', 'build'))
        self.assertIsNone(c.execute(self.manifest, 'windows-x86_64', 'build'))
        self.assertLess(time.monotonic() - started, 0.5)
        self.assertEqual(len(c.running_workers), 2)
        effect = c.ledger.effect(self.manifest['release_id'], 'linux-x86_64', 'build')
        pid = c.running_workers[effect['id']]['process'].pid
        self.assertIsNone(c.execute(self.manifest, 'linux-x86_64', 'build'))
        self.assertEqual(c.running_workers[effect['id']]['process'].pid, pid)
        release_worker.touch()
        c.running_workers[effect['id']]['process'].wait(timeout=5)
        self.assertIsNone(c.execute(self.manifest, 'linux-x86_64', 'build'))
        self.assertNotIn(effect['id'], c.running_workers)
        self.assertEqual(c.ledger.effect(self.manifest['release_id'], 'linux-x86_64', 'build')['id'], effect['id'])

    @unittest.skipUnless(os.name == 'posix', 'controller uses POSIX process groups')
    def test_nonblocking_worker_zero_exit_without_receipt_cannot_pass(self):
        import sys
        recipe = {'run': [sys.executable, '-c', 'pass'], 'reconcile': [sys.executable, '-c', 'pass']}
        c = Coordinator(self.root, {'nonblocking_workers': True, 'workers': {'linux-x86_64': {'build': recipe}}})
        self.addCleanup(c.ledger.close)
        self.addCleanup(c.close_workers)
        c.ledger.add(self.manifest)
        c.execute(self.manifest, 'linux-x86_64', 'build')
        next(iter(c.running_workers.values()))['process'].wait(timeout=5)
        with self.assertRaisesRegex(ValueError, 'without a source-bound receipt'):
            c.execute(self.manifest, 'linux-x86_64', 'build')

    def test_invalid_worker_limits_do_not_create_release_state(self):
        for value in (0, 9, True, '3'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Coordinator(self.root / 'unused', {'maximum_workers': value})
            self.assertFalse((self.root / 'unused').exists())
    def test_invalid_poll_interval_cannot_create_release_state(self):
        for interval in (0, 9, 301, True, 0.5, '30', None):
            state=self.root / 'unused'
            with self.subTest(interval=interval),self.assertRaisesRegex(ValueError,'poll_interval_seconds'):
                Coordinator(state,{'poll_interval_seconds':interval})
            self.assertFalse(state.exists())

    def test_required_deployment_blocks_even_a_verified_platform(self):
        from release_pair import canonical
        manifest=copy.deepcopy(self.manifest)
        manifest['policy']['deployment_required']=True
        manifest['release_id']=hashlib.sha256(canonical({k:v for k,v in manifest.items() if k!='release_id'})).hexdigest()
        platforms=('android','ios','linux-x86_64','macos-aarch64','macos-x86_64','windows-x86_64')
        c=Coordinator(self.root,{'workers':{p:{} for p in platforms}});self.addCleanup(c.ledger.close)
        release=c.ledger.add(manifest)
        for platform in platforms:
            with self.subTest(platform=platform):
                c.ledger.transition(release,platform,'building')
                c.ledger.transition(release,platform,'verifying')
                c.ledger.transition(release,platform,'verified',evidence='a'*64)
                with patch.object(c,'execute',side_effect=AssertionError('publication before deployment')):
                    c.step(release,platform)
                self.assertEqual(c.ledger.target(release,platform)['state'],'verified')

    def test_deployment_observation_must_be_fresh_and_inventory_unchanged(self):
        from release_pair import canonical
        manifest=copy.deepcopy(self.manifest);manifest['policy']['deployment_required']=True
        inventory=self.root/'inventory.json';atomic_json(inventory,{'targets':[]})
        c=Coordinator(self.root,{'deployment_file':str(inventory)});self.addCleanup(c.ledger.close)
        release=manifest['release_id'];directory=self.root/'deployment'/release
        atomic_json(self.root/'deployment/desired.json',{'release_id':release})
        report={'state':'deployed','sources':manifest['sources'],'observed_at':100,
                'revision':hashlib.sha256(canonical({'targets':[]})).hexdigest()}
        atomic_json(directory/'journal.json',report)
        with patch('release_coordinator.time.time',return_value=150):
            self.assertTrue(c.deployment_ready(manifest))
        with patch('release_coordinator.time.time',return_value=401):
            self.assertFalse(c.deployment_ready(manifest))
        atomic_json(inventory,{'targets':[],'revision':2})
        with patch('release_coordinator.time.time',return_value=150):
            self.assertFalse(c.deployment_ready(manifest))

    def deployment_candidates(self):
        inventory=self.root/'inventory.json';atomic_json(inventory,{'targets':[]})
        c=Coordinator(self.root,{'deployment_file':str(inventory),
            'workers':{'linux-x86_64':{'infrastructure':{}}}})
        self.addCleanup(c.ledger.close)
        manifests=[]
        for number in (1,2):
            m=candidate(number);m['policy']['deployment_required']=True
            m['release_id']=hashlib.sha256(canonical({k:v for k,v in m.items() if k!='release_id'})).hexdigest()
            c.ledger.add(m);manifests.append(m)
        return c,manifests

    def mark_verified(self,c,manifest,platform):
        for state in ('building','verifying','verified'):
            c.ledger.transition(manifest['release_id'],platform,state,evidence='a'*64)

    def test_newer_mobile_artifact_does_not_stall_qualified_linux_rollout(self):
        c,(first,second)=self.deployment_candidates()
        self.mark_verified(c,first,'linux-x86_64')
        self.mark_verified(c,second,'android')
        with patch.object(c,'execute',return_value=({},'a'*64)) as execute, \
                patch('release_deployment.reconcile') as reconcile:
            c.reconcile_deployment()
        execute.assert_called_once_with(first,'linux-x86_64','infrastructure')
        self.assertEqual(reconcile.call_args.args[1],first)
        self.assertEqual(json.loads((self.root/'deployment/desired.json').read_text()),
                         {'release_id':first['release_id'],'sequence':1})

    def test_missing_infrastructure_receipt_cannot_advance_desired_release(self):
        c,(first,second)=self.deployment_candidates()
        self.mark_verified(c,second,'linux-x86_64')
        desired=self.root/'deployment/desired.json'
        previous={'release_id':first['release_id'],'sequence':1};atomic_json(desired,previous)
        with patch.object(c,'execute',return_value=None),patch('release_deployment.reconcile') as reconcile:
            c.reconcile_deployment()
        reconcile.assert_not_called()
        self.assertEqual(json.loads(desired.read_text()),previous)
        self.assertEqual(json.loads((self.root/'public/deployment.json').read_text())['state'],'waiting_artifacts')

    def test_invalid_infrastructure_receipt_cannot_advance_desired_release(self):
        c,(first,second)=self.deployment_candidates()
        self.mark_verified(c,second,'linux-x86_64')
        with patch.object(c,'execute',side_effect=ValueError('changed source')), \
                patch('release_deployment.reconcile') as reconcile:
            c.reconcile_deployment()
        reconcile.assert_not_called()
        self.assertFalse((self.root/'deployment/desired.json').exists())
        self.assertEqual(json.loads((self.root/'public/deployment.json').read_text())['state'],'blocked')

    def test_late_qualified_linux_cannot_downgrade_desired_release(self):
        c,(first,second)=self.deployment_candidates()
        self.mark_verified(c,first,'linux-x86_64')
        previous={'release_id':second['release_id'],'sequence':2}
        atomic_json(self.root/'deployment/desired.json',previous)
        with patch.object(c,'execute') as execute,patch('release_deployment.reconcile') as reconcile:
            c.reconcile_deployment()
        execute.assert_not_called();reconcile.assert_not_called()
        self.assertEqual(json.loads((self.root/'deployment/desired.json').read_text()),previous)

    def test_active_rollout_retains_owner_before_newer_ready_linux(self):
        c,(first,second)=self.deployment_candidates()
        self.mark_verified(c,first,'linux-x86_64');self.mark_verified(c,second,'linux-x86_64')
        atomic_json(self.root/'deployment/owner.json',{'release_id':first['release_id']})
        atomic_json(self.root/'deployment/desired.json',{'release_id':first['release_id'],'sequence':1})
        with patch.object(c,'execute',return_value=({},'a'*64)) as execute, \
                patch('release_deployment.reconcile') as reconcile:
            c.reconcile_deployment()
        execute.assert_called_once_with(first,'linux-x86_64','infrastructure')
        self.assertEqual(reconcile.call_args.args[1],first)

    @unittest.skipUnless(os.name == 'posix', 'coordinator daemon uses POSIX flock')
    def test_daemon_polling_uses_configured_interval_and_releases_lock(self):
        import release_coordinator
        for interval in (None, 10, 300):
            config=self.root/'config.json'
            config.write_text(json.dumps({} if interval is None else {'poll_interval_seconds':interval}))
            argv=['release_coordinator.py','--state',str(self.root/'state'),'--config',str(config)]
            with self.subTest(interval=interval),patch.object(sys,'argv',argv), \
                    patch.object(Coordinator,'tick') as tick, \
                    patch('release_coordinator.time.sleep',side_effect=KeyboardInterrupt) as sleep:
                with self.assertRaises(KeyboardInterrupt):release_coordinator.main()
                tick.assert_called_once()
                sleep.assert_called_once_with(30 if interval is None else interval)
            # The next daemon can acquire the same lock after interruption.

    def test_selected_platforms_preserve_other_queued_and_active_work(self):
        from release_pair import canonical
        c=Coordinator(self.root,{'workers':{}});self.addCleanup(c.ledger.close)
        first=c.ledger.add(self.manifest)
        c.ledger.transition(first,'windows-x86_64','building')
        second=candidate(2);second['selected_platforms']=['macos-aarch64','macos-x86_64']
        second['release_id']=hashlib.sha256(canonical({k:v for k,v in second.items() if k!='release_id'})).hexdigest()
        latest=c.ledger.add(second);c.ledger.coalesce()
        self.assertEqual(c.ledger.target(first,'android')['state'],'queued')
        self.assertEqual(c.ledger.target(first,'windows-x86_64')['state'],'building')
        self.assertEqual(c.ledger.target(first,'macos-aarch64')['state'],'superseded')
        self.assertEqual(c.ledger.target(latest,'macos-aarch64')['state'],'queued')
        self.assertEqual(c.ledger.target(latest,'android')['state'],'superseded')
        self.assertEqual(c.ledger.add(second),latest)

    def test_invalid_target_selection_is_rejected_before_ledger_mutation(self):
        from release_pair import canonical
        c=Coordinator(self.root,{'workers':{}});self.addCleanup(c.ledger.close)
        for selected in ([],['ios','ios'],['unknown'],'ios',[{}]):
            m=copy.deepcopy(self.manifest);m['selected_platforms']=selected
            m['release_id']=hashlib.sha256(canonical({k:v for k,v in m.items() if k!='release_id'})).hexdigest()
            with self.assertRaisesRegex(ValueError,'selected platforms'):c.ledger.add(m)
        self.assertEqual(c.ledger.db.execute('SELECT COUNT(*) FROM candidates').fetchone()[0],0)
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

    def test_same_clock_tick_keeps_both_logs_and_reconciles_the_original_effect(self):
        c=Coordinator(self.root,{'minimum_free_bytes':0,
            'workers':{'android':{'build':{'run':['first'],'reconcile':['recover']}}}})
        self.addCleanup(c.ledger.close);release=c.ledger.add(self.manifest)
        with patch('release_coordinator.time.time_ns',return_value=42),patch('release_coordinator.subprocess.run',return_value=type('Result',(),{'returncode':75})()) as worker:
            c.step(release,'android');effect=c.ledger.effect(release,'android','build');c.step(release,'android')
        self.assertEqual([v.args[0] for v in worker.call_args_list],[['first'],['recover']])
        self.assertEqual(c.ledger.effect(release,'android','build')['id'],effect['id'])
        self.assertEqual(c.ledger.target(release,'android')['state'],'building')
        self.assertEqual(len(list((self.root/'jobs'/effect['id']).glob('42-*.log'))),2)

    def test_transient_recovery_backs_off_and_only_reconciles(self):
        c=Coordinator(self.root,{'minimum_free_bytes':0,'automatic_recovery':True,
            'workers':{'android':{'build':{'run':['first'],'reconcile':['recover']}}}})
        self.addCleanup(c.ledger.close);release=c.ledger.add(self.manifest);seen=[]
        def launch(argv,**kwargs):
            seen.append(argv)
            if len(seen)==1:raise TimeoutError('lost external reply')
            return type('Result',(),{'returncode':75})()
        with patch('release_coordinator.subprocess.run',side_effect=launch):
            c.step(release,'android');c.step(release,'android')
            self.assertEqual(seen,[['first']])
            recovery=json.loads(c.recovery_path(release,'android').read_text())
            with patch('release_coordinator.time.time',return_value=recovery['retry_at']):
                c.step(release,'android')
        self.assertEqual(seen,[['first'],['recover']])
        self.assertEqual(c.ledger.target(release,'android')['state'],'building')

    def test_deterministic_failure_only_resumes_after_worker_revision_changes(self):
        c=Coordinator(self.root,{'minimum_free_bytes':0,'automatic_recovery':True,
            'workers':{'android':{'build':{'run':['first'],'reconcile':['recover']}}}})
        self.addCleanup(c.ledger.close);release=c.ledger.add(self.manifest)
        with patch('release_coordinator.subprocess.run',return_value=type('Result',(),{'returncode':1})()) as worker:
            c.step(release,'android');c.step(release,'android')
            self.assertEqual(worker.call_count,1)
            c.config['controller_revision']='corrected-worker'
            c.step(release,'android')
            self.assertEqual(worker.call_count,2)
            self.assertEqual(worker.call_args.args[0],['recover'])

    def newer_candidate(self):
        manifest=copy.deepcopy(self.manifest)
        for platform, version in manifest['versions'].items():
            pieces=version.split('.');pieces[-1]=str(int(pieces[-1])+1)
            manifest['versions'][platform]='.'.join(pieces)
        manifest['release_id']=hashlib.sha256(canonical({k:v for k,v in manifest.items() if k!='release_id'})).hexdigest()
        return manifest

    def test_storage_recovers_without_revision_change_and_preserves_legacy_block(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                c=Coordinator(self.root/str(legacy),{'minimum_free_bytes':10,'automatic_recovery':True,
                    'workers':{'android':{'build':{'run':['first'],'reconcile':['recover']}}}})
                self.addCleanup(c.ledger.close);release=c.ledger.add(self.manifest)
                with patch('shutil.disk_usage',return_value=type('Disk',(),{'free':9})()),patch('release_coordinator.subprocess.run') as worker:
                    c.step(release,'android');c.step(release,'android')
                    self.assertEqual(c.ledger.target(release,'android')['state'],'blocked');worker.assert_not_called()
                path=c.recovery_path(release,'android');recovery=json.loads(path.read_text())
                self.assertEqual(recovery['cause'],'storage_headroom')
                self.assertEqual(recovery['revision'],c.worker_revision('android','build'))
                if legacy:
                    recovery.pop('cause');atomic_json(path,recovery)
                c.config['automatic_recovery']=False
                with patch('shutil.disk_usage',return_value=type('Disk',(),{'free':10})()),patch('release_coordinator.subprocess.run',return_value=type('Result',(),{'returncode':75})()) as worker:
                    c.step(release,'android');worker.assert_not_called()
                    c.config['automatic_recovery']=True;c.step(release,'android')
                    self.assertEqual(worker.call_args.args[0],['first'])
                    effect=c.ledger.effect(release,'android','build');c.step(release,'android')
                    self.assertEqual(worker.call_args.args[0],['recover'])
                    self.assertEqual(c.ledger.effect(release,'android','build')['id'],effect['id'])

    def test_capacity_coalesces_only_undispatched_work_and_keeps_frozen_request(self):
        for ownership in ('none','reserved','attempted'):
            with self.subTest(ownership=ownership):
                c=Coordinator(self.root/ownership,{'minimum_free_bytes':10,'automatic_recovery':True,
                    'workers':{'android':{'build':{'run':['first'],'reconcile':['recover']}}}})
                self.addCleanup(c.ledger.close);old=c.ledger.add(self.manifest)
                with patch('shutil.disk_usage',return_value=type('Disk',(),{'free':9})()):c.step(old,'android')
                effect=None
                if ownership!='none':
                    effect=c.ledger.effect(old,'android','build')
                    if ownership=='attempted':atomic_json(c.state/'jobs'/effect['id']/'attempted.json',{'request_id':effect['id']})
                latest=c.ledger.add(self.newer_candidate())
                with patch('shutil.disk_usage',return_value=type('Disk',(),{'free':10})()),patch('release_coordinator.subprocess.run',return_value=type('Result',(),{'returncode':75})()) as worker:
                    c.step(old,'android')
                    if ownership=='attempted':
                        self.assertEqual(worker.call_args.args[0],['recover'])
                        self.assertEqual(c.ledger.target(old,'android')['state'],'building')
                        c.step(latest,'android');self.assertEqual(worker.call_count,1)
                    else:
                        worker.assert_not_called();self.assertEqual(c.ledger.target(old,'android')['state'],'superseded')
                        c.step(latest,'android');self.assertEqual(worker.call_args.args[0],['first'])
                if effect:self.assertEqual(c.ledger.effect(old,'android','build')['id'],effect['id'])

    def test_capacity_recovery_waits_for_another_active_build_or_verification(self):
        c=Coordinator(self.root,{'minimum_free_bytes':10,'automatic_recovery':True,
            'workers':{'android':{'build':{'run':['first'],'reconcile':['recover']}}}})
        self.addCleanup(c.ledger.close);old=c.ledger.add(self.manifest);latest=c.ledger.add(self.newer_candidate())
        c.ledger.transition(old,'android','building');c.ledger.transition(latest,'android','building')
        c.record_failure(latest,'android','build',StorageHeadroomError(STORAGE_HEADROOM_REASON))
        c.ledger.transition(latest,'android','blocked',reason=STORAGE_HEADROOM_REASON)
        with patch('shutil.disk_usage',return_value=type('Disk',(),{'free':10})()),patch('release_coordinator.subprocess.run',return_value=type('Result',(),{'returncode':75})()) as worker:
            c.step(latest,'android');worker.assert_not_called()
            c.ledger.transition(old,'android','verifying');c.step(latest,'android');worker.assert_not_called()
            c.ledger.transition(old,'android','verified',evidence='a'*64);c.step(latest,'android')
            self.assertEqual(worker.call_args.args[0],['first'])

    def test_polling_prioritizes_new_candidates_and_retains_old_active_work(self):
        c=Coordinator(self.root,{'workers':{}});self.addCleanup(c.ledger.close)
        old=c.ledger.add(self.manifest);c.ledger.transition(old,'android','building')
        latest=c.ledger.add(self.newer_candidate())
        with patch.object(c,'step') as step:c.tick()
        calls=[v.args[0] for v in step.call_args_list]
        self.assertEqual(calls[:7],[latest]*7);self.assertEqual(calls[7:],[old]*7)
        self.assertEqual(c.ledger.target(old,'android')['state'],'building')

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

    def test_windows_size_authorization_cannot_change_other_releases_or_platforms(self):
        from release_compatibility import file_policy
        from release_pair import canonical
        path=Path(__file__).resolve().parents[2]/'release/automation/qualification/windows36-4mib.json'
        raw=path.read_bytes(); authorization=json.loads(raw)
        manifest=copy.deepcopy(self.manifest)
        manifest.update(release_id=authorization['release_id'],sources={
            name:{'commit':commit,'tree':'a'*40} for name,commit in authorization['sources'].items()})
        manifest['policy']['file_qualification']={'mode':'file-recovery','bytes':16777216,
            'completion_seconds':180,'total_seconds':600}
        original=canonical(manifest)
        proof={'platform':'windows-x86_64','binary_sha256':authorization['binary_sha256'],
            'qualification_policy_sha256':hashlib.sha256(raw).hexdigest()}
        self.assertEqual(file_policy(manifest,proof,'windows-x86_64')['bytes'],4194304)
        self.assertEqual(file_policy(manifest,{},'windows-x86_64')['bytes'],16777216)
        for field,value in [('platform','android'),('binary_sha256','0'*64),
                            ('qualification_policy_sha256','0'*64)]:
            with self.subTest(field=field),self.assertRaises(ValueError):
                file_policy(manifest,{**proof,field:value},'windows-x86_64')
        for platform in (None,'android','ios','linux-x86_64','macos-aarch64'):
            with self.subTest(platform=platform),self.assertRaises(ValueError):
                file_policy(manifest,proof,platform)
        for field,value in [('release_id','0'*64),('sources',self.manifest['sources'])]:
            with self.subTest(field=field),self.assertRaises(ValueError):
                file_policy({**manifest,field:value},proof,'windows-x86_64')
        self.assertEqual(canonical(manifest),original)

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
