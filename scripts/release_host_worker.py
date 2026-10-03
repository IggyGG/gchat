"""Source-bound adapter for native relay/bootstrap/channel systemd services."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from release_coordinator import atomic_json
from release_pair import validate


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def artifact(target, manifest):
    # The bundle binds both sources; controller-only updates cannot reuse an
    # older controller merely because its protocol companion is unchanged.
    directory = Path(target['artifact_root']) / manifest['release_id']
    proof = json.loads((directory / 'build.json').read_text())
    if (proof.get('sources') != manifest['sources'] or proof.get('qualified') is not True):
        raise ValueError('infrastructure artifact has no exact qualified source binding')
    name = target['binary_name']
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', name):
        raise ValueError('invalid infrastructure binary')
    path = directory / name
    if digest(path) != proof['sha256'][name]:
        raise ValueError('infrastructure artifact changed')
    return path, proof['sha256'][name]


def ssh(target, command, payload, timeout=120):
    host = target['host']
    if not re.fullmatch(r'[a-zA-Z0-9_.@-]+', host) or host.startswith('-'):
        raise ValueError('invalid operator SSH destination')
    if command != 'install' and not re.fullmatch(r'(?:upload|canary (?:grant|revoke|operator)) [0-9a-f]{64}', command):
        raise ValueError('unsupported restricted service command')
    return subprocess.run(['ssh', '-F', target['ssh_config'],
                           '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                           '-o', 'ConnectTimeout=10', host, command],
                          input=payload, capture_output=True, check=True, timeout=timeout).stdout


def main():
    manifest = validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()))
    target = json.loads(Path(os.environ['GCHAT_DEPLOYMENT_TARGET']).read_text())
    stage = os.environ['GCHAT_DEPLOYMENT_STAGE']
    output = Path(os.environ['GCHAT_DEPLOYMENT_RECEIPT'])
    binary, sha = artifact(target, manifest)
    if stage == 'check':
        # The operator recipe must run the actual network journey. A service
        # process or TCP listener alone never qualifies relay compatibility.
        argv = target['canary']
        if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
            raise ValueError('network canary must be an operator-owned argv')
        proof_path = output.with_suffix('.canary.json')
        result = subprocess.run(argv, env=dict(os.environ, GCHAT_CANARY_RECEIPT=str(proof_path)),
                                timeout=target.get('canary_timeout', 900), check=False)
        if result.returncode == 75: raise SystemExit(75)
        if result.returncode: raise ValueError('real network canary failed')
        value = json.loads(proof_path.read_text())
        if (value.get('release_id') != manifest['release_id'] or value.get('sources') != manifest['sources']
                or value.get('target') != target['id'] or value.get('passed') is not True
                or value.get('authenticated_delivery') is not True
                or value.get('network_check', 'full') != target.get('network_check', 'full')):
            raise ValueError('network canary does not bind this deployment')
    else:
        if stage == 'prepare':
            if target.get('canary_operator') is True:
                operator, operator_sha = artifact({**target, 'binary_name': 'gc-network-operator'}, manifest)
                if operator.stat().st_size > 16 * 1024 * 1024:
                    raise ValueError('grant operator exceeds its binary budget')
                ssh(target, 'upload ' + operator_sha, operator.read_bytes(), timeout=60)
                prepared = json.loads(ssh(target, 'canary operator ' + operator_sha, b''))
                if prepared.get('passed') is not True or prepared.get('sha256') != operator_sha:
                    raise ValueError('grant operator preparation did not bind the qualified binary')
            # The remote path is content-addressed and written atomically. Never
            # execute or overwrite it until the complete upload verifies.
            # Bound memory; binaries have already been hashed and are operator-built.
            if binary.stat().st_size > 256 * 1024 * 1024:
                raise ValueError('infrastructure binary exceeds transfer limit')
            ssh(target, 'upload ' + sha, binary.read_bytes(), timeout=180)
        request = {**target, 'stage': stage, 'release_id': manifest['release_id'], 'sha256': sha}
        value = json.loads(ssh(target, 'install', json.dumps(request).encode(), timeout=180))
    evidence = output.with_suffix('.observation.json')
    atomic_json(evidence, value)
    atomic_json(output, {**value, 'schema': 1, 'release_id': manifest['release_id'],
                        'sources': manifest['sources'], 'target': target['id'], 'stage': stage,
                        'observed_at': int(time.time()),
                        'evidence': [{'path': evidence.name, 'sha256': digest(evidence)}]})


if __name__ == '__main__': main()
