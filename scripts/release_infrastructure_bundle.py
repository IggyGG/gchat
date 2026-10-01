"""Retain CI-qualified infrastructure and publish immutable OCI images.

The Linux worker's verified provider archive is the authority, not a caller's
qualified flag. OCI blobs remain on release storage so registry loss is repaired
without rebuilding a deployed or rollback image.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tarfile
import zipfile

from release_coordinator import atomic_json, read_receipt
from release_feed import digest
from release_pair import canonical, validate

BINARIES = ('gcnode', 'gcoms-catalog', 'gc-network-operator', 'gcoms-channel-service')
FILES = (*BINARIES, 'image.tar', 'controller.tar', 'push.tar', 'push-context.json', 'Dockerfile', 'ca-certificates.crt')
IMAGES = {
    'services': ('image.tar', 'oci', 'image_config', 'registry_repository', 'pull_repository'),
    'controller': ('controller.tar', 'controller-oci', 'controller_config', 'controller_registry_repository', 'controller_pull_repository'),
    'push': ('push.tar', 'push-oci', 'push_config', 'push_registry_repository', 'push_pull_repository'),
}


def archive_transport(path):
    # Docker's containerd store exports OCI blobs alongside its compatibility
    # manifest. Reading that archive through docker-archive reserializes config
    # JSON and changes its digest. Read the native OCI representation instead.
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        selected = {name: [m for m in members if m.name == name] for name in ('oci-layout', 'index.json')}
        if any(selected.values()):
            if any(len(items) != 1 or not items[0].isfile() for items in selected.values()):
                raise ValueError('image archive has an incomplete or ambiguous OCI layout')
            return 'oci-archive:' + str(path), []
    # Traditional Docker manifests must be converted to an OCI manifest for
    # the OCI layout reader. The qualified configuration hash is still checked.
    return 'docker-archive:' + str(path), ['--format', 'oci']


def retain_archive(archive, root, manifest):
    # Read the provider archive bound by the build receipt. The extracted cache
    # is derived data and cannot authenticate its own replacement hashes.
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        reports = [name for name in names if name == 'infrastructure/build.json'
                   or name.endswith('/infrastructure/build.json')]
        if len(reports) != 1 or len(names) != len(set(names)):
            raise ValueError('qualified worker has no unambiguous infrastructure bundle')
        original = json.loads(bundle.read(reports[0]))
        if original.get('sources') != manifest['sources'] or original.get('release_id') != manifest['release_id']:
            raise ValueError('infrastructure bundle does not bind the frozen CI source')
        required = set(FILES)
        if set(original['sha256']) != required:
            raise ValueError('infrastructure bundle has unexpected or missing files')
        prefix = reports[0].rsplit('/', 1)[0] + '/'
        root.mkdir(parents=True, exist_ok=True)
        for name, expected in original['sha256'].items():
            destination = root / name
            with tempfile.NamedTemporaryFile(dir=root, delete=False) as stream:
                temporary = Path(stream.name)
                try:
                    with bundle.open(prefix + name) as source:
                        shutil.copyfileobj(source, stream)
                    stream.flush(); os.fsync(stream.fileno()); stream.close()
                    if digest(temporary) != expected:
                        raise ValueError('qualified infrastructure file changed')
                    if destination.exists() and digest(destination) != expected:
                        raise ValueError('retained source bundle changed')
                    if not destination.exists(): os.replace(temporary, destination)
                    if name in BINARIES: destination.chmod(0o755)
                finally:
                    temporary.unlink(missing_ok=True)
        return original


def publish(directory, config, tag, image='services'):
    directory = Path(directory)
    archive, layout, configuration, registry, pull = IMAGES[image]
    oci = directory / layout
    # An interrupted conversion is disposable derived data; source archives are
    # immutable and retained. A complete index is verified by skopeo on every use.
    if not (oci / 'index.json').exists():
        transport, flags = archive_transport(directory / archive)
        subprocess.run(['skopeo', 'copy', *flags, transport,
                        'oci:' + str(oci) + ':release'], check=True, timeout=300,
                       stdout=subprocess.DEVNULL)
    source = 'oci:' + str(oci) + ':release'
    raw = subprocess.check_output(['skopeo', 'inspect', '--raw', source], timeout=30)
    manifest = json.loads(raw)
    build = json.loads((directory / 'source-build.json').read_text())
    expected_config = build[configuration]
    if manifest['config']['digest'] != expected_config:
        raise ValueError('OCI conversion changed the qualified image configuration')
    sha = 'sha256:' + hashlib.sha256(raw).hexdigest()
    destination = config[registry]
    tls = [] if config.get('registry_tls', True) else ['--tls-verify=false']
    # A surviving manifest does not prove its layers survived registry loss.
    # Skopeo checks every blob and uploads only missing content even when the
    # manifest already exists. Keep this repair ahead of each cold pull probe.
    flags = [] if config.get('registry_tls', True) else ['--dest-tls-verify=false']
    subprocess.run(['skopeo', 'copy', '--preserve-digests', *flags, source,
                    'docker://' + destination + ':' + tag], check=True, timeout=300,
                   stdout=subprocess.DEVNULL)
    actual = subprocess.check_output(['skopeo', 'inspect', '--raw', *tls,
                                      'docker://' + destination + '@' + sha], timeout=30)
    if actual != raw: raise ValueError('registry read-back changed the image manifest')
    return config[pull] + '@' + sha


def collect(state, manifest, config):
    state = Path(state)
    root = state / 'infrastructure' / manifest['release_id']
    ready = root / 'build.json'
    if not ready.exists():
        jobs = {stage: state / 'jobs' / hashlib.sha256(canonical(
            [manifest['release_id'], 'linux-x86_64', stage])).hexdigest() for stage in ('build', 'verify')}
        if not all((path / 'receipt.json').is_file() for path in jobs.values()): return None
        for stage, path in jobs.items():
            read_receipt(path / 'receipt.json', manifest, 'linux-x86_64', stage)
        receipt, _ = read_receipt(jobs['build'] / 'receipt.json', manifest, 'linux-x86_64', 'build')
        if not any(ref['path'] == 'native.zip' for ref in receipt['evidence']):
            raise ValueError('provider archive is not bound by the build receipt')
        original = retain_archive(jobs['build'] / 'native.zip', root, manifest)
        atomic_json(root / 'source-build.json', original)
        atomic_json(root / 'qualification.json', {'release_id': manifest['release_id'], 'sources': manifest['sources'],
            'receipts': {stage: {'path': str(path / 'receipt.json'), 'sha256': digest(path / 'receipt.json')}
                         for stage, path in jobs.items()}})
        images = {name: publish(root, config, name + '-' + manifest['release_id'], name)
                  for name in IMAGES}
        atomic_json(ready, {**original, 'qualified': True, 'images': images,
                           'qualification_sha256': digest(root / 'qualification.json')})
    value = json.loads(ready.read_text())
    if value.get('sources') != manifest['sources'] or value.get('qualified') is not True:
        raise ValueError('retained bundle has the wrong qualification identity')
    if digest(root / 'qualification.json') != value['qualification_sha256']:
        raise ValueError('retained qualification changed')
    for name, expected in value['sha256'].items():
        if digest(root / name) != expected: raise ValueError('retained infrastructure artifact changed')
    for name in IMAGES:
        image = publish(root, config, name + '-' + manifest['release_id'], name)
        if value['images'][name] != image:
            raise ValueError('retained OCI image changed; refusing to relabel its deployment')
    return ready


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    manifest = validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()))
    path = collect(args.state, manifest, json.loads(args.config.read_text()))
    if path is None: raise SystemExit(75)
    output = Path(os.environ['GCHAT_RELEASE_RECEIPT'])
    evidence = output.parent / 'infrastructure-build.json'; shutil.copyfile(path, evidence)
    atomic_json(output, {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
        'platform': 'linux-x86_64', 'stage': 'infrastructure', 'passed': True, 'source_unchanged': True,
        'evidence': [{'path': evidence.name, 'sha256': digest(evidence)}]})


if __name__ == '__main__': main()
