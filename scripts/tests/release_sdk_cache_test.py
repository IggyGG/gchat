import hashlib,json
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import release_sdk as sdk
from release_automation_test import candidate

class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.cache=self.root/'sdk-cache';self.cache.mkdir()
        (self.root/'mirrors/gcoms.git').mkdir(parents=True)
        self.original='a'*40;self.manifest=candidate();self.manifest['sources']['gcoms']['commit']='b'*40
        self.providers={};self.markers={}
        for i,(kind,(workflow,_,_)) in enumerate(sdk.JOBS.items(),1):
            directory=self.cache/self.original/kind;directory.mkdir(parents=True)
            run={'id':i,'status':'completed','conclusion':'success','head_sha':self.original,
                 'path':'.github/workflows/'+workflow,'head_repository':{'full_name':sdk.REPO}}
            marker=directory/'run.json';marker.write_text(json.dumps(run));self.markers[kind]=marker
            artifacts=[]
            for name in sdk.expected_names(kind,self.original):
                p=directory/(name+'.zip');p.write_bytes(name.encode())
                artifacts.append({'name':name,'size_in_bytes':p.stat().st_size,
                                  'digest':'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest(),'expired':False})
            self.providers['actions/runs/'+str(i)]=run
            self.providers[f'actions/runs/{i}/artifacts?per_page=100']={'artifacts':artifacts}
    def reuse(self,inputs=None,kind=None):
        with patch.object(sdk,'qualification_inputs',side_effect=inputs or (lambda *_:'c'*64)), \
             patch.object(sdk,'api',side_effect=lambda path:self.providers[path]) as api:
            result=sdk.reuse_qualification(self.manifest,self.cache,kind)
        return result,api
    def test_complete_source_equivalent_matrix_preserves_original_archive_labels(self):
        result,api=self.reuse();self.assertEqual(len(result),16);self.assertEqual(api.call_count,6)
        binding=json.loads(result[-1].read_text());self.assertEqual(binding['original_qualification_source'],self.original)
        self.assertEqual(binding['requested_source'],'b'*40)
        self.assertTrue(binding['original_source_labels_preserved'])
        self.assertEqual(len(binding['archives']),12)
        self.assertTrue(all(self.original in p.name for p in result if p.suffix=='.zip'))
    def test_changed_qualification_input_never_reuses_or_dispatches(self):
        result,api=self.reuse(lambda _,commit:commit)
        self.assertIsNone(result);api.assert_not_called()
    def test_cancelled_provider_cannot_be_promoted_by_a_successful_cache_marker(self):
        self.providers['actions/runs/1']['conclusion']='cancelled'
        result,_=self.reuse();self.assertIsNone(result)
        self.assertFalse((self.cache/('b'*40)/'qualification-reuse.json').exists())
    def test_missing_variant_never_produces_a_partial_qualification_receipt(self):
        self.markers['mobile-push'].unlink()
        result,_=self.reuse();self.assertIsNone(result)
    def test_completed_desktop_matrix_can_be_reused_while_mobile_still_waits(self):
        self.markers['mobile-push'].unlink()
        result,api=self.reuse(kind='rust')
        self.assertEqual(len(result),6);self.assertEqual(api.call_count,2)
        self.assertEqual(json.loads(result[-1].read_text())['provider_runs'][0]['kind'],'rust')
    def test_changed_retained_bytes_are_rejected(self):
        archive=next((self.cache/self.original/'rust').glob('*.zip'));archive.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'archive changed'):self.reuse()
    def test_input_key_ignores_only_reviewed_status_and_retains_toolchain_policy_and_tests(self):
        def key(names):
            raw=b'\0'.join(('100644 blob '+sha+'\t'+name).encode() for name,sha in names)+b'\0'
            with patch.object(sdk.subprocess,'check_output',return_value=raw):return sdk.qualification_inputs(self.root,'a'*40)
        fixed=[('crates/runtime/src/lib.rs','a'*40),('rust-toolchain.toml','a'*40),
               ('scripts/sdk_size_policy.py','a'*40),('.github/workflows/rust-integrations.yml','a'*40),
               ('scripts/release_evidence.py','a'*40),('crates/runtime/src/modern_files/tests.rs','a'*40)]
        baseline=key([*fixed,('README.md','a'*40)])
        self.assertEqual(baseline,key([*fixed,('README.md','b'*40)]))
        for name,_ in fixed:
            with self.subTest(name=name):
                changed=[(n,'b'*40 if n==name else sha) for n,sha in fixed]
                self.assertNotEqual(baseline,key([*changed,('README.md','a'*40)]))
        self.assertNotEqual(baseline,key([*fixed,('unknown-build-input','a'*40)]))
