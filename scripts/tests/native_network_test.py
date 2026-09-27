"""Deadline rejection controls for the real packaged network fixture."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('native_network', ROOT / 'test-native-network.py')
network = importlib.util.module_from_spec(spec)
spec.loader.exec_module(network)

class DeadlineTests(unittest.TestCase):
    def setUp(self):
        self.journey = network.Journey.__new__(network.Journey)
        self.journey.deadline = 100

    def test_late_success_cannot_reset_stage_budget(self):
        with patch.object(network.time, 'monotonic', side_effect=[0, 1, 11]):
            with self.assertRaisesRegex(ValueError, 'after original stage deadline'):
                self.journey.until(lambda: True, 10)

    def test_global_deadline_caps_a_larger_stage_budget(self):
        with patch.object(network.time, 'monotonic', side_effect=[90, 99, 101]):
            with self.assertRaisesRegex(ValueError, 'after original stage deadline'):
                self.journey.until(lambda: True, 120)

    def test_success_within_original_budget_is_returned(self):
        with patch.object(network.time, 'monotonic', side_effect=[0, 1, 9]):
            self.assertEqual(self.journey.until(lambda: 'observed', 10), 'observed')

    def test_exhausted_global_budget_refuses_new_request(self):
        with patch.object(network.time, 'monotonic', return_value=100):
            with self.assertRaisesRegex(ValueError, 'original 600-second'):
                self.journey.timeout()

if __name__ == '__main__':
    unittest.main()
