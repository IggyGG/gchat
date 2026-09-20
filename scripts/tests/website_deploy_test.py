import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import website

spec = importlib.util.spec_from_file_location('deploy_website', SCRIPTS / 'deploy-website.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


def fixture():
    return {'metadata': {'name': 'gchat-site', 'uid': 'site-uid', 'generation': 3},
            'spec': {'replicas': 2, 'template': {'spec': {
                'containers': [{'name': 'nginx', 'image': 'retained-image', 'volumeMounts': [
                    {'name': 'content', 'mountPath': '/usr/share/nginx/html', 'readOnly': True}]}],
                'volumes': [{'name': 'content', 'configMap': {'name': 'previous'}},
                            {'name': 'nginx-conf', 'configMap': {'name': 'gchat-site-nginx'}}]}}}}


class KubernetesWebsiteTests(unittest.TestCase):
    def test_public_check_retries_whole_bundle_after_stale_upstream(self):
        def response(data):
            value = MagicMock()
            value.__enter__.return_value.status = 200
            value.__enter__.return_value.read.return_value = data
            return value
        hashes = {name: hashlib.sha256(data).hexdigest()
                  for name, data in [('index.html', b'page'), ('downloads.json', b'new')]}
        replies = [response(b'page'), response(b'old'), response(b'page'), response(b'new')]
        with patch.object(deploy, 'urlopen', side_effect=replies) as request, patch.object(deploy.time, 'sleep'):
            deploy.verify_public(hashes)
        self.assertEqual(request.call_count, 4)
        self.assertNotEqual(request.call_args_list[0].args[0].full_url,
                            request.call_args_list[2].args[0].full_url)

    def test_public_check_never_accepts_persistent_digest_mismatch(self):
        response = MagicMock()
        response.__enter__.return_value.status = 200
        response.__enter__.return_value.read.return_value = b'old'
        with patch.object(deploy, 'urlopen', return_value=response), self.assertRaisesRegex(ValueError, 'digest mismatch'):
            deploy.verify_public({'downloads.json': hashlib.sha256(b'new').hexdigest()}, timeout=0)

    def test_self_consistent_but_stale_output_cannot_claim_current_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            website.build(root, website.validate(json.loads((website.ROOT / 'release/downloads.json').read_text())))
            deploy.verify_source(root)
            (root / 'index.html').write_text('stale but internally consistent page')
            (root / 'build.json').write_text(json.dumps({'index_sha256': hashlib.sha256((root / 'index.html').read_bytes()).hexdigest(), 'version': None}))
            deploy.bundle(root, 'a' * 40)
            with self.assertRaisesRegex(ValueError, 'differs from current source'):
                deploy.verify_source(root)

    def test_bundle_round_trips_binary_font_and_existing_robots(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            website.build(root, {'schema': 1, 'version': None, 'artifacts': []})
            cm, hashes = deploy.configmap(root, 'a' * 40, 'ghost-com', 'gchat-site')
            self.assertTrue(cm['immutable'])
            self.assertEqual(cm['data']['robots.txt'], 'User-agent: *\nAllow: /\n')
            self.assertEqual(base64.b64decode(cm['binaryData']['fonts--fixedsys-excelsior.ttf']),
                             (root / 'fonts/fixedsys-excelsior.ttf').read_bytes())
            self.assertEqual(set(hashes), deploy.FILES)
            (root / 'fonts/fixedsys-excelsior.ttf').write_bytes(b'0' * (1024 * 1024))
            with self.assertRaisesRegex(ValueError, 'size limit'):
                deploy.configmap(root, 'a' * 40, 'ghost-com', 'gchat-site')

    def test_only_expected_document_root_can_be_changed(self):
        before = fixture()
        operations = deploy.volume_patch(before, deploy.version_volume('next'))
        self.assertEqual([o['op'] for o in operations], ['test', 'test', 'test', 'replace'])
        self.assertEqual(operations[0]['value'], 'site-uid')
        self.assertEqual(operations[1]['value'], 3)
        self.assertEqual(operations[-1]['path'], '/spec/template/spec/volumes/0')
        for override in ({'mountPath': '/elsewhere'}, {'readOnly': False}, {'subPath': 'index.html'}):
            changed = copy.deepcopy(before)
            changed['spec']['template']['spec']['containers'][0]['volumeMounts'][0].update(override)
            with self.assertRaises(ValueError):
                deploy.content_volume(changed)

    def test_existing_version_cannot_be_overwritten(self):
        desired = {'metadata': {'name': 'next', 'annotations': {'gchat.boo/bundle-version': 'revision'}},
                   'immutable': True, 'data': {'index.html': 'expected'}, 'binaryData': {}}
        kube = Mock()
        kube.get.return_value = copy.deepcopy(desired)
        deploy.ensure_configmap(kube, desired)
        kube.run.assert_not_called()
        kube.get.return_value['data']['index.html'] = 'tampered'
        with self.assertRaises(ValueError):
            deploy.ensure_configmap(kube, desired)
        kube.run.assert_not_called()

    def test_failed_public_check_restores_only_previous_content(self):
        before = fixture()
        target = deploy.version_volume('next')
        after = copy.deepcopy(before)
        after['spec']['template']['spec']['volumes'][0] = target
        after['metadata']['generation'] += 1
        kube = Mock()
        kube.get.return_value = after
        kube.patch.return_value = before
        with patch.object(deploy, 'wait_ready', return_value=after), patch.object(deploy, 'verify_public', side_effect=ValueError('digest mismatch')):
            with self.assertRaisesRegex(RuntimeError, 'previous content restored'):
                deploy.activate(kube, before, target, {})
        self.assertEqual(kube.patch.call_count, 2)
        self.assertEqual(kube.patch.call_args.args, (after, before['spec']['template']['spec']['volumes'][0]))

    def test_failed_update_does_not_overwrite_a_newer_pod_template(self):
        before = fixture()
        newer = copy.deepcopy(before)
        newer['spec']['template']['spec']['containers'][0]['image'] = 'operator-update'
        kube = Mock()
        kube.get.return_value = newer
        with patch.object(deploy, 'wait_ready', side_effect=RuntimeError('concurrent update')):
            with self.assertRaisesRegex(RuntimeError, 'no newer deployment was overwritten'):
                deploy.activate(kube, before, deploy.version_volume('next'), {})
        self.assertEqual(kube.patch.call_count, 1)

    def test_lost_patch_acknowledgement_can_restore_the_applied_volume(self):
        before = fixture()
        target = deploy.version_volume('next')
        after = copy.deepcopy(before)
        after['spec']['template']['spec']['volumes'][0] = target
        kube = Mock()
        kube.get.return_value = after
        kube.patch.side_effect = [RuntimeError('connection lost'), before]
        with patch.object(deploy, 'wait_ready'):
            with self.assertRaisesRegex(RuntimeError, 'previous content restored'):
                deploy.activate(kube, before, target, {})
        self.assertEqual(kube.patch.call_count, 2)

    def test_readiness_requires_all_replicas_on_the_expected_template(self):
        current = fixture()
        current['status'] = {'observedGeneration': 3, 'replicas': 2, 'updatedReplicas': 2,
                             'readyReplicas': 1, 'availableReplicas': 1}
        kube = Mock()
        kube.get.return_value = current
        with self.assertRaisesRegex(RuntimeError, 'did not become ready'):
            deploy.wait_ready(kube, current, timeout=0)
        current['status'].update(readyReplicas=2, availableReplicas=2)
        self.assertEqual(deploy.wait_ready(kube, current, timeout=0), current)


if __name__ == '__main__':
    unittest.main()
