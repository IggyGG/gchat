"""Unsigned outputs remain tied to their original source, compiler and run."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import linux_build_artifacts as builds
from release_automation_test import candidate
from release_evidence import EvidenceError, digest
from release_pair import canonical


class LinuxBuildTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.manifest = candidate()
        self.environment = {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': 'IggyGG/gchat',
                            'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '2', 'RUSTFLAGS': '',
                            'GITHUB_WORKFLOW_SHA': self.manifest['sources']['gchat']['commit'],
                            'GITHUB_SHA': self.manifest['sources']['gchat']['commit']}
        self.inputs = {'schema': 1, 'kind': 'frozen_source_pair', 'sources': self.manifest['sources'],
                       'source_archive_sha256': {'gchat': 'a' * 64, 'gcoms': 'b' * 64},
                       'target': builds.TARGET, 'rust_graphs': {'workspace': ['exact graph']},
                       'derived_lock_sha256': {'Cargo.lock': 'c' * 64}, 'npm_archives': {'local.tgz': 'd' * 64},
                       'npm_bindings': {'local': 'e' * 64}, 'rust_sources_verified': True,
                       'npm_sources_verified': True}
        compiler = patch.object(builds, 'rustc', return_value='rustc pinned\nhost: ' + builds.TARGET + '\n')
        compiler.start(); self.addCleanup(compiler.stop)
        self.retained = self.root / 'retained'
        self.retained.mkdir()

    def services(self):
        for name in builds.SERVICES:
            (self.retained / name).write_bytes(('production ' + name).encode())
        return builds.record(self.retained, self.manifest, 'linux_native_services',
                             [builds.SERVICE_COMMAND], environment=self.environment)

    def desktop(self):
        for name in ('bin/gchat', 'bin/gchat-desktop', 'resources/apps/client/dist/index.html',
                     'resources/third-party/generated/notices.txt'):
            path = self.retained / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(('qualified ' + name).encode())
        return builds.record(self.retained, self.manifest, 'linux_desktop',
                             [builds.DESKTOP_COMMAND, builds.CLI_COMMAND], self.inputs, self.environment)

    def test_same_run_prior_attempt_restages_exact_binaries_and_generated_resources(self):
        self.environment['GITHUB_RUN_ATTEMPT'] = '1'
        report = self.desktop()
        self.environment['GITHUB_RUN_ATTEMPT'] = '2'
        checkout = self.root / 'paired'
        for name in builds.RESOURCE_DIRS:
            path = checkout / name
            path.mkdir(parents=True)
            (path / 'stale.txt').write_text('must be replaced')
        build = self.root / 'target'
        self.assertEqual(builds.stage_desktop(self.retained, build, checkout, self.manifest,
                                             self.inputs, self.environment), report)
        for name in ('gchat', 'gchat-desktop'):
            self.assertEqual(digest(build / builds.TARGET / 'release' / name), report['files']['bin/' + name])
        self.assertEqual((checkout / 'apps/client/dist/index.html').read_bytes(),
                         (self.retained / 'resources/apps/client/dist/index.html').read_bytes())
        self.assertFalse((checkout / 'third-party/generated/stale.txt').exists())

    def test_source_run_attempt_features_compiler_and_profile_must_match(self):
        original = self.services()
        cases = [('sources', {}), ('release_id', 'f' * 64), ('target', 'aarch64-unknown-linux-gnu'),
                 ('provider', {**original['provider'], 'run_id': '124'}),
                 ('provider', {**original['provider'], 'run_attempt': 3}),
                 ('provider', {**original['provider'], 'run_attempt': True}),
                 ('commands', [['cargo', 'build']]), ('rustc', 'other\nhost: ' + builds.TARGET + '\n'),
                 ('rustflags', '-C opt-level=0'),
                 ('compiler_environment', {**original['compiler_environment'], 'CARGO_PROFILE_RELEASE_LTO': 'false'})]
        for key, value in cases:
            (self.retained / 'receipt.json').write_bytes(canonical({**original, key: value}))
            with self.subTest(key=key, value=value), self.assertRaises(EvidenceError):
                builds.verify(self.retained, self.manifest, 'linux_native_services', self.environment)

    def test_changed_missing_and_extra_executable_cannot_be_packaged(self):
        self.services()
        executable = self.retained / 'gcnode'
        original = executable.read_bytes()
        for change in ('changed', 'missing', 'extra'):
            if change == 'changed': executable.write_bytes(b'changed')
            elif change == 'missing': executable.unlink()
            else: (self.retained / 'unexpected').write_bytes(b'extra')
            with self.subTest(change=change), self.assertRaises(EvidenceError):
                builds.verify(self.retained, self.manifest, 'linux_native_services', self.environment)
            executable.write_bytes(original)

    def test_desktop_dependency_graph_is_the_qualified_graph(self):
        self.desktop()
        inputs = copy.deepcopy(self.inputs)
        inputs['derived_lock_sha256']['Cargo.lock'] = 'f' * 64
        with self.assertRaisesRegex(EvidenceError, 'dependencies'):
            builds.verify(self.retained, self.manifest, 'linux_desktop', self.environment, inputs)

    def test_retention_builds_cli_once_and_preserves_ci_desktop(self):
        checkout = self.root / 'paired'; checkout.mkdir()
        target = self.root / 'target/release'; target.mkdir(parents=True)
        (target / 'gchat-desktop').write_bytes(b'CI desktop')
        for name in builds.RESOURCE_DIRS:
            (checkout / name).mkdir(parents=True)
            (checkout / name / 'resource').write_text('qualified')
        manifest = self.root / 'manifest.json'; manifest.write_bytes(canonical(self.manifest))
        environment = {**self.environment, 'GCHAT_RELEASE_MANIFEST': str(manifest),
                       'CARGO_TARGET_DIR': str(target.parent)}
        def compile_cli(command, **kwargs):
            self.assertEqual(command, builds.CLI_COMMAND)
            self.assertEqual(kwargs['cwd'], checkout)
            (target / 'gchat').write_bytes(b'CLI')
        with patch.object(builds.subprocess, 'run', side_effect=compile_cli) as run:
            report = builds.retain_desktop(checkout, self.inputs, self.root / 'provenance', environment)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(report['files']['bin/gchat-desktop'], hashlib.sha256(b'CI desktop').hexdigest())

    def test_load_cannot_substitute_fixture_gcnode_for_production(self):
        services = self.services()
        self.retained.rename(self.root / 'native-services')
        fixture = self.root / 'relay-build'; (fixture / 'bin').mkdir(parents=True)
        report = {'passed': True, 'sources': {}, 'artifacts': {}, 'provided_relay': {
            'receipt': services, 'receipt_sha256': digest(self.root / 'native-services/receipt.json')}}
        for name, source in self.manifest['sources'].items():
            report['sources'][name] = {'unchanged': True, 'revision': source['commit'], 'files': {},
                'snapshot_sha256': hashlib.sha256(json.dumps({}, sort_keys=True).encode()).hexdigest()}
        for name in ('gcnode', 'gchat', 'fleet_probe', 'turnover_daemon'):
            path = fixture / 'bin' / name
            path.write_bytes((self.root / 'native-services/gcnode').read_bytes() if name == 'gcnode' else name.encode())
            report['artifacts'][name] = {'sha256': digest(path), 'size': path.stat().st_size}
        (fixture / 'build.json').write_bytes(canonical(report))
        self.assertEqual(builds.verify_fleet(self.root, self.manifest, self.environment), report)
        # Even a self-consistent fixture report cannot substitute its own relay.
        (fixture / 'bin/gcnode').write_bytes(b'fixture feature graph')
        report['artifacts']['gcnode'] = {'sha256': digest(fixture / 'bin/gcnode'), 'size': (fixture / 'bin/gcnode').stat().st_size}
        (fixture / 'build.json').write_bytes(canonical(report))
        with self.assertRaisesRegex(EvidenceError, 'production relay'):
            builds.verify_fleet(self.root, self.manifest, self.environment)


if __name__ == '__main__': unittest.main()
