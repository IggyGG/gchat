"""Publish encrypted acceptance transport only to a verified running worker."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import zipfile

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

import acceptance_delivery as delivery
from release_coordinator import atomic_json
from release_feed import digest


def retain_original(state, spec, target, api):
    state = Path(state)
    for receipt in sorted((state / 'jobs').glob('*/receipt.json')):
        proof = json.loads(receipt.read_text())
        if (proof.get('stage') == 'build' and proof.get('passed') is True
                and str(proof.get('external_id')) == str(spec['run'])
                and proof.get('worker', {}).get('artifact_id') == spec['artifact']):
            references = [v for v in proof.get('evidence', []) if v.get('path') == 'native.zip']
            expected = {k: v.get('commit') for k, v in proof.get('sources', {}).items()}
            if (len(references) != 1 or references[0]['sha256'] != spec['archive']
                    or expected != spec['sources'] or proof['worker']['workflow_commit'] != spec['controller']):
                raise ValueError('retained acceptance build receipt differs')
            path = receipt.parent / 'native.zip'
            if path.is_symlink() or digest(path) != spec['archive']:
                raise ValueError('retained acceptance provider archive changed')
            return path
    root = state / 'native-baselines'; root.mkdir(exist_ok=True)
    path = root / (spec['archive'] + '.zip')
    if not path.exists():
        artifact = api(f'actions/artifacts/{spec["artifact"]}')
        if (artifact.get('digest') != 'sha256:' + spec['archive'] or artifact.get('expired') is not False
                or artifact.get('workflow_run', {}).get('id') != spec['run']
                or type(artifact.get('size_in_bytes')) is not int
                or not 0 < artifact['size_in_bytes'] <= delivery.MAXIMUM):
            raise ValueError('original acceptance archive is unavailable or differs')
        partial = path.with_suffix('.partial')
        with partial.open('wb') as stream:
            subprocess.run(['gh', 'api', f'repos/IggyGG/gchat/actions/artifacts/{spec["artifact"]}/zip'],
                           stdout=stream, stderr=subprocess.PIPE, check=True, timeout=600)
        if digest(partial) != spec['archive'] or partial.stat().st_size != artifact['size_in_bytes']:
            raise ValueError('original acceptance archive changed in transit')
        partial.replace(path)
    if path.is_symlink() or digest(path) != spec['archive']:
        raise ValueError('retained original acceptance archive differs')
    return path


def provider_metadata(path, spec, target):
    # The immutable operator/build-receipt hash is the authority after provider
    # download expiry. Native drivers still verify the original run and signing.
    with zipfile.ZipFile(path) as source:
        build = json.loads(source.read(spec['manifest']))
    if target in ('android', 'ios'):
        sources = {k: v.get('commit') for k, v in build.get('sources', {}).items()}
        if build.get('passed') is not True or build.get('sources_unchanged') is not True:
            raise ValueError('retained mobile archive has no successful original build')
        name = f'{target}-{spec["sources"]["gchat"]}-{spec["sources"]["gcoms"]}'
        if target == 'ios' and spec.get('recovery') is None: name += '-' + build['build_number']
    else:
        sources = build.get('sources'); name = target
        if build.get('target') != target: raise ValueError('retained desktop archive target differs')
    recovery = spec.get('recovery')
    if recovery is not None:
        if target == 'ios' and recovery.get('kind') == 'ios-retained':
            name = 'ios-verified-' + recovery['rule']['request']
        elif target.startswith('macos') and recovery.get('kind') == 'macos-package':
            name = target + '-package'
        else:
            raise ValueError('unknown retained acceptance recovery')
    if sources != spec['sources']: raise ValueError('retained acceptance archive source differs')
    return {'id': spec['artifact'], 'digest': 'sha256:' + spec['archive'], 'size_in_bytes': path.stat().st_size,
            'workflow_run': {'id': spec['run']}, 'name': name, 'retained_locally': True}


def prepare(state, intent, api):
    paths = {}
    for role in ('current', 'baseline', 'peer'):
        if role not in intent['inputs']: continue
        target = intent['inputs']['peer_target'] if role == 'peer' else intent['target']
        spec = intent['inputs'][role]
        path = retain_original(state, spec, target, api)
        metadata = provider_metadata(path, spec, target)
        paths[role] = {'path': str(path), 'provider': metadata}
    return paths


def ready(state, intent, work, run, api, issue, *, now=None):
    if run.get('status') != 'in_progress': return None
    actual_clock = now is None
    now = int(time.time()) if now is None else now
    request = intent['request']; work = Path(work)
    if not re.fullmatch('[0-9a-f]{64}', request):
        raise ValueError('invalid acceptance delivery request')
    marker = work / 'sealed-delivery.json'
    if marker.exists():
        proof = json.loads(marker.read_text())
        if (proof['request'] != request or proof['run'] != run['id']
                or proof['worker']['sources'] != intent['sources']
                or proof['worker']['commit'] != intent['qualification_commit']):
            raise ValueError('delivered acceptance worker changed')
        response = Path(state) / 'public/updates/acceptance' / request / 'response.json'
        retained = work / 'sealed-response.json'
        if digest(retained) != proof['response_sha256']:
            raise ValueError('retained encrypted response changed')
        if not response.exists():
            atomic_json(response, json.loads(retained.read_text())); response.chmod(0o644)
        if digest(response) != proof['response_sha256']:
            raise ValueError('published encrypted response changed')
        return proof
    artifacts = api(f'actions/runs/{run["id"]}/artifacts?per_page=100')['artifacts']
    selected = [a for a in artifacts if a['name'] == 'acceptance-ready-' + request and not a['expired']]
    if not selected: return None
    if len(selected) != 1: raise ValueError('acceptance ready artifact is ambiguous')
    artifact = selected[0]
    if (not re.fullmatch('sha256:[0-9a-f]{64}', artifact.get('digest', ''))
            or type(artifact.get('size_in_bytes')) is not int or not 0 < artifact['size_in_bytes'] <= 65536):
        raise ValueError('acceptance ready artifact identity is invalid')
    archive = work / 'ready.zip'
    if not archive.exists():
        with archive.open('xb') as stream:
            subprocess.run(['gh', 'api', f'repos/IggyGG/gchat/actions/artifacts/{artifact["id"]}/zip'],
                           stdout=stream, stderr=subprocess.PIPE, check=True, timeout=120)
    if 'sha256:' + digest(archive) != artifact['digest'] or archive.stat().st_size != artifact['size_in_bytes']:
        raise ValueError('acceptance ready artifact changed')
    with zipfile.ZipFile(archive) as source:
        if (source.namelist() != ['acceptance-ready.json']
                or not 0 < source.getinfo('acceptance-ready.json').file_size <= 16384):
            raise ValueError('acceptance ready artifact has unexpected members')
        binding = json.loads(source.read('acceptance-ready.json'))
    expected = {'schema': 1, 'protocol': delivery.PROTOCOL, 'request': request,
                'release_id': intent['release_id'], 'sources': intent['sources'], 'target': intent['target'],
                'commit': intent['qualification_commit'], 'tree': intent['qualification_tree']}
    if (any(binding.get(k) != v for k, v in expected.items())
            or type(binding.get('created_at')) is not int or not 0 <= now - binding['created_at'] <= 300):
        raise ValueError('acceptance ready source, request or freshness differs')
    private = X25519PrivateKey.generate()
    # Reject invalid/small-order recipient keys before any grant is issued.
    delivery.key(private, binding['public_key'], request, 'response')
    root = Path(state) / 'public/updates/acceptance' / request
    for relative in ('public', 'public/updates', 'public/updates/acceptance'):
        parent = Path(state) / relative
        if parent.is_symlink(): raise ValueError('acceptance delivery parent is a symlink')
        if not parent.exists():
            parent.mkdir(); parent.chmod(0o755)  # Public ciphertext, even under a private coordinator umask.
    root.parent.chmod(0o755)
    if root.exists():
        # Only an unfinished derived ciphertext publication for this request.
        if root.is_symlink(): raise ValueError('acceptance delivery path is a symlink')
        shutil.rmtree(root)
    root.mkdir(); root.chmod(0o755)
    archives = {}
    for role, retained in intent['delivery_archives'].items():
        spec = intent['inputs'][role]
        archives[role] = delivery.encrypt_archive(retained['path'], root / (role + '.sealed'),
            delivery.key(private, binding['public_key'], request, role), request, role, spec['archive'])
        archives[role]['provider'] = retained['provider']
        (root / (role + '.sealed')).chmod(0o644)
    issued = issue()  # Original host-owned one-hour authority, after the runner is ready.
    issued_at = int(time.time()) if actual_clock else now
    if (type(issued.get('expires_at')) is not int or not issued_at < issued['expires_at'] <= issued_at + 3600
            or not isinstance(issued.get('invitation'), str)
            or not 0 < len(issued['invitation'].encode()) <= 48000):
        raise ValueError('host-owned acceptance grant is invalid or expired')
    payload = {'request': request, 'sources': intent['sources'], 'target': intent['target'],
               'inputs': intent['inputs'], 'archives': archives, **issued}
    sealed = delivery.seal(payload, private, binding['public_key'], request)
    # Journal the exact sealed response before making it visible. A lost reply
    # republishes these same bytes; it cannot renew authority or re-key a download.
    response = work / 'sealed-response.json'; atomic_json(response, sealed)
    proof = {'schema': 1, 'request': request, 'run': run['id'], 'worker': expected,
             'ready_artifact_id': artifact['id'], 'ready_archive_sha256': digest(archive),
             'response_sha256': digest(response), 'archives': archives,
             'original_archives_retained': True, 'grant_issued_after_ready': True,
             'expires_at': issued['expires_at']}
    atomic_json(marker, proof)
    atomic_json(root / 'response.json', sealed); (root / 'response.json').chmod(0o644)
    return proof


def cleanup(state, request):
    if not re.fullmatch('[0-9a-f]{64}', request):
        raise ValueError('invalid acceptance cleanup request')
    root = Path(state) / 'public/updates/acceptance' / request
    if root.exists():
        if root.is_symlink(): raise ValueError('acceptance delivery path is a symlink')
        shutil.rmtree(root)  # Completed/revoked transport only; originals stay private.


def verify_receipt(proof, intent, work):
    retained = json.loads((Path(work) / 'sealed-delivery.json').read_text())
    expected = {'schema': 1, 'protocol': delivery.PROTOCOL, 'request': intent['request'],
                'sources': intent['sources'], 'target': intent['target'],
                'qualification_commit': intent['qualification_commit'],
                'qualification_tree': intent['qualification_tree'], 'passed': True,
                'response_sha256': retained['response_sha256'],
                'archives': {role: spec['archive'] for role, spec in intent['inputs'].items()
                             if role in ('current', 'baseline', 'peer')},
                'private_key_removed': True, 'decrypted_archives_removed': True,
                'derived_native_copies_removed': True}
    if any(proof.get(k) != v for k, v in expected.items()):
        raise ValueError('native encrypted delivery bytes, source or private cleanup differs')
