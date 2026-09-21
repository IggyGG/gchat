"""Artifact reuse must not relabel a failed build or substitute an application."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
module = importlib.util.spec_from_file_location('ios_lifecycle', SCRIPTS / 'ios-lifecycle.py')
journey = importlib.util.module_from_spec(module)
module.loader.exec_module(journey)


class LifecycleBindingTests(unittest.TestCase):
    def setUp(self):
        self.spec = {'run_id': 123, 'artifact_id': 456, 'gchat_commit': 'a' * 40,
                     'gcoms_commit': 'b' * 40, 'artifact_sha256': 'c' * 64, 'build_number': '1.0.6'}
        self.run = {'id': 123, 'head_sha': self.spec['gchat_commit'], 'head_branch': 'release/gchat-ios-0.1.4',
                    'head_repository': {'full_name': 'IggyGG/gchat'}, 'event': 'workflow_dispatch',
                    'status': 'completed', 'conclusion': 'success', 'path': '.github/workflows/ios-release.yml'}
        self.artifact = {'id': 456, 'name': 'ios-' + 'a' * 40 + '-' + 'b' * 40 + '-1.0.6',
                         'expired': False, 'workflow_run': {'id': 123}, 'digest': 'sha256:' + 'c' * 64}
        self.report = {'scope': 'ios_exact_pair_simulator_and_signed_ipa', 'sources_unchanged': True,
                       'bundle': journey.ios.BUNDLE, 'team': journey.ios.TEAM, 'build_number': '1.0.6',
                       'sources': {'gchat': {'commit': 'a' * 40}, 'gcoms': {'commit': 'b' * 40}},
                       'passed': False, 'error': 'original unrelated device failure'}

    def test_completed_simulator_reuse_does_not_promote_original_failed_build(self):
        self.run['conclusion'] = 'failure'
        before = copy.deepcopy(self.report)
        journey.run_binding(self.run, self.artifact, self.spec)
        journey.build_binding(self.report, self.spec)
        self.assertEqual(self.report, before)
        self.assertIs(self.report['passed'], False)

    def test_substituted_run_source_workflow_or_origin_rejected(self):
        for key, value in (('head_sha', 'd' * 40), ('id', 124), ('head_branch', 'agent/unreviewed'),
                           ('path', '.github/workflows/unrelated.yml'), ('event', 'pull_request'),
                           ('status', 'in_progress'), ('head_repository', {'full_name': 'other/gchat'})):
            with self.subTest(key=key), patch.dict(self.run, {key: value}), self.assertRaises(ValueError):
                journey.run_binding(self.run, self.artifact, self.spec)

    def test_substituted_artifact_rejected(self):
        for key, value in (('id', 999), ('name', 'another-build'), ('expired', True),
                           ('digest', 'sha256:' + 'd' * 64), ('workflow_run', {'id': 124})):
            with self.subTest(key=key), patch.dict(self.artifact, {key: value}), self.assertRaises(ValueError):
                journey.run_binding(self.run, self.artifact, self.spec)

    def test_source_and_original_app_identity_required(self):
        for key, value in (('sources_unchanged', False), ('bundle', 'other.app'), ('team', 'OTHERTEAM0'),
                           ('build_number', '1.0.7'), ('sources', {'gchat': {'commit': 'd' * 40}})):
            with self.subTest(key=key), patch.dict(self.report, {key: value}), self.assertRaises(ValueError):
                journey.build_binding(self.report, self.spec)

    def test_relocated_evidence_requires_original_bytes_and_safe_location(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'report.json').write_bytes(b'bound report')
            item = {'path': '/old/ios-output/report.json', 'size': 12,
                    'sha256': hashlib.sha256(b'bound report').hexdigest()}
            self.assertEqual(journey.relocated(item, root), root / 'report.json')
            for path in ('/old/ios-output/../report.json', '/unrelated/report.json'):
                with patch.dict(item, {'path': path}), self.assertRaises(ValueError):
                    journey.relocated(item, root)
            (root / 'report.json').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                journey.relocated(item, root)

    def test_exactly_one_unskipped_xctest_required(self):
        result = {'result': 'Passed', 'passedTests': 1, 'failedTests': 0, 'skippedTests': 0}
        journey.test_result(result)
        for key, value in (('result', 'Failed'), ('passedTests', 0), ('passedTests', 2),
                           ('failedTests', 1), ('skippedTests', 1)):
            with self.subTest(key=key), patch.dict(result, {key: value}), self.assertRaises(ValueError):
                journey.test_result(result)

    def test_runner_compiles_only_external_ui_test_target(self):
        project = journey.runner_project()
        self.assertEqual(list(project['targets']), ['LifecycleTests'])
        target = project['targets']['LifecycleTests']
        self.assertEqual(target['type'], 'bundle.ui-testing')
        self.assertNotIn('dependencies', target)
        self.assertNotIn('TEST_TARGET_NAME', target['settings']['base'])
        self.assertEqual(target['settings']['base']['CODE_SIGNING_ALLOWED'], 'NO')

    def test_cleanup_failure_still_attempts_delete_and_records_failure(self):
        report = {}
        with patch.object(journey.subprocess, 'run', side_effect=subprocess.TimeoutExpired('simctl', 60)), \
                patch.object(journey.ios, 'run') as delete, patch.object(journey.ios, 'output', return_value='{}'):
            journey.cleanup_device('owned-device', report)
        delete.assert_called_once_with(['xcrun', 'simctl', 'delete', 'owned-device'], timeout=60)
        self.assertIs(report['cleanup_complete'], False)
        self.assertEqual(len(report['cleanup_errors']), 2)


class SimulatorFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.app = self.root / 'original' / 'GChat.app'
        self.app.mkdir(parents=True)
        (self.app / 'Info.plist').write_bytes(plistlib.dumps({'CFBundleExecutable': 'GChat'}))
        (self.app / 'GChat').write_bytes(b'original simulator executable')
        (self.app / 'resource').write_bytes(b'original resource')
        self.destination = self.root / 'journey'

    def sign(self, app, output, change=None):
        self.assertNotEqual(app, self.app)
        self.assertEqual((app / 'GChat').read_bytes(), b'original simulator executable')
        original = journey.ios.reference(app / 'GChat')
        (app / 'GChat').write_bytes(b'derived simulator signature')
        output.mkdir(parents=True)
        receipt = {'scope': 'ios_simulator_adhoc_private_keychain_signing', 'passed': True,
                   'device_qualified': False, 'resources_unchanged': True,
                   'original_executable': original, 'derived_executable': journey.ios.reference(app / 'GChat')}
        if change:
            change(receipt)
        path = output / 'report.json'
        path.write_text(json.dumps(receipt))
        return journey.ios.reference(path)

    def test_default_journey_does_not_sign_or_copy_the_application(self):
        with patch.object(journey.ios, 'sign_simulator') as sign:
            app, binding = journey.application_for_journey(self.app, self.destination)
        self.assertEqual(app, self.app)
        self.assertFalse(self.destination.exists())
        self.assertIs(binding['application_resigned'], False)
        sign.assert_not_called()

    def test_explicit_fixture_preserves_original_and_binds_derived_bytes(self):
        with patch.object(journey.ios, 'sign_simulator', side_effect=self.sign):
            app, binding = journey.application_for_journey(self.app, self.destination, True)
        self.assertEqual((self.app / 'GChat').read_bytes(), b'original simulator executable')
        self.assertEqual((self.app / 'resource').read_bytes(), b'original resource')
        self.assertEqual((app / 'GChat').read_bytes(), b'derived simulator signature')
        self.assertNotEqual(binding['original_application']['sha256'], binding['application']['sha256'])
        self.assertIs(binding['application_resigned'], True)
        self.assertIs(binding['derived_simulator_only'], True)

    def test_substituted_signing_receipt_cannot_qualify_fixture(self):
        changes = [lambda receipt: receipt.update(passed=False),
                   lambda receipt: receipt.update(device_qualified=True),
                   lambda receipt: receipt.update(resources_unchanged=False),
                   lambda receipt: receipt['original_executable'].update(sha256='0' * 64),
                   lambda receipt: receipt['derived_executable'].update(sha256='0' * 64)]
        for index, change in enumerate(changes):
            with self.subTest(index=index), patch.object(journey.ios, 'sign_simulator',
                    side_effect=lambda app, output: self.sign(app, output, change)), self.assertRaises(ValueError):
                journey.application_for_journey(self.app, self.root / str(index), True)

    def test_original_resource_mutation_is_rejected(self):
        def changed(app, output):
            receipt = self.sign(app, output)
            (self.app / 'resource').write_bytes(b'unexpected original mutation')
            return receipt
        with patch.object(journey.ios, 'sign_simulator', side_effect=changed), \
                self.assertRaisesRegex(ValueError, 'original simulator application changed'):
            journey.application_for_journey(self.app, self.destination, True)

    def test_signing_failure_never_modifies_original_executable(self):
        def fails(app, output):
            (app / 'GChat').write_bytes(b'partially signed fixture')
            raise ValueError('signing failed')
        with patch.object(journey.ios, 'sign_simulator', side_effect=fails), self.assertRaises(ValueError):
            journey.application_for_journey(self.app, self.destination, True)
        self.assertEqual((self.app / 'GChat').read_bytes(), b'original simulator executable')


if __name__ == '__main__':
    unittest.main()
