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
        return {'NeedDaemonReload': 'no', 'FragmentPath': str(self.unit), 'DropInPaths': '',
                'MemoryMax': '1073741824', 'TasksMax': '256', 'LimitNOFILE': '8192'}[field]

    def observe(self, _):
        return {'healthy': True, 'running': {'sha256': install.digest(self.args[0]),
                'executable': self.args[0], 'process_id': self.pid}}

    def command(self, argv, **kwargs):
        if argv[:2] == ['systemctl', 'restart']:
            self.pid += 1
            drop = self.paths['unit_root'] / 'ghost-relay.service.d/99z-gchat-release.conf'
            if drop.exists():
                import shlex
                self.args = shlex.split(drop.read_text().split('ExecStart=')[-1].strip())
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


if __name__ == '__main__': unittest.main()
