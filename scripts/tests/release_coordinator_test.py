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

    def test_windows_worker_cleanup_terminates_child_and_closes_log(self):
        import subprocess
        from unittest.mock import Mock, call
        for timed_out in (False, True):
            with self.subTest(timed_out=timed_out):
                c = Coordinator(self.root, {})
                self.addCleanup(c.ledger.close)
                process = Mock()
                process.poll.return_value = None
                if timed_out:
                    process.wait.side_effect = [subprocess.TimeoutExpired('worker', 15), 0]
                log = (self.root / 'worker.log').open('wb')
                self.addCleanup(log.close)
                c.running_workers['worker'] = {'process': process, 'log': log}
                with patch('release_coordinator.os.name', 'nt'), \
                     patch('release_coordinator.os.killpg', create=True) as killpg:
                    c.close_workers()
                killpg.assert_not_called()
                process.terminate.assert_called_once_with()
                self.assertEqual(process.kill.call_count, int(timed_out))
                self.assertEqual(process.wait.call_args_list,
                                 [call(timeout=15), call(timeout=5)] if timed_out else [call(timeout=15)])
                self.assertTrue(log.closed)
                self.assertEqual(c.running_workers, {})

    def test_worker_cleanup_closes_log_even_when_termination_fails(self):
        from unittest.mock import Mock
        c = Coordinator(self.root, {})
        self.addCleanup(c.ledger.close)
        process = Mock()
        process.poll.return_value = None
        log = (self.root / 'worker.log').open('wb')
        self.addCleanup(log.close)
        c.running_workers['worker'] = {'process': process, 'log': log}
        with patch('release_coordinator.stop_worker', side_effect=OSError('termination failed')):
            with self.assertRaisesRegex(OSError, 'termination failed'):
                c.close_workers()
        self.assertTrue(log.closed)

    def test_observation_reuses_pending_request_and_advances_only_after_verified_completion(self):
        from unittest.mock import Mock
        recipe = {'run': ['read-only-store-status'], 'reconcile': ['reconcile-store-status']}
        c = Coordinator(self.root, {'nonblocking_workers': True,
                                  'workers': {'android': {'observe': recipe}}})
        self.addCleanup(c.ledger.close)
        c.ledger.add(self.manifest)
        process = Mock(returncode=0)
        process.poll.return_value = None
        with patch('release_coordinator.subprocess.Popen', return_value=process) as launch:
            self.assertIsNone(c.execute(self.manifest, 'android', 'observe'))
            first = c.ledger.effect(self.manifest['release_id'], 'android', 'observe')
            log = c.running_workers[first['id']]['log']
            self.assertIsNone(c.execute(self.manifest, 'android', 'observe'))
            self.assertEqual(launch.call_count, 1)
            self.receipt(self.root / 'jobs' / first['id'], stage='observe')
            process.poll.return_value = 0
            self.assertIsNotNone(c.execute(self.manifest, 'android', 'observe'))
            self.assertTrue(log.closed)
            self.assertEqual(c.ledger.effect(self.manifest['release_id'], 'android', 'observe')['state'], 'confirmed')
            process.poll.return_value = None
            self.assertIsNone(c.execute(self.manifest, 'android', 'observe'))
            self.assertEqual(launch.call_count, 2)
            pointer = json.loads((self.root / 'observe-effects' / self.manifest['release_id'] / 'android.json').read_text())
            self.assertEqual(pointer['kind'], 'observe-after-' + first['id'])
        process.poll.return_value = 0
        c.close_workers()

    def test_obsolete_observation_logs_are_closed_without_confirming_unknown_outcomes(self):
        from unittest.mock import Mock
        c = Coordinator(self.root, {'workers': {}})
        self.addCleanup(c.ledger.close)
        c.ledger.add(self.manifest)
        logs = []
        for index in range(32):
            effect = c.ledger.effect(self.manifest['release_id'], 'android', f'observe-{index}')
            process = Mock(returncode=0)
            process.poll.return_value = 0
            log = (self.root / f'old-{index}.log').open('wb'); logs.append(log)
            c.running_workers[effect['id']] = dict(process=process, log=log, stage='observe',
                release_id=self.manifest['release_id'], platform='android')
        c.collect_finished_workers()
        self.assertEqual(c.running_workers, {})
        self.assertTrue(all(log.closed for log in logs))
        self.assertEqual(c.ledger.db.execute("SELECT COUNT(*) FROM effects WHERE state='confirmed'").fetchone()[0], 0)

    def test_mobile_native_checks_finish_before_store_serialization_and_prerequisite_is_read_only(self):
        for platform in ('ios','android'):
            for waiting in ('submitting','processing','in_review','blocked'):
                for proven in (False,True):
                    with self.subTest(platform=platform,waiting=waiting,proven=proven):
                        c=Coordinator(self.root/f'{platform}-{waiting}-{proven}',
                            {'workers':{platform:{'acceptance':{},'compatibility':{},'prerequisite':{}}}})
                        self.addCleanup(c.ledger.close)
                        old=c.ledger.add(candidate(1))
                        for state in ('building','verifying','verified','submitting'):
                            c.ledger.transition(old,platform,state,evidence='a'*64)
                        if waiting in ('processing','in_review'):
                            c.ledger.transition(old,platform,'processing',evidence='a'*64)
                        if waiting in ('in_review','blocked'):
                            c.ledger.transition(old,platform,waiting,evidence='a'*64,reason='retained provider failure')
                        latest=c.ledger.add(candidate(2))
                        for state in ('building','verifying','verified'):
                            c.ledger.transition(latest,platform,state,evidence='b'*64)
                        with patch.object(c,'execute',return_value=({'relay_compatible':True},'c'*64)) as execute, \
                             patch('release_flight.external_ios_wait',return_value=proven):
                            c.step(latest,platform)
                        self.assertEqual([call.args[2] for call in execute.call_args_list],
                            ['acceptance','compatibility','prerequisite'] if platform=='ios' else ['acceptance','compatibility'])
                        self.assertEqual(c.ledger.target(latest,platform)['state'],'verified')
                        self.assertEqual(c.ledger.target(old,platform)['state'],waiting)

    @unittest.skipUnless(os.name == 'posix', 'controller uses POSIX process groups')
    def test_nonblocking_worker_does_not_prevent_another_platform_and_reconciles_same_effect(self):
        import sys
        import time
        script = self.root / 'async.py'
        release_worker = self.root / 'release-worker'
        script.write_text('import time\nfrom pathlib import Path\nwhile not Path(' +
                          repr(str(release_worker)) + ').exists(): time.sleep(0.01)\nraise SystemExit(75)\n')
        recipe = {'run': [sys.executable, str(script)], 'reconcile': [sys.executable, str(script)], 'timeout': 10}
        c = Coordinator(self.root, {'nonblocking_workers': True, 'maximum_workers': 2, 'minimum_free_bytes': 0,
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
        with patch('shutil.disk_usage', return_value=type('Usage', (), {'free': -1})()):
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
        c = Coordinator(self.root, {'nonblocking_workers': True, 'minimum_free_bytes': 0,
                                  'workers': {'linux-x86_64': {'build': recipe}}})
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

    def test_slow_older_reconciliation_keeps_capacity_for_resumed_active_workers(self):
        from unittest.mock import Mock
        for stage, limit in (('build', 3), ('acceptance', 6), ('build', 1)):
            with self.subTest(stage=stage, limit=limit):
                root = self.root / (stage + str(limit))
                recipe = {'run': ['fixture-worker'], 'reconcile': ['fixture-worker'], 'timeout': 10}
                c = Coordinator(root, {'single_flight': True, 'nonblocking_workers': True,
                    'maximum_workers': min(limit, 3), 'maximum_acceptance_workers': limit,
                    'minimum_free_bytes': 0, 'workers': {'linux-x86_64': {stage: recipe}}})
                manifests = [candidate(i) for i in (1, 2, 3)]
                for manifest in manifests: c.ledger.add(manifest)
                atomic_json(root / 'deployment/desired.json', {'release_id': manifests[0]['release_id']})
                retained = []
                for manifest in manifests[1:]:
                    effect = c.ledger.effect(manifest['release_id'], 'linux-x86_64', stage)
                    path = root / 'jobs' / effect['id'] / 'attempted.json'
                    atomic_json(path, {'request_id': effect['id'], 'attempted': 1})
                    retained.append((path, path.read_bytes()))
                processes = []
                def launch(*args, **kwargs):
                    process = Mock(); process.poll.return_value = None; processes.append(process); return process
                try:
                    with patch('release_coordinator.subprocess.Popen', side_effect=launch) as worker:
                        for manifest in manifests[1:]:
                            c.execute(manifest, 'linux-x86_64', stage)
                        self.assertEqual(worker.call_count, 1 if limit > 1 else 0)
                        c.execute(manifests[0], 'linux-x86_64', stage)
                        self.assertEqual(worker.call_count, 2 if limit > 1 else 1)
                        self.assertTrue(any(item['release_id'] == manifests[0]['release_id']
                                            for item in c.running_workers.values()))
                        self.assertEqual(retained[-1][0].read_bytes(), retained[-1][1])
                finally:
                    for process in processes: process.poll.return_value = 0
                    c.close_workers(); c.ledger.close()
    def test_invalid_poll_interval_cannot_create_release_state(self):
        for interval in (0, 9, 301, True, 0.5, '30', None):
            state=self.root / 'unused'
            with self.subTest(interval=interval),self.assertRaisesRegex(ValueError,'poll_interval_seconds'):
                Coordinator(state,{'poll_interval_seconds':interval})
            self.assertFalse(state.exists())

    def test_selected_flight_admits_new_build_while_old_requests_only_reconcile(self):
        from types import SimpleNamespace
        from release_minutes import POLICY, budget
        for recovery in (False, True):
            with self.subTest(storage_recovery=recovery):
                root = self.root / str(recovery)
                recipe = {'run': ['dispatch-original'], 'reconcile': ['collect-original']}
                c = Coordinator(root, {'single_flight': True, 'publication_policy': POLICY,
                    'automatic_recovery': True, 'minimum_free_bytes': 0,
                    'workers': {'linux-x86_64': {'build': recipe}}})
                self.addCleanup(c.ledger.close)
                manifests = [candidate(i) for i in (1, 2, 3, 4)]
                old, verifying, selected = [c.ledger.add(m) for m in manifests[:3]]
                c.ledger.transition(old, 'linux-x86_64', 'building')
                for state in ('building', 'verifying'):
                    c.ledger.transition(verifying, 'linux-x86_64', state)
                original = c.ledger.effect(old, 'linux-x86_64', 'build')
                marker = root / 'jobs' / original['id'] / 'attempted.json'
                atomic_json(marker, {'request_id': original['id'], 'attempted': 100})
                budget(root, manifests[0], 'linux-x86_64', 'building', now=100)
                atomic_json(root / 'release-flight.json', {'schema': 1, 'active': selected, 'pending': None})
                if recovery:
                    c.ledger.transition(selected, 'linux-x86_64', 'building')
                    c.ledger.transition(selected, 'linux-x86_64', 'blocked', reason=STORAGE_HEADROOM_REASON)
                    atomic_json(c.recovery_path(selected, 'linux-x86_64'), {
                        'stage': 'build', 'cause': 'storage_headroom',
                        'revision': c.worker_revision('linux-x86_64', 'build')})
                with patch('release_coordinator.subprocess.run', return_value=SimpleNamespace(returncode=75)) as run:
                    c.step(selected, 'linux-x86_64')
                    self.assertEqual(c.ledger.target(selected, 'linux-x86_64')['state'], 'building')
                    self.assertEqual(run.call_args.args[0], ['dispatch-original'])
                    pending = c.ledger.add(manifests[3])
                    c.step(pending, 'linux-x86_64')
                    self.assertEqual(run.call_count, 1)
                    self.assertEqual(c.ledger.target(pending, 'linux-x86_64')['state'], 'queued')
                    c.step(old, 'linux-x86_64')
                    self.assertEqual(run.call_args.args[0], ['collect-original'])
                    self.assertEqual(run.call_args.kwargs['env']['GCHAT_RELEASE_RECONCILE_ONLY'], '1')
                self.assertEqual(json.loads(marker.read_text())['request_id'], original['id'])
                self.assertEqual(c.ledger.effect(old, 'linux-x86_64', 'build')['id'], original['id'])
                self.assertEqual(c.ledger.target(verifying, 'linux-x86_64')['state'], 'verifying')

    def test_without_single_flight_other_build_still_blocks_queued_admission(self):
        c = Coordinator(self.root, {'workers': {'linux-x86_64': {'build': {'run': ['unused']}}}})
        self.addCleanup(c.ledger.close)
        old = c.ledger.add(candidate(1))
        latest = c.ledger.add(candidate(2))
        c.ledger.transition(old, 'linux-x86_64', 'building')
        with patch.object(c, 'execute') as execute:
            c.step(latest, 'linux-x86_64')
        execute.assert_not_called()
        self.assertEqual(c.ledger.target(latest, 'linux-x86_64')['state'], 'queued')

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

    def test_relay_load_waits_without_advancing_or_restarting_the_fleet(self):
        c, (first, second) = self.deployment_candidates()
        c.config['workers']['linux-x86_64']['relay_load'] = {}
        self.mark_verified(c, second, 'linux-x86_64')
        desired = self.root / 'deployment/desired.json'
        previous = {'release_id': first['release_id'], 'sequence': 1}
        atomic_json(desired, previous)
        with patch.object(c, 'execute', return_value=None) as execute, \
             patch('release_deployment.reconcile') as reconcile:
            c.reconcile_deployment()
        execute.assert_called_once_with(second, 'linux-x86_64', 'relay_load')
        reconcile.assert_not_called()
        self.assertEqual(json.loads(desired.read_text()), previous)
        self.assertEqual(json.loads((self.root / 'public/deployment.json').read_text())['state'],
                         'waiting_load_acceptance')

    def test_valid_original_relay_gate_allows_the_existing_infrastructure_path(self):
        c, (_, second) = self.deployment_candidates()
        c.config['workers']['linux-x86_64']['relay_load'] = {}
        self.mark_verified(c, second, 'linux-x86_64')
        with patch.object(c, 'execute', side_effect=[({'relay_load_verified': True}, 'a' * 64), ({}, 'b' * 64)]) as execute, \
             patch('release_deployment.reconcile') as reconcile:
            c.reconcile_deployment()
        self.assertEqual([call.args[2] for call in execute.call_args_list], ['relay_load', 'infrastructure'])
        self.assertEqual(reconcile.call_args.args[1], second)

    def test_existing_owned_rollback_does_not_require_historical_load_evidence(self):
        c, (first, second) = self.deployment_candidates()
        c.config['workers']['linux-x86_64']['relay_load'] = {}
        self.mark_verified(c, first, 'linux-x86_64')
        self.mark_verified(c, second, 'linux-x86_64')
        desired = self.root / 'deployment/desired.json'
        previous = {'release_id': first['release_id'], 'sequence': 1}
        atomic_json(desired, previous)
        owner = self.root / 'deployment/owner.json'
        atomic_json(owner, {'release_id': first['release_id']})
        journal = self.root / 'deployment' / first['release_id'] / 'journal.json'
        atomic_json(journal, {'release_id': first['release_id'], 'sources': first['sources'],
                             'state': 'blocked', 'targets': {'relay-1': {'state': 'rollback_failed'}}})
        retained = {path: path.read_bytes() for path in (owner, journal)}
        with patch.object(c, 'execute', return_value=({}, 'a' * 64)) as execute, \
             patch('release_deployment.reconcile') as reconcile:
            c.reconcile_deployment()
        execute.assert_called_once_with(first, 'linux-x86_64', 'infrastructure')
        self.assertEqual(reconcile.call_args.args[1], first)
        self.assertEqual(json.loads(desired.read_text()), previous)
        self.assertFalse((self.root / 'relay-load').exists())
        for path, original in retained.items():
            self.assertEqual(path.read_bytes(), original)

    def test_owned_recovery_exemption_requires_matching_sources_and_owner(self):
        c, (first, second) = self.deployment_candidates()
        c.config['workers']['linux-x86_64']['relay_load'] = {}
        self.mark_verified(c, first, 'linux-x86_64')
        desired = self.root / 'deployment/desired.json'
        previous = {'release_id': first['release_id'], 'sequence': 1}
        atomic_json(desired, previous)
        owner = self.root / 'deployment/owner.json'
        journal = self.root / 'deployment' / first['release_id'] / 'journal.json'
        for missing in ('matching_sources', 'owner'):
            with self.subTest(missing=missing):
                atomic_json(owner, {'release_id': first['release_id']})
                atomic_json(journal, {'release_id': first['release_id'], 'state': 'blocked',
                    'sources': second['sources'] if missing == 'matching_sources' else first['sources']})
                if missing == 'owner': owner.unlink()
                with patch.object(c, 'execute', return_value=None) as execute, \
                     patch('release_deployment.reconcile') as reconcile:
                    c.reconcile_deployment()
                execute.assert_called_once_with(first, 'linux-x86_64', 'relay_load')
                reconcile.assert_not_called()
                self.assertEqual(json.loads(desired.read_text()), previous)

    def test_failed_relay_gate_is_retained_without_automatic_reruns(self):
        c, (_, second) = self.deployment_candidates()
        c.config['workers']['linux-x86_64']['relay_load'] = {}
        with patch.object(c, 'execute', side_effect=ValueError('original load failed')) as execute:
            self.assertFalse(c.relay_load_ready(second))
            self.assertFalse(c.relay_load_ready(second))
        self.assertEqual(execute.call_count, 1)
        status = json.loads((self.root / 'relay-load' / second['release_id'] / 'status.json').read_text())
        self.assertEqual(status['state'], 'blocked')

    def test_load_worker_does_not_accept_an_unverified_pass_flag(self):
        c, (_, second) = self.deployment_candidates()
        c.config['workers']['linux-x86_64']['relay_load'] = {}
        with patch.object(c, 'execute', return_value=({'passed': True}, 'a' * 64)):
            self.assertFalse(c.relay_load_ready(second))

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

    def test_provider_unavailable_exit_automatically_reconciles_original_effect(self):
        c=Coordinator(self.root,{'minimum_free_bytes':0,'automatic_recovery':True,
            'workers':{'android':{'build':{'run':['first'],'reconcile':['recover']}}}})
        self.addCleanup(c.ledger.close);release=c.ledger.add(self.manifest)
        results=[type('Result',(),{'returncode':76})(),type('Result',(),{'returncode':75})()]
        with patch('release_coordinator.subprocess.run',side_effect=results) as worker:
            c.step(release,'android');effect=c.ledger.effect(release,'android','build')
            recovery=json.loads(c.recovery_path(release,'android').read_text())
            self.assertTrue(recovery['transient']);self.assertEqual(recovery['attempts'],1)
            c.step(release,'android');self.assertEqual(worker.call_count,1)
            with patch('release_coordinator.time.time',return_value=recovery['retry_at']):c.step(release,'android')
        self.assertEqual([call.args[0] for call in worker.call_args_list],[['first'],['recover']])
        self.assertEqual(c.ledger.effect(release,'android','build')['id'],effect['id'])
        self.assertEqual(c.ledger.effect(release,'android','build')['state'],'reserved')

    @unittest.skipUnless(os.name == 'posix', 'controller uses POSIX process groups')
    def test_nonblocking_provider_unavailable_exit_retains_effect_and_cannot_pass(self):
        recipe={'run':[sys.executable,'-c','raise SystemExit(76)'],
                'reconcile':[sys.executable,'-c','raise SystemExit(76)']}
        c=Coordinator(self.root,{'minimum_free_bytes':0,'nonblocking_workers':True,
            'workers':{'android':{'build':recipe}}})
        self.addCleanup(c.ledger.close);self.addCleanup(c.close_workers);c.ledger.add(self.manifest)
        c.execute(self.manifest,'android','build');effect=c.ledger.effect(self.manifest['release_id'],'android','build')
        next(iter(c.running_workers.values()))['process'].wait(timeout=5)
        with self.assertRaises(ConnectionError):c.execute(self.manifest,'android','build')
        self.assertEqual(c.ledger.effect(self.manifest['release_id'],'android','build')['id'],effect['id'])
        self.assertEqual(c.ledger.effect(self.manifest['release_id'],'android','build')['state'],'reserved')

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

    def test_original_store_lane_reconciles_before_background_artifacts_and_after_active_release(self):
        c=Coordinator(self.root,{'workers':{},'single_flight':True});self.addCleanup(c.ledger.close)
        old=c.ledger.add(candidate(1))
        for state in ('building','verifying','verified','submitting'):
            c.ledger.transition(old,'ios',state,evidence='a'*64)
        active=c.ledger.add(candidate(2));c.ledger.transition(active,'android','building')
        latest=c.ledger.add(candidate(3))
        atomic_json(self.root/'deployment/desired.json',{'release_id':active})
        with patch.object(c,'step') as step,patch.object(c,'reconcile_deployment'):
            c.tick()
        calls=[call.args for call in step.call_args_list]
        self.assertTrue(all(release==active for release,platform in calls[:7]))
        self.assertEqual(calls[7],(old,'ios'))
        self.assertEqual(calls[8][0],latest)
        self.assertEqual(c.ledger.target(old,'ios')['state'],'submitting')

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
