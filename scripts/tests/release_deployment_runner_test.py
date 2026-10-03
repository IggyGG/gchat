import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_automation_test import candidate
from release_coordinator import Coordinator, atomic_json
from release_deployment_runner import DeploymentRunner
from release_pair import canonical


@unittest.skipUnless(os.name == 'posix', 'deployment process ownership uses POSIX')
class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = candidate()
        self.runner = DeploymentRunner(self.root)
        self.addCleanup(self.runner.close)
        self.gate = self.root / 'allow-observation'
        script = self.root / 'worker.py'
        script.write_text('''import hashlib,json,os,pathlib,time
from pathlib import Path
while not Path(GATE).exists():time.sleep(.01)
directory=Path(os.environ['GCHAT_DEPLOYMENT_RECEIPT']).parent
source=json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text())
target=json.loads(Path(os.environ['GCHAT_DEPLOYMENT_TARGET']).read_text())
evidence=directory/'evidence';evidence.write_bytes(b'actual fixture observation')
report={'schema':1,'target':target['id'],'stage':os.environ['GCHAT_DEPLOYMENT_STAGE'],
'release_id':source['release_id'],'sources':source['sources'],'observed_at':int(time.time()),
'healthy':True,'matches':True,'running':{'sha256':'fixture'},'passed':True,
'evidence':[{'path':evidence.name,'sha256':hashlib.sha256(evidence.read_bytes()).hexdigest()}]}
Path(os.environ['GCHAT_DEPLOYMENT_RECEIPT']).write_text(json.dumps(report))
'''.replace('GATE', repr(str(self.gate))))
        self.config = {'targets': [{'id': 'fixture', 'workers': {stage: [sys.executable, str(script)]
                       for stage in ('observe', 'prepare', 'activate', 'rollback', 'check')}}]}

    def test_real_worker_keeps_parent_responsive_and_records_bound_completed_step(self):
        started = time.monotonic()
        self.runner.step(self.manifest, self.config)
        self.assertLess(time.monotonic() - started, 0.5)
        pid = self.runner.pending['process'].pid
        self.runner.step(self.manifest, self.config)
        self.assertEqual(self.runner.pending['process'].pid, pid)
        self.assertFalse((self.root / 'ledger.sqlite').exists(), 'worker never opens the ledger')
        self.gate.touch()
        self.runner.pending['process'].wait(timeout=5)
        output = self.runner.pending['output']
        self.runner.step(self.manifest, self.config)
        self.assertIsNone(self.runner.pending)
        proof = json.loads(output.read_text())
        self.assertTrue(proof['deployed'])
        self.assertEqual(proof['sources'], self.manifest['sources'])
        self.assertEqual(proof['revision'], hashlib.sha256(canonical(self.config)).hexdigest())
        journal = self.root / 'deployment' / self.manifest['release_id'] / 'journal.json'
        self.assertEqual(json.loads(journal.read_text())['state'], 'deployed')

    def test_changed_step_receipt_cannot_qualify_deployment(self):
        self.gate.touch()
        self.runner.step(self.manifest, self.config)
        self.runner.pending['process'].wait(timeout=5)
        output = self.runner.pending['output']
        proof = json.loads(output.read_text());proof['sources'] = {};atomic_json(output, proof)
        with self.assertRaisesRegex(ValueError, 'frozen inputs'):
            self.runner.step(self.manifest, self.config)

    def test_deadline_stops_only_owned_process_and_retains_original_request(self):
        self.runner.step(self.manifest, self.config)
        process = self.runner.pending['process']
        output = self.runner.pending['output']
        self.runner.pending['deadline'] = 0
        with self.assertRaisesRegex(ValueError, 'deadline'):
            self.runner.step(self.manifest, self.config)
        self.assertIsNotNone(process.poll())
        self.assertTrue((output.parent / 'request.json').is_file())
        self.assertFalse(output.exists())

    def test_coordinator_tick_remains_live_during_a_waiting_real_rollout(self):
        manifest = self.manifest;manifest['policy']['deployment_required'] = True
        manifest['release_id'] = hashlib.sha256(canonical({k:v for k,v in manifest.items() if k!='release_id'})).hexdigest()
        inventory = self.root / 'inventory.json';atomic_json(inventory, self.config)
        c = Coordinator(self.root, {'nonblocking_deployment': True, 'deployment_file': str(inventory),
                                  'workers': {'linux-x86_64': {}}})
        self.addCleanup(c.ledger.close);self.addCleanup(c.close_workers)
        c.ledger.add(manifest)
        for state in ('building', 'verifying', 'verified'):
            c.ledger.transition(manifest['release_id'], 'linux-x86_64', state, evidence='a'*64)
        started = time.monotonic()
        c.tick()
        c.tick()
        self.assertLess(time.monotonic() - started, 0.5)
        public = json.loads((self.root / 'public/status.json').read_text())
        self.assertEqual(public['observed_at'], int(time.time()))
        self.assertTrue(public['deployment_worker']['process_alive'])
        self.assertEqual(public['deployment_worker']['release_id'], manifest['release_id'])

    def test_six_acceptances_progress_independently_of_three_artifact_workers(self):
        script = self.root / 'hold.py';script.write_text('import time;time.sleep(60)')
        recipe = {'run': [sys.executable, str(script)], 'reconcile': [sys.executable, str(script)], 'timeout': 120}
        platforms = ('linux-x86_64','windows-x86_64','macos-aarch64','macos-x86_64','android','ios')
        c = Coordinator(self.root, {'nonblocking_workers': True, 'maximum_workers': 3,
            'maximum_acceptance_workers': 6, 'minimum_free_bytes': 0,
            'workers': {p:{stage:recipe for stage in ('build','acceptance')} for p in platforms}})
        self.addCleanup(c.ledger.close);self.addCleanup(c.close_workers);c.ledger.add(self.manifest)
        for platform in platforms[:3]:c.execute(self.manifest, platform, 'build')
        for platform in platforms:c.execute(self.manifest, platform, 'acceptance')
        self.assertEqual(len(c.running_workers), 9)
        c.execute(self.manifest, platforms[3], 'build')
        self.assertEqual(len(c.running_workers), 9)

    def test_invalid_execution_limits_do_not_create_state(self):
        for config in ({'nonblocking_deployment': 'true'}, {'maximum_acceptance_workers': 7},
                       {'maximum_acceptance_workers': True}, {'deployment_step_timeout_seconds': 899},
                       {'deployment_step_timeout_seconds': True}):
            path = self.root / 'unused'
            with self.subTest(config=config), self.assertRaises(ValueError):Coordinator(path, config)
            self.assertFalse(path.exists())
