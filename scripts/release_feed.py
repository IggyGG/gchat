#!/usr/bin/env python3
"""Publish immutable, signed desktop update feeds after candidate qualification.

The signed binding covers release identity, version, architecture, size and hash.
A feed pointer may advance only to a strictly newer semantic version. Same-version
replacement is forbidden, including after a partial publication or restart.
"""
import argparse
import base64
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit

from release_pair import canonical, validate
from release_coordinator import atomic_json, read_receipt

TARGETS = {'linux-x86_64': ('linux', 'x86_64'), 'macos-aarch64': ('darwin', 'aarch64'),
           'macos-x86_64': ('darwin', 'x86_64'), 'windows-x86_64': ('windows', 'x86_64')}


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', value):
        raise ValueError('production updates require a stable semantic version')
    return tuple(map(int, value.split('.')))


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def minisign_verify(path, signature, public_key):
    # Use the audited minisign implementation, not a second cryptographic parser.
    public = base64.b64decode(public_key, validate=True).decode().splitlines()
    if len(public) != 2 or not public[0].startswith('untrusted comment:'):
        raise ValueError('invalid configured updater public key')
    with tempfile.TemporaryDirectory(prefix='gchat-update-verify-') as work:
        signature_path = Path(work) / 'signature'
        signature_path.write_bytes(base64.b64decode(signature.strip(), validate=True))
        subprocess.run(['minisign', '-Vm', str(path), '-P', public[1], '-x', str(signature_path)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def publish(manifest, platform, artifact, signature, root, url, public_key, signer, receipt, compatibility):
    validate(manifest)
    os_name, arch = TARGETS[platform]
    release = manifest['release_id']
    number = manifest['versions'][platform]
    version(number)
    report, _ = read_receipt(receipt, manifest, platform, 'verify')
    compatible, _ = read_receipt(compatibility, manifest, platform, 'compatibility')
    if compatible.get('relay_compatible') is not True: raise ValueError('relay compatibility not established')
    artifact = Path(artifact).resolve()
    sha = digest(artifact)
    # A passed receipt for some other file is not publication authorization.
    if not any(item['sha256'] == sha for item in report['evidence']):
        raise ValueError('artifact is not covered by the verified candidate receipt')
    size = artifact.stat().st_size
    if not 0 < size <= 512 * 1024 * 1024:
        raise ValueError('update artifact exceeds the client size limit')
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('update base must be a credential-free HTTPS URL')
    minisign_verify(artifact, signature, public_key)
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.publish.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        target = root / 'desktop' / os_name / arch
        target.mkdir(parents=True, exist_ok=True)
        destination = root / 'artifacts' / release / f'{sha}{"".join(artifact.suffixes)}'
        latest = target / 'latest.json'
        if latest.exists():
            old = json.loads(latest.read_text())
            old_binding = json.loads(old['binding'])
            if version(old['version']) >= version(number):
                if (old['version'], old_binding['release_id'], old_binding['sha256']) == (number, release, sha):
                    if not destination.is_file() or digest(destination) != sha:
                        raise ValueError('published immutable artifact is missing or changed')
                    return old  # crash after replace; immutable success
                raise ValueError('cannot replace or regress a published version')
        destination = root / 'artifacts' / release / f'{sha}{"".join(artifact.suffixes)}'
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if digest(destination) != sha:
                raise ValueError('immutable artifact changed')
        else:
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
                temporary = Path(stream.name)
                try:
                    with artifact.open('rb') as source:
                        shutil.copyfileobj(source, stream)
                    stream.flush(); os.fsync(stream.fileno())
                    if digest(temporary) != sha:
                        raise ValueError('artifact changed during publication')
                    os.chmod(temporary, 0o644)
                    os.replace(temporary, destination)
                finally:
                    temporary.unlink(missing_ok=True)
        binding = canonical({'schema': 1, 'release_id': release, 'version': number,
                             'target': os_name + '-' + arch, 'sha256': sha, 'size': size})
        # The signer receives only a file path. Keys remain in its protected
        # environment; no key text or passphrase enters argv, receipts or feeds.
        with tempfile.TemporaryDirectory(dir=root, prefix='.binding-') as work:
            path = Path(work) / 'binding.json'
            path.write_bytes(binding)
            subprocess.run([*signer, str(path)], check=True, stdout=subprocess.DEVNULL)
            binding_signature = path.with_suffix('.json.sig').read_text().strip()
            minisign_verify(path, binding_signature, public_key)
        feed = {'version': number, 'notes': 'GChat production update. See the release notes for changes and remaining privacy improvements.',
                'pub_date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'url': url.rstrip('/') + '/' + destination.relative_to(root).as_posix(),
                'signature': signature.strip(), 'binding': binding.decode(), 'binding_signature': binding_signature}
        atomic_json(latest, feed)
        os.chmod(latest, 0o644)
        descriptor = os.open(target, os.O_RDONLY)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
        return feed


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('manifest', 'artifact', 'signature', 'receipt', 'compatibility', 'root', 'config'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--platform', choices=TARGETS, required=True)
    a = p.parse_args(); config = json.loads(a.config.read_text())
    publish(json.loads(a.manifest.read_text()), a.platform, a.artifact, a.signature.read_text(),
            a.root, config['public_url'], config['public_key'], config['signer'], a.receipt, a.compatibility)
    print('Verified desktop update published')


if __name__ == '__main__': main()
