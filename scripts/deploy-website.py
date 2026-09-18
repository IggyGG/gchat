#!/usr/bin/env python3
"""Deploy a static GChat bundle with immutable versions and an atomic activation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
from urllib.request import urlopen
import uuid

ROOT = Path(__file__).resolve().parents[1]
VERSION = r'[0-9a-f]{40}-[0-9a-f]{16}'
FILES = {'index.html', 'downloads.json', 'build.json', 'fonts/fixedsys-excelsior.ttf', 'fonts/LICENSE-CC0'}


def bundle(directory, commit):
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('website source must be a full commit ID')
    actual = {f.relative_to(directory).as_posix() for f in directory.rglob('*') if f.is_file()}
    if actual != FILES or any(f.is_symlink() for f in directory.rglob('*')):
        raise ValueError('unexpected website bundle contents')
    hashes = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in sorted(FILES)}
    build = json.loads((directory / 'build.json').read_text())
    if build['index_sha256'] != hashes['index.html']:
        raise ValueError('website build report differs from rendered page')
    identity = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:16]
    return commit + '-' + identity, hashes, build


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', type=Path, default=ROOT / 'dist/website')
    p.add_argument('--rollback', help='previous immutable version to activate')
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    host = os.environ.get('GCHAT_WEB_SSH', '')
    root = os.environ.get('GCHAT_WEB_ROOT', '').rstrip('/')
    if not re.fullmatch(r'[A-Za-z0-9_.@-]+', host) or host.startswith('-'):
        raise ValueError('GCHAT_WEB_SSH must name the configured website SSH host/user')
    if not re.fullmatch(r'/[A-Za-z0-9_./-]+', root) or '..' in Path(root).parts or root in ('/var', '/srv', '/var/www'):
        raise ValueError('GCHAT_WEB_ROOT must name a dedicated GChat website directory')
    if a.rollback:
        revision = a.rollback
        if not re.fullmatch(VERSION, revision):
            raise ValueError('rollback requires a full immutable version ID')
    else:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        revision, hashes, build = bundle(a.directory.resolve(), commit)
    if a.dry_run:
        print(json.dumps({'ssh': host, 'root': root, 'revision': revision, 'rollback': bool(a.rollback), 'deployed': False}))
        return
    q = shlex.quote
    version = root + '/releases/' + revision
    ssh = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', host]
    previous = subprocess.check_output(ssh + [f'readlink {q(root + "/current")} || true'], text=True).strip()
    if previous and not re.fullmatch('releases/' + VERSION, previous):
        raise ValueError('current is not a managed website version; finish dedicated host setup first')
    if not a.rollback:
        stage = root + '/releases/.upload-' + uuid.uuid4().hex
        subprocess.run(ssh + [f'mkdir -p {q(stage)}'], check=True)
        subprocess.run(['rsync', '-r', '--checksum', '--chmod=D755,F644', '-e', 'ssh -o BatchMode=yes -o StrictHostKeyChecking=yes', str(a.directory.resolve()) + '/', host + ':' + stage + '/'], check=True)
        checksums = ''.join(f'{sha}  {name}\n' for name, sha in hashes.items())
        subprocess.run(ssh + [f'cd {q(stage)} && sha256sum -c -'], input=checksums, text=True, check=True)
        # A retry must reuse identical content; it cannot overwrite an active directory.
        install = f'if test -d {q(version)}; then diff -qr {q(stage)} {q(version)}; else mv -T {q(stage)} {q(version)}; fi'
        subprocess.run(ssh + [f'flock {q(root + "/.deploy-lock")} sh -c {q(install)}'], check=True)
    activate = f'test -f {q(version + "/index.html")} && cd {q(root)} && ln -sfn {q("releases/" + revision)} .next && mv -Tf .next current'
    subprocess.run(ssh + [f'flock {q(root + "/.deploy-lock")} sh -c {q(activate)}'], check=True)
    if not a.rollback:
        try:
            with urlopen('https://gchat.boo/build.json', timeout=30) as response:
                if json.load(response) != build:
                    raise ValueError('public build report mismatch')
            with urlopen('https://gchat.boo/', timeout=30) as response:
                if hashlib.sha256(response.read()).hexdigest() != hashes['index.html']:
                    raise ValueError('public page digest mismatch')
        except Exception:
            if previous:
                restore = f'cd {q(root)} && if test "$(readlink current)" = {q("releases/" + revision)}; then ln -sfn {q(previous)} .next && mv -Tf .next current; fi'
                subprocess.run(ssh + [f'flock {q(root + "/.deploy-lock")} sh -c {q(restore)}'], check=True)
            raise RuntimeError('website verification failed; previous managed version restored when available') from None
    print('Website activated: ' + revision)


if __name__ == '__main__':
    main()
