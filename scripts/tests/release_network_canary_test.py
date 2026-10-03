import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_network_canary as canary


class NetworkCanaryTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {'policy': {'file_qualification': {'bytes': 16777216,
            'completion_seconds': 360, 'total_seconds': 600}}}
        self.report = {'passed': True, 'inputs_unchanged': True, 'binary_unchanged': True,
            'children_stopped': True, 'temporary_profile_removed': True, 'elapsed_seconds': 150,
            'events': [{'event': 'authenticated_ack', 'sender': sender} for _ in range(3) for sender in (0, 1)],
            'file_check': {'bytes': 16777216, 'completion_elapsed_seconds': 100,
                'abrupt_stop': True, 'verified_pieces_retained': True, 'hash_verified_after_reopen': True}}

    def test_only_complete_covered_ack_recovery_and_cleanup_can_pass(self):
        canary.verify_journey(self.report, self.manifest)
        for field in ('passed', 'inputs_unchanged', 'binary_unchanged', 'children_stopped', 'temporary_profile_removed'):
            proof = {**self.report, field: False}
            with self.subTest(field=field), self.assertRaises(ValueError):
                canary.verify_journey(proof, self.manifest)
        for field, value in (('events', self.report['events'][:2]), ('elapsed_seconds', 601),
                             ('elapsed_seconds', float('nan')), ('elapsed_seconds', 0)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                canary.verify_journey({**self.report, field: value}, self.manifest)

    def test_smaller_files_late_completion_and_missing_resume_proof_fail(self):
        for field, value in (('bytes', 4194304), ('completion_elapsed_seconds', 361),
                ('abrupt_stop', False), ('verified_pieces_retained', False), ('hash_verified_after_reopen', False)):
            proof = copy.deepcopy(self.report); proof['file_check'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): canary.verify_journey(proof, self.manifest)

    def test_short_canary_never_qualifies_full_file_recovery(self):
        proof = {**self.report, 'mode': 'chat'}
        canary.verify_chat(proof)
        with self.assertRaises(ValueError):
            canary.verify_journey(proof, self.manifest)
        for field, value in [('mode', 'full'), ('events', proof['events'][:1]),
                             ('elapsed_seconds', 301), ('elapsed_seconds', float('nan')),
                             ('children_stopped', False), ('temporary_profile_removed', False)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                canary.verify_chat({**proof, field: value})


if __name__ == '__main__': unittest.main()
