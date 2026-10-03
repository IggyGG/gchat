"""Admit one release's new builds while retaining already dispatched work."""
import json
from pathlib import Path
from release_coordinator import atomic_json


DONE = {'available', 'superseded'}


def internal_complete(ledger, release):
    rows = ledger.db.execute('SELECT platform,state FROM platforms WHERE candidate=?', (release,)).fetchall()
    return bool(rows) and all(row['state'] in DONE or
        (row['platform'] in ('ios', 'android') and row['state'] in ('processing', 'in_review')) for row in rows)


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
    if active is None or internal_complete(ledger, active):
        active = waiting[0] if waiting else active
        waiting = [release for release in waiting if release != active]
    result = {'schema': 1, 'active': active, 'pending': waiting[0] if waiting else None}
    if result != previous:
        atomic_json(path, result)
    return result


def already_dispatched(state, ledger, release, platform):
    effect = ledger.db.execute('''SELECT id,state,external_id FROM effects
        WHERE candidate=? AND platform=? AND kind='build' ''', (release, platform)).fetchone()
    if effect is None:
        return False
    root = Path(state) / 'jobs' / effect['id']
    return effect['state'] == 'complete' or effect['external_id'] is not None or (root / 'attempted.json').exists()


def can_build(coordinator, release, platform):
    if not coordinator.config.get('single_flight', False):
        return True
    flight = select(coordinator.state, coordinator.ledger)
    return release == flight['active'] or already_dispatched(coordinator.state, coordinator.ledger, release, platform)
