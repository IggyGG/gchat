"""Package retries reuse exact native inputs, never a newer controller's identity."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import tarfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('macos_package', SCRIPTS / 'macos-package.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class OriginTest(unittest.TestCase):
    def setUp(self):
        self.run = {'id': 12, 'head_sha': 'a' * 40, 'event': 'workflow_dispatch',
                    'path': '.github/workflows/macos-release.yml', 'repository': {'full_name': package.REPO},
                    'status': 'in_progress', 'conclusion': None}
        self.artifact = {'id': 34, 'name': 'macos-aarch64', 'expired': False,
                         'digest': 'sha256:' + 'b' * 64, 'workflow_run': {'id': 12, 'head_sha': 'a' * 40}}

    def verify(self):
        package.verify_origin(self.run, self.artifact, 12, 34, 'b' * 64, 'macos-aarch64', 'a' * 40)

    def test_completed_sibling_can_be_reused_while_other_architecture_runs(self):
        self.verify()

    def test_failed_packaging_run_can_supply_independently_passed_native_receipts(self):
        self.run.update(status='completed', conclusion='failure')
        self.verify()

    def test_other_workflow_event_repository_or_commit_is_rejected(self):
        for field, value in [('head_sha', 'c' * 40), ('event', 'pull_request'), ('id', 13),
                             ('path', '.github/workflows/untrusted.yml'), ('repository', {'full_name': 'other/repo'})]:
            with self.subTest(field=field), patch.dict(self.run, {field: value}):
                with self.assertRaisesRegex(ValueError, 'original native run'):
                    self.verify()

    def test_digest_architecture_expiration_and_run_are_bound(self):
        for field, value in [('digest', 'sha256:' + 'c' * 64), ('name', 'macos-x86_64'),
                             ('expired', True), ('id', 35), ('workflow_run', {'id': 99, 'head_sha': 'a' * 40})]:
            with self.subTest(field=field), patch.dict(self.artifact, {field: value}):
                with self.assertRaisesRegex(ValueError, 'artifact identity'):
                    self.verify()


class ArchiveTest(unittest.TestCase):
    def test_valid_archive_and_traversal_symlink_duplicate_refusal(self):
        for kind in ('valid', 'traversal', 'absolute', 'backslash', 'symlink', 'duplicate'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                archive = root / 'native.zip'
                with zipfile.ZipFile(archive, 'w') as stream:
                    name = {'traversal': '../escape', 'absolute': '/escape', 'backslash': '..\\escape'}.get(kind, 'evidence/report.json')
                    info = zipfile.ZipInfo(name)
                    if kind == 'symlink':
                        info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    stream.writestr(info, b'{}')
                    if kind == 'duplicate':
                        import warnings
                        with warnings.catch_warnings():
                            warnings.simplefilter('ignore', UserWarning)
                            stream.writestr(name, b'{}')
                if kind == 'valid':
                    package.extract_archive(archive, root / 'extracted')
                    self.assertEqual((root / 'extracted/evidence/report.json').read_bytes(), b'{}')
                else:
                    with self.assertRaisesRegex(ValueError, 'unsafe native'):
                        package.extract_archive(archive, root / 'extracted')


class NativeReceiptTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.evidence = self.root / 'evidence'
        self.evidence.mkdir()
        self.target = 'macos-aarch64'
        self.sources = {name: {'commit': letter * 40, 'tree': letter * 40}
                        for name, letter in [('gchat', 'a'), ('gcoms', 'b')]}
        self.candidate = {'sources': copy.deepcopy(self.sources), 'targets': [self.target], 'artifacts': {}, 'checks': {}}
        for name in self.sources:
            self.candidate['sources'][name]['archive'] = self.write('sources/' + name + '.tar', b'source ' + name.encode())
        self.inputs = {'schema': 1, 'kind': 'frozen_source_pair', 'sources': self.sources,
                       'source_archive_sha256': {name: value['archive']['sha256'] for name, value in self.candidate['sources'].items()},
                       'target': package.TARGETS[self.target], 'rust_graphs': {'workspace': [{'name': 'gcoms-node'}]},
                       'rust_sources_verified': True, 'npm_sources_verified': True,
                       'derived_lock_sha256': {'Cargo.lock': self.write('paired-gchat/derived/Cargo.lock', b'lock')['sha256']},
                       'npm_archives': {'package.tgz': self.write('paired-gchat/npm/package.tgz', b'npm')['sha256']},
                       'npm_bindings': {'@gcoms/rpc': {'version': '1'}}}
        self.inputs['cargo_config_sha256'] = self.write('paired-gchat/derived/.cargo/config.toml', b'paths')['sha256']
        self.native = {'exit_code': 0, 'source_unchanged': True, 'sources': self.sources, 'inputs': self.inputs}
        self.reports = {}
        for name in self.sources:
            check = f'native.{name}.{self.target}'
            self.reports[check] = {'schema_version': 1, 'check': check, 'sources': self.sources, 'status': 'passed',
                                   'source_unchanged': True, 'started_at': '2026-01-01T00:00:00Z',
                                   'finished_at': '2026-01-01T00:00:01Z', 'duration_seconds': 1, 'exit_code': 0,
                                   'steps': [{'status': 'passed', 'command': ['python3', 'scripts/ci.py'],
                                              'exit_code': 0, 'log': self.write('logs/' + name + '.log', b'passed')}],
                                   'target': self.target, 'environment': {'native_target': self.target, 'rust_host': package.TARGETS[self.target]},
                                   'tests': {'passed': 12, 'failed': 0, 'ignored': 0, 'excluded': [], 'incomplete': []}}

    def write(self, name, content):
        path = self.evidence / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return {'path': name, 'sha256': hashlib.sha256(content).hexdigest()}

    def save(self):
        for check, report in self.reports.items():
            self.candidate['checks'][check] = self.write('reports/' + check + '.json', json.dumps(report).encode())
        self.write('candidate.json', json.dumps(self.candidate).encode())
        self.write('paired-gchat/inputs.json', json.dumps(self.inputs).encode())
        self.write('paired-gchat/native-ci.json', json.dumps(self.native).encode())

    def verify(self):
        self.save()
        return package.verify_native(self.root, self.target, {name: value['commit'] for name, value in self.sources.items()})

    def test_exact_native_pair_validates_without_relabeling_controller(self):
        result = self.verify()
        self.assertEqual(result['sources'], self.sources)
        self.assertEqual(result['native_ci']['report_sha256'], package.digest(self.evidence / 'paired-gchat/native-ci.json'))

    def test_both_complete_native_ci_entrypoints_are_required(self):
        for check in self.reports:
            original = self.reports[check]['status']
            self.reports[check]['status'] = 'failed'
            with self.assertRaisesRegex(ValueError, 'check status'):
                self.verify()
            self.reports[check]['status'] = original
        self.reports[next(iter(self.reports))]['steps'][0]['command'][1] = 'scripts/only-unit-tests.py'
        with self.assertRaisesRegex(ValueError, 'repository CI entrypoint'):
            self.verify()

    def test_wrong_source_pair_or_architecture_is_refused(self):
        self.save()
        with self.assertRaisesRegex(ValueError, 'source pair differs'):
            package.verify_native(self.root, self.target, {'gchat': 'c' * 40, 'gcoms': 'b' * 40})
        with self.assertRaisesRegex(ValueError, 'target differs'):
            package.verify_native(self.root, 'macos-x86_64', {name: value['commit'] for name, value in self.sources.items()})

    def test_failed_native_provenance_and_changed_input_are_refused(self):
        self.native['exit_code'] = 1
        with self.assertRaisesRegex(ValueError, 'did not pass unchanged'):
            self.verify()
        self.native['exit_code'] = 0
        self.verify()
        (self.evidence / 'paired-gchat/derived/Cargo.lock').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            package.verify_native(self.root, self.target, {name: value['commit'] for name, value in self.sources.items()})

    def test_unbound_log_or_source_archive_is_refused(self):
        self.verify()
        for name in ('logs/gchat.log', 'sources/gcoms.tar'):
            path = self.evidence / name
            original = path.read_bytes()
            path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                package.verify_native(self.root, self.target, {name: value['commit'] for name, value in self.sources.items()})
            path.write_bytes(original)

    def test_missing_config_reconstructed_only_when_original_hash_matches(self):
        original_root = '/Users/runner/work/gchat/gchat/gchat/target/paired-ci/' + 'd' * 32 + '/inputs/gcoms'
        check = f'native.gchat.{self.target}'
        self.reports[check]['steps'][0]['log'] = self.write('logs/gchat.log',
            f'Compiling gcoms-node v1 ({original_root}/crates/node)\n'.encode())
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode='w') as stream:
            for name, content in {'Cargo.toml': '[workspace]\nmembers=["crates/*"]\n',
                                  'crates/node/Cargo.toml': '[package]\nname="gcoms-node"\n'}.items():
                member = tarfile.TarInfo(name)
                member.size = len(content.encode())
                stream.addfile(member, io.BytesIO(content.encode()))
        self.candidate['sources']['gcoms']['archive'] = self.write('sources/gcoms.tar', archive.getvalue())
        self.inputs['source_archive_sha256']['gcoms'] = self.candidate['sources']['gcoms']['archive']['sha256']
        expected = ('[patch.crates-io]\n"gcoms-node" = { path = "' + original_root + '/crates/node" }\n').encode()
        self.inputs['cargo_config_sha256'] = hashlib.sha256(expected).hexdigest()
        destination = self.evidence / 'paired-gchat/derived/.cargo/config.toml'
        destination.unlink()
        self.save()
        commits = {name: value['commit'] for name, value in self.sources.items()}
        result = package.verify_native(self.root, self.target, commits, recover_omitted_config=True)
        self.assertEqual(destination.read_bytes(), expected)
        self.assertIn('cargo_config_reconstruction', result)
        self.assertTrue(json.loads((destination.parents[2] / 'cargo-config-reconstruction.json').read_text())['exact_original_hash_matched'])
        destination.unlink()
        self.inputs['cargo_config_sha256'] = 'f' * 64
        self.save()
        with self.assertRaisesRegex(ValueError, 'does not match the original native hash'):
            package.verify_native(self.root, self.target, commits, recover_omitted_config=True)
        self.assertFalse(destination.exists())


class ControllerTest(unittest.TestCase):
    def test_controller_uses_own_sha_and_approved_ref_separate_from_native_pair(self):
        identity = {'commit': 'c' * 40, 'tree': 'd' * 40}
        ref = 'refs/heads/release/gchat-package-0.1.4'
        environment = {'GITHUB_SHA': identity['commit'], 'GITHUB_WORKFLOW_SHA': identity['commit'],
                       'GITHUB_REF': ref, 'GITHUB_WORKFLOW_REF': f'{package.REPO}/.github/workflows/macos-package.yml@{ref}'}
        with patch.object(package, 'source_identity', return_value=identity), \
             patch.object(package.subprocess, 'check_output', return_value=identity['commit'] + '\n'):
            self.assertEqual(package.verify_controller(Path('.'), environment), {**identity, 'ref': ref})
            for key in ('GITHUB_SHA', 'GITHUB_WORKFLOW_SHA'):
                with patch.dict(environment, {key: 'a' * 40}), self.assertRaisesRegex(ValueError, 'own frozen'):
                    package.verify_controller(Path('.'), environment)
            with patch.dict(environment, {'GITHUB_WORKFLOW_REF': f'{package.REPO}/.github/workflows/macos-release.yml@{ref}'}):
                with self.assertRaisesRegex(ValueError, 'own frozen'):
                    package.verify_controller(Path('.'), environment)


class PackagingHelperTest(unittest.TestCase):
    def test_original_dependency_helper_is_used_with_separate_controller_installer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'scripts').mkdir()
            names = ('prepare_pair', 'verify_derived_inputs', 'verify_resolved_protocol',
                     'verify_native_ci_inputs', 'verify_retained_inputs')
            (root / 'scripts/paired_sources.py').write_text('\n'.join(
                f'def {name}(): return "original {name}"' for name in names))
            installer = SimpleNamespace(ROOT=Path('/controller'), main=lambda _: None)
            with patch.object(package, 'script', return_value=installer):
                selected = package.packaging_helper(root)
            self.assertIs(selected, installer)
            self.assertEqual(selected.ROOT, root.resolve())
            for name in names:
                self.assertEqual(getattr(selected, name)(), 'original ' + name)

    def test_workflow_records_logs_and_preserves_final_dmg_on_later_failure(self):
        workflow = (SCRIPTS.parent / '.github/workflows/macos-package.yml').read_text()
        self.assertIn('controller/scripts/macos-package.py package', workflow)
        self.assertIn('tee retry-evidence/package.log', workflow)
        self.assertIn('signed/build/*/release/bundle/dmg/*.dmg', workflow)
        self.assertIn('if: always()', workflow)
        self.assertNotIn('python3 scripts/build-installer.py --target', workflow)


if __name__ == '__main__':
    unittest.main()
