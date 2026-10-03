#!/usr/bin/env python3
"""Run a real covered network journey from a qualified Linux provider package."""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import select
import signal
import sys
import tempfile
import time
import zipfile

from release_coordinator import atomic_json, read_receipt
from release_feed import digest
from release_host_worker import ssh
from release_pair import canonical, validate
from release_publish import job


def module(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), Path(__file__).with_name(name + '.py'))
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def acquire(state, manifest, work):
    build_job = job(state, manifest, 'linux-x86_64', 'build')
    for stage in ('build', 'verify'):
        receipt = job(state, manifest, 'linux-x86_64', stage) / 'receipt.json'
        if not receipt.is_file(): return None
        read_receipt(receipt, manifest, 'linux-x86_64', stage)
    proof, _ = read_receipt(build_job / 'receipt.json', manifest, 'linux-x86_64', 'build')
    archive = build_job / 'native.zip'
    if not any(e['path'] == 'native.zip' and e['sha256'] == digest(archive) for e in proof['evidence']):
        raise ValueError('canary provider archive has no verified build binding')
    with zipfile.ZipFile(archive) as source:
        names = source.namelist()
        reports = [n for n in names if n.endswith('build.json') and not any(
            part in ('inputs', 'build', 'native-tests', 'infrastructure') for part in Path(n).parts[:-1])]
        if len(reports) != 1 or len(names) != len(set(names)):
            raise ValueError('canary needs one unambiguous native installer report')
        build = json.loads(source.read(reports[0]))
        if build.get('sources') != {k: v['commit'] for k, v in manifest['sources'].items()} or build.get('target') != 'linux-x86_64':
            raise ValueError('canary package differs from frozen source pair')
        packages = [f for f in build['files'] if f['format'] == 'deb']
        if len(packages) != 1 or Path(packages[0]['name']).name != packages[0]['name']:
            raise ValueError('canary needs one qualified Debian package')
        prefix = reports[0][:-len('build.json')]
        (work / 'build.json').write_bytes(source.read(reports[0]))
        (work / 'native-ci.json').write_bytes(source.read(prefix + 'provenance/native-ci.json'))
        package = work / 'package.deb'
        with source.open(prefix + packages[0]['name']) as incoming, package.open('xb') as output:
            shutil.copyfileobj(incoming, output)
        if digest(package) != packages[0]['sha256']:
            raise ValueError('canary package bytes changed')
    import subprocess
    extracted = work / 'package'
    subprocess.run(['dpkg-deb', '--extract', str(package), str(extracted)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
    binary = extracted / 'usr/bin/gchat'
    if not binary.is_file() or binary.is_symlink():
        raise ValueError('qualified installer has no regular CLI executable')
    smoke = module('test-native-cli').smoke
    smoke.validate_artifacts(binary, work / 'build.json', work / 'native-ci.json')
    return binary


def verify_journey(report, manifest):
    acknowledgments = [e for e in report.get('events', []) if e.get('event') == 'authenticated_ack']
    expected = manifest['policy']['file_qualification']['bytes']
    check = report.get('file_check', {})
    completion, elapsed = check.get('completion_elapsed_seconds'), report.get('elapsed_seconds')
    if any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0
           for value in (completion, elapsed)) or completion > elapsed:
        raise ValueError('canary durations must be finite positive measurements')
    if (report.get('mode', 'full') != 'full' or report.get('passed') is not True or report.get('inputs_unchanged') is not True
            or report.get('binary_unchanged') is not True or report.get('children_stopped') is not True
            or report.get('temporary_profile_removed') is not True or len(acknowledgments) < 6
            or {e.get('sender') for e in acknowledgments} != {0, 1}
            or check.get('bytes') != expected or check.get('abrupt_stop') is not True
            or check.get('verified_pieces_retained') is not True or check.get('hash_verified_after_reopen') is not True
            or check.get('completion_elapsed_seconds', float('inf')) > manifest['policy']['file_qualification']['completion_seconds']
            or report.get('elapsed_seconds', float('inf')) > manifest['policy']['file_qualification']['total_seconds']):
        raise ValueError('covered network delivery, bounded recovery or cleanup did not pass')


def verify_chat(report):
    acknowledgments = [e for e in report.get('events', []) if e.get('event') == 'authenticated_ack']
    elapsed = report.get('elapsed_seconds')
    if (report.get('mode') != 'chat' or report.get('passed') is not True
            or report.get('inputs_unchanged') is not True or report.get('binary_unchanged') is not True
            or report.get('children_stopped') is not True or report.get('temporary_profile_removed') is not True
            or len(acknowledgments) < 2 or {e.get('sender') for e in acknowledgments} != {0, 1}
            or type(elapsed) not in (int, float) or not math.isfinite(elapsed) or not 0 < elapsed <= 300):
        raise ValueError('covered bidirectional messaging or cleanup did not pass')


def interrupted_profiles(work, state):
    """Stop only services in this previously recorded disposable fixture."""
    work = Path(work).resolve()
    if not work.is_relative_to((Path(state) / 'tmp').resolve()) or not work.name.startswith('nc-'):
        raise ValueError('interrupted canary path escapes its private temporary root')
    binary = work / 'package/usr/bin/gchat'
    homes = {str(work / 'journey' / ('c' + str(i))) for i in (0, 1)}
    handles = []
    try:
        for process in Path('/proc').iterdir():
            if not process.name.isdigit(): continue
            try:
                args = (process / 'cmdline').read_bytes().split(b'\0')
                decoded = [os.fsdecode(a) for a in args if a]
                if not decoded or decoded[0] != str(binary) or '--home' not in decoded: continue
                if decoded[decoded.index('--home') + 1] not in homes: continue
                if (process / 'exe').resolve() != binary:
                    raise ValueError('interrupted canary executable identity changed')
                handle = os.pidfd_open(int(process.name))
                handles.append(handle)
                signal.pidfd_send_signal(handle, signal.SIGTERM)
            except (FileNotFoundError, ProcessLookupError):
                continue
        deadline = time.monotonic() + 15
        waiting = list(handles)
        while waiting:
            ready, _, _ = select.select(waiting, [], [], max(0, deadline - time.monotonic()))
            waiting = [h for h in waiting if h not in ready]
            if waiting and time.monotonic() >= deadline:
                for handle in waiting: signal.pidfd_send_signal(handle, signal.SIGKILL)
                raise ValueError('interrupted canary required forced process cleanup')
        for home in homes:
            if Path(home).exists(): shutil.rmtree(home)
        atomic_json(work / 'interrupted-cleanup.json', {'stopped': True, 'profiles_removed': True})
    finally:
        for handle in handles: os.close(handle)


def run(state, manifest, target, grant_config, output):
    import fcntl
    state, output = Path(state), Path(output)
    mode = target.get('network_check', 'full')
    if mode not in ('full', 'chat'):
        raise ValueError('unknown operator network check')
    owner = state / 'canaries'; owner.mkdir(mode=0o700, parents=True, exist_ok=True)
    key = hashlib.sha256(canonical([manifest['release_id'], target['id']])).hexdigest()
    with (owner / (key + '.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        intent = owner / (key + '.json')
        # A prior interrupted invocation's grant is revoked before new authority
        # is created. Container restarts stop its disposable service processes.
        if intent.is_file():
            previous = json.loads(intent.read_text())
            if previous.get('revoked') is not True:
                revoked = json.loads(ssh(grant_config, 'canary revoke ' + previous['operation'], b''))
                if revoked.get('revoked') is not True: raise ValueError('previous canary grant remains active')
                atomic_json(intent, {**previous, 'revoked': True})
            interrupted_profiles(previous['work'], state)
        temporary = state / 'tmp'; temporary.mkdir(mode=0o700, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix='nc-', dir=temporary))
        work.chmod(0o700)
        binary = acquire(state, manifest, work)
        if binary is None: return None
        operation = hashlib.sha256(canonical([key, str(work)])).hexdigest()
        atomic_json(intent, {'operation': operation, 'work': str(work), 'revoked': False})
        invitation = work / 'invitation'
        passed = False
        try:
            issued = json.loads(ssh(grant_config, 'canary grant ' + operation, b''))
            invitation.write_text(issued['invitation']); invitation.chmod(0o600)
            network = module('test-native-network')
            cli = module('test-native-cli')
            network.m.service_command = cli.service_command
            args = argparse.Namespace(binary=binary, build_manifest=work / 'build.json',
                native_receipt=work / 'native-ci.json', invitation=invitation, output=work / 'journey',
                bytes=manifest['policy']['file_qualification']['bytes'], binary_sha256=digest(binary), mode=mode)
            if network.Journey(args).run() != 0:
                raise ValueError('installed network canary failed; retain its journey report')
            report = json.loads((work / 'journey/report.json').read_text())
            if mode == 'full':
                verify_journey(report, manifest)
            else:
                verify_chat(report)
            if report['inputs']['sources'] != manifest['sources']:
                raise ValueError('installed network journey source binding differs')
            passed = True
        finally:
            invitation.unlink(missing_ok=True)
            revoked = json.loads(ssh(grant_config, 'canary revoke ' + operation, b''))
            if revoked.get('revoked') is not True: raise ValueError('canary grant revocation failed')
            atomic_json(intent, {'operation': operation, 'work': str(work), 'revoked': True, 'passed': passed})
        retained = output.parent / ('canary-' + operation)
        retained.mkdir(mode=0o700, exist_ok=True)
        evidence = []
        for path in (work / 'journey').iterdir():
            if path.is_file() and path.suffix in ('.json', '.log'):
                destination = retained / path.name; shutil.copyfile(path, destination)
                evidence.append({'path': destination.relative_to(output.parent).as_posix(), 'sha256': digest(destination)})
        atomic_json(retained / 'grant-cleanup.json', {'revoked': True, 'invitation_removed': not invitation.exists()})
        evidence.append({'path': (retained / 'grant-cleanup.json').relative_to(output.parent).as_posix(),
                         'sha256': digest(retained / 'grant-cleanup.json')})
        atomic_json(output, {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
            'target': target['id'], 'passed': True, 'authenticated_delivery': True, 'network_check': mode,
            'binary_sha256': digest(binary), 'completed_at': int(time.time()), 'evidence': evidence})
        return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--grant-config', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    # A bounded worker timeout must enter the journey's ordinary child cleanup.
    def terminate(_signal, _frame): raise RuntimeError('canary interrupted')
    signal.signal(signal.SIGTERM, terminate)
    manifest = validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()))
    target = json.loads(Path(os.environ['GCHAT_DEPLOYMENT_TARGET']).read_text())
    output = Path(os.environ['GCHAT_CANARY_RECEIPT'])
    if run(args.state, manifest, target, json.loads(args.grant_config.read_text()), output) is None:
        raise SystemExit(75)


if __name__ == '__main__': main()
