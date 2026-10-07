"""Headless activation is explicit and scoped to one existing user manager."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('install_updates', ROOT / 'scripts/install-local-updates.py')
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def preview(self, *args):
        output = io.StringIO()
        with patch('sys.argv', ['install-local-updates.py', *args]), contextlib.redirect_stdout(output), \
             patch.object(installer.subprocess, 'run') as command:
            installer.main()
            command.assert_not_called()
        return output.getvalue()

    def test_default_install_remains_package_only(self):
        output = self.preview()
        self.assertIn('package timer only', output)
        self.assertNotIn('headless-activate', output)

    def test_opt_in_preview_describes_headless_timer(self):
        output = self.preview('--headless-user', 'operator')
        self.assertIn('/etc/systemd/user/gchat-headless-activate.timer', output)
        self.assertIn("selected user's headless activation timer", output)

    @unittest.skipUnless(os.name == 'posix', 'Linux user manager installer')
    def test_opt_in_only_enables_named_users_timer(self):
        with patch('pwd.getpwnam', return_value=SimpleNamespace(pw_uid=1000, pw_name='operator')), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(installer.subprocess, 'run') as command:
            installer.enable_headless('operator')
        calls = [call.args[0] for call in command.call_args_list]
        self.assertEqual(len(calls), 5)
        self.assertEqual(calls[-1], ['runuser', '-u', 'operator', '--', 'env',
                                    'XDG_RUNTIME_DIR=/run/user/1000',
                                    'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus',
                                    'systemctl', '--user', 'enable', '--now', 'gchat-headless-activate.timer'])
        self.assertTrue(all('restart' not in call and 'enable-linger' not in call for call in calls))

    @unittest.skipUnless(os.name == 'posix', 'Linux user manager installer')
    def test_root_or_missing_user_manager_is_rejected_before_installation(self):
        for uid, exists, message in [(0, True, 'non-root'), (1000, False, 'already be running')]:
            with self.subTest(uid=uid), \
                 patch('pwd.getpwnam', return_value=SimpleNamespace(pw_uid=uid, pw_name='operator')), \
                 patch.object(Path, 'exists', return_value=exists), \
                 patch.object(installer.subprocess, 'run') as command:
                with self.assertRaisesRegex(ValueError, message):
                    installer.enable_headless('operator')
                command.assert_not_called()


if __name__ == '__main__':
    unittest.main()
