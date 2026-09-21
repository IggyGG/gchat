"""Retained signing preserves code and source identity; pending requests resume."""
import importlib.util
import json
from pathlib import Path
import plistlib
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('macos_notarize_retained', SCRIPTS / 'macos-notarize-retained.py')
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


class FakeCommands:
    def __init__(self, output, report, replies=None):
        self.output = output
        self.report = report
        self.replies = iter(replies or [])
        self.calls = []

    def run(self, label, command, **kwargs):
        self.calls.append(command)
        self.report.setdefault('commands', []).append({'name': label, 'command': command})
        if command[:2] == ['codesign', '--remove-signature']:
            path = Path(command[-1])
            path.write_bytes(path.read_bytes().split(b'SIGNATURE', 1)[0])
            raw = b''
        elif command[:3] == ['xcrun', 'notarytool', 'log']:
            Path(command[4]).write_text(json.dumps({'jobId': command[3], 'status': 'Accepted', 'sha256': 'a' * 64}))
            raw = b''
        else:
            raw = json.dumps(next(self.replies)).encode()
        (self.output / (label + '.stdout')).write_bytes(raw)
        (self.output / (label + '.stderr')).write_bytes(b'')
        return 0, raw


class PolicyAndOriginTests(unittest.TestCase):
    def setUp(self):
        self.args = SimpleNamespace(kind='native', target='macos-aarch64', run_id=12, artifact_id=34,
                                    artifact_sha256='a' * 64, gchat_commit='b' * 40, gcoms_commit='c' * 40)
        self.run = {'id': 12, 'event': 'workflow_dispatch', 'path': '.github/workflows/macos-release.yml',
                    'repository': {'full_name': 'IggyGG/gchat'}, 'status': 'completed',
                    'conclusion': 'success', 'head_sha': 'b' * 40}
        self.artifact = {'id': 34, 'name': 'macos-aarch64', 'expired': False,
                         'digest': 'sha256:' + 'a' * 64, 'workflow_run': {'id': 12, 'head_sha': 'b' * 40}}

    def test_successful_native_origin_binds_workflow_pair_and_archive(self):
        tool.validate_origin(self.run, self.artifact, self.args)

    def test_wrong_origin_and_hash_are_refused(self):
        for key, value in [('status', 'in_progress'), ('conclusion', 'failure'), ('head_sha', 'd' * 40),
                           ('path', '.github/workflows/other.yml'), ('repository', {'full_name': 'other/repo'})]:
            with self.subTest(key=key), patch.dict(self.run, {key: value}):
                with self.assertRaises(ValueError):
                    tool.validate_origin(self.run, self.artifact, self.args)
        for key, value in [('expired', True), ('digest', 'sha256:' + 'd' * 64), ('name', 'macos-x86_64')]:
            with self.subTest(key=key), patch.dict(self.artifact, {key: value}):
                with self.assertRaises(ValueError):
                    tool.validate_origin(self.run, self.artifact, self.args)

    def test_failed_native_is_not_qualified_but_pending_resume_has_distinct_origin(self):
        self.args.kind = 'resume'
        self.run.update(path='.github/workflows/macos-notarize.yml', conclusion='failure')
        self.artifact['name'] = 'macos-aarch64-notarized'
        tool.validate_origin(self.run, self.artifact, self.args)

    def test_per_mac_policy_keeps_other_platform_self_signed_policy(self):
        identity = {'name': 'Gh0st', 'signing_policy': 'publicly-trusted', 'distribution': 'developer-id',
                    'team_id': 'ABCDEFGHIJ', 'certificate_fingerprint': 'a' * 40, 'certificate_sha256': 'b' * 64}
        config = {'signing_policy': 'self-signed', 'publisher_identities': {'macos': identity}}
        self.assertEqual(tool.publisher(config), identity)
        for key, value in [('signing_policy', 'self-signed'), ('distribution', 'app-store'),
                           ('team_id', ''), ('certificate_fingerprint', ''), ('certificate_sha256', '')]:
            with self.subTest(key=key), patch.dict(identity, {key: value}):
                with self.assertRaisesRegex(ValueError, 'Developer ID'):
                    tool.publisher(config)


class CodeIdentityTests(unittest.TestCase):
    def test_signature_changes_only_compare_equal_without_mutating_app(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            app = root / 'GChat.app'
            (app / 'Contents/MacOS').mkdir(parents=True)
            executable = app / 'Contents/MacOS/gchat-native'
            original = bytes.fromhex('cffaedfe') + b'ORIGINAL CODE' + b'SIGNATURE old'
            executable.write_bytes(original)
            executable.chmod(0o755)
            resource = app / 'Contents/Info.plist'
            resource.write_bytes(b'unchanged resources')
            signature = app / 'Contents/_CodeSignature'
            signature.mkdir()
            (signature / 'CodeResources').write_bytes(b'old')
            commands = FakeCommands(root, {})
            before = tool.bundle_identity(app, commands, 'before')
            self.assertEqual(executable.read_bytes(), original)
            executable.write_bytes(original.replace(b'SIGNATURE old', b'SIGNATURE new longer certificate'))
            (signature / 'CodeResources').write_bytes(b'new')
            self.assertEqual(tool.bundle_identity(app, commands, 'after'), before)
            resource.write_bytes(b'changed resources')
            self.assertNotEqual(tool.bundle_identity(app, commands, 'resource'), before)
            resource.write_bytes(b'unchanged resources')
            executable.write_bytes(original.replace(b'ORIGINAL CODE', b'MODIFIED CODE'))
            self.assertNotEqual(tool.bundle_identity(app, commands, 'code'), before)

    @unittest.skipUnless(hasattr(__import__('os'), 'symlink') and sys.platform != 'win32', 'native symlink fixture')
    def test_external_bundle_symlink_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); app = root / 'GChat.app'; app.mkdir()
            (app / 'escape').symlink_to(root)
            with self.assertRaisesRegex(ValueError, 'escapes'):
                tool.bundle_identity(app, FakeCommands(root, {}), 'symlink')

    def test_entitlements_preserved_but_debugger_entitlement_refused(self):
        existing = {'com.apple.security.cs.allow-jit': True, 'com.apple.security.network.client': True}
        self.assertEqual(tool.parse_entitlements(plistlib.dumps(existing)), existing)
        self.assertEqual(tool.parse_entitlements(b''), {})
        with self.assertRaisesRegex(ValueError, 'debugger'):
            tool.parse_entitlements(plistlib.dumps({'com.apple.security.get-task-allow': True}))


class NotaryStateTests(unittest.TestCase):
    environment = {'APPLE_API_KEY_PATH': '/private/protected/key.p8', 'APPLE_API_KEY': 'KEYID', 'APPLE_API_ISSUER': 'issuer'}
    request_id = '11111111-2222-3333-4444-555555555555'

    def test_submit_records_request_before_any_poll_and_cannot_resubmit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); dmg = root / 'GChat.dmg'; dmg.write_bytes(b'signed image')
            report = {'commands': []}
            commands = FakeCommands(root, report, [{'id': self.request_id}])
            tool.submit_once(dmg, self.environment, root, report, commands)
            retained = json.loads((root / 'report.json').read_text())
            self.assertTrue(retained['pending'])
            self.assertEqual(retained['notarization']['id'], self.request_id)
            self.assertEqual(retained['notarization']['submission_dmg_sha256'], tool.digest(dmg))
            with self.assertRaisesRegex(ValueError, 'never resubmitted'):
                tool.submit_once(dmg, self.environment, root, report, commands)
            self.assertEqual(len(commands.calls), 1)

    def test_ambiguous_submit_retains_unknown_without_second_upload(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); dmg = root / 'GChat.dmg'; dmg.write_bytes(b'image')
            report = {'commands': []}; commands = FakeCommands(root, report, [{}])
            with self.assertRaisesRegex(ValueError, 'do not resubmit'):
                tool.submit_once(dmg, self.environment, root, report, commands)
            self.assertEqual(json.loads((root / 'report.json').read_text())['notarization']['status'], 'submission_outcome_unknown')
            self.assertNotIn('id', report['notarization'])

    def test_poll_timeout_is_pending_and_issues_no_upload(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = {'commands': [], 'notarization': {'id': self.request_id, 'status': 'In Progress',
                                                      'submission_dmg_sha256': 'a' * 64}}
            commands = FakeCommands(root, report, [{'id': self.request_id, 'status': 'In Progress'}])
            self.assertFalse(tool.await_notary(self.environment, root, report, commands, 0))
            self.assertTrue(report['pending'])
            self.assertEqual([call[2] for call in commands.calls], ['info'])

    def test_accepted_poll_retains_apple_log_and_wrong_request_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = {'commands': [], 'notarization': {'id': self.request_id, 'status': 'In Progress',
                                                      'submission_dmg_sha256': 'a' * 64}}
            commands = FakeCommands(root, report, [{'id': self.request_id, 'status': 'Accepted'}])
            self.assertTrue(tool.await_notary(self.environment, root, report, commands, 0))
            self.assertEqual(report['notarization']['status'], 'Accepted')
            self.assertTrue(tool.file_reference(root, report['notarization']['log']).is_file())
            self.assertEqual([call[2] for call in commands.calls], ['info', 'log'])
            report['notarization']['status'] = 'In Progress'
            commands.replies = iter([{'id': 'different', 'status': 'Accepted'}])
            with self.assertRaisesRegex(ValueError, 'another notarization'):
                tool.await_notary(self.environment, root, report, commands, 0)

    def test_resume_requires_exact_original_pair_controller_and_pending_id(self):
        args = SimpleNamespace(target='macos-aarch64', gchat_commit='a' * 40, gcoms_commit='b' * 40)
        controller = {'commit': 'c' * 40, 'tree': 'd' * 40, 'ref': 'refs/heads/release/gchat-macos-notarize-0.1.4'}
        report = {'scope': 'retained_macos_developer_id_notarization', 'controller': controller, 'pending': True,
                  'passed': False, 'cleanup_complete': True, 'target': args.target, 'sources': {'gchat': {'commit': args.gchat_commit},
                  'gcoms': {'commit': args.gcoms_commit}}, 'notarization': {'id': self.request_id, 'status': 'In Progress'}}
        tool.validate_resume(report, args, controller)
        for key, value in [('pending', False), ('passed', True), ('cleanup_complete', False), ('target', 'macos-x86_64'),
                           ('notarization', {'status': 'submission_outcome_unknown'}), ('controller', {})]:
            with self.subTest(key=key), patch.dict(report, {key: value}):
                with self.assertRaisesRegex(ValueError, 'pending frozen request'):
                    tool.validate_resume(report, args, controller)

    def test_accepted_request_with_local_failure_resumes_without_second_upload(self):
        args = SimpleNamespace(target='macos-aarch64', gchat_commit='a' * 40, gcoms_commit='b' * 40)
        controller = {'commit': 'c' * 40, 'tree': 'd' * 40}
        report = {'scope': 'retained_macos_developer_id_notarization', 'controller': controller,
                  'pending': False, 'passed': False, 'cleanup_complete': True, 'target': args.target,
                  'sources': {'gchat': {'commit': args.gchat_commit}, 'gcoms': {'commit': args.gcoms_commit}},
                  'notarization': {'id': self.request_id, 'status': 'Accepted'},
                  'error': 'prior local Gatekeeper or staple failure'}
        tool.validate_resume(report, args, controller)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); dmg = root / 'GChat.dmg'; dmg.write_bytes(b'already submitted')
            commands = FakeCommands(root, report)
            with self.assertRaisesRegex(ValueError, 'never resubmitted'):
                tool.submit_once(dmg, self.environment, root, report, commands)
            self.assertEqual(commands.calls, [])


class GatekeeperPreflightTests(unittest.TestCase):
    def test_disabled_policy_fails_before_signing_or_submission_without_modifying_policy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); report = {'commands': []}
            commands = FakeCommands(root, report)
            with patch.object(commands, 'run', return_value=(3, b'assessments disabled\n')) as run:
                with self.assertRaisesRegex(ValueError, 'before signing or Apple submission'):
                    tool.gatekeeper_preflight(root, report, commands)
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[1], ['spctl', '--status'])
            self.assertNotIn('notarization', report)

    def test_enabled_policy_preflight_records_observation_without_global_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); report = {'commands': []}
            commands = FakeCommands(root, report)
            (root / 'gatekeeper-preflight.stdout').write_bytes(b'assessments enabled\n')
            (root / 'gatekeeper-preflight.stderr').write_bytes(b'')
            with patch.object(commands, 'run', return_value=(0, b'assessments enabled\n')):
                tool.gatekeeper_preflight(root, report, commands)
            self.assertTrue(report['gatekeeper_preflight']['assessment_policy_enabled'])
            self.assertFalse(report['gatekeeper_preflight']['policy_modified'])


class WorkflowTests(unittest.TestCase):
    def test_retained_worker_has_no_build_or_gatekeeper_bypass_and_retains_pending_evidence(self):
        workflow = (SCRIPTS.parent / '.github/workflows/macos-notarize.yml').read_text()
        self.assertIn('environment: release-signing', workflow)
        self.assertIn('cancel-in-progress: false', workflow)
        self.assertIn('if: always()', workflow)
        self.assertIn('set -o pipefail', workflow)
        self.assertIn('APPLE_DEVELOPER_ID_CERTIFICATE_BASE64', workflow)
        self.assertIn('options: [native, verified, resume]', workflow)
        for forbidden in ('cargo ', 'npm ', '--no-verify', '--master-disable', 'notarized/work/**'):
            self.assertNotIn(forbidden, workflow)
        source = (SCRIPTS / 'macos-notarize-retained.py').read_text()
        self.assertIn("'--check-notarization'", source)
        self.assertIn("'--context', 'context:primary-signature'", source)
        self.assertIn("'--type', 'execute'", source)
        self.assertIn("'com.apple.quarantine'", source)
        self.assertNotIn("'--remove-signature', str(app)", source)


if __name__ == '__main__':
    unittest.main()
