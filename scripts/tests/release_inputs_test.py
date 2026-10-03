import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import copy
import hashlib
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_inputs import fingerprints
from release_discovery import coalesce_equivalent_queued
from release_automation_test import candidate
from release_ledger import Ledger
from release_pair import canonical


class QueuedInputTests(unittest.TestCase):
    def test_only_undispatched_equivalent_work_is_coalesced(self):
        for case in ('equivalent', 'changed-input', 'changed-policy', 'active',
                     'reserved-effect', 'manual', 'failed-baseline', 'other-platform'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                ledger = Ledger(Path(temporary) / 'ledger.sqlite')
                try:
                    before, after = candidate(), candidate(2)
                    for manifest in (before, after):
                        manifest['upstream'] = copy.deepcopy(manifest['sources'])
                    if case == 'manual':
                        del after['upstream']
                    if case == 'changed-policy':
                        after['policy']['profile'] = 99
                    for manifest in (before, after):
                        manifest['release_id'] = hashlib.sha256(canonical(
                            {k:v for k,v in manifest.items() if k != 'release_id'})).hexdigest()
                    first, second = ledger.add(before), ledger.add(after)
                    target = 'macos-aarch64'
                    ledger.transition(first, 'macos-x86_64' if case == 'other-platform' else target,
                                      'building')
                    if case == 'failed-baseline':
                        ledger.transition(first, target, 'failed', reason='retained failure')
                    if case == 'active':
                        ledger.transition(second, target, 'building')
                    if case == 'reserved-effect':
                        ledger.effect(second, target, 'build')
                    original_manifests = list(ledger.db.execute('SELECT manifest FROM candidates'))
                    def classified(roots, sources):
                        return {'artifacts': sources['gchat']['commit'] if case == 'changed-input' else 'same'}
                    with patch('release_inputs.fingerprints', side_effect=classified):
                        coalesce_equivalent_queued({p:{'mirror':p} for p in ('gchat','gcoms')}, ledger)
                    expected = 'superseded' if case == 'equivalent' else 'building' if case == 'active' else 'queued'
                    self.assertEqual(ledger.target(second, target)['state'], expected)
                    self.assertEqual(list(ledger.db.execute('SELECT manifest FROM candidates')), original_manifests)
                    self.assertEqual(ledger.target(second, target)['evidence'], None)
                    self.assertEqual(ledger.db.execute('SELECT COUNT(*) FROM latest').fetchone()[0], 0)
                    self.assertEqual(ledger.target(first, target)['state'],
                        'failed' if case == 'failed-baseline' else 'queued' if case == 'other-platform' else 'building')
                finally:
                    ledger.close()


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
            self.assertNotEqual(first['infrastructure'], second['infrastructure'])
            self.assertNotEqual(first['qualification'], second['qualification'])
            for path in ('release/downloads.json', 'scripts/website.py',
                         'scripts/release_inventory.py', 'scripts/release_sdk.py',
                         'scripts/macos-package.py', '.github/workflows/macos-package.yml',
                         '.github/workflows/macos-rollback.yml', 'scripts/macos-rollback.py',
                         '.github/workflows/release-tools-check.yml',
                         'scripts/acceptance_delivery.py', 'scripts/release_acceptance_delivery.py',
                         'release/automation/requirements.txt',
                         'marketing/play-store/retro-v1/listing.md',
                         'marketing/play-store/retro-v1/exports/feature.png',
                         'marketing/app-store/retro-v1/listing.json',
                         'marketing/app-store/retro-v1/publication.json',
                         'marketing/app-store/retro-v1/exports/ipad-01-conversation.jpg'):
                before = fingerprints(roots, sources)
                commit('gchat', path, 'reviewed non-application change')
                after = fingerprints(roots, sources)
                self.assertEqual(before['artifacts'], after['artifacts'])
                self.assertNotEqual(before['qualification'], after['qualification'])
            for project, path in [('gchat', 'new-unclassified-input'),
                                  ('gchat', 'marketing/play-store/retro-v1/new-input.js'),
                                  ('gchat', 'marketing/app-store/retro-v2/listing.json'),
                                  ('gchat', 'apps/client/src-tauri/icons/icon.png'),
                                  ('gchat', 'scripts/release_prepare.py'),
                                  ('gchat', 'release/publication.json'),
                                  ('gchat', '.github/workflows/windows-release.yml'),
                                  ('gcoms', 'crates/node/src/lib.rs')]:
                before = fingerprints(roots, sources)
                commit(project, path, 'changed')
                self.assertNotEqual(before['artifacts'], fingerprints(roots, sources)['artifacts'])
            for project,path in [('gchat','scripts/mobile_installed_journey.py'),
                                 ('gchat','scripts/release_compaction.py'),
                                 ('gchat','release/automation/compaction.yaml'),
                                 ('gchat','.github/workflows/mobile-acceptance.yml'),
                                 ('gchat','scripts/fixtures/ios-acceptance/AcceptanceTests.swift'),
                                 ('gchat','docs/evidence/stabilization-20261001/ios-build-allocation.json'),
                                 ('gchat','docs/evidence/stabilization-20261001/ios-passphrase-control.json'),
                                 ('gcoms','PLAN.md'),
                                 ('gcoms','docs/evidence/stabilization-20261001/durable-reopen.json'),
                                 ('gcoms','docs/evidence/stabilization-20261001/contact-request-window.json'),
                                 ('gcoms','docs/evidence/stabilization-20261001/windows-locked-storage-tests.json'),
                                 ('gcoms','docs/evidence/stabilization-20261001/sdk-size-policy.json'),
                                 ('gcoms','crates/file-transfer/README.md'),
                                 ('gcoms','docs/evidence/stabilization-20261001/sdk-native-90d7eac.json')]:
                before=fingerprints(roots,sources)
                commit(project,path,'reviewed qualification change')
                after=fingerprints(roots,sources)
                self.assertEqual(before['artifacts'],after['artifacts'])
                self.assertNotEqual(before['qualification'],after['qualification'])
                if project == 'gcoms' or path.startswith('docs/'):
                    self.assertEqual(before['infrastructure'],after['infrastructure'])
                elif path in ('.github/workflows/mobile-acceptance.yml',
                              'scripts/release_compaction.py', 'release/automation/compaction.yaml'):
                    self.assertNotEqual(before['infrastructure'],after['infrastructure'])
            for project,path in [('gchat','scripts/mobile-build-new.py'),
                                 ('gchat','.github/workflows/ios-release.yml'),
                                 ('gchat','scripts/android-build.py'),
                                 ('gchat','docs/evidence/stabilization-20261001/new-unreviewed.json'),
                                 ('gcoms','docs/evidence/stabilization-20261001/new-unreviewed.json'),
                                 ('gcoms','docs/evidence/unreviewed.json')]:
                before=fingerprints(roots,sources)
                commit(project,path,'unclassified or packaging change')
                after=fingerprints(roots,sources)
                self.assertNotEqual(before['artifacts'],after['artifacts'])
                if project == 'gcoms':
                    self.assertNotEqual(before['infrastructure'],after['infrastructure'])
            if os.name != 'nt':
                before = fingerprints(roots, sources)
                subprocess.run(['git', '-C', str(roots['gchat']), 'update-index', '--chmod=+x',
                                'new-unclassified-input'], check=True)
                subprocess.run(['git', '-C', str(roots['gchat']), '-c', 'user.name=Fixture',
                    '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'mode'], check=True)
                sources['gchat']['commit'] = subprocess.check_output(
                    ['git', '-C', str(roots['gchat']), 'rev-parse', 'HEAD'], text=True).strip()
                self.assertNotEqual(before['artifacts'], fingerprints(roots, sources)['artifacts'])
