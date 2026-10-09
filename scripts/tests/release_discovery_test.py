"""Source-backed discovery regression: controller fixes retain app versions."""
from contextlib import contextmanager
import hashlib
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
from release_pair import canonical, identity
from release_prepare import prepare


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


    @contextmanager
    def intel_successor(self, temporary, *, changed_chat_runtime=False):
        root, origin, git, config = preparation.PreparationTests().discovery_fixture(temporary)
        state = root / 'state'; state.mkdir()
        ledger = Ledger(state / 'ledger.sqlite')
        discover(config, state, ledger)
        release = discover(config, state, ledger)
        deployed = ledger.manifest(release)
        coms = root / 'coms-origin'
        subprocess.run(['git', 'clone', str(origin), str(coms)], check=True, capture_output=True)
        def coms_git(*args):
            return subprocess.check_output(['git', '-C', str(coms), *args], text=True,
                                           stderr=subprocess.PIPE).strip()
        coms_git('config', 'user.name', 'Fixture'); coms_git('config', 'user.email', 'fixture@example.invalid')
        subprocess.run(['git', '-C', config['gcoms']['mirror'], 'remote', 'set-url', 'origin', str(coms)], check=True)
        fixture = coms / 'crates/node/src/node/persist/machine_scope_tests.rs'
        fixture.parent.mkdir(parents=True); fixture.write_text('// corrected checkpoint fixture\n')
        coms_git('add', '.'); coms_git('commit', '-m', 'test-only correction')
        subprocess.run(['git', '-C', config['gcoms']['mirror'], 'fetch', 'origin',
                        'refs/heads/main:refs/heads/main'], check=True, capture_output=True)
        if changed_chat_runtime:
            (origin / 'new-runtime-input').write_text('runtime changed since deployed baseline')
            git('add', '.'); git('commit', '-m', 'changed runtime')
            subprocess.run(['git', '-C', config['gchat']['mirror'], 'fetch', 'origin',
                            'refs/heads/main:refs/heads/main'], check=True, capture_output=True)
        upstream = {'gchat': identity(origin), 'gcoms': identity(coms)}
        versions = dict(deployed['versions'], **{p: '1.0.2' for p in
            ('linux-x86_64', 'macos-aarch64', 'macos-x86_64', 'windows-x86_64', 'sdk')})
        versions.update(android='3', ios='1.1.1')
        branch = 'refs/heads/release/gchat-' + 'b' * 20
        prepared = prepare(config['gchat']['mirror'], upstream['gchat']['commit'],
                           upstream['gcoms']['commit'], versions, branch)
        latest = {'schema': 1, 'sources': dict(upstream, gchat=identity(config['gchat']['mirror'], prepared)),
                  'upstream': upstream, 'versions': versions, 'policy': deployed['policy'],
                  'selected_platforms': ['macos-x86_64'], 'deployment_baseline': release,
                  'refs': {'gchat': branch, 'gcoms': branch}}
        latest['release_id'] = hashlib.sha256(canonical(latest)).hexdigest()
        ledger.add(latest)
        desired = state / 'deployment/desired.json'; desired.parent.mkdir(parents=True)
        desired.write_bytes(canonical({'release_id': release}))
        journal = state / 'deployment' / release / 'journal.json'; journal.parent.mkdir()
        journal.write_bytes(canonical({'state': 'deployed', 'sources': deployed['sources']}))
        (origin / 'scripts').mkdir()
        (origin / 'scripts/release_provider.py').write_text('# new controller-only scheduling\n')
        git('add', '.'); git('commit', '-m', 'controller-only update')
        try:
            yield root, state, ledger, config, deployed, latest, coms, coms_git
        finally:
            ledger.close()

    def test_intel_successor_controller_update_targets_its_explicit_deployed_baseline(self):
        with tempfile.TemporaryDirectory() as temporary, self.intel_successor(temporary) as values:
            root, state, ledger, config, deployed, latest, _, _ = values
            candidates = list(ledger.db.execute('SELECT manifest FROM candidates ORDER BY seq'))
            versions = [tuple(r) for r in ledger.db.execute('SELECT * FROM versions ORDER BY platform,version')]
            for _ in range(3):
                self.assertEqual(discover(config, state, ledger), latest['release_id'])
            ident = json.loads((state / 'controller-updates/desired.json').read_text())['id']
            intent = json.loads((state / 'controller-updates' / ident / 'intent.json').read_text())
            self.assertEqual(intent['baseline'], deployed)
            self.assertEqual(intent['sources']['gcoms'], deployed['sources']['gcoms'])
            self.assertNotEqual(intent['sources']['gcoms'], latest['sources']['gcoms'])
            self.assertEqual(intent['sources']['gchat'], identity(config['gchat']['mirror'], 'main'))
            self.assertEqual(verify_inputs(intent, {p: config[p]['mirror'] for p in ('gchat', 'gcoms')}), deployed)
            self.assertEqual(ledger.manifest(latest['release_id']), latest)
            self.assertEqual([r[0] for r in ledger.db.execute('SELECT manifest FROM candidates ORDER BY seq')], [r[0] for r in candidates])
            self.assertEqual([tuple(r) for r in ledger.db.execute('SELECT * FROM versions ORDER BY platform,version')], versions)
            self.assertEqual(ledger.db.execute('SELECT COUNT(*) FROM effects').fetchone()[0], 0)
            self.assertEqual(len(list((state / 'controller-updates').glob('*/intent.json'))), 1)

    def test_intel_baseline_requires_selected_and_deployed_original_sources(self):
        for mismatch in ('desired', 'state', 'sources'):
            with self.subTest(mismatch=mismatch), tempfile.TemporaryDirectory() as temporary, self.intel_successor(temporary) as values:
                _, state, ledger, config, deployed, latest, _, _ = values
                if mismatch == 'desired':
                    (state / 'deployment/desired.json').write_bytes(canonical({'release_id': latest['release_id']}))
                else:
                    value = {'state': 'deployed', 'sources': deployed['sources']}
                    value[mismatch] = 'deploying' if mismatch == 'state' else latest['sources']
                    (state / 'deployment' / deployed['release_id'] / 'journal.json').write_bytes(canonical(value))
                for _ in range(2):
                    self.assertEqual(discover(config, state, ledger), latest['release_id'])
                self.assertFalse((state / 'controller-updates/desired.json').exists())
                self.assertEqual(ledger.db.execute('SELECT COUNT(*) FROM candidates').fetchone()[0], 2)

    def test_controller_pair_cannot_hide_application_change_since_deployed_baseline(self):
        with tempfile.TemporaryDirectory() as temporary, self.intel_successor(temporary, changed_chat_runtime=True) as values:
            _, state, ledger, config, _, latest, _, _ = values
            self.assertEqual(discover(config, state, ledger), latest['release_id'])
            with self.assertRaisesRegex(ValueError, 'changes deployed application'):
                discover(config, state, ledger)
            self.assertFalse((state / 'controller-updates/desired.json').exists())
            self.assertEqual(ledger.db.execute('SELECT COUNT(*) FROM candidates').fetchone()[0], 2)

    def test_new_main_gcoms_runtime_change_follows_normal_application_discovery(self):
        with tempfile.TemporaryDirectory() as temporary, self.intel_successor(temporary) as values:
            _, state, ledger, config, _, latest, coms, git = values
            (coms / 'new-runtime-input').write_text('real production change')
            git('add', '.'); git('commit', '-m', 'new GComs runtime')
            self.assertIsNone(discover(config, state, ledger))
            release = discover(config, state, ledger)
            self.assertNotEqual(release, latest['release_id'])
            self.assertEqual(ledger.manifest(release)['sources']['gcoms'], identity(coms))
            self.assertEqual(ledger.manifest(latest['release_id']), latest)
            self.assertFalse((state / 'controller-updates/desired.json').exists())
            self.assertEqual(ledger.db.execute('SELECT COUNT(*) FROM candidates').fetchone()[0], 3)


if __name__ == '__main__': unittest.main()
