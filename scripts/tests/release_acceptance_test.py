import copy
from contextlib import closing
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_acceptance as acceptance
from release_automation_test import candidate
from release_coordinator import Coordinator, atomic_json
from release_ledger import Ledger


def fixture():
    manifest = candidate()
    manifest['refs'] = {'gchat': 'refs/heads/release/example', 'gcoms': 'refs/heads/release/example'}
    manifest['policy']['file_qualification'] = {'bytes': 16777216, 'completion_seconds': 360, 'total_seconds': 600}
    item = {'run': 1, 'artifact': 2, 'archive': 'a'*64, 'controller': 'b'*40,
            'sources': {k: v['commit'] for k, v in manifest['sources'].items()}, 'manifest': 'build.json', 'conclusion': 'success'}
    previous = {**item, 'run': 3, 'artifact': 4, 'archive': 'c'*64,
                'sources': {'gchat': '5'*40, 'gcoms': '6'*40}}
    specs = {'target': 'linux-x86_64', 'current': item, 'baseline': previous}
    report = {'schema': 1, 'passed': True, 'platform': specs['target'], 'sources': manifest['sources'],
              'release_id': manifest['release_id'], 'application_rebuilt': False, 'personal_profiles_accessed': False,
              'invitation_removed': True, 'completed_at': 100, 'installation_cleanup': [],
              'artifacts': {name: {'archive_sha256': specs[name]['archive'], 'sources': specs[name]['sources'],
                                  'binary_sha256': ('d' if name == 'current' else 'a')*64}
                            for name in ('current', 'baseline')}}
    events = [{'event': 'authenticated_ack', 'sender': i} for _ in range(4) for i in (0, 1)]
    rollback = {'passed': True, 'cleanup_complete': True, 'profiles_removed': True, 'binaries_unchanged': True,
                'elapsed_seconds': 100, 'events': events,
                'phases': [{'phase': name, 'binary_sha256': ('a' if name == 'baseline' else 'd')*64,
                            'cache_sha256': 'e'*64, 'same_identity': True,
                            'history_retained': True, 'authenticated_bidirectional_ack': True}
                           for name in ('upgraded', 'baseline', 'restored')]}
    network = {'passed': True, 'inputs_unchanged': True, 'binary_unchanged': True, 'children_stopped': True,
               'temporary_profile_removed': True, 'elapsed_seconds': 150, 'binary_sha256': 'd'*64,
               'inputs': {'sources': manifest['sources']}, 'events': events,
               'file_check': {'bytes': 16777216, 'sha256': 'f'*64, 'completion_elapsed_seconds': 100,
                              'abrupt_stop': True, 'verified_pieces_retained': True, 'hash_verified_after_reopen': True}}
    return manifest, specs, report, rollback, network


class NativeAcceptanceTests(unittest.TestCase):
    def test_production_controller_revision_is_the_default_and_legacy_requests_remain_explicit(self):
        manifest = candidate()
        with patch.dict(acceptance.os.environ, GCHAT_CONTROLLER_REVISION='7'*40):
            self.assertEqual(acceptance.qualification_revision({}, manifest), '7'*40)
            self.assertEqual(acceptance.qualification_revision({'qualification_commit': '8'*40}, manifest), '8'*40)
            self.assertIsNone(acceptance.qualification_revision({'qualification_commit': None}, manifest))
            for value in ('main', '', '7'*39, 'G'*40, True):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    acceptance.qualification_revision({'qualification_commit': value}, manifest)

    def test_qualification_reference_reconciles_lost_publication_and_never_replaces_sources(self):
        commit = '7' * 40
        name = 'release/qualification-' + commit
        reference = {'ref': 'refs/heads/' + name, 'object': {'type': 'commit', 'sha': commit}}
        with patch.object(acceptance, 'gh', side_effect=[[], subprocess.TimeoutExpired('provider', 1), reference]) as api:
            self.assertEqual(acceptance.qualification_ref(commit), name)
            self.assertEqual(api.call_args_list[1].kwargs['body'], {'ref': reference['ref'], 'sha': commit})
            self.assertFalse(any(call.kwargs.get('method') == 'PATCH' for call in api.call_args_list))
        with patch.object(acceptance, 'gh', return_value=[reference]) as api:
            self.assertEqual(acceptance.qualification_ref(commit), name)
            api.assert_called_once()
        for bad in ({**reference, 'object': {'type': 'commit', 'sha': '8'*40}},
                    {**reference, 'ref': reference['ref'] + '-other'},
                    {**reference, 'object': {'type': 'tag', 'sha': commit}}):
            with self.subTest(bad=bad), patch.object(acceptance, 'gh', return_value=[bad]) as api:
                with self.assertRaisesRegex(ValueError, 'frozen source'):
                    acceptance.qualification_ref(commit)
                api.assert_called_once()

    def test_qualification_worker_keeps_exact_retained_application_and_request_binding(self):
        manifest, specs, _, _, _ = fixture()
        intent = {'request': '1'*64, 'qualification_commit': '7'*40, 'qualification_tree': '8'*40}
        binding = {'schema': 1, 'request': intent['request'], 'release_id': manifest['release_id'],
                   'sources': manifest['sources'], 'target': specs['target'], 'commit': '7'*40,
                   'tree': '8'*40, 'source_unchanged': True}
        acceptance.verify_worker(binding, intent, manifest, specs['target'])
        for field, value in (('request', '2'*64), ('release_id', '3'*64), ('sources', {}),
                             ('target', 'ios'), ('commit', manifest['sources']['gchat']['commit']),
                             ('tree', 'main'), ('tree', '9'*40), ('tree', None), ('source_unchanged', False)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                acceptance.verify_worker({**binding, field: value}, intent, manifest, specs['target'])

    def test_new_qualification_dispatch_does_not_relabel_or_repeat_an_unknown_app_worker(self):
        manifest, inputs, _, _, _ = fixture()
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary); grant = work / 'grant.json'; grant.write_text('{}')
            config = {'grant_config': str(grant), 'qualification_commit': '7'*40}
            request = '1'*64
            def provider_api(path, **kwargs):
                if path.startswith('git/commits/'):
                    return {'sha': path.rsplit('/', 1)[-1], 'tree': {'sha': '8'*40}}
                if path.endswith('/dispatches'):
                    raise subprocess.TimeoutExpired('provider', 1)
                return {'workflow_runs': []}
            with patch.object(acceptance, 'provider', return_value=inputs['current']), \
                 patch.object(acceptance, 'baseline', return_value=inputs['baseline']), \
                 patch.object(acceptance, 'qualification_ref', side_effect=lambda c: 'release/qualification-' + c), \
                 patch.object(acceptance, 'gh', side_effect=provider_api) as api, \
                 patch.object(acceptance, 'ssh', return_value=b'{"invitation":"fixture-with-no-authority"}') as ssh, \
                 patch.object(acceptance.subprocess, 'run') as command:
                with self.assertRaises(subprocess.TimeoutExpired):
                    acceptance.collect(work, config, manifest, inputs['target'], work, request)
                marker = (work / 'acceptance-intent.json').read_bytes()
                dispatched = next(call for call in api.call_args_list if call.args[0].endswith('/dispatches'))
                self.assertEqual(dispatched.kwargs['body']['ref'], 'release/qualification-' + '7'*40)
                self.assertEqual(dispatched.kwargs['body']['inputs']['gchat_commit'], manifest['sources']['gchat']['commit'])
                self.assertEqual(dispatched.kwargs['body']['inputs']['qualification_commit'], '7'*40)
                self.assertIsNone(acceptance.collect(work, {**config, 'qualification_commit': '8'*40},
                                                    manifest, inputs['target'], work, request))
                self.assertEqual((work / 'acceptance-intent.json').read_bytes(), marker)
                self.assertEqual(sum(call.args[0].endswith('/dispatches') for call in api.call_args_list), 1)
                ssh.assert_called_once(); command.assert_called_once()

    def test_only_retained_confirmed_failure_can_create_a_corrected_followup(self):
        manifest, inputs, _, _, _ = fixture()
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary); target = inputs['target']; request = '1'*64
            intent = {'request': request, 'sources': manifest['sources'], 'target': target,
                      'qualification_commit': '7'*40, 'cleaned': True}
            atomic_json(work / 'acceptance-intent.json', intent)
            run = {'status': 'completed', 'conclusion': 'failure', 'head_sha': '7'*40,
                   'event': 'workflow_dispatch', 'path': '.github/workflows/native-acceptance.yml',
                   'display_title': acceptance.PREFIX + request,
                   'head_repository': {'full_name': 'IggyGG/gchat'}}
            atomic_json(work / 'acceptance-run.json', run)
            import zipfile
            with zipfile.ZipFile(work / 'acceptance.zip', 'w') as archive:
                archive.writestr('report.json', '{"passed":false}')
            atomic_json(work / 'acceptance-failed.json', {
                'request': request, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
                'target': target, 'qualification_commit': '7'*40, 'passed': False,
                'run_sha256': acceptance.digest(work / 'acceptance-run.json'),
                'archive_sha256': acceptance.digest(work / 'acceptance.zip'),
                'intent_sha256': acceptance.digest(work / 'acceptance-intent.json')})
            retained = {name: (work / name).read_bytes() for name in (
                'acceptance-intent.json', 'acceptance-run.json', 'acceptance.zip', 'acceptance-failed.json')}
            with self.assertRaisesRegex(ValueError, 'original reports retained'):
                acceptance.failed_followup(work, {}, manifest, target, work, request, intent, '7'*40)
            with patch.object(acceptance, 'collect', return_value=None) as collect:
                self.assertEqual(acceptance.failed_followup(work, {}, manifest, target, work, request, intent, '8'*40), (True, None))
                first = collect.call_args
                pointer = (work / 'acceptance-followup.json').read_bytes()
                acceptance.failed_followup(work, {}, manifest, target, work, request, intent, '9'*40)
                self.assertEqual((work / 'acceptance-followup.json').read_bytes(), pointer)
                self.assertEqual(collect.call_args.args[-1], first.args[-1])
                self.assertEqual(collect.call_args.kwargs['frozen_revision'], '8'*40)
                self.assertNotEqual(first.args[-1], request)
            for name, content in retained.items():
                self.assertEqual((work / name).read_bytes(), content)
            (work / 'acceptance.zip').write_bytes(b'changed retained archive')
            with patch.object(acceptance, 'collect') as collect, self.assertRaisesRegex(ValueError, 'outcome changed'):
                acceptance.failed_followup(work, {}, manifest, target, work, request, intent, '9'*40)
            collect.assert_not_called()

    def test_baseline_rotates_to_available_predecessor_and_keeps_seed_as_fallback(self):
        with tempfile.TemporaryDirectory() as temporary, closing(Ledger(Path(temporary) / 'ledger.sqlite')) as ledger:
            root = Path(temporary)
            manifests = [candidate(i) for i in range(1, 5)]
            target = 'linux-x86_64'
            for manifest in manifests:
                release = ledger.add(manifest)
                for state in ('building', 'verifying', 'verified', 'publishing', 'available'):
                    ledger.transition(release, target, state, evidence='a'*64)
            current = manifests[2]
            specs = {m['release_id']: {'sources': {k:v['commit'] for k,v in m['sources'].items()},
                                     'archive': str(i)*64}
                     for i,m in enumerate(manifests, 1)}
            seed = {'sources': {'gchat':'5'*40,'gcoms':'6'*40},'archive':'e'*64}
            config = {'baselines': {target: seed}}
            with patch.object(acceptance, 'provider', side_effect=lambda _,m,t: specs[m['release_id']]) as provider:
                self.assertEqual(acceptance.baseline(root,target,config,current), specs[manifests[1]['release_id']])
                self.assertEqual([call.args[1]['release_id'] for call in provider.call_args_list],
                                 [manifests[1]['release_id']])
            # A historical provider without a normal retained archive cannot be
            # relabelled. An older valid provider still precedes the seed.
            def historical(_, manifest, _target):
                if manifest['release_id'] == manifests[1]['release_id']: raise FileNotFoundError('retained archive absent')
                return specs[manifest['release_id']]
            with patch.object(acceptance,'provider',side_effect=historical):
                self.assertEqual(acceptance.baseline(root,target,config,current), specs[manifests[0]['release_id']])
            with patch.object(acceptance,'provider',return_value=None):
                self.assertEqual(acceptance.baseline(root,target,config,current),seed)
                self.assertIsNone(acceptance.baseline(root,target,{},current))
            # Neither an identical source pair nor a corrupt receipt can become
            # an upgrade baseline, including in the operator-bound seed.
            same = specs[current['release_id']]
            with patch.object(acceptance,'provider',return_value=same):
                self.assertIsNone(acceptance.baseline(root,target,{'baselines':{target:same}},current))
            with patch.object(acceptance,'provider',side_effect=ValueError('corrupt source binding')):
                with self.assertRaisesRegex(ValueError,'corrupt source binding'):
                    acceptance.baseline(root,target,config,current)

    def test_cleanup_failure_still_stops_other_children_and_retains_failed_report(self):
        driver = acceptance.module('test-native-upgrade')

        class Child:
            returncode = None
            def poll(self): return self.returncode
            def kill(self): self.returncode = -9
            def wait(self, timeout): return self.returncode

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); output = root / 'rollback'; output.mkdir()
            for i in (0, 1): (output / f'c{i}').mkdir()
            children = [(i, Child(), output / f'stop-{i}', (output / f'child-{i}.log').open('wb')) for i in (0, 1)]
            journey = SimpleNamespace(root=output, start=time.monotonic(), clients={0: None, 1: None},
                children=children, report={'events': []})
            def fail_start(*args): raise ValueError('fixture startup failed')
            journey.start_client = fail_start
            items = {}
            for name in ('current', 'baseline'):
                binary = root / name; binary.write_bytes(name.encode())
                items[name] = {'binary': binary, 'build_manifest': root / 'build.json',
                               'native_receipt': root / 'native.json', 'build': {'publisher': 'fixture'}}
            stopped = []
            def stop(process, *args):
                stopped.append(process)
                if process is children[1][1]: raise OSError('fixture stop failure')
                process.returncode = 0
                return {'stopped': True, 'forced': False, 'exit_code': 0}
            with patch.object(driver.network, 'Journey', return_value=journey), patch.object(driver.smoke, 'stop_service', side_effect=stop):
                report = driver.rollback(items['current'], items['baseline'], root / 'invitation', output)
            self.assertEqual(len(stopped), 2)
            self.assertFalse(report['passed']); self.assertFalse(report['cleanup_complete'])
            self.assertTrue(report['children_stopped']); self.assertTrue(report['profiles_removed'])
            self.assertEqual(report['cleanup_errors'], ['OSError'])
            self.assertTrue(all(log.closed for _, _, _, log in children))
            self.assertEqual(json.loads((output / 'report.json').read_text()), report)

    def test_only_bound_native_artifacts_complete_rollback_and_original_file_gate_pass(self):
        manifest, specs, report, rollback, network = fixture()
        acceptance.qualify_native(report, rollback, network, manifest, specs['target'], specs, 110)
        for field, bad in (('passed', False), ('platform', 'android'), ('application_rebuilt', True),
                           ('personal_profiles_accessed', True), ('completed_at', 111), ('completed_at', -4000),
                           ('invitation_removed', False), ('installation_cleanup', [{'passed': False}])):
            changed = copy.deepcopy(report); changed[field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                acceptance.qualify_native(changed, rollback, network, manifest, specs['target'], specs, 110)
        for field, bad in (('cleanup_complete', False), ('profiles_removed', False), ('binaries_unchanged', False),
                           ('elapsed_seconds', 601), ('elapsed_seconds', float('nan')), ('phases', []), ('events', [])):
            changed = copy.deepcopy(rollback); changed[field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                acceptance.qualify_native(report, changed, network, manifest, specs['target'], specs, 110)
        for field, bad in (('bytes', 4194304), ('completion_elapsed_seconds', 361), ('sha256', 'unverified'),
                           ('verified_pieces_retained', False), ('hash_verified_after_reopen', False)):
            changed = copy.deepcopy(network); changed['file_check'][field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                acceptance.qualify_native(report, rollback, changed, manifest, specs['target'], specs, 110)

    def test_baseline_cache_and_source_cannot_be_relabelled(self):
        manifest, specs, report, rollback, network = fixture()
        for name in ('current', 'baseline'):
            changed = copy.deepcopy(report); changed['artifacts'][name]['archive_sha256'] = '0'*64
            with self.subTest(name=name), self.assertRaises(ValueError):
                acceptance.qualify_native(changed, rollback, network, manifest, specs['target'], specs, 110)
        changed = copy.deepcopy(rollback); changed['phases'][1]['cache_sha256'] = '0'*64
        with self.assertRaises(ValueError): acceptance.qualify_native(report, changed, network, manifest, specs['target'], specs, 110)
        changed = copy.deepcopy(rollback); changed['phases'][2]['cache_sha256'] = '0'*64
        with self.assertRaises(ValueError): acceptance.qualify_native(report, changed, network, manifest, specs['target'], specs, 110)
        changed = copy.deepcopy(report); changed['artifacts']['baseline']['binary_sha256'] = changed['artifacts']['current']['binary_sha256']
        with self.assertRaises(ValueError): acceptance.qualify_native(changed, rollback, network, manifest, specs['target'], specs, 110)
        changed = copy.deepcopy(network); changed['inputs']['sources']['gcoms']['commit'] = '0'*40
        with self.assertRaises(ValueError): acceptance.qualify_native(report, rollback, changed, manifest, specs['target'], specs, 110)

    def test_native_inputs_reject_escape_failed_provider_and_mobile_target(self):
        spec = importlib.util.spec_from_file_location('native_upgrade_test', Path(__file__).resolve().parents[1] / 'test-native-upgrade.py')
        driver = importlib.util.module_from_spec(spec); spec.loader.exec_module(driver)
        _, inputs, _, _, _ = fixture()
        driver.validate_inputs(inputs)
        for path in ('../build.json', '/build.json', 'C:/build.json', r'\build.json'):
            changed = copy.deepcopy(inputs); changed['current']['manifest'] = path
            with self.subTest(path=path), self.assertRaises(ValueError): driver.validate_inputs(changed)
        changed = copy.deepcopy(inputs); changed['baseline']['conclusion'] = 'failure'
        with self.assertRaises(ValueError): driver.validate_inputs(changed)
        for field in ('run', 'artifact', 'archive', 'sources'):
            changed = copy.deepcopy(inputs); changed['baseline'][field] = changed['current'][field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'distinct'):
                driver.validate_inputs(changed)
        with self.assertRaises(ValueError): driver.validate_inputs({**inputs, 'target': 'android'})

    def test_dispatch_lost_reply_reconciles_without_new_grant_or_blind_submission(self):
        manifest, inputs, _, _, _ = fixture()
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary); grant = work / 'grant.json'; grant.write_text('{}')
            config = {'grant_config': str(grant), 'qualification_commit': None}; request = '1'*64
            def provider_api(path, **kwargs):
                if path.endswith('/dispatches'): raise subprocess.TimeoutExpired('provider', 1)
                return {'workflow_runs': []}
            with patch.object(acceptance, 'provider', return_value=inputs['current']), \
                 patch.object(acceptance, 'baseline', return_value=inputs['baseline']), \
                 patch.object(acceptance, 'gh', side_effect=provider_api) as api, \
                 patch.object(acceptance, 'ssh', return_value=b'{"invitation":"fixture-with-no-authority"}') as ssh, \
                 patch.object(acceptance.subprocess, 'run') as command:
                with self.assertRaises(subprocess.TimeoutExpired): acceptance.collect(work, config, manifest, inputs['target'], work, request)
                marker = json.loads((work / 'acceptance-intent.json').read_text())
                self.assertTrue(marker['dispatch_reserved'])
                self.assertNotIn('invitation', marker)
                self.assertIsNone(acceptance.collect(work, config, manifest, inputs['target'], work, request))
                ssh.assert_called_once(); command.assert_called_once()
                self.assertEqual(sum(call.args[0].endswith('/dispatches') for call in api.call_args_list), 1)

    def test_expired_unknown_dispatch_revokes_without_resubmitting(self):
        manifest, _, _, _, _ = fixture()
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary); grant = work / 'grant.json'; grant.write_text('{}')
            intent = {'request': '1'*64, 'target': 'linux-x86_64', 'sources': manifest['sources'],
                      'created_at': 1, 'operation': '2'*64, 'secret': 'GCHAT_ACCEPTANCE_'+'2'*64, 'dispatch_reserved': True}
            atomic_json(work / 'acceptance-intent.json', intent)
            with patch.object(acceptance, 'gh', return_value={'workflow_runs': []}) as api, \
                 patch.object(acceptance, 'ssh', return_value=b'{"revoked":true}') as ssh, \
                 patch.object(acceptance.subprocess, 'check_output', return_value=b'[]'):
                with self.assertRaisesRegex(ValueError, 'do not resubmit blindly'):
                    acceptance.collect(work, {'grant_config': str(grant), 'qualification_commit': None}, manifest, 'linux-x86_64', work, '1'*64)
                ssh.assert_called_once()
                self.assertTrue(json.loads((work / 'acceptance-intent.json').read_text())['cleaned'])
                self.assertFalse(any(call.args[0].endswith('/dispatches') for call in api.call_args_list))

    def test_oversized_invitation_revokes_without_secret_or_workflow_dispatch(self):
        manifest, inputs, _, _, _ = fixture()
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary); grant = work / 'grant.json'; grant.write_text('{}')
            with patch.object(acceptance, 'provider', return_value=inputs['current']), \
                 patch.object(acceptance, 'baseline', return_value=inputs['baseline']), \
                 patch.object(acceptance, 'gh', return_value={'workflow_runs': []}) as api, \
                 patch.object(acceptance, 'ssh', side_effect=[json.dumps({'invitation': 'x'*48001}).encode(), b'{"revoked":true}']) as ssh, \
                 patch.object(acceptance.subprocess, 'check_output', return_value=b'[]'), \
                 patch.object(acceptance.subprocess, 'run') as command:
                with self.assertRaisesRegex(ValueError, 'grant revoked'):
                    acceptance.collect(work, {'grant_config': str(grant), 'qualification_commit': None}, manifest, inputs['target'], work, '1'*64)
                intent = json.loads((work / 'acceptance-intent.json').read_text())
                self.assertTrue(intent['cleaned']); self.assertTrue(intent['rejected_before_dispatch'])
                with self.assertRaisesRegex(ValueError, 'grant revoked'):
                    acceptance.collect(work, {'grant_config': str(grant), 'qualification_commit': None}, manifest, inputs['target'], work, '1'*64)
                command.assert_not_called(); self.assertEqual(ssh.call_count, 2)
                self.assertFalse(any(call.args[0].endswith('/dispatches') for call in api.call_args_list))


class AcceptanceFreshnessTests(unittest.TestCase):
    def coordinator(self, root):
        script = root / 'waiting.py'; script.write_text('raise SystemExit(75)\n')
        command = [sys.executable, str(script)]
        c = Coordinator(root, {'workers': {'linux-x86_64': {'acceptance': {'run': command, 'reconcile': command, 'max_age_seconds': 60}}}})
        self.addCleanup(c.ledger.close); manifest = candidate(); c.ledger.add(manifest)
        effect = c.ledger.effect(manifest['release_id'], 'linux-x86_64', 'acceptance')
        work = root / 'jobs' / effect['id']; work.mkdir(parents=True)
        return c, manifest, effect, work

    def test_only_completed_acceptance_can_expire_and_old_evidence_is_retained(self):
        temporary = self.enterContext(tempfile.TemporaryDirectory())
        c, manifest, effect, work = self.coordinator(Path(temporary))
        log = work / 'proof.log'; log.write_text('fixture evidence')
        report = {'schema': 1, 'passed': True, 'source_unchanged': True, 'stage': 'acceptance', 'platform': 'linux-x86_64',
                  'release_id': manifest['release_id'], 'sources': manifest['sources'], 'completed_at': 100,
                  'evidence': [{'path': log.name, 'sha256': hashlib.sha256(log.read_bytes()).hexdigest()}]}
        receipt = work / 'receipt.json'; atomic_json(receipt, report); original = receipt.read_bytes()
        with patch('release_coordinator.time.time', return_value=200):
            self.assertIsNone(c.execute(manifest, 'linux-x86_64', 'acceptance'))
            self.assertIsNone(c.execute(manifest, 'linux-x86_64', 'acceptance'))
        self.assertEqual(receipt.read_bytes(), original)
        self.assertEqual(c.ledger.db.execute('SELECT COUNT(*) FROM effects').fetchone()[0], 2)
        self.assertEqual(c.ledger.db.execute('SELECT state FROM effects WHERE id=?', (effect['id'],)).fetchone()[0], 'confirmed')

    def test_unknown_old_request_cannot_expire_into_a_new_effect(self):
        temporary = self.enterContext(tempfile.TemporaryDirectory())
        c, manifest, effect, work = self.coordinator(Path(temporary))
        atomic_json(work / 'attempted.json', {'request_id': effect['id'], 'attempted': 1})
        with patch('release_coordinator.time.time', return_value=10000):
            self.assertIsNone(c.execute(manifest, 'linux-x86_64', 'acceptance'))
        self.assertEqual(c.ledger.db.execute('SELECT COUNT(*) FROM effects').fetchone()[0], 1)
        self.assertFalse((c.state / 'acceptance-effects').exists())

    def test_acceptance_failure_keeps_its_own_recovery_stage(self):
        temporary = self.enterContext(tempfile.TemporaryDirectory())
        c, manifest, _, _ = self.coordinator(Path(temporary))
        release = manifest['release_id']; target = 'linux-x86_64'
        for state in ('building', 'verifying', 'verified'):
            c.ledger.transition(release, target, state, evidence='a'*64)
        with patch.object(c, 'execute', side_effect=ValueError('native acceptance failed')) as execute:
            c.step(release, target)
        execute.assert_called_once_with(manifest, target, 'acceptance')
        self.assertEqual(c.ledger.target(release, target)['state'], 'blocked')
        self.assertEqual(json.loads(c.recovery_path(release, target).read_text())['stage'], 'acceptance')
