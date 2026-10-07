import copy
import hashlib
import json
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

    def test_unconfigured_controller_is_noop(self):
        owner = SimpleNamespace(config={})
        controller.reconcile(owner)
        controller.close(owner)


if __name__ == '__main__': unittest.main()
