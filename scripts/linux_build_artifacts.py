"""Source-bound unsigned Linux outputs reused by qualification and packaging."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import re
import subprocess

from paired_sources import dependency_identity
from release_evidence import digest, file_reference, read_json, require
from release_pair import canonical, validate

TARGET = 'x86_64-unknown-linux-gnu'
SERVICES = ('gcnode', 'gcoms-catalog', 'gc-network-operator', 'gcoms-channel-service')
SERVICE_COMMAND = ['cargo', 'build', '--locked', '--release', '-p', 'gcoms-node',
                   '-p', 'gcoms-catalog', '-p', 'gcoms-channel-service', '--features',
                   'gcoms-node/experimental-gc2,gcoms-node/push-gateway,gcoms-catalog/experimental-gc2']
CLI_COMMAND = ['cargo', 'build', '--locked', '--release', '-p', 'gchat-tui', '--features', 'gc2-carrier']
DESKTOP_COMMAND = ['npm', 'run', 'tauri', '-w', '@gchat/client', '--', 'build', '--no-bundle']
RESOURCE_DIRS = ('apps/client/dist', 'third-party/generated')


def compiler_environment(environment):
    return {**{key: environment.get(key, '') for key in
               ('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'CARGO_BUILD_TARGET')},
            **{key: value for key, value in environment.items()
               if key.startswith('CARGO_PROFILE_RELEASE_')}}


def rustc():
    return subprocess.check_output(['rustc', '-vV'], text=True)


def files(root):
    result = {}
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(), 'retained Linux build contains a symlink')
        if path.is_file() and path != root / 'receipt.json':
            result[path.relative_to(root).as_posix()] = digest(path)
    return result


def record(root, manifest, kind, commands, inputs=None, environment=None):
    from release_linux_qualification import context
    environment = os.environ if environment is None else environment
    report = {'schema': 1, 'kind': kind, 'release_id': manifest['release_id'],
              'sources': manifest['sources'], 'provider': context(manifest, environment),
              'target': TARGET, 'rustc': rustc(), 'commands': commands,
              'rustflags': environment.get('RUSTFLAGS', ''), 'files': files(root),
              'compiler_environment': compiler_environment(environment),
              'passed': True}
    if inputs is not None:
        report['dependency_identity'] = dependency_identity(inputs)
    (root / 'receipt.json').write_bytes(canonical(report))
    return report


def verify(root, manifest, kind, environment=None, inputs=None, check_toolchain=True):
    from release_linux_qualification import context
    environment = os.environ if environment is None else environment
    root = Path(root)
    require(kind in ('linux_native_services', 'linux_desktop'), 'unknown retained Linux build kind')
    report = read_json(root / 'receipt.json')
    expected = context(manifest, environment)
    provider = report.get('provider', {})
    require(report.get('schema') == 1 and report.get('kind') == kind and report.get('passed') is True
            and report.get('release_id') == manifest['release_id'] and report.get('sources') == manifest['sources']
            and report.get('target') == TARGET, 'retained Linux build source/target differs')
    require(all(provider.get(key) == expected[key] for key in ('repository', 'run_id', 'workflow_commit'))
            and type(provider.get('run_attempt')) is int
            and 1 <= provider['run_attempt'] <= expected['run_attempt'],
            'retained Linux build belongs to another workflow run')
    require(report.get('rustflags') == environment.get('RUSTFLAGS', ''), 'retained Linux compiler flags differ')
    require(report.get('compiler_environment') == compiler_environment(environment),
            'retained Linux compiler environment differs')
    require(isinstance(report.get('rustc'), str) and f'host: {TARGET}\n' in report['rustc'],
            'retained Linux compiler target differs')
    if check_toolchain:
        require(report['rustc'] == rustc(), 'retained Linux compiler differs')
    commands = [SERVICE_COMMAND] if kind == 'linux_native_services' else [DESKTOP_COMMAND, CLI_COMMAND]
    require(report.get('commands') == commands, 'retained Linux build commands/features differ')
    inventory = report.get('files', {})
    require(inventory and inventory == files(root), 'retained Linux build files changed')
    required = set(SERVICES) if kind == 'linux_native_services' else {'bin/gchat', 'bin/gchat-desktop'}
    require(required <= set(inventory), 'retained Linux executables are missing')
    if kind == 'linux_native_services':
        require(set(inventory) == required, 'retained service inventory differs')
    else:
        require(inputs is not None and report.get('dependency_identity') == dependency_identity(inputs),
                'retained desktop dependencies differ from native qualification')
        allowed = tuple('resources/' + name + '/' for name in RESOURCE_DIRS)
        require(all(name in required or name.startswith(allowed) for name in inventory),
                'unexpected retained desktop resource')
        require(all(any(name.startswith(prefix) for name in inventory) for prefix in allowed),
                'retained desktop resource directory is missing')
    for name, sha in inventory.items():
        file_reference(root, {'path': name, 'sha256': sha})
    return report


def retain_desktop(checkout, inputs, provenance, environment):
    """The existing paired CI has already built this exact release desktop."""
    manifest = validate(read_json(environment['GCHAT_RELEASE_MANIFEST']))
    require(inputs['sources'] == manifest['sources'] and inputs['target'] == TARGET,
            'paired desktop inputs differ from frozen release')
    require(f'host: {TARGET}\n' in rustc(), 'retained desktop requires native Linux Rust')
    target = Path(environment.get('CARGO_TARGET_DIR', checkout / 'target')).resolve()
    desktop = target / 'release/gchat-desktop'
    require(desktop.is_file() and not desktop.is_symlink(), 'CI release desktop is missing')
    desktop_sha = digest(desktop)
    subprocess.run(CLI_COMMAND, cwd=checkout, env=environment, check=True)
    require(digest(desktop) == desktop_sha, 'CLI compilation changed the qualified desktop')
    retained = provenance / 'linux-build'
    (retained / 'bin').mkdir(parents=True, exist_ok=False)
    for name in ('gchat', 'gchat-desktop'):
        shutil.copy2(target / 'release' / name, retained / 'bin' / name)
    for name in RESOURCE_DIRS:
        shutil.copytree(checkout / name, retained / 'resources' / name)
    return record(retained, manifest, 'linux_desktop', [DESKTOP_COMMAND, CLI_COMMAND], inputs, environment)


def stage_desktop(retained, build_root, checkout, manifest, inputs, environment):
    report = verify(retained, manifest, 'linux_desktop', environment, inputs)
    release = build_root / TARGET / 'release'
    release.mkdir(parents=True, exist_ok=False)
    for name in ('gchat', 'gchat-desktop'):
        shutil.copy2(retained / 'bin' / name, release / name)
        (release / name).chmod(0o755)
    for directory in RESOURCE_DIRS:
        destination = checkout / directory
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(retained / 'resources' / directory, destination)
    return report


def verify_fleet(root, manifest, environment=None):
    services = verify(root / 'native-services', manifest, 'linux_native_services', environment)
    fixture = read_json(root / 'relay-build/build.json')
    require(fixture.get('passed') is True and set(fixture.get('sources', {})) == {'gchat', 'gcoms'},
            'retained fixture build did not pass')
    for name, expected in manifest['sources'].items():
        source = fixture['sources'][name]
        require(source.get('unchanged') is True and source.get('revision') == expected['commit']
                and source.get('snapshot_sha256') == hashlib.sha256(
                    json.dumps(source.get('files', {}), sort_keys=True).encode()).hexdigest(),
                'retained fixture source differs')
    require(set(fixture.get('artifacts', {})) == {'gcnode', 'gchat', 'fleet_probe', 'turnover_daemon'},
            'retained fixture executable inventory differs')
    for name, info in fixture['artifacts'].items():
        path = file_reference(root / 'relay-build', {'path': 'bin/' + name, 'sha256': info.get('sha256')})
        require(type(info.get('size')) is int and path.stat().st_size == info['size'] and info['size'] > 0,
                'retained fixture executable size differs')
    supplied = fixture.get('provided_relay', {})
    require(supplied.get('receipt') == services
            and supplied.get('receipt_sha256') == digest(root / 'native-services/receipt.json')
            and fixture['artifacts']['gcnode']['sha256'] == services['files']['gcnode'],
            'load fixture does not use the retained production relay')
    return fixture


def fetch_fleet(workspace, output, manifest, artifact_id, expected_sha, environment):
    from release_jobs import extract, gh
    from release_linux_qualification import checked_sources, context
    checked_sources(workspace, manifest)
    provider = context(manifest, environment)
    require(re.fullmatch('[1-9][0-9]*', artifact_id) is not None
            and re.fullmatch('[0-9a-f]{64}', expected_sha) is not None, 'invalid retained build artifact reference')
    artifact = gh('actions/artifacts/' + artifact_id)
    origin = artifact.get('workflow_run', {})
    require(artifact.get('id') == int(artifact_id) and artifact.get('expired') is False
            and artifact.get('digest') == 'sha256:' + expected_sha
            and origin.get('id') == int(provider['run_id'])
            and origin.get('head_sha') == manifest['sources']['gchat']['commit']
            and type(artifact.get('size_in_bytes')) is int and 0 < artifact['size_in_bytes'] <= 2 * 1024**3,
            'retained build artifact belongs to another source/run or digest')
    archive = output.with_suffix('.zip')
    with archive.open('xb') as stream:
        subprocess.run(['gh', 'api', 'repos/IggyGG/gchat/actions/artifacts/' + artifact_id + '/zip'],
                       stdout=stream, stderr=subprocess.PIPE, check=True, timeout=600)
    require(archive.stat().st_size == artifact['size_in_bytes'] and digest(archive) == expected_sha,
            'retained build archive changed')
    output.mkdir(parents=True, exist_ok=False)
    extract(archive, output)
    verify_fleet(output, manifest, environment)
    # Artifact archives do not preserve executable mode; the bytes were checked above.
    for name in SERVICES:
        (output / 'native-services' / name).chmod(0o755)
    for name in ('gcnode', 'gchat', 'fleet_probe', 'turnover_daemon'):
        (output / 'relay-build/bin' / name).chmod(0o755)
    receipt = read_json(output / 'native-services/receipt.json')
    require(artifact.get('name') == 'linux-native-build-' + str(receipt['provider']['run_attempt']),
            'retained build artifact attempt differs')
    checked_sources(workspace, manifest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-id', required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    fetch_fleet(Path.cwd(), args.output.resolve(), validate(read_json(os.environ['GCHAT_RELEASE_MANIFEST'])),
                args.artifact_id, args.sha256.removeprefix('sha256:'), os.environ)
