#!/usr/bin/env python3
"""Publish one exact platform bundle without modifying an existing release."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from urllib.error import HTTPError

from platform_release import immutable_assets, public_manifest, validate
from release_evidence import digest, file_reference, read_json, require
from release_signatures import fingerprint, verify, verify_tag

SPEC = importlib.util.spec_from_file_location('paired_publisher', Path(__file__).with_name('publish-release.py'))
paired = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(paired)


def github_asset_hash(item):
    raw = subprocess.check_output(['gh', 'api', '-H', 'Accept: application/octet-stream',
                                   f'repos/IggyGG/gchat/releases/assets/{item["id"]}'])
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('manifest', 'check', 'publish'))
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--gchat', type=Path, required=True)
    parser.add_argument('--gcoms', type=Path, required=True)
    parser.add_argument('--notes', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); base = args.candidate.resolve().parent
    candidate = read_json(args.candidate)
    commit = candidate['sources']['gchat']['commit']
    publication = json.loads(subprocess.check_output(['git', 'show', commit + ':release/publication.json'], cwd=args.gchat))
    for name, root in (('gchat', args.gchat), ('gcoms', args.gcoms)):
        source = candidate['sources'][name]
        tree = subprocess.check_output(['git', 'rev-parse', source['commit'] + '^{tree}'], cwd=root, text=True).strip()
        require(tree == source['tree'], 'source commit/tree mismatch')
    with tempfile.TemporaryDirectory(prefix='gchat-platform-signatures-') as temporary:
        home = Path(temporary); home.chmod(0o700)
        key = file_reference(base, candidate['release_key'])
        subprocess.run(['gpg', '--homedir', str(home), '--batch', '--import', str(key)], check=True, capture_output=True)
        validate(candidate, base, publication, home)
        manifest_bytes = (json.dumps(public_manifest(candidate, base), sort_keys=True, indent=2) + '\n').encode()
        if args.action == 'manifest':
            args.output.parent.mkdir(parents=True, exist_ok=True)
            if args.output.exists():
                require(args.output.read_bytes() == manifest_bytes, 'refusing to replace a different platform manifest')
            else:
                with args.output.open('xb') as stream: stream.write(manifest_bytes)
            return
        manifest = base / 'platform-release.json'
        require(manifest.read_bytes() == manifest_bytes, 'signed platform manifest differs from qualified inputs')
        pin = fingerprint(candidate['release_key']['fingerprint'])
        verify(base / 'platform-release.json.asc', manifest, pin, home)
        assets = {'platform-release.json': manifest, 'platform-release.json.asc': base / 'platform-release.json.asc',
                  'gchat-release-key.asc': key,
                  'gchat-release-key.asc.asc': file_reference(base, candidate['release_key']['signature'])}
        for name, item in candidate['artifacts'].items():
            assets[name] = file_reference(base, item)
            assets[name + '.asc'] = file_reference(base, item['signature'])
        hashes = {name: digest(path) for name, path in assets.items()}
        tag = candidate['tag']
        verify_tag(args.gchat, tag, pin)
        require(subprocess.check_output(['git', 'rev-parse', tag + '^{}'], cwd=args.gchat, text=True).strip() == commit,
                'platform tag differs from qualified source')
        if args.action == 'check':
            args.output.write_text(json.dumps({'passed': True, 'published': False, 'tag': tag, 'assets': hashes}, indent=2) + '\n')
            return
        require(args.notes is not None, 'release notes with qualification limits are required')
        # Both source commits must already be available in the public mirrors.
        for name, source in candidate['sources'].items():
            obj = paired.github(f'repos/IggyGG/{name}/git/commits/{source["commit"]}')
            require(obj.get('sha') == source['commit'] and obj['tree']['sha'] == source['tree'], 'public source differs from qualified pair')
        local_tag = subprocess.check_output(['git', 'rev-parse', 'refs/tags/' + tag], cwd=args.gchat, text=True).strip()
        for remote in ('forgejo', 'https://github.com/IggyGG/gchat.git'):
            refs = subprocess.check_output(['git', 'ls-remote', remote, 'refs/tags/' + tag], cwd=args.gchat, text=True).split()
            require(len(refs) == 2 and refs[0] == local_tag, 'both mirrors must contain the exact signed platform tag')
        forgejo = paired.Forgejo(); notes = args.notes.read_text()
        local = 'repos/ghost-local/gchat/releases'; remote = 'repos/IggyGG/gchat/releases'
        try: source = forgejo.request(local + '/tags/' + tag)
        except HTTPError as error:
            if error.code != 404: raise
            source = forgejo.request(local, 'POST', {'tag_name': tag, 'target_commitish': commit, 'name': tag,
                                                    'body': notes, 'draft': True, 'prerelease': False})
        require(source['tag_name'] == tag, 'unexpected private platform release')
        missing = immutable_assets(source, hashes, lambda item: forgejo.asset_hash(item['browser_download_url']))
        for name in sorted(missing):
            item = forgejo.upload(local + '/' + str(source['id']) + '/assets', assets[name], name)
            require(forgejo.asset_hash(item['browser_download_url']) == hashes[name], 'private uploaded asset mismatch')
        forgejo.request(local + '/' + str(source['id']), 'PATCH', {'draft': False})
        releases = paired.github(remote + '?per_page=100')
        destination = next((item for item in releases if item['tag_name'] == tag), None)
        if destination is None:
            destination = paired.github(remote, 'POST', {'tag_name': tag, 'target_commitish': commit, 'name': tag,
                                                         'body': notes, 'draft': True, 'prerelease': False})
        missing = immutable_assets(destination, hashes, github_asset_hash)
        with tempfile.TemporaryDirectory(prefix='gchat-platform-publish-') as staging:
            for name in sorted(missing):
                copy = Path(staging) / name; copy.write_bytes(assets[name].read_bytes())
                paired.gh('release', 'upload', tag, str(copy), '--repo', 'IggyGG/gchat')
                uploaded = paired.github(remote + '/' + str(destination['id']) + '/assets?per_page=100')
                item = next(item for item in uploaded if item['name'] == name)
                require(github_asset_hash(item) == hashes[name], 'public uploaded asset mismatch')
        paired.github(remote + '/' + str(destination['id']), 'PATCH', {'draft': False})
        for name, sha in hashes.items():
            require(paired.public_asset_hash(f'https://github.com/IggyGG/gchat/releases/download/{tag}/{name}') == sha,
                    'final public artifact mismatch')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({'passed': True, 'published': True, 'tag': tag, 'sources': candidate['sources'],
                                          'assets': hashes}, indent=2) + '\n')


if __name__ == '__main__':
    main()
