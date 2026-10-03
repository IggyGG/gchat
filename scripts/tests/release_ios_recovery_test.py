"""Retained iOS qualification must bind the existing IPA and original failure."""
import copy
import hashlib
import sys
from pathlib import Path
import unittest
import json
import tempfile
import subprocess
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_ios_recovery import RULE, INPUTS, validate_run, validate_report
import release_ios_recovery as worker


def manifest():
    return {'release_id': RULE['release_id'],
            'sources': {p: {'commit': INPUTS[p + '_commit']} for p in ('gchat', 'gcoms')},
            'versions': {'ios': INPUTS['build_number'], 'linux-x86_64': '0.1.40'},
            'policy': {'ios_certificate_sha256': 'a' * 64}}


class IosRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.manifest = manifest()
        self.run = {'id': RULE['run'], 'head_sha': RULE['controller'],
                    'path': '.github/workflows/ios-verify.yml',
                    'head_repository': {'full_name': 'IggyGG/gchat'},
                    'display_title': 'iOS retained verification ' + RULE['request'],
                    'event': 'workflow_dispatch', 'status': 'completed', 'conclusion': 'success'}
        self.artifact = {'id': RULE['artifact'], 'expired': False,
                         'workflow_run': {'id': RULE['run']},
                         'digest': 'sha256:' + RULE['sha256'], 'size_in_bytes': 316898149}
        self.report = {'scope': 'ios_retained_pair_simulator_and_signed_ipa',
                       'passed': True, 'sources_unchanged': True,
                       'sources': copy.deepcopy(self.manifest['sources']), 'inputs': copy.deepcopy(INPUTS),
                       'application_recompiled': False, 'device_resigned': False,
                       'original_build_passed': False, 'physical_device_qualified': False,
                       'push_qualified': False, 'original_build_verdict_unchanged': True,
                       'simulator_reused_from_original': True,
                       'application': {'ipa': {'sha256': RULE['ipa']}, 'bundle': 'boo.gchat.app',
                           'build_number': INPUTS['build_number'], 'marketing_version': '0.1.40',
                           'profile': {'certificate_sha256': 'a' * 64}}}

    def test_exact_followup_accepts_without_rewriting_original_failure(self):
        before = copy.deepcopy(self.report)
        validate_run(self.manifest, self.run, self.artifact)
        validate_report(self.manifest, self.report)
        self.assertEqual(self.report, before)
        self.assertIs(self.report['original_build_passed'], False)

    def test_other_run_controller_workflow_or_candidate_rejected(self):
        for key, value in [('id', 1), ('head_sha', 'b'*40), ('path', 'other.yml'),
                           ('head_repository', {'full_name': 'other/gchat'}),
                           ('display_title', 'another request'), ('event', 'pull_request'),
                           ('status', 'in_progress'), ('conclusion', 'failure')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_run(self.manifest, {**self.run, key: value}, self.artifact)
        with self.assertRaises(ValueError):
            validate_run({**self.manifest, 'release_id': '0'*64}, self.run, self.artifact)

    def test_other_archive_identity_expiry_or_length_rejected(self):
        for key, value in [('id', 1), ('expired', True), ('workflow_run', {'id': 1}),
                           ('digest', 'sha256:'+'0'*64), ('size_in_bytes', 100)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_run(self.manifest, self.run, {**self.artifact, key: value})

    def test_scope_source_and_verdict_changes_rejected(self):
        for key, value in [('scope', 'another scope'), ('passed', False), ('sources_unchanged', False),
                           ('sources', {}), ('inputs', {}), ('application_recompiled', True),
                           ('device_resigned', True), ('original_build_passed', True),
                           ('physical_device_qualified', True), ('push_qualified', True),
                           ('original_build_verdict_unchanged', False), ('simulator_reused_from_original', False)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_report(self.manifest, {**self.report, key: value})

    def test_substituted_ipa_version_bundle_and_signer_rejected(self):
        for key, value in [('ipa', {'sha256': '0'*64}), ('bundle', 'another.app'),
                           ('build_number', '1.0.60'), ('marketing_version', '0.1.41'),
                           ('profile', {'certificate_sha256': 'b'*64})]:
            report = copy.deepcopy(self.report); report['application'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_report(self.manifest, report)


class RegisteredIosTests(unittest.TestCase):
    def setUp(self):
        from release_macos_recovery import REGISTRY
        self.config = next(v for v in json.loads(REGISTRY.read_text())['recoveries'] if v['kind'] == 'ios-retained')
        self.manifest = {'release_id': self.config['release_id'], 'sources': self.config['sources'],
                         'versions': {'ios': '1.1.13'}}
        self.original = {'id': self.config['original_run'], 'status': 'completed', 'conclusion': 'failure',
                         'head_sha': self.config['sources']['gchat']['commit'], 'path': '.github/workflows/ios-release.yml',
                         'event': 'workflow_dispatch', 'head_repository': {'full_name': 'IggyGG/gchat'}}
        self.lifecycle = {'id': self.config['lifecycle']['run'], 'head_sha': self.config['lifecycle']['controller'],
                          'path': '.github/workflows/ios-lifecycle.yml', 'event': 'workflow_dispatch',
                          'head_repository': {'full_name': 'IggyGG/gchat'}, 'status': 'completed', 'conclusion': 'success',
                          'display_title': 'iOS lifecycle ' + self.config['lifecycle']['request']}
        self.artifact = {'id': 123, 'workflow_run': {'id': self.lifecycle['id']}, 'expired': False,
                         'name': 'ios-lifecycle-' + self.config['lifecycle']['request'],
                         'digest': 'sha256:' + 'a' * 64, 'size_in_bytes': 100}

    def provider(self, endpoint, **kwargs):
        if endpoint == 'actions/runs/' + str(self.lifecycle['id']): return self.lifecycle
        if endpoint == 'actions/runs/' + str(self.lifecycle['id']) + '/artifacts?per_page=100': return {'artifacts': [self.artifact]}
        if endpoint == 'actions/artifacts/123': return self.artifact
        if endpoint.startswith('actions/workflows/ios-verify.yml/runs?'): return {'workflow_runs': []}
        if endpoint.startswith('git/ref/heads/'): return {'object': {'sha': self.config['verification']['controller']}}
        if endpoint.endswith('/dispatches'): return None
        raise AssertionError(endpoint)

    def corrected_verification(self, work):
        with patch('release_jobs.gh',side_effect=self.provider):
            worker.retained_followup(self.manifest,work,self.original,self.config)
        old=json.loads((work/'ios-retained-verification-dispatch.json').read_text())['intent']
        config=copy.deepcopy(self.config)
        config['previous_verification']={**self.config['verification'],'run':999}
        config['verification']={'controller':'7'*40,'ref':'release/qualification-ios-installed-'+'7'*12,
                                'request':hashlib.sha256(__import__('release_pair').canonical(
                                    ['ios-retained-verification-followup',old['request'],'7'*40])).hexdigest()}
        failed={'id':999,'head_sha':old['controller'],'head_branch':old['ref'],
                'display_title':'iOS retained verification '+old['request'],
                'path':'.github/workflows/ios-verify.yml','head_repository':{'full_name':'IggyGG/gchat'},
                'event':'workflow_dispatch','status':'completed','conclusion':'failure'}
        return config,failed

    def test_one_corrected_verification_preserves_failure_and_reconciles_lost_dispatch_reply(self):
        with tempfile.TemporaryDirectory() as temporary:
            work=Path(temporary); config,failed=self.corrected_verification(work)
            original=(work/'ios-retained-verification-dispatch.json').read_bytes()
            def provider(endpoint,**kwargs):
                if endpoint=='actions/runs/999': return failed
                if endpoint=='actions/runs/999/artifacts?per_page=100': return {'artifacts':[]}
                if endpoint.startswith('git/ref/heads/'): return {'object':{'sha':config['verification']['controller']}}
                if endpoint.endswith('/dispatches'): raise subprocess.TimeoutExpired('provider',1)
                return self.provider(endpoint,**kwargs)
            with patch('release_jobs.gh',side_effect=provider) as api:
                self.assertIsNone(worker.retained_followup(self.manifest,work,self.original,config))
                self.assertIsNone(worker.retained_followup(self.manifest,work,self.original,config))
                self.assertEqual(sum(call.kwargs.get('method')=='POST' for call in api.call_args_list),1)
                self.assertEqual((work/'ios-retained-verification-dispatch.json').read_bytes(),original)
                directory=work/'ios-retained-verification-followups'/('7'*40)
                self.assertIs(json.loads((directory/'original-failure.json').read_text())['passed'],False)
                (directory/'original-failed-artifacts.json').write_text('{}')
                with self.assertRaisesRegex(ValueError,'failure evidence changed'):
                    worker.retained_followup(self.manifest,work,self.original,config)
                self.assertEqual(sum(call.kwargs.get('method')=='POST' for call in api.call_args_list),1)

    def test_corrected_verification_refuses_unknown_successful_or_changed_predecessor(self):
        for changed in ({'status':'in_progress'}, {'conclusion':'success'}, {'head_sha':'0'*40}):
            with self.subTest(changed=changed),tempfile.TemporaryDirectory() as temporary:
                work=Path(temporary); config,failed=self.corrected_verification(work); failed.update(changed)
                def provider(endpoint,**kwargs):
                    if endpoint=='actions/runs/999': return failed
                    return self.provider(endpoint,**kwargs)
                with patch('release_jobs.gh',side_effect=provider) as api,self.assertRaisesRegex(ValueError,'predecessor'):
                    worker.retained_followup(self.manifest,work,self.original,config)
                self.assertFalse(any(call.kwargs.get('method')=='POST' for call in api.call_args_list))

    def test_queued_lifecycle_waits_without_dispatching_or_changing_original(self):
        with tempfile.TemporaryDirectory() as root, patch('release_jobs.gh', return_value={**self.lifecycle, 'status': 'queued', 'conclusion': None}) as gh:
            self.assertIsNone(worker.collect(self.manifest, Path(root), self.original))
            self.assertEqual(gh.call_count, 1)
            self.assertEqual(list(Path(root).iterdir()), [])
        self.assertEqual(self.original['conclusion'], 'failure')

    def test_positive_lifecycle_dispatches_same_ipa_once_and_disables_upload(self):
        with tempfile.TemporaryDirectory() as root, patch('release_jobs.gh', side_effect=self.provider) as gh:
            root = Path(root)
            self.assertIsNone(worker.retained_followup(self.manifest, root, self.original, self.config))
            first = [c for c in gh.call_args_list if c.args[0].endswith('/dispatches')]
            self.assertEqual(len(first), 1)
            body = first[0].kwargs['body']['inputs']
            self.assertIs(body['upload_testflight'], False)
            self.assertEqual(body['artifact_sha256'], self.config['original_sha256'])
            self.assertEqual(body['original_run_id'], str(self.config['original_run']))
            self.assertEqual(json.loads(body['simulator_input'])['mode'], 'retained_original')
            self.assertIsNone(worker.retained_followup(self.manifest, root, self.original, self.config))
            self.assertEqual(len([c for c in gh.call_args_list if c.args[0].endswith('/dispatches')]), 1)

    def test_lost_dispatch_reply_keeps_intent_and_never_resubmits(self):
        def lost(endpoint, **kwargs):
            if endpoint.endswith('/dispatches'): raise subprocess.CalledProcessError(1, ['gh'])
            return self.provider(endpoint, **kwargs)
        with tempfile.TemporaryDirectory() as root, patch('release_jobs.gh', side_effect=lost) as gh:
            for _ in range(2):
                self.assertIsNone(worker.retained_followup(self.manifest, Path(root), self.original, self.config))
            self.assertEqual(len([c for c in gh.call_args_list if c.args[0].endswith('/dispatches')]), 1)
            self.assertTrue((Path(root) / 'ios-retained-verification-dispatch.json').is_file())

    def test_failed_lifecycle_or_wrong_helper_cannot_dispatch_verification(self):
        for key, value in (('conclusion', 'failure'), ('head_sha', '0' * 40), ('display_title', 'another request')):
            with tempfile.TemporaryDirectory() as root, patch('release_jobs.gh', return_value={**self.lifecycle, key: value}) as gh:
                with self.assertRaises(ValueError):
                    worker.retained_followup(self.manifest, Path(root), self.original, self.config)
                self.assertEqual(gh.call_count, 1)

    def test_source_and_lifecycle_archive_changes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'source differs'):
            worker.registered({**self.manifest, 'sources': {}})
        for key, value in (('digest', ''), ('expired', True), ('workflow_run', {'id': 1}), ('size_in_bytes', 0)):
            with tempfile.TemporaryDirectory() as root:
                before = copy.deepcopy(self.artifact); self.artifact[key] = value
                try:
                    with patch('release_jobs.gh', side_effect=self.provider), self.assertRaises(ValueError):
                        worker.retained_followup(self.manifest, Path(root), self.original, self.config)
                finally:
                    self.artifact = before
