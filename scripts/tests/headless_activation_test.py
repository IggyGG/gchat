"""An opted-in hub activates installed bytes once, without recovery restarts."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import threading
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
        self.maintenance = self.enterContext(patch.object(helper, 'Maintenance'))
        self.lease = self.maintenance.return_value
        self.lease.record.return_value = {'view': 'd' * 32, 'instance': 'e' * 64, 'endpoint': '/owner/gcd.chat'}
        self.lease.prepare.return_value = {'state': 'ready', 'process_id': self.before['pid']}
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
        self.lease.prepare.assert_called_once()
        self.lease.release.assert_called_once()

    def test_attached_view_or_active_work_defers_restart_without_spending_activation(self):
        self.lease.prepare.side_effect = [
            {'state': 'busy', 'reason': 'Another GChat window is attached.'},
            {'state': 'ready', 'process_id': self.before['pid']},
        ]
        self.process.side_effect = [self.before, self.before, self.before, self.before, self.after, self.after]
        self.assertEqual(self.activate()['state'], 'deferred')
        self.assertNotIn('restart_requested_at', json.loads(self.marker.read_text()))
        self.assertEqual([call.args[:2] for call in self.action.call_args_list], [('start', helper.BACKUP)])
        self.assertEqual(self.activate()['state'], 'activated')
        self.assertEqual(sum(call.args[0] == 'try-restart' for call in self.action.call_args_list), 1)

    def test_transient_new_process_permission_does_not_fail_completed_restart(self):
        self.process.side_effect = [self.before, self.before, PermissionError('proc transition'),
                                    self.after, self.after]
        result = self.activate()
        self.assertEqual(result['state'], 'activated')
        self.assertEqual(result['after'], self.after)
        self.assertEqual(sum(call.args[0] == 'try-restart' for call in self.action.call_args_list), 1)
        self.assertEqual(json.loads(self.marker.read_text()), result)

    def test_persistent_unreadable_process_times_out_without_restarting_again(self):
        self.process.side_effect = [self.before, self.before, PermissionError('still private')]
        with patch.object(helper.time, 'monotonic', side_effect=[0, 1, 31]):
            result = self.activate()
        self.assertEqual(result['state'], 'failed')
        self.assertIn('did not remain active', result['reason'])
        self.assertIn('restart_requested_at', result)
        self.process.side_effect = None
        self.assertEqual(self.activate()['state'], 'suppressed')
        self.assertEqual(sum(call.args[0] == 'try-restart' for call in self.action.call_args_list), 1)

    def test_lost_prepare_response_is_not_a_restart_permission(self):
        self.lease.prepare.side_effect = OSError('interrupted')
        self.assertEqual(self.activate()['state'], 'failed')
        self.assertEqual(self.activate()['state'], 'suppressed')
        self.action.assert_called_once_with('start', helper.BACKUP, 180)
        self.assertGreaterEqual(self.lease.release.call_count, 1)

    def test_suppressed_attempt_releases_its_own_lease_without_restarting(self):
        self.state.mkdir()
        receipt = {'state': 'intent', 'before': self.before, 'maintenance': self.lease.record.return_value}
        self.marker.write_text(json.dumps(receipt))
        self.assertEqual(self.activate()['state'], 'suppressed')
        self.lease.release.assert_called_once()
        self.lease.prepare.assert_not_called()
        self.action.assert_not_called()

    def test_deferred_record_with_restart_intent_remains_suppressed(self):
        self.state.mkdir()
        self.marker.write_text(json.dumps({'state': 'deferred', 'restart_requested_at': 1}))
        self.assertEqual(self.activate()['state'], 'suppressed')
        self.action.assert_not_called()

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

    def test_unreadable_observation_breaks_the_stable_process_sequence(self):
        package = {'path': '/usr/bin/gchat', 'sha256': 'new'}
        new = {**package, 'pid': 2}
        with patch.object(helper, 'process', side_effect=[new, PermissionError('proc transition'), new, new]) as process, \
             patch.object(helper.time, 'sleep'):
            self.assertEqual(helper.wait_running(package, 1), new)
        self.assertEqual(process.call_count, 4)


@unittest.skipUnless(sys.platform == 'linux', 'Linux kernel-owned maintenance socket')
class MaintenanceBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.endpoint = self.root / 'chat'
        self.lease = helper.Maintenance.__new__(helper.Maintenance)
        self.lease.before = {'pid': os.getpid()}
        self.lease.instance = 'e' * 64
        self.lease.endpoint = self.endpoint
        self.received = []

    def serve(self, response):
        listener = socket.socket(socket.AF_UNIX)
        listener.settimeout(2)
        listener.bind(str(self.endpoint)); listener.listen(1)
        self.addCleanup(listener.close)
        def receive(connection, count):
            data = b''
            while len(data) < count:
                piece = connection.recv(count - len(data))
                if not piece: return data
                data += piece
            return data
        def worker():
            with listener.accept()[0] as connection:
                connection.settimeout(2)
                header = receive(connection, 4)
                if not header: return
                count = struct.unpack('!I', header)[0]
                self.received.append(json.loads(receive(connection, count)))
                try:
                    for byte in response:
                        connection.sendall(bytes([byte]))
                except (BrokenPipeError, ConnectionResetError):
                    pass
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 3)

    def frame(self, **changes):
        value = {'version': 3, 'instance_id': self.lease.instance,
                 'response': {'kind': 'instance', 'instance': {'id': self.lease.instance}}}
        value.update(changes)
        raw = json.dumps(value).encode()
        return struct.pack('!I', len(raw)) + raw

    def test_fragmented_owned_reply_is_bound_to_the_selected_instance(self):
        self.serve(self.frame())
        self.assertEqual(self.lease.exchange({'kind': 'identify'})['kind'], 'instance')
        self.assertEqual(self.received[0]['instance_id'], self.lease.instance)

    def test_wrong_kernel_process_receives_no_request(self):
        self.lease.before['pid'] += 1
        self.serve(self.frame())
        with self.assertRaisesRegex(ValueError, 'process owner'):
            self.lease.exchange({'kind': 'identify'})
        self.assertEqual(self.received, [])

    def test_changed_instance_is_not_readiness(self):
        self.serve(self.frame(instance_id='f' * 64))
        with self.assertRaisesRegex(ValueError, 'changed instance'):
            self.lease.exchange({'kind': 'identify'})

    def test_noninteger_api_version_is_not_an_identification(self):
        self.serve(self.frame(version=3.0))
        with self.assertRaisesRegex(ValueError, 'API'):
            self.lease.exchange({'kind': 'identify'})

    def test_oversized_frame_is_refused_before_body_allocation(self):
        self.serve(struct.pack('!I', helper.MAX_FRAME + 1))
        with self.assertRaisesRegex(ValueError, 'frame bound'):
            self.lease.exchange({'kind': 'identify'})

    def test_truncated_frame_is_not_a_successful_reply(self):
        self.serve(struct.pack('!I', 100) + b'{}')
        with self.assertRaisesRegex(ValueError, 'interrupted'):
            self.lease.exchange({'kind': 'identify'})

    def test_registration_rejects_duplicate_fields_size_and_shared_access(self):
        path = self.root / 'host.json'
        for body, mode, error in [
            (b'{"version":1,"version":1}', 0o600, 'duplicate'),
            (b' ' * 32769, 0o600, 'size limit'),
            (b'{}', 0o644, 'owner-private'),
        ]:
            with self.subTest(error=error):
                path.write_bytes(body); path.chmod(mode)
                with self.assertRaisesRegex(ValueError, error): helper.private_json(path)

    def test_native_paths_are_lossless_and_traversal_is_refused(self):
        self.assertEqual(os.fsencode(helper.local_path({'unix': list(b'/private/\xff')})), b'/private/\xff')
        for value in ('relative', '/private/../other', '/private/\0', {'unix': [47, True]}, {'unix': [47, 0]}):
            with self.subTest(value=value), self.assertRaises(ValueError): helper.local_path(value)

    def test_deeply_nested_json_is_a_bounded_validation_error(self):
        with self.assertRaisesRegex(ValueError, 'nesting'):
            helper.decode_json('[' * 2000 + '0' + ']' * 2000)


if __name__ == '__main__':
    unittest.main()
