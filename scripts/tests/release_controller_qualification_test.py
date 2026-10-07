"""Controller image evidence remains mandatory on both provider and local paths."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import controller_runtime as runtime
import release_controller as controller
import release_controller_test as fixtures
from release_pair import canonical


def bundle_fixture(root, intent):
    bundle = root / 'bundle'; bundle.mkdir()
    request = {'schema': 1, 'source': intent['sources']['gchat'],
               'files': {f'scripts/test-{i}.py': 'a' * 64 for i in range(len(runtime.SUITES))}}
    proof = {'schema': 1, 'passed': True, 'source': intent['sources']['gchat'],
        'source_unchanged': True, 'production_controller_revision_tested': True,
        'tests': runtime.MINIMUM_TESTS, 'source_files_verified': len(request['files']),
        'suites': list(runtime.SUITES), 'inventory_sha256': hashlib.sha256(canonical(request['files'])).hexdigest(),
        'configuration_digest': 'sha256:' + 'a' * 64}
    (bundle / 'controller-runtime.log').write_text('qualified test output\n')
    proof['log_sha256'] = controller.sha(bundle / 'controller-runtime.log')
    controller.save(bundle / 'controller-runtime.json', proof)
    controller.save(bundle / 'runtime-request.json', request)
    (bundle / 'controller.tar').write_bytes(b'archive fixture')
    build = {'schema': 1, 'passed': True, 'intent': intent, 'controller_config': proof['configuration_digest'],
        'sha256': {name: controller.sha(bundle / name) for name in
            ('controller.tar', 'controller-runtime.json', 'controller-runtime.log', 'runtime-request.json')}}
    controller.save(bundle / 'build.json', build)
    return bundle, request, proof


class ControllerQualificationTests(unittest.TestCase):
    def test_mutated_bundle_log_and_source_inventory_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); intent = fixtures.intent_fixture(root)
            bundle, request, proof = bundle_fixture(root, intent)
            controller.validate_bundle(intent, bundle)
            (bundle / 'controller-runtime.log').write_text('replacement')
            with self.assertRaisesRegex(ValueError, 'bundle file changed'):
                controller.validate_bundle(intent, bundle)
            build = controller.read(bundle / 'build.json')
            build['sha256']['controller-runtime.log'] = controller.sha(bundle / 'controller-runtime.log')
            controller.save(bundle / 'build.json', build)
            with self.assertRaisesRegex(ValueError, 'runtime log changed'):
                controller.validate_bundle(intent, bundle)

    def test_actual_kubernetes_success_binds_source_and_running_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); intent = fixtures.intent_fixture(root)
            bundle, request, proof = bundle_fixture(root, intent)
            work = root / 'proof'; work.mkdir()
            image = 'registry/controller@sha256:' + 'b' * 64
            target = {'probe_namespace': 'ghost-bench'}
            def create(argv, **kwargs):
                if 'get' in argv: return b''
                if 'create' in argv: return b'created'
                raise AssertionError(argv)
            with patch('release_controller.subprocess.check_output', side_effect=create):
                self.assertIsNone(controller.kubernetes_qualify(intent, bundle, image, target, work))
            job = controller.read(work / 'kubernetes-request.json')
            self.assertFalse(job['spec']['template']['spec']['automountServiceAccountToken'])
            self.assertEqual(job['spec']['template']['spec']['volumes'], [{'name': 'tmp', 'emptyDir': {'sizeLimit': '256Mi'}}])
            job['status'] = {'succeeded': 1}
            pod = {'metadata': {'name': 'qualified-pod', 'uid': 'exact-pod'}, 'status': {'containerStatuses': [{
                'imageID': image, 'state': {'terminated': {'exitCode': 0}}}]}}
            def completed(argv, **kwargs):
                if 'logs' in argv: return (json.dumps(proof) + '\n').encode()
                if 'pods' in argv: return canonical({'items': [pod]})
                return canonical(job)
            with patch('release_controller.subprocess.check_output', side_effect=completed):
                result = controller.kubernetes_qualify(intent, bundle, image, target, work)
                self.assertEqual(result['source'], intent['sources']['gchat'])
                pod['status']['containerStatuses'][0]['imageID'] = 'registry/controller@sha256:' + 'c' * 64
                with self.assertRaisesRegex(ValueError, 'image or exit status'):
                    controller.kubernetes_qualify(intent, bundle, image, target, work)
            saved = controller.read(work / 'kubernetes-runtime.json')
            self.assertEqual(saved['pod_uid'], 'exact-pod')
            self.assertEqual(saved['image_id'], image)


if __name__ == '__main__': unittest.main()
