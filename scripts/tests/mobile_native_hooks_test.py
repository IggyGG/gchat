"""Native release hooks require execution evidence and preserve cleanup failures."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_') + '_native_hooks', SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


android, ios = load('android-build'), load('ios-build')
ANDROID_CASES = [('PushNotificationValidationTest', 'delayedPermissionAndTokenCallbacksCannotUndoOptOut'),
                 ('PushNotificationValidationTest', 'onlyOpaqueReferencesAreAccepted'),
                 ('UnlockVaultValidationTest', 'rejectsPathSlotsAndInvalidSecrets')]
IOS_CASES = [('PushValidationTests', 'testOnlyOpaqueGenericHintsAreAccepted'),
             ('UnlockVaultTests', 'testValidationRejectsPathsAndInvalidSecrets'),
             ('UnlockVaultTests', 'testOptInRoundTripUpdateAndDelete')]


class AndroidHooks(unittest.TestCase):
    def junit(self, folder, cases=ANDROID_CASES, outcome=None):
        root = ET.Element('testsuite')
        for cls, name in cases:
            case = ET.SubElement(root, 'testcase', classname='boo.gchat.app.mobileplatform.' + cls, name=name)
            if outcome: ET.SubElement(case, outcome)
        path = folder / 'TEST-fixture.xml'
        path.parent.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(root).write(path)
        return path

    def test_requires_actual_new_tests_without_failure_skip_or_duplicates(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            self.assertEqual(android.native_unit_results([self.junit(root)])['passed'], 3)
            for cases, outcome in [(ANDROID_CASES[:1], None), (ANDROID_CASES + ANDROID_CASES[:1], None),
                                    (ANDROID_CASES, 'failure'), (ANDROID_CASES, 'error'), (ANDROID_CASES, 'skipped')]:
                with self.subTest(cases=cases, outcome=outcome), self.assertRaises(ValueError):
                    android.native_unit_results([self.junit(root, cases, outcome)])
            with self.assertRaises(ValueError): android.native_unit_results([])

    def test_generated_project_executes_exact_plugin_and_retains_failed_results(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            plugin = root / 'chat/apps/client/src-tauri/mobile-platform/android'
            plugin.mkdir(parents=True)
            (plugin / 'build.gradle.kts').write_text('// exact plugin')
            destination = root / 'evidence'
            def execute(command, **kwargs):
                init = (destination / 'native-tests.gradle').read_text()
                self.assertIn(json.dumps(str(plugin.resolve())), init)
                self.assertIn('tasks.named("testDebugUnitTest")', init)
                self.assertIn('outputs.upToDateWhen { false }', init)
                self.assertNotIn('--rerun-tasks', command)
                self.assertEqual(command[-1], 'gchatNativeUnitTests')
                self.junit(destination / 'junit', outcome='failure')
                return subprocess.CompletedProcess(command, 1)
            with patch.object(android.subprocess, 'run', side_effect=execute), self.assertRaisesRegex(ValueError, 'tests failed'):
                android.native_unit_tests(root / 'chat', root / 'generated', destination, {})
            report = json.loads((destination / 'report.json').read_text())
            self.assertFalse(report['passed'])
            self.assertEqual(report['exit_code'], 1)
            self.assertTrue(report['sources_unchanged'])
            self.assertEqual(len(report['results']), 1)
            self.assertFalse(report['push_qualified'])


class IosHooks(unittest.TestCase):
    def test_result_requires_named_cases_and_exact_success_summary(self):
        summary = {'result': 'Passed', 'passedTests': 3, 'failedTests': 0, 'skippedTests': 0}
        log = '\n'.join("Test Case '-[PluginTests.%s %s]' passed (0.01 seconds)." % row for row in IOS_CASES)
        self.assertEqual(ios.native_test_results(summary, log)['passed'], 3)
        for value, text in [(summary | {'skippedTests': 1}, log), (summary | {'failedTests': 1}, log),
                            (summary | {'passedTests': 0}, log), (summary, ''), (summary, log + '\n' + log),
                            (summary, log.replace('testOnlyOpaqueGenericHintsAreAccepted', 'testSomethingElse'))]:
            with self.subTest(value=value, log=text), self.assertRaises(ValueError):
                ios.native_test_results(value, text)

    def test_fixture_compiles_original_sources_tests_and_private_host_only(self):
        plugin = Path('/exact/mobile-platform/ios')
        spec = ios.native_test_project(plugin)
        targets = spec['targets']
        sources = targets['tauri-plugin-gchat-mobile-platform']['sources']
        self.assertEqual(sources, [str(plugin / 'Sources/PushNotifications.swift'), str(plugin / 'Sources/UnlockVault.swift')])
        self.assertEqual(targets['PluginTests']['sources'],
                         [str(plugin / 'Tests/PluginTests/PushValidationTests.swift'), str(plugin / 'Tests/PluginTests/UnlockVaultTests.swift')])
        self.assertIn('GChatNativeHost.app', targets['PluginTests']['settings']['base']['TEST_HOST'])
        self.assertNotIn('packages', spec)
        self.assertNotIn('preBuildScripts', json.dumps(spec))

    def test_compile_failure_retains_log_and_deletes_only_owned_simulator(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            plugin = root / 'chat/apps/client/src-tauri/mobile-platform/ios'
            for name in ('Sources/PushNotifications.swift', 'Sources/UnlockVault.swift',
                         'Tests/PluginTests/PushValidationTests.swift', 'Tests/PluginTests/UnlockVaultTests.swift'):
                path = plugin / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('// fixture')
            destination = root / 'evidence'
            device = '11111111-2222-3333-4444-555555555555'
            def execute(command, **kwargs):
                self.assertEqual(command[0], '/usr/bin/xcodebuild')
                self.assertIn('platform=iOS Simulator,id=' + device, command)
                self.assertNotIn('XCODE_XCCONFIG_FILE', kwargs['env'])
                kwargs['stdout'].write(b'compile failure\n')
                return subprocess.CompletedProcess(command, 65)
            def cleanup(value, report):
                self.assertEqual(value, device)
                report['cleanup_complete'] = True
            with patch.object(ios, 'simulator_runtime', return_value='fixture-runtime'), \
                    patch.object(ios, 'simulator_phone', return_value='fixture-phone'), \
                    patch.object(ios, 'output', side_effect=['{"devicetypes":[]}', '{"devices":{}}', device]), \
                    patch.object(ios, 'run'), patch.object(ios.subprocess, 'run', side_effect=execute), \
                    patch.object(ios, 'cleanup_simulator', side_effect=cleanup) as clean, \
                    self.assertRaisesRegex(ValueError, 'native tests failed'):
                ios.native_unit_tests(root / 'chat', destination)
            clean.assert_called_once()
            report = json.loads((destination / 'report.json').read_text())
            self.assertFalse(report['passed'])
            self.assertEqual(report['exit_code'], 65)
            self.assertTrue(report['cleanup_complete'])
            self.assertTrue(report['sources_unchanged'])
            self.assertEqual(ios.verify_reference(report['log']).read_text(), 'compile failure\n')


if __name__ == '__main__':
    unittest.main()
