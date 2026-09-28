import copy
import importlib.util
from pathlib import Path
import sys
import unittest

scripts = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(scripts))
spec = importlib.util.spec_from_file_location('macos_network_retained', scripts / 'macos-network-retained.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class RetainedTests(unittest.TestCase):
    def test_exact_registered_failed_artifacts_only(self):
        for target, (run_id, artifact_id, sha) in module.ARTIFACTS.items():
            run = {'id': run_id, 'head_sha': module.SOURCE,
                   'head_repository': {'full_name': 'IggyGG/gchat'},
                   'path': '.github/workflows/macos-release.yml', 'event': 'workflow_dispatch',
                   'status': 'completed', 'conclusion': 'failure'}
            artifact = {'id': artifact_id, 'name': target, 'workflow_run': {'id': run_id},
                        'expired': False, 'digest': 'sha256:' + sha, 'size_in_bytes': 100}
            module.validate(target, run, artifact)
            for field, value in [('head_sha', '0' * 40), ('conclusion', 'success'),
                                 ('path', '.github/workflows/other.yml'), ('event', 'pull_request')]:
                altered = copy.deepcopy(run); altered[field] = value
                with self.assertRaises(ValueError): module.validate(target, altered, artifact)
            for field, value in [('expired', True), ('id', 1), ('digest', 'sha256:' + '0' * 64),
                                 ('size_in_bytes', 0), ('size_in_bytes', 513 * 1024**2)]:
                altered = copy.deepcopy(artifact); altered[field] = value
                with self.assertRaises(ValueError): module.validate(target, run, altered)
