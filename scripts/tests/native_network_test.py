"""Deadline rejection controls for the real packaged network fixture."""
import importlib.util
from pathlib import Path
import sys
import unittest
import json
import os
import tempfile
import copy
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

class DiagnosticTests(unittest.TestCase):
    def test_diagnostics_require_explicit_opt_in_and_keep_provider_overrides_stripped(self):
        for enabled in ('0', '1'):
            with self.subTest(enabled=enabled), patch.dict(os.environ, {
                    'GC_HTTP_RESOLVE': 'untrusted', 'GCHAT_HOME': 'other-profile',
                    'GCHAT_NETWORK_INVITATION': 'must-not-inherit',
                    'GCHAT_FILE_DIAGNOSTICS': '1', 'GCHAT_NETWORK_DIAGNOSTICS': enabled}, clear=True):
                env = network.fixture_environment(Path('owned-profile'))
                self.assertEqual(env['GCHAT_HOME'], 'owned-profile')
                self.assertNotIn('GC_HTTP_RESOLVE', env)
                self.assertNotIn('GCHAT_NETWORK_INVITATION', env)
                self.assertEqual(env.get('GCHAT_FILE_DIAGNOSTICS'), '1' if enabled == '1' else None)

    def test_retained_retry_refuses_other_failures_or_incomplete_cleanup(self):
        spec = importlib.util.spec_from_file_location('windows_network', ROOT / 'windows-network.py')
        retained = importlib.util.module_from_spec(spec); spec.loader.exec_module(retained)
        good = {'report': {'passed': False, 'error': 'installed network delivery/recovery failed',
                          'cleanup': {'passed': True}, 'persistent_certificate_stores_unchanged': True},
                'network': {'passed': False, 'inputs_unchanged': True, 'children_stopped': True},
                'service': {'passed': True}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def write(value):
                for name, item in value.items():
                    path = root / 'application-smoke' / ('report.json' if name == 'report' else name + '/report.json')
                    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(item))
            write(good); retained.original_network_failure(root)
            for section, key, bad in [('report', 'error', 'signature failure'),
                    ('report', 'cleanup', {'passed': False}), ('report', 'persistent_certificate_stores_unchanged', False),
                    ('network', 'inputs_unchanged', False), ('network', 'children_stopped', False),
                    ('service', 'passed', False)]:
                with self.subTest(section=section, key=key):
                    value = copy.deepcopy(good); value[section][key] = bad; write(value)
                    with self.assertRaises(ValueError): retained.original_network_failure(root)

if __name__ == '__main__':
    unittest.main()
