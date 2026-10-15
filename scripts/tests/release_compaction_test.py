import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import contextlib
import io

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_compaction import compact_build, compact_rollback_images, compact_public_sdk, checked_metadata
from release_pair import canonical
import release_compaction as compactor


@unittest.skipUnless(os.name == 'posix', 'the cluster archive producer requires POSIX locks, descriptors and allocated-block accounting')
class ColdNativeProducerTests(unittest.TestCase):
    def setUp(self):
        from release_automation_test import candidate
        from release_ledger import Ledger
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.ledger = Ledger(self.root / 'ledger.sqlite'); self.addCleanup(self.ledger.close)
        manifests = [candidate(n) for n in range(1, 43)]
        for manifest in manifests:
            manifest['policy']['deployment_required'] = True
            manifest['release_id'] = hashlib.sha256(canonical({k: v for k, v in manifest.items() if k != 'release_id'})).hexdigest()
        with patch('release_ledger.time.time', return_value=1):
            for manifest in manifests: self.ledger.add(manifest)
        self.manifest = manifests[0]; self.platform = 'linux-x86_64'
        self.request = self.ledger.effect(self.manifest['release_id'], self.platform, 'build')['id']
        self.work = self.root / 'jobs' / self.request; self.work.mkdir(parents=True)
        self.data = b'original native ZIP bytes' * (16 * 1024 ** 2 // 25 + 1)
        (self.work / 'native.zip').write_bytes(self.data)
        self.sha = hashlib.sha256(self.data).hexdigest()
        compactor.atomic_json(self.work / 'receipt.json', {'schema': 1, 'release_id': self.manifest['release_id'],
            'sources': self.manifest['sources'], 'platform': self.platform, 'stage': 'build',
            'passed': True, 'source_unchanged': True, 'evidence': [{'path': 'native.zip', 'sha256': self.sha}]})
        self.receipt_sha = hashlib.sha256((self.work / 'receipt.json').read_bytes()).hexdigest()
        self.ledger.complete_effect(self.request, 'original-native-run', self.receipt_sha)
        for manifest in manifests[:2]:
            for state in ('building', 'verifying', 'verified', 'publishing', 'available'):
                self.ledger.transition(manifest['release_id'], self.platform, state, evidence='a' * 64)

    def tool(self, tool, action, state, receipt, *, source=None, destination=None, **kwargs):
        if action == 'archive':
            path = state / source
            compactor.atomic_json(receipt, {'format': 'triform.closed-file-archive/v1', 'owner': 'gchat-native-builds',
                'source': source, 'source_sha256': self.sha, 'source_bytes': len(self.data),
                'source_identity': list(compactor.identity(path.stat())), 'plaintext_verified': True,
                'manifest_key': 'cluster-retention/v1/gchat-native-builds/original/manifest.json'})
            return {'archived': source}
        if action == 'restore':
            destination.write_bytes(self.data)
            return {'source_sha256': self.sha}
        self.assertEqual(action, 'retire')
        path = self.work / 'native.zip'; size = path.stat().st_blocks * 512; path.unlink()
        return {'retired': 'jobs/' + self.request + '/native.zip', 'allocated_bytes_released': size}

    def test_only_old_available_builds_are_selected_and_pending_work_is_protected(self):
        plan = compactor.cold_native_plan(self.root)
        self.assertEqual([p['request_id'] for p in plan], [self.request])
        with patch('release_compaction.time.time', return_value=2):
            self.assertEqual(compactor.cold_native_plan(self.root), [])
        compactor.atomic_json(self.root / 'control/incoming/operator.json', {'release_id': self.manifest['release_id']})
        self.assertEqual(compactor.cold_native_plan(self.root), [])

    def test_inactive_completed_build_can_archive_but_active_or_unknown_submissions_cannot(self):
        # Seed alternative historical platform states around the same immutable
        # passing build; these are fixture rows, never production transitions.
        for state, resume, eligible in [('verified', None, True), ('blocked', 'verified', True),
                ('superseded', None, True), ('building', None, False), ('verifying', None, False),
                ('publishing', None, False), ('submitting', None, False), ('in_review', None, False),
                ('blocked', 'submitting', False), ('blocked', 'processing', False)]:
            with self.subTest(state=state, resume=resume):
                self.ledger.db.execute('UPDATE platforms SET state=?,resume_state=? WHERE candidate=? AND platform=?',
                                       (state, resume, self.manifest['release_id'], self.platform))
                self.assertEqual(bool(compactor.cold_native_plan(self.root)), eligible)
        self.ledger.db.execute("UPDATE platforms SET state='blocked',resume_state='verified' WHERE candidate=? AND platform=?",
                               (self.manifest['release_id'], self.platform))
        compactor.atomic_json(self.root / 'recovery' / self.manifest['release_id'] / (self.platform + '.json'), {'transient': True})
        self.assertEqual(compactor.cold_native_plan(self.root), [])

    def test_verified_native_restore_precedes_retirement_and_keeps_all_other_evidence(self):
        original = (self.work / 'receipt.json').read_bytes()
        (self.work / 'original.log').write_bytes(b'original failed attempts')
        before = [tuple(r) for r in self.ledger.db.execute('SELECT * FROM platforms')]
        with patch.object(compactor, 'archive_tool', side_effect=self.tool) as calls:
            result = compactor.archive_cold_native(self.root, 'approved-archive.py', retire=True, target_bytes=1)
        self.assertEqual([c.args[1] for c in calls.call_args_list], ['archive', 'restore', 'retire'])
        self.assertEqual(len(result['objects']), 1); self.assertGreater(result['reclaimed_bytes'], 0)
        self.assertFalse((self.work / 'native.zip').exists())
        self.assertEqual((self.work / 'receipt.json').read_bytes(), original)
        self.assertTrue((self.work / 'original.log').exists())
        self.assertTrue((self.work / 'native.zip.archive.json').exists())
        self.assertEqual(before, [tuple(r) for r in self.ledger.db.execute('SELECT * FROM platforms')])

    def test_failed_restore_preserves_the_original_and_never_calls_retirement(self):
        def broken(*args, **kwargs):
            if args[1] == 'restore': kwargs['destination'].write_bytes(b'wrong'); return {}
            return self.tool(*args, **kwargs)
        with patch.object(compactor, 'archive_tool', side_effect=broken) as calls, \
             self.assertRaisesRegex(ValueError, 'original qualification'):
            compactor.archive_cold_native(self.root, 'approved-archive.py', retire=True, target_bytes=1)
        self.assertNotIn('retire', [c.args[1] for c in calls.call_args_list])
        self.assertEqual((self.work / 'native.zip').read_bytes(), self.data)

    def test_new_operator_request_after_upload_defers_retirement(self):
        def intervening(*args, **kwargs):
            result = self.tool(*args, **kwargs)
            if args[1] == 'restore':
                compactor.atomic_json(self.root / 'control/incoming/operator.json', {'release_id': self.manifest['release_id']})
            return result
        with patch.object(compactor, 'archive_tool', side_effect=intervening) as calls:
            result = compactor.archive_cold_native(self.root, 'approved-archive.py', retire=True, target_bytes=1)
        self.assertEqual(result['reclaimed_bytes'], 0)
        self.assertNotIn('retire', [c.args[1] for c in calls.call_args_list])
        self.assertTrue((self.work / 'native.zip').is_file())


@unittest.skipUnless(os.name == 'posix', 'the release filesystem requires POSIX links')
class CompactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'jobs/build'
        self.root.mkdir(parents=True)
        self.native = self.root / 'native'
        self.native.mkdir()
        self.content = b'original-signed-artifact' * 100
        self.archive = self.root / 'native.zip'
        with zipfile.ZipFile(self.archive, 'w') as archive:
            for name in ('package.deb', 'installer/package.deb', 'other/package.deb', 'different.deb'):
                content = self.content if name != 'different.deb' else b'a' * len(self.content)
                archive.writestr(name, content)
                path = self.native / name
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(content)
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.proof = {'schema': 1, 'release_id': 'a' * 64,
                      'sources': {'gchat': {'commit': 'b' * 40}, 'gcoms': {'commit': 'c' * 40}},
                      'platform': 'linux-x86_64', 'stage': 'build', 'passed': True,
                      'source_unchanged': True, 'evidence': [{'path': 'native.zip', 'sha256': digest}]}
        (self.root / 'receipt.json').write_text(json.dumps(self.proof))
        (self.root / 'extracted.json').write_text(json.dumps({'sha256': digest}))

    def test_exact_bytes_paths_permissions_and_original_proof_survive_idempotent_compaction(self):
        original = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        report = compact_build(self.root, minimum_bytes=1)
        self.assertEqual(len(report['changes']), 2)
        self.assertTrue(report['original_archive_retained'])
        self.assertTrue(report['all_paths_retained'])
        for path, content in original.items():
            self.assertEqual(path.read_bytes(), content)
        paths = [self.native / name for name in ('package.deb', 'installer/package.deb', 'other/package.deb')]
        self.assertEqual(len({p.stat().st_ino for p in paths}), 1)
        self.assertNotEqual(paths[0].stat().st_ino, (self.native / 'different.deb').stat().st_ino)
        self.assertEqual(compact_build(self.root, minimum_bytes=1)['changes'], [])

    def test_archive_or_extraction_tampering_fails_before_any_replacement(self):
        victim = self.native / 'other/package.deb'
        originals = [p.stat().st_ino for p in self.native.rglob('*') if p.is_file()]
        victim.write_bytes(b'x' * len(self.content))
        with self.assertRaisesRegex(ValueError, 'bytes differ'):
            compact_build(self.root, minimum_bytes=1)
        self.assertEqual([p.stat().st_ino for p in self.native.rglob('*') if p.is_file()], originals)
        victim.write_bytes(self.content)
        self.archive.write_bytes(self.archive.read_bytes() + b'changed')
        with self.assertRaises(ValueError):
            compact_build(self.root, minimum_bytes=1)
        self.assertEqual([p.stat().st_ino for p in self.native.rglob('*') if p.is_file()], originals)

    def test_different_permissions_are_retained_on_a_separate_inode(self):
        private = self.native / 'installer/package.deb'
        private.chmod(0o600)
        before = private.stat()
        report = compact_build(self.root, minimum_bytes=1)
        self.assertEqual(len(report['changes']), 1)
        self.assertEqual(private.stat().st_ino, before.st_ino)
        self.assertEqual(private.stat().st_mode, before.st_mode)
        self.assertEqual(private.read_bytes(), self.content)
        self.assertNotEqual(private.stat().st_ino, (self.native / 'package.deb').stat().st_ino)

    def test_verified_stage_copies_keep_both_receipts_and_reject_changed_provenance(self):
        verified = self.root.parent / 'verify'
        payload = verified / 'verified/package.deb'
        payload.parent.mkdir(parents=True)
        payload.write_bytes(self.content)
        proof = dict(self.proof, stage='verify', evidence=[{
            'path': 'verified/package.deb', 'sha256': hashlib.sha256(self.content).hexdigest()}])
        receipt = verified / 'receipt.json'
        receipt.write_text(json.dumps(proof))
        original = receipt.read_bytes()
        report = compact_build(self.root, minimum_bytes=1, verified_work=verified)
        self.assertEqual(len(report['changes']), 3)
        self.assertEqual(payload.stat().st_ino, (self.native / 'package.deb').stat().st_ino)
        self.assertEqual(payload.read_bytes(), self.content)
        self.assertEqual(receipt.read_bytes(), original)
        proof['sources'] = {'gchat': {'commit': 'd' * 40}}
        receipt.write_text(json.dumps(proof))
        with self.assertRaisesRegex(ValueError, 'exact candidate'):
            compact_build(self.root, minimum_bytes=1, verified_work=verified)

    def test_unfinished_or_symlinked_artifacts_and_replacement_races_are_rejected(self):
        self.proof['passed'] = False
        (self.root / 'receipt.json').write_text(json.dumps(self.proof))
        with self.assertRaisesRegex(ValueError, 'completed native build'):
            compact_build(self.root, minimum_bytes=1)
        self.proof['passed'] = True
        (self.root / 'receipt.json').write_text(json.dumps(self.proof))
        victim = self.native / 'installer/package.deb'
        victim.unlink()
        victim.symlink_to(self.native / 'package.deb')
        with self.assertRaises(ValueError):
            compact_build(self.root, minimum_bytes=1)
        victim.unlink()
        victim.write_bytes(self.content)
        archive_before = self.archive.read_bytes()
        receipt_before = (self.root / 'receipt.json').read_bytes()
        real_link = os.link
        def race(source, target, **kwargs):
            real_link(source, target, **kwargs)
            # An in-place same-size write can share the original timestamp on
            # fast tmpfs. Replace the path with a distinct, already-created
            # inode so this fixture deterministically injects its stated race.
            replacement = victim.with_name('racing-replacement')
            replacement.write_bytes(b'x' * len(self.content))
            os.replace(replacement, victim)
        with patch('release_compaction.os.link', side_effect=race):
            with self.assertRaisesRegex(ValueError, 'changed before replacement'):
                compact_build(self.root, minimum_bytes=1)
        self.assertEqual(victim.read_bytes(), b'x' * len(self.content))
        for name in ('package.deb', 'other/package.deb'):
            self.assertEqual((self.native / name).read_bytes(), self.content)
        self.assertEqual(self.archive.read_bytes(), archive_before)
        self.assertEqual((self.root / 'receipt.json').read_bytes(), receipt_before)
        self.assertFalse(list(self.native.rglob('.compact-*')))


@unittest.skipUnless(os.name == 'posix', 'the release filesystem requires POSIX links')
class RollbackImageCompactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name)
        self.content = b'original compressed image layer' * 100
        self.paths = []
        for number in (1, 2, 3):
            config = ('original image configuration ' + str(number)).encode()
            config_sha = hashlib.sha256(config).hexdigest()
            layer_sha = hashlib.sha256(self.content).hexdigest()
            manifest = {'schemaVersion': 2, 'config': {'digest': 'sha256:' + config_sha, 'size': len(config)},
                        'layers': [{'digest': 'sha256:' + layer_sha, 'size': len(self.content)}]}
            raw = json.dumps(manifest).encode();sha = hashlib.sha256(raw).hexdigest()
            directory = self.state / 'rollback-images' / sha
            image = directory / ('oci' if number == 3 else 'image')
            blobs = image / 'blobs/sha256' if number == 3 else image;blobs.mkdir(parents=True)
            (blobs / config_sha).write_bytes(config);layer = blobs / layer_sha;layer.write_bytes(self.content)
            self.paths.append(layer)
            if number == 3:
                (blobs / sha).write_bytes(raw)
                (image / 'index.json').write_text(json.dumps({'manifests': [{'digest': 'sha256:' + sha}]}))
            else:
                (image / 'manifest.json').write_bytes(raw)
            proof = {'schema': 1, 'image': '127.0.0.1:30444/ghost/gchat-release@sha256:' + sha,
                     'manifest_sha256': 'sha256:' + sha}
            if number != 3:proof['transport'] = 'dir'
            (directory / 'retained.json').write_text(json.dumps(proof))

    def compact(self):
        return compact_rollback_images(self.state, minimum_bytes=1)

    def test_directory_and_legacy_oci_images_keep_every_byte_and_path(self):
        files = {p: (p.read_bytes(), p.stat().st_mode) for p in (self.state / 'rollback-images').rglob('*') if p.is_file()}
        report = self.compact()
        self.assertEqual(len(report['images']), 3);self.assertEqual(len(report['changes']), 2)
        self.assertTrue(report['all_image_manifests_and_blobs_verified'])
        for path, (content, mode) in files.items():
            self.assertEqual(path.read_bytes(), content);self.assertEqual(path.stat().st_mode, mode)
        self.assertEqual(len({p.stat().st_ino for p in self.paths}), 1)
        self.assertEqual(self.compact()['changes'], [])

    def test_changed_large_layer_and_small_configuration_prevent_every_link(self):
        for victim in (self.paths[-1], next(p for p in self.paths[0].parent.iterdir()
                                          if p != self.paths[0] and p.name != 'manifest.json')):
            before = victim.read_bytes();inodes = [p.stat().st_ino for p in self.paths]
            victim.write_bytes(b'x' * len(before))
            with self.assertRaisesRegex(ValueError, 'digest or size differs'):self.compact()
            self.assertEqual([p.stat().st_ino for p in self.paths], inodes)
            victim.write_bytes(before)

    def test_changed_manifest_or_oci_index_prevents_every_link(self):
        for victim in (self.paths[0].parent / 'manifest.json', self.paths[-1].parents[2] / 'index.json'):
            before = victim.read_bytes();inodes = [p.stat().st_ino for p in self.paths]
            if victim.name == 'index.json':victim.write_text('{"manifests":[]}')
            else:victim.write_bytes(before + b' ')
            with self.assertRaises(ValueError):self.compact()
            self.assertEqual([p.stat().st_ino for p in self.paths], inodes)
            victim.write_bytes(before)

    def test_permission_and_unrelated_workload_boundaries_are_preserved(self):
        self.paths[0].chmod(0o600)
        directory = self.paths[-1].parents[3]
        receipt = directory / 'retained.json';proof = json.loads(receipt.read_text())
        proof['image'] = proof['image'].replace('/ghost/gchat-release@', '/other/workload@')
        receipt.write_text(json.dumps(proof))
        inodes = [p.stat().st_ino for p in self.paths]
        self.assertEqual(self.compact()['changes'], [])
        self.assertEqual([p.stat().st_ino for p in self.paths], inodes)

    def test_symlink_layer_and_nonregular_metadata_fail_without_following(self):
        victim = self.paths[1];victim.unlink();victim.symlink_to(self.paths[0])
        with self.assertRaisesRegex(ValueError, 'unsafe.*layer'):self.compact()
        victim.unlink();victim.write_bytes(self.content)
        fifo = self.state / 'metadata.pipe';os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError, 'regular file'):checked_metadata(fifo, 65536)

    def test_preexisting_aliases_can_merge_without_false_race_or_byte_changes(self):
        self.paths[2].unlink();os.link(self.paths[1], self.paths[2])
        report = self.compact()
        self.assertTrue(report['all_paths_retained'])
        self.assertEqual(len({p.stat().st_ino for p in self.paths}), 1)
        self.assertTrue(all(p.read_bytes() == self.content for p in self.paths))

    def test_layer_replacement_race_refuses_success_and_removes_temporary_links(self):
        original = os.link
        def race(source, destination, **kwargs):
            original(source, destination, **kwargs)
            path = destination.parent / source.name
            path.write_bytes(b'x' * len(self.content))
        with patch('release_compaction.os.link', side_effect=race), self.assertRaisesRegex(ValueError, 'changed before replacement'):
            self.compact()
        self.assertFalse(list(self.state.rglob('.compact-*')))
        for path in self.paths:
            path.write_bytes(self.content)
        receipt = next((self.state / 'rollback-images').glob('*/retained.json'))
        def provenance_race(source, destination, **kwargs):
            original(source, destination, **kwargs)
            receipt.write_bytes(receipt.read_bytes() + b' ')
        with patch('release_compaction.os.link', side_effect=provenance_race), self.assertRaisesRegex(ValueError, 'provenance changed'):
            self.compact()
        self.assertFalse(list(self.state.rglob('.compact-*')))


@unittest.skipUnless(os.name == 'posix', 'the release filesystem requires POSIX links')
class PublicSdkCompactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name)
        self.content = b'original-qualified-sdk-archive' * 100
        self.sha = hashlib.sha256(self.content).hexdigest()
        self.public, self.originals, self.reports = [], [], []
        for number in range(1, 4):
            manifest = {'schema': 1, 'sources': {
                'gchat': {'commit': 'b' * 40, 'tree': 'e' * 40},
                'gcoms': {'commit': 'c' * 40, 'tree': 'f' * 40}},
                'versions': {'sdk': '0.0.' + str(number)}, 'policy': {}}
            manifest['release_id'] = hashlib.sha256(canonical(manifest)).hexdigest()
            release = manifest['release_id']
            build = self.state / 'jobs' / hashlib.sha256(canonical([release, 'sdk', 'build'])).hexdigest()
            source = build / 'archives/native.zip'
            source.parent.mkdir(parents=True)
            source.write_bytes(self.content); source.chmod(0o600)
            self.originals.append(source)
            receipt = {'schema': 1, 'release_id': release, 'sources': manifest['sources'],
                       'platform': 'sdk', 'passed': True, 'source_unchanged': True,
                       'stage': 'build', 'evidence': [{'path': 'archives/native.zip', 'sha256': self.sha}]}
            (build / 'receipt.json').write_bytes(canonical(receipt))
            publication = self.state / 'jobs' / hashlib.sha256(canonical([release, 'sdk', 'publish'])).hexdigest()
            publication.mkdir()
            (publication / 'candidate.json').write_bytes(canonical(manifest))
            target = self.state / 'public/updates/sdk' / release / 'native.zip'
            target.parent.mkdir(parents=True)
            target.write_bytes(self.content); target.chmod(0o644)
            self.public.append(target)
            report = {'schema': 1, 'release_id': release, 'sources': manifest['sources'],
                      'version': manifest['versions']['sdk'], 'archives': [{
                          'path': release + '/native.zip', 'sha256': self.sha, 'size': len(self.content)}]}
            report_path = publication / 'public-sdk.json'
            report_path.write_bytes(canonical(report)); self.reports.append(report_path)
            receipt = dict(receipt, stage='publish', evidence=[{
                'path': 'public-sdk.json', 'sha256': hashlib.sha256(report_path.read_bytes()).hexdigest()}])
            (publication / 'receipt.json').write_bytes(canonical(receipt))

    def compact(self):
        return compact_public_sdk(self.state, minimum_bytes=1)

    def test_all_urls_originals_permissions_and_receipts_survive_idempotent_sharing(self):
        originals = {p: (p.read_bytes(), p.stat().st_mode) for p in self.state.rglob('*') if p.is_file()}
        private_inodes = [p.stat().st_ino for p in self.originals]
        report = self.compact()
        self.assertEqual(len(report['changes']), 2)
        self.assertTrue(report['original_provider_archives_retained'])
        self.assertFalse(report['private_provider_archives_shared'])
        self.assertEqual(len({p.stat().st_ino for p in self.public}), 1)
        self.assertEqual([p.stat().st_ino for p in self.originals], private_inodes)
        for path, (content, mode) in originals.items():
            self.assertEqual((path.read_bytes(), path.stat().st_mode), (content, mode))
        self.assertEqual(self.compact()['changes'], [])

    def test_changed_public_or_original_archive_blocks_before_any_replacement(self):
        for victim in (self.public[-1], self.originals[-1]):
            with self.subTest(victim=victim):
                before = [p.stat().st_ino for p in self.public]
                victim.write_bytes(b'x' * len(self.content))
                with self.assertRaisesRegex(ValueError, 'bytes differ'):
                    self.compact()
                self.assertEqual([p.stat().st_ino for p in self.public], before)
                victim.write_bytes(self.content)

    def test_changed_provenance_is_rejected_before_any_replacement(self):
        before = [p.stat().st_ino for p in self.public]
        self.reports[-1].write_bytes(self.reports[-1].read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'index differs'):
            self.compact()
        self.assertEqual([p.stat().st_ino for p in self.public], before)

    def test_index_cannot_redirect_archives_outside_the_public_release(self):
        path = self.reports[-1]
        report = json.loads(path.read_text())
        report['archives'][0]['path'] = report['release_id'] + '/../outside.zip'
        path.write_bytes(canonical(report))
        receipt = path.parent / 'receipt.json'
        proof = json.loads(receipt.read_text())
        proof['evidence'][0]['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        receipt.write_bytes(canonical(proof))
        with self.assertRaisesRegex(ValueError, 'unsafe SDK artifact path'):
            self.compact()

    def test_private_original_inodes_cannot_be_used_as_public_canonical_files(self):
        self.public[-1].unlink()
        os.link(self.originals[-1], self.public[-1])
        self.originals[-1].chmod(0o644)
        with self.assertRaisesRegex(ValueError, 'shares a private provider inode'):
            self.compact()

    def test_bounded_maintenance_visits_recent_publications_and_ignores_unfinished_work(self):
        for number, path in enumerate(self.reports, 1):
            os.utime(path.parent / 'receipt.json', ns=(number * 10**9, number * 10**9))
        report = compact_public_sdk(self.state, maximum_publications=2, minimum_bytes=1)
        expected = [json.loads(p.read_text())['release_id'] for p in reversed(self.reports[-2:])]
        self.assertEqual(report['publications'], expected)
        self.assertEqual(len(report['changes']), 1)
        receipt = self.reports[-1].parent / 'receipt.json'
        proof = json.loads(receipt.read_text()); proof['passed'] = False
        receipt.write_bytes(canonical(proof))
        report = compact_public_sdk(self.state, minimum_bytes=1)
        self.assertNotIn(json.loads(self.reports[-1].read_text())['release_id'], report['publications'])

    def test_different_public_permissions_stay_separate(self):
        self.public[-1].chmod(0o640)
        before = self.public[-1].stat().st_ino
        self.assertEqual(len(self.compact()['changes']), 1)
        self.assertEqual(self.public[-1].stat().st_ino, before)
        self.assertEqual(self.public[-1].stat().st_mode & 0o777, 0o640)

    def test_symlink_and_fifo_are_rejected_without_reading_or_changing_their_target(self):
        victim = self.public[-1]
        victim.unlink()
        victim.symlink_to(self.originals[-1])
        with self.assertRaisesRegex(ValueError, 'escapes retained'):
            self.compact()
        victim.unlink(); os.mkfifo(victim)
        with self.assertRaisesRegex(ValueError, 'size or type'):
            self.compact()

    def test_replacement_and_original_archive_races_fail_closed(self):
        original_link = os.link
        def race(source, destination, **kwargs):
            original_link(source, destination, **kwargs)
            (destination.parent / source.name).write_bytes(b'x' * len(self.content))
        with patch('release_compaction.os.link', side_effect=race), self.assertRaisesRegex(ValueError, 'changed before replacement'):
            self.compact()
        self.assertFalse(list(self.state.rglob('.compact-*')))
        for path in self.public:
            path.write_bytes(self.content)
        def authority_race(source, destination, **kwargs):
            original_link(source, destination, **kwargs)
            self.originals[-1].write_bytes(b'x' * len(self.content))
        with patch('release_compaction.os.link', side_effect=authority_race), self.assertRaisesRegex(ValueError, 'original SDK archive changed'):
            self.compact()
        self.assertFalse(list(self.state.rglob('.compact-*')))


@unittest.skipUnless(os.name == 'posix', 'canary compaction uses POSIX links')
class CanaryCompactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / 'jobs').mkdir()
        self.sources = {'gchat': {'commit': 'a' * 40, 'tree': 'b' * 40},
                        'gcoms': {'commit': 'c' * 40, 'tree': 'd' * 40}}

    def workspace(self, index, package=b'qualified package' * 100):
        work = self.root / 'tmp' / f'nc-{index:08d}'
        (work / 'journey').mkdir(parents=True)
        (work / 'package/usr/bin').mkdir(parents=True)
        (work / 'package.deb').write_bytes(package)
        (work / 'package.deb').chmod(0o600)
        executables = []
        for name in ('gchat', 'gchat-desktop'):
            value = (name.encode() + b' qualified executable') * 100
            path = work / 'package/usr/bin' / name
            path.write_bytes(value); path.chmod(0o755)
            executables.append({'name': name, 'size': len(value), 'sha256': hashlib.sha256(value).hexdigest()})
        native = {'sources': self.sources, 'exit_code': 0, 'source_unchanged': True}
        (work / 'native-ci.json').write_bytes(canonical(native))
        native_sha = hashlib.sha256((work / 'native-ci.json').read_bytes()).hexdigest()
        build = {'target': 'linux-x86_64', 'sources': {k: v['commit'] for k, v in self.sources.items()},
                 'native_ci': {'report_sha256': native_sha}, 'executables': executables,
                 'files': [{'format': 'deb', 'signing_verified': True,
                            'sha256': hashlib.sha256(package).hexdigest()}]}
        (work / 'build.json').write_bytes(canonical(build))
        cli = next(v['sha256'] for v in executables if v['name'] == 'gchat')
        report = {k: True for k in ('passed', 'children_stopped', 'temporary_profile_removed',
                                   'inputs_unchanged', 'binary_unchanged')}
        report.update(binary_sha256=cli, inputs={'sources': self.sources,
            'binary': {'path': str(work / 'package/usr/bin/gchat'), 'sha256': cli},
            'build_manifest': {'path': str(work / 'build.json'),
                               'sha256': hashlib.sha256((work / 'build.json').read_bytes()).hexdigest()},
            'native_receipt': {'path': str(work / 'native-ci.json'), 'sha256': native_sha}})
        (work / 'journey/report.json').write_bytes(canonical(report))
        os.utime(work / 'journey/report.json', (1000 + index, 1000 + index))
        return work

    def compact(self, **kwargs):
        return compactor.compact_canaries(self.root, minimum_bytes=1, **kwargs)

    def test_scheduled_maintenance_compacts_closed_canary_packages(self):
        first = self.workspace(1, b'p' * (16 * 1024**2))
        second = self.workspace(2, b'p' * (16 * 1024**2))
        with patch.object(sys, 'argv', ['release_compaction.py', '--state', str(self.root)]), \
                contextlib.redirect_stdout(io.StringIO()):
            compactor.main()
        self.assertEqual((first / 'package.deb').stat().st_ino, (second / 'package.deb').stat().st_ino,
                         'scheduled maintenance left completed canary package copies duplicated')

    def test_all_paths_bytes_modes_and_evidence_survive_idempotent_sharing(self):
        first, second = self.workspace(1), self.workspace(2)
        originals = {p: (p.read_bytes(), p.stat().st_mode) for work in (first, second)
                     for p in work.rglob('*') if p.is_file()}
        result = self.compact()
        self.assertEqual(len(result['changes']), 3)
        self.assertTrue(result['all_paths_retained'])
        self.assertTrue(result['all_qualified_inputs_verified'])
        for path, (contents, mode) in originals.items():
            self.assertEqual(path.read_bytes(), contents)
            self.assertEqual(path.stat().st_mode, mode)
        for path in ('package.deb', 'package/usr/bin/gchat', 'package/usr/bin/gchat-desktop'):
            self.assertEqual((first / path).stat().st_ino, (second / path).stat().st_ino)
        self.assertEqual(self.compact()['changes'], [])

    def test_active_failed_and_unclean_canaries_are_not_shared(self):
        first = self.workspace(1)
        for index, field in ((2, 'passed'), (3, 'children_stopped'), (4, 'temporary_profile_removed')):
            work = self.workspace(index)
            path = work / 'journey/report.json'; value = json.loads(path.read_text()); value[field] = False
            path.write_bytes(canonical(value))
        active = self.workspace(5)
        owners = self.root / 'canaries'; owners.mkdir()
        (owners / ('a' * 64 + '.json')).write_bytes(canonical({'work': str(active), 'revoked': False, 'passed': True}))
        (self.root / 'tmp/nc-00000006').mkdir()
        self.assertEqual(self.compact()['changes'], [])
        self.assertNotEqual((first / 'package.deb').stat().st_ino, (active / 'package.deb').stat().st_ino)

    def test_changed_artifact_or_source_binding_prevents_every_link(self):
        first, second = self.workspace(1), self.workspace(2)
        original = (second / 'package.deb').read_bytes()
        (second / 'package.deb').write_bytes(b'x' * len(original))
        with self.assertRaisesRegex(ValueError, 'qualified input'):
            self.compact()
        self.assertNotEqual((first / 'package/usr/bin/gchat').stat().st_ino,
                            (second / 'package/usr/bin/gchat').stat().st_ino)
        (second / 'package.deb').write_bytes(original)
        path = second / 'journey/report.json'; report = json.loads(path.read_text())
        report['inputs']['sources']['gcoms']['commit'] = 'e' * 40
        path.write_bytes(canonical(report))
        with self.assertRaisesRegex(ValueError, 'binding changed'):
            self.compact()
        self.assertNotEqual((first / 'package.deb').stat().st_ino, (second / 'package.deb').stat().st_ino)

    def test_permission_boundary_and_recent_bounded_selection(self):
        old, first, second = self.workspace(1), self.workspace(2), self.workspace(3)
        (first / 'package.deb').chmod(0o640)
        result = self.compact(maximum_canaries=2)
        self.assertEqual(len(result['canaries']), 2)
        self.assertNotEqual((first / 'package.deb').stat().st_ino, (second / 'package.deb').stat().st_ino)
        self.assertEqual((first / 'package/usr/bin/gchat').stat().st_ino,
                         (second / 'package/usr/bin/gchat').stat().st_ino)
        self.assertNotEqual((old / 'package/usr/bin/gchat').stat().st_ino,
                            (second / 'package/usr/bin/gchat').stat().st_ino)

    def test_symlink_and_control_replacement_are_refused(self):
        first, second = self.workspace(1), self.workspace(2)
        victim = second / 'package/usr/bin/gchat'
        original = victim.read_bytes(); victim.unlink(); victim.symlink_to(first / 'package/usr/bin/gchat')
        with self.assertRaisesRegex(ValueError, 'unsafe canary artifact'):
            self.compact()
        victim.unlink(); victim.write_bytes(original); victim.chmod(0o755)
        real_digest = compactor.file_digest
        changed = False
        def race(path):
            nonlocal changed
            result = real_digest(path)
            if not changed and path.name == 'package.deb':
                changed = True
                (second / 'journey/report.json').write_text('{}')
            return result
        with patch('release_compaction.file_digest', side_effect=race):
            with self.assertRaisesRegex(ValueError, 'control evidence changed'):
                self.compact()
        self.assertNotEqual((first / 'package.deb').stat().st_ino, (second / 'package.deb').stat().st_ino)


if __name__ == '__main__':
    unittest.main()
