import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_host_install as install


@unittest.skipUnless(os.name == 'posix', 'systemd worker uses POSIX locks')
class HostInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old = self.root / 'old'; self.old.write_bytes(b'old qualified binary')
        self.unit = self.root / 'original-unit'; self.unit.write_text('original unit')
        self.key = self.root / 'identity'; self.key.write_bytes(b'retained identity fixture')
        self.sha = hashlib.sha256(b'new qualified binary').hexdigest()
        (self.root / ('gchat-release-' + self.sha)).write_bytes(b'new qualified binary')
        self.args = [str(self.old), 'serve', '--keystore', str(self.key)]
        self.pid = 100
        self.paths = dict(state_root=self.root / 'state', binary_root=self.root / 'binaries',
                          unit_root=self.root / 'units', upload_root=self.root)
        self.paths['unit_root'].mkdir()
        self.request = dict(unit='ghost-relay.service', release_id='a' * 64,
                            sha256=self.sha, binary_name='gcnode')
        self.addCleanup(patch.stopall)
        patch.object(install, 'show', side_effect=self.show).start()
        patch.object(install, 'arguments', side_effect=lambda _: list(self.args)).start()
        patch.object(install, 'observe', side_effect=self.observe).start()
        patch.object(install.subprocess, 'run', side_effect=self.command).start()
        patch.object(install.time, 'sleep').start()

    def show(self, unit, field):
        dropins = sorted((self.paths['unit_root'] / (unit + '.d')).glob('*.conf'))
        return {'NeedDaemonReload': 'no', 'FragmentPath': str(self.unit), 'DropInPaths': ' '.join(map(str, dropins)),
                'MemoryMax': '1073741824', 'TasksMax': '256', 'LimitNOFILE': '8192'}[field]

    def observe(self, _):
        return {'healthy': True, 'running': {'sha256': install.digest(self.args[0]),
                'executable': str(Path(self.args[0]).resolve()), 'process_id': self.pid}}

    def command(self, argv, **kwargs):
        if argv[:2] == ['systemctl', 'restart']:
            self.pid += 1
            drops = sorted((self.paths['unit_root'] / 'ghost-relay.service.d').glob('*.conf'))
            if drops:
                import shlex
                commands = [drop.read_text().split('ExecStart=')[-1].strip()
                            for drop in drops if 'ExecStart=' in drop.read_text()]
                if commands: self.args = shlex.split(commands[-1])
            else:
                self.args[0] = str(self.old)

    def run_stage(self, stage):
        return install.run({**self.request, 'stage': stage}, **self.paths)

    def test_activation_preserves_arguments_identity_and_rolls_back(self):
        self.run_stage('prepare'); self.run_stage('activate')
        self.assertEqual(install.digest(self.args[0]), self.sha)
        self.assertEqual(self.args[1:], ['serve', '--keystore', str(self.key)])
        self.assertEqual(self.key.read_bytes(), b'retained identity fixture')
        self.run_stage('rollback')
        self.assertEqual(self.args[0], str(self.old))
        self.assertEqual(self.unit.read_text(), 'original unit')

    def test_lost_activation_reply_is_reconciled_without_second_restart(self):
        self.run_stage('prepare'); self.run_stage('activate'); pid = self.pid
        self.run_stage('activate')
        self.assertEqual(self.pid, pid)

    def test_private_worker_umask_allows_service_traversal_without_exposing_state(self):
        previous = os.umask(0o077)
        try:
            self.run_stage('prepare')
            binary = self.paths['binary_root'] / self.sha / 'gcnode'
            for path in (self.paths['binary_root'], binary.parent, binary):
                self.assertEqual(path.stat().st_mode & 0o777, 0o755)
            state = self.paths['state_root'] / self.request['unit']
            self.assertEqual(state.stat().st_mode & 0o777, 0o700)
            self.assertEqual((state / self.request['release_id'] / 'before.json').stat().st_mode & 0o777, 0o600)
            self.paths['binary_root'].chmod(0o700)
            binary.parent.chmod(0o700)
            self.run_stage('prepare')
            self.assertEqual(self.paths['binary_root'].stat().st_mode & 0o777, 0o755)
            self.assertEqual(binary.parent.stat().st_mode & 0o777, 0o755)
            self.run_stage('activate')
            self.run_stage('rollback')
        finally:
            os.umask(previous)

    def test_symlinked_binary_directory_is_rejected_before_installation(self):
        outside = self.root / 'outside'
        outside.mkdir()
        self.paths['binary_root'].symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'directory cannot be a symlink'):
            self.run_stage('prepare')
        self.assertEqual(list(outside.iterdir()), [])

    def test_changed_key_blocks_activation_without_mutation(self):
        self.run_stage('prepare'); self.key.write_bytes(b'changed by another owner')
        with self.assertRaisesRegex(ValueError, 'protected'):
            self.run_stage('activate')
        self.assertEqual(self.args[0], str(self.old))

    def test_tampered_upload_and_missing_rollback_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no retained preparation'):
            self.run_stage('activate')
        (self.root / ('gchat-release-' + self.sha)).write_bytes(b'bad upload')
        with self.assertRaisesRegex(ValueError, 'uploaded artifact'):
            self.run_stage('prepare')

    def test_another_operator_artifact_is_not_overwritten(self):
        self.run_stage('prepare')
        other = self.root / 'other'; other.write_bytes(b'another qualified release')
        self.args[0] = str(other)
        with self.assertRaisesRegex(ValueError, 'another operator'):
            self.run_stage('activate')

    def test_rollback_preserves_another_operators_running_artifact_and_dropin(self):
        self.run_stage('prepare'); self.run_stage('activate')
        other = self.root / 'other'; other.write_bytes(b'another qualified release')
        self.args[0] = str(other)
        drop = self.paths['unit_root'] / 'ghost-relay.service.d/99z-gchat-release.conf'
        retained = drop.read_bytes()
        pid, calls, arguments = self.pid, install.subprocess.run.call_count, list(self.args)
        with self.assertRaisesRegex(ValueError, 'another operator'):
            self.run_stage('rollback')
        self.assertEqual(drop.read_bytes(), retained)
        self.assertEqual(self.args, arguments)
        self.assertEqual(self.pid, pid)
        self.assertEqual(install.subprocess.run.call_count, calls)

    def test_interrupted_rollback_accepts_the_recorded_previous_artifact(self):
        self.run_stage('prepare'); self.run_stage('activate'); self.run_stage('rollback')
        self.run_stage('rollback')
        self.assertEqual(self.args[0], str(self.old))

    def takeover(self):
        import shlex
        drop = self.paths['unit_root'] / 'ghost-relay.service.d/zz-capacity-port.conf'
        drop.parent.mkdir(exist_ok=True)
        drop.write_text('[Service]\nExecStart=\nExecStart=' + shlex.join(self.args) + '\n')
        drop.chmod(0o640)
        self.request['takeover'] = {'release_id': self.request['release_id'],
            'running_sha256': install.digest(self.args[0]),
            'dropins': [{'path': str(drop), 'sha256': install.digest(drop)}]}
        return drop

    def test_bound_takeover_retires_only_authorized_override_and_restores_it(self):
        drop = self.takeover(); original = drop.read_bytes()
        self.request['protected_paths'] = [str(drop), str(self.key)]
        unrelated = drop.parent / '10-resource.conf'; unrelated.write_text('[Service]\nMemoryMax=1G\n')
        self.run_stage('prepare')
        self.assertEqual(drop.read_bytes(), original)
        self.assertEqual(self.pid, 100)
        self.run_stage('activate')
        self.assertFalse(drop.exists())
        self.assertEqual(install.digest(self.args[0]), self.sha)
        self.assertEqual(unrelated.read_text(), '[Service]\nMemoryMax=1G\n')
        self.run_stage('rollback')
        self.assertEqual(drop.read_bytes(), original)
        self.assertEqual(drop.stat().st_mode & 0o777, 0o640)
        self.assertEqual(self.args[0], str(self.old))

    def test_takeover_grant_for_another_release_does_not_apply(self):
        drop = self.takeover()
        self.request['takeover']['release_id'] = 'b' * 64
        self.run_stage('prepare')
        before = self.paths['state_root'] / self.request['unit'] / self.request['release_id'] / 'before.json'
        self.assertNotIn('takeover', json.loads(before.read_text()))
        self.assertTrue(drop.exists())

    def test_takeover_rejects_changed_hash_outside_path_or_symlink_before_restart(self):
        drop = self.takeover()
        original = json.loads(json.dumps(self.request['takeover']))
        for kind in ('hash', 'outside', 'symlink', 'running'):
            with self.subTest(kind=kind):
                self.request['takeover'] = json.loads(json.dumps(original))
                if kind == 'hash': self.request['takeover']['dropins'][0]['sha256'] = 'f' * 64
                if kind == 'outside': self.request['takeover']['dropins'][0]['path'] = str(self.unit)
                if kind == 'running': self.request['takeover']['running_sha256'] = 'f' * 64
                if kind == 'symlink':
                    retained = drop.read_bytes(); drop.unlink(); drop.symlink_to(self.unit)
                with self.assertRaises(ValueError): self.run_stage('prepare')
                self.assertEqual(self.pid, 100)
                if kind == 'symlink': drop.unlink(); drop.write_bytes(retained)

    def test_takeover_missing_without_intent_is_not_treated_as_retired(self):
        drop = self.takeover(); self.run_stage('prepare'); drop.unlink()
        with self.assertRaisesRegex(ValueError, 'missing without retained intent'):
            self.run_stage('activate')
        self.assertEqual(self.pid, 100)

    def test_takeover_resumes_activation_after_override_removed_before_restart(self):
        drop = self.takeover(); self.run_stage('prepare')
        with patch.object(install.subprocess, 'run', side_effect=OSError('restart interrupted')):
            with self.assertRaises(OSError): self.run_stage('activate')
        self.assertFalse(drop.exists()); self.assertEqual(self.pid, 100)
        self.run_stage('activate')
        self.assertEqual(install.digest(self.args[0]), self.sha)
        pid = self.pid; self.run_stage('activate'); self.assertEqual(self.pid, pid)

    def test_takeover_rollback_refuses_reappeared_foreign_override(self):
        drop = self.takeover(); self.run_stage('prepare'); self.run_stage('activate')
        drop.write_text('[Service]\nExecStart=/foreign\n'); pid = self.pid
        with self.assertRaisesRegex(ValueError, 'takeover drop-in changed'):
            self.run_stage('rollback')
        self.assertEqual(drop.read_text(), '[Service]\nExecStart=/foreign\n')
        self.assertEqual(self.pid, pid)

    def test_takeover_rollback_resumes_after_original_restoration_before_restart(self):
        drop = self.takeover(); original = drop.read_bytes()
        self.run_stage('prepare'); self.run_stage('activate')
        with patch.object(install.subprocess, 'run', side_effect=OSError('restart interrupted')):
            with self.assertRaises(OSError): self.run_stage('rollback')
        self.assertEqual(drop.read_bytes(), original)
        self.run_stage('rollback')
        self.assertEqual(self.args[0], str(self.old))

    def test_rollback_refuses_changed_previous_command_symlink(self):
        alias = self.root / 'current'; alias.symlink_to(self.old); self.args[0] = str(alias)
        self.run_stage('prepare'); self.run_stage('activate')
        foreign = self.root / 'foreign'; foreign.write_bytes(b'foreign binary')
        alias.unlink(); alias.symlink_to(foreign)
        pid = self.pid
        with self.assertRaisesRegex(ValueError, 'rollback command changed'):
            self.run_stage('rollback')
        self.assertEqual(self.pid, pid)


if __name__ == '__main__': unittest.main()
