"""An opted-in hub activates installed bytes once, without recovery restarts."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('headless_activate', ROOT / 'release/automation/headless-activate.py')
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


@unittest.skipUnless(sys.platform == 'linux', 'Linux systemd activation and file locks')
class ActivationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.state = self.root / 'state'
        self.lock = self.root / 'package.lock'
        self.lock.touch(mode=0o644)
        self.package = {'version': '0.1.173', 'sha256': 'b' * 64, 'path': '/usr/bin/gchat'}
        self.before = {'pid': 100, 'sha256': 'a' * 64, 'path': '/usr/bin/gchat'}
        self.after = {**self.before, 'pid': 200, 'sha256': self.package['sha256']}
        self.marker = self.state / (self.package['sha256'] + '.json')
        self.process = self.enterContext(patch.object(helper, 'process', return_value=self.before))
        self.installed = self.enterContext(patch.object(helper, 'installed', return_value=self.package))
        self.action = self.enterContext(patch.object(helper, 'action'))
        self.enterContext(patch.object(helper.time, 'sleep'))

    def activate(self):
        return helper.activate(self.state, self.lock)

    def test_absent_or_inactive_hub_is_not_started(self):
        self.process.return_value = None
        self.assertEqual(self.activate()['state'], 'skipped')
        self.installed.assert_not_called()
        self.action.assert_not_called()

    def test_same_bytes_do_not_restart_or_create_attempt(self):
        self.process.return_value = self.after
        self.assertEqual(self.activate()['state'], 'current')
        self.action.assert_not_called()
        self.assertFalse(self.marker.exists())

    def test_override_executable_is_not_restarted(self):
        self.process.return_value = {**self.before, 'path': '/opt/private/gchat'}
        self.assertEqual(self.activate()['state'], 'blocked')
        self.action.assert_not_called()
        self.assertFalse(self.marker.exists())

    def test_backup_intent_then_try_restart_and_stable_actual_hash(self):
        self.process.side_effect = [self.before, self.before, self.after, self.after]
        def checked_action(verb, unit, timeout):
            self.assertEqual(json.loads(self.marker.read_text())['state'], 'intent')
        self.action.side_effect = checked_action
        result = self.activate()
        self.assertEqual(result['state'], 'activated')
        self.assertEqual(result['after'], self.after)
        self.assertFalse(result['network_delivery_verified'])
        self.assertEqual([call.args for call in self.action.call_args_list],
                         [('start', helper.BACKUP, 180), ('try-restart', helper.HUB, 90)])
        self.assertEqual(json.loads(self.marker.read_text()), result)

    def test_failed_backup_is_not_followed_by_restart_or_automatic_retry(self):
        self.action.side_effect = subprocess.CalledProcessError(1, ['systemctl'])
        self.assertEqual(self.activate()['state'], 'failed')
        self.assertEqual(self.activate()['state'], 'suppressed')
        self.action.assert_called_once_with('start', helper.BACKUP, 180)

    def test_unknown_restart_outcome_is_not_retried(self):
        self.action.side_effect = [None, subprocess.TimeoutExpired(['systemctl'], 90)]
        self.assertEqual(self.activate()['state'], 'failed')
        self.assertEqual(self.activate()['state'], 'suppressed')
        self.assertEqual(self.action.call_count, 2)

    def test_interrupted_intent_is_not_retried(self):
        self.state.mkdir()
        self.marker.write_text(json.dumps({'state': 'intent'}))
        result = self.activate()
        self.assertEqual((result['state'], result['previous_state']), ('suppressed', 'intent'))
        self.action.assert_not_called()

    def test_package_replaced_during_backup_prevents_restart(self):
        self.installed.side_effect = [self.package, {**self.package, 'sha256': 'c' * 64}]
        self.assertEqual(self.activate()['state'], 'failed')
        self.action.assert_called_once_with('start', helper.BACKUP, 180)

    def test_manually_stopped_or_changed_hub_is_not_restarted(self):
        self.process.side_effect = [self.before, None]
        self.assertEqual(self.activate()['state'], 'failed')
        self.action.assert_called_once_with('start', helper.BACKUP, 180)

    def test_package_replaced_during_activation_is_not_reported_successful(self):
        self.process.side_effect = [self.before, self.before, self.after, self.after]
        self.installed.side_effect = [self.package, self.package, {**self.package, 'sha256': 'c' * 64}]
        self.assertEqual(self.activate()['state'], 'failed')

    def test_wrong_executable_after_restart_fails_and_stays_suppressed(self):
        self.process.side_effect = [self.before, self.before, self.before]
        with patch.object(helper.time, 'monotonic', side_effect=[0, 1, 31]):
            self.assertEqual(self.activate()['state'], 'failed')
        self.process.side_effect = None
        self.assertEqual(self.activate()['state'], 'suppressed')
        self.assertEqual(self.action.call_count, 2)

    def test_missing_updater_lock_defers_without_actions(self):
        self.lock.unlink()
        self.assertEqual(self.activate()['state'], 'deferred')
        self.process.assert_not_called()
        self.action.assert_not_called()

    def test_busy_updater_lock_defers_without_actions(self):
        import fcntl
        with self.lock.open('rb') as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.activate()['state'], 'deferred')
        self.process.assert_not_called()
        self.action.assert_not_called()

    def test_updater_lock_is_opened_read_only(self):
        original = Path.open
        modes = []
        def opened(path, *args, **kwargs):
            if path == self.lock:
                modes.append(args[0])
            return original(path, *args, **kwargs)
        self.process.return_value = None
        with patch.object(Path, 'open', opened):
            self.activate()
        self.assertEqual(modes, ['rb'])


class ExecutableTests(unittest.TestCase):
    def test_unconfigured_package_cannot_activate(self):
        with patch.object(helper, 'capture', return_value='install ok unpacked\n0.1.173'):
            with self.assertRaisesRegex(ValueError, 'fully installed'):
                helper.installed()

    @unittest.skipUnless(sys.platform == 'linux', 'Linux process executable')
    def test_hash_is_read_from_actual_process_inode(self):
        pid = os.getpid()
        result = subprocess.CompletedProcess([], 0, 'LoadState=loaded\nActiveState=active\nMainPID=' + str(pid))
        with patch.object(helper.subprocess, 'run', return_value=result):
            current = helper.process()
        self.assertEqual(current['sha256'], helper.digest('/proc/self/exe'))
        self.assertEqual(current['path'], os.readlink('/proc/self/exe'))

    def test_replaced_process_inode_keeps_managed_path_identity(self):
        result = subprocess.CompletedProcess([], 0, 'LoadState=loaded\nActiveState=active\nMainPID=123')
        with patch.object(helper.subprocess, 'run', return_value=result), \
             patch.object(helper.os, 'readlink', return_value='/usr/bin/gchat (deleted)'), \
             patch.object(helper, 'digest', return_value='old-inode-hash') as digest:
            self.assertEqual(helper.process()['path'], '/usr/bin/gchat')
            digest.assert_called_once_with(Path('/proc/123/exe'))

    def test_missing_systemd_unit_is_not_an_activation_request(self):
        result = subprocess.CompletedProcess([], 1, 'LoadState=not-found\nActiveState=inactive\nMainPID=0')
        with patch.object(helper.subprocess, 'run', return_value=result):
            self.assertIsNone(helper.process())

    def test_new_process_requires_two_identical_observations(self):
        package = {'path': '/usr/bin/gchat', 'sha256': 'new'}
        new = {**package, 'pid': 2}
        observations = [None, {**new, 'sha256': 'wrong'}, new, {**new, 'pid': 3}, new, new]
        with patch.object(helper, 'process', side_effect=observations) as process, \
             patch.object(helper.time, 'sleep'):
            self.assertEqual(helper.wait_running(package, 1), new)
        self.assertEqual(process.call_count, 6)


if __name__ == '__main__':
    unittest.main()
