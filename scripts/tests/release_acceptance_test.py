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
from unittest.mock import Mock, patch
import io
import os
import zipfile

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_acceptance as acceptance
import acceptance_delivery as transport
import release_acceptance_delivery as delivery
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


class EncryptedAcceptanceDeliveryTests(unittest.TestCase):
    def ready_fixture(self, root, mutate=None):
        manifest, inputs, _, _, _ = fixture()
        request = '1'*64; work = root / 'work'; work.mkdir()
        binding = {'request': request, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
                   'target': inputs['target'], 'commit': '7'*40, 'tree': '8'*40}
        private = root / 'private'
        with patch.object(transport.time, 'time', return_value=100):
            transport.generate(private, binding, root / 'acceptance-ready.json')
        ready = json.loads((root / 'acceptance-ready.json').read_text())
        if mutate: ready.update(mutate)
        with zipfile.ZipFile(work / 'ready.zip', 'w') as source:
            source.writestr('acceptance-ready.json', json.dumps(ready))
        artifact = {'id': 20, 'name': 'acceptance-ready-' + request, 'expired': False,
                    'digest': 'sha256:' + transport.digest(work / 'ready.zip'),
                    'size_in_bytes': (work / 'ready.zip').stat().st_size}
        paths = {}
        for role in ('current', 'baseline'):
            path = root / (role + '.zip'); path.write_bytes((role.encode() + b'-original-private-archive') * 100)
            inputs[role]['archive'] = transport.digest(path)
            paths[role] = {'path': str(path), 'provider': {'id': inputs[role]['artifact'], 'name': inputs['target'],
                'workflow_run': {'id': inputs[role]['run']}, 'retained_locally': True,
                'digest': 'sha256:' + inputs[role]['archive'], 'size_in_bytes': path.stat().st_size}}
        intent = {'request': request, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
                  'target': inputs['target'], 'inputs': inputs, 'qualification_commit': '7'*40,
                  'qualification_tree': '8'*40, 'delivery_archives': paths}
        run = {'id': 10, 'status': 'in_progress'}
        api = Mock(return_value={'artifacts': [artifact]})
        issue = Mock(return_value={'invitation': 'fixture-with-no-authority', 'expires_at': 3700})
        return manifest, intent, work, private, run, api, issue

    def test_actual_multiframe_crypto_rejects_tampering_and_preserves_existing_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); request = '1'*64
            sender, receiver = X25519PrivateKey.generate(), X25519PrivateKey.generate()
            secret = transport.key(sender, transport.public(receiver), request, 'current')
            self.assertEqual(secret, transport.key(receiver, transport.public(sender), request, 'current'))
            source = root / 'original'; source.write_bytes(b'a' * (transport.CHUNK + 19))
            bound = transport.encrypt_archive(source, root / 'sealed', secret, request, 'current', transport.digest(source))
            transport.decrypt_archive(root / 'sealed', root / 'plain', secret, request, 'current', bound)
            self.assertEqual((root / 'plain').read_bytes(), source.read_bytes())
            for other_request, purpose, other_key in ((request, 'baseline', secret), ('2'*64, 'current', secret),
                                                       (request, 'current', b'0'*32)):
                with self.subTest(purpose=purpose), self.assertRaises(InvalidTag):
                    transport.decrypt_archive(root / 'sealed', root / 'failed', other_key, other_request, purpose, bound)
                self.assertFalse((root / 'failed').exists())
            data = bytearray((root / 'sealed').read_bytes()); data[2] ^= 1; (root / 'sealed').write_bytes(data)
            changed = {**bound, 'ciphertext_sha256': transport.digest(root / 'sealed')}
            with self.assertRaises(InvalidTag):
                transport.decrypt_archive(root / 'sealed', root / 'failed', secret, request, 'current', changed)
            self.assertFalse((root / 'failed').exists())
            before = (root / 'plain').read_bytes()
            with self.assertRaises(FileExistsError):
                transport.decrypt_archive(root / 'sealed', root / 'plain', secret, request, 'current', changed)
            self.assertEqual((root / 'plain').read_bytes(), before)
            with self.assertRaises(ValueError): transport.archive_bound({**bound, 'ciphertext_size': 12*1024**3+1})

    def test_response_is_bound_to_the_request_and_the_runner_private_key(self):
        sender, receiver = X25519PrivateKey.generate(), X25519PrivateKey.generate(); request = '1'*64
        sealed = transport.seal({'invitation': 'fixture-with-no-authority'}, sender, transport.public(receiver), request)
        self.assertEqual(transport.unseal(sealed, receiver, request), {'invitation': 'fixture-with-no-authority'})
        self.assertNotIn('invitation', sealed)
        for value, private, bound_request in ((sealed, X25519PrivateKey.generate(), request),
                                               (sealed, receiver, '2'*64),
                                               ({**sealed, 'protocol': 'other'}, receiver, request)):
            with self.subTest(request=bound_request), self.assertRaises((ValueError, InvalidTag)):
                transport.unseal(value, private, bound_request)

    def test_queued_worker_has_no_grant_and_ready_delivery_replays_the_same_response(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); _, intent, work, _, run, api, issue = self.ready_fixture(root)
            self.assertIsNone(delivery.ready(root, intent, work, {**run, 'status': 'queued'}, api, issue, now=100))
            api.assert_not_called(); issue.assert_not_called()
            previous_umask = os.umask(0o077)
            try:
                proof = delivery.ready(root, intent, work, run, api, issue, now=100)
            finally:
                os.umask(previous_umask)
            response = root / 'public/updates/acceptance' / intent['request'] / 'response.json'
            for directory in (response.parent, response.parent.parent, root / 'public', root / 'public/updates'):
                self.assertEqual(directory.stat().st_mode & 0o777, 0o755)
            for file in response.parent.iterdir(): self.assertEqual(file.stat().st_mode & 0o777, 0o644)
            self.assertEqual((work / 'sealed-response.json').stat().st_mode & 0o777, 0o600)
            original = response.read_bytes(); response.unlink()
            self.assertEqual(delivery.ready(root, intent, work, run, api, issue, now=150), proof)
            self.assertEqual(response.read_bytes(), original); issue.assert_called_once()
            self.assertTrue(proof['grant_issued_after_ready'])
            self.assertEqual(proof['expires_at'], 3700)
            for role, item in intent['delivery_archives'].items():
                self.assertEqual(transport.digest(item['path']), intent['inputs'][role]['archive'])
            delivery.cleanup(root, intent['request']); self.assertFalse(response.parent.exists())
            self.assertTrue((work / 'sealed-delivery.json').exists())
            self.assertTrue(all(Path(v['path']).exists() for v in intent['delivery_archives'].values()))

    def test_wrong_source_stale_and_small_order_ready_keys_never_issue_a_grant(self):
        for changed in ({'request': '2'*64}, {'commit': '9'*40}, {'tree': '9'*40}, {'sources': {}},
                        {'target': 'ios'}, {'release_id': '3'*64}, {'created_at': -201},
                        {'created_at': 101}, {'public_key': transport.encode(b'\0'*32)}):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); _, intent, work, _, run, api, issue = self.ready_fixture(root, changed)
                with self.assertRaises(ValueError): delivery.ready(root, intent, work, run, api, issue, now=100)
                issue.assert_not_called(); self.assertFalse((root / 'public').exists())

    def test_ambiguous_and_changed_ready_provider_archives_are_refused(self):
        for duplicate in (True, False):
            with self.subTest(duplicate=duplicate), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); _, intent, work, _, run, api, issue = self.ready_fixture(root)
                if duplicate: api.return_value['artifacts'] *= 2
                else: (work / 'ready.zip').write_bytes(b'changed')
                with self.assertRaises(ValueError): delivery.ready(root, intent, work, run, api, issue, now=100)
                issue.assert_not_called()

    def test_runner_receives_exact_bytes_and_removes_private_transport_on_success_or_failure(self):
        class Response(io.BytesIO):
            def __init__(self, data, url): super().__init__(data); self.url = url
        for fail in (False, True):
            with self.subTest(fail=fail), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); manifest, intent, work, private, run, api, issue = self.ready_fixture(root)
                delivery.ready(root, intent, work, run, api, issue, now=100)
                public = root / 'public/updates/acceptance' / intent['request']
                def urlopen(url, **kwargs):
                    return Response((public / url.rsplit('/', 1)[-1]).read_bytes(), url)
                def driver(*args, **kwargs):
                    env = kwargs['env']; self.assertEqual(env['GCHAT_NETWORK_INVITATION'], 'fixture-with-no-authority')
                    copies = Path(env['GCHAT_ACCEPTANCE_RETAINED_ROOT'])
                    for role in ('current', 'baseline'):
                        spec = intent['inputs'][role]
                        self.assertEqual(transport.digest(copies / (spec['archive'] + '.zip')), spec['archive'])
                        destination = root / 'acceptance' / role; destination.mkdir(parents=True)
                        (destination / 'artifact.zip').write_bytes((copies / (spec['archive'] + '.zip')).read_bytes())
                    (root / 'acceptance/network').mkdir()
                    (root / 'acceptance/network/report.json').write_text('{"retained":true}')
                    if fail: raise OSError('fixture driver failure')
                    return SimpleNamespace(returncode=0)
                with patch.object(transport.urllib.request, 'urlopen', side_effect=urlopen), \
                     patch.object(transport.subprocess, 'run', side_effect=driver), \
                     patch.object(transport.time, 'time', return_value=100):
                    if fail:
                        with self.assertRaises(OSError):
                            transport.receive('https://example.test/updates/acceptance', intent['request'], private,
                                              intent['inputs'], manifest, 'driver.py', root / 'acceptance')
                    else:
                        self.assertEqual(transport.receive('https://example.test/updates/acceptance', intent['request'],
                            private, intent['inputs'], manifest, 'driver.py', root / 'acceptance'), 0)
                self.assertFalse(private.exists())
                proof = json.loads((root / 'acceptance/delivery.json').read_text())
                self.assertEqual(proof['passed'], not fail)
                self.assertTrue(proof['private_key_removed']); self.assertTrue(proof['decrypted_archives_removed'])
                self.assertTrue(proof['derived_native_copies_removed'])
                self.assertFalse((root / 'acceptance/current').exists())
                self.assertFalse((root / 'acceptance/baseline').exists())
                self.assertTrue((root / 'acceptance/network/report.json').exists())
                if not fail: delivery.verify_receipt(proof, intent, work)
                self.assertEqual({p.suffix for p in public.iterdir()}, {'.json', '.sealed'})
                self.assertFalse(any(b'fixture-with-no-authority' in p.read_bytes() for p in public.iterdir()))

    def test_delivered_archive_metadata_and_bytes_cannot_be_changed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); _, intent, _, _, _, _, _ = self.ready_fixture(root)
            spec = intent['inputs']['current']; source = Path(intent['delivery_archives']['current']['path'])
            copies = root / 'copies'; copies.mkdir(); source.rename(copies / (spec['archive'] + '.zip'))
            metadata = copies / (spec['archive'] + '.json')
            atomic_json(metadata, intent['delivery_archives']['current']['provider'])
            with patch.dict(os.environ, GCHAT_ACCEPTANCE_RETAINED_ROOT=str(copies)):
                transport.copy_retained(spec, root / 'verified.zip')
                self.assertEqual(transport.digest(root / 'verified.zip'), spec['archive'])
                atomic_json(metadata, {**json.loads(metadata.read_text()), 'workflow_run': {'id': 999}})
                with self.assertRaises(ValueError): transport.copy_retained(spec, root / 'bad.zip')
                atomic_json(metadata, intent['delivery_archives']['current']['provider'])
                (copies / (spec['archive'] + '.zip')).write_bytes(b'changed')
                with self.assertRaises(ValueError): transport.copy_retained(spec, root / 'bad.zip')
                self.assertFalse((root / 'bad.zip').exists())

    def test_retained_original_remains_available_without_provider_download(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); _, specs, _, _, _ = fixture(); spec = specs['current']
            builds = root / 'jobs/build'; builds.mkdir(parents=True)
            with zipfile.ZipFile(builds / 'native.zip', 'w') as archive:
                archive.writestr('build.json', json.dumps({'target': specs['target'], 'sources': spec['sources']}))
            spec['archive'] = transport.digest(builds / 'native.zip')
            atomic_json(builds / 'receipt.json', {'stage': 'build', 'passed': True, 'external_id': str(spec['run']),
                'sources': {k: {'commit': v} for k, v in spec['sources'].items()},
                'worker': {'artifact_id': spec['artifact'], 'workflow_commit': spec['controller']},
                'evidence': [{'path': 'native.zip', 'sha256': spec['archive']}]})
            api = Mock(side_effect=AssertionError('provider download must not be required'))
            path = delivery.retain_original(root, spec, specs['target'], api)
            metadata = delivery.provider_metadata(path, spec, specs['target'])
            self.assertTrue(metadata['retained_locally']); self.assertEqual(metadata['digest'], 'sha256:' + spec['archive'])
            api.assert_not_called()

    def test_new_dispatch_waits_for_readiness_and_freezes_unknown_requests_without_a_secret(self):
        manifest, inputs, _, _, _ = fixture()
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary); grant = work / 'grant.json'; grant.write_text('{}'); request = '1'*64
            config = {'grant_config': str(grant), 'qualification_commit': '7'*40,
                      'delivery_url': 'https://example.test/updates/acceptance'}
            run = {'id': 10, 'display_title': acceptance.PREFIX + request, 'head_sha': '7'*40,
                   'event': 'workflow_dispatch', 'path': '.github/workflows/native-acceptance.yml',
                   'head_repository': {'full_name': 'IggyGG/gchat'}, 'status': 'queued'}
            dispatched = False
            def provider_api(path, **kwargs):
                nonlocal dispatched
                if path.startswith('git/commits/'): return {'sha': '7'*40, 'tree': {'sha': '8'*40}}
                if path.endswith('/dispatches'): dispatched = True; raise subprocess.TimeoutExpired('provider', 1)
                return {'workflow_runs': [run] if dispatched else []}
            with patch.object(acceptance, 'provider', return_value=inputs['current']), \
                 patch.object(acceptance, 'baseline', return_value=inputs['baseline']), \
                 patch.object(acceptance, 'qualification_ref', side_effect=lambda c: 'release/qualification-' + c), \
                 patch.object(acceptance, 'gh', side_effect=provider_api) as api, \
                 patch.object(delivery, 'prepare', return_value={}), patch.object(acceptance, 'ssh') as ssh, \
                 patch.object(acceptance.subprocess, 'run') as command:
                with self.assertRaises(subprocess.TimeoutExpired):
                    acceptance.collect(work, config, manifest, inputs['target'], work, request)
                marker = (work / 'acceptance-intent.json').read_bytes()
                self.assertIsNone(acceptance.collect(work, {**config, 'qualification_commit': '9'*40},
                                                     manifest, inputs['target'], work, request))
                self.assertEqual((work / 'acceptance-intent.json').read_bytes(), marker)
                inputs_sent = next(c.kwargs['body']['inputs'] for c in api.call_args_list if c.args[0].endswith('/dispatches'))
                self.assertNotIn('invitation_secret', inputs_sent); self.assertIn('delivery_url', inputs_sent)
                ssh.assert_not_called(); command.assert_not_called()
                intent = json.loads(marker); intent['cleaned'] = True
                atomic_json(work / 'acceptance-intent.json', intent)
                run['status'] = 'in_progress'
                with self.assertRaisesRegex(ValueError, 'closed acceptance'):
                    acceptance.collect(work, config, manifest, inputs['target'], work, request)
                ssh.assert_not_called()

    def test_delivery_cleanup_receipt_cannot_relabel_source_bytes_or_key_removal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); _, intent, work, _, run, api, issue = self.ready_fixture(root)
            retained = delivery.ready(root, intent, work, run, api, issue, now=100)
            proof = {'schema': 1, 'protocol': transport.PROTOCOL, 'request': intent['request'],
                     'sources': intent['sources'], 'target': intent['target'], 'qualification_commit': '7'*40,
                     'qualification_tree': '8'*40, 'passed': True, 'response_sha256': retained['response_sha256'],
                     'archives': {r: s['archive'] for r, s in intent['inputs'].items() if r != 'target'},
                     'private_key_removed': True, 'decrypted_archives_removed': True, 'derived_native_copies_removed': True}
            delivery.verify_receipt(proof, intent, work)
            for field, value in (('sources', {}), ('request', '2'*64), ('qualification_tree', '9'*40),
                                 ('archives', {}), ('response_sha256', '0'*64), ('passed', False),
                                 ('private_key_removed', False), ('decrypted_archives_removed', False),
                                 ('derived_native_copies_removed', False)):
                with self.subTest(field=field), self.assertRaises(ValueError):
                    delivery.verify_receipt({**proof, field: value}, intent, work)

    def test_expired_provider_copy_still_requires_the_original_mobile_run_and_sources(self):
        import mobile_acceptance_inputs as mobile
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); _, specs, _, _, _ = fixture(); spec = specs['current']
            copies = root / 'copies'; copies.mkdir()
            original = copies / 'original.zip'
            report = {'passed': True, 'sources_unchanged': True,
                      'sources': {k: {'commit': v} for k, v in spec['sources'].items()}}
            with zipfile.ZipFile(original, 'w') as archive: archive.writestr('build.json', json.dumps(report))
            spec['archive'] = transport.digest(original); original.rename(copies / (spec['archive'] + '.zip'))
            provider = delivery.provider_metadata(copies / (spec['archive'] + '.zip'), spec, 'android')
            atomic_json(copies / (spec['archive'] + '.json'), provider)
            run = {'status': 'completed', 'conclusion': 'success', 'head_sha': spec['controller'],
                   'head_repository': {'full_name': 'IggyGG/gchat'}, 'event': 'workflow_dispatch',
                   'path': '.github/workflows/android-release.yml'}
            with patch.dict(os.environ, GCHAT_ACCEPTANCE_RETAINED_ROOT=str(copies)), \
                 patch.object(mobile, 'gh', return_value=run) as api:
                accepted = mobile.acquire('current', spec, 'android', root)
                self.assertEqual(accepted['archive_sha256'], spec['archive']); api.assert_called_once()
                api.return_value = {**run, 'conclusion': 'failure'}
                with self.assertRaisesRegex(ValueError, 'binding differs'):
                    mobile.acquire('wrong-run', spec, 'android', root)

    def test_delivery_url_and_cleanup_reject_escape_and_cleartext(self):
        for url in ('http://example.test', 'https://user@example.test', 'https://example.test?x=1',
                    'https://example.test#secret'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                transport.delivery_url(url, '1'*64, 'response.json')
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError): delivery.cleanup(Path(temporary), '../../original')


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
