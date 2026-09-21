"""Validate one independently qualified application bundle; no publication.

Checks are source/artifact-bound runner attestations, not proof of execution.
Original native reports and logs remain retained under their original hashes.
This schema does not qualify or republish the companion SDK packages.
"""
import re

from release_evidence import bindings, file_reference, read_json, require, validate_sources
from release_signatures import fingerprint, verify

FORMATS = {'macos-aarch64': 'dmg', 'macos-x86_64': 'dmg',
           'windows-x86_64': 'nsis', 'android-arm64': 'apk', 'android-x86_64': 'apk'}
SUFFIXES = {'dmg': '.dmg', 'nsis': '.exe', 'apk': '.apk'}


def asset_name(name):
    require(isinstance(name, str) and name not in ('.', '..') and
            re.fullmatch(r'[A-Za-z0-9_.+-]+', name), 'unsafe public asset name')
    return name


def validate(candidate, base, publication, signature_home=None):
    require(candidate.get('schema') == 1 and candidate.get('kind') == 'platform-release', 'unsupported platform bundle')
    version, tag, target = candidate.get('version'), candidate.get('tag'), candidate.get('target')
    require(isinstance(version, str) and re.fullmatch(r'\d+\.\d+\.\d+', version), 'invalid app version')
    require(target in FORMATS, 'unsupported platform target')
    platform = target.split('-')[0]
    require(isinstance(tag, str) and re.fullmatch(re.escape('v' + version + '-' + target + '.') + r'[1-9][0-9]*', tag),
            'use a new immutable version-target.build tag')
    require(candidate.get('channel') == 'production' and candidate.get('release_policy') == 'production-minutes-v1',
            'platform bundle requires explicit production policy')
    require(candidate.get('privacy_qualified') is False and
            isinstance(candidate.get('unqualified_scopes'), list) and candidate['unqualified_scopes'] and
            all(isinstance(x, str) and x.strip() for x in candidate['unqualified_scopes']), 'disclose remaining qualification limits')
    require(publication.get('publication_status') == 'approved_by_owner' and publication.get('version') == version,
            'publication policy/version mismatch')
    validate_sources(candidate, base)
    pin = fingerprint(publication['publisher_identities']['linux']['certificate_fingerprint'])
    publisher = publication['publisher_identities'][platform]
    expected_signer = {'name': publisher['name'], 'certificate_sha256': publisher['certificate_sha256'].lower()}
    require(candidate.get('signer') == expected_signer, 'platform signer differs from frozen publisher')
    key = candidate.get('release_key', {})
    require(fingerprint(key.get('fingerprint')) == pin, 'wrong detached release signer')
    key_file = file_reference(base, key)
    require(key_file.read_bytes().lstrip().startswith(b'-----BEGIN PGP PUBLIC KEY BLOCK-----'),
            'publish only an armored public release key')
    verify(file_reference(base, key['signature']), key_file, pin, signature_home)
    artifacts = candidate.get('artifacts')
    require(isinstance(artifacts, dict) and len(artifacts) == 1, 'one independently checked installer per platform bundle')
    artifact_hashes = {}
    for name, item in artifacts.items():
        asset_name(name)
        require(item.get('target') == target and item.get('format') == FORMATS[target] and
                name.lower().endswith(SUFFIXES[FORMATS[target]]), 'artifact target/format mismatch')
        path = file_reference(base, item)
        require(type(item.get('size')) is int and item['size'] == path.stat().st_size > 0, 'artifact size mismatch')
        verify(file_reference(base, item['signature']), path, pin, signature_home)
        artifact_hashes[name] = item['sha256']
    checks = candidate.get('checks', {})
    require(set(checks) == {'build', 'smoke', 'signing'}, 'build, smoke and signing receipts required')
    for role, reference in checks.items():
        report = read_json(file_reference(base, reference))
        require(report.get('schema') == 1 and report.get('scope') == 'platform.' + role and
                report.get('passed') is True and report.get('source_unchanged') is True, 'incomplete ' + role + ' receipt')
        require(report.get('sources') == bindings(candidate), role + ' receipt has wrong source pair')
        require(report.get('target') == target and report.get('artifacts') == artifact_hashes,
                role + ' receipt has wrong artifact/target')
        require(isinstance(report.get('qualified_scopes'), list) and report['qualified_scopes'] and
                all(isinstance(x, str) and x.strip() for x in report['qualified_scopes']), 'name the actual checked scope')
        evidence = report.get('evidence')
        require(isinstance(evidence, list) and evidence, 'retain original ' + role + ' reports/logs')
        for linked in evidence:
            file_reference(base, linked)
        if role == 'signing':
            require(report.get('signer') == expected_signer, 'signing receipt has wrong publisher')
        if role == 'smoke':
            require(report.get('cleanup_complete') is True, 'installed/emulator cleanup incomplete')
    return candidate


def public_manifest(candidate, base):
    """Publish hashes and scope, never private worker paths or full raw logs."""
    return {key: candidate[key] for key in ('schema', 'kind', 'version', 'tag', 'target', 'channel',
            'release_policy', 'privacy_qualified', 'unqualified_scopes', 'signer')} | {
        'sources': {name: {'commit': source['commit'], 'tree': source['tree'],
                          'archive_sha256': source['archive']['sha256']}
                    for name, source in candidate['sources'].items()},
        'release_key': {'fingerprint': candidate['release_key']['fingerprint'], 'sha256': candidate['release_key']['sha256']},
        'artifacts': {name: {key: item[key] for key in ('sha256', 'size', 'format', 'target')}
                      for name, item in candidate['artifacts'].items()},
        'checks': {role: {'report_sha256': reference['sha256'],
                          'qualified_scopes': read_json(file_reference(base, reference))['qualified_scopes'],
                          'evidence_sha256': [item['sha256'] for item in read_json(file_reference(base, reference))['evidence']]}
                   for role, reference in candidate['checks'].items()}}


def immutable_assets(release, expected, hash_existing):
    """Published assets form a closed set; even adding different names is refused."""
    existing = {asset['name']: asset for asset in release.get('assets', [])}
    require(set(existing) <= set(expected), 'release contains assets outside the frozen bundle')
    if not release['draft']:
        require(set(existing) == set(expected), 'cannot add assets to a published platform release')
    for name, item in existing.items():
        require(hash_existing(item) == expected[name], 'refusing to replace published platform bytes')
    return set(expected) - set(existing)
