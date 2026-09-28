"""Retained follow-up proofs must not admit another artifact or failed run."""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_recovery import WINDOWS36, validate_runs
from release_automation_test import candidate


class RetainedRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.manifest = candidate()
        self.manifest['release_id'] = WINDOWS36['release_id']
        common = {'event': 'workflow_dispatch', 'status': 'completed',
                  'head_repository': {'full_name': 'IggyGG/gchat'}}
        self.original = {**common, 'id': WINDOWS36['original_run'], 'conclusion': 'failure',
                         'head_sha': self.manifest['sources']['gchat']['commit'],
                         'path': '.github/workflows/windows-release.yml'}
        self.followup = {**common, 'id': WINDOWS36['followup_run'], 'conclusion': 'success',
                        'head_sha': WINDOWS36['controller_commit'],
                        'path': '.github/workflows/windows-verify.yml',
                        'display_title': 'Windows retained installer verification ' + WINDOWS36['request_id']}

    def test_exact_followup_preserves_original_failure(self):
        before = copy.deepcopy(self.original)
        validate_runs(self.manifest, 'windows-x86_64', self.original, self.followup)
        self.assertEqual(self.original, before)
        self.assertEqual(self.original['conclusion'], 'failure')

    def test_other_runs_sources_workflows_and_failed_followups_rejected(self):
        for which in ('original', 'followup'):
            for key, value in [('id', 1), ('head_sha', '0'*40), ('path', '.github/workflows/other.yml'),
                               ('event', 'pull_request'), ('status', 'in_progress'),
                               ('head_repository', {'full_name': 'another/gchat'}),
                               ('conclusion', 'cancelled')]:
                with self.subTest(which=which, field=key):
                    original, followup = copy.deepcopy(self.original), copy.deepcopy(self.followup)
                    (original if which == 'original' else followup)[key] = value
                    with self.assertRaises(ValueError):
                        validate_runs(self.manifest, 'windows-x86_64', original, followup)
        with self.assertRaises(ValueError):
            validate_runs(self.manifest, 'windows-x86_64', self.original,
                          {**self.followup, 'display_title': 'unrelated'})

    def test_another_candidate_or_platform_cannot_borrow_followup(self):
        for platform in ('android', 'ios', 'linux-x86_64', 'macos-x86_64'):
            with self.subTest(platform=platform), self.assertRaises(ValueError):
                validate_runs(self.manifest, platform, self.original, self.followup)
        with self.assertRaises(ValueError):
            validate_runs({**self.manifest, 'release_id': '0'*64}, 'windows-x86_64', self.original, self.followup)
