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


class HostedLiveCleanupTest(unittest.TestCase):
    def journey(self):
        journey = object.__new__(module.Journey)
        journey.report = {'passed': False}
        journey.processes = {'alice': object(), 'bob': object()}
        journey.start = Mock(side_effect=RuntimeError('injected journey failure'))
        journey.note = Mock()
        return journey

    def test_failure_still_stops_every_owned_process_and_records_cleanup(self):
        journey = self.journey()
        journey.stop = Mock(side_effect=lambda who: journey.processes.pop(who))
        with self.assertRaisesRegex(RuntimeError, 'injected journey failure'):
            journey.run()
        self.assertTrue(journey.report['cleanup_passed'])
        self.assertEqual(journey.stop.call_count, 2)
        self.assertEqual(journey.report['error'], 'injected journey failure')

    def test_one_cleanup_failure_does_not_skip_the_other_owned_process(self):
        journey = self.journey()
        def stop(who):
            if who == 'alice':
                raise RuntimeError('injected stop failure')
            journey.processes.pop(who)
        journey.stop = Mock(side_effect=stop)
        with self.assertRaisesRegex(RuntimeError, 'owned daemon cleanup failed'):
            journey.run()
        self.assertFalse(journey.report['cleanup_passed'])
        self.assertEqual(journey.stop.call_count, 2)
        self.assertEqual(journey.report['cleanup_errors'], ['alice: injected stop failure'])


if __name__ == '__main__':
    unittest.main()
