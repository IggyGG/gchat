#!/usr/bin/env python3
"""Build retained native services and their container after the frozen CI gate."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import hashlib
import tarfile
from pathlib import PurePosixPath

from release_feed import digest
from release_pair import identity, validate
from release_coordinator import atomic_json

BASE = 'ubuntu:24.04@sha256:008173c23f95b170204355c12626cb5a965d779a7e1283b09e9cffbb1bf33ca3'
BINARIES = ('gcnode', 'gcoms-catalog', 'gc-network-operator', 'gcoms-channel-service')


def archive_config(path, tag):
    # Docker's .Id may be an attested image index with the containerd store.
    # The retained docker-save archive binds the actual configuration bytes.
    with tarfile.open(path) as archive:
        reports = [m for m in archive.getmembers() if m.name == 'manifest.json']
        if len(reports) != 1 or not reports[0].isfile() or reports[0].size > 1024 * 1024:
            raise ValueError('image archive has no unambiguous Docker manifest')
        images = json.load(archive.extractfile(reports[0]))
        selected = [m for m in images if tag in m.get('RepoTags', [])]
        if len(selected) != 1:
            raise ValueError('image archive does not bind the exact build tag')
        name = selected[0]['Config']; relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('image configuration path escapes archive')
        members = [m for m in archive.getmembers() if m.name == name]
        if len(members) != 1 or not members[0].isfile() or not 0 < members[0].size <= 16 * 1024 * 1024:
            raise ValueError('image archive configuration is missing or ambiguous')
        return 'sha256:' + hashlib.sha256(archive.extractfile(members[0]).read()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gcoms', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()))
    root = args.gcoms.resolve(); output = args.output.resolve()
    chat = Path(__file__).resolve().parents[1]
    if identity(root) != manifest['sources']['gcoms'] or identity(chat) != manifest['sources']['gchat']:
        raise ValueError('infrastructure checkout differs from frozen candidate')
    subprocess.run(['cargo', 'build', '--locked', '--release', '-p', 'gcoms-node',
                    '-p', 'gcoms-catalog', '-p', 'gcoms-channel-service', '--features',
                    'gcoms-node/experimental-gc2,gcoms-node/push-gateway,gcoms-catalog/experimental-gc2'],
                   cwd=root, check=True)
    output.mkdir(parents=True, exist_ok=False)
    target = Path(os.environ.get('CARGO_TARGET_DIR', root / 'target'))
    if not target.is_absolute(): target = root / target
    target = target.resolve() / 'release'
    for name in BINARIES: shutil.copy2(target / name, output / name)
    shutil.copy2('/etc/ssl/certs/ca-certificates.crt', output / 'ca-certificates.crt')
    dockerfile = output / 'Dockerfile'
    dockerfile.write_text('FROM ' + BASE + '\n'
        'COPY gcnode gcoms-catalog gc-network-operator gcoms-channel-service /usr/local/bin/\n'
        'COPY gcoms-catalog /usr/local/bin/gc-catalog\n'
        'COPY ca-certificates.crt /etc/ssl/certs/ca-certificates.crt\n'
        'USER 65532:65532\nENTRYPOINT ["/usr/local/bin/gcnode"]\n')
    tag = 'gchat-infrastructure:' + manifest['sources']['gcoms']['commit']
    subprocess.run(['docker', 'build', '--platform', 'linux/amd64', '-t', tag, str(output)], check=True)
    subprocess.run(['docker', 'save', '-o', str(output / 'image.tar'), tag], check=True)
    image_id = archive_config(output / 'image.tar', tag)
    controller = 'gchat-controller:' + manifest['sources']['gchat']['commit']
    subprocess.run(['docker', 'build', '--platform', 'linux/amd64', '-t', controller,
        '--build-arg', 'GCHAT_CONTROLLER_REVISION=' + manifest['sources']['gchat']['commit'],
        '-f', str(chat / 'release/automation/Dockerfile'), str(chat)], check=True)
    subprocess.run(['docker', 'save', '-o', str(output / 'controller.tar'), controller], check=True)
    controller_id = archive_config(output / 'controller.tar', controller)
    if identity(root) != manifest['sources']['gcoms'] or identity(chat) != manifest['sources']['gchat']:
        raise ValueError('infrastructure source changed during build')
    atomic_json(output / 'build.json', {'schema': 1, 'sources': manifest['sources'],
        'gcoms_source': manifest['sources']['gcoms'],
        'release_id': manifest['release_id'], 'runtime_base': BASE, 'image_tag': tag,
        'image_config': image_id, 'controller_config': controller_id,
        'sha256': {name: digest(output / name) for name in
            (*BINARIES, 'image.tar', 'controller.tar', 'Dockerfile', 'ca-certificates.crt')}})


if __name__ == '__main__': main()
