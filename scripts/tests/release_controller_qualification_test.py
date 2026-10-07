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
            target = {'probe_namespace': 'ghost-bench', 'probe_dns_nameservers': ['10.96.254.54']}
            def create(argv, **kwargs):
                if 'get' in argv: return b''
                if 'create' in argv: return b'created'
                raise AssertionError(argv)
            with patch('release_controller.subprocess.check_output', side_effect=create):
                self.assertIsNone(controller.kubernetes_qualify(intent, bundle, image, target, work))
            job = controller.read(work / 'kubernetes-request.json')
            spec = job['spec']['template']['spec']
            self.assertEqual(spec['dnsPolicy'], 'None')
            self.assertEqual(spec['dnsConfig'], {'nameservers': ['10.96.254.54']})
            self.assertEqual(spec['affinity'], {'nodeAffinity': {
                'requiredDuringSchedulingIgnoredDuringExecution': {'nodeSelectorTerms': [{
                    'matchExpressions': [{'key': 'kubernetes.io/hostname',
                        'operator': 'NotIn', 'values': ['triform-1']}]}]}}})
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

    def test_invalid_probe_dns_is_rejected_before_any_kubernetes_request(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); intent = fixtures.intent_fixture(root)
            bundle, _, _ = bundle_fixture(root, intent)
            work = root / 'proof'; work.mkdir()
            for dns in ([], ['10.96.254.54'] * 4, '10.96.254.54', ['not-an-address']):
                with self.subTest(dns=dns), patch('release_controller.subprocess.check_output') as kube:
                    with self.assertRaises(ValueError):
                        controller.kubernetes_qualify(intent, bundle, 'registry@sha256:' + 'b' * 64,
                            {'probe_namespace': 'ghost-bench', 'probe_dns_nameservers': dns}, work)
                    kube.assert_not_called()
                    self.assertFalse((work / 'kubernetes-request.json').exists())

    def test_retained_job_cannot_change_dns_or_scheduling_constraints(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); intent = fixtures.intent_fixture(root)
            bundle, _, _ = bundle_fixture(root, intent)
            work = root / 'proof'; work.mkdir()
            target = {'probe_namespace': 'ghost-bench', 'probe_dns_nameservers': ['10.96.254.54']}
            image = 'registry@sha256:' + 'b' * 64
            with patch('release_controller.subprocess.check_output', side_effect=[b'', b'created']):
                self.assertIsNone(controller.kubernetes_qualify(intent, bundle, image, target, work))
            for key, replacement in (('dnsPolicy', 'ClusterFirst'), ('dnsConfig', {'nameservers': ['8.8.8.8']}),
                                     ('affinity', {})):
                job = controller.read(work / 'kubernetes-request.json')
                job['spec']['template']['spec'][key] = replacement
                with self.subTest(key=key), patch('release_controller.subprocess.check_output', return_value=canonical(job)):
                    with self.assertRaisesRegex(ValueError, 'qualification job changed'):
                        controller.kubernetes_qualify(intent, bundle, image, target, work)


if __name__ == '__main__': unittest.main()
