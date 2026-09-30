"""Source-bound adapter for native relay/bootstrap/channel systemd services."""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

from release_coordinator import atomic_json
from release_pair import validate


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def artifact(target, manifest):
    # Each source commit has an immutable, CI-qualified infrastructure bundle.
    directory = Path(target['artifact_root']) / manifest['sources']['gcoms']['commit']
    proof = json.loads((directory / 'build.json').read_text())
    if (proof.get('gcoms_source') != manifest['sources']['gcoms'] or proof.get('qualified') is not True):
        raise ValueError('infrastructure artifact has no exact qualified source binding')
    name = target['binary_name']
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', name):
        raise ValueError('invalid infrastructure binary')
    path = directory / name
    if digest(path) != proof['sha256'][name]:
        raise ValueError('infrastructure artifact changed')
    return path, proof['sha256'][name]


def ssh(host, code, payload, timeout=120):
    if not re.fullmatch(r'[a-zA-Z0-9_.@-]+', host) or host.startswith('-'):
        raise ValueError('invalid operator SSH destination')
    return subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                           '-o', 'ConnectTimeout=10', host, shlex.join(['python3', '-c', code])],
                          input=payload, capture_output=True, check=True, timeout=timeout).stdout


def main():
    manifest = validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()))
    target = json.loads(Path(os.environ['GCHAT_DEPLOYMENT_TARGET']).read_text())
    stage = os.environ['GCHAT_DEPLOYMENT_STAGE']
    output = Path(os.environ['GCHAT_DEPLOYMENT_RECEIPT'])
    binary, sha = artifact(target, manifest)
    host = target['host']
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
                or value.get('authenticated_delivery') is not True):
            raise ValueError('network canary does not bind this deployment')
    else:
        if stage == 'prepare':
            # The remote path is content-addressed and written atomically. Never
            # execute or overwrite it until the complete upload verifies.
            upload = '''import hashlib,os,sys,tempfile
from pathlib import Path
sha=sys.argv[1]; path=Path('/var/tmp')/('gchat-release-'+sha)
with tempfile.NamedTemporaryFile(dir='/var/tmp',delete=False) as f:
 try:
  h=hashlib.sha256()
  while data:=sys.stdin.buffer.read(1024*1024): f.write(data); h.update(data)
  f.flush();os.fsync(f.fileno());f.close()
  if h.hexdigest()!=sha: raise ValueError('upload digest mismatch')
  os.chmod(f.name,0o600);os.replace(f.name,path)
 finally: Path(f.name).unlink(missing_ok=True)
'''
            # Bound memory; binaries have already been hashed and are operator-built.
            if binary.stat().st_size > 256 * 1024 * 1024:
                raise ValueError('infrastructure binary exceeds transfer limit')
            ssh(host, 'import sys\nsys.argv=["upload",' + repr(sha) + ']\n' + upload,
                binary.read_bytes(), timeout=180)
        request = {**target, 'stage': stage, 'release_id': manifest['release_id'], 'sha256': sha}
        code = Path(__file__).with_name('release_host_install.py').read_text()
        value = json.loads(ssh(host, code, json.dumps(request).encode(), timeout=180))
    evidence = output.with_suffix('.observation.json')
    atomic_json(evidence, value)
    atomic_json(output, {**value, 'schema': 1, 'release_id': manifest['release_id'],
                        'sources': manifest['sources'], 'target': target['id'], 'stage': stage,
                        'observed_at': int(time.time()),
                        'evidence': [{'path': evidence.name, 'sha256': digest(evidence)}]})


if __name__ == '__main__': main()
