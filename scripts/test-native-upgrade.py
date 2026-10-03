#!/usr/bin/env python3
"""Qualify retained desktop applications on disposable native network profiles.

No application is compiled. Current/baseline archives, signatures and native
receipts are checked before baseline -> current -> baseline -> current recovery
and the original bounded current-binary interrupted-file journey.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import uuid

from release_jobs import gh, extract, acceptance_archive
from release_network_canary import module, verify_journey
from release_pair import validate
from release_signatures import verify as verify_gpg

network = module('test-native-network')
mac = module('macos-rollback')
windows = module('windows-rollback')
smoke = network.m
TARGETS = {'linux-x86_64': ('Linux', ('x86_64', 'AMD64')),
           'windows-x86_64': ('Windows', ('AMD64', 'x86_64')),
           'macos-aarch64': ('Darwin', ('arm64',)), 'macos-x86_64': ('Darwin', ('x86_64',))}


def validate_inputs(value):
    target = value.get('target')
    smoke.require(target in TARGETS, 'unsupported native acceptance target')
    # Reuse the strict provider identity and archive member path validation.
    mac.validate_inputs({**value, 'target': 'macos-x86_64'})
    for name in ('current', 'baseline'):
        item = value[name]
        smoke.require(item['conclusion'] == 'success', 'native acceptance needs a successful retained provider run')
        if target == 'windows-x86_64':
            executable = item['executable']
            smoke.require(executable['name'] == 'gchat-desktop.exe'
                          and type(executable['size']) is int and executable['size'] > 0
                          and re.fullmatch('[0-9a-f]{64}', executable['sha256']),
                          'invalid retained Windows executable identity')
    current, previous = value['current'], value['baseline']
    smoke.require(current['run'] != previous['run'] and current['artifact'] != previous['artifact']
                  and current['archive'] != previous['archive'] and current['sources'] != previous['sources'],
                  'upgrade acceptance requires distinct current and baseline releases')
    return value


def linux_acquire(name, spec, output):
    run = gh(f'actions/runs/{spec["run"]}')
    root = output / name; root.mkdir()
    archive = root / 'artifact.zip'
    artifact = acceptance_archive(spec, archive)
    retained = artifact is not None
    if not retained: artifact = gh(f'actions/artifacts/{spec["artifact"]}')
    smoke.require(run.get('status') == 'completed' and run.get('conclusion') == 'success'
                  and run.get('head_sha') == spec['controller']
                  and run.get('head_repository', {}).get('full_name') == 'IggyGG/gchat'
                  and run.get('path') == '.github/workflows/linux-release.yml'
                  and run.get('event') == 'workflow_dispatch'
                  and artifact.get('workflow_run', {}).get('id') == spec['run']
                  and (retained or artifact.get('expired') is False)
                  and artifact.get('digest') == 'sha256:' + spec['archive']
                  and type(artifact.get('size_in_bytes')) is int and 0 < artifact['size_in_bytes'] <= 12 * 1024**3,
                  'retained Linux provider identity differs')
    if not retained:
        with archive.open('xb') as stream:
            subprocess.run(['gh', 'api', f'repos/IggyGG/gchat/actions/artifacts/{spec["artifact"]}/zip'],
                           stdout=stream, stderr=subprocess.PIPE, check=True, timeout=600)
    smoke.require(smoke.digest(archive) == spec['archive'] and archive.stat().st_size == artifact['size_in_bytes'],
                  'retained Linux archive differs')
    extract(archive, root / 'original')
    manifest = root / 'original' / spec['manifest']; build = json.loads(manifest.read_text())
    smoke.require(build['target'] == 'linux-x86_64' and build['sources'] == spec['sources'],
                  'retained Linux build binding differs')
    packages = [item for item in build['files'] if item['format'] == 'deb']
    smoke.require(len(packages) == 1 and Path(packages[0]['name']).name == packages[0]['name'],
                  'one retained Debian installer required')
    package = manifest.parent / packages[0]['name']
    smoke.require(smoke.digest(package) == packages[0]['sha256'], 'retained installer bytes changed')
    verify_gpg(package.with_name(package.name + '.asc'), package, 'F4F6F8550D2AA952A189640D58430838AA3230BB')
    subprocess.run(['dpkg-deb', '--extract', str(package), str(root / 'package')],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
    binary = root / 'package/usr/bin/gchat-desktop'
    smoke.require(binary.is_file() and not binary.is_symlink(), 'regular packaged application required')
    native = manifest.parent / 'provenance/native-ci.json'
    smoke.validate_artifacts(binary, manifest, native)
    return {'binary': binary, 'build_manifest': manifest, 'native_receipt': native,
            'build': build, 'archive_sha256': spec['archive'], 'signature': {'gpg_verified': True}}


def rollback(current, baseline, invitation, output):
    report = {'schema': 1, 'passed': False, 'phases': []}
    args = argparse.Namespace(binary=baseline['binary'], build_manifest=baseline['build_manifest'],
        native_receipt=baseline['native_receipt'], invitation=invitation, output=output,
        bytes=network.PIECE, binary_sha256=smoke.digest(baseline['binary']))
    journey = network.Journey(args)
    binaries = {name: smoke.digest(item['binary']) for name, item in (('current', current), ('baseline', baseline))}
    try:
        smoke.require(current['build']['publisher'] == baseline['build']['publisher'], 'rollback publisher changed')
        smoke.require(binaries['current'] != binaries['baseline'], 'upgrade acceptance needs different installed binaries')
        for i in (0, 1): journey.start_client(i, True)
        journey.channel = journey.submit(0, '/create #upgrade sender')['conversation']
        code = journey.invitation()
        journey.join_peer(code)
        journey.chat('baseline-initial')
        ident = uuid.uuid4().hex; data = hashlib.shake_256(b'release-rollback-cache').digest(network.PIECE)
        expected = hashlib.sha256(data).hexdigest()
        journey.files(0, 'prepare', id=ident, conversation=journey.channel, name='rollback.bin', size_bytes=str(network.PIECE))
        journey.io(0, ident, 0, True, data); journey.files(0, 'commit', id=ident)
        journey.until(lambda: journey.row(1, ident)); journey.files(1, 'accept', id=ident)
        journey.until(lambda: journey.row(1, ident)['state'] == 'complete')
        smoke.require(journey.export(ident) == expected, 'initial cached export differs')
        for name, item in (('upgraded', current), ('baseline', baseline), ('restored', current)):
            before = {i: journey.history(i) for i in (0, 1)}
            for i in (0, 1): journey.stop(i)
            args.binary = item['binary']
            for i in (0, 1):
                journey.start_client(i, False)
                smoke.require(journey.history(i) == before[i], 'retained history changed across replacement')
            smoke.require(journey.export(ident) == expected, 'encrypted cache changed across replacement')
            journey.chat(name)
            report['phases'].append({'phase': name, 'binary_sha256': smoke.digest(item['binary']),
                'same_identity': True, 'history_retained': True, 'cache_sha256': expected,
                'authenticated_bidirectional_ack': True})
        report['passed'] = True
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        results = []
        for _, process, stop, log in reversed(journey.children):
            try:
                if process.poll() is None: results.append(smoke.stop_service(process, stop, 10))
            except Exception as error:
                report.setdefault('cleanup_errors', []).append(type(error).__name__)
                try:
                    if process.poll() is None: process.kill()
                    process.wait(timeout=10)
                except Exception as cleanup_error:
                    report['cleanup_errors'].append(type(cleanup_error).__name__)
            finally:
                log.close()
        report['cleanup_complete'] = all(process.poll() == 0 for _, process, _, _ in journey.children) and all(
            r['stopped'] and not r['forced'] and r['exit_code'] == 0 for r in results) and not report.get('cleanup_errors')
        report['children_stopped'] = all(process.poll() is not None for _, process, _, _ in journey.children)
        if report['children_stopped']:
            for i in journey.clients:
                try: shutil.rmtree(journey.root / f'c{i}')
                except FileNotFoundError: pass
                except OSError as error:
                    report.setdefault('cleanup_errors', []).append(type(error).__name__)
        report['profiles_removed'] = all(not (journey.root / f'c{i}').exists() for i in journey.clients)
        report['elapsed_seconds'] = time.monotonic() - journey.start
        report['events'] = journey.report['events']
        report['binaries_unchanged'] = binaries == {name: smoke.digest(item['binary']) for name, item in
                                                   (('current', current), ('baseline', baseline))}
        report['passed'] = report['passed'] and report['cleanup_complete'] and report['profiles_removed'] and report['binaries_unchanged'] and report['elapsed_seconds'] <= 600
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); value = validate_inputs(json.loads(args.inputs.read_text()))
    manifest = validate(json.loads(args.manifest.read_text())); target = value['target']
    smoke.require(os.environ.get('GITHUB_ACTIONS') == 'true' and platform.system() == TARGETS[target][0]
                  and platform.machine() in TARGETS[target][1], 'isolated matching native worker required')
    smoke.require(value['current']['sources'] == {k: v['commit'] for k, v in manifest['sources'].items()}, 'acceptance candidate differs')
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False); smoke.private_directory(output)
    report = {'schema': 1, 'passed': False, 'platform': target, 'release_id': manifest['release_id'],
              'sources': manifest['sources'], 'commands': [], 'application_rebuilt': False,
              'personal_profiles_accessed': False, 'rendered_gui_qualified': False}
    invitation = output / 'invitation.private'; commands = mac.installer.Commands(output, report)
    mac.MOUNTS.clear()
    try:
        code = os.environ.pop('GCHAT_NETWORK_INVITATION', '')
        smoke.require(0 < len(code.encode()) <= 180000, 'missing bounded fixture invitation')
        invitation.write_text(code); smoke.private_fixture_path(invitation, directory=False)
        if target.startswith('macos'):
            mac.INPUTS.clear(); mac.INPUTS.update(value)
            items = {name: mac.acquire(name, output, commands) for name in ('current', 'baseline')}
        elif target == 'windows-x86_64':
            windows.retained.RETAINED.update({name: {**value[name], 'conclusion': 'success'} for name in ('current', 'baseline')})
            items = {name: windows.acquire(name, output, commands) for name in ('current', 'baseline')}
        else:
            items = {name: linux_acquire(name, value[name], output) for name in ('current', 'baseline')}
        report['artifacts'] = {name: {'archive_sha256': item['archive_sha256'], 'binary_sha256': smoke.digest(item['binary']),
                                    'sources': item['build']['sources']} for name, item in items.items()}
        proof = rollback(items['current'], items['baseline'], invitation, output / 'rollback')
        smoke.require(proof['passed'], 'native profile/history/cache rollback failed')
        item = items['current']
        journey = network.Journey(argparse.Namespace(binary=item['binary'], build_manifest=item['build_manifest'],
            native_receipt=item['native_receipt'], invitation=invitation, output=output / 'network',
            bytes=manifest['policy']['file_qualification']['bytes'], binary_sha256=smoke.digest(item['binary'])))
        smoke.require(journey.run() == 0, 'bounded installed-network recovery failed')
        verify_journey(journey.report, manifest)
        smoke.require(journey.report['inputs']['sources'] == manifest['sources'], 'installed-network source binding differs')
        report['passed'] = True
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        invitation.unlink(missing_ok=True)
        report['invitation_removed'] = not invitation.exists()
        stopped = True
        for stage in ('rollback', 'network'):
            path = output / stage
            if path.exists():
                receipt = path / 'report.json'
                stopped = stopped and receipt.is_file() and json.loads(receipt.read_text()).get('children_stopped') is True
        cleanups = []
        for index, (work, mount) in enumerate(reversed(mac.MOUNTS)):
            cleanup_output = output / ('cleanup-' + str(index)); cleanup_output.mkdir()
            cleanup_commands = mac.installer.Commands(cleanup_output, report)
            cleanups.append(mac.installer.cleanup_installation(cleanup_commands, work, mount, True, stopped))
        report['installation_cleanup'] = cleanups
        report['passed'] = report['passed'] and report['invitation_removed'] and all(c['passed'] for c in cleanups)
        report['completed_at'] = int(time.time())
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'error': report.get('error')}))
    return 0 if report['passed'] else 1


if __name__ == '__main__': sys.exit(main())
