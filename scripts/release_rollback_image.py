"""Retain the actual previous image before changing a Kubernetes workload."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

from release_coordinator import atomic_json


def address(image, target):
    if not re.fullmatch(r'[^\s]+@sha256:[0-9a-f]{64}', image):
        raise ValueError('rollback requires a digest-pinned previous image')
    if image.startswith('127.0.0.1:30444/'):
        return target['rollback_registry'] + '/' + image.split('/', 1)[1], False
    return image, True


def retain(image, target):
    source, tls = address(image, target)
    expected = image.rsplit('@', 1)[1]
    root = Path(target['rollback_image_root']) / expected.split(':', 1)[1]
    oci = root / 'oci'; root.mkdir(parents=True, exist_ok=True)
    if not (oci / 'index.json').is_file():
        subprocess.run(['skopeo', 'copy', '--preserve-digests',
            *([] if tls else ['--src-tls-verify=false']), 'docker://' + source,
            'oci:' + str(oci) + ':rollback'], check=True, timeout=300, stdout=subprocess.DEVNULL)
    raw = subprocess.check_output(['skopeo', 'inspect', '--raw', 'oci:' + str(oci) + ':rollback'], timeout=30)
    if 'sha256:' + hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('retained rollback image differs from the running digest')
    atomic_json(root / 'retained.json', {'schema': 1, 'image': image, 'manifest_sha256': expected})
    return root


def repair(image, target):
    destination, tls = address(image, target)
    root = Path(target['rollback_image_root']) / image.rsplit(':', 1)[1]
    if not (root / 'retained.json').is_file():
        raise ValueError('rollback image was not retained before activation')
    proof = json.loads((root / 'retained.json').read_text())
    raw = subprocess.check_output(['skopeo', 'inspect', '--raw', 'oci:' + str(root / 'oci') + ':rollback'], timeout=30)
    expected = image.rsplit('@', 1)[1]
    if proof['manifest_sha256'] != expected or 'sha256:' + hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('rollback image changed on retained storage')
    subprocess.run(['skopeo', 'copy', '--preserve-digests',
        *([] if tls else ['--dest-tls-verify=false']), 'oci:' + str(root / 'oci') + ':rollback',
        'docker://' + destination], check=True, timeout=300, stdout=subprocess.DEVNULL)
