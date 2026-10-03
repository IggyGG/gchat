"""Admit one release's new work while retaining already dispatched requests."""
import json
import time
from pathlib import Path
from release_coordinator import atomic_json, read_receipt


DONE = {'available', 'superseded'}


def external_ios_wait(state, ledger, release):
    if state is None:
        return False
    from release_publish import job
    from release_feed import digest
    manifest = ledger.manifest(release)
    work = job(Path(state), manifest, 'ios', 'submit')
    if not (work/'attempted.json').is_file():
        return False
    try:
        waiting = json.loads((work/'external-prerequisite.json').read_text())
        observation_path = work/'encryption-observation.json'
        observed = json.loads(observation_path.read_text())
        if (waiting.get('schema') != 1 or waiting.get('release_id') != release
            or waiting.get('sources') != manifest['sources'] or waiting.get('platform') != 'ios'
            or waiting.get('kind') != 'apple_encryption_review'
            or waiting.get('uploaded') is not False or waiting.get('submitted') is not False
            or type(waiting.get('at')) is not int or not 0 <= time.time()-waiting['at'] <= 600
            or waiting.get('encryption_observation_sha256') != digest(observation_path)
            or observed.get('release_id') != release or observed.get('sources') != manifest['sources']
            or observed.get('state') != 'IN_REVIEW' or observed.get('includes_france') is not True):
            return False
        for stage, binding in [('verify', 'verification_sha256'), ('compatibility', 'compatibility_sha256')]:
            report, sha = read_receipt(job(Path(state), manifest, 'ios', stage)/'receipt.json', manifest, 'ios', stage)
            if waiting.get(binding) != sha or (stage == 'compatibility' and report.get('relay_compatible') is not True):
                return False
        return True
    except (OSError, ValueError, KeyError, TypeError):
        return False


def internal_complete(ledger, release, state=None):
    rows = ledger.db.execute('SELECT platform,state FROM platforms WHERE candidate=?', (release,)).fetchall()
    return bool(rows) and all(row['state'] in DONE or
        (row['platform'] in ('ios', 'android') and row['state'] in ('processing', 'in_review')) or
        (row['platform'] == 'ios' and row['state'] == 'submitting'
         and external_ios_wait(state, ledger, release)) for row in rows)


def select(state, ledger):
    state = Path(state)
    path = state / 'release-flight.json'
    previous = json.loads(path.read_text()) if path.is_file() else {}
    active = previous.get('active')
    if active is None:
        desired = state / 'deployment/desired.json'
        active = json.loads(desired.read_text())['release_id'] if desired.is_file() else None
    active_row = ledger.db.execute('SELECT seq FROM candidates WHERE id=?', (active,)).fetchone()
    if active is not None and active_row is None:
        raise ValueError('release flight refers to an unknown candidate')
    pending = ledger.db.execute('''SELECT c.id,c.seq FROM candidates c WHERE EXISTS
        (SELECT 1 FROM platforms p WHERE p.candidate=c.id AND p.state NOT IN ('available','superseded'))
        ORDER BY c.seq DESC''').fetchall()
    active_sequence = active_row['seq'] if active_row is not None else 0
    waiting = [row['id'] for row in pending if row['seq'] > active_sequence]
    if active is None or internal_complete(ledger, active, state):
        active = waiting[0] if waiting else active
        waiting = [release for release in waiting if release != active]
    result = {'schema': 1, 'active': active, 'pending': waiting[0] if waiting else None}
    if result != previous:
        atomic_json(path, result)
    return result


def already_dispatched(state, ledger, release, platform, kind='build'):
    effect = ledger.db.execute('''SELECT id,state,external_id FROM effects
        WHERE candidate=? AND platform=? AND kind=? ''', (release, platform, kind)).fetchone()
    if effect is None:
        return False
    root = Path(state) / 'jobs' / effect['id']
    return effect['state'] == 'complete' or effect['external_id'] is not None or (root / 'attempted.json').exists()


def can_build(coordinator, release, platform):
    return can_execute(coordinator, release, platform, 'build', 'build')


def can_execute(coordinator, release, platform, stage, kind):
    if not coordinator.config.get('single_flight', False):
        return True
    if stage in ('verify', 'observe'):
        return True  # Retain completed artifacts and observe external store reviews.
    flight = select(coordinator.state, coordinator.ledger)
    return release == flight['active'] or already_dispatched(coordinator.state, coordinator.ledger,
                                                            release, platform, kind)
