"""Verify OpenPGP signatures against the configured primary release key."""
import re
import subprocess


def fingerprint(value):
    value = value.replace(' ', '').upper() if isinstance(value, str) else ''
    if not re.fullmatch(r'(?:[A-F0-9]{40}|[A-F0-9]{64})', value):
        raise ValueError('configure the full primary release key fingerprint')
    return value


def check_status(result, expected):
    expected = fingerprint(expected)
    records = [line.split()[1:] for line in result.stdout.splitlines() if line.startswith('[GNUPG:] ')]
    bad = {'BADSIG', 'ERRSIG', 'EXPSIG', 'EXPKEYSIG', 'REVKEYSIG', 'KEYREVOKED', 'KEYEXPIRED', 'SIGEXPIRED'}
    valid = [fields for fields in records if fields and fields[0] == 'VALIDSIG']
    # VALIDSIG ends with the primary fingerprint even when a signing subkey is used.
    if result.returncode or any(fields[0] in bad for fields in records) or len(valid) != 1 or valid[0][-1].upper() != expected:
        raise ValueError('signature is not valid under the configured release key')


def verify(signature, artifact, expected, home=None):
    command = ['gpg'] + (['--homedir', str(home)] if home else [])
    result = subprocess.run(command + ['--batch', '--no-auto-key-retrieve', '--status-fd=1', '--verify', str(signature), str(artifact)], capture_output=True, text=True)
    check_status(result, expected)


def verify_tag(root, tag, expected):
    result = subprocess.run(['git', 'verify-tag', '--raw', tag], cwd=root, capture_output=True, text=True)
    result.stdout = result.stderr  # git routes GnuPG's machine-readable status here.
    check_status(result, expected)
