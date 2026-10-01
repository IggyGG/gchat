import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_infrastructure_bundle as bundle


class InfrastructureBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = {'release_id': 'a' * 64, 'sources': {'gcoms': {'commit': 'b' * 40, 'tree': 'c' * 40},
            'gchat': {'commit': 'd' * 40, 'tree': 'e' * 40}}}
        self.files = {name: name.encode() for name in bundle.FILES}
        self.build = {'release_id': self.manifest['release_id'],
                      'sources': self.manifest['sources'],
                      'gcoms_source': self.manifest['sources']['gcoms'],
                      'sha256': {name: hashlib.sha256(data).hexdigest() for name, data in self.files.items()}}

    def archive(self):
        archive = self.root / 'native.zip'
        with zipfile.ZipFile(archive, 'w') as output:
            output.writestr('signed/infrastructure/build.json', json.dumps(self.build))
            for name, data in self.files.items():
                output.writestr('signed/infrastructure/' + name, data)
        return archive

    def test_retains_only_hash_verified_provider_bytes(self):
        directory = self.root / 'retained'
        bundle.retain_archive(self.archive(), directory, self.manifest)
        self.assertEqual({p.name: p.read_bytes() for p in directory.iterdir()}, self.files)
        self.assertEqual(bundle.retain_archive(self.archive(), directory, self.manifest), self.build)

    def test_wrong_source_cannot_be_promoted(self):
        self.build['sources'] = {**self.manifest['sources'], 'gchat': {'commit': 'f' * 40, 'tree': '0' * 40}}
        with self.assertRaisesRegex(ValueError, 'frozen CI source'):
            bundle.retain_archive(self.archive(), self.root / 'retained', self.manifest)

    def test_provider_payload_hash_must_match(self):
        self.files['gcnode'] = b'changed executable'
        with self.assertRaisesRegex(ValueError, 'file changed'):
            bundle.retain_archive(self.archive(), self.root / 'retained', self.manifest)

    def test_existing_retained_bytes_cannot_be_replaced(self):
        directory = self.root / 'retained'
        bundle.retain_archive(self.archive(), directory, self.manifest)
        (directory / 'gcnode').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'retained source bundle changed'):
            bundle.retain_archive(self.archive(), directory, self.manifest)

    def test_manifest_cannot_write_outside_bundle(self):
        self.build['sha256']['../outside'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'unexpected or missing'):
            bundle.retain_archive(self.archive(), self.root / 'retained', self.manifest)
        self.assertFalse((self.root / 'outside').exists())

    def test_no_bundle_is_published_before_build_and_verify_receipts(self):
        with patch.object(bundle, 'publish') as publish:
            self.assertIsNone(bundle.collect(self.root, self.manifest, {}))
            publish.assert_not_called()

    def test_push_image_uses_its_own_qualified_configuration_and_repository(self):
        directory = self.root / 'retained'
        (directory / 'push-oci').mkdir(parents=True)
        (directory / 'push-oci/index.json').write_text('{}')
        expected_config = 'sha256:' + 'a' * 64
        (directory / 'source-build.json').write_text(json.dumps({'image_config': 'sha256:' + 'b' * 64,
                                                               'push_config': expected_config}))
        raw = json.dumps({'config': {'digest': expected_config}}).encode()
        config = {'push_registry_repository': 'registry/push', 'push_pull_repository': 'node/push'}
        with patch.object(bundle.subprocess, 'run') as copy, \
             patch.object(bundle.subprocess, 'check_output', return_value=raw):
            image = bundle.publish(directory, config, 'retained', 'push')
            self.assertEqual(image, 'node/push@sha256:' + hashlib.sha256(raw).hexdigest())
            self.assertEqual(copy.call_args.args[0][-1], 'docker://registry/push:retained')
        (directory / 'source-build.json').write_text(json.dumps({'push_config': 'sha256:' + 'b' * 64}))
        with patch.object(bundle.subprocess, 'run') as copy, \
             patch.object(bundle.subprocess, 'check_output', return_value=raw):
            with self.assertRaisesRegex(ValueError, 'qualified image configuration'):
                bundle.publish(directory, config, 'retained', 'push')
            copy.assert_not_called()

    def test_surviving_manifest_repairs_missing_layers_before_readback(self):
        directory = self.root / 'retained'
        (directory / 'oci').mkdir(parents=True)
        (directory / 'oci/index.json').write_text('{}')
        (directory / 'source-build.json').write_text(json.dumps({'image_config': 'sha256:' + 'f' * 64}))
        raw = json.dumps({'config': {'digest': 'sha256:' + 'f' * 64}}).encode()
        copied = False

        def copy(command, **kwargs):
            nonlocal copied
            self.assertIn('--preserve-digests', command)
            self.assertIn('oci:' + str(directory / 'oci') + ':release', command)
            copied = True  # Missing remote layers are restored by this copy.

        def inspect(command, **kwargs):
            if command[-1].startswith('docker://'):
                self.assertTrue(copied, 'manifest inspection alone cannot establish blob availability')
            return raw

        config = {'registry_repository': 'registry/services', 'pull_repository': 'node/services'}
        with patch.object(bundle.subprocess, 'run', side_effect=copy), \
             patch.object(bundle.subprocess, 'check_output', side_effect=inspect):
            expected = 'node/services@sha256:' + hashlib.sha256(raw).hexdigest()
            self.assertEqual(bundle.publish(directory, config, 'retained'), expected)
        self.assertTrue(copied)


if __name__ == '__main__': unittest.main()
