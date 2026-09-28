"""Retained iOS qualification must bind the existing IPA and original failure."""
import copy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_ios_recovery import RULE, INPUTS, validate_run, validate_report


def manifest():
    return {'release_id': RULE['release_id'],
            'sources': {p: {'commit': INPUTS[p + '_commit']} for p in ('gchat', 'gcoms')},
            'versions': {'ios': INPUTS['build_number'], 'linux-x86_64': '0.1.40'},
            'policy': {'ios_certificate_sha256': 'a' * 64}}


class IosRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.manifest = manifest()
        self.run = {'id': RULE['run'], 'head_sha': RULE['controller'],
                    'path': '.github/workflows/ios-verify.yml',
                    'head_repository': {'full_name': 'IggyGG/gchat'},
                    'display_title': 'iOS retained verification ' + RULE['request'],
                    'event': 'workflow_dispatch', 'status': 'completed', 'conclusion': 'success'}
        self.artifact = {'id': RULE['artifact'], 'expired': False,
                         'workflow_run': {'id': RULE['run']},
                         'digest': 'sha256:' + RULE['sha256'], 'size_in_bytes': 316898149}
        self.report = {'scope': 'ios_retained_pair_simulator_and_signed_ipa',
                       'passed': True, 'sources_unchanged': True,
                       'sources': copy.deepcopy(self.manifest['sources']), 'inputs': copy.deepcopy(INPUTS),
                       'application_recompiled': False, 'device_resigned': False,
                       'original_build_passed': False, 'physical_device_qualified': False,
                       'push_qualified': False, 'original_build_verdict_unchanged': True,
                       'simulator_reused_from_original': True,
                       'application': {'ipa': {'sha256': RULE['ipa']}, 'bundle': 'boo.gchat.app',
                           'build_number': INPUTS['build_number'], 'marketing_version': '0.1.40',
                           'profile': {'certificate_sha256': 'a' * 64}}}

    def test_exact_followup_accepts_without_rewriting_original_failure(self):
        before = copy.deepcopy(self.report)
        validate_run(self.manifest, self.run, self.artifact)
        validate_report(self.manifest, self.report)
        self.assertEqual(self.report, before)
        self.assertIs(self.report['original_build_passed'], False)

    def test_other_run_controller_workflow_or_candidate_rejected(self):
        for key, value in [('id', 1), ('head_sha', 'b'*40), ('path', 'other.yml'),
                           ('head_repository', {'full_name': 'other/gchat'}),
                           ('display_title', 'another request'), ('event', 'pull_request'),
                           ('status', 'in_progress'), ('conclusion', 'failure')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_run(self.manifest, {**self.run, key: value}, self.artifact)
        with self.assertRaises(ValueError):
            validate_run({**self.manifest, 'release_id': '0'*64}, self.run, self.artifact)

    def test_other_archive_identity_expiry_or_length_rejected(self):
        for key, value in [('id', 1), ('expired', True), ('workflow_run', {'id': 1}),
                           ('digest', 'sha256:'+'0'*64), ('size_in_bytes', 100)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_run(self.manifest, self.run, {**self.artifact, key: value})

    def test_scope_source_and_verdict_changes_rejected(self):
        for key, value in [('scope', 'another scope'), ('passed', False), ('sources_unchanged', False),
                           ('sources', {}), ('inputs', {}), ('application_recompiled', True),
                           ('device_resigned', True), ('original_build_passed', True),
                           ('physical_device_qualified', True), ('push_qualified', True),
                           ('original_build_verdict_unchanged', False), ('simulator_reused_from_original', False)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_report(self.manifest, {**self.report, key: value})

    def test_substituted_ipa_version_bundle_and_signer_rejected(self):
        for key, value in [('ipa', {'sha256': '0'*64}), ('bundle', 'another.app'),
                           ('build_number', '1.0.60'), ('marketing_version', '0.1.41'),
                           ('profile', {'certificate_sha256': 'b'*64})]:
            report = copy.deepcopy(self.report); report['application'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_report(self.manifest, report)
