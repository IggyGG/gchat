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
        self.original = {'scope': 'ios_exact_pair_simulator_and_signed_ipa', 'sources_unchanged': True,
            'passed': False, 'sources': {'gchat': {'commit': 'a' * 40}}, 'build_number': '1.0.9',
            'application': {'ipa': write('app.ipa', b'exact device app')},
            'signing_cleanup': write('cleanup.json', b'original cleanup'),
            'simulator_executable': write('simulator', b'original simulator')}
        self.report = {'scope': 'ios_retained_pair_simulator_and_signed_ipa', 'passed': True,
            'sources_unchanged': True, 'application_recompiled': False, 'device_resigned': False,
            'original_build_verdict_unchanged': True, 'sources': self.original['sources'],
            'build_number': '1.0.9', 'original_build_passed': False,
            'original_build': write('original.json', json.dumps(self.original).encode()),
            'original_archive': write('original.zip', b'exact artifact archive'),
            'application': copy.deepcopy(self.original['application']),
            'signing_cleanup': self.original['signing_cleanup'],
            'simulator_binding': {'original_application': self.original['simulator_executable']}}
        self.report['inputs'] = {'artifact_sha256': self.report['original_archive']['sha256']}

    def test_separate_pass_never_changes_original_failed_build(self):
        ios.validate_upload_build(self.report)
        self.assertIs(json.loads(ios.verify_reference(self.report['original_build']).read_text())['passed'], False)

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
        def retained_file(name, data):
            path = self.root / name
            path.write_text(json.dumps(data))
            return ios.reference(path)
        binary = self.root / 'derived-simulator'
        binary.write_bytes(b'correct simulator')
        actual = ios.reference(binary)
        report.update(bundle=ios.BUNDLE, team=ios.TEAM)
        report['signing_cleanup'] = retained_file('valid-cleanup.json', {'passed': True})
        report['simulator'] = retained_file('smoke.json', {'passed': True, 'cleanup_complete': True,
            'executable': actual | {'sha256': '0' * 64}})
        report['simulator_binding'].update(application_resigned=True, derived_simulator_only=True,
            original_application_unchanged=True, application=actual,
            simulator_keychain_signing=retained_file('signing.json', {'passed': True,
                'resources_unchanged': True, 'device_qualified': False, 'derived_executable': actual}))
        retained_file('build.json', report)
        with patch.object(ios, 'validate_upload_build'), patch.object(ios, 'signing_pin') as credential_gate:
            with self.assertRaisesRegex(ValueError, 'signing/startup artifact differs'):
                ios.upload(argparse.Namespace(output=self.root))
            credential_gate.assert_not_called()

    def test_incomplete_or_failed_recheck_never_reaches_upload(self):
        for key in ('passed', 'sources_unchanged', 'original_build_verdict_unchanged'):
            report = copy.deepcopy(self.report)
            report[key] = False
            with self.subTest(key=key), self.assertRaises(ValueError):
                ios.validate_upload_build(report)


if __name__ == '__main__':
    unittest.main()
