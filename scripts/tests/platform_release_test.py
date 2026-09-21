import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import platform_release as platform
import website


class PlatformReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.pin = 'A' * 40
        self.signer = {'name': 'Gh0st', 'certificate_sha256': 'b' * 64}
        self.publication = {'version': '0.1.4', 'publication_status': 'approved_by_owner',
                            'publisher_identities': {'linux': {'certificate_fingerprint': self.pin}, 'macos': self.signer}}
        self.candidate = {'schema': 1, 'kind': 'platform-release', 'version': '0.1.4',
                          'tag': 'v0.1.4-macos-aarch64.1', 'target': 'macos-aarch64', 'channel': 'production',
                          'release_policy': 'production-minutes-v1', 'privacy_qualified': False,
                          'unqualified_scopes': ['statistical privacy', 'live push'], 'signer': self.signer.copy(),
                          'sources': {name: {'commit': char * 40, 'tree': char * 40, 'archive': self.file(name + '.tar', name.encode())}
                                      for name, char in [('gchat', 'c'), ('gcoms', 'd')]},
                          'release_key': self.file('key.asc', b'-----BEGIN PGP PUBLIC KEY BLOCK-----\nfixture') | {'fingerprint': self.pin,
                              'signature': self.file('key.asc.asc', b'key signature')},
                          'artifacts': {'GChat.dmg': self.file('GChat.dmg', b'installer') | {
                              'format': 'dmg', 'target': 'macos-aarch64', 'size': 9,
                              'signature': self.file('GChat.dmg.asc', b'installer signature')}}, 'checks': {}}
        self.reports = {}
        for role in ('build', 'smoke', 'signing'):
            report = {'schema': 1, 'scope': 'platform.' + role, 'passed': True, 'source_unchanged': True,
                      'sources': platform.bindings(self.candidate), 'target': 'macos-aarch64',
                      'artifacts': {'GChat.dmg': self.candidate['artifacts']['GChat.dmg']['sha256']},
                      'qualified_scopes': [role + ' actual scope'], 'evidence': [self.file(role + '.log', b'original report/log')],
                      'signer': self.signer.copy(), 'cleanup_complete': True}
            self.reports[role] = report; self.record(role)

    def file(self, name, contents):
        (self.base / name).write_bytes(contents)
        return {'path': name, 'sha256': hashlib.sha256(contents).hexdigest()}

    def record(self, role):
        self.candidate['checks'][role] = self.file(role + '.json', json.dumps(self.reports[role]).encode())

    def validate(self):
        with patch.object(platform, 'verify') as verifier:
            result = platform.validate(self.candidate, self.base, self.publication)
            self.assertEqual(verifier.call_count, 2)
            return result

    def test_exact_scoped_bundle_and_public_manifest(self):
        self.validate()
        manifest = platform.public_manifest(self.candidate, self.base)
        self.assertEqual(manifest['sources']['gchat']['commit'], 'c' * 40)
        self.assertNotIn(str(self.base), json.dumps(manifest))
        self.assertNotIn('path', manifest['checks']['smoke'])
        self.assertEqual(manifest['artifacts']['GChat.dmg']['sha256'], self.candidate['artifacts']['GChat.dmg']['sha256'])

    def test_wrong_source_artifact_signer_or_incomplete_smoke_rejected(self):
        mutations = [('source', lambda r: r['sources']['gchat'].update(commit='e' * 40)),
                     ('artifact', lambda r: r['artifacts'].update({'GChat.dmg': 'f' * 64})),
                     ('target', lambda r: r.update(target='windows-x86_64')),
                     ('failed', lambda r: r.update(passed=False)),
                     ('changed', lambda r: r.update(source_unchanged=False)),
                     ('cleanup', lambda r: r.update(cleanup_complete=False))]
        original = copy.deepcopy(self.reports['smoke'])
        for name, mutate in mutations:
            self.reports['smoke'] = copy.deepcopy(original); mutate(self.reports['smoke']); self.record('smoke')
            with self.subTest(name=name), self.assertRaises(ValueError): self.validate()
        self.reports['smoke'] = original; self.record('smoke')
        self.reports['signing']['signer']['certificate_sha256'] = 'f' * 64; self.record('signing')
        with self.assertRaisesRegex(ValueError, 'wrong publisher'): self.validate()

    def test_changed_raw_evidence_archive_and_installer_rejected(self):
        for path in ('build.log', 'gcoms.tar', 'GChat.dmg'):
            original = (self.base / path).read_bytes(); (self.base / path).write_bytes(b'changed')
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'hash mismatch'): self.validate()
            (self.base / path).write_bytes(original)

    def test_frozen_policy_and_detached_signature_required(self):
        self.candidate['signer']['certificate_sha256'] = 'e' * 64
        with self.assertRaisesRegex(ValueError, 'frozen publisher'): self.validate()
        self.candidate['signer'] = self.signer.copy()
        with patch.object(platform, 'verify', side_effect=ValueError('bad signature')):
            with self.assertRaisesRegex(ValueError, 'bad signature'):
                platform.validate(self.candidate, self.base, self.publication)

    def test_private_key_file_cannot_be_published(self):
        replacement = self.file('key.asc', b'-----BEGIN PGP PRIVATE KEY BLOCK-----\nfixture')
        self.candidate['release_key'].update(replacement)
        with self.assertRaisesRegex(ValueError, 'public release key'): self.validate()

    def test_published_release_is_closed_and_existing_bytes_immutable(self):
        release = {'draft': False, 'assets': [{'name': 'app', 'sha': 'a'}]}
        self.assertEqual(platform.immutable_assets(release, {'app': 'a'}, lambda x: x['sha']), set())
        for expected in ({'app': 'b'}, {'app': 'a', 'new': 'b'}, {}):
            with self.subTest(expected=expected), self.assertRaises(ValueError):
                platform.immutable_assets(release, expected, lambda x: x['sha'])
        release['draft'] = True
        self.assertEqual(platform.immutable_assets(release, {'app': 'a', 'new': 'b'}, lambda x: x['sha']), {'new'})


class PlatformWebsiteTests(unittest.TestCase):
    def manifest(self):
        pin = 'A' * 40; releases = {}; artifacts = []
        for tag, target, formats in [('v0.1.3', 'linux-x86_64', ['deb', 'appimage']),
                                     ('v0.1.4-macos-aarch64.1', 'macos-aarch64', ['dmg'])]:
            prefix = 'https://github.com/IggyGG/gchat/releases/download/' + tag + '/'
            legacy = tag == 'v0.1.3'; name = 'release-manifest.json' if legacy else 'platform-release.json'
            releases[tag] = {'version': '0.1.3' if legacy else '0.1.4', 'manifest_format': 'legacy-v1' if legacy else 'platform-v1',
                             'sources': {'gchat': 'c' * 40, 'gcoms': 'd' * 40},
                             'release_key': {'url': prefix + 'gchat-release-key.asc', 'sha256': 'e' * 64, 'fingerprint': pin},
                             'manifest': {'url': prefix + name, 'signature_url': prefix + name + '.asc', 'sha256': 'f' * 64, 'signature_sha256': 'a' * 64}}
            for fmt in formats:
                artifacts.append({'release': tag, 'target': target, 'format': fmt, 'url': prefix + 'GChat.' + fmt,
                                  'signature_url': prefix + 'GChat.' + fmt + '.asc', 'sha256': 'b' * 64,
                                  'signature_sha256': 'c' * 64, 'signing_verified': True})
        return {'schema': 2, 'version': None, 'channel': 'production', 'publisher_fingerprint': pin, 'releases': releases, 'artifacts': artifacts}

    def test_independent_versions_preserve_linux_links(self):
        data = website.validate(self.manifest()); page = website.downloads(data)
        self.assertIn('0.1.3', page); self.assertIn('0.1.4', page)
        self.assertIn('/v0.1.3/GChat.deb', page)
        self.assertNotIn('Production 0.1.4', page)
        self.assertIn('for Linux, macOS.', website.client_status(data))

    def test_x86_64_platform_tags_preserve_asset_origin_checks(self):
        for target, fmt in [('android-x86_64', 'apk'), ('windows-x86_64', 'nsis'), ('macos-x86_64', 'dmg')]:
            with self.subTest(target=target):
                data = self.manifest()
                old_tag = 'v0.1.4-macos-aarch64.1'
                tag = 'v0.1.4-' + target + '.1'
                release = data['releases'].pop(old_tag)
                for record in (release['release_key'], release['manifest']):
                    for key in ('url', 'signature_url'):
                        if key in record: record[key] = record[key].replace(old_tag, tag)
                data['releases'][tag] = release
                artifact = data['artifacts'][-1]
                artifact.update(release=tag, target=target, format=fmt)
                for key in ('url', 'signature_url'):
                    artifact[key] = artifact[key].replace(old_tag, tag)
                website.validate(data)
                self.assertIn('/' + tag + '/', website.downloads(data))
                artifact['url'] = artifact['url'].replace(tag, tag + '/..')
                with self.assertRaises(ValueError): website.validate(data)

    def test_untrusted_malformed_cross_release_unsigned_and_wrong_key_fail(self):
        mutations = [lambda d: d['artifacts'][0].update(url='https://evil.invalid/file.deb'),
                     lambda d: d['artifacts'][0].update(url=d['artifacts'][0]['url'] + '?download=1'),
                     lambda d: d['artifacts'][0].update(url=d['artifacts'][0]['url'].replace('v0.1.3', 'v0.1.4')),
                     lambda d: d['artifacts'][0].update(signing_verified=False),
                     lambda d: d['artifacts'].pop(0),
                     lambda d: d['releases']['v0.1.3']['release_key'].update(fingerprint='B' * 40),
                     lambda d: d['releases']['v0.1.3']['manifest'].update(signature_url='https://evil.invalid/sig')]
        for i, mutate in enumerate(mutations):
            data = self.manifest(); mutate(data)
            with self.subTest(i=i), self.assertRaises(ValueError): website.validate(data)

    def test_signed_manifest_must_name_exact_download_source_format_and_hash(self):
        data = self.manifest(); tag = 'v0.1.4-macos-aarch64.1'
        release = data['releases'][tag]; artifacts = [data['artifacts'][-1]]
        signed = {'kind': 'platform-release', 'schema': 1, 'tag': tag, 'version': '0.1.4', 'sources': release['sources'],
                  'artifacts': {'GChat.dmg': {'sha256': 'b' * 64, 'format': 'dmg', 'target': 'macos-aarch64'}}}
        website.validate_signed_manifest(release, signed, artifacts)
        for mutation in ('source', 'artifact', 'target'):
            changed = copy.deepcopy(signed)
            if mutation == 'source': changed['sources']['gchat'] = 'e' * 40
            else: changed['artifacts']['GChat.dmg']['sha256' if mutation == 'artifact' else 'target'] = 'wrong'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                website.validate_signed_manifest(release, changed, artifacts)


if __name__ == '__main__': unittest.main()
