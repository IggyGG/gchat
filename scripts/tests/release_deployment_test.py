import json
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_deployment import reconcile, inventory, request_rollback, handoff, write


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

    def test_short_checks_are_only_between_full_rollout_boundaries(self):
        targets = self.config['targets']
        config = {'targets': [targets[0], {**targets[1], 'id': 'middle'}, targets[1]],
                  'network_check_policy': 'boundaries-v1'}
        self.assertEqual([t['network_check'] for t in inventory(config)], ['full', 'chat', 'full'])
        with self.assertRaises(ValueError):
            inventory({'targets': [{**targets[0], 'network_check': 'chat'}]})
        with self.assertRaises(ValueError):
            inventory({**config, 'network_check_policy': 'unknown'})

    def test_operator_rollback_restores_previous_targets_without_reactivation(self):
        for _ in range(3): self.tick()
        from release_deployment import write
        write(self.root / 'deployment/desired.json', {'release_id': self.manifest['release_id']})
        request_rollback(self.root, self.manifest['release_id'])
        self.calls.clear()
        for _ in range(4): self.tick()
        self.assertEqual([name for name, stage in self.calls if stage == 'rollback'], ['relay-2', 'canary'])
        self.assertFalse(any(stage == 'activate' for _, stage in self.calls))
        self.assertFalse(any(value['matches'] for value in self.live.values()))
        journal = json.loads((self.root / 'deployment' / self.manifest['release_id'] / 'journal.json').read_text())
        self.assertEqual(journal['state'], 'rolled_back')
        self.assertFalse((self.root / 'deployment/owner.json').exists())

    def test_boundary_checks_run_even_when_controller_already_has_qualified_image(self):
        self.config['network_check_policy'] = 'boundaries-v1'
        for value in self.live.values(): value['matches'] = True
        for _ in range(3): self.tick()
        self.assertEqual([name for name, stage in self.calls if stage == 'check'], ['canary', 'relay-2'])
        self.assertFalse(any(stage == 'activate' for _, stage in self.calls))

    def test_failed_check_without_activation_does_not_restart_healthy_target(self):
        self.config['network_check_policy'] = 'boundaries-v1'
        for value in self.live.values(): value['matches'] = True
        self.fail = ('canary', 'check')
        self.tick()
        self.assertFalse(any(stage in ('activate', 'rollback') for _, stage in self.calls))

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

    def test_evicted_deployed_image_waits_for_kubernetes_without_rollback(self):
        for _ in range(3): self.tick()
        self.calls.clear()
        self.live['relay-2'].update(healthy=False, matches=False, configured_matches=True)
        self.assertFalse(self.tick())
        self.assertTrue(all(stage == 'observe' for _, stage in self.calls))
        report=json.loads((self.root/'deployment'/self.manifest['release_id']/'journal.json').read_text())
        self.assertEqual(report['state'],'deploying')
        self.assertEqual(report['targets']['relay-2']['state'],'deployed')
        self.live['relay-2'].update(healthy=True, matches=True)
        self.assertTrue(self.tick())

    def test_foreign_configured_image_still_requires_repair(self):
        for _ in range(3): self.tick()
        self.calls.clear()
        self.live['relay-2'].update(healthy=False, matches=False, configured_matches=False)
        self.assertFalse(self.tick())
        self.assertIn(('relay-2','activate'),self.calls)

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

    def test_inventory_revision_cannot_abandon_pending_rollback(self):
        ordinary = self.worker
        def pending(target, stage, *args):
            if stage == 'check': raise ValueError('canary failed')
            if stage == 'rollback': return None
            return ordinary(target, stage, *args)
        reconcile(self.root, self.manifest, self.config, pending, now=100)
        self.config = {'targets': [self.config['targets'][1]], 'revision': 2}
        self.calls.clear()
        self.assertFalse(reconcile(self.root, self.manifest, self.config, self.worker, now=200))
        self.assertEqual(self.calls, [('canary', 'rollback'), ('canary', 'observe')])
        self.assertFalse(self.live['canary']['matches'])
        journal = json.loads((self.root / 'deployment' / self.manifest['release_id'] / 'journal.json').read_text())
        self.assertEqual(journal['state'], 'blocked')
        self.assertEqual(journal['targets']['canary']['state'], 'rolled_back')

    def external_handoff(self):
        ordinary = self.worker
        def failed(target, stage, *args):
            if stage in ('check', 'rollback'): raise ValueError('failed old rollout')
            return ordinary(target, stage, *args)
        reconcile(self.root, self.manifest, self.config, failed, now=100)
        write(self.root / 'deployment/desired.json', {'release_id': self.manifest['release_id']})
        self.journal = self.root / 'deployment' / self.manifest['release_id'] / 'journal.json'
        self.original = self.journal.read_bytes()
        self.live['canary'] = {'healthy': True, 'matches': False, 'running': {'sha256': 'd' * 64}}
        self.calls.clear()
        return {'id': 'e' * 32, 'observed': {'canary': 'd' * 64}, 'reason': 'Retain installed capacity fix',
                'journal_sha256': hashlib.sha256(self.original).hexdigest()}

    def test_handoff_retains_hotfix_and_failure_then_new_release_can_deploy(self):
        request = self.external_handoff()
        handoff(self.root, self.manifest, request, self.worker)
        self.assertEqual(self.calls, [('canary', 'observe')])
        self.assertEqual(self.live['canary']['running']['sha256'], 'd' * 64)
        report = json.loads(self.journal.read_text())
        self.assertEqual(report['state'], 'handed_off')
        self.assertEqual(report['targets']['canary']['state'], 'rollback_failed')
        self.assertEqual(json.loads((self.journal.parent / ('before-handoff-' + request['id'] + '.json')).read_text()),
                         json.loads(self.original))
        self.assertFalse((self.root / 'deployment/owner.json').exists())
        self.calls.clear()
        self.config['revision'] = 2
        self.assertFalse(self.tick())
        self.assertEqual(self.calls, [])
        with self.assertRaises(ValueError): request_rollback(self.root, self.manifest['release_id'])
        other = {**self.manifest, 'release_id': 'f' * 64}
        self.assertFalse(reconcile(self.root, other, self.config, self.worker, now=200))
        self.assertIn(('canary', 'activate'), self.calls)

    def test_handoff_rejects_changed_journal_hash_unhealthy_artifact_and_missing_target(self):
        request = self.external_handoff()
        for change in ('journal', 'hash', 'health', 'target', 'same_previous', 'source'):
            with self.subTest(change=change):
                proposal = {**request, 'observed': dict(request['observed'])}
                observed = dict(self.live['canary'])
                manifest = self.manifest
                if change == 'journal': proposal['journal_sha256'] = '0' * 64
                if change == 'hash': proposal['observed']['canary'] = '0' * 64
                if change == 'health': self.live['canary']['healthy'] = False
                if change == 'target': proposal['observed'] = {'relay-2': 'd' * 64}
                if change == 'same_previous': self.live['canary']['matches'] = True
                if change == 'source': manifest = {**self.manifest, 'sources': {}}
                with self.assertRaises(ValueError): handoff(self.root, manifest, proposal, self.worker)
                self.live['canary'] = observed
                self.assertEqual(self.journal.read_bytes(), self.original)
                self.assertTrue((self.root / 'deployment/owner.json').exists())
                self.assertTrue(all(stage == 'observe' for _, stage in self.calls))

    def test_handoff_recovers_after_durable_record_without_clearing_a_new_owner(self):
        request = self.external_handoff()
        handoff(self.root, self.manifest, request, self.worker)
        owner = self.root / 'deployment/owner.json'
        write(owner, {'release_id': self.manifest['release_id']})
        self.calls.clear()
        handoff(self.root, self.manifest, request, self.worker)
        self.assertFalse(owner.exists())
        write(owner, {'release_id': 'f' * 64})
        handoff(self.root, self.manifest, request, self.worker)
        self.assertEqual(json.loads(owner.read_text())['release_id'], 'f' * 64)
        self.assertEqual(self.calls, [])


if __name__ == '__main__': unittest.main()
