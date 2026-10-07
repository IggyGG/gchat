"""Small operator requests consumed by the existing, sole release coordinator."""
import json
import hashlib
from pathlib import Path
import re
import sqlite3
import subprocess
import time
import uuid
from contextlib import closing

from release_coordinator import atomic_json
from release_pair import canonical


def identity(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('release must be its full immutable ID')
    return value


def selected(state, release=None):
    state = Path(state)
    if release:
        return identity(release)
    desired = state / 'deployment/desired.json'
    if desired.is_file():
        return identity(json.loads(desired.read_text())['release_id'])
    with closing(sqlite3.connect((state / 'ledger.sqlite').resolve().as_uri() + '?mode=ro', uri=True)) as db:
        row = db.execute('SELECT id FROM candidates ORDER BY seq DESC LIMIT 1').fetchone()
    if not row:
        raise ValueError('no release candidate exists')
    return identity(row[0])


def status(state, release=None, now=None):
    state = Path(state)
    release = selected(state, release)
    now = int(time.time()) if now is None else now
    with closing(sqlite3.connect((state / 'ledger.sqlite').resolve().as_uri() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        candidate = db.execute('SELECT seq,manifest FROM candidates WHERE id=?', (release,)).fetchone()
        if candidate is None:
            raise ValueError('unknown release candidate')
        platforms = []
        for item in db.execute('SELECT platform,state,reason FROM platforms WHERE candidate=? ORDER BY platform', (release,)):
            event = db.execute('SELECT time FROM events WHERE candidate=? AND platform=? ORDER BY seq DESC LIMIT 1',
                               (release, item['platform'])).fetchone()
            platforms.append({**dict(item), 'state_age_seconds': max(0, now - event[0]) if event else None})
        manifest = json.loads(candidate['manifest'])
    for item in platforms:
        routine = state / 'routine-runs' / release / (item['platform'] + '.json')
        if routine.is_file():
            run = json.loads(routine.read_text())
            item['routine_deadline_at'] = run.get('deadline_at')
            item['external_wait'] = 'paused_at' in run
        publication = state / 'publication-runs' / release / (item['platform'] + '.json')
        if publication.is_file():
            run = json.loads(publication.read_text())
            item['publication_deadline_at'] = run.get('deadline_at')
            item['publication_wait'] = 'paused_at' in run
    journal = state / 'deployment' / release / 'journal.json'
    deployment = json.loads(journal.read_text()) if journal.is_file() else {}
    targets = [{'id': name, 'state': value.get('state', 'pending'),
                'healthy': value.get('observed', {}).get('healthy'),
                'matches': value.get('observed', {}).get('matches'),
                'running': value.get('observed', {}).get('running', {})}
               for name, value in deployment.get('targets', {}).items()]
    # Public summary omits hostnames, private paths, provider URLs and commands.
    for item in targets:
        item['running'] = {key: value for key, value in item['running'].items() if key in ('sha256', 'images')}
        if 'images' in item['running']:
            item['running']['images'] = [{'container': image.get('container'), 'image_id': image.get('image_id')}
                                         for image in item['running']['images']]
    public_path = state / 'public/status.json'
    public = json.loads(public_path.read_text()) if public_path.is_file() else {}
    progress_path = state / 'deployment' / release / 'progress.json'
    progress = json.loads(progress_path.read_text()) if progress_path.is_file() else {}
    load_path = state / 'relay-load' / release / 'status.json'
    load = json.loads(load_path.read_text()) if load_path.is_file() else {}
    return {'schema': 1, 'release_id': release, 'sequence': candidate['seq'],
            'versions': manifest['versions'], 'sources': manifest['sources'], 'observed_at': now,
            'deployment': {'state': deployment.get('state', 'waiting_artifacts'),
                           'reason': deployment.get('reason', ''), 'targets': targets},
            'platforms': platforms, 'flight': public.get('flight'),
            'publication_policy': public.get('publication_policy'),
            'relay_load': load,
            'controller_status_age_seconds': max(0, now - public['observed_at']) if public.get('observed_at') else None,
            'running_workers': [{key: item[key] for key in ('release_id', 'platform', 'stage', 'started_at', 'deadline_at')
                                 if key in item} for item in public.get('running_workers', [])],
            'deployment_progress': {key: progress[key] for key in ('target', 'stage', 'started_at', 'deadline_at')
                                    if key in progress}}


def request(state, action, release=None, platform=None, *, observed=None, reason=None):
    if action not in ('resume', 'rollback', 'qualify', 'handoff'):
        raise ValueError('unsupported release control')
    if action == 'qualify' and platform not in ('android', 'ios'):
        raise ValueError('deep mobile qualification requires --platform android or ios')
    if action == 'rollback' and platform is not None:
        raise ValueError('rollback restores the deployment; it cannot roll back a store publication')
    if action == 'handoff':
        if (platform is not None or not isinstance(observed, dict) or not observed
                or len(observed) > 17 or not isinstance(reason, str) or not 1 <= len(reason) <= 500
                or any(not re.fullmatch('[a-z0-9][a-z0-9-]{0,63}', name)
                       or not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{64}', sha)
                       for name, sha in observed.items())):
            raise ValueError('handoff needs a reason and exact target=sha256 observations')
    elif observed is not None or reason is not None:
        raise ValueError('observed hashes and reason are only available for handoff')
    release = selected(state, release)
    # Resolve against retained state before queuing anything.
    current = status(state, release)
    if platform and platform not in {item['platform'] for item in current['platforms']}:
        raise ValueError('unknown release platform')
    ident = uuid.uuid4().hex
    value = {'schema': 1, 'id': ident, 'release_id': release, 'action': action,
             'platform': platform, 'requested_at': int(time.time())}
    if action == 'handoff':
        journal = Path(state) / 'deployment' / release / 'journal.json'
        value.update(observed=observed, reason=reason,
                     journal_sha256=hashlib.sha256(journal.read_bytes()).hexdigest())
    path = Path(state) / 'control/incoming' / (ident + '.json')
    atomic_json(path, value)
    return {'request_id': ident, 'release_id': release, 'action': action, 'state': 'queued'}


def deployment_config(state, manifest, config):
    """Qualified controller overlays and retries never change a manifest."""
    from release_controller import deployment_config as controller_config
    config = controller_config(state, manifest, config)
    path = Path(state) / 'control/deployment-retries' / (manifest['release_id'] + '.json')
    return {**config, 'operator_retry': json.loads(path.read_text())['id']} if path.is_file() else config


def consume(controller):
    state = controller.state
    incoming = state / 'control/incoming'
    incoming.mkdir(parents=True, exist_ok=True)
    for path in sorted(incoming.glob('*.json'))[:8]:
        output = state / 'control/results' / path.name
        if output.is_file():
            path.unlink()
            continue
        try:
            if path.is_symlink() or path.stat().st_size > 4096:
                raise ValueError('invalid operator request file')
            value = json.loads(path.read_text())
            if (value.get('schema') != 1 or value.get('id') != path.stem
                    or not re.fullmatch('[0-9a-f]{32}', path.stem)):
                raise ValueError('invalid operator request identity')
            release = identity(value['release_id'])
            controller.ledger.manifest(release)
            if value['action'] == 'resume':
                if not value.get('platform'):
                    desired = state / 'deployment/desired.json'
                    if not desired.is_file() or json.loads(desired.read_text())['release_id'] != release:
                        raise ValueError('only the selected deployment can be resumed')
                    journal = state / 'deployment' / release / 'journal.json'
                    if journal.is_file() and json.loads(journal.read_text()).get('state') == 'handed_off':
                        raise ValueError('deployment was handed off; a new qualified release is required')
                platforms = [value['platform']] if value.get('platform') else [
                    row[0] for row in controller.ledger.db.execute('SELECT platform FROM platforms WHERE candidate=?', (release,))]
                resumed = []
                for platform in platforms:
                    item = controller.ledger.target(release, platform)
                    if item['state'] == 'blocked':
                        controller.ledger.transition(release, platform, item['resume_state'], evidence=item['evidence'])
                        resumed.append(platform)
                if not value.get('platform'):
                    atomic_json(state / 'control/deployment-retries' / (release + '.json'), {'id': value['id']})
                result = {'state': 'accepted', 'resumed_platforms': resumed}
            elif value['action'] == 'qualify' and value.get('platform') in ('android', 'ios'):
                atomic_json(state / 'control/qualifications' / (value['id'] + '.json'), value)
                result = {'state': 'accepted', 'qualification': 'queued'}
            elif value['action'] == 'rollback' and value.get('platform') is None:
                from release_deployment import request_rollback
                request_rollback(state, release)
                result = {'state': 'accepted', 'rollback': 'pending'}
            elif value['action'] == 'handoff' and value.get('platform') is None:
                from release_deployment import handoff
                handoff(state, controller.ledger.manifest(release), value)
                result = {'state': 'accepted', 'deployment': 'handed_off', 'qualification': 'unchanged'}
            else:
                raise ValueError('unsupported operator request')
        except BlockingIOError:
            continue  # Keep the operator request queued while the rollout owns its lock.
        except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
            result = {'state': 'rejected', 'reason': str(error) if isinstance(error, ValueError) else type(error).__name__}
        atomic_json(output, result)
        path.unlink()


def qualifications(controller):
    """Explicit deep checks have their own results and never change publication."""
    root = controller.state / 'control/qualifications'
    for path in sorted(root.glob('*.json'))[:2]:
        value = json.loads(path.read_text())
        manifest = controller.ledger.manifest(identity(value['release_id']))
        platform = value['platform']
        output = controller.state / 'control/qualification-results' / path.name
        try:
            result = controller.execute(manifest, platform, 'acceptance')
            if result is None:
                continue
            report, digest = result
            status = {'state': 'passed', 'receipt_sha256': digest, 'scope': 'installed_mobile_qualification'}
        except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
            status = {'state': 'failed', 'error_type': type(error).__name__, 'scope': 'installed_mobile_qualification'}
        atomic_json(output, {'release_id': manifest['release_id'], 'platform': platform, **status})
        path.unlink()
