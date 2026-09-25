from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from release_sdk import expected_names
class SdkMatrixTests(unittest.TestCase):
    def test_all_native_roles_and_push_variants_have_distinct_exact_source_names(self):
        commit='a'*40
        desktop=expected_names('rust',commit);base=expected_names('mobile-base',commit);push=expected_names('mobile-push',commit)
        self.assertEqual(len(desktop|base|push),12)
        self.assertTrue(all(n.endswith(commit) for n in desktop|base|push))
        self.assertFalse(base&push)

    def test_publication_does_not_replace_versions_or_advertise_partial_copy(self):
        import tempfile,hashlib,json
        from unittest.mock import patch
        from release_sdk import publish_archives
        from release_automation_test import candidate
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);payload=root/'sdk.zip';payload.write_bytes(b'qualified sdk')
            sha=hashlib.sha256(payload.read_bytes()).hexdigest();manifest=candidate();public=root/'public'
            with patch('release_sdk.shutil.copyfileobj',side_effect=OSError('interrupted copy')):
                with self.assertRaises(OSError):publish_archives(manifest,[(payload,sha)],public)
            self.assertFalse((public/'latest.json').exists())
            self.assertFalse((public/manifest['release_id']/payload.name).exists())
            first=publish_archives(manifest,[(payload,sha)],public)
            self.assertEqual(first,publish_archives(manifest,[(payload,sha)],public))
            manifest['release_id']='b'*64
            with self.assertRaisesRegex(ValueError,'another source pair'):
                publish_archives(manifest,[(payload,sha)],public)
            self.assertEqual(json.loads((public/'latest.json').read_text()),first)
