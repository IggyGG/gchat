"""A late successful IPC probe must not turn a fixed deadline into a pass."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location(
    'hosted_live', Path(__file__).resolve().parents[1] / 'hosted-live.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HostedLiveDeadlineTest(unittest.TestCase):
    def test_late_success_is_a_timeout_without_a_pass_observation(self):
        journey = object.__new__(module.Journey)
        journey.note = Mock()
        with patch.object(module.time, 'monotonic', side_effect=[0, 0, 1.1]):
            with self.assertRaisesRegex(TimeoutError, 'after its deadline'):
                journey.wait('recipient', lambda: True, timeout=1)
        journey.note.assert_not_called()

    def test_timely_success_keeps_its_actual_observation(self):
        journey = object.__new__(module.Journey)
        journey.note = Mock()
        with patch.object(module.time, 'monotonic', side_effect=[0, 0, 0.4]):
            self.assertEqual(journey.wait('recipient', lambda: 'received', timeout=1), 'received')
        journey.note.assert_called_once_with('recipient', duration_ms=400)


if __name__ == '__main__':
    unittest.main()
