import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_automation_test import candidate
from release_coordinator import Coordinator, atomic_json
import release_control as control


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.controller = Coordinator(self.root, {})
        self.addCleanup(self.controller.ledger.close)
        self.manifest = candidate()
        self.release = self.controller.ledger.add(self.manifest)
        atomic_json(self.root / 'deployment/desired.json', {'release_id': self.release})

    def blocked(self, platform='linux-x86_64'):
        self.controller.ledger.transition(self.release, platform, 'building')
        self.controller.ledger.transition(self.release, platform, 'blocked', reason='source-bound failure')

    def test_status_does_not_write_the_ledger_or_expose_private_paths(self):
        atomic_json(self.root / 'deployment' / self.release / 'journal.json', {
            'state': 'blocked', 'targets': {'relay-1': {'observed': {'healthy': True,
            'running': {'executable': '/private/path', 'sha256': 'a' * 64}}}}})
        before = list(self.controller.ledger.db.iterdump())
        status = control.status(self.root)
        self.assertEqual(status['release_id'], self.release)
        self.assertNotIn('/private/path', json.dumps(status))
        self.assertEqual(list(self.controller.ledger.db.iterdump()), before)

    def test_resume_is_queued_until_existing_coordinator_consumes_it(self):
        self.blocked()
        effect = self.controller.ledger.effect(self.release, 'linux-x86_64', 'build')
        atomic_json(self.root / 'jobs' / effect['id'] / 'attempted.json', {'request_id': effect['id']})
        response = control.request(self.root, 'resume', platform='linux-x86_64')
        self.assertEqual(self.controller.ledger.target(self.release, 'linux-x86_64')['state'], 'blocked')
        control.consume(self.controller)
        self.assertEqual(self.controller.ledger.target(self.release, 'linux-x86_64')['state'], 'building')
        self.assertEqual(self.controller.ledger.effect(self.release, 'linux-x86_64', 'build')['id'], effect['id'])
        self.assertTrue((self.root / 'jobs' / effect['id'] / 'attempted.json').exists())
        proof = json.loads((self.root / 'control/results' / (response['request_id'] + '.json')).read_text())
        self.assertEqual(proof['state'], 'accepted')

    def test_completed_stages_survive_resume_and_manifests_never_change(self):
        self.blocked()
        baseline = self.controller.ledger.manifest(self.release)
        control.request(self.root, 'resume')
        control.consume(self.controller)
        self.assertEqual(self.controller.ledger.target(self.release, 'android')['state'], 'queued')
        self.assertEqual(self.controller.ledger.manifest(self.release), baseline)
        config = control.deployment_config(self.root, baseline, {'targets': []})
        self.assertIn('operator_retry', config)

    def test_unknown_release_platform_and_invalid_ids_do_not_queue_requests(self):
        for kwargs in [{'release': '../escape'}, {'platform': 'other'}, {'action': 'delete'}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                control.request(self.root, **{'action': 'resume', **kwargs})
        self.assertFalse((self.root / 'control/incoming').exists())

    def test_rejected_whole_release_resume_cannot_change_other_release(self):
        self.blocked()
        other = self.controller.ledger.add(candidate(2))
        atomic_json(self.root / 'deployment/desired.json', {'release_id': other})
        response = control.request(self.root, 'resume', release=self.release)
        control.consume(self.controller)
        self.assertEqual(self.controller.ledger.target(self.release, 'linux-x86_64')['state'], 'blocked')
        result = json.loads((self.root / 'control/results' / (response['request_id'] + '.json')).read_text())
        self.assertEqual(result['state'], 'rejected')

    def test_store_publication_cannot_be_rolled_back_by_operator_command(self):
        with self.assertRaises(ValueError):
            control.request(self.root, 'rollback', platform='android')

    def test_handoff_request_binds_journal_and_never_qualifies_a_release(self):
        from unittest.mock import patch
        import hashlib
        journal = self.root / 'deployment' / self.release / 'journal.json'
        atomic_json(journal, {'state': 'blocked', 'targets': {}})
        before = list(self.controller.ledger.db.iterdump())
        response = control.request(self.root, 'handoff', observed={'relay-1': 'a' * 64}, reason='Retain capacity fix')
        incoming = self.root / 'control/incoming' / (response['request_id'] + '.json')
        value = json.loads(incoming.read_text())
        self.assertEqual(value['journal_sha256'], hashlib.sha256(journal.read_bytes()).hexdigest())
        with patch('release_deployment.handoff') as handoff:
            control.consume(self.controller)
        handoff.assert_called_once_with(self.root, self.manifest, value)
        self.assertEqual(list(self.controller.ledger.db.iterdump()), before)
        self.assertEqual(json.loads((self.root / 'control/results' / incoming.name).read_text())['qualification'], 'unchanged')

    def test_handoff_requires_explicit_hashes_and_reason(self):
        for options in ({}, {'observed': {'relay-1': 'bad'}, 'reason': 'fix'},
                        {'observed': {'relay-1': 'a' * 64}, 'reason': ''}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                control.request(self.root, 'handoff', **options)

    def test_resume_cannot_resurrect_handed_off_deployment(self):
        atomic_json(self.root / 'deployment' / self.release / 'journal.json', {'state': 'handed_off'})
        response = control.request(self.root, 'resume')
        control.consume(self.controller)
        result = json.loads((self.root / 'control/results' / (response['request_id'] + '.json')).read_text())
        self.assertEqual(result['state'], 'rejected')

    def test_rollback_waits_for_busy_rollout_instead_of_losing_the_operator_request(self):
        from unittest.mock import patch
        response = control.request(self.root, 'rollback')
        pending = self.root / 'control/incoming' / (response['request_id'] + '.json')
        with patch('release_deployment.request_rollback', side_effect=BlockingIOError):
            control.consume(self.controller)
        self.assertTrue(pending.is_file())
        with patch('release_deployment.request_rollback') as rollback:
            control.consume(self.controller)
        rollback.assert_called_once_with(self.root, self.release)
        self.assertFalse(pending.exists())

    def test_status_exposes_flight_stage_and_deadline_without_private_worker_details(self):
        atomic_json(self.root / 'public/status.json', {'observed_at': 100,
                    'flight': {'active': self.release, 'pending': None},
                    'running_workers': [{'platform': 'ios', 'stage': 'build', 'private': '/private/worker'}]})
        atomic_json(self.root / 'deployment' / self.release / 'progress.json',
                    {'target': 'relay-1', 'stage': 'check', 'started_at': 100, 'deadline_at': 1000,
                     'log': '/private/rollout'})
        result = control.status(self.root, now=130)
        self.assertEqual(result['controller_status_age_seconds'], 30)
        self.assertEqual(result['deployment_progress']['deadline_at'], 1000)
        self.assertEqual(result['flight']['active'], self.release)
        self.assertNotIn('/private/', json.dumps(result))

    @unittest.skipUnless(os.name == 'posix', 'POSIX symlinks')
    def test_symlinked_operator_request_is_rejected_without_reading_target(self):
        incoming = self.root / 'control/incoming'
        incoming.mkdir(parents=True)
        private = self.root / 'private'
        private.write_text('private detail')
        (incoming / ('a' * 32 + '.json')).symlink_to(private)
        control.consume(self.controller)
        result = (self.root / 'control/results' / ('a' * 32 + '.json')).read_text()
        self.assertNotIn('private detail', result)
        self.assertEqual(private.read_text(), 'private detail')
