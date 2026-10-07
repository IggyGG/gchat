"""Original provider evidence and raw observations gate relay capacity activation."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_automation_test import candidate
from release_evidence import EvidenceError, digest
from release_jobs import authorize_native_retry
from release_pair import canonical
from release_publish import job
from release_relay_load import MEMBERS, SCOPE, collect, verify


class RelayLoadTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.manifest = candidate()
        self.provider = {'repository': 'IggyGG/gchat', 'run_id': '123', 'run_attempt': 1,
                         'workflow_commit': self.manifest['sources']['gchat']['commit']}
        self.binary = {'sha256': 'e' * 64, 'size': 10}
        files = {'scripts/gchat-turnover.py': hashlib.sha256(b'driver').hexdigest(),
                 'scripts/privacy-client-capture.py': hashlib.sha256(b'helper').hexdigest()}
        self.build = {'passed': True, 'sources': {p: {'revision': s['commit'], 'files': files,
            'unchanged': True, 'snapshot_sha256': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}
            for p, s in self.manifest['sources'].items()}, 'artifacts': {p: self.binary for p in
            ('gcnode', 'gchat', 'fleet_probe', 'turnover_daemon')}}
        self.write('build.json', self.build)
        self.file = {'id': 'file', 'sha256': 'f' * 64, 'size': 5235248}
        self.records = [{'sender': 0, 'channel_index': i % 4, 'recipients': MEMBERS[i % 4] - 1,
                         'id': str(i), 'recipient_seconds': [1.0] * (MEMBERS[i % 4] - 1),
                         'authenticated_ack_seconds': 2.0} for i in range(720)]
        self.load = {'clients': 64, 'seconds': 1800, 'topology': 'fleet-four-channels', 'channels': 4,
                     'channel_members': MEMBERS, 'recipient_deliveries_per_round': 63,
                     'started_unix': 1000, 'completed_unix': 2800, 'observed_seconds': 1800,
                     'relay_restart': True, 'authenticated_commands': self.records, 'commands': 720,
                     'attempts': 720, 'application_refusals': 0, 'application_refusal_fraction': 0.0,
                     'recipient_p95_seconds': 1.0, 'file': self.file, 'relay_data_accepted': 0,
                     'relay_forwarding_accepted': 6, 'relay_refusals': 0, 'relay_refusal_fraction': 0.0,
                     'contribution_transferred_bytes': 32}
        self.workers = {}
        for phase in ('preflight', 'load'):
            self.write(phase + '/driver.py', b'driver')
            self.write(phase + '/boundary-helper.py', b'helper')
            config = {'mode': 'relay-' + phase}
            if phase == 'load': config.update(load_seconds=1800, relay_schedule='gc2')
            self.workers[phase] = {'completed': True, 'children_stopped': True, 'route_relay_hops': 5,
                'relay_count': 6, 'config': config, 'build': {'manifest_sha256': digest(self.root / 'build.json'),
                'artifacts': self.build['artifacts'], 'sources': {p: {k: s[k] for k in
                    ('revision', 'snapshot_sha256')} for p, s in self.build['sources'].items()}}}
        self.workers['preflight']['relay_preflight'] = {'clients': 2, 'relay_restart': True,
                                                       'chat_acknowledged': 2, 'file': self.file}
        self.workers['load']['relay_load'] = self.load
        self.workers['load']['contributions'] = {'count': 32, 'listener_proofs': 32}
        for i in range(6):
            self.write('load/r' + str(i) + '/metrics.jsonl', canonical({'ts': 1500000, 'event': 'gc2_forward_accepted'}))
        for i in range(2, 34): self.write('load/c' + str(i) + '/contribution.json', {'transferred_bytes': 2})
        self.seal()

    def write(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value if isinstance(value, bytes) else canonical(value))

    def seal(self):
        for phase, worker in self.workers.items():
            events = [{'event': 'file_export_verified', 'verified': True, **self.file}]
            if phase == 'load':
                events += [{'event': 'relay_load_started', 'clients': 64, 'channels': 4},
                           {'event': 'load_relay_restarted', 'relay': 0, 'unix_seconds': 2000}]
                events += [{'event': 'load_command_delivered', **record} for record in self.records]
            self.write(phase + '/events.jsonl', b''.join(canonical(e) for e in events))
            worker['evidence'] = {'events.jsonl': digest(self.root / phase / 'events.jsonl')}
            self.write(phase + '/worker.json', worker)
            report = {'scope': SCOPE, 'worker': worker, 'worker_exit': 0, 'retired_namespace_pids': [],
                      'fixture_host': self.binary, 'driver_sha256': hashlib.sha256(b'driver').hexdigest(),
                      'helper_sha256': hashlib.sha256(b'helper').hexdigest(),
                      'evidence': {'worker.json': digest(self.root / phase / 'worker.json'), **worker['evidence']}}
            report.update({key: True for key in ('passed', 'host_links_unchanged', 'build_unchanged',
                                                 'tooling_unchanged', 'fixture_host_unchanged')})
            self.write(phase + '/report.json', report)
        self.summary = {'schema': 1, 'kind': 'relay_load', 'release_id': self.manifest['release_id'],
                        'sources': self.manifest['sources'], 'provider': self.provider, 'passed': True,
                        'source_unchanged': True, 'evidence': {p.relative_to(self.root).as_posix(): digest(p)
                            for p in self.root.rglob('*') if p.is_file() and p.name != 'summary.json'}}
        self.write('summary.json', self.summary)

    def check(self):
        return verify(self.root, self.manifest, self.provider)

    def test_original_64_client_gate_passes_with_final_contribution_growth(self):
        self.assertEqual(self.check(), self.summary)

    def test_passed_flags_do_not_replace_actual_campaign_duration(self):
        for key, value in [('seconds', 60), ('observed_seconds', 1799), ('completed_unix', 2799),
                           ('attempts', 719), ('relay_restart', False), ('clients', 63)]:
            old = self.load[key]; self.load[key] = value; self.seal()
            with self.subTest(key=key), self.assertRaises(EvidenceError): self.check()
            self.load[key] = old

    def test_latency_boundary_is_strict_and_recomputed(self):
        for record in self.records:
            record['recipient_seconds'] = [5.0] * record['recipients']
            record['authenticated_ack_seconds'] = 6.0
        self.load['recipient_p95_seconds'] = 5.0
        self.seal()
        with self.assertRaisesRegex(EvidenceError, 'latency'): self.check()

    def test_missing_recipient_and_duplicate_commands_fail(self):
        self.records[0]['recipient_seconds'].pop(); self.seal()
        with self.assertRaises(EvidenceError): self.check()
        self.records[0]['recipient_seconds'].append(1.0)
        self.records[1]['id'] = self.records[0]['id']; self.seal()
        with self.assertRaisesRegex(EvidenceError, 'duplicate'): self.check()

    def test_raw_refusals_cannot_be_hidden_by_summary(self):
        self.write('load/r0/metrics.jsonl', canonical({'ts': 1500000, 'event': 'gc2_forward_refused'}))
        self.seal()
        with self.assertRaisesRegex(EvidenceError, 'refusal'): self.check()

    def test_omitted_original_artifact_or_tampered_log_fails(self):
        (self.root / 'load/driver.py').write_bytes(b'changed')
        with self.assertRaises(EvidenceError): self.check()
        self.write('load/driver.py', b'driver'); self.seal()
        del self.summary['evidence']['load/c2/contribution.json']
        self.write('summary.json', self.summary)
        with self.assertRaisesRegex(EvidenceError, 'contribution'): self.check()

    def test_production_relay_receipt_binds_exact_loaded_binary_and_original_attempt(self):
        from linux_build_artifacts import SERVICE_COMMAND, SERVICES, TARGET
        from release_relay_load import verify_production_relay
        receipt = {'schema': 1, 'kind': 'linux_native_services', 'passed': True,
                   'release_id': self.manifest['release_id'], 'sources': self.manifest['sources'],
                   'provider': self.provider, 'target': TARGET, 'commands': [SERVICE_COMMAND],
                   'rustflags': '', 'rustc': 'rustc1\nhost: ' + TARGET + '\n',
                   'compiler_environment': {'RUSTFLAGS': '', 'CARGO_ENCODED_RUSTFLAGS': '', 'CARGO_BUILD_TARGET': ''},
                   'files': {n: 'e' * 64 for n in SERVICES}}
        def check(value, loaded_sha='e' * 64):
            self.write('native-services.json', value)
            sha = digest(self.root / 'native-services.json')
            build = {'provided_relay': {'receipt': value, 'receipt_sha256': sha},
                     'artifacts': {'gcnode': {'sha256': loaded_sha}}}
            verify_production_relay(self.root, build, self.manifest, {**self.provider, 'run_attempt': 2},
                                    {'evidence': {'native-services.json': sha}})
        check(receipt)
        for change in ({'sources': {}}, {'commands': [['cargo', 'build']]}, {'target': 'other'},
                       {'provider': {**self.provider, 'run_id': '999'}},
                       {'provider': {**self.provider, 'run_attempt': 3}}, {'rustflags': '-Copt-level=0'},
                       {'compiler_environment': {**receipt['compiler_environment'], 'CARGO_PROFILE_RELEASE_LTO': 'off'}}):
            with self.subTest(change=change), self.assertRaises(EvidenceError): check({**receipt, **change})
        with self.assertRaisesRegex(EvidenceError, 'retained production binary'): check(receipt, 'a' * 64)

    def test_source_provider_and_cleanup_must_match(self):
        bad = copy.deepcopy(self.manifest); bad['sources']['gchat']['commit'] = '9' * 40
        with self.assertRaises(EvidenceError): verify(self.root, bad, self.provider)
        with self.assertRaises(EvidenceError): verify(self.root, self.manifest, {**self.provider, 'run_id': '124'})
        self.workers['load']['children_stopped'] = False; self.seal()
        with self.assertRaisesRegex(EvidenceError, 'clean up'): self.check()

    def test_collector_never_dispatches_a_missing_original_request(self):
        with patch('release_relay_load.gh', side_effect=AssertionError('no dispatch')):
            self.assertIsNone(collect(self.root / 'state', self.manifest, self.root / 'receipt.json'))

    def test_collector_reconciles_original_request_and_rejects_duplicate_or_failed_run(self):
        state = self.root / 'state'; build = job(state, self.manifest, 'linux-x86_64', 'build')
        build.mkdir(parents=True); (build / 'dispatch.json').write_text('{}')
        run = {'id': 123, 'run_attempt': 1, 'display_title': 'Forgejo Linux ' + build.name,
               'head_sha': self.manifest['sources']['gchat']['commit'], 'event': 'workflow_dispatch',
               'head_repository': {'full_name': 'IggyGG/gchat'}, 'path': '.github/workflows/linux-release.yml',
               'status': 'in_progress'}
        with patch('release_relay_load.gh', side_effect=[{'workflow_runs': [run]}, {'jobs': []}]) as called:
            self.assertIsNone(collect(state, self.manifest, self.root / 'receipt.json'))
            self.assertEqual(called.call_count, 2)
        (build / 'run.json').unlink()
        with patch('release_relay_load.gh', return_value={'workflow_runs': [run, run]}), self.assertRaises(ValueError):
            collect(state, self.manifest, self.root / 'receipt.json')
        failed = {**run, 'status': 'completed', 'conclusion': 'failure'}
        provider_job = {'id': 9, 'name': 'relay-load', 'run_id': 123, 'head_sha': run['head_sha'], 'run_attempt': 1,
               'status': 'completed', 'conclusion': 'failure'}
        with patch('release_relay_load.gh', side_effect=[{'workflow_runs': [failed]}, {'jobs': [provider_job]}]), \
                self.assertRaisesRegex(ValueError, 'native check relay-load failure'):
            collect(state, self.manifest, self.root / 'receipt.json')

    def test_collector_authenticates_retained_archive_and_never_rebuilds(self):
        evidence = [p for p in self.root.rglob('*') if p.is_file()]
        state = self.root / 'state'; build = job(state, self.manifest, 'linux-x86_64', 'build')
        build.mkdir(parents=True); (build / 'dispatch.json').write_text('{}')
        output = self.root / 'collector/receipt.json'
        output.parent.mkdir()
        archive = output.parent / 'relay-load.zip'
        with zipfile.ZipFile(archive, 'w') as bundle:
            for path in evidence: bundle.write(path, path.relative_to(self.root).as_posix())
        run = {'id': 123, 'run_attempt': 1, 'display_title': 'Forgejo Linux ' + build.name,
               'head_sha': self.manifest['sources']['gchat']['commit'], 'event': 'workflow_dispatch',
               'head_repository': {'full_name': 'IggyGG/gchat'}, 'path': '.github/workflows/linux-release.yml',
               'status': 'completed', 'conclusion': 'success'}
        artifact = {'id': 456, 'name': 'relay-load-1', 'expired': False,
                    'digest': 'sha256:' + digest(archive), 'size_in_bytes': archive.stat().st_size,
                    'workflow_run': {'id': 123, 'head_sha': run['head_sha']}}
        job_attempt, job_conclusion = 1, 'success'
        def provider(path):
            if '/workflows/' in path: return {'workflow_runs': [run]}
            if path == 'actions/runs/123': return run
            if '/jobs?' in path:
                requested_attempt = int(path.split('/attempts/')[1].split('/')[0])
                if requested_attempt == job_attempt:
                    return {'jobs': [{'id': 9, 'name': 'relay-load', 'run_id': 123, 'head_sha': run['head_sha'],
                                     'run_attempt': job_attempt, 'status': 'completed', 'conclusion': job_conclusion}]}
                return {'jobs': [{'id': 10, 'name': 'qualify-gcoms', 'run_id': 123, 'head_sha': run['head_sha'],
                                 'run_attempt': requested_attempt, 'status': 'completed', 'conclusion': 'failure'}]}
            return {'artifacts': [artifact]}
        with patch('release_relay_load.gh', side_effect=provider), \
                patch('release_relay_load.subprocess.run', side_effect=AssertionError('no redispatch/download')):
            receipt = collect(state, self.manifest, output)
            self.assertTrue(receipt['relay_load_verified'])
            self.assertEqual(receipt['stage'], 'relay_load')
            self.assertFalse(receipt['provider_policy_qualified'])
            run.update(run_attempt=2, conclusion='failure')
            retained = collect(state, self.manifest, output)
            self.assertEqual(retained['provider']['run_attempt'], 1)
            self.assertEqual(retained['evidence'], receipt['evidence'])
            job_attempt, job_conclusion = 2, 'failure'
            with self.assertRaisesRegex(ValueError, 'native check relay-load failure.*attempt 2'):
                collect(state, self.manifest, output)
            job_attempt, job_conclusion = 1, 'success'
            archive.write_bytes(b'tampered')
            with self.assertRaisesRegex(EvidenceError, 'archive changed'):
                collect(state, self.manifest, output)

    def test_load_only_retry_runs_after_native_receipt_completion_once(self):
        state = self.root / 'state'; build = job(state, self.manifest, 'linux-x86_64', 'build')
        build.mkdir(parents=True); (build / 'dispatch.json').write_text('{}')
        original_receipt = b'{"passed": true, "retained": "original signed native artifact"}\n'
        (build / 'receipt.json').write_bytes(original_receipt)
        run = {'id': 123, 'run_attempt': 1, 'display_title': 'Forgejo Linux ' + build.name,
               'head_sha': self.manifest['sources']['gchat']['commit'], 'event': 'workflow_dispatch',
               'head_repository': {'full_name': 'IggyGG/gchat'}, 'path': '.github/workflows/linux-release.yml',
               'status': 'completed', 'conclusion': 'failure'}
        binding = {'schema': 1, 'release_id': self.manifest['release_id'], 'sources': self.manifest['sources'],
                   'platform': 'linux-x86_64', 'request_id': build.name, 'id': run['id']}
        (build / 'run.json').write_text(json.dumps(binding))
        authorize_native_retry(self.manifest, 'linux-x86_64', build, build.name, 'a' * 32)
        provider_job = {'id': 9, 'name': 'relay-load', 'run_id': 123, 'head_sha': run['head_sha'], 'run_attempt': 1,
                        'status': 'completed', 'conclusion': 'failure'}
        mutations = []
        def provider(path, **kwargs):
            if kwargs.get('method') == 'POST':
                mutations.append(path)
                self.assertEqual(json.loads((build / 'native-retry.json').read_text())['state'], 'intent')
                return None
            if '/jobs?' in path: return {'jobs': [provider_job]}
            self.assertEqual(path, 'actions/runs/123')
            return run
        with patch('release_relay_load.gh', side_effect=provider):
            self.assertIsNone(collect(state, self.manifest, self.root / 'receipt.json'))
            self.assertIsNone(collect(state, self.manifest, self.root / 'receipt.json'))
        self.assertEqual(mutations, ['actions/runs/123/rerun-failed-jobs'])
        self.assertEqual((build / 'receipt.json').read_bytes(), original_receipt)


if __name__ == '__main__': unittest.main()
