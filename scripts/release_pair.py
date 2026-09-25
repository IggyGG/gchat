"""Immutable paired inputs shared by CI, release workers and the coordinator."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def identity(root, commit='HEAD'):
    # Resolve locally once; only full object IDs cross a worker boundary.
    commit = git(root, 'rev-parse', '--verify', commit + '^{commit}')
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('expected a full SHA-1 source object')
    return {'commit': commit, 'tree': git(root, 'rev-parse', commit + '^{tree}')}


def freeze(chat, coms, versions, policy):
    sources = {name: identity(root) for name, root in [('gchat', chat), ('gcoms', coms)]}
    for name, root in [('gchat', chat), ('gcoms', coms)]:
        if git(root, 'status', '--porcelain', '--untracked-files=normal'):
            raise ValueError(name + ' source is not clean')
    value = {'schema': 1, 'sources': sources, 'versions': versions, 'policy': policy}
    value['release_id'] = hashlib.sha256(canonical(value)).hexdigest()
    return value


def validate(value):
    if type(value.get('schema')) is not int or value.get('schema') != 1 or set(value.get('sources', {})) != {'gchat', 'gcoms'}:
        raise ValueError('invalid paired release manifest')
    for source in value['sources'].values():
        if set(source) != {'commit', 'tree'} or any(
                not isinstance(v, str) or not re.fullmatch(r'[0-9a-f]{40}', v)
                for v in source.values()):
            raise ValueError('invalid source identity')
    if not isinstance(value.get('versions'), dict) or not isinstance(value.get('policy'), dict):
        raise ValueError('manifest needs explicit platform versions and release policy')
    for target, version in value['versions'].items():
        expression = r'[1-9][0-9]{0,9}' if target == 'android' else r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)'
        if not isinstance(version, str) or not re.fullmatch(expression, version):
            raise ValueError('invalid production platform version')
        if target == 'android' and int(version) > 2100000000:
            raise ValueError('Android version code exceeds the store limit')
    if 'refs' in value:
        refs = value['refs']
        if set(refs) != {'gchat', 'gcoms'} or not all(isinstance(ref, str) and re.fullmatch(r'refs/heads/(main|release/gchat-[0-9a-f]{16,64})', ref) for ref in refs.values()):
            raise ValueError('candidate refs must be protected release refs')
    unsigned = {k: v for k, v in value.items() if k != 'release_id'}
    if value.get('release_id') != hashlib.sha256(canonical(unsigned)).hexdigest():
        raise ValueError('release manifest digest mismatch')
    return value


def verify(value, chat, coms):
    validate(value)
    for name, root in [('gchat', chat), ('gcoms', coms)]:
        if identity(root) != value['sources'][name]:
            raise ValueError(name + ' checkout differs from frozen pair')
        if git(root, 'status', '--porcelain', '--untracked-files=normal'):
            raise ValueError(name + ' checkout is dirty')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze', 'verify'])
    parser.add_argument('--gchat', type=Path, required=True)
    parser.add_argument('--gcoms', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--versions', type=Path)
    parser.add_argument('--policy', type=Path)
    args = parser.parse_args()
    if args.action == 'verify':
        verify(json.loads(args.manifest.read_text()), args.gchat, args.gcoms)
    else:
        if args.versions is None or args.policy is None:
            parser.error('freeze requires --versions and --policy')
        value = freeze(args.gchat, args.gcoms, json.loads(args.versions.read_text()),
                       json.loads(args.policy.read_text()))
        # Never silently replace inputs of an already dispatched candidate.
        with args.manifest.open('xb') as stream:
            stream.write(canonical(value))
    print('Exact source pair verified')


if __name__ == '__main__':
    main()
