import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_compaction import compact_build


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
        real_link = os.link
        def race(source, target, **kwargs):
            real_link(source, target, **kwargs)
            victim.write_bytes(b'x' * len(self.content))
        with patch('release_compaction.os.link', side_effect=race):
            with self.assertRaisesRegex(ValueError, 'changed before replacement'):
                compact_build(self.root, minimum_bytes=1)
        self.assertFalse(list(self.native.rglob('.compact-*')))


if __name__ == '__main__':
    unittest.main()
