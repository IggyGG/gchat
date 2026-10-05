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
        self.root = Path(temporary.name)
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

    def test_rejects_reference_outside_the_fixture(self):
        for reference in ('../outside', '/outside'):
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
