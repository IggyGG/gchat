"""Select immutable release artifacts before changing either public feed."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_publish
from release_coordinator import atomic_json, read_receipt


class PublishSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paths = []
        for name in ('GChat.AppImage', 'GChat.AppImage.sig', 'GChat.deb', 'GChat.deb.asc'):
            self.paths.append(self.artifact(name, name.encode()))

    def artifact(self, name, data):
        path = self.root / (hashlib.sha256(data).hexdigest() + '-' + name)
        path.write_bytes(data)
        return path

    def test_installer_also_referenced_as_updater_is_one_artifact(self):
        # Mirrors the actual Linux verification receipt, including repeated signatures.
        self.assertEqual(release_publish.select_artifacts(self.paths * 2, 'linux-x86_64'),
                         tuple(self.paths))

    def test_two_distinct_debian_candidates_are_rejected(self):
        second = self.artifact('GChat.deb', b'other build')
        with self.assertRaisesRegex(ValueError, 'Debian package.*ambiguous'):
            release_publish.select_artifacts(self.paths + [second], 'linux-x86_64')

    def test_missing_or_ambiguous_debian_signature_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Debian signature'):
            release_publish.select_artifacts(self.paths[:-1], 'linux-x86_64')
        other = self.artifact('GChat.deb.asc', b'other signature')
        with self.assertRaisesRegex(ValueError, 'Debian signature'):
            release_publish.select_artifacts(self.paths + [other], 'linux-x86_64')

    def test_duplicate_reference_does_not_hide_conflicting_hash(self):
        manifest = {'release_id': 'a' * 64, 'sources': {}}
        receipt = dict(schema=1, **manifest, platform='linux-x86_64', stage='verify',
                       passed=True, source_unchanged=True,
                       evidence=[{'path': self.paths[0].name,
                                  'sha256': hashlib.sha256(self.paths[0].read_bytes()).hexdigest()},
                                 {'path': self.paths[0].name, 'sha256': '0' * 64}])
        target = self.root / 'receipt.json'
        atomic_json(target, receipt)
        with self.assertRaisesRegex(ValueError, 'evidence changed'):
            read_receipt(target, manifest, 'linux-x86_64', 'verify')

    def test_invalid_package_cannot_publish_updater_pointer_first(self):
        manifest = {'release_id': 'a' * 64, 'sources': {}, 'policy': {}}
        candidate = self.root / 'candidate.json'
        atomic_json(candidate, manifest)
        config = self.root / 'config.json'
        atomic_json(config, {})
        evidence = {'evidence': [{'path': p.name} for p in self.paths[:-1]]}
        with patch.dict('os.environ', GCHAT_RELEASE_MANIFEST=str(candidate),
                        GCHAT_RELEASE_TARGET='linux-x86_64',
                        GCHAT_RELEASE_RECEIPT=str(self.root / 'output.json')), \
             patch.object(sys, 'argv', ['release_publish', '--state', str(self.root),
                                        '--config', str(config)]), \
             patch.object(release_publish, 'validate', return_value=manifest), \
             patch.object(release_publish, 'job', return_value=self.root), \
             patch.object(release_publish, 'read_receipt', return_value=(evidence, 'hash')), \
             patch.object(release_publish, 'publish') as publish:
            with self.assertRaisesRegex(ValueError, 'Debian signature'):
                release_publish.main()
            publish.assert_not_called()


if __name__ == '__main__':
    unittest.main()
