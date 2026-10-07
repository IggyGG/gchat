import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import controller_runtime as runtime
from release_pair import canonical


class ControllerRuntimeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = {'commit': 'a' * 40, 'tree': 'b' * 40}
        self.path = self.root / 'scripts/release_coordinator.py'
        self.path.parent.mkdir(); self.path.write_bytes(b'frozen bytes')
        self.request = {'schema': 1, 'source': self.source, 'files': {
            self.path.relative_to(self.root).as_posix(): hashlib.sha256(self.path.read_bytes()).hexdigest()}}
        environment = patch.dict(os.environ, GCHAT_CONTROLLER_REVISION=self.source['commit'])
        environment.start(); self.addCleanup(environment.stop)

    def execute(self, action=lambda: None):
        suite = unittest.TestSuite([unittest.FunctionTestCase(action)])
        with patch.object(runtime.unittest.defaultTestLoader, 'loadTestsFromNames', return_value=suite), \
             patch.object(runtime, 'MINIMUM_TESTS', 1):
            return runtime.check(self.request, self.root)

    def test_actual_success_retains_the_source_inventory_and_revision(self):
        proof = self.execute()
        self.assertTrue(proof['production_controller_revision_tested'])
        self.assertEqual(proof['source'], self.source)
        self.assertEqual(proof['inventory_sha256'], hashlib.sha256(canonical(self.request['files'])).hexdigest())

    def test_noisy_test_import_and_cli_output_do_not_corrupt_json_proof(self):
        from contextlib import redirect_stderr, redirect_stdout
        stdout, stderr = io.StringIO(), io.StringIO()
        def noisy_loader(_):
            print('test import diagnostic')
            return unittest.TestSuite([unittest.FunctionTestCase(
                lambda: print('provider quota; retained original operation'))])
        with redirect_stdout(stdout), redirect_stderr(stderr), \
             patch.object(runtime.unittest.defaultTestLoader, 'loadTestsFromNames', side_effect=noisy_loader), \
             patch.object(runtime, 'MINIMUM_TESTS', 1):
            # This is the same check-then-print protocol as the container entry.
            print(json.dumps(runtime.check(self.request, self.root)), flush=True)
        proof = json.loads(stdout.getvalue())
        self.assertTrue(proof['passed'])
        self.assertEqual(proof['source'], self.source)
        self.assertIn('test import diagnostic', stderr.getvalue())
        self.assertIn('provider quota; retained original operation', stderr.getvalue())
        self.assertIn('Ran 1 test', stderr.getvalue())

    def test_noisy_failure_retains_diagnostics_without_success_json(self):
        from contextlib import redirect_stderr, redirect_stdout
        stdout, stderr = io.StringIO(), io.StringIO()
        def noisy_failure():
            print('failed operation diagnostic')
            raise AssertionError('original test failure')
        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaisesRegex(ValueError, 'tests did not complete'):
                print(json.dumps(self.execute(noisy_failure)), flush=True)
        self.assertEqual(stdout.getvalue(), '')
        self.assertIn('failed operation diagnostic', stderr.getvalue())
        self.assertIn('original test failure', stderr.getvalue())

    def test_wrong_production_revision_is_refused_before_tests(self):
        with patch.dict(os.environ, GCHAT_CONTROLLER_REVISION='c' * 40), \
             patch.object(runtime.unittest.defaultTestLoader, 'loadTestsFromNames') as loader:
            with self.assertRaisesRegex(ValueError, 'revision'): runtime.check(self.request, self.root)
            loader.assert_not_called()

    def test_changed_bytes_symlinks_and_unsafe_paths_are_refused(self):
        self.path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'bytes changed'): self.execute()
        self.path.unlink(); self.path.symlink_to('/dev/null')
        with self.assertRaisesRegex(ValueError, 'bytes changed'): self.execute()
        for name in ('../outside', '/scripts/outside', '', 'application/code.py'):
            with self.subTest(name=name):
                self.request['files'] = {name: 'a' * 64}
                with self.assertRaisesRegex(ValueError, 'path or hash'): self.execute()

    def test_failed_and_skipped_real_tests_cannot_qualify_an_image(self):
        def failure(): raise AssertionError('original gate failed')
        def skipped(): raise unittest.SkipTest('missing runtime capability')
        for action in (failure, skipped):
            with self.subTest(action=action):
                with self.assertRaisesRegex(ValueError, 'tests did not complete'): self.execute(action)

    def test_test_mutation_invalidates_the_previously_matching_source(self):
        with self.assertRaisesRegex(ValueError, 'changed during tests'):
            self.execute(lambda: self.path.write_bytes(b'mutated by test'))

    def test_failed_container_retains_its_log_without_a_success_receipt(self):
        failed = subprocess.CompletedProcess(['docker'], 1, b'', b'production ENV test failed')
        with patch.object(runtime, 'expected_sources', return_value=self.request), \
             patch.object(runtime.subprocess, 'run', return_value=failed):
            with self.assertRaises(subprocess.CalledProcessError):
                runtime.qualify('exact-image', self.root, self.source, 'sha256:' + 'f' * 64, self.root)
        self.assertEqual((self.root / 'controller-runtime.log').read_bytes(), failed.stderr)
        self.assertFalse((self.root / 'controller-runtime.json').exists())

    def test_success_requires_the_complete_inventory_and_is_bound_to_image_and_log(self):
        proof = {'schema': 1, 'passed': True, 'source': self.source, 'source_unchanged': True,
                 'production_controller_revision_tested': True, 'tests': runtime.MINIMUM_TESTS,
                 'source_files_verified': len(runtime.SUITES), 'suites': list(runtime.SUITES),
                 'inventory_sha256': hashlib.sha256(canonical(self.request['files'])).hexdigest()}
        result = subprocess.CompletedProcess(['docker'], 0, json.dumps(proof).encode(), b'actual tests')
        with patch.object(runtime, 'expected_sources', return_value=self.request), \
             patch.object(runtime.subprocess, 'run', return_value=result) as run:
            with self.assertRaisesRegex(ValueError, 'different source inventory'):
                runtime.qualify('exact-image', self.root, self.source, 'sha256:' + 'f' * 64, self.root)
            proof['source_files_verified'] = 1
            result.stdout = json.dumps(proof).encode()
            with patch.object(runtime, 'SUITES', ('release_coordinator_test',)):
                proof['suites'] = list(runtime.SUITES); result.stdout = json.dumps(proof).encode()
                retained = runtime.qualify('exact-image', self.root, self.source, 'sha256:' + 'f' * 64, self.root)
            command = run.call_args.args[0]
        self.assertIn('none', command); self.assertIn('--read-only', command)
        self.assertIn('--cap-drop=ALL', command); self.assertNotIn('-v', command)
        self.assertNotIn('GCHAT_CONTROLLER_REVISION=' + self.source['commit'], command)
        self.assertEqual(retained['configuration_digest'], 'sha256:' + 'f' * 64)
        self.assertEqual(retained['log_sha256'], hashlib.sha256(result.stderr).hexdigest())


if __name__ == '__main__': unittest.main()
