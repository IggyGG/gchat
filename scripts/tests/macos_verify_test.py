"""Retained signed artifacts keep original failed checks and exact provenance."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('macos_verify', SCRIPTS / 'macos-verify.py')
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class OriginTest(unittest.TestCase):
    def setUp(self):
        self.args = SimpleNamespace(package_run_id=12, artifact_id=34, target='macos-aarch64', artifact_sha256='a' * 64)
        self.run = {'id': 12, 'event': 'workflow_dispatch', 'path': '.github/workflows/macos-package.yml',
                    'repository': {'full_name': 'IggyGG/gchat'}, 'status': 'completed', 'head_sha': 'b' * 40,
                    'conclusion': 'failure'}
        self.artifact = {'id': 34, 'name': 'macos-aarch64-package', 'expired': False,
                         'digest': 'sha256:' + 'a' * 64, 'workflow_run': {'id': 12, 'head_sha': 'b' * 40}}

    def test_failed_origin_can_supply_retained_artifact_without_relabeling(self):
        verify.validate_origin(self.run, self.artifact, self.args)
        self.assertEqual(self.run['conclusion'], 'failure')

    def test_wrong_run_workflow_repository_or_incomplete_origin_is_refused(self):
        for field, value in (('id', 99), ('event', 'push'), ('status', 'in_progress'),
                             ('path', '.github/workflows/other.yml'), ('repository', {'full_name': 'other/repo'})):
            with self.subTest(field=field), patch.dict(self.run, {field: value}):
                with self.assertRaisesRegex(ValueError, 'run identity'):
                    verify.validate_origin(self.run, self.artifact, self.args)

    def test_artifact_hash_target_expiration_and_worker_commit_are_required(self):
        for field, value in (('id', 99), ('name', 'macos-x86_64-package'), ('expired', True),
                             ('digest', 'sha256:' + 'c' * 64), ('workflow_run', {'id': 12, 'head_sha': 'c' * 40})):
            with self.subTest(field=field), patch.dict(self.artifact, {field: value}):
                with self.assertRaisesRegex(ValueError, 'artifact identity'):
                    verify.validate_origin(self.run, self.artifact, self.args)

    def test_controller_workflow_identity_is_separate_from_original_package(self):
        identity = {'commit': 'c' * 40, 'tree': 'd' * 40}
        ref = 'refs/heads/release/gchat-macos-verify-0.1.4'
        environment = {'GITHUB_SHA': identity['commit'], 'GITHUB_WORKFLOW_SHA': identity['commit'],
                       'GITHUB_REF': ref, 'GITHUB_WORKFLOW_REF': 'IggyGG/gchat/.github/workflows/macos-verify.yml@' + ref}
        with patch.object(verify.package, 'source_identity', return_value=identity), \
             patch.object(verify.package.subprocess, 'check_output', return_value=identity['commit'] + '\n'):
            self.assertEqual(verify.package.verify_controller(Path('.'), environment, 'macos-verify.yml'), {**identity, 'ref': ref})
            with self.assertRaisesRegex(ValueError, 'own frozen'):
                verify.package.verify_controller(Path('.'), environment)

    def test_verification_worker_has_no_build_signing_or_secret_step(self):
        workflow = (SCRIPTS.parent / '.github/workflows/macos-verify.yml').read_text()
        self.assertIn('set -o pipefail', workflow)
        self.assertIn('scripts/macos-verify.py', workflow)
        self.assertIn('if: always()', workflow)
        for forbidden in ('secrets.', 'cargo ', 'npm ', 'build-installer.py', 'APPLE_CERTIFICATE'):
            self.assertNotIn(forbidden, workflow)
        source = (SCRIPTS / 'macos-verify.py').read_text()
        self.assertIn("'original_packaging_passed': False", source)
        self.assertIn("'original_post_build_source_recheck_performed': False", source)
        self.assertIn("'recompiled': False, 'resigned': False", source)


if __name__ == '__main__':
    unittest.main()
