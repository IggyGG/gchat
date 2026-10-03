import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_macos_recovery as worker


class MacRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.rule = json.loads(worker.REGISTRY.read_text())['recoveries'][0]
        self.manifest = {'release_id': self.rule['release_id'], 'sources': self.rule['sources']}
        self.target = self.rule['target']
        common = {'event': 'workflow_dispatch', 'head_repository': {'full_name': 'IggyGG/gchat'}}
        self.original = {**common, 'id': self.rule['original_run'], 'status': 'completed', 'conclusion': 'failure',
                         'head_sha': self.rule['sources']['gchat']['commit'], 'path': '.github/workflows/macos-release.yml'}
        self.followup = {**common, 'id': self.rule['followup_run'], 'status': 'completed', 'conclusion': 'success',
                         'head_sha': self.rule['controller_commit'], 'path': '.github/workflows/macos-package.yml',
                         'display_title': 'Forgejo macOS package ' + self.rule['request_id']}
        self.artifact = {'id': 123, 'name': self.target + '-package', 'expired': False, 'digest': 'sha256:' + 'a' * 64,
                         'size_in_bytes': 100, 'workflow_run': {'id': self.followup['id'], 'head_sha': self.followup['head_sha']}}

    def test_exact_source_registration_and_provider_preserve_failure(self):
        original = copy.deepcopy(self.original)
        self.assertEqual(worker.rule_for(self.manifest, self.target), self.rule)
        self.assertTrue(worker.validate_runs(self.manifest, self.target, self.rule, self.original, self.followup))
        self.assertEqual(self.original, original)
        worker.validate_artifact(self.artifact, self.followup, self.target)

    def test_pending_provider_does_not_collect_or_dispatch_another_run(self):
        with tempfile.TemporaryDirectory() as root:
            pending = {**self.followup, 'status': 'queued', 'conclusion': None}
            with patch('release_jobs.gh', return_value=pending) as provider:
                self.assertIsNone(worker.collect(self.manifest, self.target, Path(root), self.original, self.rule))
            provider.assert_called_once_with('actions/runs/' + str(self.rule['followup_run']))
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_other_source_or_duplicate_registration_is_rejected(self):
        self.assertIsNone(worker.rule_for({**self.manifest, 'release_id': '0' * 64}, self.target))
        self.assertIsNone(worker.rule_for(self.manifest, 'macos-aarch64'))
        with self.assertRaisesRegex(ValueError, 'source or target'):
            worker.rule_for({**self.manifest, 'sources': {}}, self.target)
        with tempfile.TemporaryDirectory() as root:
            registry = Path(root) / 'registry.json'
            registry.write_text(json.dumps({'schema': 1, 'recoveries': [self.rule, self.rule]}))
            with patch.dict(os.environ, {'GCHAT_NATIVE_RECOVERIES': str(registry)}):
                with self.assertRaisesRegex(ValueError, 'ambiguous'):
                    worker.rule_for(self.manifest, self.target)

    def test_wrong_runs_recipes_repositories_and_failed_followups_are_rejected(self):
        for which in ('original', 'followup'):
            for key, value in (('id', 1), ('head_sha', '0' * 40), ('path', '.github/workflows/other.yml'),
                               ('event', 'pull_request'), ('head_repository', {'full_name': 'other/gchat'})):
                with self.subTest(which=which, key=key):
                    old, new = copy.deepcopy(self.original), copy.deepcopy(self.followup)
                    (old if which == 'original' else new)[key] = value
                    with self.assertRaises(ValueError):
                        worker.validate_runs(self.manifest, self.target, self.rule, old, new)
        for result in ('failure', 'cancelled', 'timed_out'):
            with self.subTest(result=result), self.assertRaisesRegex(ValueError, 'did not pass'):
                worker.validate_runs(self.manifest, self.target, self.rule, self.original,
                                     {**self.followup, 'conclusion': result})
        with self.assertRaisesRegex(ValueError, 'request differs'):
            worker.validate_runs(self.manifest, self.target, self.rule, self.original,
                                 {**self.followup, 'display_title': 'another request'})

    def test_other_artifacts_expired_archives_and_missing_digests_are_rejected(self):
        for key, value in (('name', 'macos-aarch64-package'), ('expired', True), ('digest', ''),
                           ('size_in_bytes', 0), ('size_in_bytes', 1024 ** 3 + 1),
                           ('workflow_run', {'id': 1, 'head_sha': self.followup['head_sha']})):
            with self.subTest(key=key), self.assertRaises(ValueError):
                worker.validate_artifact({**self.artifact, key: value}, self.followup, self.target)

    def test_extraction_must_match_all_provider_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root); archive = root / 'native.zip'; destination = root / 'native'; destination.mkdir()
            path = destination / 'report.json'; path.write_text('{"passed":false}')
            with zipfile.ZipFile(archive, 'w') as bundle:
                bundle.write(path, path.name)
            worker.verify_extraction(archive, destination)
            path.write_text('{"passed":true}')
            with self.assertRaisesRegex(ValueError, 'immutable provider ZIP'):
                worker.verify_extraction(archive, destination)

    def test_extraction_link_cannot_borrow_an_outside_receipt(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root); destination = root / 'native'; destination.mkdir()
            outside = root / 'outside'; outside.write_text('original')
            archive = root / 'native.zip'
            with zipfile.ZipFile(archive, 'w') as bundle:
                bundle.writestr('report.json', 'original')
            (destination / 'report.json').symlink_to(outside)
            with self.assertRaisesRegex(ValueError, 'unsafe path'):
                worker.verify_extraction(archive, destination)
