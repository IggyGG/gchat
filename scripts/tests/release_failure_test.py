import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_automation_test import candidate
import release_failure as failure
import release_provider as provider
import release_jobs as jobs
from release_coordinator import Coordinator, atomic_json


class FailureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name); self.manifest = candidate()
        self.work = self.root / ('f' * 64); self.work.mkdir()
        self.run = {'id': 123, 'head_sha': self.manifest['sources']['gchat']['commit'],
                    'run_attempt': 1, 'status': 'completed', 'conclusion': 'failure',
                    'created_at': '2026-01-01T00:00:00Z'}
        self.checks = {'run_id': 123, 'workflow_commit': self.run['head_sha'], 'run_attempt': 1,
                      'jobs': {'windows': {'job_id': 7, 'attempt': 1, 'status': 'completed',
                                          'conclusion': 'failure', 'step': 'Native qualification'}}}

    def diagnose(self, raw=b'##[error]The hosted runner lost communication with the server.', truncated=False):
        return failure.native_diagnostics(self.manifest, 'windows-x86_64', self.work, self.run, self.checks,
            repo='IggyGG/gchat', download=lambda *a, **k: (raw, truncated))

    def test_only_positive_complete_infrastructure_evidence_permits_native_retry(self):
        examples = [
            ('##[error]The hosted runner lost communication with the server.', True, 'native_runner_unavailable'),
            ('##[error]failed to download action: 503', True, 'native_runner_unavailable'),
            ('test result: FAILED. 6 passed; 1 failed; connection reset', True, 'native_check_failed'),
            ('error[E0308]: mismatched types\n##[error]hosted runner unavailable', True, 'native_check_failed'),
            ('No signing certificate found', True, 'native_operator_action'),
            ('HTTP 503\nfixture timed out', True, 'native_failure_unknown'),
            ('error: failed to download from `https://static.crates.io/crates/quick-xml/0.41.0/download`\nCaused by:\n  [6] Could not resolve host: static.crates.io', True, 'native_dependency_network'),
            ('error: unexplained provider failure', True, 'native_failure_unknown'),
            ('##[error]hosted runner unavailable', False, 'native_log_truncated'),
            ('x' * 20000 + '##[error]hosted runner unavailable', True, 'native_log_truncated'),
        ]
        for text, complete, code in examples:
            with self.subTest(code=code): self.assertEqual(failure.classify_native_log(text, complete=complete), code)

    def test_failure_identifiers_exclude_log_arguments_and_expected_negative_fixture(self):
        text = ("---- chat_service::host_registration::tests::native_paths stdout ----\n"
                "Failed to import test module: android_release_cluster_test\n"
                "runner.swift:69: error: -[LifecycleTests.GChatLifecycleTests testProfileBackgroundAndReopen] : timeout\n"
                "AssertionError: original gate failed\nprivate-token=do-not-publish")
        self.assertEqual(failure.failed_checks(text), ['LifecycleTests.GChatLifecycleTests testProfileBackgroundAndReopen',
            'android_release_cluster_test', 'chat_service::host_registration::tests::native_paths'])

    def test_timestamped_and_nested_unittest_failures_expose_only_identifiers(self):
        name = 'release_provider_test.ProviderTests.test_store_request_keeps_unknown_commit_and_never_reuploads_after_quota'
        text = ('2026-10-14T11:23:58.3097989Z ERROR: test_store_request (' + name + ')\n'
                'FAIL: test_fixture (controller_runtime_test.RuntimeTests.test_failure.<locals>.Failed.test_bad)\n'
                'ERROR: test_secret (module.Tests.test_secret password=private)\n'
                'private-token=do-not-publish')
        self.assertEqual(failure.failed_checks(text), [name])
        self.assertEqual(failure.failed_checks('ERROR: test_store_request (' + name + ')\n'), [name])

    def test_bound_logs_are_immutable_reused_and_tampering_is_rejected(self):
        report, ref = self.diagnose()
        self.assertTrue(report['native_retry_eligible'])
        with patch('release_provider.github_log', side_effect=AssertionError('unexpected network')):
            self.assertEqual(self.diagnose(b'changed provider log'), (report, ref))
        self.assertEqual(failure.retained_diagnostics(self.work, self.manifest, 'windows-x86_64'), (report, ref))
        (self.work / report['jobs'][0]['log']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'changed'): self.diagnose()

    def test_late_old_diagnostic_cannot_replace_latest_native_attempt(self):
        first, first_ref = self.diagnose()
        self.run['run_attempt'] = self.checks['run_attempt'] = 2
        self.checks['jobs']['windows']['attempt'] = 2
        latest, latest_ref = self.diagnose(b'test result: FAILED. 0 passed; 1 failed')
        self.run['run_attempt'] = self.checks['run_attempt'] = 1
        self.checks['jobs']['windows']['attempt'] = 1
        self.diagnose()
        self.assertEqual(failure.retained_diagnostics(self.work, self.manifest, 'windows-x86_64'), (latest, latest_ref))
        self.assertEqual(json.loads((self.work / first_ref['path']).read_text()), first)

    def test_quota_pending_preserves_failed_job_without_inventing_cause(self):
        def download(*a, **k): raise provider.ProviderWait({'provider': 'github', 'next_poll_at': 5000})
        report, _ = failure.native_diagnostics(self.manifest, 'windows-x86_64', self.work, self.run, self.checks,
                                              repo='IggyGG/gchat', download=download)
        self.assertTrue(report['diagnostics_pending']); self.assertFalse(report['native_retry_eligible'])
        self.assertEqual(report['jobs'][0]['job_id'], 7)
        self.assertEqual(report['category'], 'unclassified')
        before = list((self.work / 'native-diagnostics').rglob('*.json'))
        final, _ = self.diagnose(b'test result: FAILED. 0 passed; 1 failed')
        self.assertFalse(final['diagnostics_pending']); self.assertEqual(final['category'], 'code')
        self.assertTrue(all(path.is_file() for path in before))

    def test_cross_source_or_run_diagnostics_are_refused_before_download(self):
        for key, value in [('head_sha', '0' * 40), ('id', 124), ('id', True), ('run_attempt', 2)]:
            with self.subTest(key=key), patch('release_provider.github_log') as download:
                with self.assertRaises(ValueError):
                    failure.native_diagnostics(self.manifest, 'windows-x86_64', self.work,
                        {**self.run, key: value}, self.checks, repo='IggyGG/gchat', download=download)
                download.assert_not_called()

    def test_nested_failure_archive_is_source_bound_bounded_and_never_extracted(self):
        archive = self.root / 'fixture.zip'
        with zipfile.ZipFile(archive, 'w') as bundle:
            bundle.writestr('../../outside.log', "ModuleNotFoundError: No module named 'fcntl'")
            bundle.writestr('evidence/native.log', 'error[E0308]: mismatched types')
        raw = archive.read_bytes(); sha = hashlib.sha256(raw).hexdigest()
        artifact = {'id': 17, 'name': 'windows-x86_64', 'expired': False, 'digest': 'sha256:' + sha,
                    'size_in_bytes': len(raw), 'workflow_run': {'id': self.run['id'], 'head_sha': self.run['head_sha']}}
        def download(path, **kwargs):
            self.assertEqual(path, 'actions/artifacts/17/zip')
            self.assertEqual(kwargs['maximum_bytes'], len(raw))
            kwargs['stream'].write(raw)
        with patch('shutil.disk_usage', return_value=type('Disk', (), {'free': 32 * 1024 ** 3})()):
            result = failure.archive_diagnostics(self.manifest, 'windows-x86_64', self.work, self.run, self.checks,
                repo='IggyGG/gchat', api=lambda path: {'artifacts': [artifact]}, download=download)
        self.assertEqual({m['code'] for m in result[0]['members']}, {'native_check_failed', 'native_posix_import'})
        self.assertFalse((self.root / 'outside.log').exists())
        self.assertTrue(all((self.work / m['log']).is_file() for m in result[0]['members']))
        with self.assertRaisesRegex(ValueError, 'original run/source'):
            failure.archive_diagnostics(self.manifest, 'windows-x86_64', self.work, self.run, self.checks,
                repo='IggyGG/gchat', api=lambda path: {'artifacts': [{**artifact, 'workflow_run': {'id': 99}}]},
                download=lambda *a, **k: self.fail('wrong-source download'))

    def test_child_failure_can_refine_wrapper_but_never_authorize_a_native_retry(self):
        with patch.dict(os.environ, GCHAT_RELEASE_STAGE='diagnose'), \
             patch('release_failure.archive_diagnostics', return_value=[{'state': 'retained', 'members': [
                 {'code': 'native_posix_import'}]}]):
            report, _ = self.diagnose(b'wrapper exited 1; detailed errors retained in child log')
        self.assertEqual(report['code'], 'native_posix_import'); self.assertFalse(report['native_retry_eligible'])

    def test_structured_worker_boundary_is_execution_bound_and_redacted(self):
        manifest = self.work / 'candidate.json'; atomic_json(manifest, self.manifest)
        environment = {'GCHAT_RELEASE_MANIFEST': str(manifest), 'GCHAT_RELEASE_RECEIPT': str(self.work / 'receipt.json'),
                       'GCHAT_RELEASE_EXECUTION_ID': '123-abcdef.log', 'GCHAT_RELEASE_REQUEST_ID': self.work.name,
                       'GCHAT_RELEASE_TARGET': 'windows-x86_64', 'GCHAT_RELEASE_STAGE': 'build'}
        with patch.dict(os.environ, environment):
            with self.assertRaisesRegex(ValueError, 'private-token'):
                provider.worker_main(lambda: (_ for _ in ()).throw(ValueError('private-token')))
        report = failure.read_worker_failure(self.work, self.manifest, 'windows-x86_64', 'build', '123-abcdef.log')
        self.assertEqual(report['category'], 'unclassified')
        self.assertNotIn('private-token', json.dumps(report))
        self.assertIsNone(failure.read_worker_failure(self.work, self.manifest, 'windows-x86_64', 'build', 'new.log'))
        with self.assertRaises(ValueError):
            failure.read_worker_failure(self.work, self.manifest, 'ios', 'build', '123-abcdef.log')

    def test_child_timeout_classification_reaches_coordinator_and_original_effect(self):
        script = Path(__file__).resolve().parents[1] / 'release_jobs.py'
        recipe = {'run': [sys.executable, str(script)], 'reconcile': [sys.executable, str(script), '--reconcile']}
        controller = Coordinator(self.root / 'state', {'minimum_free_bytes': 0, 'automatic_recovery': True,
            'workers': {'windows-x86_64': {'build': recipe}}})
        self.addCleanup(controller.ledger.close)
        release = controller.ledger.add(self.manifest)
        def launch(*args, env, **kwargs):
            with patch.dict(os.environ, env): failure.retain_worker_failure(subprocess.TimeoutExpired('private', 1))
            return subprocess.CompletedProcess([], 1)
        with patch('release_coordinator.subprocess.run', side_effect=launch): controller.step(release, 'windows-x86_64')
        recovery = json.loads(controller.recovery_path(release, 'windows-x86_64').read_text())
        self.assertTrue(recovery['transient']); self.assertEqual(recovery['code'], 'worker_timeout')
        self.assertEqual(recovery['failure']['request_id'], controller.ledger.effect(release, 'windows-x86_64', 'build')['id'])

    def test_verified_store_configuration_correction_resumes_only_affected_worker(self):
        settings = self.root / 'stores.json'
        atomic_json(settings, {'android': {'package': 'original'}, 'ios': {'app_id': 'original'}})
        script = Path(__file__).resolve().parents[1] / 'release_store_worker.py'
        argv = [sys.executable, str(script), '--config', str(settings)]
        controller = Coordinator(self.root / 'state', {'controller_revision': 'stale-pin',
            'workers': {p: {'submit': {'run': argv, 'reconcile': argv}} for p in ('android', 'ios')}})
        self.addCleanup(controller.ledger.close)
        release = controller.ledger.add(self.manifest)
        for platform in ('android', 'ios'):
            for state in ('building', 'verifying', 'verified', 'submitting'):
                controller.ledger.transition(release, platform, state, evidence='f' * 64)
            controller.record_failure(release, platform, 'submit', failure.WorkerFailure('store_action_required'))
            controller.ledger.transition(release, platform, 'blocked', reason='Store account requires attention')
        atomic_json(settings, {'android': {'package': 'original'}, 'ios': {'app_id': 'corrected'}})
        self.assertFalse(controller.resume_corrected(release, 'android', controller.ledger.target(release, 'android')))
        self.assertTrue(controller.resume_corrected(release, 'ios', controller.ledger.target(release, 'ios')))
        self.assertEqual(controller.config['controller_revision'], 'stale-pin')

    def test_store_account_and_unknown_mutation_are_distinct_from_transient(self):
        from release_stores import ProviderError
        manifest = self.work / 'candidate.json'; atomic_json(manifest, self.manifest)
        environment = {'GCHAT_RELEASE_MANIFEST': str(manifest), 'GCHAT_RELEASE_RECEIPT': str(self.work / 'receipt.json'),
                       'GCHAT_RELEASE_EXECUTION_ID': '123-abcdef.log', 'GCHAT_RELEASE_REQUEST_ID': self.work.name,
                       'GCHAT_RELEASE_TARGET': 'android', 'GCHAT_RELEASE_STAGE': 'submit'}
        for error, code, retry in [(ProviderError('permission', status=403), 'store_action_required', False),
                                   (ProviderError('unknown commit'), 'provider_outcome_unknown', False),
                                   (ProviderError('connection', transient=True), 'provider_unavailable', True)]:
            with patch.dict(os.environ, environment): failure.retain_worker_failure(error)
            report = failure.read_worker_failure(self.work, self.manifest, 'android', 'submit', '123-abcdef.log')
            self.assertEqual((report['code'], report['reconcile_retry']), (code, retry))

    def test_native_policy_retry_survives_lost_reply_and_cannot_rearm(self):
        report, _ = self.diagnose()
        now = 1767225700
        def retry(api):
            return jobs.policy_retry(self.manifest, 'windows-x86_64', self.work, self.run, self.checks, report,
                                     validate_fresh=lambda fresh: self.assertEqual(fresh, self.run), api=api)
        with patch.dict(os.environ, GCHAT_RELEASE_NATIVE_RETRY_POLICY='native-transient-v1'), \
             patch('release_jobs.time.time', return_value=now):
            calls = []
            def api(path, **kwargs):
                calls.append(path)
                if kwargs.get('method') == 'POST':
                    self.assertTrue((self.work / 'native-policy-retry.json').is_file())
                    raise subprocess.TimeoutExpired('gh', 1)
                return self.run
            with self.assertRaises(subprocess.TimeoutExpired): retry(api)
            self.assertTrue(retry(lambda *a, **k: self.fail('second request')))
            self.assertEqual(len(calls), 2)
        with patch('release_jobs.time.time', return_value=now + 1801):
            with self.assertRaisesRegex(ValueError, 'unknown'): retry(lambda *a, **k: self.fail('redispatched'))
        self.run['run_attempt'] = 2
        self.assertFalse(retry(lambda *a, **k: self.fail('rearmed')))

    def test_automatic_retry_requires_policy_complete_evidence_and_original_deadline(self):
        report, _ = self.diagnose()
        variants = ({}, {'GCHAT_RELEASE_NATIVE_RETRY_POLICY': 'native-transient-v1', 'GCHAT_RELEASE_RECONCILE_ONLY': '1'})
        for env in variants:
            with patch.dict(os.environ, env, clear=True), patch('release_jobs.time.time', return_value=1767225700):
                self.assertFalse(jobs.policy_retry(self.manifest, 'windows-x86_64', self.work, self.run, self.checks, report,
                    validate_fresh=lambda r: None, api=lambda *a, **k: self.fail('not authorized')))
        with patch.dict(os.environ, GCHAT_RELEASE_NATIVE_RETRY_POLICY='native-transient-v1'), \
             patch('release_jobs.time.time', return_value=1767232900):
            self.assertFalse(jobs.policy_retry(self.manifest, 'windows-x86_64', self.work, self.run, self.checks, report,
                validate_fresh=lambda r: None, api=lambda *a, **k: self.fail('deadline extended')))


class LogTransportTests(unittest.TestCase):
    def test_archive_stream_enforces_its_cap_before_filling_storage(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'bounded.zip'
            with output.open('wb') as stream, self.assertRaisesRegex(ValueError, 'byte cap'):
                provider.bounded_diagnostic_download([sys.executable, '-c', "import sys; sys.stdout.buffer.write(b'x'*1000000)"],
                                                     stream, 65536, 5)
            self.assertLessEqual(output.stat().st_size, 65536)

    def run_log(self, code, **kwargs):
        popen = subprocess.Popen
        def spawn(argv, **options):
            self.assertEqual(argv, ['gh', 'api', '--include', '--allow-escape-sequences', 'repos/IggyGG/gchat/actions/jobs/7/logs'])
            return popen([sys.executable, '-c', code], **options)
        with patch.dict(os.environ, {}, clear=True), patch('release_provider.github_log_options', return_value=['--allow-escape-sequences']), \
             patch('release_provider.subprocess.Popen', side_effect=spawn):
            return provider.github_log('actions/jobs/7/logs', repo='IggyGG/gchat', **kwargs)

    def test_escape_sequence_opt_in_is_private_log_only_and_backwards_compatible(self):
        for stdout, expected in [(b'usage: gh api', []), (b'--allow-escape-sequences', ['--allow-escape-sequences'])]:
            provider.github_log_options.cache_clear()
            with patch('release_provider.subprocess.run', return_value=subprocess.CompletedProcess([], 0, stdout, b'')) as process:
                self.assertEqual(provider.github_log_options(), expected)
                self.assertEqual(provider.github_log_options(), expected)
                self.assertEqual(process.call_count, 1)
        provider.github_log_options.cache_clear()

    def test_bounded_log_transport_drains_stderr_and_preserves_exact_bytes(self):
        raw, truncated = self.run_log("import sys; sys.stderr.write('e'*100000); sys.stdout.buffer.write(b'HTTP/2 302 Found\\r\\n\\r\\nHTTP/2 200 OK\\r\\n\\r\\noriginal\\r\\n')", maximum_bytes=100)
        self.assertEqual(raw, b'original\r\n'); self.assertFalse(truncated)

    def test_oversized_stream_and_timeout_are_bounded_and_child_reaped(self):
        raw, truncated = self.run_log("import sys; sys.stdout.buffer.write(b'HTTP/2 200 OK\\n\\n'+b'x'*1000000)", maximum_bytes=1024)
        self.assertEqual(raw, b'x' * 1024); self.assertTrue(truncated)
        with self.assertRaises(subprocess.TimeoutExpired):
            self.run_log('import time; time.sleep(30)', timeout=0.05)

    def test_provider_503_is_structured_but_ordinary_403_is_not_retryable(self):
        with patch.dict(os.environ, {}, clear=True):
            for status in (503, 403):
                reply = subprocess.CompletedProcess([], 1, f'HTTP/2 {status} Failed\r\n\r\n{{}}'.encode(), b'private')
                with patch('release_provider.subprocess.run', return_value=reply):
                    error = failure.WorkerFailure if status == 503 else subprocess.CalledProcessError
                    with self.assertRaises(error): provider.github('actions/runs/1', repo='IggyGG/gchat')


if __name__ == '__main__': unittest.main()
