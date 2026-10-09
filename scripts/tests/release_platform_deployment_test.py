"""Intel-only provenance must not manufacture deployment or load qualification."""
import copy
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_platform_deployment as reuse
from release_pair import canonical, identity, validate
from release_prepare import prepare
from release_publish import job


class PlatformDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(self.temp)
        self.state = self.root / 'state'
        self.state.mkdir()
        self.repositories = {name: self.root / name for name in ('gchat', 'gcoms')}
        for root in self.repositories.values():
            root.mkdir()
            self.git(root, 'init', '-q')
            self.git(root, 'config', 'user.name', 'Fixture')
            self.git(root, 'config', 'user.email', 'fixture@example.invalid')
        chat, coms = self.repositories.values()
        self.write(chat / 'apps/client/src-tauri/tauri.conf.json',
                   {'version': '0.1.0', 'bundle': {'android': {'versionCode': 1}}})
        self.write(chat / 'release/publication.json', {'version': '0.1.0'})
        self.text(chat / 'apps/client/src-tauri/Cargo.toml', '[package]\nname = "gchat-desktop"\nversion = "0.1.0"\n')
        self.text(chat / 'apps/client/src-tauri/Cargo.lock', '[[package]]\nname = "gchat-desktop"\nversion = "0.1.0"\n')
        self.text(chat / 'crates/core/src/lib.rs', '// unchanged production input\n')
        self.text(coms / 'crates/node/src/node/persist.rs',
                  '#[cfg(test)]\nmod tests {\ninclude!("persist/machine_scope_tests.rs");\n}\n')
        self.fixture = coms / 'crates/node/src/node/persist/machine_scope_tests.rs'
        self.text(self.fixture, '// original fixture\n')
        self.text(coms / 'crates/node/src/node/direct.rs', '// unchanged production input\n')
        self.old_upstream = {name: self.commit(root) for name, root in self.repositories.items()}
        self.old = self.manifest(self.old_upstream, 1)
        self.text(self.fixture, '// corrected shutdown checkpoint fixture\n')
        self.new_upstream = dict(self.old_upstream, gcoms=self.commit(coms))
        self.new = self.manifest(self.new_upstream, 2, self.old['release_id'])
        with closing(sqlite3.connect(self.state / 'ledger.sqlite')) as db, db:
            db.execute('CREATE TABLE candidates (id TEXT PRIMARY KEY, manifest TEXT)')
            db.execute('INSERT INTO candidates VALUES (?, ?)',
                       (self.old['release_id'], json.dumps(self.old)))
        self.inventory = {'targets': [{'id': 'relay-1'}, {'id': 'controller'}]}
        self.config = {'discovery': {p: {'mirror': str(r)} for p, r in self.repositories.items()},
                       'deployment_file': str(self.root / 'deployment.json')}
        self.write(Path(self.config['deployment_file']), self.inventory)
        self.desired = self.state / 'deployment/desired.json'
        self.write(self.desired, {'release_id': self.old['release_id']})
        self.journal = self.state / 'deployment' / self.old['release_id'] / 'journal.json'
        self.journal_data = {'state': 'deployed', 'sources': self.old['sources'], 'observed_at': 1000,
            'revision': hashlib.sha256(canonical(self.inventory)).hexdigest(),
            'targets': {t['id']: {'observed': {'healthy': True, 'matches': True}}
                        for t in self.inventory['targets']}}
        self.write(self.journal, self.journal_data)
        self.receipt = job(self.state, self.old, 'linux-x86_64', 'relay_load') / 'receipt.json'
        self.text(self.receipt.parent / 'traffic.log', 'retained qualified baseline fixture\n')
        self.report = {'schema': 1, 'release_id': self.old['release_id'], 'sources': self.old['sources'],
            'platform': 'linux-x86_64', 'stage': 'relay_load', 'passed': True,
            'source_unchanged': True, 'relay_load_verified': True,
            'evidence': [{'path': 'traffic.log', 'sha256': hashlib.sha256(
                (self.receipt.parent / 'traffic.log').read_bytes()).hexdigest()}]}
        self.write(self.receipt, self.report)
        self.load = self.state / 'relay-load' / self.old['release_id'] / 'status.json'
        self.load_data = {'state': 'passed', 'release_id': self.old['release_id'],
                          'sources': self.old['sources'],
                          'receipt_sha256': hashlib.sha256(self.receipt.read_bytes()).hexdigest()}
        self.write(self.load, self.load_data)
        # Inventory overlay behavior has its own suite. This fixture exercises
        # real source preparation, ledger reads and retained receipt verification.
        self.enterContext(patch('release_control.deployment_config', side_effect=lambda _s, _m, c: c))

    @staticmethod
    def git(root, *args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True,
                                       stderr=subprocess.PIPE).strip()

    @staticmethod
    def text(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)

    def write(self, path, value):
        self.text(path, canonical(value).decode())

    def commit(self, root):
        self.git(root, 'add', '.')
        self.git(root, 'commit', '-qm', 'source fixture')
        return identity(root)

    def manifest(self, upstream, number, baseline=None):
        versions = {p: f'0.1.{number}' for p in
                    ('linux-x86_64', 'macos-aarch64', 'macos-x86_64', 'windows-x86_64', 'ios')}
        versions['android'] = str(number)
        versions['ios'] = f'1.0.{number}'
        ref = 'refs/heads/release/gchat-' + str(number) * 16
        prepared = prepare(self.repositories['gchat'], upstream['gchat']['commit'],
                           upstream['gcoms']['commit'], versions, ref)
        value = {'schema': 1, 'sources': {'gchat': identity(self.repositories['gchat'], prepared),
                 'gcoms': upstream['gcoms']}, 'upstream': upstream, 'versions': versions,
                 'policy': {'native': 'required', 'carrier_profile': 'gchat-covered',
                            'required_checks': ['authentication', 'durable_delivery', 'files',
                                                'reopen_recovery', 'upgrade_rollback', 'relay_compatibility'],
                            'file_qualification': {'mode': 'file-recovery', 'bytes': 16777216,
                                                   'completion_seconds': 360, 'total_seconds': 600}}, 'refs': {'gchat': ref, 'gcoms': 'refs/heads/main'}}
        if baseline:
            value.update(selected_platforms=['macos-x86_64'], deployment_baseline=baseline)
        return self.seal(value)

    @staticmethod
    def seal(value):
        value = json.loads(json.dumps(value))
        value.pop('release_id', None)
        value['release_id'] = hashlib.sha256(canonical(value)).hexdigest()
        return validate(value)

    def ready(self, value=None, now=1000):
        return reuse.ready(self.state, self.config, object(), value or self.new, now=now)

    def test_exact_intel_successor_retains_original_journal_load_and_ledger(self):
        protected = [self.journal, self.desired, self.load, self.receipt, self.state / 'ledger.sqlite']
        original = {p: p.read_bytes() for p in protected}
        self.assertTrue(self.ready())
        old, proof = reuse.retained(self.state, self.new, now=1001)
        self.assertEqual(old, self.old)
        self.assertEqual(proof['changed_paths']['gcoms'], ['crates/node/src/node/persist/machine_scope_tests.rs'])
        self.assertEqual(proof['baseline_journal_sha256'], hashlib.sha256(original[self.journal]).hexdigest())
        self.assertEqual(proof['relay_load_receipt_sha256'], self.load_data['receipt_sha256'])
        self.assertEqual({p: p.read_bytes() for p in protected}, original)
        self.assertFalse((self.state / 'deployment' / self.new['release_id']).exists())
        self.assertFalse((self.state / 'relay-load' / self.new['release_id']).exists())

    def test_only_explicit_intel_platform_and_same_policy_are_admitted(self):
        for selected in (None, [], ['linux-x86_64'], ['macos-x86_64', 'macos-aarch64']):
            value = copy.deepcopy(self.new)
            value['selected_platforms'] = selected
            with self.subTest(selected=selected):
                self.assertFalse(self.ready(value))
        value = copy.deepcopy(self.new)
        value['policy'] = {'native': 'optional'}
        self.assertFalse(self.ready(value))
        value = copy.deepcopy(self.new)
        value['deployment_baseline'] = value['release_id']
        self.assertFalse(self.ready(value))

    def test_runtime_lock_unknown_path_or_fixture_rename_requires_normal_deployment(self):
        for project, path in (
            ('gcoms', 'crates/node/src/node/direct.rs'), ('gcoms', 'Cargo.lock'),
            ('gcoms', 'scripts/unreviewed.py'), ('gcoms', 'crates/node/src/node/persist/renamed.rs'),
            ('gchat', 'crates/core/src/lib.rs'), ('gchat', 'apps/client/src-tauri/Cargo.lock')):
            with self.subTest(project=project, path=path):
                root = self.repositories[project]
                before = self.new_upstream[project]['commit']
                self.git(root, 'checkout', '--detach', before)
                self.text(root / path, '// changed production or unknown input\n')
                value = copy.deepcopy(self.new)
                value['upstream'][project] = self.commit(root)
                with self.assertRaisesRegex(ValueError, 'production inputs changed'):
                    reuse.qualify_sources(self.repositories, value, self.old)

    def test_source_tree_and_version_preparation_must_match(self):
        mutations = (
            lambda v: v['upstream']['gcoms'].update(tree='f' * 40),
            lambda v: v['sources']['gcoms'].update(commit='f' * 40),
            lambda v: v['sources']['gchat'].update(commit=self.old['sources']['gchat']['commit']),
            lambda v: v['sources']['gchat'].update(tree='f' * 40),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                value = copy.deepcopy(self.new)
                mutate(value)
                with self.assertRaises(ValueError):
                    reuse.qualify_sources(self.repositories, value, self.old)

    def test_fixture_must_stay_inside_unchanged_cfg_test_parent(self):
        root = self.repositories['gcoms']
        self.text(root / 'crates/node/src/node/persist.rs',
                  'mod tests { include!("persist/machine_scope_tests.rs"); }\n')
        value = copy.deepcopy(self.new)
        value['upstream']['gcoms'] = self.commit(root)
        with self.assertRaisesRegex(ValueError, 'production inputs changed'):
            reuse.qualify_sources(self.repositories, value, self.old)

    def test_fresh_healthy_exact_inventory_is_mandatory(self):
        changes = (
            lambda j: j.update(observed_at=699), lambda j: j.update(observed_at=1001),
            lambda j: j.update(state='deploying'), lambda j: j.update(revision='f' * 64),
            lambda j: j.update(sources=self.new['sources']),
            lambda j: j['targets'].pop('controller'),
            lambda j: j['targets']['controller']['observed'].update(healthy=False),
            lambda j: j['targets']['controller']['observed'].update(matches=False),
        )
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                value = copy.deepcopy(self.journal_data)
                change(value)
                self.write(self.journal, value)
                self.assertFalse(self.ready())
        self.write(self.journal, self.journal_data)
        self.write(self.desired, {'release_id': self.new['release_id']})
        self.assertFalse(self.ready())

    def test_retained_qualified_load_and_original_evidence_hash_are_required(self):
        for field, changed in (('state', 'running'), ('release_id', self.new['release_id']),
                               ('sources', self.new['sources']), ('receipt_sha256', 'f' * 64)):
            with self.subTest(field=field):
                self.write(self.load, dict(self.load_data, **{field: changed}))
                self.assertFalse(self.ready())
        self.write(self.load, self.load_data)
        self.write(self.receipt, dict(self.report, relay_load_verified=False))
        self.assertFalse(self.ready())
        self.write(self.receipt, self.report)
        self.text(self.receipt.parent / 'traffic.log', 'modified retained evidence\n')
        self.assertFalse(self.ready())

    def test_reuse_proof_expires_and_cannot_bind_another_source_pair(self):
        self.assertTrue(self.ready())
        with self.assertRaisesRegex(ValueError, 'stale'):
            reuse.retained(self.state, self.new, now=1301)
        with self.assertRaisesRegex(ValueError, 'stale'):
            reuse.retained(self.state, self.new, now=999)
        path = reuse.evidence_path(self.state, self.new)
        proof = json.loads(path.read_text())
        proof['sources'] = self.old['sources']
        self.write(path, proof)
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            reuse.retained(self.state, self.new, now=1001)


    def compatibility_proof(self):
        self.assertTrue(self.ready())
        _, deployment = reuse.retained(self.state, self.new, now=1000)
        proof = {'schema': 1, 'passed': True, 'release_id': self.new['release_id'],
                 'sources': self.new['sources'], 'platform': 'macos-x86_64', 'completed_at': 1000,
                 'carrier_profile': self.new['policy']['carrier_profile'],
                 'checks': {key: True for key in self.new['policy']['required_checks']},
                 'rollback_state_compatible': True, 'deployment_reuse_sha256': reuse.binding(deployment),
                 'relays': [{'id': f'relay-{index}', 'healthy': True,
                             'gcoms_commit': self.old['sources']['gcoms']['commit'],
                             'carrier_profile': self.new['policy']['carrier_profile']} for index in range(8)],
                 'file_check': {'mode': 'file-recovery', 'bytes': 16777216,
                                'completion_elapsed_seconds': 100, 'total_elapsed_seconds': 150,
                                'source_sha256': 'f' * 64, 'export_sha256': 'f' * 64,
                                **{key: True for key in ('abrupt_stop', 'verified_pieces_retained',
                                    'same_identity', 'authenticated_chat_ack', 'hash_verified_after_reopen',
                                    'cleanup_complete')}}}
        return proof, deployment

    def test_compatibility_binding_survives_fresh_observation_but_not_provenance_change(self):
        from release_compatibility import verify
        proof, first = self.compatibility_proof()
        self.write(self.journal, dict(self.journal_data, observed_at=1100))
        self.assertTrue(self.ready(now=1100))
        _, fresh = reuse.retained(self.state, self.new, now=1100)
        self.assertNotEqual(first['baseline_journal_sha256'], fresh['baseline_journal_sha256'])
        self.assertNotEqual(first['observed_at'], fresh['observed_at'])
        self.assertEqual(reuse.binding(first), reuse.binding(fresh))
        self.assertEqual(verify(proof, self.new, 1100, 'macos-x86_64', fresh), proof)
        for key in ('inventory_revision', 'relay_load_receipt_sha256'):
            changed = dict(fresh, **{key: 'f' * 64})
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'deployment provenance'):
                verify(proof, self.new, 1100, 'macos-x86_64', changed)

    def test_compatibility_requires_actual_baseline_relays_and_fresh_separate_proof(self):
        from release_compatibility import verify
        proof, deployment = self.compatibility_proof()
        wrong_relays = copy.deepcopy(proof)
        for relay in wrong_relays['relays']:
            relay['gcoms_commit'] = self.new['sources']['gcoms']['commit']
        with self.assertRaisesRegex(ValueError, 'relay observations'):
            verify(wrong_relays, self.new, 1000, 'macos-x86_64', deployment)
        for wrong in (None, dict(deployment, passed=False), dict(deployment, observed_at=699),
                      dict(deployment, baseline_release_id='f' * 64),
                      dict(deployment, sources=self.old['sources'])):
            with self.subTest(proof=wrong is None), self.assertRaisesRegex(ValueError, 'deployment provenance'):
                verify(proof, self.new, 1000, 'macos-x86_64', wrong)
        with self.assertRaisesRegex(ValueError, 'deployment provenance'):
            verify(proof, self.new, 1000, 'linux-x86_64', deployment)

    def native_acceptance_fixture(self, work, mutation=None):
        import release_acceptance as acceptance
        from release_acceptance_test import fixture
        _, inputs, report, rollback, network = fixture()
        target = 'macos-x86_64'
        request = hashlib.sha256(work.name.encode()).hexdigest()
        inputs['target'] = target
        inputs['current']['sources'] = {k: v['commit'] for k, v in self.new['sources'].items()}
        inputs['baseline']['sources'] = {k: v['commit'] for k, v in self.old['sources'].items()}
        report.update(platform=target, sources=self.new['sources'], release_id=self.new['release_id'], completed_at=1000)
        for name in ('current', 'baseline'):
            report['artifacts'][name]['sources'] = inputs[name]['sources']
        network['inputs']['sources'] = self.new['sources']
        if mutation:
            mutation(report, network)
        work.mkdir()
        self.write(work / 'acceptance-intent.json', {'request': request, 'sources': self.new['sources'],
                   'target': target, 'inputs': inputs, 'cleaned': True})
        with zipfile.ZipFile(work / 'acceptance.zip', 'w') as archive:
            for path, value in (('report.json', report), ('rollback/report.json', rollback),
                                ('network/report.json', network)):
                archive.writestr(path, canonical(value))
        artifact = {'id': 2, 'name': 'acceptance-' + request, 'expired': False,
                    'digest': 'sha256:' + acceptance.digest(work / 'acceptance.zip'),
                    'size_in_bytes': (work / 'acceptance.zip').stat().st_size}
        run = {'id': 1, 'status': 'completed', 'conclusion': 'success',
               'head_sha': self.new['sources']['gchat']['commit'], 'event': 'workflow_dispatch',
               'path': '.github/workflows/native-acceptance.yml', 'display_title': acceptance.PREFIX + request,
               'head_repository': {'full_name': 'IggyGG/gchat'}}
        def api(path, **kwargs):
            self.assertFalse(kwargs)
            if path.startswith('actions/workflows/'):
                return {'workflow_runs': [run]}
            self.assertEqual(path, 'actions/runs/1/artifacts?per_page=100')
            return {'artifacts': [artifact]}
        grant = self.root / 'grant.json'
        self.write(grant, {})
        config = dict(self.config, grant_config=str(grant), qualification_commit=None)
        return target, request, config, api

    def test_acceptance_observes_old_relays_but_qualifies_current_native_artifact(self):
        import release_acceptance as acceptance
        self.assertTrue(self.ready())
        work = self.root / 'native-acceptance'
        target, request, config, api = self.native_acceptance_fixture(work)
        relays = [{'id': f'relay-{index}', 'binary_name': 'gcnode'} for index in range(8)]
        with patch.object(acceptance, 'gh', side_effect=api), \
             patch.object(acceptance, 'inventory', return_value=relays), \
             patch.object(acceptance, 'invoke', return_value={'healthy': True, 'matches': True}) as observe, \
             patch.object(acceptance.time, 'time', return_value=1000):
            result = acceptance.collect(self.state, config, self.new, target, work, request)
        self.assertIs(result['passed'], True)
        self.assertEqual(result['sources'], self.new['sources'])
        self.assertEqual(observe.call_count, 8)
        for call in observe.call_args_list:
            self.assertEqual(call.args[1:3], ('observe', self.old))
        proof = json.loads((self.state / 'acceptance' / target / (self.new['release_id'] + '.json')).read_text())
        self.assertEqual({r['gcoms_commit'] for r in proof['relays']}, {self.old['sources']['gcoms']['commit']})
        self.assertEqual(proof['sources'], self.new['sources'])
        self.assertEqual(proof['deployment_reuse_sha256'], reuse.binding(
            json.loads(reuse.evidence_path(self.state, self.new).read_text())))

    def test_baseline_deployment_cannot_substitute_old_or_failed_native_artifact(self):
        import release_acceptance as acceptance
        self.assertTrue(self.ready())
        mutations = (
            lambda r, n: r.update(sources=self.old['sources']),
            lambda r, n: r.update(passed=False),
            lambda r, n: r['artifacts']['current'].update(archive_sha256='f' * 64),
            lambda r, n: n['inputs'].update(sources=self.old['sources']),
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                work = self.root / f'bad-native-{index}'
                target, request, config, api = self.native_acceptance_fixture(work, mutation)
                with patch.object(acceptance, 'gh', side_effect=api), \
                     patch.object(acceptance, 'invoke') as observe, \
                     patch.object(acceptance.time, 'time', return_value=1000), \
                     self.assertRaises(ValueError):
                    acceptance.collect(self.state, config, self.new, target, work, request)
                observe.assert_not_called()
                self.assertFalse((self.state / 'acceptance' / target / (self.new['release_id'] + '.json')).exists())


if __name__ == '__main__':
    unittest.main()
