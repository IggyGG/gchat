"""The Android agent lane cannot block or replace existing release workers."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_android_agent import AndroidAgent


class AndroidLane(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def lane(self, code):
        value = AndroidAgent(self.root, {'command': [sys.executable, '-c', code], 'timeout_seconds': 30})
        self.addCleanup(value.close)
        return value

    def finish(self, lane):
        lane.pending['process'].wait(timeout=5)
        lane.tick()

    def test_disabled_lane_does_not_start_a_process_or_change_existing_workers(self):
        lane = AndroidAgent(self.root)
        with patch('release_android_agent.subprocess.Popen') as spawn:
            lane.tick(); lane.close()
        spawn.assert_not_called()
        self.assertIsNone(lane.progress())
        self.assertFalse((self.root / 'android-agent').exists())

    def test_slow_cluster_observation_is_nonblocking_and_never_overlaps(self):
        lane = self.lane('import time;time.sleep(20)')
        started = time.monotonic()
        lane.tick()
        process = lane.pending['process']
        lane.tick()
        self.assertLess(time.monotonic() - started, 1)
        self.assertIs(lane.pending['process'], process)
        self.assertTrue(lane.progress()['observing'])
        lane.close()
        self.assertIsNotNone(process.poll())

    def test_only_bound_cluster_status_is_exposed(self):
        value = {'schema': 1, 'execution': 'kubernetes', 'state': 'active', 'observed_at': 100,
                 'active': [{'request_id': 'a' * 64, 'state': 'running'}], 'private': 'must remain private'}
        lane = self.lane('print(' + repr(json.dumps(value)) + ')')
        lane.tick();self.finish(lane)
        self.assertEqual(lane.progress()['active'], value['active'])
        self.assertNotIn('private', lane.progress())
        self.assertNotIn('must remain private', (lane.state / 'status.json').read_text())

    def test_failed_or_malformed_observation_is_not_release_success(self):
        for code in ('print("private error");raise SystemExit(1)', 'print("{}")'):
            with self.subTest(code=code):
                lane = self.lane(code)
                lane.tick();self.finish(lane)
                self.assertEqual(lane.progress()['state'], 'observation_failed')
                self.assertNotIn('private error', json.dumps(lane.progress()))

    def test_timeout_stops_only_the_observer_and_records_reconciliation_failure(self):
        lane = self.lane('import time;time.sleep(20)')
        lane.tick();process = lane.pending['process']
        lane.pending['deadline'] = 0
        lane.tick()
        self.assertIsNotNone(process.poll())
        self.assertEqual(lane.progress()['reason'], 'reconciliation_timeout')
        self.assertFalse(lane.progress()['observing'])

    def test_command_and_timeout_require_explicit_bounded_configuration(self):
        for config in ({'command': 'shell command'}, {'command': ['relative']},
                       {'command': [sys.executable], 'timeout_seconds': 301}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                AndroidAgent(self.root, config)


if __name__ == '__main__':
    unittest.main()
