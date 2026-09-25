import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_stores import google_state, apple_state

class StoreStateTests(unittest.TestCase):
    def google(self, state, code=1020):
        return google_state([{'track': 'production', 'activeArtifacts': [{'versionCode': code}],
                              'releaseLifecycleState': state}], 1020)
    def test_only_actual_exact_version_publication_is_available(self):
        self.assertEqual(self.google('RELEASE_LIFECYCLE_STATE_PUBLISHED')['state'], 'available')
        self.assertNotEqual(self.google('RELEASE_LIFECYCLE_STATE_PUBLISHED', 1007)['state'], 'available')
        for state in ['completed', 'RELEASE_LIFECYCLE_STATE_APPROVED_NOT_PUBLISHED',
                      'RELEASE_LIFECYCLE_STATE_NOT_SENT_FOR_REVIEW', 'RELEASE_LIFECYCLE_STATE_IN_REVIEW']:
            self.assertNotEqual(self.google(state)['state'], 'available')
    def test_apple_published_version_requires_the_exact_uploaded_build(self):
        version = {'attributes': {'appStoreState': 'READY_FOR_DISTRIBUTION'},
                   'relationships': {'build': {'data': {'id': 'correct'}}}}
        self.assertEqual(apple_state(version, 'correct')['state'], 'available')
        self.assertEqual(apple_state(version, 'wrong')['state'], 'blocked')
        version['attributes']['appStoreState'] = 'PENDING_DEVELOPER_RELEASE'
        self.assertEqual(apple_state(version, 'correct')['state'], 'blocked')
        version['attributes']['appStoreState'] = 'WAITING_FOR_REVIEW'
        self.assertEqual(apple_state(version, 'correct')['state'], 'in_review')

class SubmissionTests(unittest.TestCase):
    def test_unknown_google_edit_creation_never_repeats_post(self):
        import tempfile, hashlib
        from release_stores import submit_google,ProviderError
        class API:
            calls=[]
            def request(self,method,path,**kwargs):
                self.calls.append((method,path));raise ProviderError('lost reply')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);aab=root/'app.aab';aab.write_bytes(b'qualified')
            candidate={'release_id':'a'*64,'version_code':'1020','aab_sha256':hashlib.sha256(b'qualified').hexdigest()}
            api=API()
            for _ in range(2):
                with self.assertRaises(ProviderError):submit_google(api,{},candidate,aab,root/'journal')
            self.assertEqual(api.calls,[('POST','/edits')])
    def test_bundle_mismatch_fails_before_any_provider_call(self):
        import tempfile
        from release_stores import submit_google
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);aab=root/'app.aab';aab.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'changed'):
                submit_google(None,{}, {'aab_sha256':'f'*64},aab,root/'journal')
    def test_apple_build_must_belong_to_our_app_and_reserved_version(self):
        import tempfile
        from release_stores import submit_apple
        class API:
            def request(self,*args,**kwargs):return {'data':{'attributes':{'version':'1.0.1','processingState':'VALID'},'relationships':{'app':{'data':{'id':'other'}}}}}
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'different application'):
                submit_apple(API(),{'app_id':'ours'},{'build_id':'build','build_number':'1.0.1'},Path(d)/'journal')
