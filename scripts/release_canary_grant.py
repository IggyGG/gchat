"""Host-owned, expiring bootstrap/invitation authority for rollout canaries."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

from release_host_install import write


def prepare_operator(policy_path, sha, *, upload_root=Path('/var/lib/gchat-release/uploads'),
                     binary_root=Path('/usr/local/lib/gchat-release/operators'),
                     backup_root=Path('/var/lib/gchat-release/operator-backups')):
    """Install the source-qualified companion operator before catalog activation."""
    if not re.fullmatch('[0-9a-f]{64}', sha):
        raise ValueError('invalid operator digest')
    policy_path = Path(policy_path)
    raw = policy_path.read_bytes()
    policy = json.loads(raw)
    configured = policy.get('canary')
    if not configured or not {'operator', 'network_id', 'provider_urls'} <= configured.keys():
        raise ValueError('operator preparation requires the enabled host canary policy')
    source = upload_root / ('gchat-release-' + sha)
    if source.is_symlink() or not source.is_file() or not 0 < source.stat().st_size <= 16 * 1024 * 1024:
        raise ValueError('operator upload is missing or unsafe')
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha:
        raise ValueError('operator upload changed')
    directory = binary_root / sha
    for path in (binary_root, directory):
        if path.is_symlink():
            raise ValueError('operator directory cannot be a symlink')
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(0o755)
    binary = directory / 'gc-network-operator'
    if binary.is_symlink():
        raise ValueError('operator binary cannot be a symlink')
    if binary.exists():
        if binary.read_bytes() != data:
            raise ValueError('retained operator binary changed')
    else:
        temporary = binary.with_suffix('.new')
        temporary.write_bytes(data)
        temporary.chmod(0o755)
        os.replace(temporary, binary)
    with tempfile.TemporaryDirectory(prefix='operator-check-', dir=directory) as temporary:
        root = Path(temporary)
        store, request, code = root / 'grants', root / 'request', root / 'invitation'
        write(store, {'version': 1, 'grants': []})
        write(request, {'network_id': configured['network_id'], 'provider_urls': configured['provider_urls'],
                       'expires_at': int(time.time()) + 600, 'scopes': ['bootstrap', 'invitations'], 'max_names': 0})
        subprocess.run([str(binary), 'grant', str(store), str(request), str(code)],
                       check=True, capture_output=True, timeout=30)
        _, _, ident = invitation(code)
        subprocess.run([str(binary), 'revoke', str(store), ident],
                       check=True, capture_output=True, timeout=30)
        grants = json.loads(store.read_text())['grants']
        if len(grants) != 1 or grants[0].get('revoked') is not True:
            raise ValueError('operator did not revoke its diagnostic grant')
    if configured['operator'] != str(binary):
        backup_root.mkdir(parents=True, exist_ok=True)
        backup = backup_root / ('policy-' + str(time.time_ns()) + '.json')
        backup.write_bytes(raw)
        backup.chmod(0o600)
        configured['operator'] = str(binary)
        ownership = policy_path.stat()
        if policy_path.read_bytes() != raw:
            raise ValueError('host policy changed during operator preparation')
        write(policy_path, policy)
        os.chown(policy_path, ownership.st_uid, ownership.st_gid)
        policy_path.chmod(ownership.st_mode & 0o777)
    return {'passed': True, 'sha256': sha, 'scope_checked': True, 'diagnostic_grant_revoked': True}


def invitation(path):
    raw = path.read_text().strip()
    if len(raw) > 180000 or not raw.startswith('GCNI1-'):
        raise ValueError('invalid retained canary invitation')
    encoded = raw[6:]
    value = json.loads(base64.urlsafe_b64decode(encoded + '=' * (-len(encoded) % 4)))
    token = value['grant']
    secret = base64.urlsafe_b64decode(token + '=' * (-len(token) % 4))
    if len(secret) != 32 or base64.urlsafe_b64encode(secret).decode().rstrip('=') != token:
        raise ValueError('invalid canary grant')
    ident = base64.urlsafe_b64encode(hashlib.sha256(b'gc/network/grant/v1\0' + secret).digest()).decode().rstrip('=')
    return raw, value, ident


def operate(policy, action, ident, *, state_root=Path('/var/lib/gchat-release/canaries'), now=None):
    if action not in ('grant', 'revoke') or not re.fullmatch('[0-9a-f]{64}', ident):
        raise ValueError('invalid canary operation')
    configured = policy.get('canary')
    if not configured:
        raise ValueError('canary invitations are not enabled on this host')
    if not {'operator', 'grants_file', 'network_id', 'provider_urls'} <= configured.keys():
        raise ValueError('canary host policy is incomplete')
    ttl = configured.get('ttl_seconds', 3600)
    if action == 'grant' and (type(ttl) is not int or not 600 <= ttl <= 3600):
        raise ValueError('canary duration must be between 600 and 3600 seconds')
    import fcntl  # The grant operator preserves a Linux service store's owner/mode.
    now = int(time.time()) if now is None else now
    work = state_root / ident
    work.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (work / 'owner.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        intent = work / 'request.json'
        code = work / 'invitation'
        store = Path(configured['grants_file'])
        if not intent.exists():
            if action == 'revoke': return {'revoked': True, 'created': False}
            # Every authority and duration comes from the root-owned policy.
            write(intent, {'network_id': configured['network_id'],
                'provider_urls': configured['provider_urls'], 'expires_at': now + ttl,
                'scopes': ['bootstrap', 'invitations'], 'max_names': 0})
        expected = json.loads(intent.read_text())
        if (expected['network_id'] != configured['network_id']
                or expected['provider_urls'] != configured['provider_urls']
                or expected['scopes'] not in (['bootstrap'], ['bootstrap', 'invitations'])
                or expected['max_names'] != 0):
            raise ValueError('retained canary authority differs from host policy')
        if action == 'grant' and expected['scopes'] != ['bootstrap', 'invitations']:
            raise ValueError('legacy bootstrap-only canary authority can only be revoked')

        def operator(arguments):
            ownership = store.stat()
            try:
                subprocess.run([configured['operator'], *arguments], check=True,
                               capture_output=True, timeout=30)
            finally:
                # The operator atomically replaces this existing service file.
                os.chown(store, ownership.st_uid, ownership.st_gid)
                store.chmod(ownership.st_mode & 0o777)

        if not code.exists():
            if action == 'revoke': return {'revoked': True, 'created': False}
            if expected['expires_at'] <= now:
                raise ValueError('canary grant intent expired; do not renew the same operation')
            operator(['grant', str(store), str(intent), str(code)])
        raw, value, grant_id = invitation(code)
        if any(value.get(key) != expected[key] for key in ('network_id', 'provider_urls', 'expires_at')) or value.get('version') != 1:
            raise ValueError('retained invitation differs from its grant intent')
        grants = json.loads(store.read_text())['grants']
        matches = [g for g in grants if g['id'] == grant_id]
        if len(matches) != 1 or any(matches[0].get(k) != expected[k] for k in ('expires_at', 'scopes', 'max_names')):
            raise ValueError('retained invitation has no exact committed canary grant')
        if action == 'grant':
            if matches[0]['revoked'] or value['expires_at'] <= now:
                raise ValueError('canary grant is revoked or expired')
            return {'invitation': raw, 'expires_at': value['expires_at']}
        if not matches[0]['revoked']:
            operator(['revoke', str(store), grant_id])
        actual = [g for g in json.loads(store.read_text())['grants'] if g['id'] == grant_id]
        if len(actual) != 1 or actual[0]['revoked'] is not True:
            raise ValueError('canary grant revocation did not persist')
        result = {'revoked': True, 'created': True}
        write(work / 'revoked.json', result)
        return result
