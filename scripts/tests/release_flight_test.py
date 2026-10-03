import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_coordinator import Coordinator, atomic_json
from release_automation_test import candidate
from release_flight import select, can_build


class FlightTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.controller = Coordinator(self.root, {'single_flight': True})
        self.addCleanup(self.controller.ledger.close)
        self.releases = [self.controller.ledger.add(candidate(i)) for i in (1, 2, 3)]
        atomic_json(self.root / 'deployment/desired.json', {'release_id': self.releases[0], 'sequence': 1})

    def test_selected_launch_stays_active_and_latest_pending_is_combined(self):
        flight = select(self.root, self.controller.ledger)
        self.assertEqual(flight['active'], self.releases[0])
        self.assertEqual(flight['pending'], self.releases[2])
        self.assertTrue(can_build(self.controller, self.releases[0], 'ios'))
        self.assertFalse(can_build(self.controller, self.releases[2], 'ios'))

    def test_blocked_active_release_does_not_admit_a_new_release(self):
        self.controller.ledger.transition(self.releases[0], 'ios', 'blocked', reason='retained failed fixture')
        self.assertEqual(select(self.root, self.controller.ledger)['active'], self.releases[0])
        self.assertFalse(can_build(self.controller, self.releases[1], 'linux-x86_64'))

    def test_reserved_effect_without_dispatch_cannot_bypass_admission(self):
        self.controller.ledger.effect(self.releases[2], 'ios', 'build')
        self.assertFalse(can_build(self.controller, self.releases[2], 'ios'))

    def test_unknown_dispatch_retains_its_original_request_for_reconciliation(self):
        effect = self.controller.ledger.effect(self.releases[1], 'ios', 'build')
        atomic_json(self.root / 'jobs' / effect['id'] / 'attempted.json', {'request_id': effect['id']})
        self.assertTrue(can_build(self.controller, self.releases[1], 'ios'))
        self.assertEqual(self.controller.ledger.effect(self.releases[1], 'ios', 'build')['id'], effect['id'])

    def test_store_reviews_do_not_hold_the_next_internal_release(self):
        # These owned ledger fixtures model completed upstream gates. No actual
        # application or provider receipt is manufactured by the scheduler.
        for item in self.controller.ledger.db.execute('SELECT platform FROM platforms WHERE candidate=?',
                                                     (self.releases[0],)).fetchall():
            state = 'in_review' if item['platform'] == 'ios' else 'processing' if item['platform'] == 'android' else 'available'
            self.controller.ledger.db.execute('UPDATE platforms SET state=? WHERE candidate=? AND platform=?',
                                              (state, self.releases[0], item['platform']))
        self.assertEqual(select(self.root, self.controller.ledger)['active'], self.releases[2])
        self.assertTrue(can_build(self.controller, self.releases[2], 'ios'))

    def test_unknown_saved_flight_is_rejected(self):
        atomic_json(self.root / 'release-flight.json', {'schema': 1, 'active': 'f' * 64, 'pending': None})
        with self.assertRaisesRegex(ValueError, 'unknown candidate'):
            select(self.root, self.controller.ledger)

    def test_completed_newest_release_never_selects_an_older_pending_candidate(self):
        atomic_json(self.root / 'release-flight.json', {'schema': 1, 'active': self.releases[2], 'pending': None})
        self.controller.ledger.db.execute('UPDATE platforms SET state=? WHERE candidate=?',
                                          ('available', self.releases[2]))
        self.assertEqual(select(self.root, self.controller.ledger),
                         {'schema': 1, 'active': self.releases[2], 'pending': None})

    def test_later_ready_artifact_cannot_advance_an_incomplete_active_flight(self):
        from unittest.mock import patch
        import hashlib
        from release_pair import canonical
        inventory = self.root / 'inventory.json';atomic_json(inventory, {'targets': []})
        controller = Coordinator(self.root / 'deployment-fixture',
                                 {'single_flight': True, 'deployment_file': str(inventory)})
        self.addCleanup(controller.ledger.close)
        releases = []
        for number in (1, 2):
            manifest = candidate(number);manifest['policy']['deployment_required'] = True
            manifest['release_id'] = hashlib.sha256(canonical({k:v for k,v in manifest.items() if k!='release_id'})).hexdigest()
            release = controller.ledger.add(manifest);releases.append(release)
            for state in ('building', 'verifying', 'verified'):
                controller.ledger.transition(release, 'linux-x86_64', state, evidence='a'*64)
        atomic_json(controller.state / 'deployment/desired.json', {'release_id': releases[0], 'sequence': 1})
        with patch('release_deployment.reconcile') as reconcile:
            controller.reconcile_deployment()
        self.assertEqual(reconcile.call_args.args[1]['release_id'], releases[0])

    def test_invalid_flight_configuration_creates_no_state(self):
        path = self.root / 'unused'
        with self.assertRaisesRegex(ValueError, 'boolean'):
            Coordinator(path, {'single_flight': 'true'})
        self.assertFalse(path.exists())
