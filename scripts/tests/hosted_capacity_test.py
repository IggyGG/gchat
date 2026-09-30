"""Missing identities, observations, timings or cleanup cannot qualify capacity."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'hosted_capacity', Path(__file__).resolve().parents[1] / 'hosted-capacity.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CapacityEvidenceTest(unittest.TestCase):
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
                  'cleanup_passed': True, 'observations': {
                      'independent_members': 500, 'baseline': {'senders': 10, 'recipients_per_sender': 499},
                      'mixed_file': {'senders': 10, 'recipients_per_sender': 499},
                      'offline_recovery': True, 'verified_file_resume': True,
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
        for key in ('passed', 'latency_passed', 'cleanup_passed'):
            failed = copy.deepcopy(report)
            failed[key] = False
            self.assertFalse(module.qualifies(failed), key)
        report['requested_members'] = 12
        self.assertFalse(module.qualifies(report))


if __name__ == '__main__':
    unittest.main()
