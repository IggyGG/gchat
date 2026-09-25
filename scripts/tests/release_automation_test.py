import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_pair import canonical, validate
from release_ledger import Ledger, PLATFORMS


def candidate(number=1):
    value = {'schema': 1, 'sources': {
        'gchat': {'commit': f'{number:040x}', 'tree': 'a' * 40},
        'gcoms': {'commit': 'b' * 40, 'tree': 'c' * 40}},
        'versions': {p: str(number) if p == 'android' else f'1.0.{number}' for p in PLATFORMS},
        'policy': {'channel': 'production', 'profile': 46}}
    value['release_id'] = hashlib.sha256(canonical(value)).hexdigest()
    return value


class ReleaseLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'ledger.db'
        self.ledger = Ledger(self.path)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(lambda: self.ledger.close())
        self.first = self.ledger.add(candidate())

    def verified(self, release, platform):
        for state in ('building', 'verifying', 'verified'):
            self.ledger.transition(release, platform, state, evidence='f' * 64)

    def test_duplicate_candidate_survives_restart(self):
        self.ledger.close()
        self.ledger = Ledger(self.path)
        self.assertEqual(self.ledger.add(candidate()), self.first)
        self.assertEqual(len(self.ledger.status()['candidates']), 1)

    def test_partial_version_reservation_is_atomic(self):
        item = candidate(2)
        item['versions']['ios'] = '1.0.1'
        item['release_id'] = hashlib.sha256(canonical({k: v for k, v in item.items()
                                                     if k != 'release_id'})).hexdigest()
        with self.assertRaises(ValueError):
            self.ledger.add(item)
        self.assertEqual(len(self.ledger.status()['candidates']), 1)
        self.ledger.add(candidate(2))

    def test_cannot_jump_checks_or_relabel_failure(self):
        with self.assertRaises(ValueError):
            self.ledger.transition(self.first, 'android', 'available', evidence='f' * 64)
        self.ledger.transition(self.first, 'android', 'building')
        self.ledger.transition(self.first, 'android', 'failed', reason='emulator failed')
        with self.assertRaises(ValueError):
            self.ledger.transition(self.first, 'android', 'verified', evidence='f' * 64)

    def test_ambiguous_dispatch_is_retained_across_restart(self):
        request = self.ledger.effect(self.first, 'ios', 'build')
        self.ledger.close()
        self.ledger = Ledger(self.path)
        self.assertEqual(request, self.ledger.effect(self.first, 'ios', 'build'))
        self.ledger.complete_effect(request['id'], 'run-123', 'f' * 64)
        with self.assertRaises(ValueError):
            self.ledger.complete_effect(request['id'], 'run-456', 'e' * 64)

    def test_one_store_review_does_not_block_other_platforms(self):
        second = self.ledger.add(candidate(2))
        self.verified(self.first, 'ios')
        self.ledger.transition(self.first, 'ios', 'submitting')
        self.ledger.transition(self.first, 'ios', 'in_review')
        self.verified(second, 'ios')
        with self.assertRaises(ValueError):
            self.ledger.transition(second, 'ios', 'submitting')
        self.verified(second, 'android')
        self.ledger.transition(second, 'android', 'submitting')
        self.ledger.transition(second, 'android', 'available', evidence='e' * 64)

    def test_blocked_review_retains_ownership_and_stage(self):
        second = self.ledger.add(candidate(2))
        self.verified(self.first, 'ios')
        self.ledger.transition(self.first, 'ios', 'submitting')
        self.ledger.transition(self.first, 'ios', 'blocked', reason='waiting for provider reconciliation')
        with self.assertRaises(ValueError):
            self.ledger.transition(self.first, 'ios', 'verified', evidence='f' * 64)
        self.verified(second, 'ios')
        with self.assertRaises(ValueError):
            self.ledger.transition(second, 'ios', 'submitting')
        self.ledger.transition(self.first, 'ios', 'submitting')

    def test_late_older_build_cannot_regress_latest(self):
        second = self.ledger.add(candidate(2))
        for release in (second, self.first):
            self.verified(release, 'linux-x86_64')
            self.ledger.transition(release, 'linux-x86_64', 'publishing')
            self.ledger.transition(release, 'linux-x86_64', 'available', evidence='f' * 64)
        self.assertEqual(self.ledger.status()['available']['linux-x86_64'], second)

    def test_manifest_tampering_is_rejected(self):
        item = candidate()
        item['sources']['gcoms']['commit'] = 'd' * 40
        with self.assertRaises(ValueError):
            validate(item)

    def test_success_needs_evidence(self):
        self.ledger.transition(self.first, 'sdk', 'building')
        self.ledger.transition(self.first, 'sdk', 'verifying')
        with self.assertRaises(ValueError):
            self.ledger.transition(self.first, 'sdk', 'verified')


if __name__ == '__main__':
    unittest.main()

class CoalescingTests(unittest.TestCase):
    def test_new_sources_skip_only_unstarted_targets(self):
        with tempfile.TemporaryDirectory() as root:
            ledger=Ledger(Path(root)/'db')
            try:
                first=ledger.add(candidate());ledger.transition(first,'android','building')
                latest=ledger.add(candidate(2));ledger.coalesce()
                self.assertEqual(ledger.target(first,'android')['state'],'building')
                self.assertEqual(ledger.target(first,'ios')['state'],'superseded')
                self.assertEqual(ledger.target(latest,'android')['state'],'queued')
            finally:ledger.close()
