#!/usr/bin/env python3
"""Maintain release state without changing which application is advertised."""
import datetime
import email.utils
import fcntl
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import time
import uuid

from release_coordinator import atomic_json
from release_feed import digest
from release_signatures import fingerprint, verify


def refresh_apt(output, key, now=None):
    output = Path(output)
    stable = output / 'dists/stable'
    if not stable.exists(): return False
    now = now or datetime.datetime.now(datetime.timezone.utc)
    key = fingerprint(key)
    with (output / '.apt.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        previous = stable.resolve()
        if not previous.is_relative_to((output / 'snapshots').resolve()):
            raise ValueError('APT pointer escapes retained snapshots')
        verify(previous / 'Release.gpg', previous / 'Release', key)
        text = (previous / 'Release').read_text()
        dates = [line.split(': ', 1)[1] for line in text.splitlines() if line.startswith('Valid-Until: ')]
        if len(dates) != 1: raise ValueError('APT validity missing or ambiguous')
        if email.utils.parsedate_to_datetime(dates[0]) - now > datetime.timedelta(days=7): return False
        hashes = text.split('\nSHA256:\n')
        if len(hashes) != 2: raise ValueError('APT index has no unambiguous SHA256 section')
        for line in hashes[1].splitlines():
            sha, size, name = line.split()
            path = (previous / name).resolve()
            if not path.is_relative_to(previous) or not path.is_file() or path.stat().st_size != int(size) or digest(path) != sha:
                raise ValueError('signed APT index changed')
        snapshot = output / 'snapshots' / ('refresh-' + uuid.uuid4().hex)
        snapshot.mkdir()
        shutil.copytree(previous / 'main', snapshot / 'main', copy_function=os.link)
        lines = []
        for line in text.splitlines():
            if line.startswith('Date: '): line = 'Date: ' + email.utils.format_datetime(now, usegmt=True)
            if line.startswith('Valid-Until: '): line = 'Valid-Until: ' + email.utils.format_datetime(now + datetime.timedelta(days=14), usegmt=True)
            lines.append(line)
        (snapshot / 'Release').write_text('\n'.join(lines) + '\n')
        unlock = ['--pinentry-mode', 'loopback', '--passphrase-file', os.environ['GCHAT_RELEASE_PASSPHRASE_FILE']] if os.environ.get('GCHAT_RELEASE_PASSPHRASE_FILE') else []
        for flags, destination in [(['--clearsign'], 'InRelease'), (['--armor', '--detach-sign'], 'Release.gpg')]:
            subprocess.run(['gpg', '--batch', '--yes', *unlock, '--local-user', key, *flags,
                            '--output', str(snapshot / destination), str(snapshot / 'Release')], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=60)
        verify(snapshot / 'Release.gpg', snapshot / 'Release', key)
        link = stable.parent / ('.refresh-' + uuid.uuid4().hex)
        link.symlink_to(os.path.relpath(snapshot, stable.parent)); os.replace(link, stable)
        return True


def maintain(state, ledger, config):
    state = Path(state)
    marker = state / 'maintenance.json'
    if marker.exists() and time.time() - marker.stat().st_mtime < 86400: return
    if config.get('apt'):
        refresh_apt(Path(config['apt']['root']), config['apt']['key'])
    backup = state / 'backups'
    backup.mkdir(mode=0o700, exist_ok=True)
    name = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    temporary = backup / (name + '.partial')
    with sqlite3.connect(temporary) as destination: ledger.db.backup(destination)
    temporary.chmod(0o600); os.replace(temporary, backup / (name + '.sqlite'))
    # Only our completed, daily database backups expire. Job receipts, provider
    # journals, manifests, source and published payloads are never removed here.
    for old in sorted(backup.glob('*.sqlite'))[:-7]: old.unlink()
    atomic_json(marker, {'completed_at': int(time.time()), 'database_backup': name + '.sqlite'})
