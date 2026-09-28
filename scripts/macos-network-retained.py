#!/usr/bin/env python3
"""Diagnose a registered immutable Mac installer without rebuilding or publishing."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

from release_coordinator import atomic_json
from release_jobs import extract, gh

SOURCE = '80fc0dc4dea4bd6d40a0f1e58ed76eafa7b6e547'
GCOMS = '8cdfd3fee2ab7809f1c348dc3a60ef24393b4101'
ARTIFACTS = {
    'macos-aarch64': (36478808391, 11000164890,
        'fb52b752c444ef4aaa83e78697bc757610b9d637b8cc8625c3f0beab72c1f5ca'),
    'macos-x86_64': (36478817333, 11003725122,
        '696b6630ed31ab5b9c77683f4a85635e1978c259c63c5958ec65d372217834bf'),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def validate(target, run, artifact):
    run_id, artifact_id, digest = ARTIFACTS[target]
    require(run.get('id') == run_id and run.get('head_sha') == SOURCE
            and run.get('head_repository', {}).get('full_name') == 'IggyGG/gchat'
            and run.get('path') == '.github/workflows/macos-release.yml'
            and run.get('event') == 'workflow_dispatch' and run.get('status') == 'completed'
            and run.get('conclusion') == 'failure', 'original failed run identity differs')
    require(artifact.get('id') == artifact_id and artifact.get('name') == target
            and artifact.get('workflow_run', {}).get('id') == run_id
            and artifact.get('expired') is False and artifact.get('digest') == 'sha256:' + digest
            and type(artifact.get('size_in_bytes')) is int
            and 0 < artifact['size_in_bytes'] <= 512 * 1024**2,
            'registered native artifact differs')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', required=True, choices=ARTIFACTS)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(platform.system() == 'Darwin' and os.environ.get('GITHUB_ACTIONS') == 'true',
            'isolated native Mac worker required')
    require(platform.machine() == {'macos-aarch64': 'arm64', 'macos-x86_64': 'x86_64'}[args.target],
            'native architecture differs')
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    run_id, artifact_id, expected = ARTIFACTS[args.target]
    run = gh(f'actions/runs/{run_id}'); artifact = gh(f'actions/artifacts/{artifact_id}')
    validate(args.target, run, artifact)
    atomic_json(out / 'original-run.json', run)
    atomic_json(out / 'original-artifact.json', artifact)
    archive = out / 'original.zip'
    with archive.open('xb') as stream:
        subprocess.run(['gh', 'api', f'repos/IggyGG/gchat/actions/artifacts/{artifact_id}/zip'],
                       stdout=stream, stderr=subprocess.PIPE, check=True, timeout=300)
    require(archive.stat().st_size == artifact['size_in_bytes'] and digest(archive) == expected,
            'archive hash or size differs')
    original = out / 'original'; extract(archive, original)
    build = json.loads((original / 'build.json').read_text())
    require(build.get('sources') == {'gchat': SOURCE, 'gcoms': GCOMS}
            and build.get('target') == args.target, 'original application source differs')
    failed = original / 'application-smoke/network/report.json'
    require(json.loads(failed.read_text()).get('passed') is False,
            'original network failure is missing')
    scripts = Path(__file__).resolve().parent
    command = [sys.executable, str(scripts / 'test-macos-bundle.py'),
               '--build-manifest', str(original / 'build.json'),
               '--native-receipt', str(original / 'provenance/native-ci.json'),
               '--output', str(out / 'diagnostic'), '--temp-parent', '/private/tmp',
               '--timeout', '30', '--network-invitation-env']
    with (out / 'diagnostic.log').open('xb') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                env={**os.environ, 'GCHAT_NETWORK_DIAGNOSTICS': '1'}, timeout=1100)
    atomic_json(out / 'summary.json', {
        'scope': 'retained installer diagnostic; not publication approval',
        'passed': result.returncode == 0, 'application_rebuilt': False,
        'target': args.target, 'sources': build['sources'], 'original_run': run_id,
        'original_workflow_conclusion': 'failure', 'archive_sha256': expected,
        'original_failure_sha256': digest(failed), 'exit_code': result.returncode,
        'helper_sha256': digest(Path(__file__)),
        'network_harness_sha256': digest(scripts / 'test-native-network.py')})
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
