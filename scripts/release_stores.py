#!/usr/bin/env python3
"""Durable store submission and observation. Credentials are file references only.

Uploading, submitted for review and available are different states. Never infer
publication from a successful upload or an edits.tracks `completed` response.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from release_coordinator import atomic_json, read_receipt
from release_pair import validate


class ProviderError(RuntimeError):
    pass


class Provider:
    def __init__(self, session, base):
        self.session, self.base = session, base

    def request(self, method, path, **kwargs):
        response = self.session.request(method, self.base + path, timeout=(15, 120), **kwargs)
        if not response.ok:
            # Provider bodies can contain temporary URLs or personal details.
            raise ProviderError(f'Provider HTTP {response.status_code}; action requires reconciliation')
        return response.json() if response.content else {}


def google(config):
    import jwt
    import requests
    credentials = json.loads(Path(config['credentials']).read_text())
    if credentials['client_email'] != config['service_account']:
        raise ValueError('unexpected Play publisher account')
    assertion = jwt.encode({'iss': credentials['client_email'], 'scope': 'https://www.googleapis.com/auth/androidpublisher',
                           'aud': 'https://oauth2.googleapis.com/token', 'iat': int(time.time()) - 5,
                           'exp': int(time.time()) + 600}, credentials['private_key'], algorithm='RS256')
    response = requests.post('https://oauth2.googleapis.com/token', timeout=30,
                             data={'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer', 'assertion': assertion})
    if not response.ok: raise ProviderError('Play publisher authentication failed')
    session = requests.Session()
    session.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
    return Provider(session, 'https://androidpublisher.googleapis.com/androidpublisher/v3/applications/' + config['package'])


def apple(config):
    import jwt
    import requests
    token = jwt.encode({'iss': config['issuer'], 'iat': int(time.time()) - 5, 'exp': int(time.time()) + 600,
                        'aud': 'appstoreconnect-v1'}, Path(config['key']).read_text(), algorithm='ES256',
                       headers={'kid': config['key_id'], 'typ': 'JWT'})
    session = requests.Session(); session.headers['Authorization'] = 'Bearer ' + token
    return Provider(session, 'https://api.appstoreconnect.apple.com')


def google_state(releases, code, track='production'):
    matching = [r for r in releases if r.get('track') == track and
                any(str(a.get('versionCode')) == str(code) for a in r.get('activeArtifacts', []))]
    if len(matching) != 1:
        return {'state': 'processing', 'reason': 'Waiting for the exact version to appear in the store lifecycle API'}
    status = matching[0].get('releaseLifecycleState')
    states = {'RELEASE_LIFECYCLE_STATE_PUBLISHED': 'available',
              'RELEASE_LIFECYCLE_STATE_IN_REVIEW': 'in_review',
              'RELEASE_LIFECYCLE_STATE_NOT_APPROVED': 'blocked',
              'RELEASE_LIFECYCLE_STATE_APPROVED_NOT_PUBLISHED': 'blocked',
              'RELEASE_LIFECYCLE_STATE_NOT_SENT_FOR_REVIEW': 'blocked',
              'RELEASE_LIFECYCLE_STATE_DRAFT': 'blocked'}
    return {'state': states.get(status, 'processing'), 'provider_status': status,
            'reason': 'Play Console action required' if states.get(status) == 'blocked' else ''}


def apple_state(version, expected_build):
    build = version.get('relationships', {}).get('build', {}).get('data') or {}
    if build.get('id') != expected_build:
        return {'state': 'blocked', 'reason': 'App Store version is not attached to the candidate build'}
    status = version['attributes']['appStoreState']
    states = {'READY_FOR_DISTRIBUTION': 'available', 'READY_FOR_SALE': 'available',
              'WAITING_FOR_REVIEW': 'in_review', 'IN_REVIEW': 'in_review',
              'PENDING_APPLE_RELEASE': 'processing', 'PROCESSING_FOR_DISTRIBUTION': 'processing',
              'PROCESSING_FOR_APP_STORE': 'processing'}
    return {'state': states.get(status, 'blocked'), 'provider_status': status,
            'reason': '' if status in states else 'App Store Connect action required'}


def observe_google(api, code, track='production'):
    return google_state(api.request('GET', '/tracks/' + track + '/releases').get('releases', []), code, track)


def observe_apple(api, version_id, build_id):
    return apple_state(api.request('GET', '/v1/appStoreVersions/' + version_id,
                                   params={'include': 'build'})['data'], build_id)


def submit_google(api, config, candidate, aab, journal):
    """One edit, retained before each mutation; unknown upload/commit reconciled.

    The caller supplies the already signature/source-verified AAB. Version code
    and sha256 must match the exact immutable qualification record.
    """
    aab, journal = Path(aab), Path(journal)
    with aab.open('rb') as stream: digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != candidate['aab_sha256']: raise ValueError('qualified Android bundle changed')
    identity = {k: candidate[k] for k in ('release_id', 'version_code', 'aab_sha256')}
    state = json.loads(journal.read_text()) if journal.exists() else {'identity': identity}
    if state['identity'] != identity: raise ValueError('store submission identity changed')
    if state.get('commit_attempted'):
        observed = observe_google(api, candidate['version_code'], config.get('track', 'production'))
        if observed['state'] != 'processing': return observed
        # An uncommitted edit can still be read. Never create a replacement edit
        # merely because the committed release is not visible immediately.
        try: retained = api.request('GET', '/edits/' + state['edit'])
        except ProviderError:
            return {'state': 'processing', 'reason': 'Commit outcome unknown; waiting for provider reconciliation'}
        if retained.get('id') != state['edit']: raise ValueError('unexpected retained edit')
        raise ProviderError('Commit outcome not confirmed; do not repeat it automatically')
    if 'edit' not in state:
        if state.get('edit_attempted'): raise ProviderError('Edit creation outcome unknown; reconcile before creating another')
        state['edit_attempted'] = True; atomic_json(journal, state)
        state['edit'] = api.request('POST', '/edits', json={})['id']; atomic_json(journal, state)
    edit = '/edits/' + state['edit']
    code = str(candidate['version_code'])
    bundles = api.request('GET', edit + '/bundles').get('bundles', [])
    existing = next((b for b in bundles if str(b['versionCode']) == code), None)
    if existing:
        if existing.get('sha256') != digest: raise ValueError('Play version code has different bundle bytes')
    else:
        if state.get('upload_attempted'): raise ProviderError('Bundle upload outcome unknown; waiting for reconciliation')
        state['upload_attempted'] = True; atomic_json(journal, state)
        # Media endpoint is fixed to Google's authenticated upload API.
        upload = Provider(api.session, 'https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications/' + config['package'])
        with aab.open('rb') as stream:
            result = upload.request('POST', edit + '/bundles', params={'uploadType': 'media'},
                                    headers={'Content-Type': 'application/octet-stream'}, data=stream)
        if str(result.get('versionCode')) != code or result.get('sha256') != digest:
            raise ValueError('uploaded bundle identity differs')
    track = config.get('track', 'production')
    desired = {'track': track, 'releases': [{'name': candidate['release_id'], 'versionCodes': [code], 'status': 'completed'}]}
    # PUT of the exact retained edit is idempotent. No new release/version on retry.
    api.request('PUT', edit + '/tracks/' + track, json=desired)
    api.request('POST', edit + ':validate', json={})
    state['commit_attempted'] = True; atomic_json(journal, state)
    api.request('POST', edit + ':commit', params={'changesNotSentForReview': 'false'}, json={})
    state['commit_accepted'] = True; atomic_json(journal, state)
    return observe_google(api, code, track)


def submit_apple(api, config, candidate, journal):
    """Attach a uniquely reserved, processed build, then submit its review item.

    Apple upload remains on the native signing worker. Its source/signature and
    structured upload-acceptance receipt are required by the coordinator first.
    """
    journal = Path(journal)
    state = json.loads(journal.read_text()) if journal.exists() else {'identity': candidate}
    if state['identity'] != candidate: raise ValueError('Apple submission identity changed')
    build = api.request('GET', '/v1/builds/' + candidate['build_id'], params={'include': 'app'})['data']
    if (build.get('relationships', {}).get('app', {}).get('data') or {}).get('id') != config['app_id'] or build['attributes'].get('version') != candidate['build_number']:
        raise ValueError('Apple build belongs to a different application or reserved version')
    if build['attributes'].get('processingState') != 'VALID':
        return {'state': 'processing', 'reason': 'Apple is processing the exact uploaded build'}
    declaration = api.request('GET', '/v1/appEncryptionDeclarations/' + config['encryption_declaration'])['data']
    if declaration['attributes'].get('appEncryptionDeclarationState') != 'APPROVED':
        return {'state': 'blocked', 'reason': 'Apple encryption declaration approval is required, including France'}
    if declaration['attributes'].get('availableOnFrenchStore') is not True:
        raise ValueError('encryption declaration does not cover France')
    version_id = candidate['version_id']
    current = api.request('GET', '/v1/appStoreVersions/' + version_id, params={'include': 'build,app'})['data']
    if (current.get('relationships', {}).get('app', {}).get('data') or {}).get('id') != config['app_id']:
        raise ValueError('App Store version belongs to a different application')
    if current['attributes']['appStoreState'] in ('WAITING_FOR_REVIEW', 'IN_REVIEW', 'READY_FOR_DISTRIBUTION', 'READY_FOR_SALE'):
        return apple_state(current, candidate['build_id'])
    if state.get('submitted') or state.get('submit_attempted'):
        return {'state': 'processing', 'reason': 'Awaiting Apple review submission reconciliation'}
    api.request('PATCH', '/v1/appStoreVersions/' + version_id + '/relationships/build',
                json={'data': {'type': 'builds', 'id': candidate['build_id']}})
    api.request('PATCH', '/v1/appStoreVersions/' + version_id,
                json={'data': {'type': 'appStoreVersions', 'id': version_id, 'attributes': {'releaseType': 'AFTER_APPROVAL'}}})
    if 'review' not in state:
        if state.get('review_attempted'): raise ProviderError('Review creation outcome unknown; reconcile the retained submission')
        state['review_attempted'] = True; atomic_json(journal, state)
        review = api.request('POST', '/v1/reviewSubmissions', json={'data': {'type': 'reviewSubmissions',
                             'attributes': {'platform': 'IOS'}, 'relationships': {'app': {'data': {'type': 'apps', 'id': config['app_id']}}}}})
        state['review'] = review['data']['id']; atomic_json(journal, state)
    if not state.get('item'):
        items = api.request('GET', '/v1/reviewSubmissions/' + state['review'] + '/items')['data']
        matching = [i for i in items if (i.get('relationships', {}).get('appStoreVersion', {}).get('data') or {}).get('id') == version_id]
        if not matching:
            if state.get('item_attempted'): raise ProviderError('Review item outcome unknown; reconcile before adding another')
            state['item_attempted'] = True; atomic_json(journal, state)
            api.request('POST', '/v1/reviewSubmissionItems', json={'data': {'type': 'reviewSubmissionItems', 'relationships': {
                'reviewSubmission': {'data': {'type': 'reviewSubmissions', 'id': state['review']}},
                'appStoreVersion': {'data': {'type': 'appStoreVersions', 'id': version_id}}}}})
        state['item'] = True; atomic_json(journal, state)
    state['submit_attempted'] = True; atomic_json(journal, state)
    api.request('PATCH', '/v1/reviewSubmissions/' + state['review'], json={'data': {'type': 'reviewSubmissions',
                'id': state['review'], 'attributes': {'submitted': True}}})
    state['submitted'] = True; atomic_json(journal, state)
    return observe_apple(api, version_id, candidate['build_id'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('observe', 'submit'))
    parser.add_argument('--platform', choices=('android', 'ios'), required=True)
    for name in ('config', 'candidate', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--journal', type=Path)
    parser.add_argument('--aab', type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--verification', type=Path)
    parser.add_argument('--compatibility', type=Path)
    args = parser.parse_args(); os.umask(0o077)
    config = json.loads(args.config.read_text())[args.platform]
    candidate = json.loads(args.candidate.read_text())
    if args.action == 'submit':
        if not all((args.manifest, args.verification, args.compatibility)):
            parser.error('submission requires exact source manifest, native verification and compatibility receipts')
        manifest = validate(json.loads(args.manifest.read_text()))
        verified, _ = read_receipt(args.verification, manifest, args.platform, 'verify')
        compatible, _ = read_receipt(args.compatibility, manifest, args.platform, 'compatibility')
        if candidate['release_id'] != manifest['release_id'] or compatible.get('relay_compatible') is not True:
            raise ValueError('candidate or relay compatibility does not match')
        if args.platform == 'android':
            if not args.aab or str(candidate['version_code']) != manifest['versions']['android'] or not any(e['sha256'] == candidate['aab_sha256'] for e in verified['evidence']):
                raise ValueError('Android upload is not covered by exact qualification')
        elif candidate['build_number'] != manifest['versions']['ios'] or not any(e['sha256'] == candidate['ipa_sha256'] for e in verified['evidence']):
            raise ValueError('iOS upload is not covered by exact qualification')
    api = google(config) if args.platform == 'android' else apple(config)
    if args.action == 'submit':
        if args.journal is None: parser.error('submit requires a durable journal')
        result = submit_google(api, config, candidate, args.aab, args.journal) if args.platform == 'android' else submit_apple(api, config, candidate, args.journal)
    else:
        result = observe_google(api, candidate['version_code'], config.get('track', 'production')) if args.platform == 'android' else observe_apple(api, candidate['version_id'], candidate['build_id'])
    atomic_json(args.output, {'release_id': candidate['release_id'], 'observed_at': int(time.time()), **result})


if __name__ == '__main__': main()
