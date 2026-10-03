import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_kubernetes_worker as worker


class KubernetesWorkerTests(unittest.TestCase):
    def test_worker_entry_point_observes_the_qualified_bundle_without_preparation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = {'release_id': 'b' * 64, 'sources': {'gchat': 'original', 'gcoms': 'companion'}}
            directory = root / manifest['release_id']
            directory.mkdir()
            build = {'sources': manifest['sources'], 'qualified': True, 'images': {'gcnode': self.image}}
            (directory / 'build.json').write_text(json.dumps(build))
            target = {**self.target, 'artifact_root': str(root), 'image': 'gcnode'}
            observed = {'healthy': True, 'matches': True, 'running': {'image': self.image}}
            with patch.object(worker, 'observe', return_value=observed) as observe:
                self.assertEqual(worker.run(target, manifest, 'observe', root / 'result.json'), observed)
                observe.assert_called_once_with(target, self.image)
            build['qualified'] = False
            (directory / 'build.json').write_text(json.dumps(build))
            with patch.object(worker, 'observe') as observe, self.assertRaisesRegex(ValueError, 'qualified'):
                worker.run(target, manifest, 'observe', root / 'result.json')
            observe.assert_not_called()

    def test_independent_controller_pin_requires_complete_sealed_native_qualification(self):
        import hashlib
        import controller_runtime
        source = {'commit': 'b' * 40, 'tree': 'c' * 40}
        configuration = 'sha256:' + 'd' * 64
        runtime = {'schema': 1, 'passed': True, 'source': source, 'source_unchanged': True,
            'production_controller_revision_tested': True, 'suites': list(controller_runtime.SUITES),
            'tests': controller_runtime.MINIMUM_TESTS, 'source_files_verified': 222,
            'inventory_sha256': 'e' * 64, 'configuration_digest': configuration}
        proof = {'schema': 1, 'source': source, 'runtime': runtime, 'configuration': configuration,
                 'registry_configuration_verified': True, 'image': 'registry/controller@sha256:' + 'f' * 64,
                 'kubernetes_validation': {'source': source['commit'], 'tests': runtime['tests'],
                    'source_files_verified': 222, 'previous_digest_retained_and_repaired': True}}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'qualified.json'
            target = {'kind': 'deployment', 'namespace': 'ghost-com', 'name': 'gchat-release',
                      'image': 'controller', 'controller_qualification': str(path)}
            def seal(value):
                path.write_text(json.dumps(value))
                target['controller_qualification_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            seal(proof)
            self.assertEqual(worker.expected_image(target, {}), proof['image'])
            path.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'changed'):
                worker.expected_image(target, {})
            for field, value in [('registry_configuration_verified', False), ('kubernetes_validation', {}),
                                 ('image', 'registry/controller:latest'), ('runtime', {**runtime, 'passed': False})]:
                seal({**proof, field: value})
                with self.subTest(field=field), self.assertRaises(ValueError):
                    worker.expected_image(target, {})
            seal(proof)
            with self.assertRaisesRegex(ValueError, 'outside'):
                worker.expected_image({**target, 'name': 'other-workload'}, {})
    def setUp(self):
        self.image = 'registry/gcnode@sha256:' + 'a' * 64
        self.target = {'kind': 'statefulset', 'namespace': 'ghost-com', 'name': 'gc-anchor',
                       'pod': 'gc-anchor-2', 'containers': ['gcnode', 'gcnode-keygen'], 'ordinal': 2}
        self.current = {'metadata': {'resourceVersion': '123'}, 'spec': {'replicas': 3,
            'template': {'spec': {'containers': [{'name': 'gcnode', 'image': 'old', 'args': ['serve'],
                                                  'volumeMounts': [{'name': 'identity'}]}],
                                  'initContainers': [{'name': 'gcnode-keygen', 'image': 'old'}],
                                  'volumes': [{'name': 'identity', 'persistentVolumeClaim': {'claimName': 'keep'}}]}}}}
        self.pod = {'metadata': {'uid': 'same-pvc-new-pod'}, 'status': {
            'conditions': [{'type': 'Ready', 'status': 'True'}],
            'containerStatuses': [{'name': 'gcnode', 'imageID': self.image}],
            'initContainerStatuses': [{'name': 'gcnode-keygen', 'imageID': self.image}]}}

    def observe(self):
        with patch.object(worker, 'resource', return_value=self.current), \
                patch.object(worker, 'kubectl', return_value=json.dumps(self.pod).encode()):
            return worker.observe(self.target, self.image)

    def test_both_runtime_and_init_images_are_observed(self):
        self.assertTrue(self.observe()['matches'])
        self.pod['status']['initContainerStatuses'][0]['imageID'] = 'registry/gcnode@sha256:' + 'b' * 64
        self.assertFalse(self.observe()['matches'])

    def test_pinned_image_without_ready_process_is_not_healthy(self):
        self.pod['status']['conditions'][0]['status'] = 'False'
        report = self.observe()
        self.assertTrue(report['matches']); self.assertFalse(report['healthy'])

    def test_patch_updates_only_named_images_and_partition(self):
        before = copy.deepcopy(self.current)
        with patch.object(worker, 'kubectl') as command:
            worker.patch_images(self.target, self.current, {name: self.image for name in self.target['containers']}, 2)
        payload = json.loads(command.call_args.args[-1])
        self.assertEqual(payload['metadata'], {'resourceVersion': '123'})
        self.assertEqual(payload['spec']['updateStrategy']['rollingUpdate']['partition'], 2)
        pod = payload['spec']['template']['spec']
        self.assertEqual(set(pod), {'containers', 'initContainers'})
        self.assertEqual(set(pod['containers'][0]), {'name', 'image'})
        self.assertEqual(self.current, before)

    def test_disabled_workload_is_never_started(self):
        self.current['spec']['replicas'] = 0
        with self.assertRaisesRegex(ValueError, 'disabled'):
            self.observe()

    def test_incomplete_identity_observation_cannot_qualify(self):
        self.target.update(identity_container='gcnode', identity_paths=['/var/lib/gc/ks.bin', '/var/lib/gc/tls-identity.bin'])
        with patch.object(worker, 'kubectl', return_value=(('a' * 64) + '  /var/lib/gc/ks.bin\n').encode()):
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                worker.identities(self.target)

    def test_lower_ordinal_rollback_replaces_only_failed_pod_and_restores_prior_partition(self):
        old = 'registry/gcnode@sha256:' + 'b' * 64
        before = {'images': {name: self.image for name in self.target['containers']},
                  'pod_images': {name: old for name in self.target['containers']},
                  'partition': 2, 'identities': {'identity': 'unchanged'}}
        self.target.update(pod='gc-anchor-1', ordinal=1)
        failed = {'metadata': {'uid': 'failed-pod'}}
        replacement = {'metadata': {'uid': 'restored-pod'}}
        healthy = {'healthy': True, 'matches': True, 'running': {}}
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(worker, 'kubectl', return_value=json.dumps(failed).encode()) as kubectl, \
                patch.object(worker, 'patch_images') as patch_images, \
                patch.object(worker, 'observe', return_value=healthy), \
                patch.object(worker, 'identities', return_value=before['identities']), \
                patch.object(worker, 'resource', return_value=self.current):
            journal = Path(tmp) / 'before.json'
            self.assertIsNone(worker.rollback_stateful(self.target, self.current, before, journal))
            self.assertTrue(journal.is_file())
            self.assertEqual(patch_images.call_args.kwargs, {'on_delete': True})
            self.assertEqual(patch_images.call_args.args[2], before['pod_images'])
            self.assertEqual(kubectl.call_args.args[1:], ('delete', 'pod', 'gc-anchor-1', '--wait=false'))
            # A lost delete reply resumes from the retained failed UID. The new
            # pod and every healthy higher ordinal must survive reconciliation.
            kubectl.reset_mock(); kubectl.return_value = json.dumps(replacement).encode()
            resumed = json.loads(journal.read_text())
            self.assertTrue(worker.rollback_stateful(self.target, self.current, resumed, journal)['passed'])
            self.assertEqual(patch_images.call_args.args[2:], (before['images'], 2))
            self.assertFalse(any('delete' in call.args for call in kubectl.call_args_list))
            self.assertEqual(json.loads(journal.read_text())['rollback']['state'], 'complete')


if __name__ == '__main__': unittest.main()
