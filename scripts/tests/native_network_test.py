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
    def test_small_file_permission_is_windows_only_and_sizes_stay_bounded(self):
        for platform in ('nt', 'posix'):
            network.validate_file_bytes(16777216, platform)
        network.validate_file_bytes(4194304, 'nt')
        for size, platform in [(4194304, 'posix'), (1, 'nt'), (True, 'nt'),
                               (4194304.0, 'nt'), (1073741824, 'nt')]:
            with self.subTest(size=size, platform=platform), self.assertRaises(ValueError):
                network.validate_file_bytes(size, platform)

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
    def test_retained_small_gate_binds_exact_binary_and_original_deadlines(self):
        spec = importlib.util.spec_from_file_location('windows_network_policy', ROOT / 'windows-network.py')
        retained = importlib.util.module_from_spec(spec); spec.loader.exec_module(retained)
        self.assertIsNone(retained.qualification_policy('windows36', 16777216))
        path = retained.qualification_policy('windows36', 4194304)
        original = json.loads(path.read_text())
        for candidate in ('windows18', 'windows29'):
            with self.assertRaises(ValueError):retained.qualification_policy(candidate, 4194304)
        with tempfile.TemporaryDirectory() as directory, patch.object(retained, 'ROOT', Path(directory)):
            target = Path(directory) / 'release/automation/qualification/windows36-4mib.json'
            target.parent.mkdir(parents=True)
            for field, bad in [('binary_sha256', 'a'*64), ('sources', {}),
                    ('release_id', 'b'*64), ('platform', 'ios'), ('bytes', 1),
                    ('original_bytes', 4194304), ('completion_seconds', 181), ('total_seconds', 601)]:
                target.write_text(json.dumps({**original, field: bad}))
                with self.subTest(field=field), self.assertRaises(ValueError):
                    retained.qualification_policy('windows36', 4194304)

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
