"""Keep compiler warming separate from release trust and runtime qualification."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import warm_linux_cache as warm


class TrustedCompilerWarmup(unittest.TestCase):
    def test_only_owned_main_push_schedule_or_dispatch_can_warm(self):
        environment = {'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': 'IggyGG/gchat',
                       'GITHUB_REF': 'refs/heads/main', 'GITHUB_EVENT_NAME': 'push'}
        for event in ('push', 'schedule', 'workflow_dispatch'):
            warm.trusted_main(dict(environment, GITHUB_EVENT_NAME=event))
        for field, value in [('GITHUB_ACTIONS', 'false'), ('GITHUB_REPOSITORY', 'fork/gchat'),
                             ('GITHUB_REF', 'refs/heads/release/gchat-test'),
                             ('GITHUB_EVENT_NAME', 'pull_request'), ('GITHUB_EVENT_NAME', 'pull_request_target')]:
            with self.subTest(field=field, value=value), self.assertRaisesRegex(ValueError, 'trusted main'):
                warm.trusted_main(dict(environment, **{field: value}))

    def test_warm_commands_compile_without_running_suites_or_signing(self):
        for scope in warm.SCOPES:
            for _, argv in warm.compile_commands(scope):
                if argv[:2] == ['cargo', 'test']:
                    self.assertIn('--no-run', argv)
                self.assertFalse(any(word in ' '.join(argv) for word in (
                    'release_attest', 'release.py', 'gchat-turnover', 'build-installer',
                    'gpg', 'codesign', 'cargo publish')))
        with self.assertRaisesRegex(ValueError, 'unknown compiler scope'):
            warm.compile_commands('all')

    def test_release_reads_cache_without_saving_or_using_it_as_qualification(self):
        root = Path(__file__).resolve().parents[2]
        release = (root / '.github/workflows/linux-release.yml').read_text()
        self.assertEqual(release.count('uses: actions/cache/restore@'), 3)
        self.assertNotIn('uses: actions/cache@', release)
        self.assertNotIn('uses: actions/cache/save@', release)
        self.assertNotIn('cache-hit', release)
        for scope in warm.SCOPES:
            self.assertIn('--scope ' + scope + ' --github-output', release)
        for command in ('qualify --scope gchat', 'qualify --scope gcoms',
                        'scripts/relay_load_run.py', 'Verify same-run qualification before signing'):
            self.assertIn(command, release)

    def test_only_trusted_main_saves_compiler_bytes_without_release_secrets(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / '.github/workflows/linux-cache.yml').read_text()
        self.assertIn("github.ref == 'refs/heads/main' && github.repository == 'IggyGG/gchat'", workflow)
        self.assertIn("if: success() && steps.cache.outputs.cache-hit != 'true'", workflow)
        self.assertEqual(workflow.count('uses: actions/cache/save@'), 1)
        self.assertNotIn('secrets.', workflow)
        self.assertNotIn('actions/upload-artifact', workflow)
        for forbidden in ('~/.ssh', '~/.cargo/credentials', 'native-evidence/', 'signed/', 'run.lock'):
            self.assertNotIn(forbidden, workflow)

    def test_warm_save_and_release_restore_use_identical_path_version_inputs(self):
        root = Path(__file__).resolve().parents[2]
        paths = []
        for name in ('linux-cache.yml', 'linux-release.yml'):
            workflow = (root / '.github/workflows' / name).read_text()
            for step in workflow.split('      - '):
                if 'uses: actions/cache/' not in step:
                    continue
                if 'uses: actions/cache/restore@' in step:
                    self.assertIn('restore-keys: |\n', step)
                    self.assertIn('${{ steps.compiler.outputs.restore_prefix }}', step)
                    self.assertIn('${{ steps.compiler.outputs.legacy_restore_key }}', step)
                block = step.split('          path: |\n', 1)[1]
                selected = []
                for line in block.splitlines():
                    if not line.startswith('            '):
                        break
                    selected.append(line.strip())
                paths.append(tuple(selected))
        expected = ('~/.cargo/registry', '~/.cargo/git', '~/.cargo/bin/cargo-deny',
                    '~/.npm/_cacache', '${{ steps.compiler.outputs.target }}')
        self.assertEqual(paths, [expected] * 5)


if __name__ == '__main__':
    unittest.main()
