"""Compiler cache identities, never qualification or publication evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tomllib

SCOPES = {
    'gchat': '.cache/linux-gchat-target',
    'gcoms': '.cache/linux-gcoms-target',
    'services': '.cache/linux-infrastructure-target',
}
LOCKS = {
    'gchat': ('Cargo.lock', 'apps/client/src-tauri/Cargo.lock',
              'release/contracts/consumer/Cargo.lock'),
    'gcoms': ('Cargo.lock', 'examples/rust-integration/Cargo.lock',
              'mobile/native/Cargo.lock', 'fuzz/Cargo.lock'),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def own_package(name):
    return name in ('gcoms', 'gchat') or name.startswith(('gcoms-', 'gchat-'))


def dependencies(workspace):
    """Release version bumps must not evict unchanged third-party compilation."""
    rust, npm = {}, {}
    for project, names in LOCKS.items():
        root = workspace / project
        for name in names:
            path = root / name
            if not path.is_file():
                if name == 'Cargo.lock':
                    raise ValueError('missing workspace dependency lock: ' + project)
                continue
            records = tomllib.loads(path.read_text())['package']
            for item in records:
                if item.get('source') and not own_package(item['name']):
                    record = {key: item[key] for key in ('name', 'version', 'source', 'checksum') if key in item}
                    rust[digest(record)] = record
        lock = root / 'package-lock.json'
        if lock.is_file():
            for name, item in json.loads(lock.read_text()).get('packages', {}).items():
                package_name = name.rsplit('node_modules/', 1)[-1]
                if (not name.startswith('node_modules/') or item.get('link')
                        or package_name.startswith(('@gcoms/', '@gchat/'))):
                    continue
                record = {key: item[key] for key in ('version', 'resolved', 'integrity') if key in item}
                record['name'] = name
                npm[digest(record)] = record
    return {'rust': sorted(rust.values(), key=digest), 'npm': sorted(npm.values(), key=digest)}


def identity(workspace, scope, image):
    if scope not in SCOPES or not image:
        raise ValueError('known cache scope and runner image required')
    pins = [tomllib.loads((workspace / project / 'rust-toolchain.toml').read_text())['toolchain']
            for project in LOCKS]
    if pins[0] != pins[1]:
        raise ValueError('paired Rust toolchains differ')
    # Change this profile revision if compiler flags or warm-build graphs change.
    profile = {'revision': 1, 'scope': scope, 'target': 'x86_64-unknown-linux-gnu',
               'image': image, 'rust': pins[0], 'node': '22.23.2', 'npm': '11.6.2',
               'incremental': False, 'dev_debug': 0, 'test_debug': 0}
    prefix = 'linux-compiler-v1-' + scope + '-' + digest(profile)[:20] + '-'
    return {'key': prefix + digest(dependencies(workspace)), 'restore_prefix': prefix,
            'target': SCOPES[scope], 'qualification_reused': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path.cwd())
    parser.add_argument('--scope', required=True, choices=SCOPES)
    parser.add_argument('--image', default=os.environ.get('ImageOS', '') + '/' + os.environ.get('ImageVersion', ''))
    parser.add_argument('--github-output', type=Path)
    args = parser.parse_args()
    if args.image == '/':
        parser.error('runner image identity is missing; supply --image for local checks')
    result = identity(args.workspace.resolve(), args.scope, args.image)
    if args.github_output:
        with args.github_output.open('a') as output:
            for key in ('key', 'restore_prefix', 'target'):
                output.write(key + '=' + result[key] + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
