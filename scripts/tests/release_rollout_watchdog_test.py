import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_automation_test import candidate
import release_rollout_watchdog as watchdog
from release_coordinator import atomic_json


@unittest.skipUnless(os.name == 'posix', 'Kubernetes recovery controller requires POSIX rollout locking')
class WatchdogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.manifest = candidate()
        self.directory = self.root / 'deployment' / self.manifest['release_id']
        self.work = self.directory / 'controller'; self.work.mkdir(parents=True)
        self.target = {'id': 'controller', 'kind': 'deployment', 'namespace': 'ghost-com',
            'name': 'gchat-release', 'image': 'controller', 'activation_deadline_seconds': 900}
        self.report = {'sources': self.manifest['sources'], 'state': 'deploying',
            'inventory': {'targets': [self.target]},
            'targets': {'controller': {'state': 'activating', 'started_at': 100, 'previous': {'old': 'image'}}}}
        atomic_json(self.root / 'deployment/owner.json', {'release_id': self.manifest['release_id']})
        atomic_json(self.directory / 'journal.json', self.report)
        atomic_json(self.work / 'candidate.json', self.manifest)
        self.calls = []; self.healthy = False; self.complete = True

    def worker(self, target, stage, manifest, work, previous=None):
        self.calls.append(stage)
        self.assertEqual(manifest, self.manifest)
        if stage == 'observe': return {'healthy': self.healthy, 'matches': True}
        self.assertEqual(stage, 'rollback')
        self.assertEqual(previous, {'old': 'image'})
        self.assertEqual(json.loads((self.directory / 'journal.json').read_text())['targets']['controller']['state'], 'rollback_pending')
        return {'passed': True} if self.complete else None

    def test_unhealthy_controller_restores_previous_image_and_blocks_exact_rollout(self):
        self.assertTrue(watchdog.recover(self.root, worker=self.worker, now=230))
        self.assertEqual(self.calls, ['observe', 'rollback'])
        report = json.loads((self.directory / 'journal.json').read_text())
        self.assertEqual(report['state'], 'blocked')
        self.assertEqual(report['targets']['controller']['state'], 'rolled_back')
        self.assertFalse((self.root / 'deployment/owner.json').exists())

    def test_healthy_or_starting_controller_is_not_interrupted(self):
        self.assertFalse(watchdog.recover(self.root, worker=self.worker, now=200))
        self.assertEqual(self.calls, [])
        self.healthy = True
        self.assertFalse(watchdog.recover(self.root, worker=self.worker, now=230))
        self.assertEqual(self.calls, ['observe'])

    def test_lost_rollback_reply_resumes_original_intent_after_backoff(self):
        self.complete = False
        self.assertFalse(watchdog.recover(self.root, worker=self.worker, now=230))
        self.assertTrue((self.root / 'deployment/owner.json').exists())
        self.calls.clear(); self.complete = True
        self.assertFalse(watchdog.recover(self.root, worker=self.worker, now=250))
        self.assertTrue(watchdog.recover(self.root, worker=self.worker, now=291))
        self.assertEqual(self.calls, ['rollback'])

    def test_unrelated_workload_and_changed_source_are_not_rolled_back(self):
        self.report['inventory']['targets'][0]['name'] = 'unrelated'
        atomic_json(self.directory / 'journal.json', self.report)
        self.assertFalse(watchdog.recover(self.root, worker=self.worker, now=1200))
        self.assertEqual(self.calls, [])
        self.report['inventory']['targets'][0]['name'] = 'gchat-release'
        self.report['sources'] = {}
        atomic_json(self.directory / 'journal.json', self.report)
        with self.assertRaises(ValueError): watchdog.recover(self.root, worker=self.worker, now=1200)
        self.assertEqual(self.calls, [])


if __name__ == '__main__': unittest.main()
