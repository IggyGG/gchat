import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from relay_load_run import retain_journey, run
from release_automation_test import candidate


class RelayLoadRetentionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'source'
        self.source.mkdir()
        self.output = self.root / 'output'

    def test_retains_original_rotated_evidence_without_profile_keys(self):
        (self.source / 'r0').mkdir()
        (self.source / 'r0/metrics.jsonl.1').write_text('original metric')
        (self.source / 'r0/private.key').write_text('must stay in fixture')
        value = {'evidence': {'r0/metrics.jsonl.1': 'unused by copying'}}
        (self.source / 'worker.json').write_text(json.dumps(value))
        retain_journey(self.source, self.output)
        self.assertEqual((self.output / 'r0/metrics.jsonl.1').read_text(), 'original metric')
        self.assertFalse((self.output / 'r0/private.key').exists())
        self.assertEqual((self.output / 'worker.json').read_bytes(), (self.source / 'worker.json').read_bytes())

    @unittest.skipUnless(os.name == 'posix', 'isolated relay workers require POSIX')
    def test_retained_production_build_skips_compilation_but_runs_both_complete_gates(self):
        value = candidate(); manifest = self.root / 'candidate.json'; manifest.write_text(json.dumps(value))
        retained = self.root / 'prebuilt'
        (retained / 'relay-build').mkdir(parents=True)
        (retained / 'relay-build/build.json').write_text('{"passed":true}')
        (retained / 'native-services').mkdir()
        (retained / 'native-services/receipt.json').write_text('{"original":"receipt"}')
        with patch.dict(os.environ, {'GCHAT_RELEASE_MANIFEST': str(manifest)}), \
             patch('relay_load_run.context', return_value={}), patch('relay_load_run.checked_sources'), \
             patch('linux_build_artifacts.verify_fleet') as verified, \
             patch('relay_load_run.retain_journey'), patch('release_relay_load.verify'), \
             patch('relay_load_run.source_identity', side_effect=[value['sources']['gchat'], value['sources']['gcoms']]), \
             patch('relay_load_run.execute') as executed:
            run(self.source, self.output, self.root / 'work', self.root / 'target', retained)
        verified.assert_called_once_with(retained.resolve(), value)
        self.assertEqual(executed.call_count, 2)
        commands = [call.args[0] for call in executed.call_args_list]
        self.assertEqual([command[command.index('--mode') + 1] for command in commands], ['relay-preflight', 'relay-load'])
        self.assertEqual(commands[1][commands[1].index('--load-seconds') + 1], '1800')
        self.assertTrue(all(command[command.index('--build') + 1] == retained / 'relay-build' for command in commands))
        self.assertEqual((self.output / 'native-services.json').read_bytes(), (retained / 'native-services/receipt.json').read_bytes())
        self.assertTrue(json.loads((self.output / 'summary.json').read_text())['passed'])

    def test_rejects_reference_outside_the_fixture(self):
        for reference in ('../outside', '/outside', 'r0/../../outside',
                          'C:/outside', 'C:outside', '\\outside',
                          '\\\\server\\outside', 'r0\\..\\..\\outside'):
            (self.source / 'worker.json').write_text(json.dumps({'evidence': {reference: 'bad'}}))
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                retain_journey(self.source, self.output)

    @unittest.skipUnless(os.name == 'posix', 'isolated relay workers require POSIX')
    def test_rejects_symlinked_reference(self):
        (self.root / 'outside').write_text('private')
        (self.source / 'log').symlink_to(self.root / 'outside')
        (self.source / 'worker.json').write_text(json.dumps({'evidence': {'log': 'bad'}}))
        with self.assertRaises(ValueError):
            retain_journey(self.source, self.output)

    @unittest.skipUnless(os.name == 'posix', 'isolated relay workers require POSIX')
    def test_dirty_source_retains_original_failure_and_failed_summary(self):
        manifest = self.root / 'candidate.json'
        manifest.write_text(json.dumps(candidate()))
        with patch.dict(os.environ, {'GCHAT_RELEASE_MANIFEST': str(manifest)}), \
             patch('relay_load_run.context', return_value={}), \
             patch('relay_load_run.checked_sources'), \
             patch('relay_load_run.execute', side_effect=RuntimeError('original failure')), \
             patch('relay_load_run.source_identity', side_effect=ValueError('dirty source')):
            with self.assertRaisesRegex(RuntimeError, 'original failure'):
                run(self.source, self.output, self.root / 'work', self.root / 'target')
        summary = json.loads((self.output / 'summary.json').read_text())
        self.assertFalse(summary['passed'])
        self.assertFalse(summary['source_unchanged'])
        self.assertTrue(summary['source_check_failed'])
