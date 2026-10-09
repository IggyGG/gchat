#!/usr/bin/env python3
"""Activate an installed package only for an explicitly opted-in, running hub."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time

BINARY = Path('/usr/bin/gchat')
HUB = 'gchat-fleet-host.service'
BACKUP = 'gchat-hub-backup.service'
PACKAGE_LOCK = Path('/run/lock/gchat-package-update.lock')


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
        except FileNotFoundError:  # A starting process may exit between show and /proc.
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
                return {'state': 'suppressed', 'reason': 'this executable already had an activation attempt; inspect its receipt before a manual reset',
                        'sha256': package['sha256'], 'previous_state': old.get('state')}
            receipt = {'schema': 1, 'state': 'intent', 'package': package, 'before': before,
                       'started_at': int(time.time())}
            save(marker, receipt)  # An interrupted/unknown outcome never authorizes another restart.
            try:
                action('start', BACKUP, 180)
                if installed() != package:
                    raise ValueError('installed package changed during backup')
                if process() != before:
                    raise ValueError('running hub changed during backup')
                action('try-restart', HUB, 90)
                after = wait_running(package, before['pid'])
                if installed() != package:
                    raise ValueError('installed package changed during activation')
                receipt.update(state='activated', after=after, completed_at=int(time.time()),
                               network_delivery_verified=False)
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                receipt.update(state='failed', completed_at=int(time.time()),
                               reason=str(error) if isinstance(error, ValueError) else type(error).__name__)
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
