import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('copy_registry', Path(__file__).parents[1] / 'copy-release-registry.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class CopyRegistryTest(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        root = Path(self.scratch.name)
        self.source, self.destination = root / 'old', root / 'new'
        self.blob = self.source / 'docker/registry/v2/blobs/sha256/aa/data'
        self.blob.parent.mkdir(parents=True)
        self.blob.write_bytes(b'original registry bytes')
        self.blob.chmod(0o640)

    def test_copy_preserves_original_and_modes_and_repeats_safely(self):
        original = worker.inventory(self.source)
        receipt = worker.copy(self.source, self.destination, True)
        self.assertTrue(receipt['passed'])
        self.assertEqual(worker.inventory(self.source), original)
        self.assertEqual(worker.inventory(self.destination), original)
        self.assertEqual(worker.copy(self.source, self.destination, True), receipt)

    def test_live_writer_and_overlapping_volumes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'stop the registry writer'):
            worker.copy(self.source, self.destination)
        with self.assertRaisesRegex(ValueError, 'overlap'):
            worker.copy(self.source, self.source / 'new', True)

    def test_links_and_unexpected_destination_files_are_rejected(self):
        (self.source / 'linked').symlink_to(self.blob)
        with self.assertRaisesRegex(ValueError, 'link or nonregular'):
            worker.copy(self.source, self.destination, True)
        (self.source / 'linked').unlink()
        self.destination.mkdir()
        (self.destination / 'unrelated').write_text('retain me')
        with self.assertRaisesRegex(ValueError, 'destination bytes'):
            worker.copy(self.source, self.destination, True)
        self.assertEqual((self.destination / 'unrelated').read_text(), 'retain me')

    def test_source_mutation_prevents_a_success_receipt(self):
        copy = worker.shutil.copy2
        def changed(old, new):
            copy(old, new)
            old.write_bytes(b'changed by another writer')
        with patch.object(worker.shutil, 'copy2', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                worker.copy(self.source, self.destination, True)

    def test_symlinked_parent_is_rejected(self):
        alias = self.source.parent / 'alias'
        alias.symlink_to(self.source.parent, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'path contains a link'):
            worker.copy(self.source, alias / 'other', True)
