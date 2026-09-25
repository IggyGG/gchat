"""Prepare a version-only release branch without changing either working checkout."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from release_pair import canonical, git
from release_feed import version


def prepare(root, base, coms, versions, branch):
    root = Path(root)
    if not re.fullmatch(r'refs/heads/release/gchat-[0-9a-f]{16,64}', branch):
        raise ValueError('invalid immutable release branch')
    def read(path): return subprocess.check_output(['git', '-C', str(root), 'show', base + ':' + path])
    app_version = versions['linux-x86_64']; version(app_version)
    if any(versions[p] != app_version for p in ('macos-aarch64', 'macos-x86_64', 'windows-x86_64')):
        raise ValueError('desktop versions must agree')
    if not re.fullmatch('[1-9][0-9]{0,9}', versions['android']) or int(versions['android']) > 2100000000:
        raise ValueError('invalid Android version code')
    version(versions['ios'])
    config = json.loads(read('apps/client/src-tauri/tauri.conf.json'))
    config['version'] = app_version; config['bundle']['android']['versionCode'] = int(versions['android'])
    publication = json.loads(read('release/publication.json')); publication['version'] = app_version
    cargo = read('apps/client/src-tauri/Cargo.toml').decode()
    cargo, count = re.subn(r'(?m)^version = "[^"\n]+"$', f'version = "{app_version}"', cargo, count=1)
    if count != 1: raise ValueError('desktop version field missing')
    lock = read('apps/client/src-tauri/Cargo.lock').decode()
    lock, count = re.subn(r'(\[\[package\]\]\nname = "gchat-desktop"\nversion = ")[^"]+("\n)',
                          lambda m: m[1] + app_version + m[2], lock, count=1)
    if count != 1: raise ValueError('desktop lock version missing')
    files = {'apps/client/src-tauri/tauri.conf.json': canonical(config), 'release/publication.json': canonical(publication),
             'apps/client/src-tauri/Cargo.toml': cargo.encode(), 'apps/client/src-tauri/Cargo.lock': lock.encode(),
             'release/automation/versions.json': canonical({'schema': 1, 'versions': versions,
                                                          'based_on': {'gchat': base, 'gcoms': coms}})}
    # Isolated index creates a normal child commit. Never checkout/reset a user's
    # tree, and never force-push the source branch or an existing candidate branch.
    with tempfile.TemporaryDirectory(prefix='gchat-release-index-') as temp:
        environment = dict(os.environ, GIT_INDEX_FILE=str(Path(temp) / 'index'))
        def run(args, data=None):
            return subprocess.check_output(['git', '-C', str(root), *args], env=environment, input=data).decode().strip()
        run(['read-tree', base])
        for path, data in files.items():
            blob = run(['hash-object', '-w', '--stdin'], data)
            run(['update-index', '--add', '--cacheinfo', '100644,' + blob + ',' + path])
        tree = run(['write-tree'])
        existing = subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', branch], capture_output=True, text=True)
        if existing.returncode == 0:
            commit = existing.stdout.strip()
            if git(root, 'rev-parse', commit + '^{tree}') != tree or git(root, 'rev-parse', commit + '^') != base:
                raise ValueError('immutable release branch already has different inputs')
            return commit
        commit = run(['-c', 'user.name=Gh0st release', '-c', 'user.email=release@gchat.boo',
                      'commit-tree', tree, '-p', base], f'Prepare GChat {app_version} paired production release\n'.encode())
        run(['update-ref', branch, commit, '0' * 40])
        return commit
