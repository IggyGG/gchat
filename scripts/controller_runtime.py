"""Qualify the actual controller image before retaining its release bundle."""
from contextlib import redirect_stdout
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import unittest

from release_pair import canonical


SUITES = (
    'release_minutes_test', 'release_provider_test', 'release_stores_test', 'release_store_worker_test',
    'release_controller_test', 'release_controller_qualification_test',
    'release_discovery_test', 'release_platform_deployment_test',
    'release_config_test', 'release_acceptance_test', 'mobile_acceptance_test',
    'release_coordinator_test', 'release_deployment_test', 'release_control_test',
    'release_relay_load_test',
    'relay_load_run_test',
    'release_rollback_image_test', 'release_infrastructure_bundle_test',
    'release_kubernetes_worker_test', 'release_host_install_test', 'release_host_serve_test',
    'release_rollout_watchdog_test', 'release_inputs_test',
    'release_ios_versions_test', 'release_prepare_test', 'release_compaction_test',
    'controller_runtime_test', 'infrastructure_build_test',
)
MINIMUM_TESTS = 101


def expected_sources(root, source):
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only',
                                     source['commit'], 'scripts', 'release'], cwd=root, text=True)
    tree = subprocess.check_output(['git', 'rev-parse', source['commit'] + '^{tree}'],
                                   cwd=root, text=True).strip()
    if tree != source['tree']:
        raise ValueError('controller qualification source tree changed')
    files = {name: hashlib.sha256(subprocess.check_output(
        ['git', 'show', source['commit'] + ':' + name], cwd=root)).hexdigest()
        for name in names.splitlines()}
    return {'schema': 1, 'source': source, 'files': files}


def check(request, root=Path('/opt/gchat')):
    source = request.get('source', {})
    if (request.get('schema') != 1 or set(source) != {'commit', 'tree'}
            or any(not re.fullmatch(r'[0-9a-f]{40}', str(value)) for value in source.values())
            or os.environ.get('GCHAT_CONTROLLER_REVISION') != source['commit']):
        raise ValueError('controller runtime revision differs from frozen source')
    files = request.get('files')
    if not isinstance(files, dict) or not files:
        raise ValueError('controller runtime source inventory is missing')
    for name, expected in files.items():
        path = PurePosixPath(name)
        if (not path.parts or path.is_absolute() or '..' in path.parts or path.parts[0] not in ('scripts', 'release')
                or not re.fullmatch(r'[0-9a-f]{64}', str(expected))):
            raise ValueError('controller runtime source path or hash is invalid')
        actual = root / name
        if actual.is_symlink() or hashlib.sha256(actual.read_bytes()).hexdigest() != expected:
            raise ValueError('controller runtime source bytes changed: ' + name)
    # stdout is the machine-readable proof channel. Test imports and exercised
    # CLI handlers may print diagnostics; retain those in the qualification log.
    with redirect_stdout(sys.stderr):
        suite = unittest.defaultTestLoader.loadTestsFromNames(SUITES)
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=1).run(suite)
    if not result.wasSuccessful() or result.testsRun < MINIMUM_TESTS or result.skipped:
        raise ValueError('controller runtime tests did not complete successfully')
    # Tests must not silently alter the source they just qualified.
    for name, expected in files.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError('controller runtime source changed during tests: ' + name)
    return {'schema': 1, 'passed': True, 'source': source,
            'inventory_sha256': hashlib.sha256(canonical(files)).hexdigest(),
            'source_files_verified': len(files), 'tests': result.testsRun,
            'suites': list(SUITES), 'source_unchanged': True,
            'production_controller_revision_tested': True}


def qualify(image, root, source, configuration, output):
    request = expected_sources(root, source)
    command = ['docker', 'run', '--rm', '--network', 'none', '--read-only',
               '--cap-drop=ALL', '--security-opt=no-new-privileges',
               '--tmpfs', '/tmp:rw,nosuid,nodev,size=256m',
               '--entrypoint', 'python3', '-e', 'TMPDIR=/tmp',
               '-e', 'PYTHONDONTWRITEBYTECODE=1',
               '-e', 'PYTHONPATH=/opt/gchat/scripts:/opt/gchat/scripts/tests',
               '-i', image, '/opt/gchat/scripts/controller_runtime.py']
    result = subprocess.run(command, input=canonical(request), capture_output=True, timeout=300)
    output = Path(output)
    log = output / 'controller-runtime.log'
    log.write_bytes(result.stderr)
    # A failed image retains its diagnostic log but cannot produce build.json.
    result.check_returncode()
    proof = json.loads(result.stdout)
    proof['configuration_digest'] = configuration
    validate(proof, source, configuration)
    if (proof['inventory_sha256'] != hashlib.sha256(canonical(request['files'])).hexdigest()
            or proof['source_files_verified'] != len(request['files'])):
        raise ValueError('controller image qualified a different source inventory')
    proof['log_sha256'] = hashlib.sha256(log.read_bytes()).hexdigest()
    (output / 'controller-runtime.json').write_text(json.dumps(proof, indent=2) + '\n')
    return proof


def validate(proof, source, configuration):
    if (proof.get('schema') != 1 or proof.get('passed') is not True
            or proof.get('source') != source or proof.get('source_unchanged') is not True
            or proof.get('production_controller_revision_tested') is not True
            or proof.get('suites') != list(SUITES)
            or not isinstance(proof.get('tests'), int) or proof['tests'] < MINIMUM_TESTS
            or not isinstance(proof.get('source_files_verified'), int)
            or proof['source_files_verified'] < len(SUITES)
            or not re.fullmatch(r'[0-9a-f]{64}', str(proof.get('inventory_sha256', '')))
            or proof.get('configuration_digest') != configuration):
        raise ValueError('controller runtime qualification does not bind the retained image')


if __name__ == '__main__':
    print(json.dumps(check(json.load(sys.stdin))), flush=True)
