import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_automation_test import candidate
from release_coordinator import Coordinator, atomic_json
from release_minutes import POLICY, budget, enabled, verify
from release_publish import job
from release_flight import select


class MinutesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.manifest = candidate()
        self.controller = Coordinator(self.root, {'publication_policy': POLICY})
        self.addCleanup(self.controller.ledger.close)
        self.controller.ledger.add(self.manifest)
        folder = job(self.root, self.manifest, 'android', 'verify')
        atomic_json(folder / 'original.json', {'native_verification_fixture': True})
        self.original = folder / 'original.json'
        atomic_json(folder / 'receipt.json', {'schema': 1, 'release_id': self.manifest['release_id'],
            'sources': self.manifest['sources'], 'platform': 'android', 'stage': 'verify',
            'passed': True, 'source_unchanged': True,
            'evidence': [{'path': 'original.json', 'sha256': hashlib.sha256(self.original.read_bytes()).hexdigest()}]})
        self.deployment = self.root / 'deployment' / self.manifest['release_id'] / 'journal.json'
        self.journal = {'state': 'deployed', 'sources': self.manifest['sources'], 'observed_at': 100,
            'targets': {'relay-' + str(i): {'state': 'deployed', 'observed': {'healthy': True, 'matches': True}}
                        for i in range(1, 9)}}
        atomic_json(self.deployment, self.journal)

    def test_native_gate_and_relays_do_not_claim_full_gui_qualification(self):
        proof = verify(self.root, self.manifest, 'android', now=100)
        self.assertTrue(proof['passed'])
        self.assertTrue(proof['relay_compatible'])
        self.assertEqual(proof['publication_policy'], POLICY)
        self.assertFalse(proof['qualification_complete'])
        self.assertIn('full_installed_gui_upgrade_rollback', proof['unqualified_scopes'])

    def test_missing_changed_or_failed_native_gate_cannot_publish(self):
        receipt = self.original.parent / 'receipt.json'
        saved = receipt.read_bytes()
        for field, value in [('passed', False), ('source_unchanged', False), ('platform', 'ios')]:
            row = json.loads(saved); row[field] = value; atomic_json(receipt, row)
            with self.subTest(field=field), self.assertRaises(ValueError):
                verify(self.root, self.manifest, 'android', now=100)
        receipt.write_bytes(saved)
        self.original.write_bytes(b'changed original native evidence')
        with self.assertRaisesRegex(ValueError, 'evidence changed'):
            verify(self.root, self.manifest, 'android', now=100)

    def test_stale_foreign_unhealthy_or_missing_relays_cannot_publish(self):
        for kind in ('stale', 'future', 'source', 'missing', 'unhealthy', 'mismatch'):
            row = copy.deepcopy(self.journal)
            if kind == 'stale': row['observed_at'] = -201
            elif kind == 'future': row['observed_at'] = 101
            elif kind == 'source': row['sources']['gcoms']['commit'] = 'd' * 40
            elif kind == 'missing': del row['targets']['relay-8']
            else: row['targets']['relay-8']['observed']['healthy' if kind == 'unhealthy' else 'matches'] = False
            atomic_json(self.deployment, row)
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                verify(self.root, self.manifest, 'android', now=100)

    def test_budget_survives_restart_and_retry_and_expires_at_exact_boundary(self):
        first = budget(self.root, self.manifest, 'android', 'build', now=100)
        self.assertEqual(budget(self.root, self.manifest, 'android', 'verify', now=300), first)
        self.assertEqual(budget(self.root, self.manifest, 'android', 'publish', now=3699), first)
        with self.assertRaisesRegex(ValueError, '60 minutes'):
            budget(self.root, self.manifest, 'android', 'publish', now=3700)

    def test_fast_policy_is_explicit_and_unknown_policies_fail(self):
        self.assertFalse(enabled({}))
        self.assertTrue(enabled({'publication_policy': POLICY}))
        with self.assertRaises(ValueError): enabled({'publication_policy': 'ignore-signatures'})

    def test_external_review_pause_does_not_reset_the_remaining_active_budget(self):
        budget(self.root, self.manifest, 'ios', 'verify', now=100)
        budget(self.root, self.manifest, 'ios', 'submit', now=200, paused=True)
        budget(self.root, self.manifest, 'ios', 'submit', now=10000, paused=True)
        resumed = budget(self.root, self.manifest, 'ios', 'submit', now=10200)
        self.assertEqual(resumed['paused_seconds'], 10000)
        self.assertEqual(resumed['deadline_at'], 13700)
        with self.assertRaisesRegex(ValueError, '60 minutes'):
            budget(self.root, self.manifest, 'ios', 'submit', now=13700)

    def test_full_gui_acceptance_is_not_a_fast_mobile_publication_prerequisite(self):
        release = self.manifest['release_id']
        for state in ('building', 'verifying', 'verified'):
            self.controller.ledger.transition(release, 'android', state, evidence='f' * 64)
        self.controller.config['workers'] = {'android': {'acceptance': {}, 'compatibility': {}}}
        proof = verify(self.root, self.manifest, 'android', now=100)
        with patch.object(self.controller, 'deployment_ready', return_value=True), \
             patch.object(self.controller, 'execute', return_value=(proof, 'f' * 64)) as execute:
            self.controller.step(release, 'android')
        self.assertEqual([call.args[2] for call in execute.call_args_list], ['compatibility'])
        self.assertEqual(self.controller.ledger.target(release, 'android')['state'], 'submitting')

    def test_failed_optional_platform_and_sdk_do_not_hold_next_routine_release(self):
        first = self.manifest['release_id']
        second = self.controller.ledger.add(candidate(2))
        self.controller.ledger.db.execute("UPDATE platforms SET state='available' WHERE candidate=?", (first,))
        self.controller.ledger.db.execute("UPDATE platforms SET state='blocked' WHERE candidate=? AND platform='android'", (first,))
        self.controller.ledger.db.execute("UPDATE platforms SET state='building' WHERE candidate=? AND platform='sdk'", (first,))
        atomic_json(self.root / 'deployment/desired.json', {'release_id': first, 'sequence': 1})
        self.assertEqual(select(self.root, self.controller.ledger)['active'], first)
        self.assertEqual(select(self.root, self.controller.ledger, minutes=True)['active'], second)
        self.assertEqual(self.controller.ledger.target(first, 'android')['state'], 'blocked')

    def test_separate_qualification_failure_does_not_change_publication_state(self):
        from release_control import request, consume, qualifications
        queued = request(self.root, 'qualify', self.manifest['release_id'], 'android')
        before = self.controller.ledger.target(self.manifest['release_id'], 'android')
        consume(self.controller)
        with patch.object(self.controller, 'execute', side_effect=ValueError('original GUI failure')):
            qualifications(self.controller)
        result = json.loads((self.root / 'control/qualification-results' / (queued['request_id'] + '.json')).read_text())
        self.assertEqual(result['state'], 'failed')
        self.assertEqual(self.controller.ledger.target(self.manifest['release_id'], 'android'), before)
