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
        self.manifest = {'release_id': 'a' * 64, 'sources': {'gcoms': {'commit': 'b' * 40, 'tree': 'c' * 40}}}
        self.files = {name: name.encode() for name in
                      (*bundle.BINARIES, 'Dockerfile', 'image.tar', 'ca-certificates.crt')}
        self.build = {'release_id': self.manifest['release_id'],
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
        self.build['gcoms_source'] = {'commit': 'd' * 40, 'tree': 'e' * 40}
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


if __name__ == '__main__': unittest.main()
