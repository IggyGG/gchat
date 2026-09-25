#!/usr/bin/env python3
"""Build an atomic APT snapshot containing only source-qualified GChat packages."""
import argparse
import datetime
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid

from release_coordinator import read_receipt
from release_feed import digest
from release_pair import validate
from release_signatures import fingerprint, verify


def build(manifest, package, signature, verification, compatibility, output, key):
    validate(manifest)
    platform = 'linux-x86_64'
    qualified, _ = read_receipt(verification, manifest, platform, 'verify')
    compatible, _ = read_receipt(compatibility, manifest, platform, 'compatibility')
    if compatible.get('relay_compatible') is not True: raise ValueError('relay compatibility is not established')
    key = fingerprint(key); package = Path(package).resolve(); output = Path(output).resolve()
    sha = digest(package)
    if not any(item['sha256'] == sha for item in qualified['evidence']): raise ValueError('package is not qualified')
    verify(signature, package, key)
    metadata = subprocess.check_output(['dpkg-deb', '-f', str(package), 'Package', 'Version', 'Architecture'], text=True)
    fields = dict(line.split(': ', 1) for line in metadata.splitlines())
    if fields != {'Package': 'g-chat', 'Version': manifest['versions'][platform], 'Architecture': 'amd64'}:
        raise ValueError('APT package identity differs from the frozen candidate')
    output.mkdir(parents=True, exist_ok=True)
    with (output / '.apt.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        # Immutable pools remain reachable while clients finish an earlier index.
        pool = output / 'pool' / manifest['release_id']
        pool.mkdir(parents=True, exist_ok=True)
        target = pool / f'g-chat_{fields["Version"]}_amd64.deb'
        if target.exists() and digest(target) != sha: raise ValueError('immutable Debian package changed')
        if not target.exists():
            with tempfile.NamedTemporaryFile(dir=pool, delete=False) as stream:
                temporary = Path(stream.name)
                try:
                    with package.open('rb') as source: shutil.copyfileobj(source, stream)
                    stream.flush(); os.fsync(stream.fileno())
                    if digest(temporary) != sha: raise ValueError('Debian package changed during publication')
                    temporary.chmod(0o644); os.replace(temporary, target)
                finally: temporary.unlink(missing_ok=True)
        index = subprocess.check_output(['dpkg-scanpackages', '--multiversion', 'pool', '/dev/null'], cwd=output)
        now = datetime.datetime.now(datetime.timezone.utc)
        snapshot = output / 'snapshots' / (manifest['release_id'] + '-' + uuid.uuid4().hex)
        binary = snapshot / 'main/binary-amd64'; binary.mkdir(parents=True)
        (binary / 'Packages').write_bytes(index)
        (binary / 'Packages.gz').write_bytes(gzip.compress(index, mtime=0))
        release = ('Origin: GChat\nLabel: GChat\nSuite: stable\nCodename: stable\n'
                   'Architectures: amd64\nComponents: main\nAcquire-By-Hash: yes\n'
                   f'Date: {now.strftime("%a, %d %b %Y %H:%M:%S +0000")}\n'
                   f'Valid-Until: {(now + datetime.timedelta(days=14)).strftime("%a, %d %b %Y %H:%M:%S +0000")}\nSHA256:\n')
        for path in [binary / 'Packages', binary / 'Packages.gz']:
            h = digest(path); release += f' {h} {path.stat().st_size} {path.relative_to(snapshot).as_posix()}\n'
            byhash = binary / 'by-hash/SHA256' / h; byhash.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, byhash)
        (snapshot / 'Release').write_text(release)
        # GPG agent/protected GNUPGHOME supplies the already configured key.
        for flags, destination in [(['--clearsign'], 'InRelease'), (['--armor', '--detach-sign'], 'Release.gpg')]:
            unlock = ['--pinentry-mode', 'loopback', '--passphrase-file', os.environ['GCHAT_RELEASE_PASSPHRASE_FILE']] if os.environ.get('GCHAT_RELEASE_PASSPHRASE_FILE') else []
            subprocess.run(['gpg', '--batch', '--yes', *unlock, '--local-user', key, *flags, '--output', str(snapshot / destination), str(snapshot / 'Release')], check=True)
        verify(snapshot / 'Release.gpg', snapshot / 'Release', key)
        # Copy historical by-hash indices into the new snapshot before switching:
        # clients holding an old Release must still resolve its immutable hashes.
        stable = output / 'dists/stable'
        if stable.exists():
            previous = stable.resolve() / 'main/binary-amd64/by-hash'
            if previous.exists(): shutil.copytree(previous, binary / 'by-hash', dirs_exist_ok=True)
        stable.parent.mkdir(exist_ok=True)
        link = stable.parent / ('.stable-' + manifest['release_id'])
        link.unlink(missing_ok=True); link.symlink_to(os.path.relpath(snapshot, stable.parent))
        os.replace(link, stable)
        return {'package': target.relative_to(output).as_posix(), 'sha256': sha, 'release': digest(snapshot / 'Release')}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('manifest', 'package', 'signature', 'verification', 'compatibility', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--key', required=True)
    a = p.parse_args()
    build(json.loads(a.manifest.read_text()), a.package, a.signature, a.verification, a.compatibility, a.output, a.key)
    print('Signed GChat APT snapshot published')


if __name__ == '__main__': main()
