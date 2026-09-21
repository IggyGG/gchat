"""Validate one independently qualified application bundle; no publication.

Checks are source/artifact-bound runner attestations, not proof of execution.
Original native reports and logs remain retained under their original hashes.
This schema does not qualify or republish the companion SDK packages.
"""
import hashlib
import json
from pathlib import PurePosixPath
import re
import subprocess

from release_evidence import bindings, file_reference, read_json, require, validate_sources
from release_signatures import fingerprint, verify
from paired_sources import verify_native_ci_inputs

FORMATS = {'macos-aarch64': 'dmg', 'macos-x86_64': 'dmg',
           'windows-x86_64': 'nsis', 'android-arm64': 'apk', 'android-x86_64': 'apk'}
SUFFIXES = {'dmg': '.dmg', 'nsis': '.exe', 'apk': '.apk'}


def asset_name(name):
    require(isinstance(name, str) and name not in ('.', '..') and
            re.fullmatch(r'[A-Za-z0-9_.+-]+', name), 'unsafe public asset name')
    return name



def controller_publication(candidate, base, original, repository):
    """Resolve an explicit Mac re-signing policy from committed Git objects."""
    policy = candidate['signer_policy']
    require(candidate['target'].startswith('macos-') and
            policy.get('kind') == 'macos-developer-id-controller', 'unsupported separate signer policy')
    require(repository is not None, 'signer policy requires the committed GChat repository')
    controller = policy.get('controller', {})
    commit, tree = controller.get('commit'), controller.get('tree')
    require(isinstance(commit, str) and re.fullmatch('[0-9a-f]{40}', commit) and
            isinstance(tree, str) and re.fullmatch('[0-9a-f]{40}', tree), 'invalid signer controller identity')

    def git(*args):
        return subprocess.check_output(['git', *args], cwd=repository)

    require(git('rev-parse', commit + '^{tree}').decode().strip() == tree, 'signer controller tree mismatch')
    source = candidate['sources']['gchat']['commit']
    require(json.loads(git('show', source + ':release/publication.json')) == original,
            'original publication is not the application source policy')
    # Architecture release branches may diverge. Bind the original bytes rather
    # than requiring the separate signing controller to descend from both.
    application = candidate['sources']['gchat']
    require(git('rev-parse', source + '^{tree}').decode().strip() == application['tree'],
            'original application tree mismatch')
    require(hashlib.sha256(git('archive', '--format=tar', source)).hexdigest() == application['archive']['sha256'],
            'original application archive differs from committed source')
    archive = file_reference(base, controller.get('archive'))
    require(hashlib.sha256(git('archive', '--format=tar', commit)).hexdigest() == controller['archive']['sha256'],
            'signer controller archive differs from committed source')
    publication = file_reference(base, policy.get('publication'))
    require(publication.read_bytes() == git('show', commit + ':release/publication.json'),
            'signer policy differs from committed publication')
    current = read_json(publication)
    require(current.get('project') == 'gchat' and current.get('version') == candidate['version'] and
            current.get('publication_status') == 'approved_by_owner', 'unapproved signer controller publication')
    require(fingerprint(current['publisher_identities']['linux']['certificate_fingerprint']) ==
            fingerprint(original['publisher_identities']['linux']['certificate_fingerprint']),
            'controller cannot replace the original detached release key')
    publisher = current['publisher_identities']['macos']
    require(publisher.get('distribution') == 'developer-id' and
            publisher.get('signing_policy') == 'publicly-trusted' and
            re.fullmatch('[A-Z0-9]{10}', publisher.get('team_id', '')) and
            re.fullmatch('[0-9a-f]{64}', publisher.get('certificate_sha256', '')),
            'separate Mac policy requires a pinned Developer ID identity')
    previous = policy.get('replaces')
    prefix = 'v' + candidate['version'] + '-' + candidate['target'] + '.'
    require(isinstance(previous, str) and re.fullmatch(re.escape(prefix) + '[1-9][0-9]*', previous)
            and int(candidate['tag'].removeprefix(prefix)) > int(previous.removeprefix(prefix)),
            'notarized replacement requires a distinct later platform tag')
    return current


def validate_notarization(candidate, base, publisher, artifact_hashes):
    policy = candidate['signer_policy']
    proof_path = file_reference(base, policy.get('qualification'))
    proof = read_json(proof_path)
    root = proof_path.parent
    require(proof.get('schema') == 1 and proof.get('scope') == 'retained_macos_developer_id_notarization'
            and proof.get('passed') is True and proof.get('recompiled') is False
            and proof.get('resigned') is True and proof.get('native_tests_rerun') is False,
            'incomplete retained Mac notarization proof')
    require(proof.get('sources') == bindings(candidate) and proof.get('target') == candidate['target'],
            'notarization proof changed the original application identity')
    require({key: proof.get('controller', {}).get(key) for key in ('commit', 'tree')} ==
            {key: policy['controller'][key] for key in ('commit', 'tree')}, 'notarization controller mismatch')
    for key, expected in (('controller_archive', policy['controller']['archive']), ('publication', policy['publication'])):
        file_reference(root, proof.get(key))
        require(proof[key]['sha256'] == expected['sha256'], 'notarization policy/archive mismatch')
    require(proof.get('publisher') == publisher, 'notarization proof has wrong Developer ID publisher')
    original = proof.get('original', {})
    old_build = read_json(file_reference(root, original.get('build')))
    old_smoke = read_json(file_reference(root, original.get('application_smoke')))
    old_dmg = file_reference(root, original.get('dmg'))
    native = original.get('native_ci', {})
    native_path = file_reference(root, original.get('native_receipt'))
    require(old_build.get('target') == candidate['target']
            and old_build.get('dependency_inputs', {}).get('sources') == bindings(candidate)
            and verify_native_ci_inputs(native_path, old_build['dependency_inputs']) == native
            and old_build.get('native_ci') == native, 'notarization lost the original native qualification')
    require(old_smoke.get('scope') == 'macos_dmg_private_copy_install_service_lifecycle'
            and old_smoke.get('target') == candidate['target']
            and old_smoke.get('passed') is True and old_smoke.get('sources') == bindings(candidate)
            and old_smoke.get('inputs', {}).get('dmg', {}).get('sha256') == original['dmg']['sha256'],
            'original application smoke does not bind the retained DMG')
    identity = proof.get('code_identity', {})
    require(identity.get('method') == 'codesign_remove_signature_on_private_copies'
            and identity.get('unchanged') is True and isinstance(identity.get('before'), dict)
            and identity['before'] and identity['before'] == identity.get('after'),
            're-signing changed normalized executable/resources')
    for name, item in identity['before'].items():
        require(isinstance(name, str) and not PurePosixPath(name).is_absolute()
                and '..' not in PurePosixPath(name).parts and isinstance(item, dict),
                'invalid normalized bundle identity')
        require(item.get('kind') in ('file', 'macho', 'symlink'), 'unknown normalized bundle entry')
        if item['kind'] == 'symlink':
            require(isinstance(item.get('target'), str) and item['target'], 'missing normalized symlink target')
        else:
            require(re.fullmatch('[0-9a-f]{64}', item.get('sha256', ''))
                    and type(item.get('executable')) is bool, 'invalid normalized code/resource hash')
    require(any(item['kind'] == 'macho' for item in identity['before'].values()), 'normalized bundle has no executable code')
    dmg = file_reference(root, proof.get('dmg'))
    require(set(artifact_hashes.values()) == {proof['dmg']['sha256']}
            and proof['dmg']['sha256'] != original['dmg']['sha256'], 'replacement DMG binding mismatch')
    build = read_json(file_reference(root, proof.get('build')))
    smoke = read_json(file_reference(root, proof.get('application_smoke')))
    require(build.get('target') == candidate['target'] and build.get('native_ci') == native
            and build.get('publisher') == publisher and build.get('apple_notarization') is True
            and build.get('signing_policy') == 'publicly-trusted'
            and build.get('dependency_inputs', {}).get('sources') == bindings(candidate)
            and any(item.get('sha256') == proof['dmg']['sha256'] for item in build.get('files', [])),
            'replacement manifest changed native identity, publisher or DMG')
    require(smoke.get('scope') == 'macos_dmg_private_copy_install_service_lifecycle'
            and smoke.get('target') == candidate['target'] and smoke.get('gui_startup_passed') is True
            and smoke.get('passed') is True and smoke.get('inputs_unchanged') is True
            and smoke.get('sources') == bindings(candidate)
            and smoke.get('inputs', {}).get('dmg', {}).get('sha256') == proof['dmg']['sha256']
            and all(smoke.get('cleanup', {}).get(key) is True for key in
                    ('passed', 'detached', 'installation_removed', 'service_children_stopped')),
            'replacement application smoke or cleanup incomplete')
    notarization = proof.get('notarization', {})
    info = read_json(file_reference(root, notarization.get('info')))
    log = read_json(file_reference(root, notarization.get('log')))
    require(notarization.get('status') == 'Accepted' and info.get('status') == 'Accepted'
            and info.get('id') == notarization.get('id') and log.get('status') == 'Accepted'
            and log.get('jobId') == notarization.get('id')
            and log.get('sha256') == notarization.get('submission_dmg_sha256')
            and re.fullmatch('[0-9a-f]{64}', notarization.get('submission_dmg_sha256', '')),
            'Apple notarization was not accepted for the bound submission')
    require(proof.get('stapling', {}).get('dmg_validated') is True and proof.get('cleanup_complete') is True,
            'DMG stapling or cleanup incomplete')
    gatekeeper = proof.get('gatekeeper', {})
    require(all(gatekeeper.get(key) is True for key in ('quarantine_applied', 'dmg_assessment_passed',
            'app_assessment_passed', 'app_notarization_requirement_passed', 'cleanup_complete', 'assessment_policy_enabled')),
            'quarantined Gatekeeper assessment incomplete')
    for role in ('stapling', 'gatekeeper'):
        evidence = proof[role].get('evidence')
        require(isinstance(evidence, list) and evidence, 'retain native ' + role + ' command evidence')
        for item in evidence:
            file_reference(root, item)
    return proof


def validate(candidate, base, publication, signature_home=None, controller_repository=None):
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
    effective = (controller_publication(candidate, base, publication, controller_repository)
                 if 'signer_policy' in candidate else publication)
    publisher = effective['publisher_identities'][platform]
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
    if 'signer_policy' in candidate:
        validate_notarization(candidate, base, publisher, artifact_hashes)
    return candidate


def public_manifest(candidate, base):
    """Publish hashes and scope, never private worker paths or full raw logs."""
    manifest = {key: candidate[key] for key in ('schema', 'kind', 'version', 'tag', 'target', 'channel',
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
    if 'signer_policy' in candidate:
        policy = candidate['signer_policy']
        manifest['signer_policy'] = {'kind': policy['kind'], 'replaces': policy['replaces'],
            'controller': {key: policy['controller'][key] for key in ('commit', 'tree')},
            'controller_archive_sha256': policy['controller']['archive']['sha256'],
            'publication_sha256': policy['publication']['sha256'],
            'qualification_sha256': policy['qualification']['sha256']}
    return manifest


def immutable_assets(release, expected, hash_existing):
    """Published assets form a closed set; even adding different names is refused."""
    existing = {asset['name']: asset for asset in release.get('assets', [])}
    require(set(existing) <= set(expected), 'release contains assets outside the frozen bundle')
    if not release['draft']:
        require(set(existing) == set(expected), 'cannot add assets to a published platform release')
    for name, item in existing.items():
        require(hash_existing(item) == expected[name], 'refusing to replace published platform bytes')
    return set(expected) - set(existing)
