"""Retained iOS qualification preserves failed receipts and exact device bytes."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('ios_retained', SCRIPTS / 'ios-verify-retained.py')
retained = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(retained)
ios = retained.ios


class RetainedInputsTests(unittest.TestCase):
    def setUp(self):
        self.spec = {'gchat_commit': 'a' * 40, 'gcoms_commit': 'b' * 40, 'build_number': '1.0.9'}
        sources = {name: {'commit': self.spec[name + '_commit'], 'tree': 'c' * 40} for name in ('gchat', 'gcoms')}
        self.inputs = {'schema': 1, 'kind': 'frozen_source_pair', 'sources': sources,
            'source_archive_sha256': {'gchat': 'd' * 64, 'gcoms': 'e' * 64}, 'target': 'aarch64-apple-ios',
            'rust_graphs': {'workspace': ['fixture']}, 'derived_lock_sha256': {'Cargo.lock': 'f' * 64},
            'npm_archives': {'fixture.tgz': '1' * 64}, 'npm_bindings': {'fixture': 'bound'},
            'rust_sources_verified': True, 'npm_sources_verified': True}
        self.original = {'scope': 'ios_exact_pair_simulator_and_signed_ipa', 'sources_unchanged': True,
            'sources': sources, 'bundle': ios.BUNDLE, 'team': ios.TEAM, 'build_number': '1.0.9', 'passed': False,
            'application': {'ipa': 'bound'}, 'simulator_archive': {'sha256': '2' * 64},
            'simulator_executable': {'sha256': '3' * 64}, 'dependency_inputs': self.inputs,
            'feature_graphs': {target: {'gcoms': ['network-client'], 'gcoms-node': ['experimental-gc2']}
                               for target in ios.TARGETS}}
        self.cleanup = {name: True for name in ('passed', 'original_keychain_search_restored',
            'temporary_keychain_removed', 'original_profiles_unchanged', 'private_certificate_removed')}
        self.cleanup['errors'] = []

    def test_original_failed_verdict_is_retained_and_inputs_unchanged(self):
        before = copy.deepcopy(self.original)
        retained.validate_inputs(self.original, self.cleanup, self.inputs, self.spec)
        self.assertEqual(self.original, before)
        self.assertIs(self.original['passed'], False)

    def test_missing_device_artifact_cannot_be_recovered_by_simulator_pass(self):
        self.original.pop('application')
        with self.assertRaisesRegex(ValueError, 'both original'):
            retained.validate_inputs(self.original, self.cleanup, self.inputs, self.spec)

    def test_each_signer_cleanup_and_dependency_binding_is_required(self):
        for key in self.cleanup:
            bad = copy.deepcopy(self.cleanup)
            bad[key] = ['failed'] if key == 'errors' else False
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'signing cleanup'):
                retained.validate_inputs(self.original, bad, self.inputs, self.spec)
        changed = copy.deepcopy(self.inputs)
        changed['source_archive_sha256']['gchat'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'dependency inputs'):
            retained.validate_inputs(self.original, self.cleanup, changed, self.spec)

    def test_hosting_or_missing_mobile_graph_is_not_a_network_client(self):
        self.original['feature_graphs'][ios.TARGETS[0]]['gcoms-node'].append('relay-host')
        with self.assertRaisesRegex(ValueError, 'mobile network client'):
            retained.validate_inputs(self.original, self.cleanup, self.inputs, self.spec)


class RetainedUploadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        def write(name, data):
            path = self.root / name
            path.write_bytes(data)
            return ios.reference(path)
        self.write_json = lambda name, data: write(name, json.dumps(data).encode())
        RetainedInputsTests.setUp(self)
        self.original.update(application={'ipa': write('app.ipa', b'exact device app')},
            signing_cleanup=self.write_json('cleanup.json', self.cleanup),
            simulator_executable=write('original-simulator', b'original simulator'))
        self.sim_spec = {'controller_commit': '4' * 40, 'artifact_sha256': '5' * 64}
        simulator = write('linked-simulator', b'simulator linked by Xcode')
        lifecycle = {'scope': 'ios_installed_simulator_profile_background_reopen', 'passed': True,
            'cleanup_complete': True, 'cleanup_errors': [], 'application': simulator,
            'application_recompiled': False, 'application_resigned': False}
        lifecycle['test_summary'] = self.write_json('xctest-summary.json',
            {'result': 'Passed', 'passedTests': 1, 'failedTests': 0, 'skippedTests': 0})
        lifecycle['xctest_log'] = write('xctest.log', b'actual test evidence fixture')
        authority = {'scope': 'ios_xcode_linked_simulator_authority', 'passed': True,
            'device_qualified': False, 'executable': simulator, 'host_entitlements': {},
            'linked_simulator_authority': {'fixture': 'matching linked authority'}}
        lifecycle_ref = self.write_json('lifecycle.json', lifecycle)
        authority_ref = self.write_json('authority.json', authority)
        simulator_inputs = copy.deepcopy(self.inputs)
        simulator_inputs['target'] = 'aarch64-apple-ios-sim'
        candidate = {'scope': 'ios_exact_pair_xcode_simulator_lifecycle', 'passed': True,
            'sources_unchanged': True, 'sources': self.original['sources'],
            'controller': {'commit': self.sim_spec['controller_commit']}, 'bundle': ios.BUNDLE,
            'build_number': '1.0.9', 'device_rebuilt': False, 'distribution_signer_used': False,
            'dependency_inputs': simulator_inputs, 'feature_graph': {'gcoms': ['network-client'], 'gcoms-node': []},
            'executable': simulator, 'lifecycle': lifecycle_ref, 'linked_authority': authority_ref}
        archive = write('simulator-artifact.zip', b'simulator archive')
        self.sim_spec['artifact_sha256'] = archive['sha256']
        self.report = {'scope': 'ios_retained_pair_simulator_and_signed_ipa', 'passed': True,
            'sources_unchanged': True, 'application_recompiled': False, 'device_resigned': False,
            'simulator_relinked_from_same_source': True,
            'original_build_verdict_unchanged': True, 'sources': self.original['sources'],
            'build_number': '1.0.9', 'original_build_passed': False,
            'original_build': write('original.json', json.dumps(self.original).encode()),
            'original_archive': write('original.zip', b'exact artifact archive'),
            'application': copy.deepcopy(self.original['application']),
            'signing_cleanup': self.original['signing_cleanup'],
            'simulator': lifecycle_ref,
            'simulator_binding': {'report': self.write_json('simulator-build.json', candidate),
                'archive': archive, 'application': simulator, 'lifecycle': lifecycle_ref,
                'original_lifecycle': lifecycle_ref, 'original_build_passed': True, 'lifecycle_rechecked': True,
                'linked_authority': authority_ref, 'verification': self.write_json('verification.json', authority)}}
        self.report['inputs'] = {'artifact_sha256': self.report['original_archive']['sha256'],
                                'simulator': self.sim_spec}

    def test_separate_pass_never_changes_original_failed_build(self):
        ios.validate_upload_build(self.report)
        self.assertIs(json.loads(ios.verify_reference(self.report['original_build']).read_text())['passed'], False)

    def test_original_failed_simulator_journey_requires_distinct_passing_recheck(self):
        report = copy.deepcopy(self.report)
        binding = report['simulator_binding']
        candidate = json.loads(ios.verify_reference(binding['report']).read_text())
        failed = json.loads(ios.verify_reference(binding['original_lifecycle']).read_text())
        failed['passed'] = False
        binding['original_lifecycle'] = self.write_json('original-failed-lifecycle.json', failed)
        candidate.update(passed=False, lifecycle=binding['original_lifecycle'])
        binding.update(report=self.write_json('original-failed-simulator.json', candidate), original_build_passed=False)
        ios.validate_upload_build(report)
        self.assertIs(json.loads(ios.verify_reference(binding['report']).read_text())['passed'], False)
        binding['lifecycle_rechecked'] = False
        with self.assertRaisesRegex(ValueError, 'separate lifecycle'):
            ios.validate_upload_build(report)

    def test_missing_or_skipped_actual_lifecycle_does_not_qualify(self):
        report = copy.deepcopy(self.report)
        lifecycle = json.loads(ios.verify_reference(report['simulator_binding']['lifecycle']).read_text())
        skipped = {'result': 'Passed', 'passedTests': 0, 'failedTests': 0, 'skippedTests': 1}
        lifecycle['test_summary'] = self.write_json('skipped-summary.json', skipped)
        report['simulator_binding']['lifecycle'] = self.write_json('skipped-lifecycle.json', lifecycle)
        report['simulator'] = report['simulator_binding']['lifecycle']
        with self.assertRaisesRegex(ValueError, 'exactly one passing lifecycle'):
            ios.validate_upload_build(report)

    def test_substituted_ipa_or_promoted_original_verdict_is_refused(self):
        for change in ('ipa', 'verdict', 'archive', 'source', 'resigned'):
            report = copy.deepcopy(self.report)
            if change == 'ipa': report['application']['ipa']['sha256'] = '0' * 64
            if change == 'verdict': report['original_build_passed'] = True
            if change == 'archive': report['inputs']['artifact_sha256'] = '0' * 64
            if change == 'source': report['sources']['gchat']['commit'] = 'b' * 40
            if change == 'resigned': report['device_resigned'] = True
            with self.subTest(change=change), self.assertRaises(ValueError):
                ios.validate_upload_build(report)

    def test_wrong_simulator_cannot_authorize_device_upload(self):
        report = copy.deepcopy(self.report)
        report.update(bundle=ios.BUNDLE, team=ios.TEAM)
        wrong = self.root / 'wrong-simulator'
        wrong.write_bytes(b'other source executable')
        report['simulator_binding']['application'] = ios.reference(wrong)
        self.write_json('build.json', report)
        with patch.object(ios, 'signing_pin') as credential_gate:
            with self.assertRaisesRegex(ValueError, 'executable differs'):
                ios.upload(argparse.Namespace(output=self.root))
            credential_gate.assert_not_called()

    def test_failed_lifecycle_cleanup_or_device_source_substitution_prevents_upload(self):
        for change in ('cleanup', 'source', 'archive', 'postlink'):
            report = copy.deepcopy(self.report)
            if change == 'cleanup':
                value = json.loads(ios.verify_reference(report['simulator']).read_text())
                value['cleanup_complete'] = False
                report['simulator_binding']['lifecycle'] = self.write_json('failed-lifecycle.json', value)
            if change == 'source':
                value = json.loads(ios.verify_reference(report['simulator_binding']['report']).read_text())
                value['sources'] = {'gchat': {'commit': '9' * 40}}
                report['simulator_binding']['report'] = self.write_json('other-source.json', value)
            if change == 'archive': report['inputs']['simulator']['artifact_sha256'] = '0' * 64
            if change == 'postlink': report['simulator_relinked_from_same_source'] = False
            with self.subTest(change=change), self.assertRaises(ValueError):
                ios.validate_upload_build(report)

    def test_incomplete_or_failed_recheck_never_reaches_upload(self):
        for key in ('passed', 'sources_unchanged', 'original_build_verdict_unchanged'):
            report = copy.deepcopy(self.report)
            report[key] = False
            with self.subTest(key=key), self.assertRaises(ValueError):
                ios.validate_upload_build(report)


class SameSourceSimulatorTests(unittest.TestCase):
    def setUp(self):
        RetainedInputsTests.setUp(self)
        self.sim_spec = {'controller_commit': '4' * 40, 'run_id': 101, 'artifact_id': 202,
                         'request_id': 'simulator-01', 'artifact_sha256': '5' * 64}
        inputs = copy.deepcopy(self.inputs)
        inputs['target'] = 'aarch64-apple-ios-sim'
        self.candidate = {'scope': 'ios_exact_pair_xcode_simulator_lifecycle', 'passed': True,
            'sources_unchanged': True, 'sources': self.original['sources'],
            'controller': {'commit': self.sim_spec['controller_commit']}, 'bundle': ios.BUNDLE,
            'build_number': '1.0.9', 'device_rebuilt': False, 'distribution_signer_used': False,
            'dependency_inputs': inputs, 'feature_graph': {'gcoms': ['network-client'],
                                                         'gcoms-node': ['experimental-gc2']}}

    def test_same_source_different_target_is_explicit(self):
        retained.validate_simulator(self.candidate, self.original, self.sim_spec)
        self.assertNotEqual(self.candidate['dependency_inputs']['target'], self.inputs['target'])
        self.assertIs(self.original['passed'], False)

    def test_unrelated_source_version_dependency_or_failed_journey_cannot_qualify_ipa(self):
        for key, value in (('passed', False), ('sources_unchanged', False), ('build_number', '1.0.8'),
                           ('sources', {}), ('controller', {'commit': '6' * 40}), ('device_rebuilt', True),
                           ('distribution_signer_used', True)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                retained.validate_simulator(self.candidate | {key: value}, self.original, self.sim_spec)
        for key in ('source_archive_sha256', 'npm_archives', 'npm_bindings'):
            changed = copy.deepcopy(self.candidate)
            changed['dependency_inputs'][key] = {'other': '0' * 64}
            with self.subTest(key=key), self.assertRaises(ValueError):
                retained.validate_simulator(changed, self.original, self.sim_spec)

    def test_incomplete_or_other_workflow_cannot_supply_simulator(self):
        run = {'id': 101, 'head_sha': '4' * 40, 'head_repository': {'full_name': 'IggyGG/gchat'},
            'event': 'workflow_dispatch', 'status': 'completed', 'conclusion': 'success',
            'path': '.github/workflows/ios-lifecycle.yml', 'head_branch': 'release/gchat-ios-lifecycle-0.1.4'}
        artifact = {'id': 202, 'name': 'ios-lifecycle-simulator-01', 'expired': False,
                    'workflow_run': {'id': 101}, 'digest': 'sha256:' + '5' * 64}
        retained.simulator_run_binding(run, artifact, self.sim_spec)
        retained.simulator_run_binding(run | {'conclusion': 'failure'}, artifact, self.sim_spec)
        for key, value in (('conclusion', 'cancelled'), ('path', '.github/workflows/ios-release.yml'),
                           ('head_sha', '7' * 40), ('event', 'pull_request')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                retained.simulator_run_binding(run | {key: value}, artifact, self.sim_spec)
        with self.assertRaises(ValueError):
            retained.simulator_run_binding(run, artifact | {'digest': 'sha256:' + '0' * 64}, self.sim_spec)

    def test_retained_simulator_paths_and_bytes_are_bound(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'ios-simulator-output'
            root.mkdir()
            receipt = root / 'report.json'
            receipt.write_text('original bytes')
            item = ios.reference(receipt)
            self.assertEqual(retained.simulator_file(item, root), receipt)
            with self.assertRaises(ValueError):
                retained.simulator_file(item | {'path': '/ios-simulator-output/../report.json'}, root)
            receipt.write_text('modified bytes')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                retained.simulator_file(item, root)


class OriginalSimulatorLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'ios-lifecycle-output'
        self.root.mkdir()
        self.ref = lambda name, value: self.write(name, json.dumps(value).encode())
        RetainedInputsTests.setUp(self)
        self.inputs = self.spec | {'run_id': 1, 'artifact_id': 2, 'artifact_sha256': '0' * 64}
        binary = {'sha256': '3' * 64, 'size': 123}
        self.original['simulator_executable'] = binary
        authority = {'scope': 'ios_xcode_linked_simulator_authority', 'passed': True,
            'device_qualified': False, 'executable': binary, 'host_entitlements': {},
            'linked_simulator_authority': {'entitlements': {'application-identifier': 'boo.gchat.app'}}}
        names = ('Sources/PushNotifications.swift', 'Sources/UnlockVault.swift',
                 'Tests/PluginTests/PushValidationTests.swift', 'Tests/PluginTests/UnlockVaultTests.swift')
        sources = {name: {'sha256': '4' * 64, 'size': 5} for name in names}
        self.native = {'scope': 'ios_app_hosted_native_push_validation_and_keychain_tests',
            'passed': True, 'sources_unchanged': True, 'cleanup_complete': True,
            'owned_device_removed': True, 'cleanup_errors': [], 'sources': sources,
            'tests': {'passed': 3, 'failed': 0, 'skipped': 0},
            'test_summary': self.ref('native-summary.json', {'result': 'Passed',
                'passedTests': 3, 'failedTests': 0, 'skippedTests': 0}),
            'log': self.write('native.log', b'3 native tests passed')}
        self.candidate = {'scope': 'ios_retained_simulator_profile_background_reopen',
            'passed': True, 'cleanup_complete': True, 'cleanup_errors': [],
            'application_recompiled': False, 'application_resigned': False,
            'simulator_keychain_fixture': False, 'original_build_verdict_unchanged': True,
            'inputs': self.inputs, 'original_build': self.ref('original.json', self.original),
            'original_build_passed': False, 'application': binary, 'original_application': binary,
            'linked_verification': self.ref('authority.json', authority),
            'original_linked_authority': self.ref('original-authority.json', authority),
            'native_tests': self.ref('native.json', self.native),
            'original_native_tests': self.ref('failed-native.json', self.native | {'passed': False}),
            'test_summary': self.ref('summary.json', {'result': 'Passed', 'passedTests': 1,
                'failedTests': 0, 'skippedTests': 0}), 'xctest_log': self.write('xctest.log', b'1 lifecycle passed')}

    def write(self, name, value):
        path = self.root / name
        path.write_bytes(value)
        return ios.reference(path)

    def validate(self, candidate=None):
        return retained.validate_original_lifecycle(candidate or self.candidate,
                                                    self.original, self.inputs, self.root)

    def test_exact_original_simulator_can_reuse_completed_native_and_lifecycle_pass(self):
        original = copy.deepcopy(self.original)
        self.validate()
        self.assertEqual(original, self.original)
        self.assertFalse(self.original['passed'])

    def test_failed_cleanup_resigning_wrong_artifact_and_early_success_are_rejected(self):
        for key, value in (('passed', False), ('cleanup_complete', False), ('cleanup_errors', ['leftover']),
                           ('application_recompiled', True), ('application_resigned', True),
                           ('simulator_keychain_fixture', True), ('original_build_verdict_unchanged', False),
                           ('original_build_passed', True), ('inputs', self.inputs | {'artifact_id': 3}),
                           ('application', {'sha256': '9' * 64, 'size': 123})):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(self.candidate | {key: value})

    def test_native_skip_source_change_or_cleanup_failure_cannot_qualify_upload(self):
        for change in ('skip', 'source', 'cleanup', 'failed'):
            native = copy.deepcopy(self.native)
            if change == 'skip':
                native['test_summary'] = self.ref('skipped.json', {'result': 'Passed',
                    'passedTests': 2, 'failedTests': 0, 'skippedTests': 1})
            if change == 'source': native['sources']['Sources/UnlockVault.swift']['sha256'] = '9' * 64
            if change == 'cleanup': native['owned_device_removed'] = False
            if change == 'failed': native['passed'] = False
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.validate(self.candidate | {'native_tests': self.ref('changed-native.json', native)})

    def test_missing_or_modified_evidence_and_path_escape_fail(self):
        (self.root / 'xctest.log').write_bytes(b'modified')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.validate()
        outside = {'path': str(self.root / '../outside'), 'sha256': '0' * 64, 'size': 0}
        with self.assertRaisesRegex(ValueError, 'unsafe lifecycle'):
            retained.lifecycle_file(outside, self.root)


if __name__ == '__main__':
    unittest.main()
