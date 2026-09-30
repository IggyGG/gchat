"""Missing identities, observations, timings or cleanup cannot qualify capacity."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location(
    'hosted_capacity', Path(__file__).resolve().parents[1] / 'hosted-capacity.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CapacityEvidenceTest(unittest.TestCase):
    def test_slow_membership_replay_requires_progress_even_in_small_rooms(self):
        self.assertTrue(module.membership_replay_passes(9000, [], 300))
        self.assertTrue(module.membership_replay_passes(16590, [0, 11, 12], 300))
        self.assertFalse(module.membership_replay_passes(16590, [0], 300))
        self.assertFalse(module.membership_replay_passes(10000.4, [], 300))
        self.assertFalse(module.membership_replay_passes(300000.4, [32], 300))

    def test_rounding_does_not_relax_the_feedback_deadline(self):
        journey = object.__new__(module.Capacity)
        journey.note = Mock()
        with patch.object(module.time, 'monotonic', return_value=0.2004):
            journey.timed('feedback', 0, 200)
        journey.note.assert_called_once_with('feedback', duration_ms=200,
                                            target_ms=200, within_target=False)
        journey.note.reset_mock()
        with patch.object(module.time, 'monotonic', return_value=10.0004):
            journey.timed('ordinary offline recovery', 0, 10000)
        journey.note.assert_called_once_with('ordinary offline recovery', duration_ms=10000,
                                            target_ms=10000, within_target=False)

    def test_duplicate_identity_or_missing_self_is_not_a_roster(self):
        room = {'active': True, 'members': [{'id': 'a', 'isSelf': True}, {'id': 'b'}]}
        self.assertTrue(module.verify_roster(room, 2))
        room['members'][1]['id'] = 'a'
        self.assertFalse(module.verify_roster(room, 2))
        room['members'][1]['id'] = 'b'
        room['members'][0]['isSelf'] = False
        self.assertFalse(module.verify_roster(room, 2))

    def test_smoke_and_missing_or_failed_observations_never_qualify_500(self):
        report = {'requested_members': 500, 'passed': True, 'latency_passed': True,
                  'recovery_policy': module.RECOVERY_POLICY,
                  'cleanup_passed': True, 'resources_complete': True,
                  'peak_active_profiles': 500, 'observations': {
                      'independent_members': 500, 'baseline': {'senders': 10, 'recipients_per_sender': 499},
                      'mixed_file': {'senders': 10, 'recipients_per_sender': 499},
                      'membership_catchup': True, 'offline_recovery': True, 'verified_file_resume': True,
                      'churn_and_exclusion': True}}
        self.assertTrue(module.qualifies(report))
        for key in report:
            missing = copy.deepcopy(report)
            del missing[key]
            self.assertFalse(module.qualifies(missing), key)
        for key in report['observations']:
            missing = copy.deepcopy(report)
            del missing['observations'][key]
            self.assertFalse(module.qualifies(missing), key)
        for key in ('passed', 'latency_passed', 'cleanup_passed', 'resources_complete'):
            failed = copy.deepcopy(report)
            failed[key] = False
            self.assertFalse(module.qualifies(failed), key)
        report['requested_members'] = 12
        self.assertFalse(module.qualifies(report))


if __name__ == '__main__':
    unittest.main()
