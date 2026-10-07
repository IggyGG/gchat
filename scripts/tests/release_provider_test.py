"""Provider waits preserve operation identity and leave local supervision runnable."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_provider as provider
from release_automation_test import candidate
from release_coordinator import Coordinator, atomic_json


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.environment = patch.dict(os.environ, GCHAT_RELEASE_PROVIDER_STATE=str(self.root / 'providers'))
        self.environment.start(); self.addCleanup(self.environment.stop)

    def test_exact_play_listing_quota_is_distinct_from_permission_denial(self):
        body = {'error': {'status': 'PERMISSION_DENIED', 'message': 'Listing releases quota exceeded.'}}
        with patch('release_provider.time.time', return_value=1000):
            with self.assertRaises(provider.ProviderWait) as caught:
                provider.classify('play', 'GET', '/tracks/production/releases', 403, {}, body)
        self.assertEqual(caught.exception.value['reason'], 'listing_quota')
        self.assertTrue(1900 <= caught.exception.value['next_poll_at'] <= 1990)
        for method, path, text in [('POST', '/tracks/production/releases', body),
                                  ('GET', '/edits', body),
                                  ('GET', '/tracks/production/releases', {'error': {'status': 'PERMISSION_DENIED'}})]:
            provider.classify('play', method, path, 403, {}, text)

    def test_retry_after_and_reset_are_honored_and_quota_survives_restart(self):
        with patch('release_provider.time.time', return_value=1000):
            with self.assertRaises(provider.ProviderWait) as first:
                provider.classify('github', 'GET', 'actions/runs', 403,
                                  {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': '5000'}, {})
            self.assertEqual(first.exception.value['next_poll_at'], 5001)
            with self.assertRaises(provider.ProviderWait) as retained:
                provider.before_request('github')
            self.assertEqual(retained.exception.value, first.exception.value)
            provider.reset_after_success('github')
            self.assertIsNotNone(provider.cooldown(self.root / 'providers', 'github'))
        with patch('release_provider.time.time', return_value=5002):
            with self.assertRaises(provider.ProviderWait) as second:
                provider.classify('github', 'GET', 'actions/runs', 429, {'Retry-After': '6000'}, {})
            self.assertEqual(second.exception.value['attempts'], 2)
            self.assertEqual(second.exception.value['next_poll_at'], 11002)
        provider.classify('github', 'GET', 'actions/runs', 403, {}, {'message': 'Forbidden'})

    def test_fallback_exponential_delay_is_bounded_and_success_resets_attempts(self):
        previous = 0
        for attempt in range(1, 9):
            now = previous + 1
            with patch('release_provider.time.time', return_value=now):
                with self.assertRaises(provider.ProviderWait) as caught:
                    provider.quota('apple', 429, {}, 'rate_limit')
                current = caught.exception.value
                self.assertTrue(min(21600, 900 * 2**(attempt-1)) <= current['next_poll_at'] - now <= 21600)
                previous = current['next_poll_at']
        with patch('release_provider.time.time', return_value=previous + 1):
            provider.reset_after_success('apple')
        self.assertFalse((self.root / 'providers/apple.json').exists())

    def test_shared_github_cache_reuses_metadata_but_never_mutations(self):
        reply = subprocess.CompletedProcess([], 0, b'HTTP/2 200 OK\r\ncontent-type: application/json\r\n\r\n{"id": 7}', b'')
        with patch('release_provider.subprocess.run', return_value=reply) as run, patch('release_provider.time.time', return_value=1000):
            self.assertEqual(provider.github('actions/runs/7', repo='owner/repo'), {'id': 7})
            self.assertEqual(provider.github('actions/runs/7', repo='owner/repo'), {'id': 7})
            self.assertEqual(run.call_count, 1)
            provider.github('actions/workflows/run/dispatches', repo='owner/repo', method='POST', body={})
            provider.github('actions/workflows/run/dispatches', repo='owner/repo', method='POST', body={})
            self.assertEqual(run.call_count, 3)
        with patch('release_provider.subprocess.run', return_value=reply) as run, patch('release_provider.time.time', return_value=1120):
            provider.github('actions/runs/7', repo='owner/repo')
            run.assert_called_once()

    def test_github_header_quota_prevents_further_requests_and_body_is_not_retained(self):
        reply = subprocess.CompletedProcess([], 1, b'HTTP/2 403 Forbidden\r\nx-ratelimit-remaining: 0\r\n\r\n{"secret":"do-not-retain"}', b'HTTP 403')
        with patch('release_provider.subprocess.run', return_value=reply) as run:
            for _ in range(2):
                with self.assertRaises(provider.ProviderWait): provider.github('actions/runs', repo='owner/repo')
            self.assertEqual(run.call_count, 1)
        self.assertNotIn('do-not-retain', (self.root / 'providers/github.json').read_text())

    def test_archive_headers_are_stripped_without_altering_exact_binary_bytes(self):
        payload = b'PK\x03\x04' + bytes(range(256)) * 10000
        destination = self.root / 'archive.partial'
        def run(command, stdout, **kwargs):
            self.assertIn('--include', command)
            stdout.write(b'HTTP/2 302 Found\r\nlocation: private\r\n\r\nHTTP/2 200 OK\r\ncontent-type: application/zip\r\n\r\n' + payload)
        with patch('release_provider.subprocess.run', side_effect=run):
            with destination.open('wb') as stream:
                provider.github_download('actions/artifacts/1/zip', repo='owner/repo', stream=stream, timeout=10)
        self.assertEqual(destination.read_bytes(), payload)

    def test_archive_quota_headers_survive_failed_gh_exit(self):
        def run(command, stdout, **kwargs):
            stdout.write(b'HTTP/2 429 Too Many Requests\r\nRetry-After: 4000\r\n\r\n{}')
            raise subprocess.CalledProcessError(1, command, stderr=b'HTTP 429')
        with patch('release_provider.subprocess.run', side_effect=run), patch('time.time', return_value=1000):
            with (self.root / 'partial').open('wb') as stream, self.assertRaises(provider.ProviderWait) as caught:
                provider.github_download('actions/artifacts/1/zip', repo='owner/repo', stream=stream, timeout=10)
            self.assertEqual(caught.exception.value['next_poll_at'], 5000)

    def test_committed_store_journal_survives_quota_and_resumes_observation_only(self):
        import hashlib
        from release_stores import submit_google
        payload = self.root / 'app.aab'; payload.write_bytes(b'qualified')
        identity = {'release_id': 'a' * 64, 'version_code': '1042',
                    'aab_sha256': hashlib.sha256(payload.read_bytes()).hexdigest()}
        journal = self.root / 'submission.json'
        original = {'identity': identity, 'edit': 'original', 'commit_attempted': True,
                    'edit_attempted': True, 'upload_attempted': True}
        atomic_json(journal, original)
        api = Mock()
        api.request.side_effect = lambda *args, **kwargs: provider.quota('play', 403, {}, 'listing_quota')
        with self.assertRaises(provider.ProviderWait): submit_google(api, {}, identity, payload, journal)
        self.assertEqual(json.loads(journal.read_text()), original)
        api.request.side_effect = None
        api.request.return_value = {'releases': [{'track': 'production',
            'activeArtifacts': [{'versionCode': '1042'}], 'releaseLifecycleState': 'RELEASE_LIFECYCLE_STATE_IN_REVIEW'}]}
        self.assertEqual(submit_google(api, {}, identity, payload, journal)['state'], 'in_review')
        self.assertEqual([call.args for call in api.request.call_args_list],
                         [('GET', '/tracks/production/releases')] * 2)
        self.assertEqual(json.loads(journal.read_text()), original)

    def test_worker_exit_preserves_typed_operation_bound_wait_without_receipt(self):
        manifest = self.root / 'candidate.json'; atomic_json(manifest, {'release_id': 'release'})
        output = self.root / 'job/receipt.json'
        env = dict(GCHAT_RELEASE_RECEIPT=str(output), GCHAT_RELEASE_MANIFEST=str(manifest),
                   GCHAT_RELEASE_REQUEST_ID='original', GCHAT_RELEASE_TARGET='android', GCHAT_RELEASE_STAGE='observe')
        with patch.dict(os.environ, env), self.assertRaises(SystemExit) as stopped:
            provider.worker_main(lambda: provider.quota('play', 403, {}, 'listing_quota'))
        self.assertEqual(stopped.exception.code, 75)
        waiting = json.loads((output.parent / 'provider-wait.json').read_text())
        self.assertEqual((waiting['request_id'], waiting['release_id'], waiting['stage']), ('original', 'release', 'observe'))
        self.assertFalse(output.exists())

    def test_store_request_keeps_unknown_commit_and_never_reuploads_after_quota(self):
        from release_stores import Provider, ProviderError
        response = Mock(ok=False, status_code=403, headers={}, content=b'x')
        response.json.return_value = {'error': {'status': 'PERMISSION_DENIED', 'message': 'Listing releases quota exceeded.'}}
        session = Mock(); session.request.return_value = response
        api = Provider(session, 'https://androidpublisher.googleapis.com/app')
        with self.assertRaises(provider.ProviderWait): api.request('GET', '/tracks/production/releases')
        with self.assertRaises(provider.ProviderWait): api.request('POST', '/edits')
        self.assertEqual(session.request.call_count, 1)
        (self.root / 'providers/play.json').unlink()
        response.json.return_value = {'error': {'status': 'PERMISSION_DENIED', 'message': 'Denied'}}
        with self.assertRaises(ProviderError): api.request('GET', '/tracks/production/releases')

    def test_external_review_freshness_matches_poll_and_quota_without_claiming_new_observation(self):
        with patch('release_provider.time.time', return_value=1000):
            provider.defer_effect(self.root, 'release', 'ios', 'submit', 'same', 'apple', 900)
        with patch('release_provider.time.time', return_value=1800):
            self.assertTrue(provider.external_wait_fresh(self.root, 'release', 'ios', 'submit', 'same', 1000))
            self.assertFalse(provider.external_wait_fresh(self.root, 'release', 'ios', 'submit', 'other', 1000))
        with patch('release_provider.time.time', return_value=2021):
            self.assertFalse(provider.external_wait_fresh(self.root, 'release', 'ios', 'submit', 'same', 1000))
        wait = dict(schema=1, provider='apple', reason='rate_limit', http_status=429, observed_at=1900,
                    next_poll_at=5500, release_id='release', platform='ios', stage='submit', request_id='same')
        with patch('release_provider.time.time', return_value=1900):
            provider.defer_effect(self.root, 'release', 'ios', 'submit', 'same', 'apple', 900, wait)
        with patch('release_provider.time.time', return_value=5000):
            self.assertTrue(provider.external_wait_fresh(self.root, 'release', 'ios', 'submit', 'same', 1000))
            self.assertTrue(provider.quota_waiting(self.root, 'release', 'ios'))
        with patch('release_provider.time.time', return_value=5621):
            self.assertFalse(provider.external_wait_fresh(self.root, 'release', 'ios', 'submit', 'same', 1000))


class ControllerPollingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.manifest = candidate()
        self.recipe = {'provider': 'play', 'run': ['initial'], 'reconcile': ['retained']}
        self.config = {'workers': {'android': {'observe': self.recipe}}}

    def controller(self):
        result = Coordinator(self.root, self.config)
        self.addCleanup(result.ledger.close); result.ledger.add(self.manifest)
        return result

    def test_restart_keeps_next_poll_and_same_effect_instead_of_reminting_operation(self):
        first = self.controller()
        with patch('release_coordinator.subprocess.run', return_value=Mock(returncode=75)) as run, patch('time.time', return_value=1000):
            self.assertIsNone(first.execute(self.manifest, 'android', 'observe'))
            original = first.ledger.effect(self.manifest['release_id'], 'android', 'observe')['id']
            self.assertEqual(run.call_count, 1)
        restarted = self.controller()
        with patch('release_coordinator.subprocess.run', return_value=Mock(returncode=75)) as run, patch('time.time', return_value=1899):
            self.assertIsNone(restarted.execute(self.manifest, 'android', 'observe')); run.assert_not_called()
        with patch('release_coordinator.subprocess.run', return_value=Mock(returncode=75)) as run, patch('time.time', return_value=1900):
            self.assertIsNone(restarted.execute(self.manifest, 'android', 'observe'))
            self.assertEqual(run.call_args.args[0], ['retained'])
            self.assertEqual(run.call_args.kwargs['env']['GCHAT_RELEASE_REQUEST_ID'], original)

    def test_quota_wait_keeps_ledger_state_and_other_local_stage_runs(self):
        c = self.controller()
        c.config['workers']['android']['verify'] = {'run': ['local'], 'reconcile': ['local']}
        c.ledger.db.execute("UPDATE platforms SET state='in_review' WHERE candidate=? AND platform='android'", (self.manifest['release_id'],)); c.ledger.db.commit()
        def run(argv, **kwargs):
            env = kwargs['env']
            if argv == ['initial']:
                atomic_json(Path(env['GCHAT_RELEASE_RECEIPT']).parent / 'provider-wait.json', {
                    'schema': 1, 'release_id': self.manifest['release_id'], 'platform': 'android', 'stage': 'observe',
                    'request_id': env['GCHAT_RELEASE_REQUEST_ID'], 'provider': 'play', 'reason': 'listing_quota',
                    'http_status': 403, 'observed_at': 1000, 'next_poll_at': 9000})
            return Mock(returncode=75)
        with patch('release_coordinator.subprocess.run', side_effect=run) as launch, patch('time.time', return_value=1000):
            c.step(self.manifest['release_id'], 'android')
            self.assertEqual(c.ledger.target(self.manifest['release_id'], 'android')['state'], 'in_review')
            c.execute(self.manifest, 'android', 'observe')
            c.execute(self.manifest, 'android', 'verify')
            self.assertEqual([call.args[0] for call in launch.call_args_list], [['initial'], ['local']])
            self.assertEqual(provider.public_waits(self.root)[0]['reason'], 'listing_quota')

    def test_finished_local_worker_is_collected_before_provider_deadline(self):
        self.config['nonblocking_workers'] = True
        c = self.controller(); process = Mock(returncode=75); process.poll.return_value = None
        with patch('release_coordinator.subprocess.Popen', return_value=process), patch('time.time', return_value=1000):
            c.execute(self.manifest, 'android', 'observe')
        effect = c.ledger.effect(self.manifest['release_id'], 'android', 'observe')['id']
        process.poll.return_value = 75
        with patch('time.time', return_value=1010), patch('release_coordinator.subprocess.Popen') as start:
            c.execute(self.manifest, 'android', 'observe')
            self.assertNotIn(effect, c.running_workers)
            c.execute(self.manifest, 'android', 'observe'); start.assert_not_called()

    def test_poll_bounds_are_checked_before_state_creation(self):
        for key, value in [('github_poll_interval_seconds', 10), ('store_poll_interval_seconds', 0),
                           ('store_poll_interval_seconds', True), ('github_poll_interval_seconds', 99999)]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError): Coordinator(self.root / 'absent', {key: value})
        self.assertFalse((self.root / 'absent').exists())
        c = self.controller()
        self.assertEqual((c.poll_interval, c.github_poll_interval, c.store_poll_interval), (10, 120, 900))

    def test_controller_overlay_is_considered_before_starting_next_deployment_worker(self):
        events = []
        c = Coordinator(self.root / 'ordering', {})
        self.addCleanup(c.ledger.close)
        with patch('release_controller.reconcile', side_effect=lambda _: events.append('controller')), \
             patch.object(c, 'reconcile_deployment', side_effect=lambda: events.append('deployment')):
            c.tick()
        self.assertEqual(events, ['controller', 'deployment'])
