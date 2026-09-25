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
