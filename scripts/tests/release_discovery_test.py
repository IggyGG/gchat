"""Source-backed discovery regression: controller fixes retain app versions."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import release_prepare_test as preparation
from release_discovery import discover
from release_ledger import Ledger
from release_controller import qualification_ref, verify_inputs


class ControllerDiscoveryTests(unittest.TestCase):
    def test_failed_controller_ref_publication_reuses_one_intent_and_no_versions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, origin, git, config = preparation.PreparationTests().discovery_fixture(temporary)
            state = root / 'state'; state.mkdir(); ledger = Ledger(state / 'ledger.sqlite')
            try:
                discover(config, state, ledger); release = discover(config, state, ledger)
                baseline = ledger.manifest(release)
                stable = root / 'stable-coms.git'
                subprocess.run(['git', 'clone', '--bare', str(origin), str(stable)], check=True, capture_output=True)
                subprocess.run(['git', '-C', config['gcoms']['mirror'], 'remote', 'set-url', 'origin', str(stable)], check=True)
                (origin / 'scripts').mkdir()
                (origin / 'scripts/release_provider.py').write_text('# bounded provider scheduling\n')
                git('add', '.'); git('commit', '-m', 'controller change')
                self.assertEqual(discover(config, state, ledger), release)
                normal = subprocess.run
                def refuse(argv, **kwargs):
                    if 'push' in argv: raise subprocess.CalledProcessError(1, argv)
                    return normal(argv, **kwargs)
                with patch('release_discovery.subprocess.run', side_effect=refuse):
                    with self.assertRaises(subprocess.CalledProcessError): discover(config, state, ledger)
                ident = json.loads((state / 'controller-updates/desired.json').read_text())['id']
                path = state / 'controller-updates' / ident / 'intent.json'
                original = path.read_bytes()
                self.assertEqual(discover(config, state, ledger), release)
                self.assertEqual(path.read_bytes(), original)
                intent = json.loads(original)
                self.assertEqual(verify_inputs(intent, {p: config[p]['mirror'] for p in ('gchat', 'gcoms')}), baseline)
                self.assertEqual(git('rev-parse', qualification_ref(intent)), intent['sources']['gchat']['commit'])
                self.assertEqual(ledger.manifest(release), baseline)
                self.assertEqual(ledger.db.execute('SELECT COUNT(*) FROM candidates').fetchone()[0], 1)
                self.assertEqual(ledger.db.execute('SELECT COUNT(*) FROM effects').fetchone()[0], 0)
            finally: ledger.close()


if __name__ == '__main__': unittest.main()
