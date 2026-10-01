from contextlib import closing
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_automation_test import candidate
from release_ledger import Ledger
from release_pair import canonical, ios_build_number, next_ios_build_number, validate
from release_prepare import prepare


class IosVersionTests(unittest.TestCase):
    def test_allocation_carries_and_advances_past_original_failed_reservations(self):
        for previous, expected in [
                ('1.0.98', '1.0.99'), ('1.0.99', '1.1.0'),
                ('1.0.100', '1.1.0'), ('1.0.123', '1.1.0'),
                ('1.99.99', '2.0.0'), ('1.100.0', '2.0.0'),
                ('9999.99.98', '9999.99.99')]:
            with self.subTest(previous=previous):
                current = next_ios_build_number(previous)
                self.assertEqual(current, expected)
                self.assertEqual(ios_build_number(current), current)
                self.assertGreater(tuple(map(int, current.split('.'))),
                                   tuple(map(int, previous.split('.'))))
        for previous in ('9999.99.99', '9999.100.0', '10000.0.0'):
            with self.subTest(exhausted=previous), self.assertRaisesRegex(ValueError, 'exhausted'):
                next_ios_build_number(previous)

    def test_invalid_number_fails_before_preparation_or_partial_reservation(self):
        with tempfile.TemporaryDirectory() as directory, closing(Ledger(Path(directory) / 'db')) as ledger:
            first = ledger.add(candidate())
            for number in ('1.0.100', '1.100.0', '10000.0.0', '0.1.1',
                           '1.01.1', '1.0.1b1', True):
                with self.subTest(number=number):
                    value = candidate(2)
                    value['versions']['ios'] = number
                    value['release_id'] = hashlib.sha256(canonical(
                        {k: v for k, v in value.items() if k != 'release_id'})).hexdigest()
                    with self.assertRaises(ValueError):
                        validate(value)
                    with self.assertRaises(ValueError):
                        ledger.add(value)
                    with self.assertRaises(ValueError):
                        prepare(Path(directory) / 'missing-git', 'a' * 40, 'b' * 40,
                                value['versions'], 'refs/heads/release/gchat-' + 'a' * 20)
                    self.assertEqual(ledger.manifest(first), candidate())
                    self.assertEqual(len(ledger.status()['candidates']), 1)
            ledger.add(candidate(2))

    def test_repeated_valid_allocations_are_monotonic_and_unique(self):
        current = '1.99.80'
        seen = {current}
        for _ in range(220):
            following = next_ios_build_number(current)
            self.assertNotIn(following, seen)
            self.assertGreater(tuple(map(int, following.split('.'))),
                               tuple(map(int, current.split('.'))))
            seen.add(following)
            current = following
