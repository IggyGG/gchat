"""Only both successful native gates from this run may reach Linux signing."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_automation_test import candidate
from release_evidence import EvidenceError, digest
from release_linux_qualification import COMMANDS, SCOPES, aggregate, qualify, validate_artifact, verify
from release_pair import canonical


class LinuxQualificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.root = self.workspace / 'native-evidence'
        self.root.mkdir()
        self.manifest = candidate()
        self.environment = {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': 'IggyGG/gchat',
                            'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '2',
                            'GITHUB_WORKFLOW_SHA': self.manifest['sources']['gchat']['commit'],
                            'GITHUB_SHA': self.manifest['sources']['gchat']['commit']}
        self.inputs = {
            'schema': 1, 'kind': 'frozen_source_pair', 'sources': self.manifest['sources'],
            'source_archive_sha256': {'gchat': 'a' * 64, 'gcoms': 'b' * 64},
            'target': 'x86_64-unknown-linux-gnu', 'rust_graphs': {'workspace': ['fixture']},
            'derived_lock_sha256': {'Cargo.lock': self.write('paired-gchat/derived/Cargo.lock', b'locked')},
            'npm_archives': {'fixture.tgz': self.write('paired-gchat/npm/fixture.tgz', b'archive')},
            'cargo_config_sha256': self.write('paired-gchat/derived/.cargo/config.toml', b'config'),
            'npm_bindings': {'fixture': 'd' * 64},
            'rust_sources_verified': True, 'npm_sources_verified': True,
        }
        self.native = {'sources': self.manifest['sources'], 'inputs': self.inputs,
                       'exit_code': 0, 'source_unchanged': True}
        self.report = {
            'schema': 1, 'kind': 'linux_native_qualification', 'platform': 'linux-x86_64',
            'native_target': 'x86_64-unknown-linux-gnu', 'sources': self.manifest['sources'],
            'release_id': self.manifest['release_id'],
            'manifest_sha256': hashlib.sha256(canonical(self.manifest)).hexdigest(),
            'provider': {'repository': 'IggyGG/gchat', 'run_id': '123', 'run_attempt': 1,
                         'workflow_commit': self.environment['GITHUB_SHA']},
            'passed': True, 'source_unchanged': True,
            'steps': [{'command': command, 'exit_code': 0,
                       'log': {'path': f'native-{i}.log',
                               'sha256': self.write(f'native-{i}.log', b'actual CI log')}}
                      for i, command in enumerate(COMMANDS)],
        }
        self.save_native()

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
        return digest(path)

    def save_native(self):
        for key, name, data in [('native_ci', 'native-ci.json', self.native),
                                ('inputs', 'inputs.json', self.inputs)]:
            path = 'paired-gchat/' + name
            self.report[key] = {'path': path, 'sha256': self.write(path, canonical(data))}

    def check(self):
        self.write('qualification.json', canonical(self.report))
        return verify(self.root, self.manifest, self.environment)

    def test_same_run_qualified_pair_can_survive_a_packaging_retry(self):
        self.assertEqual(self.check(), self.report)

    def test_failed_missing_boolean_or_different_ci_gate_cannot_authorize_signing(self):
        original = copy.deepcopy(self.report)
        for case in ('failed', 'missing', 'boolean', 'command', 'changed-source'):
            self.report = copy.deepcopy(original)
            if case == 'missing':
                self.report['steps'].pop()
            elif case == 'changed-source':
                self.report['source_unchanged'] = False
            elif case == 'command':
                self.report['steps'][1]['command'] = ['python3', 'mock.py']
            else:
                self.report['steps'][1]['exit_code'] = False if case == 'boolean' else 1
            with self.subTest(case=case), self.assertRaises(EvidenceError):
                self.check()

    def test_stale_platform_source_run_and_manifest_are_rejected(self):
        original = copy.deepcopy(self.report)
        for key, value in [('platform', 'windows-x86_64'), ('sources', {}),
                           ('manifest_sha256', 'a' * 64), ('release_id', 'b' * 64),
                           ('provider', {**original['provider'], 'run_id': '122'}),
                           ('provider', {**original['provider'], 'run_attempt': 3})]:
            self.report = {**original, key: value}
            with self.subTest(key=key, value=value), self.assertRaises(EvidenceError):
                self.check()

    def test_modified_or_missing_logs_locks_and_archives_are_rejected(self):
        for name in ('native-0.log', 'native-1.log', 'paired-gchat/derived/Cargo.lock',
                     'paired-gchat/npm/fixture.tgz', 'paired-gchat/derived/.cargo/config.toml'):
            path = self.root / name
            original = path.read_bytes()
            for value in (original + b'changed', None):
                if value is None:
                    path.unlink()
                else:
                    path.write_bytes(value)
                with self.subTest(name=name, value=value), self.assertRaises(EvidenceError):
                    self.check()
            path.write_bytes(original)

    def test_paired_ci_must_itself_pass_the_same_source_and_dependency_inputs(self):
        original = copy.deepcopy(self.native)
        for key, value in [('exit_code', 1), ('exit_code', False),
                           ('sources', {}), ('source_unchanged', False), ('inputs', {})]:
            self.native = {**original, key: value}
            self.save_native()
            with self.subTest(key=key, value=value), self.assertRaises(EvidenceError):
                self.check()

    def test_artifact_requires_job_digest_and_same_run_provider_binding(self):
        artifact = {'id': 456, 'name': 'linux-qualification-1', 'expired': False,
                    'digest': 'sha256:' + 'a' * 64, 'size_in_bytes': 1234,
                    'workflow_run': {'id': 123, 'head_sha': self.environment['GITHUB_SHA']}}
        validate_artifact(artifact, '456', 'a' * 64, self.manifest, self.environment)
        for key, value in [('id', 455), ('name', 'linux-x86_64'), ('expired', True),
                           ('digest', 'sha256:' + 'b' * 64), ('size_in_bytes', 0),
                           ('workflow_run', {'id': 122, 'head_sha': self.environment['GITHUB_SHA']}),
                           ('workflow_run', {'id': 123, 'head_sha': 'c' * 40})]:
            with self.subTest(key=key), self.assertRaises(EvidenceError):
                validate_artifact({**artifact, key: value}, '456', 'a' * 64,
                                  self.manifest, self.environment)

    def test_failure_retains_original_exit_and_does_not_run_the_second_gate(self):
        self.root.rename(self.workspace / 'old-evidence')
        def fail(command, workspace, log):
            log.write_text('original native CI failure\n')
            return 17
        with patch('release_linux_qualification.checked_sources'), \
                patch('release_linux_qualification.platform.system', return_value='Linux'), \
                patch('release_linux_qualification.platform.machine', return_value='x86_64'), \
                patch('release_linux_qualification.subprocess.check_output',
                      return_value='host: x86_64-unknown-linux-gnu\n'), \
                patch('release_linux_qualification.execute', side_effect=fail) as executed:
            self.assertEqual(qualify(self.workspace, self.manifest, self.environment), 17)
        self.assertEqual(executed.call_count, 1)
        from release_evidence import read_json
        report = read_json(self.root / 'qualification.json')
        self.assertIs(report['passed'], False)
        self.assertEqual(report['steps'][0]['exit_code'], 17)
        self.report = report
        with self.assertRaises(EvidenceError):
            self.check()

    def test_packaging_depends_on_qualification_and_fetch_precedes_signing(self):
        workflow = (Path(__file__).resolve().parents[2] / '.github/workflows/linux-release.yml').read_text()
        packaging = workflow.split('\n  linux:\n', 1)[1]
        self.assertIn('needs: [qualify, qualify-gcoms, native-build]\n', packaging)
        self.assertIn('${{ needs.qualify.outputs.artifact_id }}', packaging)
        self.assertIn('${{ needs.qualify.outputs.artifact_sha256 }}', packaging)
        self.assertIn('${{ needs.qualify-gcoms.outputs.artifact_id }}', packaging)
        self.assertIn('${{ needs.qualify-gcoms.outputs.artifact_sha256 }}', packaging)
        self.assertLess(packaging.index('release_linux_qualification.py aggregate'),
                        packaging.index('GCHAT_RELEASE_PRIVATE_KEY_BASE64:'))
        self.assertNotIn('GCHAT_RELEASE_PRIVATE_KEY_BASE64:', workflow.split('\n  linux:\n', 1)[0])
        for scope in SCOPES:
            self.assertIn('linux-qualification-' + scope + '-${{ github.run_attempt }}', workflow)
            self.assertIn('qualify --scope ' + scope, workflow)
            self.assertIn('CARGO_TARGET_DIR: ${{ github.workspace }}/.cache/linux-' + scope + '-target', workflow)
        self.assertIn('actions/cache/restore@0400d5f644dc74513175e3cd8d07132dd4860809', workflow)
        self.assertNotIn('actions/cache/save@', workflow)
        self.assertIn("format('linux-build-failure-{0}', github.run_attempt)", packaging)

    def scope_directories(self):
        directories = {}
        for index, scope in enumerate(SCOPES):
            directory = self.workspace / ('original-' + scope)
            shutil.copytree(self.root, directory)
            proof = {**self.report, 'kind': 'linux_native_scope', 'scope': scope,
                     'steps': [self.report['steps'][index]]}
            if scope == 'gcoms':
                proof.pop('native_ci')
                proof.pop('inputs')
                shutil.rmtree(directory / 'paired-gchat')
            (directory / 'qualification.json').write_bytes(canonical(proof))
            directories[scope] = directory
        return directories

    def test_scope_has_one_exact_gate_and_gcoms_does_not_need_gchat_provenance(self):
        for scope, directory in self.scope_directories().items():
            proof = verify(directory, self.manifest, self.environment, scope)
            self.assertEqual(len(proof['steps']), 1)
            other = 'gcoms' if scope == 'gchat' else 'gchat'
            with self.assertRaises(EvidenceError):
                verify(directory, self.manifest, self.environment, other)

    def test_aggregate_retains_both_original_scopes_and_rechecks_tampering(self):
        directories = self.scope_directories()
        shutil.rmtree(self.root)
        def fetched(workspace, manifest, environment, artifact_id, sha, scope, destination):
            self.assertEqual((artifact_id, sha), ('id-' + scope, scope + '-digest'))
            shutil.copytree(directories[scope], destination)
            return destination
        artifacts = {scope: ('id-' + scope, scope + '-digest') for scope in SCOPES}
        with patch('release_linux_qualification.fetch', side_effect=fetched), \
                patch('release_linux_qualification.checked_sources'):
            result = aggregate(self.workspace, self.manifest, self.environment, artifacts)
        self.assertEqual(result['kind'], 'linux_native_qualification')
        self.assertEqual([step['command'] for step in result['steps']], list(COMMANDS))
        self.assertEqual(set(result['scopes']), set(SCOPES))
        self.assertEqual(verify(self.root, self.manifest, self.environment), result)
        (self.root / 'scopes/gcoms/native-1.log').write_bytes(b'changed original log')
        with self.assertRaises(EvidenceError):
            verify(self.root, self.manifest, self.environment)

    def test_failed_or_missing_scope_cannot_produce_aggregate(self):
        directories = self.scope_directories()
        shutil.rmtree(self.root)
        with self.assertRaises(EvidenceError):
            aggregate(self.workspace, self.manifest, self.environment, {'gchat': ('1', 'a' * 64)})
        proof_path = directories['gcoms'] / 'qualification.json'
        proof = json.loads(proof_path.read_text())
        proof['passed'] = False
        proof_path.write_bytes(canonical(proof))
        def fetched(workspace, manifest, environment, artifact_id, sha, scope, destination):
            shutil.copytree(directories[scope], destination)
            return destination
        with patch('release_linux_qualification.fetch', side_effect=fetched), \
                self.assertRaises(EvidenceError):
            aggregate(self.workspace, self.manifest, self.environment,
                      {scope: ('1', 'a' * 64) for scope in SCOPES})
        self.assertFalse((self.root / 'qualification.json').exists())

    def test_artifact_scope_cannot_be_substituted(self):
        artifact = {'id': 456, 'name': 'linux-qualification-gchat-1', 'expired': False,
                    'digest': 'sha256:' + 'a' * 64, 'size_in_bytes': 1234,
                    'workflow_run': {'id': 123, 'head_sha': self.environment['GITHUB_SHA']}}
        validate_artifact(artifact, '456', 'a' * 64, self.manifest, self.environment, 'gchat')
        for scope in ('gcoms', None):
            with self.subTest(scope=scope), self.assertRaises(EvidenceError):
                validate_artifact(artifact, '456', 'a' * 64, self.manifest, self.environment, scope)


if __name__ == '__main__':
    unittest.main()
