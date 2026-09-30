import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_deployment import reconcile


@unittest.skipUnless(os.name == 'posix', 'deployment owner uses POSIX locks')
class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = {'release_id': 'a' * 64, 'sources': {'gcoms': {'commit': 'b' * 40}}}
        self.config = {'targets': [{'id': name, 'workers': {stage: ['worker'] for stage in
            ('observe', 'prepare', 'activate', 'rollback', 'check')}} for name in ('canary', 'relay-2')]}
        self.live = {name: {'healthy': True, 'matches': False, 'running': {'sha256': 'old'}}
                     for name in ('canary', 'relay-2')}
        self.calls = []
        self.fail = None

    def worker(self, target, stage, manifest, directory, previous=None):
        name = target['id']
        self.calls.append((name, stage))
        if (name, stage) == self.fail:
            raise ValueError('injected canary failure')
        if stage == 'observe':
            return dict(self.live[name])
        if stage == 'activate':
            self.live[name] = {'healthy': True, 'matches': True, 'running': {'sha256': 'new'}}
        if stage == 'rollback':
            self.live[name] = dict(previous)
        return {'passed': True}

    def tick(self):
        return reconcile(self.root, self.manifest, self.config, self.worker, now=100)

    def test_serial_canary_and_fresh_all_target_observation(self):
        self.assertFalse(self.tick())
        self.assertTrue(self.live['canary']['matches'])
        self.assertFalse(self.live['relay-2']['matches'])
        self.assertFalse(self.tick())
        self.assertTrue(self.tick())
        self.assertEqual([name for name, stage in self.calls if stage == 'activate'], ['canary', 'relay-2'])
        self.live['relay-2']['matches'] = False
        self.assertFalse(self.tick())
        self.assertTrue(self.live['relay-2']['matches'])

    def test_failed_canary_rolls_back_and_never_advances(self):
        self.fail = ('canary', 'check')
        self.assertFalse(self.tick())
        self.assertFalse(self.live['canary']['matches'])
        count = len(self.calls)
        self.assertFalse(self.tick())
        self.assertEqual(count, len(self.calls))
        self.assertNotIn(('relay-2', 'activate'), self.calls)

    def test_two_unhealthy_targets_do_not_trigger_mutation(self):
        for item in self.live.values(): item['healthy'] = False
        self.assertFalse(self.tick())
        self.assertTrue(all(stage == 'observe' for _, stage in self.calls))

    def test_one_existing_failure_is_repaired_before_healthy_canary(self):
        self.live['relay-2']['healthy'] = False
        self.assertFalse(self.tick())
        self.assertEqual([name for name, stage in self.calls if stage == 'activate'], ['relay-2'])

    def test_crash_after_activation_observes_and_checks_before_advancing(self):
        ordinary = self.worker
        def crash(target, stage, *args):
            result = ordinary(target, stage, *args)
            if stage == 'activate': raise KeyboardInterrupt()
            return result
        with self.assertRaises(KeyboardInterrupt):
            reconcile(self.root, self.manifest, self.config, crash)
        self.calls.clear()
        self.assertFalse(self.tick())
        self.assertIn(('canary', 'check'), self.calls)
        self.assertNotIn(('canary', 'activate'), self.calls)
        self.assertNotIn(('relay-2', 'activate'), self.calls)

    def test_another_release_cannot_interleave_an_active_rollout(self):
        self.tick()
        other = {**self.manifest, 'release_id': 'c' * 64}
        count = len(self.calls)
        self.assertFalse(reconcile(self.root, other, self.config, self.worker))
        self.assertEqual(len(self.calls), count)

    def test_corrected_inventory_preserves_failure_and_allows_reconciliation(self):
        self.fail = ('canary', 'check'); self.tick(); self.fail = None
        self.config['revision'] = 2
        self.assertFalse(self.tick())
        self.assertTrue(self.live['canary']['matches'])
        retained = list((self.root / 'deployment' / self.manifest['release_id']).glob('revision-*.json'))
        self.assertEqual(len(retained), 1)
        self.assertEqual(json.loads(retained[0].read_text())['state'], 'blocked')


if __name__ == '__main__': unittest.main()
