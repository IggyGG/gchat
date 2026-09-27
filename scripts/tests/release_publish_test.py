"""Select immutable release artifacts before changing either public feed."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_publish
from release_coordinator import atomic_json, read_receipt
from release_automation_test import candidate


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


class DownloadPageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = candidate()
        self.release = self.manifest['release_id']
        number = self.manifest['versions']['linux-x86_64']
        self.url = 'https://gchat.boo/updates'
        self.apt = {'package': f'pool/{self.release}/g-chat_{number}_amd64.deb',
                    'sha256': hashlib.sha256(b'package').hexdigest()}
        package = self.root / 'apt' / self.apt['package']
        package.parent.mkdir(parents=True); package.write_bytes(b'package')
        self.signature = self.root / 'source.asc'; self.signature.write_bytes(b'signature')
        self.feed = {'version': number, 'notes': 'Privacy <unqualified>',
                     'url': f'{self.url}/artifacts/{self.release}/' + 'b' * 64 + '.AppImage',
                     'binding': json.dumps({'release_id': self.release, 'version': number,
                                            'target': 'linux-x86_64', 'sha256': 'b' * 64})}
        self.pointer = self.root / 'desktop/linux/x86_64/latest.json'
        self.pointer.parent.mkdir(parents=True)
        atomic_json(self.pointer, self.feed)

    def publish(self):
        return release_publish.linux_download_page(self.manifest, self.feed, self.apt,
                                                   self.signature, self.root, self.url)

    def test_current_page_has_immutable_links_and_is_idempotent(self):
        latest = self.publish(); before = latest.read_bytes()
        self.assertEqual(self.publish().read_bytes(), before)
        self.assertIn((self.url + '/apt/' + self.apt['package']).encode(), before)
        self.assertIn(b'Privacy &lt;unqualified&gt;', before)
        details = json.loads((latest.parent / self.release / 'release.json').read_text())
        self.assertEqual(details['sources'], self.manifest['sources'])
        self.assertEqual(details['updater'], self.feed)
        self.assertEqual((latest.parent / self.release / 'package.asc').read_bytes(), b'signature')

    def test_old_candidate_cannot_overwrite_current_page(self):
        latest = self.publish(); original = latest.read_bytes()
        atomic_json(self.pointer, {**self.feed, 'version': '999.0.0'})
        with self.assertRaisesRegex(ValueError, 'do not regress'):
            self.publish()
        self.assertEqual(latest.read_bytes(), original)

    def test_changed_package_or_immutable_details_fail_without_replacement(self):
        latest = self.publish(); original = latest.read_bytes()
        package = self.root / 'apt' / self.apt['package']; package.write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError, 'APT artifact'):
            self.publish()
        package.write_bytes(b'package')
        self.signature.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'immutable'):
            self.publish()
        self.assertEqual(latest.read_bytes(), original)

    def test_wrong_release_or_public_location_rejected(self):
        self.feed['url'] = 'https://another.example/download'
        with self.assertRaisesRegex(ValueError, 'updater URL'):
            self.publish()
        self.feed['version'] = '999.0.0'
        with self.assertRaisesRegex(ValueError, 'qualified release'):
            self.publish()


if __name__ == '__main__':
    unittest.main()
