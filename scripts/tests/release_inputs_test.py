import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_inputs import fingerprints


class InputTests(unittest.TestCase):
    def test_reviewed_tooling_does_not_rebuild_but_unknown_and_modes_do(self):
        with tempfile.TemporaryDirectory() as directory:
            roots, sources = {}, {}
            def commit(project, path, text):
                root = roots[project]
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text)
                subprocess.run(['git', '-C', str(root), 'add', '.'], check=True, capture_output=True)
                subprocess.run(['git', '-C', str(root), '-c', 'user.name=Fixture',
                    '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'],
                    check=True, capture_output=True)
                sources[project] = {'commit': subprocess.check_output(
                    ['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()}
            for project in ('gchat', 'gcoms'):
                roots[project] = Path(directory) / project
                subprocess.run(['git', 'init', '-q', str(roots[project])], check=True)
                commit(project, 'Cargo.lock', 'pinned')
            first = fingerprints(roots, sources)
            commit('gchat', 'scripts/release_coordinator.py', '# new controller')
            second = fingerprints(roots, sources)
            self.assertEqual(first['artifacts'], second['artifacts'])
            self.assertNotEqual(first['qualification'], second['qualification'])
            for project, path in [('gchat', 'new-unclassified-input'),
                                  ('gchat', 'scripts/release_prepare.py'),
                                  ('gchat', '.github/workflows/windows-release.yml'),
                                  ('gcoms', 'crates/node/src/lib.rs')]:
                before = fingerprints(roots, sources)
                commit(project, path, 'changed')
                self.assertNotEqual(before['artifacts'], fingerprints(roots, sources)['artifacts'])
            if os.name != 'nt':
                before = fingerprints(roots, sources)
                subprocess.run(['git', '-C', str(roots['gchat']), 'update-index', '--chmod=+x',
                                'new-unclassified-input'], check=True)
                subprocess.run(['git', '-C', str(roots['gchat']), '-c', 'user.name=Fixture',
                    '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'mode'], check=True)
                sources['gchat']['commit'] = subprocess.check_output(
                    ['git', '-C', str(roots['gchat']), 'rev-parse', 'HEAD'], text=True).strip()
                self.assertNotEqual(before['artifacts'], fingerprints(roots, sources)['artifacts'])
