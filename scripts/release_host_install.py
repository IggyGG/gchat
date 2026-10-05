"""Host-side systemd artifact installer; receives private operator JSON on stdin.

The caller supplies a verified immutable artifact. This program preserves the
service arguments, unit, other drop-ins, resource budgets and identity files.
Its journal is written before changing the owned drop-in and survives SSH loss.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.new')
    with temporary.open('w') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def show(unit, field):
    return subprocess.check_output(['systemctl', 'show', unit, '-p', field, '--value'], text=True).strip()


def observe(unit):
    pid = show(unit, 'MainPID')
    active = show(unit, 'ActiveState') == 'active' and pid != '0'
    exe = Path('/proc') / pid / 'exe'
    return {'healthy': active and exe.exists(), 'running': {
        'process_id': int(pid), 'sha256': digest(exe) if exe.exists() else None,
        'executable': str(exe.resolve()) if exe.exists() else None}}


def arguments(unit):
    pid = show(unit, 'MainPID')
    args = (Path('/proc') / pid / 'cmdline').read_bytes().decode().rstrip('\0').split('\0')
    if not args or any(any(c in a for c in '\n\r%$') for a in args):
        raise ValueError('service arguments cannot be represented safely in systemd')
    return args


def identity_hashes(args, additional):
    paths = list(additional)
    for flag in ('--keystore', '--tls-identity', '--pass-file'):
        if flag in args:
            paths.append(args[args.index(flag) + 1])
    return {name: digest(name) for name in paths}


def unchanged(before, unit):
    if any(digest(p) != sha for p, sha in before['protected'].items()):
        raise ValueError('protected service identity or configuration changed')
    if any(show(unit, name) != value for name, value in before['budgets'].items()):
        raise ValueError('service resource budget changed')


def run(request, *, state_root=Path("/var/lib/gchat-release"),
        binary_root=Path("/opt/gchat-release"), unit_root=Path("/etc/systemd/system"),
        upload_root=Path("/var/tmp")):
    import fcntl  # Native systemd worker; importing helpers remains portable.
    unit, release, sha = request['unit'], request['release_id'], request['sha256']
    if not re.fullmatch(r'[a-zA-Z0-9@_.-]+\.service', unit):
        raise ValueError('invalid service unit')
    if any(not re.fullmatch('[0-9a-f]{64}', value) for value in (release, sha)):
        raise ValueError('invalid release or artifact digest')
    stage = request['stage']
    if stage == 'observe':
        value = observe(unit)
        value['matches'] = value['running']['sha256'] == sha
        return value
    root = state_root / unit
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (root / 'install.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        work = root / release
        work.mkdir(mode=0o700, exist_ok=True)
        journal = work / 'before.json'
        drop = unit_root / (unit + '.d') / '99z-gchat-release.conf'
        dest = binary_root / sha / request['binary_name']
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', request['binary_name']):
            raise ValueError('invalid binary name')
        if stage == 'prepare':
            source = upload_root / ('gchat-release-' + sha)
            if digest(source) != sha:
                raise ValueError('uploaded artifact differs from its source receipt')
            # The SSH worker keeps a private umask, while systemd runs these
            # public executables as its existing unprivileged service user.
            # Repair earlier private directories as well as fresh installs.
            for directory in (binary_root, dest.parent):
                if directory.is_symlink():
                    raise ValueError('installed binary directory cannot be a symlink')
                directory.mkdir(parents=True, exist_ok=True)
                directory.chmod(0o755)
            if not dest.exists():
                temporary = dest.with_suffix('.new')
                shutil.copyfile(source, temporary); temporary.chmod(0o755)
                os.replace(temporary, dest)
            if digest(dest) != sha:
                raise ValueError('immutable installed artifact changed')
            if request.get('help_supported', False):
                subprocess.run([str(dest), '--help'], check=True, capture_output=True, timeout=15)
            if not journal.exists():
                if show(unit, 'NeedDaemonReload') != 'no':
                    raise ValueError('service has unapplied operator configuration')
                args = arguments(unit)
                protected = identity_hashes(args, request.get('protected_paths', []))
                protected[show(unit, 'FragmentPath')] = digest(show(unit, 'FragmentPath'))
                for path in shlex.split(show(unit, 'DropInPaths')):
                    if Path(path) != drop: protected[path] = digest(path)
                before = {'observation': observe(unit), 'arguments': args, 'protected': protected,
                          'budgets': {name: show(unit, name) for name in
                                      ('MemoryMax', 'TasksMax', 'LimitNOFILE')},
                          'dropin': drop.read_text() if drop.exists() else None}
                if not before['observation']['healthy']:
                    raise ValueError('native service must be healthy before its first rollout')
                write(journal, before)
            unchanged(json.loads(journal.read_text()), unit)
            return {'passed': True, 'sha256': sha}
        if not journal.exists():
            raise ValueError('activation or rollback has no retained preparation')
        before = json.loads(journal.read_text())
        unchanged(before, unit)
        if stage == 'activate':
            actual = observe(unit)
            if actual['healthy'] and actual['running']['sha256'] == sha:
                return {'passed': True, **actual}
            if actual['running']['sha256'] not in (None, before['observation']['running']['sha256']):
                raise ValueError('another operator changed the running artifact')
            if digest(dest) != sha:
                raise ValueError('prepared artifact changed')
            args = [str(dest), *before['arguments'][1:]]
            drop.parent.mkdir(exist_ok=True)
            temporary = drop.with_suffix('.new')
            temporary.write_text('[Service]\nExecStart=\nExecStart=' + shlex.join(args) + '\n')
            temporary.chmod(0o644); os.replace(temporary, drop)
            expected = sha
        elif stage == 'rollback':
            previous = before['observation']['running']
            actual = observe(unit)
            if actual['running']['sha256'] not in (None, sha, previous['sha256']):
                raise ValueError('another operator changed the running artifact')
            if digest(previous['executable']) != previous['sha256']:
                raise ValueError('retained rollback artifact changed')
            if before['dropin'] is None:
                drop.unlink(missing_ok=True)
            else:
                temporary = drop.with_suffix('.new')
                temporary.write_text(before['dropin']); temporary.chmod(0o644)
                os.replace(temporary, drop)
            expected = previous['sha256']
        else:
            raise ValueError('unsupported host mutation')
        subprocess.run(['systemctl', 'daemon-reload'], check=True, timeout=30)
        subprocess.run(['systemctl', 'restart', unit], check=True, timeout=90)
        # Require a stable process, not a momentary active state in a crash loop.
        first = observe(unit)
        time.sleep(5)
        actual = observe(unit)
        if (not actual['healthy'] or actual['running']['sha256'] != expected
                or actual['running']['process_id'] != first['running']['process_id']):
            raise ValueError('service did not remain healthy on the requested artifact')
        unchanged(before, unit)
        expected_arguments = ([str(dest), *before['arguments'][1:]] if stage == 'activate'
                              else before['arguments'])
        if arguments(unit) != expected_arguments:
            raise ValueError('service arguments changed during activation')
        write(work / (stage + '.json'), actual)
        return {'passed': True, 'protected_state_unchanged': True, **actual}


if __name__ == '__main__':
    os.umask(0o077)
    print(json.dumps(run(json.load(sys.stdin))))
