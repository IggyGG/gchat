#!/usr/bin/env python3
"""Activate an installed package only for an explicitly opted-in, running hub."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import stat
import struct
import subprocess
import time

BINARY = Path('/usr/bin/gchat')
HUB = 'gchat-fleet-host.service'
BACKUP = 'gchat-hub-backup.service'
PACKAGE_LOCK = Path('/run/lock/gchat-package-update.lock')
MAX_FRAME = 64 * 1024


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate host configuration field')
        result[key] = value
    return result


def decode_json(raw):
    try:
        value = json.loads(raw, object_pairs_hook=unique_object)
    except RecursionError as error:
        raise ValueError('host JSON nesting exceeds its limit') from error
    pending = [(value, 0)]
    while pending:
        current, depth = pending.pop()
        if depth > 32:
            raise ValueError('host JSON nesting exceeds its limit')
        if isinstance(current, dict):
            pending.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            pending.extend((item, depth + 1) for item in current)
    return value


def private_json(path, limit=32768):
    path = Path(path)
    for selected, directory in ((path.parent, True), (path, False)):
        info = selected.lstat()
        valid = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
        if not valid or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('host registration must be owner-private')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('host registration exceeds size limit')
    return decode_json(raw)


def local_path(value):
    if isinstance(value, str):
        path = Path(value)
    elif (isinstance(value, dict) and set(value) == {'unix'} and isinstance(value['unix'], list)
          and all(type(n) is int and 0 < n <= 255 for n in value['unix'])):
        path = Path(os.fsdecode(bytes(value['unix'])))
    else:
        raise ValueError('unsupported registered host path')
    if not path.is_absolute() or '..' in path.parts or '\0' in str(path):
        raise ValueError('invalid registered host path')
    return path


def registration_for_pid(pid):
    with (Path('/proc') / str(pid) / 'cmdline').open('rb') as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError('host process arguments exceed bound')
    arguments = [os.fsdecode(arg) for arg in raw.split(b'\0') if arg]
    def selected(flag):
        values = [arguments[i + 1] for i, arg in enumerate(arguments[:-1]) if arg == flag]
        values.extend(arg[len(flag) + 1:] for arg in arguments if arg.startswith(flag + '='))
        if len(values) > 1:
            raise ValueError('ambiguous registered host arguments')
        return values[0] if values else None
    archive, home = selected('--chat-archive'), selected('--home')
    if archive is None and home is None:
        raise ValueError('managed activation requires an explicitly selected registered instance')
    path = local_path(archive) if archive is not None else local_path(home) / 'chat.gcarchive'
    registration = private_json(path.with_suffix('.host.json'))
    if (not isinstance(registration, dict) or type(registration.get('version')) is not int
            or registration['version'] != 1 or registration.get('service') != HUB):
        raise ValueError('host registration does not select this managed service')
    if local_path(registration.get('archive')) != path:
        raise ValueError('registered archive does not match the running process')
    return registration


class Maintenance:
    """The existing owner-only update lease, pinned to the observed process."""
    def __init__(self, before, release, view=None):
        registration = registration_for_pid(before['pid'])
        self.before, self.release_id = before, release
        self.view = view or secrets.token_hex(16)
        self.instance = registration.get('instance')
        if not isinstance(self.instance, str) or len(self.instance) != 64 or any(c not in '0123456789abcdef' for c in self.instance):
            raise ValueError('invalid registered instance identity')
        self.endpoint = local_path(registration.get('protocolSocket')).with_suffix('.chat')
        # Rust's registration writer defines this canonical field order. A
        # modified/reordered recipe must not silently change activation authority.
        encoded = json.dumps(registration, ensure_ascii=False, separators=(',', ':')).encode()
        self.binding = 'gchat.host.v1:' + hashlib.sha256(encoded).hexdigest()

    def record(self):
        return {'view': self.view, 'instance': self.instance, 'endpoint': str(self.endpoint)}

    def exchange(self, request):
        body = json.dumps({'version': 3, 'instance_id': self.instance, 'request': request}, separators=(',', ':')).encode()
        if not 0 < len(body) <= MAX_FRAME:
            raise ValueError('maintenance request exceeds frame bound')
        with socket.socket(socket.AF_UNIX) as connection:
            deadline = time.monotonic() + 30
            connection.settimeout(30)
            connection.connect(str(self.endpoint))
            pid, uid, _ = struct.unpack('3i', connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize('3i')))
            if pid != self.before['pid'] or uid != os.getuid():
                raise ValueError('maintenance endpoint changed process owner')
            connection.sendall(struct.pack('!I', len(body)) + body)
            def exact(size):
                data = bytearray()
                while len(data) < size:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise ValueError('maintenance response timed out')
                    connection.settimeout(remaining)
                    part = connection.recv(size - len(data))
                    if not part:
                        raise ValueError('maintenance response was interrupted')
                    data.extend(part)
                return data
            size = struct.unpack('!I', exact(4))[0]
            if not 0 < size <= MAX_FRAME:
                raise ValueError('maintenance response exceeds frame bound')
            value = decode_json(exact(size))
        if (not isinstance(value, dict) or type(value.get('version')) is not int
                or value['version'] != 3 or value.get('instance_id') != self.instance):
            raise ValueError('maintenance response changed instance or API')
        response = value.get('response')
        if not isinstance(response, dict) or response.get('kind') == 'error':
            raise ValueError('registered host refused maintenance')
        return response

    def update(self, action):
        request = {'action': action, 'view': self.view}
        if action in ('prepare', 'abort'):
            request['release'] = self.release_id
        response = self.exchange({'kind': 'update', 'request': request})
        if response.get('kind') != 'update' or not isinstance(response.get('result'), dict):
            raise ValueError('invalid host maintenance result')
        return response['result']

    def prepare(self):
        identity = self.exchange({'kind': 'identify'})
        info = identity.get('instance')
        capabilities = info.get('capabilities') if isinstance(info, dict) else None
        if (identity.get('kind') != 'instance' or not isinstance(capabilities, list)
                or not all(isinstance(value, str) for value in capabilities) or self.binding not in capabilities):
            raise ValueError('running host does not match its registered configuration')
        attached = self.update('heartbeat')
        if attached.get('state') == 'busy':
            return attached
        if attached.get('state') != 'attached':
            raise ValueError('host refused the maintenance view')
        result = self.update('prepare')
        if result.get('state') not in ('ready', 'busy'):
            raise ValueError('host returned an invalid readiness result')
        if result['state'] == 'ready' and result.get('process_id') != self.before['pid']:
            raise ValueError('maintenance readiness changed process identity')
        return result

    def release(self):
        self.update('abort')
        self.update('detach')


def release_abandoned(before, package, receipt):
    """Release only this old attempt's lease; never repeat an uncertain restart."""
    previous = receipt.get('maintenance')
    if not isinstance(previous, dict) or receipt.get('before') != before:
        return
    lease = Maintenance(before, package['sha256'], previous.get('view'))
    if lease.record() != previous:
        raise ValueError('retained maintenance owner changed')
    lease.release()


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def capture(argv):
    return subprocess.check_output(argv, text=True, stderr=subprocess.PIPE, timeout=15).strip()


def installed():
    value = capture(['dpkg-query', '-W', '-f=${Status}\n${Version}', 'g-chat']).splitlines()
    if len(value) != 2 or value[0] != 'install ok installed':
        raise ValueError('GChat package is not fully installed and configured')
    if capture(['dpkg-query', '-S', str(BINARY)]) not in (
            'g-chat: ' + str(BINARY), 'g-chat:amd64: ' + str(BINARY), 'g-chat:arm64: ' + str(BINARY)):
        raise ValueError('managed executable is not owned by the GChat package')
    info = BINARY.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
        raise ValueError('managed package executable is not a protected root-owned file')
    return {'version': value[1], 'sha256': digest(BINARY), 'path': str(BINARY.resolve())}


def process():
    result = subprocess.run(['systemctl', '--user', 'show', HUB, '--no-pager',
                             '-p', 'LoadState', '-p', 'ActiveState', '-p', 'MainPID'],
                            capture_output=True, text=True, timeout=15)
    fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    if fields.get('LoadState') == 'not-found' or fields.get('ActiveState') == 'inactive':
        return None
    if result.returncode:
        raise ValueError('cannot inspect the managed user hub')
    if fields.get('LoadState') != 'loaded' or fields.get('ActiveState') != 'active':
        return None
    pid = int(fields.get('MainPID', '0'))
    if pid <= 0: return None
    executable = Path('/proc') / str(pid) / 'exe'
    return {'pid': pid, 'path': os.readlink(executable).removesuffix(' (deleted)'),
            'sha256': digest(executable)}


def save(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, sort_keys=True); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(directory)
    finally: os.close(directory)


def action(verb, unit, timeout):
    subprocess.run(['systemctl', '--user', verb, unit], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=timeout)


def wait_running(package, old_pid):
    deadline = time.monotonic() + 30
    previous = None
    while time.monotonic() < deadline:
        try:
            current = process()
        except (FileNotFoundError, PermissionError):
            # During startup /proc may disappear or temporarily be unreadable.
            # Neither is a verified observation: reset the stable pair below
            # and keep the same deadline, PID/path/hash checks and restart intent.
            current = None
        if (current and current['pid'] != old_pid and current['path'] == package['path']
                and current['sha256'] == package['sha256']):
            if current == previous:
                return current
            previous = current
        else:
            previous = None
        time.sleep(1)
    raise ValueError('new hub did not remain active on the installed executable')


def activate(state, package_lock=PACKAGE_LOCK):
    import fcntl  # This systemd user helper runs only on Linux.
    state = Path(state); state.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (state / 'activation.lock').open('a+b') as own:
        try: fcntl.flock(own, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return {'state': 'deferred', 'reason': 'activation already running'}
        try: package_guard = Path(package_lock).open('rb')
        except (FileNotFoundError, PermissionError):
            return {'state': 'deferred', 'reason': 'package updater lock is not available read-only'}
        with package_guard:
            try: fcntl.flock(package_guard, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError: return {'state': 'deferred', 'reason': 'package update is running'}
            before = process()
            if before is None: return {'state': 'skipped', 'reason': 'managed hub is not running'}
            package = installed()
            if before['path'] != package['path']:
                return {'state': 'blocked', 'reason': 'running hub uses another executable; no restart'}
            if before['sha256'] == package['sha256']:
                return {'state': 'current', 'reason': 'running hub already uses installed bytes', **package}
            marker = state / (package['sha256'] + '.json')
            if marker.exists():
                old = json.loads(marker.read_text())
                try: release_abandoned(before, package, old)
                except (ValueError, OSError): pass
                if old.get('state') != 'deferred' or 'restart_requested_at' in old:
                    return {'state': 'suppressed', 'reason': 'this executable already had an activation attempt; inspect its receipt before a manual reset',
                            'sha256': package['sha256'], 'previous_state': old.get('state')}
            lease = Maintenance(before, package['sha256'])
            receipt = {'schema': 1, 'state': 'intent', 'package': package, 'before': before,
                       'maintenance': lease.record(), 'started_at': int(time.time())}
            save(marker, receipt)  # An interrupted/unknown outcome never authorizes another restart.
            try:
                action('start', BACKUP, 180)
                if installed() != package:
                    raise ValueError('installed package changed during backup')
                if process() != before:
                    raise ValueError('running hub changed during backup')
                ready = lease.prepare()
                if ready['state'] == 'busy':
                    receipt.update(state='deferred', reason=ready.get('reason', 'host is busy'))
                else:
                    # The short lease begins after backup and immediately guards
                    # the ordinary graceful restart. No request is replayed.
                    receipt['restart_requested_at'] = int(time.time())
                    save(marker, receipt)
                    action('try-restart', HUB, 90)
                    after = wait_running(package, before['pid'])
                    if installed() != package:
                        raise ValueError('installed package changed during activation')
                    receipt.update(state='activated', after=after, completed_at=int(time.time()),
                                   network_delivery_verified=False)
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                receipt.update(state='failed', completed_at=int(time.time()),
                                reason=str(error) if isinstance(error, ValueError) else type(error).__name__)
            finally:
                try: lease.release()
                except (ValueError, OSError): pass  # Restart may already have retired the pinned process.
            save(marker, receipt)
            return receipt


def main():
    state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'gchat-headless-activation'
    try: result = activate(state)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        result = {'state': 'deferred', 'reason': str(error) if isinstance(error, ValueError) else type(error).__name__}
    print(json.dumps(result, sort_keys=True))
    return 1 if result['state'] in ('failed', 'blocked') else 0


if __name__ == '__main__': raise SystemExit(main())
