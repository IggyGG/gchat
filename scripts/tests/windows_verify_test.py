"""Preserve signed application bytes and constrain the Windows fixture follow-up."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('windows_verify', SCRIPTS / 'windows-verify.py')
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)


class WindowsVerifyTest(unittest.TestCase):
    def test_fixture_override_cannot_change_lifecycle_or_authentication(self):
        original = "import csv\n\ndef private_directory(path):\n    old()\n\ndef isolated_environment(home):\n    unchanged()\n"
        corrected = "import base64\n\ndef private_directory(path):\n    secure()\n\ndef isolated_environment(home):\n    unchanged()\n"
        verify.verify_fixture_boundary(original, corrected)
        with self.assertRaisesRegex(ValueError, 'outside private'):
            verify.verify_fixture_boundary(original, corrected.replace('unchanged()', 'weakened()'))

    def test_retained_application_only_differs_at_fixture_boundary(self):
        config = verify.package.read(SCRIPTS.parent / 'release/windows-installer-verification.json')
        original = subprocess.check_output(['git', 'show', config['sources']['gchat'] + ':scripts/test-native-application.py'],
                                           cwd=SCRIPTS.parent, text=True)
        verify.verify_fixture_boundary(original, (SCRIPTS / 'test-native-application.py').read_text())


if __name__ == '__main__':
    unittest.main()
