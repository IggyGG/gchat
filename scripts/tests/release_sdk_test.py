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

class ExistingSdkRunTests(unittest.TestCase):
    def test_reuses_only_exact_main_default_matrix_and_never_push_for_optional_push(self):
        from release_sdk import matching_run
        commit='a'*40; request='b'*64; prefix='GComs SDK Mobile '
        run={'head_sha':commit,'head_branch':'main','event':'push','display_title':prefix+commit}
        self.assertTrue(matching_run(run,'mobile-base',commit,request,prefix))
        self.assertFalse(matching_run(run,'mobile-push',commit,request,prefix))
        self.assertFalse(matching_run(run,'mobile-base','c'*40,request,prefix))
        run['head_branch']='another-branch'
        self.assertFalse(matching_run(run,'mobile-base',commit,request,prefix))
        run.update(event='workflow_dispatch',display_title=prefix+request)
        self.assertTrue(matching_run(run,'mobile-push',commit,request,prefix))
        run['display_title']=prefix+'another-request'
        self.assertFalse(matching_run(run,'mobile-push',commit,request,prefix))
