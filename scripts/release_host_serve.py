#!/usr/bin/env python3
"""Restricted SSH entrypoint for the operator's installed service inventory."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from release_host_install import run

LIMIT = 256 * 1024 * 1024


def upload(sha, source, directory):
    if not re.fullmatch('[0-9a-f]{64}', sha): raise ValueError('invalid upload digest')
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=directory, delete=False) as stream:
        path = Path(stream.name)
        try:
            digest = hashlib.sha256(); total = 0
            while data := source.read(1024 * 1024):
                total += len(data)
                if total > LIMIT: raise ValueError('upload exceeds service binary limit')
                digest.update(data); stream.write(data)
            stream.flush(); os.fsync(stream.fileno()); stream.close()
            if not total or digest.hexdigest() != sha: raise ValueError('upload digest mismatch')
            path.chmod(0o600)
            os.replace(path, directory / ('gchat-release-' + sha))
        finally:
            path.unlink(missing_ok=True)


def request(value, policy):
    if value.get('stage') not in ('observe', 'prepare', 'activate', 'rollback'):
        raise ValueError('unsupported service stage')
    unit = value.get('unit')
    installed = policy['units'].get(unit)
    if installed is None or value.get('binary_name') != installed['binary_name']:
        raise ValueError('service is outside the installed inventory')
    # Protected paths and installer options come only from the root-owned host
    # policy. The SSH key cannot select another unit, path or executable name.
    return {**installed, **{key: value[key] for key in
        ('unit', 'stage', 'sha256', 'release_id')}}


def main():
    os.umask(0o077)
    command = os.environ.get('SSH_ORIGINAL_COMMAND', '')
    parts = command.split(' ')
    directory = Path('/var/lib/gchat-release/uploads')
    if len(parts) == 2 and parts[0] == 'upload':
        upload(parts[1], sys.stdin.buffer, directory)
        return
    if len(parts) == 3 and parts[0] == 'canary' and parts[1] in ('grant', 'revoke'):
        from release_canary_grant import operate
        policy = json.loads(Path('/etc/gchat-release-worker.json').read_text())
        # Invitations are returned only over the private, restricted SSH pipe.
        print(json.dumps(operate(policy, parts[1], parts[2])))
        return
    if command != 'install': raise ValueError('unsupported service command')
    raw = sys.stdin.buffer.read(65537)
    if len(raw) > 65536: raise ValueError('service request exceeds limit')
    policy = json.loads(Path('/etc/gchat-release-worker.json').read_text())
    result = run(request(json.loads(raw), policy), upload_root=directory)
    print(json.dumps(result))


if __name__ == '__main__': main()
