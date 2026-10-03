"""Store upload remains exact, approved and at most once after uncertain dispatch."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_store_worker as worker
from release_ios_recovery import RULE, INPUTS
from release_pair import canonical
from release_ios_recovery_test import manifest
import release_ios_recovery as recovery


class IosUploadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name); self.manifest = manifest()
        self.config = {'encryption_declaration': 'declaration', 'app_id': 'app'}
        self.declaration = {'appEncryptionDeclarationState': 'APPROVED', 'availableOnFrenchStore': True}
        self.builds = []
        self.api = Mock()
        self.api.request.side_effect = lambda method, path, **kw: (
            {'data': {'attributes': self.declaration}} if 'appEncryptionDeclarations' in path
            else {'data': self.builds})
        self.proof = {'retained_ios_followup': True,
                      'evidence': [{'path': 'native.zip', 'sha256': RULE['sha256']}]}
        self.receipt = patch.object(worker, 'read_receipt', return_value=(self.proof, 'hash')).start()
        self.addCleanup(patch.stopall)
        self.runs = []
        self.gh = patch.object(worker, 'gh').start()
        self.gh.side_effect = lambda path, **kw: ({'workflow_runs': self.runs}
                                                 if 'runs?' in path else {})
        self.request = hashlib.sha256(canonical([RULE['release_id'], 'ios', 'upload'])).hexdigest()

    def invoke(self):
        return worker.ios_build(self.api, self.config, self.manifest, self.work/'build', self.work)

    def upload_run(self):
        return {'id': 123, 'head_sha': RULE['controller'], 'path': '.github/workflows/ios-verify.yml',
                'head_repository': {'full_name': 'IggyGG/gchat'}, 'event': 'workflow_dispatch',
                'display_title': 'iOS retained verification '+self.request, 'status': 'completed',
                'conclusion': 'success', 'html_url': 'https://github.com/IggyGG/gchat/actions/runs/123'}

    def test_pending_encryption_never_dispatches_or_creates_marker(self):
        self.declaration['appEncryptionDeclarationState'] = 'IN_REVIEW'
        build, reason = self.invoke()
        self.assertIsNone(build); self.assertIn('approval', reason)
        self.gh.assert_not_called(); self.receipt.assert_not_called()
        self.assertFalse((self.work/'upload-dispatch.json').exists())
        observation=json.loads((self.work/'encryption-observation.json').read_text())
        self.assertEqual(observation['state'],'IN_REVIEW')
        self.assertTrue(observation['includes_france'])

    def test_france_remains_required(self):
        self.declaration['availableOnFrenchStore'] = False
        with self.assertRaises(ValueError): self.invoke()
        self.gh.assert_not_called()

    def test_serialized_store_prerequisite_uses_only_get_and_never_uploads_even_after_approval(self):
        from release_publish import job
        from release_automation_test import candidate
        self.manifest=candidate()
        self.proof['relay_compatible']=True
        state=self.work/'state';state.mkdir()
        source=self.work/'manifest.json';source.write_bytes(canonical(self.manifest))
        config=self.work/'stores.json';config.write_bytes(canonical({'ios':self.config}))
        work=job(state,self.manifest,'ios','prerequisite');work.mkdir(parents=True)
        for stage in ('verify','compatibility'):
            gate=job(state,self.manifest,'ios',stage);gate.mkdir(parents=True)
            (gate/'receipt.json').write_bytes(canonical(self.proof))
        environment={'GCHAT_RELEASE_MANIFEST':str(source),'GCHAT_RELEASE_RECEIPT':str(work/'receipt.json'),
            'GCHAT_RELEASE_TARGET':'ios','GCHAT_RELEASE_STAGE':'prerequisite'}
        for status in ('IN_REVIEW','APPROVED'):
            with self.subTest(status=status):
                self.declaration['appEncryptionDeclarationState']=status;self.api.reset_mock()
                with patch.dict(worker.os.environ,environment), \
                     patch.object(sys,'argv',['worker','--state',str(state),'--config',str(config)]), \
                     patch.object(worker,'apple',return_value=self.api), \
                     patch.object(worker,'ios_build') as upload, \
                     patch.object(worker,'submit_apple') as submit, \
                     self.assertRaises(SystemExit) as stopped:
                    worker.main()
                self.assertEqual(stopped.exception.code,75)
                upload.assert_not_called();submit.assert_not_called();self.gh.assert_not_called()
                self.api.request.assert_called_once_with('GET','/v1/appEncryptionDeclarations/declaration')
                self.assertEqual(json.loads((work/'encryption-observation.json').read_text())['state'],status)
                self.assertFalse(job(state,self.manifest,'ios','submit').exists())
                self.assertFalse((work/'receipt.json').exists())

    def test_exact_recovered_upload_dispatched_only_once(self):
        self.invoke(); self.invoke()
        posts = [c for c in self.gh.call_args_list if c.kwargs.get('method') == 'POST']
        self.assertEqual(len(posts), 1)
        body = posts[0].kwargs['body']; inputs = body['inputs']
        self.assertEqual(body['ref'], 'release/gchat-'+RULE['controller'][:16])
        self.assertEqual(inputs['original_run_id'], str(INPUTS['run_id']))
        self.assertEqual(inputs['artifact_sha256'], INPUTS['artifact_sha256'])
        self.assertEqual(json.loads(inputs['simulator_input']), INPUTS['simulator'])
        self.assertEqual(inputs['gchat_commit'], INPUTS['gchat_commit'])
        self.assertEqual(inputs['gcoms_commit'], INPUTS['gcoms_commit'])
        self.assertIs(inputs['upload_testflight'], True)

    def test_registered_retained_upload_uses_reviewed_sources_and_original_ipa_once(self):
        from release_ios_recovery_test import RegisteredIosTests
        case=RegisteredIosTests(); case.setUp()
        self.manifest=case.manifest
        config=case.config
        reviewed={**INPUTS,'run_id':config['original_run'],'artifact_id':config['original_artifact'],
                  'artifact_sha256':config['original_sha256'],'build_number':self.manifest['versions']['ios'],
                  **{p+'_commit':self.manifest['sources'][p]['commit'] for p in ('gchat','gcoms')},
                  'simulator':{'mode':'retained_original','run_id':config['lifecycle']['run'],
                               'controller_commit':config['lifecycle']['controller'],
                               'request_id':config['lifecycle']['request']}}
        rule={'release_id':self.manifest['release_id'],'registration':config,'original_run':config['original_run'],
              'ipa':config['ipa'],'controller':config['verification']['controller'],
              'request':config['verification']['request'],'inputs':reviewed,'sha256':'f'*64}
        root=self.work/'build'; root.mkdir()
        path=root/'ios-recovery.json'; path.write_bytes(canonical(rule))
        self.proof['evidence']=[{'path':'native.zip','sha256':rule['sha256']},
                                {'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}]
        self.invoke(); self.invoke()
        posts=[call for call in self.gh.call_args_list if call.kwargs.get('method')=='POST']
        self.assertEqual(len(posts),1)
        self.assertEqual(posts[0].kwargs['body']['ref'],config['verification']['ref'])
        values=posts[0].kwargs['body']['inputs']
        self.assertEqual(values['gchat_commit'],reviewed['gchat_commit'])
        self.assertEqual(values['artifact_sha256'],config['original_sha256'])
        self.assertIs(values['upload_testflight'],True)
        path.write_text('{}')
        with self.assertRaisesRegex(ValueError,'not source-bound'): self.invoke()
        self.assertEqual(len([call for call in self.gh.call_args_list if call.kwargs.get('method')=='POST']),1)

    def test_unknown_dispatch_is_not_retried(self):
        (self.work/'upload-dispatch.json').write_text(json.dumps({'at': time.time()-1801, 'request': self.request}))
        with self.assertRaisesRegex(ValueError, 'outcome unknown'): self.invoke()
        self.assertFalse(any(c.kwargs.get('method')=='POST' for c in self.gh.call_args_list))

    def test_wrong_archive_never_dispatches_or_records_attempt(self):
        self.proof['evidence'][0]['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'archive differs'): self.invoke()
        self.assertFalse((self.work/'upload-dispatch.json').exists())
        self.assertFalse(any(c.kwargs.get('method')=='POST' for c in self.gh.call_args_list))

    def test_foreign_failed_or_duplicate_worker_cannot_bind_apple_build(self):
        for key, value in [('head_sha', '0'*40), ('path', 'other.yml'), ('event', 'pull_request'),
                           ('head_repository', {'full_name': 'other/gchat'}), ('conclusion', 'failure')]:
            self.runs = [{**self.upload_run(), key: value}]
            with self.subTest(key=key), self.assertRaises(ValueError): self.invoke()
        self.runs = [self.upload_run(), self.upload_run()]
        with self.assertRaisesRegex(ValueError, 'duplicate'): self.invoke()

    def test_processed_build_binds_successful_exact_worker(self):
        self.runs = [self.upload_run()]
        self.builds = [{'id': 'apple-build', 'attributes': {'processingState': 'VALID'}}]
        self.assertEqual(self.invoke(), ('apple-build', None))
        proof = json.loads((self.work/'upload-worker.json').read_text())
        self.assertEqual(proof['head_sha'], RULE['controller'])
