"""Durable public-delivery obligations owned by the existing sole ledger writer.

Delivery reports are projections of qualified release state. They cannot advance
an application gate, reset a deadline, or authorize an external provider action.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

from release_pair import canonical
from release_ledger import PLATFORMS
from release_failure import DESCRIPTIONS, read_json, retained_diagnostics

POLICY = 'source-descendant-or-reviewed-equivalent-v1'
ACTIONS = {
    'code': 'Repair the recorded native job in source, then push a newly qualified candidate.',
    'operator': 'Correct the recorded signing/account configuration; reconcile the original request.',
    'infrastructure': 'Inspect retained infrastructure evidence and retry budget; reconcile the original request.',
    'unclassified': 'Inspect the retained failed job/execution log; classify the cause before authorizing recovery.',
}


def configuration(value):
    if value is None: return None
    if (not isinstance(value, dict) or set(value) != {'owner', 'successor_policy'}
            or not isinstance(value['owner'], str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', value['owner'])
            or value['successor_policy'] != POLICY):
        raise ValueError('delivery tracking needs a named owner and reviewed successor policy')
    return value


def register(ledger, manifest, config):
    config = configuration(config)
    if not config: raise ValueError('delivery tracking is not configured')
    release = manifest['release_id']
    required = manifest.get('selected_platforms', list(PLATFORMS))
    with ledger.transaction():
        ledger.db.execute('INSERT OR IGNORE INTO deliveries VALUES(?,?,?,?,?,?,?)',
            (release, int(time.time()), config['owner'], config['successor_policy'],
             canonical(required).decode(), 'in_progress', '{}'))
    return release


class Containment:
    def __init__(self, repositories):
        self.repositories = repositories
        self.ancestry = {}
        self.inputs = {}

    def contains(self, original, candidate, platform, policy):
        before = original.get('upstream', original['sources'])
        after = candidate.get('upstream', candidate['sources'])
        projects = ('gcoms',) if platform == 'sdk' else ('gchat', 'gcoms')
        if all(before[p] == after[p] for p in projects): return 'exact_source'
        if policy != POLICY: return None
        descendants = True
        for project in projects:
            old, new = before[project]['commit'], after[project]['commit']
            if old == new: continue
            if project not in self.repositories: return None
            if not all(re.fullmatch('[0-9a-f]{40}', value) for value in (old, new)):
                raise ValueError('delivery source identity is invalid')
            key = (project, old, new)
            if key not in self.ancestry:
                result = subprocess.run(['git', '-C', str(self.repositories[project]), 'merge-base', '--is-ancestor', old, new],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=15)
                if result.returncode not in (0, 1): raise ValueError('delivery source ancestry is unavailable')
                self.ancestry[key] = result.returncode == 0
            descendants &= self.ancestry[key]
        if descendants: return 'source_descendant'
        # Prepared release versions and reviewed documentation/controller-only
        # revisions may be siblings. Preserve their original source labels and
        # explicitly prove equivalent application/SDK inputs rather than claim
        # literal Git ancestry. Unknown paths remain conservative native inputs.
        if platform == 'sdk':
            from release_sdk import qualification_inputs
            def sdk(source):
                key = ('sdk', source['gcoms']['commit'])
                if key not in self.inputs:
                    self.inputs[key] = qualification_inputs(self.repositories['gcoms'], key[1])
                return self.inputs[key]
            if sdk(before) == sdk(after): return 'reviewed_sdk_equivalent'
        elif all(p in self.repositories for p in projects):
            from release_inputs import fingerprints
            def application(source):
                key = canonical(source)
                if key not in self.inputs:
                    value = fingerprints(self.repositories, source)
                    self.inputs[key] = (value['artifacts'], value['infrastructure'])
                return self.inputs[key]
            if application(before) == application(after): return 'reviewed_runtime_equivalent'
        return None


def publication(ledger, state, manifest, platform):
    release = manifest['release_id']
    target = ledger.target(release, platform)
    if target['state'] != 'available': return None
    effect = ledger.db.execute("SELECT * FROM effects WHERE candidate=? AND platform=? AND state='confirmed' AND evidence=?",
                               (release, platform, target['evidence'])).fetchone()
    if effect is None: return None
    kind = effect['kind']
    stage = 'observe' if kind.startswith('observe') else kind
    if stage not in (('submit', 'observe') if platform in ('android', 'ios') else ('publish',)):
        return None
    if stage == 'observe':
        pointer = Path(state) / 'observe-effects' / release / (platform + '.json')
        latest = read_json(pointer)['kind'] if pointer.is_file() else 'observe'
        if kind != latest: return None
    path = Path(state) / 'jobs' / effect['id'] / 'receipt.json'
    if path.is_symlink(): raise ValueError('publication receipt must not be a link')
    with path.open('rb') as stream: raw = stream.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != effect['evidence']:
        raise ValueError('publication receipt changed')
    report = json.loads(raw)
    expected = {'schema': 1, 'release_id': release, 'sources': manifest['sources'], 'platform': platform,
                'stage': stage, 'passed': True, 'source_unchanged': True}
    if any(report.get(k) != v for k, v in expected.items()): raise ValueError('publication receipt binding changed')
    if platform in ('android', 'ios') and report.get('provider_state') != 'available': return None
    return {'release_id': release, 'version': manifest['versions'][platform], 'sources': manifest['sources'],
            'receipt_sha256': effect['evidence'], 'effect_id': effect['id'], 'stage': stage}


def diagnostics(state, manifest, platform):
    request = hashlib.sha256(canonical([manifest['release_id'], platform, 'build'])).hexdigest()
    roots = [Path(state) / 'jobs' / request]
    if platform == 'sdk':
        roots = [Path(state) / 'sdk-cache' / manifest['sources']['gcoms']['commit'] / matrix
                 for matrix in ('rust', 'mobile-base', 'mobile-push')]
    reports = []
    for root in roots:
        result = retained_diagnostics(root, manifest, platform)
        if result:
            report, reference = result
            failed = sorted({name for j in report['jobs'] for name in j.get('failed_checks', [])} |
                            {name for a in report.get('child_evidence', []) for m in a.get('members', [])
                             for name in m.get('failed_checks', [])})[:8]
            reports.append({'code': report['code'], 'category': report['category'], 'repo': report['repo'],
                            'run_id': report['run_id'], 'run_attempt': report['run_attempt'],
                            'diagnostics_pending': report['diagnostics_pending'], 'evidence_sha256': reference['sha256'],
                            'failed_checks': failed,
                            'artifact_evidence': [{key: a.get(key) for key in ('artifact_id', 'sha256', 'state')}
                                                  for a in report.get('child_evidence', [])],
                            'jobs': [{key: job.get(key) for key in ('name', 'job_id', 'attempt', 'step', 'code', 'log_sha256')}
                                     for job in report['jobs']]})
    return reports


def notify(ledger, ident, value):
    ledger.db.execute('INSERT OR IGNORE INTO delivery_notifications(id,created,record) VALUES(?,?,?)',
                      (ident, int(time.time()), canonical(value).decode()))


def update(controller):
    config = configuration(controller.config.get('delivery_tracking'))
    if config is None: return []
    ledger, state = controller.ledger, controller.state
    rows = ledger.db.execute('SELECT seq,id,manifest FROM candidates ORDER BY seq DESC').fetchall()
    if not rows: return []
    cursor = ledger.db.execute("SELECT value FROM delivery_meta WHERE key='cursor'").fetchone()
    lower = int(cursor[0]) if cursor else rows[0]['seq'] - 1
    for row in reversed(rows):
        if row['seq'] > lower: register(ledger, json.loads(row['manifest']), config)
    with ledger.transaction():
        ledger.db.execute("INSERT OR REPLACE INTO delivery_meta VALUES('cursor',?)", (str(rows[0]['seq']),))
    if not hasattr(controller, 'delivery_containment'):
        controller.delivery_containment = Containment({p: v['mirror'] for p, v in controller.config.get('discovery', {}).items()
                                                       if p in ('gchat', 'gcoms')})
    containment = controller.delivery_containment
    candidates = [(row['seq'], row['id'], json.loads(row['manifest'])) for row in rows]
    sequences = {row['id']: row['seq'] for row in rows}
    rank = {'in_review': 0, 'processing': 1, 'submitting': 2, 'publishing': 3, 'verified': 4,
            'verifying': 5, 'building': 6, 'queued': 7, 'blocked': 8, 'failed': 9, 'superseded': 10}
    latest = dict(ledger.db.execute('SELECT platform,candidate FROM latest'))
    publication_cache = {}
    def published(manifest, platform):
        key = (manifest['release_id'], platform)
        if key not in publication_cache: publication_cache[key] = publication(ledger, state, manifest, platform)
        return publication_cache[key]
    completed = []
    active_tasks = set()
    for delivery in ledger.db.execute('SELECT * FROM deliveries ORDER BY created DESC').fetchall():
        original = ledger.manifest(delivery['id'])
        targets = []
        for platform in json.loads(delivery['required']):
            eligible = []
            for sequence, release, manifest in candidates:
                if sequence < sequences[delivery['id']] and release not in latest.values(): continue
                proof = containment.contains(original, manifest, platform, delivery['policy'])
                if proof:
                    target = ledger.target(release, platform)
                    eligible.append((rank.get(target['state'], -1), manifest, target, proof))
            eligible.sort(key=lambda item: item[0])  # Existing review/publication keeps progressing independently.
            _, manifest, target, proof = eligible[0]  # The original candidate is always eligible.
            available = next(((m, published(m, platform), p) for _, m, t, p in eligible
                              if t['state'] == 'available' and published(m, platform)), None)
            previous_public = published(ledger.manifest(latest[platform]), platform) if platform in latest else None
            record = {'platform': platform, 'owner': delivery['owner'], 'candidate': manifest['release_id'],
                      'candidate_version': manifest['versions'][platform], 'stage': target.get('resume_state') or target['state'],
                      'state': target['state'], 'source_proof': proof, 'published': previous_public,
                      'published_contains_change': bool(previous_public and containment.contains(
                          original, ledger.manifest(previous_public['release_id']), platform, delivery['policy'])),
                      'fulfilled': False, 'next_action': 'Continue the original qualified release automatically.'}
            record['milestone'] = {'queued': 'source_queued', 'building': 'building', 'verifying': 'built',
                'verified': 'qualified', 'publishing': 'publishing', 'submitting': 'submitting',
                'processing': 'submitted_processing', 'in_review': 'external_review'}.get(target['state'], target['state'])
            if available:
                m, receipt, proof = available
                record.update(state='published', milestone='published', fulfilled=True, fulfillment=receipt, source_proof=proof,
                              next_action='Published with verified source-containing public availability.')
            else:
                waiting = target['state'] in ('in_review', 'processing')
                if target['state'] == 'submitting' and platform == 'ios':
                    from release_flight import external_ios_wait
                    if external_ios_wait(state, ledger, manifest['release_id']):
                        record.update(milestone='external_prerequisite_review', external_owner='Apple encryption review',
                                      next_action='Observe Apple encryption approval for the original artifact before uploading.')
                if waiting:
                    from release_provider import schedule
                    observation = schedule(state, manifest['release_id'], platform, 'observe')
                    record.update(next_action='Observe the original store submission; publication requires the store availability result.',
                                  external_owner='Google Play' if platform == 'android' else 'Apple App Store',
                                  next_poll_at=(observation or {}).get('next_poll_at'))
                blocked = target['state'] in ('blocked', 'failed', 'superseded', 'available')
                if blocked:
                    recovery_path = controller.recovery_path(manifest['release_id'], platform)
                    recovery = read_json(recovery_path) if recovery_path.is_file() else {}
                    from release_coordinator import STORAGE_HEADROOM_REASON
                    capacity = recovery.get('cause') == 'storage_headroom' or target.get('reason') == STORAGE_HEADROOM_REASON
                    native = [] if capacity else diagnostics(state, manifest, platform)
                    category = recovery.get('classification', 'unclassified')
                    if native: category = next((r['category'] for r in native if r['category'] in ('code', 'operator')), native[0]['category'])
                    if category not in ACTIONS: category = 'unclassified'
                    record.update(classification=category, diagnostics=native, next_action=ACTIONS[category],
                                  evidence=target.get('evidence'), failure=recovery.get('code', 'worker_failed'))
                    checks = sorted({name for r in native for name in r['failed_checks']})[:8]
                    if checks and category == 'code':
                        record['next_action'] = 'Investigate ' + ', '.join(checks) + '; qualify a source-corrected successor.'
                    if any(r['code'] == 'native_posix_import' for r in native):
                        record['next_action'] = 'Guard POSIX-only fcntl imports in portable native tooling, then publish a source-corrected candidate.'
                    elif any(r['code'] == 'native_dependency_network' for r in native):
                        record['next_action'] = 'Restore runner DNS/registry connectivity; review the original retry budget before an explicit native retry or qualified successor.'
                    if capacity:
                        import shutil
                        record.update(classification='infrastructure', failure='storage_headroom',
                            required_free_bytes=controller.config.get('minimum_free_bytes', 16 * 1024 ** 3),
                            current_free_bytes=shutil.disk_usage(state).free,
                            next_action='Restore reserved release-storage headroom through verified retention; expired untouched work needs a new immutable successor.')
                    if target['state'] == 'available':
                        record.update(state='blocked', milestone='evidence_blocked',
                                      next_action='Restore and verify the retained public-availability receipt.')
                    if target['state'] == 'superseded':
                        record['next_action'] = 'Qualify a source-containing successor; this delivery obligation remains open.'
                    # Read-only diagnostics have their own effect; they can never
                    # change the failed build or pass an application gate.
                    if (not capacity and record['stage'] == 'building' and 'diagnose' in controller.config.get('workers', {}).get(platform, {})):
                        try: controller.execute(manifest, platform, 'diagnose')
                        except (ValueError, KeyError, OSError, subprocess.SubprocessError):
                            record['diagnostic_followup'] = 'Inspect retained diagnostic worker log; original build remains blocked.'
            # One repair can block several changes. Deduplicate the actual
            # platform/stage/failure shape, retaining every related obligation.
            shape = sorted((job.get('name') or '', job.get('step') or '', job.get('code') or '')
                           for report in record.get('diagnostics', []) for job in report['jobs'])
            failed = sorted({name for r in record.get('diagnostics', []) for name in r['failed_checks']})
            task_id = hashlib.sha256(canonical([platform, record.get('classification'), record['stage'],
                                               shape or record.get('failure', 'worker_failed'), failed])).hexdigest()
            if record.get('failure') == 'storage_headroom':
                task_id = hashlib.sha256(canonical(['release_storage_headroom'])).hexdigest()
            with ledger.transaction():
                task = ledger.db.execute('SELECT * FROM delivery_tasks WHERE id=?', (task_id,)).fetchone()
                if not record['fulfilled'] and record['state'] in ('blocked', 'failed', 'superseded'):
                    active_tasks.add(task_id)
                    generation = task['generation'] if task and task['state'] == 'open' else (task['generation'] + 1 if task else 1)
                    old = json.loads(task['record']) if task else {}
                    record['owner'] = old.get('owner', record['owner'])
                    task_record = {'id': task_id, 'delivery_id': old.get('delivery_id', delivery['id']), 'platform': old.get('platform', platform),
                                   'owner': record['owner'], 'candidate': record['candidate'], 'state': 'open',
                                   'classification': record.get('classification'), 'next_action': record['next_action'],
                                   'diagnostics': record.get('diagnostics', []), 'updated_at': int(time.time()),
                                   'platforms': sorted(set(old.get('platforms', [])) | {platform}),
                                   'deliveries': sorted(set(old.get('deliveries', [])) | {delivery['id']})}
                    if {k: v for k, v in old.items() if k != 'updated_at'} != {k: v for k, v in task_record.items() if k != 'updated_at'}:
                        ledger.db.execute('INSERT OR REPLACE INTO delivery_tasks VALUES(?,?,?,?,?,?)',
                                          (task_id, task_record['delivery_id'], task_record['platform'], generation, 'open', canonical(task_record).decode()))
                    notify(ledger, task_id + '-' + str(generation), {'kind': 'intervention', 'delivery_id': delivery['id'],
                        'platform': platform, 'owner': record['owner'], 'task_id': task_id,
                        'next_action': record['next_action']})
                    record['task_id'] = task_id
                ledger.db.execute('''INSERT INTO delivery_targets VALUES(?,?,?) ON CONFLICT(delivery,platform)
                    DO UPDATE SET record=excluded.record WHERE delivery_targets.record!=excluded.record''',
                    (delivery['id'], platform, canonical(record).decode()))
            targets.append(record)
        fulfilled = sum(t['fulfilled'] for t in targets)
        status = 'published' if fulfilled == len(targets) else 'partially_published' if fulfilled else 'in_progress'
        report = {'id': delivery['id'], 'owner': delivery['owner'], 'state': status, 'sources': original['sources'],
                  'requested_upstream': original.get('upstream', original['sources']), 'successor_policy': delivery['policy'],
                  'required_platforms': json.loads(delivery['required']),
                  'platform_exceptions': [p for p in PLATFORMS if p not in json.loads(delivery['required'])],
                  'fulfilled_count': fulfilled, 'platforms': targets, 'observed_at': int(time.time())}
        with ledger.transaction():
            ledger.db.execute('UPDATE deliveries SET state=?,record=? WHERE id=?', (status, canonical(report).decode(), delivery['id']))
            if status == 'published':
                notify(ledger, delivery['id'] + '-published', {'kind': 'published', 'delivery_id': delivery['id'],
                    'owner': delivery['owner'], 'required_platforms': report['required_platforms'],
                    'versions': {t['platform']: t['fulfillment']['version'] for t in targets}})
        completed.append(report)
    with ledger.transaction():
        for task in ledger.db.execute("SELECT * FROM delivery_tasks WHERE state='open'").fetchall():
            if task['id'] in active_tasks: continue
            value = json.loads(task['record'])
            fulfilled = all(report['state'] == 'published' for report in completed if report['id'] in value['deliveries'])
            value.update(state='resolved' if fulfilled else 'progressing', updated_at=int(time.time()))
            ledger.db.execute('UPDATE delivery_tasks SET state=?,record=? WHERE id=?',
                              (value['state'], canonical(value).decode(), task['id']))
    return completed


def public_notifications(ledger):
    return {'schema': 1, 'notifications': [dict(json.loads(row['record']), id=row['id'], sequence=row['seq'], created_at=row['created'])
        for row in ledger.db.execute('SELECT * FROM delivery_notifications ORDER BY seq DESC LIMIT 100')]}
