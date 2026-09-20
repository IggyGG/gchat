#!/usr/bin/env python3
"""Create Gh0st preview signers in a NEW private directory outside repositories.

Private keys and randomly generated passwords stay in that directory. Only
public certificates, public OpenPGP key and fingerprints may be committed.
This does not enroll with a CA, install trust roots, or upload CI secrets.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess


def run(command, **kwargs):
    result = subprocess.run(command, capture_output=True, **kwargs)
    if result.returncode:
        raise RuntimeError(f"{Path(command[0]).name} failed; private signer directory retained")
    return result.stdout


def create(root, resume=False):
    root = root.expanduser().resolve()
    # This command handles secrets: refuse any directory inside a Git tree.
    if any((parent / '.git').exists() for parent in (root, *root.parents)):
        raise ValueError('signer directory must be outside Git repositories')
    root.mkdir(mode=0o700, parents=True, exist_ok=resume)
    os.chmod(root, 0o700)
    public = root / 'public'
    public.mkdir(mode=0o700, exist_ok=resume)
    identities = {}
    for platform in ('windows', 'macos'):
        password = root / f'{platform}.password'
        if not password.exists():
            password.write_text(secrets.token_urlsafe(48) + '\n')
        password.chmod(0o600)
        key, cert = root / f'{platform}.key.pem', public / f'{platform}.cert.pem'
        if not key.exists() and not cert.exists():
            run(['openssl', 'req', '-x509', '-newkey', 'rsa:3072', '-sha256', '-days', '730',
                 '-subj', '/CN=Gh0st', '-addext', 'basicConstraints=critical,CA:FALSE',
                 '-addext', 'keyUsage=critical,digitalSignature',
                 '-addext', 'extendedKeyUsage=codeSigning',
                 '-keyout', str(key), '-out', str(cert), '-passout', f'file:{password}'])
        if not key.is_file() or not cert.is_file():
            raise ValueError('incomplete key/certificate pair; preserve and inspect before resuming')
        key.chmod(0o600)
        run(['openssl', 'pkcs12', '-export', '-inkey', str(key), '-in', str(cert),
             '-name', 'Gh0st', '-passin', f'file:{password}', '-passout', 'stdin',
             '-out', str(root / f'{platform}.p12')], input=password.read_bytes())
        (root / f'{platform}.p12').chmod(0o600)
        der = run(['openssl', 'x509', '-in', str(cert), '-outform', 'DER'])
        # Native Windows and macOS identity selectors accept SHA-1 thumbprints;
        # retain SHA-256 as an additional public certificate content identifier.
        identities[platform] = {'name': 'Gh0st', 'certificate_fingerprint': hashlib.sha1(der).hexdigest().upper(),
                                'certificate_sha256': hashlib.sha256(der).hexdigest()}
    home = root / 'gnupg'
    home.mkdir(mode=0o700, exist_ok=resume)
    password = root / 'linux.password'
    if not password.exists():
        password.write_text(secrets.token_urlsafe(48) + '\n')
    password.chmod(0o600)
    command = ['gpg', '--homedir', str(home), '--batch', '--pinentry-mode', 'loopback', '--passphrase-file', str(password)]
    listing = run(command + ['--with-colons', '--list-secret-keys']).decode()
    if not any(row.startswith('sec:') for row in listing.splitlines()):
        run(command + ['--quick-generate-key', 'Gh0st (GChat preview releases)', 'ed25519', 'sign', '2y'])
        listing = run(command + ['--with-colons', '--list-secret-keys']).decode()
    fingerprint = next(row.split(':')[9] for row in listing.splitlines() if row.startswith('fpr:'))
    (public / 'linux-release.asc').write_bytes(run(command + ['--armor', '--export', fingerprint]))
    identities['linux'] = {'name': 'Gh0st', 'certificate_fingerprint': fingerprint}
    (public / 'identities.json').write_text(json.dumps(identities, indent=2) + '\n')
    # A local known-answer signing check exercises the encrypted key and pin.
    probe = root / 'verification-probe.txt'
    probe.write_text('Gh0st preview signer verification\n')
    run(command + ['--yes', '--local-user', fingerprint, '--armor', '--detach-sign', str(probe)])
    run(['gpg', '--homedir', str(home), '--batch', '--verify', str(probe)+'.asc', str(probe)])
    return identities


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-directory', type=Path, required=True)
    parser.add_argument('--resume', action='store_true', help='finish this previously created private directory without rotating its keys')
    args = parser.parse_args()
    os.umask(0o077)
    print(json.dumps(create(args.private_directory, args.resume), indent=2))


if __name__ == '__main__':
    main()
