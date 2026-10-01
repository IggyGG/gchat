import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_rollback_image as rollback


class RollbackImageTests(unittest.TestCase):
    def test_previous_image_is_retained_and_missing_registry_layers_are_restored(self):
        with tempfile.TemporaryDirectory() as temporary:
            raw = b'{"qualified":"previous-running-image"}'
            image = '127.0.0.1:30444/old-repository@sha256:' + hashlib.sha256(raw).hexdigest()
            target = {'rollback_image_root': temporary, 'rollback_registry': 'registry.ghost-com:5000'}
            with patch.object(rollback.subprocess, 'run') as copy, \
                 patch.object(rollback.subprocess, 'check_output', return_value=raw):
                root = rollback.retain(image, target)
                self.assertIn('docker://registry.ghost-com:5000/old-repository@sha256:', copy.call_args.args[0][-2])
                self.assertIn('--src-tls-verify=false', copy.call_args.args[0])
                (root / 'image').mkdir(); (root / 'image/manifest.json').write_bytes(raw)
                copy.reset_mock(); rollback.retain(image, target); copy.assert_not_called()
                rollback.repair(image, target)
                self.assertIn('--dest-tls-verify=false', copy.call_args.args[0])
                self.assertIn('--preserve-digests', copy.call_args.args[0])
                self.assertEqual(copy.call_args.args[0][-2], 'dir:' + str(root / 'image'))

    def test_original_oci_receipts_keep_their_transport_and_exact_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            raw = b'{"mediaType":"application/vnd.oci.image.manifest.v1+json"}'
            digest = 'sha256:' + hashlib.sha256(raw).hexdigest(); image = 'registry/old@' + digest
            root = Path(temporary) / digest.split(':')[1]; root.mkdir()
            (root / 'retained.json').write_text(json.dumps({'schema': 1, 'image': image, 'manifest_sha256': digest}))
            with patch.object(rollback.subprocess, 'check_output', return_value=raw), patch.object(rollback.subprocess, 'run') as copy:
                rollback.repair(image, {'rollback_image_root': temporary})
                self.assertEqual(copy.call_args.args[0][-2], 'oci:' + str(root / 'oci') + ':rollback')

    def test_mutable_tags_missing_retention_and_changed_bytes_cannot_rollback(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = {'rollback_image_root': temporary, 'rollback_registry': 'registry:5000'}
            with self.assertRaisesRegex(ValueError, 'digest-pinned'):
                rollback.retain('registry:5000/old:latest', target)
            image = 'registry/old@sha256:' + 'a' * 64
            with self.assertRaisesRegex(ValueError, 'not retained'): rollback.repair(image, target)
            with patch.object(rollback.subprocess, 'run'), \
                 patch.object(rollback.subprocess, 'check_output', return_value=b'wrong manifest'):
                with self.assertRaisesRegex(ValueError, 'running digest'): rollback.retain(image, target)


if __name__ == '__main__': unittest.main()
