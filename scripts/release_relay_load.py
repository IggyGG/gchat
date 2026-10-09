#!/usr/bin/env python3
"""Collect original relay evidence and reconcile explicitly authorized same-run retries."""
from release_provider import github_download
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess

from release_coordinator import atomic_json
from release_evidence import digest, file_reference, read_json, require
from release_jobs import (REPO, extract, gh, resolve_run, native_checks, retry_failed_jobs,
                          require_passed_checks)
from release_pair import canonical, validate
from release_publish import job

SCOPE = 'actual_gchat_disconnected_fivehop_turnover_v2'
SHA = re.compile('[0-9a-f]{64}')
MEMBERS = [17, 17, 17, 16]


def number(value, label, minimum=0):
    require(type(value) in (int, float) and math.isfinite(value) and value >= minimum,
            'invalid relay load number: ' + label)
    return value


def integer(value, label, minimum=0):
    require(type(value) is int and value >= minimum, 'invalid relay load integer: ' + label)
    return value


def references(root, values):
    require(isinstance(values, dict) and values, 'relay evidence inventory is missing')
    for name, sha in values.items():
        file_reference(root, {'path': name, 'sha256': sha})


def event_rows(path):
    with path.open() as stream:
        for line in stream:
            value = json.loads(line)
            require(isinstance(value, dict), 'relay event must be an object')
            yield value


def file_export(events, transfer):
    require(transfer.get('size') == 5235248 and SHA.fullmatch(str(transfer.get('sha256', ''))),
            'DS-sized file identity is missing')
    matches = [e for e in events if e.get('event') == 'file_export_verified'
               and e.get('id') == transfer.get('id')]
    require(len(matches) == 1 and matches[0].get('verified') is True and
            all(matches[0].get(k) == transfer[k] for k in ('size', 'sha256')),
            'original hash-verified DS file export is missing')


def fixture(root, name, build, summary):
    directory = root / name
    report, worker = read_json(directory / 'report.json'), read_json(directory / 'worker.json')
    require(report.get('scope') == SCOPE and report.get('worker') == worker,
            'original relay fixture reports disagree')
    require(report.get('worker_exit') == 0 and type(report.get('worker_exit')) is int and
            worker.get('completed') is True and worker.get('children_stopped') is True and
            not worker.get('failure') and report.get('retired_namespace_pids') == [],
            'relay fixture did not complete and clean up')
    for key in ('passed', 'host_links_unchanged', 'build_unchanged', 'tooling_unchanged', 'fixture_host_unchanged'):
        require(report.get(key) is True, 'relay fixture failed ' + key)
    references(directory, report.get('evidence'))
    references(directory, worker.get('evidence'))
    require(worker.get('build', {}).get('manifest_sha256') == digest(root / 'build.json') and
            worker['build'].get('artifacts') == build['artifacts'], 'fixture build identity changed')
    for project in ('gchat', 'gcoms'):
        source = build['sources'][project]
        require(worker['build']['sources'].get(project) ==
                {key: source[key] for key in ('revision', 'snapshot_sha256')},
                'fixture source snapshot changed')
    for name_, field, source_path in (
            ('driver.py', 'driver_sha256', 'scripts/gchat-turnover.py'),
            ('boundary-helper.py', 'helper_sha256', 'scripts/privacy-client-capture.py')):
        require(report.get(field) == build['sources']['gcoms']['files'].get(source_path) ==
                digest(directory / name_), 'fixture driver differs from frozen source')
    host = report.get('fixture_host', {})
    require(all(host.get(k) == build['artifacts']['turnover_daemon'][k] for k in ('size', 'sha256')),
            'fixture executable differs from source-bound build')
    for evidence in (report['evidence'], worker['evidence']):
        require(all(summary['evidence'].get(name + '/' + path) == sha for path, sha in evidence.items()),
                'summary omitted original fixture evidence')
    events = list(event_rows(directory / 'events.jsonl'))
    require(worker.get('route_relay_hops') == 5 and worker.get('relay_count', 0) >= 6,
            'protected five-hop fixture is missing')
    return worker, events


def verify_production_relay(root, build, manifest, provider, summary):
    """New workers load-test the same production gcnode later put in the images."""
    supplied = build.get('provided_relay')
    if supplied is None: return  # Original frozen workers built their fixture directly.
    from linux_build_artifacts import SERVICE_COMMAND, SERVICES, TARGET
    receipt = read_json(root / 'native-services.json')
    require(supplied == {'receipt': receipt, 'receipt_sha256': digest(root / 'native-services.json')}
            and summary['evidence'].get('native-services.json') == supplied['receipt_sha256'],
            'production relay receipt is not retained in the load evidence')
    origin = receipt.get('provider', {})
    require(receipt.get('schema') == 1 and receipt.get('kind') == 'linux_native_services'
            and receipt.get('passed') is True and receipt.get('release_id') == manifest['release_id']
            and receipt.get('sources') == manifest['sources'] and receipt.get('target') == TARGET
            and receipt.get('commands') == [SERVICE_COMMAND] and receipt.get('rustflags') == ''
            and receipt.get('compiler_environment') == {'RUSTFLAGS': '', 'CARGO_ENCODED_RUSTFLAGS': '', 'CARGO_BUILD_TARGET': ''}
            and isinstance(receipt.get('rustc'), str) and f'host: {TARGET}\n' in receipt['rustc'],
            'production relay source, target or build command changed')
    require(all(origin.get(k) == provider[k] for k in ('repository', 'run_id', 'workflow_commit'))
            and type(origin.get('run_attempt')) is int and 1 <= origin['run_attempt'] <= provider['run_attempt'],
            'production relay belongs to another source/run/attempt')
    inventory = receipt.get('files', {})
    require(set(inventory) == set(SERVICES) and all(SHA.fullmatch(str(h)) for h in inventory.values())
            and build['artifacts']['gcnode']['sha256'] == inventory['gcnode'],
            'load-tested relay differs from the retained production binary')


def verify(root, manifest, provider):
    """Derive the gate from retained worker observations, not a passed flag."""
    root = Path(root)
    summary = read_json(root / 'summary.json')
    require(summary.get('schema') == 1 and summary.get('kind') == 'relay_load' and
            summary.get('release_id') == manifest['release_id'] and summary.get('sources') == manifest['sources'] and
            summary.get('provider') == provider and summary.get('source_unchanged') is True and
            summary.get('passed') is True, 'relay load summary source/provider identity failed')
    references(root, summary.get('evidence'))
    required = {'build.json', 'preflight/report.json', 'preflight/worker.json', 'load/report.json', 'load/worker.json'}
    required |= {phase + '/' + name for phase in ('preflight', 'load')
                 for name in ('driver.py', 'boundary-helper.py', 'events.jsonl')}
    require(required <= set(summary['evidence']), 'relay gate lacks original reports')
    build = read_json(root / 'build.json')
    require(build.get('passed') is True and set(build.get('sources', {})) == {'gchat', 'gcoms'},
            'source-bound fixture build did not pass')
    for project in ('gchat', 'gcoms'):
        source = build['sources'][project]
        require(source.get('unchanged') is True and source.get('revision') == manifest['sources'][project]['commit'] and
                source.get('snapshot_sha256') == hashlib.sha256(json.dumps(source['files'], sort_keys=True).encode()).hexdigest(),
                'fixture build source snapshot does not match candidate')
    require(set(build.get('artifacts', {})) == {'gcnode', 'gchat', 'fleet_probe', 'turnover_daemon'},
            'fixture build executable inventory changed')
    for binary in build['artifacts'].values():
        require(SHA.fullmatch(str(binary.get('sha256', ''))) and integer(binary.get('size'), 'binary size', 1),
                'invalid fixture executable identity')
    verify_production_relay(root, build, manifest, provider, summary)
    preflight, preflight_events = fixture(root, 'preflight', build, summary)
    short = preflight.get('relay_preflight', {})
    require(preflight.get('config', {}).get('mode') == 'relay-preflight' and short.get('clients') == 2 and
            short.get('relay_restart') is True and integer(short.get('chat_acknowledged'), 'preflight ACKs', 2),
            'relay preflight did not pass restart and delivery')
    file_export(preflight_events, short.get('file', {}))
    worker, events = fixture(root, 'load', build, summary)
    config, load = worker.get('config', {}), worker.get('relay_load', {})
    require(config.get('mode') == 'relay-load' and config.get('load_seconds') == 1800 and
            config.get('relay_schedule') == 'gc2' and load.get('clients') == 64 and load.get('seconds') == 1800 and
            load.get('topology') == 'fleet-four-channels' and load.get('channels') == 4 and
            load.get('channel_members') == MEMBERS and load.get('recipient_deliveries_per_round') == 63,
            'relay load topology or duration changed')
    started = number(load.get('started_unix'), 'campaign start', 1)
    completed = number(load.get('completed_unix'), 'campaign completion', started + 1800)
    require(completed - started <= 1920 and
            1800 <= number(load.get('observed_seconds'), 'observed campaign duration') <= 1920,
            'relay load did not run and drain within original bound')
    starts = [e for e in events if e.get('event') == 'relay_load_started']
    restarts = [e for e in events if e.get('event') == 'load_relay_restarted']
    require(len(starts) == 1 and starts[0].get('clients') == 64 and starts[0].get('channels') == 4 and
            len(restarts) == 1 and restarts[0].get('relay') == 0 and
            started + 900 <= number(restarts[0].get('unix_seconds'), 'restart') <= completed and
            load.get('relay_restart') is True, 'mid-campaign relay restart is missing')
    records = load.get('authenticated_commands')
    require(isinstance(records, list) and len(records) == load.get('commands'), 'original command records are missing')
    observed = [{k: v for k, v in e.items() if k not in ('event', 'unix_seconds', 'elapsed')}
                for e in events if e.get('event') == 'load_command_delivered']
    require(records == observed, 'load command summary differs from original delivery events')
    attempts = integer(load.get('attempts'), 'attempts', 720)
    refused = integer(load.get('application_refusals'), 'application refusals')
    require(len(records) + refused == attempts, 'load commands were lost or left pending')
    latency, ids, channels = [], set(), set()
    for record in records:
        channel = integer(record.get('channel_index'), 'channel')
        require(channel < 4 and record.get('recipients') == MEMBERS[channel] - 1 and
                isinstance(record.get('id'), str) and record['id'] and record['id'] not in ids,
                'duplicate command or incorrect recipient count')
        ids.add(record['id']); channels.add(channel)
        seconds = record.get('recipient_seconds')
        require(isinstance(seconds, list) and len(seconds) == record['recipients'], 'missing recipient delivery')
        latency.extend(number(value, 'recipient latency') for value in seconds)
        require(number(record.get('authenticated_ack_seconds'), 'authenticated ACK') >= max(seconds),
                'authenticated sender ACK preceded recipient observation')
    require(channels == set(range(4)) and latency, 'all four operator channels must deliver')
    latency.sort()
    p95 = latency[min(len(latency) - 1, (len(latency) * 95 + 99) // 100 - 1)]
    require(p95 == load.get('recipient_p95_seconds') and p95 < 5 and
            refused / attempts == load.get('application_refusal_fraction') and refused / attempts < .01,
            'relay load command latency or refusal gate failed')
    file_export(events, load.get('file', {}))
    counts = {'relay_data_accepted': 0, 'relay_forwarding_accepted': 0, 'relay_refusals': 0}
    metrics = [path for path in summary['evidence'] if re.fullmatch(r'load/r[0-9]+/metrics\.jsonl(?:\.[0-9]+)?', path)]
    require({path.split('/')[1] for path in metrics} == {'r' + str(i) for i in range(worker['relay_count'])},
            'every relay needs its original refusal metrics')
    for path in metrics:
        for row in event_rows(root / path):
            timestamp = number(row.get('ts', 0), 'metric timestamp') / 1000
            if not started <= timestamp <= completed:
                continue
            event = row.get('event')
            if event == 'gchat_push_accepted' and row.get('kind') in ('data', 'duplicate'):
                counts['relay_data_accepted'] += 1
            if event == 'gc2_forward_accepted': counts['relay_forwarding_accepted'] += 1
            if event == 'gc2_forward_refused' or (event == 'gchat_queue_refused' and
                    row.get('reason') in ('queue_full', 'store_capacity', 'replay_capacity')):
                counts['relay_refusals'] += 1
    fraction = counts['relay_refusals'] / max(1, sum(counts.values()))
    require(all(load.get(k) == v for k, v in counts.items()) and
            fraction == load.get('relay_refusal_fraction') and fraction < .01,
            'relay refusal summary differs from original metrics or exceeds gate')
    carried = 0
    for i in range(2, 34):
        path = 'load/c' + str(i) + '/contribution.json'
        require(path in summary['evidence'], 'original sharing contribution observation is missing')
        carried += integer(read_json(root / path).get('transferred_bytes'), 'contributed bytes')
    require(carried >= integer(load.get('contribution_transferred_bytes'), 'observed contributed bytes', 1) and
            worker.get('contributions', {}).get('count') == 32 and
            worker['contributions'].get('listener_proofs') == 32, 'desktop contribution traffic was not observed')
    return summary


def collect(state, manifest, output):
    state, output = Path(state), Path(output)
    build = job(state, manifest, 'linux-x86_64', 'build')
    if not (build / 'dispatch.json').is_file(): return None
    request_id = build.name
    run = resolve_run(manifest, 'linux-x86_64', build, request_id, api=gh)
    if run is None: return None
    checks = native_checks(run, 'linux-x86_64', build, api=gh)
    retrying = retry_failed_jobs(manifest, 'linux-x86_64', build, request_id, run, checks, api=gh)
    if retrying and checks['jobs'].get('relay-load', {}).get('conclusion') != 'success': return None
    if not require_passed_checks(checks, ('relay-load',)): return None
    # Failed-job retries omit successful jobs. The passing job's own attempt,
    # rather than the workflow's newest attempt, binds the original evidence.
    attempt = checks['jobs']['relay-load']['attempt']
    inventory = gh(f'actions/runs/{run["id"]}/artifacts?per_page=100')['artifacts']
    artifacts = [a for a in inventory if a.get('name') == 'relay-load-' + str(attempt)]
    require(len(artifacts) == 1 and artifacts[0].get('expired') is False, 'original relay load artifact is missing or ambiguous')
    artifact = artifacts[0]
    require(re.fullmatch('sha256:[0-9a-f]{64}', str(artifact.get('digest', ''))),
            'provider relay load artifact digest is missing')
    sha = artifact['digest'].removeprefix('sha256:')
    integer(artifact.get('id'), 'provider artifact ID', 1)
    require(0 < integer(artifact.get('size_in_bytes'), 'archive size') <= 2 * 1024**3,
            'relay load archive digest or size is invalid')
    binding = artifact.get('workflow_run', {})
    require(binding.get('id') == run['id'] and binding.get('head_sha') == run['head_sha'],
            'relay load artifact belongs to another run')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Preserve legacy attempt1 paths; later attempts have independent closures.
    suffix = '' if attempt == 1 else '-' + str(attempt)
    archive = output.parent / ('relay-load' + suffix + '.zip')
    if not archive.exists():
        temporary = output.parent / ('relay-load' + suffix + '.partial')
        with temporary.open('wb') as stream:
            github_download(f'actions/artifacts/{artifact["id"]}/zip', repo=REPO, stream=stream, timeout=600)
        require(digest(temporary) == sha, 'relay load archive download hash mismatch')
        os.replace(temporary, archive)
    require(digest(archive) == sha, 'retained relay load archive changed')
    root = output.parent / ('relay-load' + suffix)
    # An immutable archive is extracted once; incomplete extraction is never accepted.
    if not root.exists():
        temporary = output.parent / ('.relay-load-extract' + suffix)
        if temporary.exists(): shutil.rmtree(temporary)
        extract(archive, temporary)
        os.replace(temporary, root)
    provider = {'repository': REPO, 'run_id': str(run['id']), 'run_attempt': attempt,
                'workflow_commit': run['head_sha']}
    verify(root, manifest, provider)
    return {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
            'platform': 'linux-x86_64', 'stage': 'relay_load', 'passed': True, 'source_unchanged': True,
            'relay_load_verified': True,
            'provider': provider, 'qualified_scopes': ['relay_capacity_64', 'covered_delivery', 'relay_restart', 'ds_sized_file'],
            'provider_policy_qualified': False, 'privacy_qualified': False,
            'evidence': [{'path': archive.name, 'sha256': sha},
                         {'path': root.name + '/summary.json', 'sha256': digest(root / 'summary.json')}],
            'summary_sha256': digest(root / 'summary.json')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    args = parser.parse_args()
    require(os.environ.get('GCHAT_RELEASE_TARGET') == 'linux-x86_64', 'relay load requires the Linux release lane')
    manifest = validate(read_json(os.environ['GCHAT_RELEASE_MANIFEST']))
    output = Path(os.environ['GCHAT_RELEASE_RECEIPT'])
    result = collect(args.state, manifest, output)
    if result is None: raise SystemExit(75)
    atomic_json(output, result)


if __name__ == '__main__':
    from release_provider import worker_main
    worker_main(main)
