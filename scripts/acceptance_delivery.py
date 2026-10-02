"""Runner-owned encrypted delivery of retained acceptance archives and grants."""
import argparse
import base64
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from release_pair import canonical
from release_coordinator import atomic_json

PROTOCOL = 'gchat-acceptance-delivery-1'
CHUNK = 4 * 1024**2
MAXIMUM = 12 * 1024**3


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def archive_bound(bound):
    size = bound.get('size')
    if (type(size) is not int or not 0 < size <= MAXIMUM
            or not re.fullmatch('[0-9a-f]{64}', bound.get('sha256', ''))
            or bound.get('ciphertext_size') != size + 16 * ((size + CHUNK - 1) // CHUNK)
            or not re.fullmatch('[0-9a-f]{64}', bound.get('ciphertext_sha256', ''))):
        raise ValueError('invalid bound acceptance archive')
    decode(bound['nonce'], 8)
    return bound


def encode(value):
    return base64.urlsafe_b64encode(value).decode().rstrip('=')


def decode(value, size):
    if not isinstance(value, str) or len(value) > 128:
        raise ValueError('invalid delivery key encoding')
    raw = base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))
    if len(raw) != size or encode(raw) != value:
        raise ValueError('invalid delivery key length or encoding')
    return raw


def key(private, public, request, purpose):
    if not re.fullmatch('[0-9a-f]{64}', request):
        raise ValueError('invalid acceptance request')
    shared = private.exchange(X25519PublicKey.from_public_bytes(decode(public, 32)))
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=bytes.fromhex(request),
                info=(PROTOCOL + '/' + purpose).encode()).derive(shared)


def public(private):
    return encode(private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw))


def context(request, purpose, size, sha, index):
    return canonical([PROTOCOL, request, purpose, size, sha, index])


def encrypt_archive(source, destination, secret, request, purpose, expected):
    source, destination = Path(source), Path(destination)
    if source.is_symlink() or not 0 < source.stat().st_size <= MAXIMUM:
        raise ValueError('invalid original delivery archive')
    size = source.stat().st_size
    nonce = os.urandom(8)
    actual = hashlib.sha256(); cipher = AESGCM(secret)
    with source.open('rb') as origin, destination.open('xb') as output:
        index = 0
        while data := origin.read(CHUNK):
            actual.update(data)
            output.write(cipher.encrypt(nonce + struct.pack('>I', index), data,
                         context(request, purpose, size, expected, index)))
            index += 1
        output.flush(); os.fsync(output.fileno())
    if actual.hexdigest() != expected or source.stat().st_size != size:
        destination.unlink(missing_ok=True)
        raise ValueError('original archive changed during encrypted delivery')
    return {'nonce': encode(nonce), 'size': size, 'sha256': expected,
            'ciphertext_size': destination.stat().st_size,
            'ciphertext_sha256': digest(destination)}


def decrypt_archive(source, destination, secret, request, purpose, bound):
    archive_bound(bound)
    size, expected = bound['size'], bound['sha256']
    nonce = decode(bound['nonce'], 8); cipher = AESGCM(secret); actual = hashlib.sha256()
    source, destination = Path(source), Path(destination)
    if (source.stat().st_size != bound['ciphertext_size']
            or digest(source) != bound['ciphertext_sha256']):
        raise ValueError('encrypted acceptance archive changed')
    created = False
    try:
        with source.open('rb') as origin, destination.open('xb') as output:
            created = True
            remaining, index = size, 0
            while remaining:
                count = min(CHUNK, remaining)
                data = cipher.decrypt(nonce + struct.pack('>I', index), origin.read(count + 16),
                                      context(request, purpose, size, expected, index))
                if len(data) != count: raise ValueError('acceptance frame length differs')
                output.write(data); actual.update(data); remaining -= count; index += 1
            if origin.read(1) or actual.hexdigest() != expected:
                raise ValueError('decrypted original archive differs')
            output.flush(); os.fsync(output.fileno())
    except BaseException:
        if created: destination.unlink(missing_ok=True)
        raise


def seal(value, private, recipient, request):
    nonce = os.urandom(12)
    ciphertext = AESGCM(key(private, recipient, request, 'response')).encrypt(
        nonce, canonical(value), context(request, 'response', 0, '', 0))
    return {'schema': 1, 'protocol': PROTOCOL, 'request': request, 'public_key': public(private),
            'nonce': encode(nonce), 'ciphertext': encode(ciphertext)}


def unseal(value, private, request):
    if (value.get('schema') != 1 or value.get('protocol') != PROTOCOL or value.get('request') != request
            or not isinstance(value.get('ciphertext'), str) or len(value['ciphertext']) > 262144):
        raise ValueError('acceptance response request or protocol differs')
    nonce = decode(value['nonce'], 12)
    raw = base64.urlsafe_b64decode(value['ciphertext'] + '=' * (-len(value['ciphertext']) % 4))
    if encode(raw) != value['ciphertext']: raise ValueError('invalid response encoding')
    return json.loads(AESGCM(key(private, value['public_key'], request, 'response')).decrypt(
        nonce, raw, context(request, 'response', 0, '', 0)))


def generate(directory, binding, output):
    if not re.fullmatch('[0-9a-f]{64}', binding.get('request', '')):
        raise ValueError('invalid ready acceptance request')
    directory = Path(directory); directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    private = X25519PrivateKey.generate()
    path = directory / 'key'; path.write_bytes(private.private_bytes(
        serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())); path.chmod(0o600)
    ready = canonical({**binding, 'schema': 1, 'protocol': PROTOCOL,
        'public_key': public(private), 'created_at': int(time.time())})
    (directory / 'ready.json').write_bytes(ready)
    Path(output).write_bytes(ready)


def delivery_url(base, request, name):
    parsed = urllib.parse.urlsplit(base)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or not re.fullmatch('[0-9a-f]{64}', request)
            or name not in ('response.json', 'current.sealed', 'baseline.sealed', 'peer.sealed')):
        raise ValueError('invalid encrypted delivery URL')
    return base.rstrip('/') + '/' + request + '/' + name


def fetch(url, maximum):
    with urllib.request.urlopen(url, timeout=60) as response:
        if response.url != url: raise ValueError('acceptance delivery redirect refused')
        data = response.read(maximum + 1)
        if len(data) > maximum: raise ValueError('acceptance delivery exceeds its bound')
        return data


def copy_retained(spec, destination):
    """Return only hash-verified copies explicitly delivered to this runner."""
    root = os.environ.get('GCHAT_ACCEPTANCE_RETAINED_ROOT')
    if not root: return None
    root = Path(root); source = root / (spec['archive'] + '.zip')
    metadata = json.loads((root / (spec['archive'] + '.json')).read_text())
    if (source.is_symlink() or not source.is_file() or metadata.get('id') != spec['artifact']
            or metadata.get('workflow_run', {}).get('id') != spec['run']
            or metadata.get('digest') != 'sha256:' + spec['archive']
            or source.stat().st_size != metadata.get('size_in_bytes')
            or metadata.get('retained_locally') is not True
            or digest(source) != spec['archive']):
        raise ValueError('retained acceptance copy differs from frozen provider identity')
    try: os.link(source, destination)
    except OSError as error:
        if error.errno != errno.EXDEV: raise
        with source.open('rb') as origin, Path(destination).open('xb') as output:
            shutil.copyfileobj(origin, output)
    return metadata


def receive(base, request, directory, specs, manifest, driver, output):
    directory = Path(directory)
    if (directory.is_symlink() or not directory.is_dir() or (directory / 'key').is_symlink()
            or json.loads((directory / 'ready.json').read_text()).get('request') != request):
        raise ValueError('private delivery directory is not owned by this request')
    ready = json.loads((directory / 'ready.json').read_text())
    completed, response_sha, recovered = False, None, {}
    try:
        private = X25519PrivateKey.from_private_bytes((directory / 'key').read_bytes())
        deadline = time.monotonic() + 1200
        while True:
            try:
                sealed = json.loads(fetch(delivery_url(base, request, 'response.json'), 262144)); break
            except urllib.error.HTTPError as error:
                if error.code != 404 or time.monotonic() >= deadline: raise
                time.sleep(5)
        value = unseal(sealed, private, request)
        response_sha = hashlib.sha256(canonical(sealed)).hexdigest()
        if (value.get('request') != request or value.get('inputs') != specs
                or value.get('sources') != manifest['sources'] or value.get('target') != specs['target']
                or type(value.get('expires_at')) is not int or value['expires_at'] <= time.time()
                or not isinstance(value.get('invitation'), str) or not 0 < len(value['invitation'].encode()) <= 48000):
            raise ValueError('delivered acceptance authority differs')
        archives = directory / 'archives'; archives.mkdir()
        for role in ('current', 'baseline', 'peer'):
            if role not in specs: continue
            bound = archive_bound(value['archives'][role]); expected = specs[role]
            if bound['sha256'] != expected['archive']: raise ValueError('delivery selected a different archive')
            encrypted = directory / (role + '.sealed')
            url = delivery_url(base, request, role + '.sealed')
            with urllib.request.urlopen(url, timeout=600) as response, encrypted.open('xb') as stream:
                if response.url != url: raise ValueError('archive delivery redirect refused')
                total = 0
                while data := response.read(CHUNK):
                    total += len(data)
                    if total > bound['ciphertext_size']: raise ValueError('encrypted archive exceeds its bound')
                    stream.write(data)
            destination = archives / (expected['archive'] + '.zip')
            decrypt_archive(encrypted, destination, key(private, sealed['public_key'], request, role),
                            request, role, bound)
            (archives / (expected['archive'] + '.json')).write_bytes(canonical(bound['provider']))
            encrypted.unlink()
            recovered[role] = bound['sha256']
        environment = dict(os.environ, GCHAT_NETWORK_INVITATION=value['invitation'],
                           GCHAT_ACCEPTANCE_RETAINED_ROOT=str(archives.resolve()))
        result = subprocess.run([sys.executable, str(driver), '--inputs', 'acceptance-inputs.json',
            '--manifest', 'acceptance-manifest.json', '--output', str(output)], env=environment).returncode
        completed = result == 0
        return result
    finally:
        # Only this runner's temporary transport key and decrypted copies.
        shutil.rmtree(directory)
        atomic_json(Path(output) / 'delivery.json', {'schema': 1, 'protocol': PROTOCOL,
            'request': request, 'sources': manifest['sources'], 'target': specs['target'],
            'qualification_commit': ready['commit'], 'qualification_tree': ready['tree'],
            'passed': completed, 'response_sha256': response_sha, 'archives': recovered,
            'private_key_removed': not directory.exists(), 'decrypted_archives_removed': not directory.exists()})


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('action', choices=('ready', 'run'))
    parser.add_argument('--private', type=Path, required=True); parser.add_argument('--request', required=True)
    parser.add_argument('--url'); parser.add_argument('--driver', type=Path); parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.action == 'ready':
        binding = json.loads(Path('acceptance-worker.json').read_text())
        if binding['request'] != args.request: raise ValueError('ready binding differs')
        generate(args.private, binding, Path('acceptance-ready.json'))
    else:
        raise SystemExit(receive(args.url, args.request, args.private,
            json.loads(Path('acceptance-inputs.json').read_text()),
            json.loads(Path('acceptance-manifest.json').read_text()), args.driver, args.output))


if __name__ == '__main__': main()
