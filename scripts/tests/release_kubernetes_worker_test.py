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
