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

    def test_france_remains_required(self):
        self.declaration['availableOnFrenchStore'] = False
        with self.assertRaises(ValueError): self.invoke()
        self.gh.assert_not_called()

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
