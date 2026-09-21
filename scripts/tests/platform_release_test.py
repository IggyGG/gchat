import copy
import hashlib
import json
from pathlib import Path
import sys
import subprocess
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



class DeveloperIdPlatformReleaseTests(unittest.TestCase):
    file = PlatformReleaseTests.file
    record = PlatformReleaseTests.record

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo).strip()

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Fixture')
        return {'commit': self.git('rev-parse', 'HEAD').decode(), 'tree': self.git('rev-parse', 'HEAD^{tree}').decode()}

    def json_file(self, name, value):
        return self.file(name, json.dumps(value, sort_keys=True).encode())

    def setUp(self):
        PlatformReleaseTests.setUp(self)
        self.repo = self.base / 'repository'; self.repo.mkdir()
        self.git('init', '-q')
        (self.repo / 'release').mkdir()
        self.publication['project'] = 'gchat'
        (self.repo / 'release/publication.json').write_text(json.dumps(self.publication))
        original = self.commit()
        self.candidate['sources']['gchat'] = original | {'archive': self.file('gchat.tar', self.git('archive', '--format=tar', 'HEAD'))}
        self.controller_policy = copy.deepcopy(self.publication)
        self.publisher = {'name': 'Gh0st', 'certificate_sha256': 'e' * 64, 'team_id': 'FIXTURE123',
                          'distribution': 'developer-id', 'signing_policy': 'publicly-trusted'}
        self.controller_policy['publisher_identities']['macos'] = self.publisher
        (self.repo / 'release/publication.json').write_text(json.dumps(self.controller_policy))
        controller = self.commit()
        self.candidate['tag'] = 'v0.1.4-macos-aarch64.2'
        self.candidate['signer'] = {key: self.publisher[key] for key in ('name', 'certificate_sha256')}
        policy = {'kind': 'macos-developer-id-controller', 'replaces': 'v0.1.4-macos-aarch64.1',
                  'controller': controller | {'archive': self.file('controller.tar', self.git('archive', '--format=tar', 'HEAD'))},
                  'publication': self.file('controller-publication.json', (self.repo / 'release/publication.json').read_bytes())}
        self.candidate['signer_policy'] = policy
        sources = platform.bindings(self.candidate)
        for role in self.reports:
            self.reports[role].update(sources=sources, signer=self.candidate['signer'])
            self.record(role)
        inputs = {'schema': 1, 'kind': 'frozen_source_pair', 'sources': sources,
                  'source_archive_sha256': {key: value['archive']['sha256'] for key, value in self.candidate['sources'].items()},
                  'target': 'aarch64-apple-darwin', 'rust_graphs': {'workspace': ['fixture']},
                  'derived_lock_sha256': {'Cargo.lock': '1' * 64}, 'npm_archives': {'fixture': '2' * 64},
                  'npm_bindings': {'fixture': '3' * 64}, 'rust_sources_verified': True, 'npm_sources_verified': True}
        native_ref = self.json_file('native-ci.json', {'exit_code': 0, 'source_unchanged': True, 'sources': sources, 'inputs': inputs})
        native = platform.verify_native_ci_inputs(self.base / native_ref['path'], inputs)
        old_dmg = self.file('old.dmg', b'original signed installer')
        self.old_build = {'target': self.candidate['target'], 'native_ci': native, 'dependency_inputs': inputs,
                          'publisher': self.signer, 'files': [{'sha256': old_dmg['sha256']}]}
        old_smoke = {'scope': 'macos_dmg_private_copy_install_service_lifecycle', 'target': self.candidate['target'],
                     'passed': True, 'sources': sources, 'inputs': {'dmg': old_dmg}}
        dmg = self.candidate['artifacts']['GChat.dmg']
        self.build = {'target': self.candidate['target'], 'native_ci': native, 'dependency_inputs': inputs, 'publisher': self.publisher,
                      'apple_notarization': True, 'signing_policy': 'publicly-trusted',
                      'files': [{'sha256': dmg['sha256']}]}
        self.smoke = {'scope': 'macos_dmg_private_copy_install_service_lifecycle', 'target': self.candidate['target'],
                      'gui_startup_passed': True, 'passed': True, 'inputs_unchanged': True, 'sources': sources, 'inputs': {'dmg': dmg},
                      'cleanup': dict.fromkeys(('passed', 'detached', 'installation_removed', 'service_children_stopped'), True)}
        self.notary_id = '211415e9-a592-40a8-92ab-78d2eace18b6'
        manifest = {'Contents/MacOS/GChat': {'kind': 'macho', 'sha256': 'a' * 64, 'executable': True}}
        self.proof = {'schema': 1, 'scope': 'retained_macos_developer_id_notarization', 'target': self.candidate['target'],
                      'passed': True, 'recompiled': False, 'resigned': True, 'native_tests_rerun': False,
                      'sources': sources, 'controller': controller, 'controller_archive': policy['controller']['archive'],
                      'publication': policy['publication'], 'publisher': self.publisher,
                      'original': {'build': self.json_file('old-build.json', self.old_build),
                                   'application_smoke': self.json_file('old-smoke.json', old_smoke),
                                   'native_ci': native, 'native_receipt': native_ref, 'dmg': old_dmg},
                      'code_identity': {'method': 'codesign_remove_signature_on_private_copies',
                                        'before': manifest, 'after': copy.deepcopy(manifest), 'unchanged': True},
                      'build': self.json_file('new-build.json', self.build), 'dmg': dmg,
                      'application_smoke': self.json_file('new-smoke.json', self.smoke),
                      'notarization': {'id': self.notary_id, 'status': 'Accepted', 'submission_dmg_sha256': 'f' * 64,
                          'info': self.json_file('notary-info.json', {'id': self.notary_id, 'status': 'Accepted'}),
                          'log': self.json_file('notary-log.json', {'jobId': self.notary_id, 'status': 'Accepted', 'sha256': 'f' * 64})},
                      'stapling': {'dmg_validated': True, 'evidence': [self.file('stapler.log', b'validated')]},
                      'gatekeeper': dict.fromkeys(('quarantine_applied', 'dmg_assessment_passed', 'app_assessment_passed',
                                                  'app_notarization_requirement_passed', 'cleanup_complete', 'assessment_policy_enabled'), True),
                      'cleanup_complete': True}
        self.proof['gatekeeper']['evidence'] = [self.file('gatekeeper.log', b'quarantined Gatekeeper accepted')]
        self.save_proof()

    def save_proof(self):
        self.candidate['signer_policy']['qualification'] = self.json_file('notarization.json', self.proof)

    def validate(self):
        with patch.object(platform, 'verify'):
            return platform.validate(self.candidate, self.base, self.publication, controller_repository=self.repo)

    def test_new_signer_policy_keeps_original_runtime_and_private_evidence_out_of_manifest(self):
        self.validate()
        manifest = platform.public_manifest(self.candidate, self.base)
        self.assertEqual(manifest['sources']['gchat']['commit'], self.candidate['sources']['gchat']['commit'])
        self.assertNotEqual(manifest['signer_policy']['controller']['commit'], manifest['sources']['gchat']['commit'])
        self.assertEqual(manifest['signer_policy']['replaces'], 'v0.1.4-macos-aarch64.1')
        self.assertNotIn(str(self.base), json.dumps(manifest))
        self.assertNotIn('path', json.dumps(manifest['signer_policy']))

    def test_separate_architecture_history_requires_exact_original_archive(self):
        self.git('checkout', '--orphan', 'separate-controller')
        controller = self.commit()
        policy = self.candidate['signer_policy']
        policy['controller'] = controller | {'archive': self.file('separate-controller.tar', self.git('archive', '--format=tar', 'HEAD'))}
        self.proof['controller'] = controller
        self.proof['controller_archive'] = policy['controller']['archive']
        self.save_proof()
        self.validate()
        application = self.candidate['sources']['gchat']
        application['archive'] = self.file('different-app.tar', b'not the qualified application')
        with self.assertRaisesRegex(ValueError, 'original application archive'):
            self.validate()

    def test_arbitrary_policy_archive_or_tree_cannot_replace_committed_controller(self):
        policy = self.candidate['signer_policy']
        mutations = [('publication', self.json_file('arbitrary-policy.json', self.publication)),
                     ('controller', policy['controller'] | {'tree': 'a' * 40}),
                     ('controller', policy['controller'] | {'archive': self.file('fake-controller.tar', b'not the Git archive')})]
        for key, value in mutations:
            with self.subTest(key=key), patch.dict(policy, {key: value}), self.assertRaises(ValueError):
                self.validate()
        with patch.object(platform, 'verify'), self.assertRaisesRegex(ValueError, 'committed GChat'):
            platform.validate(self.candidate, self.base, self.publication)

    def test_recompiled_changed_code_wrong_native_or_missing_gatekeeper_is_rejected(self):
        original = copy.deepcopy(self.proof)
        changes = [lambda p: p.update(recompiled=True),
                   lambda p: p['sources']['gchat'].update(commit='a' * 40),
                   lambda p: p['original']['native_ci'].update(report_sha256='f' * 64),
                   lambda p: p['code_identity']['after']['Contents/MacOS/GChat'].update(sha256='b' * 64),
                   lambda p: p['notarization'].update(status='In Progress'),
                   lambda p: p['notarization'].update(submission_dmg_sha256='0' * 64),
                   lambda p: p['stapling'].update(dmg_validated=False),
                   lambda p: p['gatekeeper'].update(quarantine_applied=False),
                   lambda p: p['gatekeeper'].update(app_assessment_passed=False),
                   lambda p: p['gatekeeper'].update(assessment_policy_enabled=False),
                   lambda p: p['gatekeeper'].update(evidence=[]),
                   lambda p: p.update(cleanup_complete=False)]
        for change in changes:
            self.proof = copy.deepcopy(original); change(self.proof); self.save_proof()
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.validate()

    def test_native_receipt_and_smoke_cleanup_must_be_bound_and_successful(self):
        self.smoke['cleanup']['service_children_stopped'] = False
        self.proof['application_smoke'] = self.json_file('new-smoke.json', self.smoke); self.save_proof()
        with self.assertRaisesRegex(ValueError, 'smoke or cleanup'):
            self.validate()
        self.smoke['cleanup']['service_children_stopped'] = True
        self.proof['application_smoke'] = self.json_file('new-smoke.json', self.smoke)
        native = json.loads((self.base / 'native-ci.json').read_text()); native['exit_code'] = 1
        self.proof['original']['native_receipt'] = self.json_file('native-ci.json', native); self.save_proof()
        with self.assertRaisesRegex(ValueError, 'native CI did not pass'):
            self.validate()

    def test_committed_controller_cannot_change_detached_key_or_claim_self_signed_developer_id(self):
        original = copy.deepcopy(self.controller_policy)
        for change, reason in ((lambda p: p['publisher_identities']['linux'].update(certificate_fingerprint='F' * 40), 'detached release key'),
                               (lambda p: p['publisher_identities']['macos'].update(signing_policy='self-signed'), 'Developer ID'),
                               (lambda p: p['publisher_identities']['macos'].update(distribution='app-store'), 'Developer ID')):
            value = copy.deepcopy(original); change(value)
            (self.repo / 'release/publication.json').write_text(json.dumps(value))
            controller = self.commit()
            policy = self.candidate['signer_policy']
            policy['controller'] = controller | {'archive': self.file('controller.tar', self.git('archive', '--format=tar', 'HEAD'))}
            policy['publication'] = self.file('controller-publication.json', (self.repo / 'release/publication.json').read_bytes())
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                self.validate()

    def test_old_tag_or_non_mac_policy_override_is_rejected(self):
        with patch.dict(self.candidate, {'tag': 'v0.1.4-macos-aarch64.1'}), self.assertRaisesRegex(ValueError, 'later platform tag'):
            self.validate()
        with patch.dict(self.candidate, {'tag': 'v0.1.4-windows-x86_64.2', 'target': 'windows-x86_64'}), \
                self.assertRaisesRegex(ValueError, 'unsupported separate signer'):
            self.validate()


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
