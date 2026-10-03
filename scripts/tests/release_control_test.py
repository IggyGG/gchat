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
        self.root = Path(self.temp.name)
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
