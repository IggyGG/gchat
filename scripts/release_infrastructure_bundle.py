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
import zipfile

from release_coordinator import atomic_json, read_receipt
from release_feed import digest
from release_pair import canonical, validate

BINARIES = ('gcnode', 'gcoms-catalog', 'gc-network-operator', 'gcoms-channel-service')


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
        if original.get('gcoms_source') != manifest['sources']['gcoms'] or original.get('release_id') != manifest['release_id']:
            raise ValueError('infrastructure bundle does not bind the frozen CI source')
        required = {*BINARIES, 'image.tar', 'Dockerfile', 'ca-certificates.crt'}
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


def publish(directory, config, tag):
    directory = Path(directory)
    oci = directory / 'oci'
    # An interrupted conversion is disposable derived data; source archives are
    # immutable and retained. A complete index is verified by skopeo on every use.
    if not (oci / 'index.json').exists():
        subprocess.run(['skopeo', 'copy', 'docker-archive:' + str(directory / 'image.tar'),
                        'oci:' + str(oci) + ':release'], check=True, timeout=300,
                       stdout=subprocess.DEVNULL)
    source = 'oci:' + str(oci) + ':release'
    raw = subprocess.check_output(['skopeo', 'inspect', '--raw', source], timeout=30)
    manifest = json.loads(raw)
    build = json.loads((directory / 'source-build.json').read_text())
    if manifest['config']['digest'] != build['image_config']:
        raise ValueError('OCI conversion changed the qualified image configuration')
    sha = 'sha256:' + hashlib.sha256(raw).hexdigest()
    destination = config['registry_repository']
    tls = [] if config.get('registry_tls', True) else ['--tls-verify=false']
    observed = subprocess.run(['skopeo', 'inspect', '--raw', *tls, 'docker://' + destination + '@' + sha],
                              capture_output=True, timeout=30)
    if observed.returncode or observed.stdout != raw:
        flags = [] if config.get('registry_tls', True) else ['--dest-tls-verify=false']
        subprocess.run(['skopeo', 'copy', '--preserve-digests', *flags, source,
                        'docker://' + destination + ':' + tag], check=True, timeout=300,
                       stdout=subprocess.DEVNULL)
        actual = subprocess.check_output(['skopeo', 'inspect', '--raw', *tls,
                                          'docker://' + destination + '@' + sha], timeout=30)
        if actual != raw: raise ValueError('registry read-back changed the image manifest')
    return config['pull_repository'] + '@' + sha


def collect(state, manifest, config):
    state = Path(state)
    root = state / 'infrastructure' / manifest['sources']['gcoms']['commit']
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
        image = publish(root, config, 'source-' + manifest['sources']['gcoms']['commit'])
        atomic_json(ready, {**original, 'qualified': True, 'images': {'services': image},
                           'qualification_sha256': digest(root / 'qualification.json')})
    value = json.loads(ready.read_text())
    if value.get('gcoms_source') != manifest['sources']['gcoms'] or value.get('qualified') is not True:
        raise ValueError('retained bundle has the wrong qualification identity')
    if digest(root / 'qualification.json') != value['qualification_sha256']:
        raise ValueError('retained qualification changed')
    for name, expected in value['sha256'].items():
        if digest(root / name) != expected: raise ValueError('retained infrastructure artifact changed')
    image = publish(root, config, 'source-' + manifest['sources']['gcoms']['commit'])
    if value['images']['services'] != image:
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
