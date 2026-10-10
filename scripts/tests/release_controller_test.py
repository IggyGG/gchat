import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from release_automation_test import candidate
from release_pair import canonical
import release_controller as controller


def intent_fixture(state):
    before = {key: str(i) * 64 for i, key in enumerate(
        ('artifacts', 'infrastructure', 'controller', 'qualification'), 1)}
    after = dict(before, controller='5' * 64, qualification='6' * 64)
    baseline = candidate()
    sources = copy.deepcopy(baseline['sources'])
    sources['gchat'] = {'commit': 'd' * 40, 'tree': 'e' * 40}
    return controller.queue(state, baseline, sources, before, after)


class ControllerTests(unittest.TestCase):
    def test_quiescence_skips_artifact_trees_but_checks_all_followup_branches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / 'jobs' / ('a' * 64)
            artifact = original / 'native' / 'ios-output' / 'Index.noindex'
            controller.save(artifact / 'acceptance-intent.json', {'cleaned': False})
            controller.save(original / 'acceptance-intent.json', {'cleaned': True})
            first = original / 'followups' / ('b' * 40)
            second = original / 'followups' / ('c' * 40)
            nested = first / 'followups' / ('d' * 40)
            for work in (first, second, nested):
                controller.save(work / 'acceptance-intent.json', {'cleaned': True})
            owner = SimpleNamespace(state=root, running_workers={},
                                    deployment_runner=SimpleNamespace(pending=None))
            visited = []
            original_scandir = os.scandir
            def bounded_scandir(path):
                path = Path(path)
                self.assertFalse(path.is_relative_to(original / 'native'),
                                 'quiescence descended into an extracted artifact')
                visited.append(path)
                return original_scandir(path)
            with patch('release_controller.os.scandir', side_effect=bounded_scandir), \
                 patch('release_controller.time.time', return_value=1000):
                self.assertTrue(controller.quiescent(owner))
                self.assertEqual(set(visited), {root / 'jobs', original / 'followups', first / 'followups'})
                for work in (second, nested):
                    controller.save(work / 'acceptance-intent.json', {'cleaned': False, 'delivery_protocol': 'sealed'})
                    controller.save(work / 'sealed-delivery.json', {'expires_at': 5000})
                    self.assertFalse(controller.quiescent(owner))
                    controller.save(work / 'acceptance-intent.json', {'cleaned': True})
                self.assertTrue(controller.quiescent(owner))

    @unittest.skipUnless(os.name == 'posix', 'retained controller state uses POSIX directories')
    def test_quiescence_refuses_symlinked_followup_without_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / 'jobs' / ('a' * 64)
            controller.save(original / 'acceptance-intent.json', {'cleaned': True})
            (original / 'followups').symlink_to(root / 'jobs', target_is_directory=True)
            owner = SimpleNamespace(state=root, running_workers={},
                                    deployment_runner=SimpleNamespace(pending=None))
            with self.assertRaisesRegex(ValueError, 'followup directory is a symlink'):
                controller.quiescent(owner)

    def test_intent_is_idempotent_and_never_changes_application_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = intent_fixture(root)
            self.assertEqual(first, intent_fixture(root))
            self.assertEqual(first['baseline'], candidate())
            self.assertEqual(len(list(root.glob('controller-updates/*/intent.json'))), 1)
            self.assertFalse((root / 'incoming').exists())
            changed = copy.deepcopy(first)
            changed['baseline']['versions']['android'] = '9'
            with self.assertRaises(ValueError): controller.validate_intent(changed)
            for key in ('artifacts', 'infrastructure'):
                changed = copy.deepcopy(first); changed['inputs'][key] = 'f' * 64
                changed['id'] = hashlib.sha256(canonical({k:v for k,v in changed.items() if k != 'id'})).hexdigest()
                with self.assertRaisesRegex(ValueError, 'changes application'):
                    controller.validate_intent(changed)

    def test_rechecks_both_original_git_inventories(self):
        with tempfile.TemporaryDirectory() as temporary:
            intent = intent_fixture(Path(temporary))
            with patch('release_inputs.fingerprints', side_effect=[intent['inputs'], intent['baseline_inputs']]):
                self.assertEqual(controller.verify_inputs(intent, {}), candidate())
            with patch('release_inputs.fingerprints', return_value=intent['baseline_inputs']):
                with self.assertRaisesRegex(ValueError, 'committed input'):
                    controller.verify_inputs(intent, {})

    def test_overlay_is_release_bound_and_uses_existing_image_validator(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); intent = intent_fixture(root)
            original = {'schema': 1, 'targets': [{'id': 'relay-1'}, {'id': 'controller',
                'kind': 'deployment', 'namespace': 'ghost-com', 'name': 'gchat-release', 'image': 'controller'}]}
            self.assertEqual(controller.deployment_config(root, candidate(), original), original)
            work = root / 'controller-updates' / intent['id']; proof = work / 'qualification.json'
            controller.save(proof, {'image': 'repository@sha256:' + 'a' * 64})
            controller.save(root / 'controller-updates/active' / (candidate()['release_id'] + '.json'),
                {'id': intent['id'], 'release_id': candidate()['release_id'], 'qualification_sha256': controller.sha(proof)})
            with patch('release_kubernetes_worker.expected_image') as validate:
                result = controller.deployment_config(root, candidate(), original)
                validate.assert_called_once()
            self.assertEqual(original['targets'][1].get('controller_qualification'), None)
            self.assertEqual(result['targets'][0], original['targets'][0])
            self.assertEqual(result['targets'][1]['controller_qualification_release_id'], candidate()['release_id'])
            self.assertEqual(controller.deployment_config(root, candidate(2), original), original)
            proof.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'qualification changed'):
                controller.deployment_config(root, candidate(), original)

    def test_blocked_controller_repair_uses_canary_and_rollback_without_rewriting_fleet(self):
        from release_deployment import reconcile
        for fail in (False, True):
            with self.subTest(fail=fail), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); intent = intent_fixture(root); baseline = candidate()
                work = root / 'controller-updates' / intent['id']
                proof = work / 'qualification.json'; controller.save(proof, {'image': 'qualified'})
                ready = {'id': intent['id'], 'release_id': baseline['release_id'],
                         'qualification_sha256': controller.sha(proof)}
                controller.save(work / 'ready.json', ready)
                controller.save(root / 'controller-updates/active' / (baseline['release_id'] + '.json'), ready)
                controller.save(root / 'deployment/desired.json', {'release_id': baseline['release_id']})
                journal = root / 'deployment' / baseline['release_id'] / 'journal.json'
                controller.save(journal, {'state': 'blocked', 'sources': baseline['sources'],
                    'targets': {'controller': {'state': 'deployed'}, 'relay-2': {'state': 'check_failed'}}})
                original = journal.read_bytes()
                controller.save(root / 'public/deployment.json', {'state': 'blocked'})
                inventory = {'targets': [{'id': 'relay-2'}, {'id': 'controller', 'workers': {
                    stage: ['worker'] for stage in ('observe', 'prepare', 'activate', 'check', 'rollback')}}]}
                with patch('release_kubernetes_worker.expected_image'):
                    config = controller.deployment_config(root, baseline, inventory)
                live = {'healthy': True, 'matches': False}; calls = []
                def worker(target, stage, manifest, directory, previous=None):
                    self.assertEqual(target['id'], 'controller'); calls.append(stage)
                    if stage == 'observe': return dict(live)
                    if stage == 'activate': live['matches'] = True
                    if stage == 'rollback': live.update(previous)
                    if stage == 'check' and fail: raise ValueError('failed actual canary')
                    return {'passed': True}
                for _ in range(3):
                    self.assertFalse(reconcile(root, baseline, config, worker))
                self.assertIn('check', calls)
                self.assertEqual(calls.count('activate'), 1)
                self.assertEqual(calls.count('rollback'), int(fail))
                self.assertEqual(live['matches'], not fail)
                self.assertEqual(journal.read_bytes(), original)
                self.assertEqual(controller.read(root / 'public/deployment.json'), {'state': 'blocked'})
                repaired = controller.read(work / 'deployment' / baseline['release_id'] / 'journal.json')
                self.assertEqual(repaired['state'], 'blocked' if fail else 'deployed')
                # An intervening fleet effect invalidates the frozen recovery
                # before even observation, while preserving its durable proof.
                controller.save(journal, {'state': 'blocked', 'sources': baseline['sources'],
                    'targets': {'controller': {'state': 'deployed'}, 'relay-2': {'state': 'activating'}}})
                calls.clear()
                self.assertFalse(reconcile(root, baseline, config, worker))
                self.assertEqual(calls, [])

    def test_dispatch_timeout_never_redispatches_and_retains_original_request(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); intent = intent_fixture(root)
            work = root / 'controller-updates' / intent['id']
            def provider(path, **kwargs):
                if '/runs?' in path: return {'workflow_runs': []}
                if path.startswith('git/ref/'): return {'object': {'sha': intent['sources']['gchat']['commit']}}
                raise subprocess.TimeoutExpired('provider', 30)
            with patch('release_provider.github', side_effect=provider) as call:
                with self.assertRaises(subprocess.TimeoutExpired): controller.collect(intent, work)
                self.assertTrue((work / 'dispatch.json').exists())
                call.reset_mock()
                self.assertIsNone(controller.collect(intent, work))
                self.assertEqual(call.call_count, 1)
                self.assertFalse(any(c.kwargs.get('method') == 'POST' for c in call.call_args_list))

    def test_changed_provider_source_stops_before_artifact_download(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); intent = intent_fixture(root)
            work = root / 'controller-updates' / intent['id']
            run = {'display_title': controller.PREFIX + intent['id'], 'head_sha': 'f' * 40}
            with patch('release_provider.github', return_value={'workflow_runs': [run]}) as call:
                with self.assertRaisesRegex(ValueError, 'source or workflow changed'):
                    controller.collect(intent, work)
                self.assertEqual(call.call_count, 1)

    def test_remote_acceptance_reader_blocks_activation_without_local_worker(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            owner = SimpleNamespace(state=root, running_workers={}, deployment_runner=SimpleNamespace(pending=None))
            self.assertTrue(controller.quiescent(owner))
            intent = root / 'jobs' / ('a' * 64) / 'acceptance-intent.json'
            controller.save(intent, {'cleaned': False, 'dispatch_reserved': True, 'created_at': 100})
            with patch('release_controller.time.time', return_value=200):
                self.assertFalse(controller.quiescent(owner))
            with patch('release_controller.time.time', return_value=4000):
                self.assertTrue(controller.quiescent(owner))
            controller.save(intent.parent / 'sealed-delivery.json', {'expires_at': 5000})
            with patch('release_controller.time.time', return_value=4000):
                self.assertFalse(controller.quiescent(owner))
            controller.save(intent, {'cleaned': True})
            self.assertTrue(controller.quiescent(owner))
            owner.running_workers['worker'] = object()
            self.assertFalse(controller.quiescent(owner))

    def test_cleaned_parent_cannot_hide_live_nested_followup_reader(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            owner = SimpleNamespace(state=root, running_workers={}, deployment_runner=SimpleNamespace(pending=None))
            original = root / 'jobs' / ('a' * 64)
            child = original / 'followups' / ('b' * 40)
            nested = child / 'followups' / ('c' * 40)
            controller.save(original / 'acceptance-intent.json', {'cleaned': True})
            controller.save(child / 'acceptance-intent.json', {'cleaned': True})
            controller.save(nested / 'acceptance-intent.json',
                            {'cleaned': False, 'dispatch_reserved': True, 'delivery_protocol': 1})
            controller.save(nested / 'sealed-delivery.json', {'expires_at': 5000})
            with patch('release_controller.time.time', return_value=4000):
                self.assertFalse(controller.quiescent(owner))
            controller.save(nested / 'acceptance-run.json', {'status': 'completed'})
            with patch('release_controller.time.time', return_value=4000):
                self.assertFalse(controller.quiescent(owner), 'unrevoked live authority still blocks replacement')
            with patch('release_controller.time.time', return_value=5001):
                self.assertTrue(controller.quiescent(owner))
            controller.save(nested / 'acceptance-intent.json', {'cleaned': True})
            with patch('release_controller.time.time', return_value=4000):
                self.assertTrue(controller.quiescent(owner))

    def test_unselected_baseline_waits_without_provider_calls(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); intent = intent_fixture(root)
            config = {'discovery': {p: {'mirror': p} for p in ('gchat', 'gcoms')}}
            with patch('release_controller.verify_inputs', return_value=candidate()), \
                    patch('release_controller.collect') as collect:
                controller.step(root, config)
            collect.assert_not_called()
            status = controller.read(root / 'controller-updates' / intent['id'] / 'status.json')
            self.assertEqual(status['state'], 'waiting_baseline')

    def test_controller_recovery_observes_its_deployed_target_without_rewriting_global_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); baseline = candidate(); work = root / 'repair'
            controller.save(root / 'deployment/desired.json', {'release_id': baseline['release_id']})
            path = root / 'deployment' / baseline['release_id'] / 'journal.json'
            journal = {'state': 'blocked', 'sources': baseline['sources'], 'inventory': {},
                       'targets': {'controller': {'state': 'deployed'}, 'unrelated': {'state': 'check_failed'}}}
            controller.save(path, journal); original = path.read_bytes()
            with patch('release_deployment.inventory', return_value=[{'id': 'controller'}]), \
                 patch('release_deployment.invoke', return_value={'healthy': True, 'matches': True}) as observe:
                self.assertTrue(controller.baseline_ready(root, baseline, work))
                self.assertEqual(observe.call_args.args[1], 'observe')
                self.assertEqual(path.read_bytes(), original)
                proof = controller.read(work / 'baseline-observation.json')
                self.assertEqual(proof['global_state'], 'blocked')
                self.assertEqual(proof['journal_sha256'], controller.sha(path))
                observe.return_value = {'healthy': True, 'matches': False}
                self.assertFalse(controller.baseline_ready(root, baseline, work))
            for changed in ({'operator_rollback': True}, {'sources': {}},
                            {'targets': {'controller': {'state': 'deployed'}, 'relay': {'state': 'activating'}}},
                            {'targets': {'controller': {'state': 'rollback_failed'}}}):
                controller.save(path, dict(journal, **changed))
                with patch('release_deployment.invoke') as observe:
                    self.assertFalse(controller.baseline_ready(root, baseline, work))
                    observe.assert_not_called()

    def test_unconfigured_controller_is_noop(self):
        owner = SimpleNamespace(config={})
        controller.reconcile(owner)
        controller.close(owner)


if __name__ == '__main__': unittest.main()
