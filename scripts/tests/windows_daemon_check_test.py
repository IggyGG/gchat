"""Standalone diagnostic keeps the real source immutable and retains failed output."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('daemon_check', SCRIPTS / 'windows-daemon-check.py')
daemon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daemon)


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repositories = {}
        for name in ('gchat', 'gcoms'):
            root = self.root / name
            root.mkdir()
            (root / 'Cargo.toml').write_text('[workspace]\nmembers=["crates/unit"]\n', encoding='utf-8')
            (root / 'Cargo.lock').write_text('canonical lock\n', encoding='utf-8')
            (root / 'crates/unit').mkdir(parents=True)
            (root / 'crates/unit/Cargo.toml').write_text('[package]\nname="' + ('gcoms' if name == 'gcoms' else 'gchat-tui') + '"\n', encoding='utf-8')
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            subprocess.run(['git', 'add', '.'], cwd=root, check=True)
            subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                            'commit', '-qm', 'Frozen source'], cwd=root, check=True)
            self.repositories[name] = root
        self.output = self.root / 'evidence'

    def run_check(self, code=0, mutate_source=False, crash=False):
        def execute(command, cwd, environment, log, timeout):
            self.assertEqual(command, ['cargo', 'test', '-p', 'gchat-tui', '--all-features', '--test', 'standalone_daemon', '--', '--nocapture'])
            self.assertFalse(Path(environment['CARGO_TARGET_DIR']).is_relative_to(cwd))
            self.assertEqual(timeout, 600)
            self.assertIn('"gcoms" = { path = ', (cwd / '.cargo/config.toml').read_text())
            (cwd / 'Cargo.lock').write_text('derived locked dependencies\n', encoding='utf-8')
            if mutate_source:
                (cwd / 'Cargo.toml').write_text('changed implementation input', encoding='utf-8')
            log.write_text('standalone child exit diagnostics\n', encoding='utf-8')
            if crash:
                raise RuntimeError('test process launch failed')
            return code, code == 124
        with patch.object(daemon, 'execute', side_effect=execute):
            return daemon.check(self.repositories['gchat'], self.repositories['gcoms'], self.output, self.root / 'target')

    def test_real_archives_and_derived_lock_do_not_modify_original_sources(self):
        before = {name: daemon.source_identity(root) for name, root in self.repositories.items()}
        report = self.run_check()
        self.assertTrue(report['passed'] and report['source_unchanged'] and report['snapshot_sources_unchanged'])
        self.assertEqual(report['sources'], before)
        for name, root in self.repositories.items():
            self.assertEqual(daemon.source_identity(root), before[name])
            self.assertEqual((root / 'Cargo.lock').read_text(), 'canonical lock\n')
            self.assertEqual(daemon.digest(self.output / report['archives'][name]['path']), report['archives'][name]['sha256'])

    def test_failed_test_retains_log_and_source_maps(self):
        report = self.run_check(code=101)
        self.assertFalse(report['passed'])
        self.assertEqual(report['exit_code'], 101)
        self.assertTrue(report['source_unchanged'])
        for key in ('log', 'before', 'after', 'derived_lock', 'cargo_config'):
            self.assertEqual(daemon.digest(self.output / report[key]['path']), report[key]['sha256'])
        self.assertEqual(json.loads((self.output / 'report.json').read_text()), report)

    def test_output_alias_does_not_look_like_an_escaped_member(self):
        alias = self.root / 'alias'
        alias.mkdir()
        self.output = alias / '..' / 'evidence'
        report = self.run_check()
        self.assertTrue(report['passed'] and report['source_unchanged'])

    def test_unexpected_snapshot_mutation_refuses_success(self):
        report = self.run_check(mutate_source=True)
        self.assertFalse(report['passed'] or report['snapshot_sources_unchanged'])

    def test_launch_exception_is_still_retained(self):
        with self.assertRaisesRegex(RuntimeError, 'launch failed'):
            self.run_check(crash=True)
        report = json.loads((self.output / 'report.json').read_text())
        self.assertFalse(report['passed'])
        self.assertEqual(report['error'], 'test process launch failed')


if __name__ == '__main__':
    unittest.main()
