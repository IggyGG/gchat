"""Reconcile a serial infrastructure rollout before installed-network acceptance.

Inventory and worker argv are operator-owned, never supplied by a candidate.
Workers observe actual running artifacts. A successful command alone is not
deployment evidence. A crash after activation always resumes with observation.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from release_pair import canonical


def write(path, value):
    from release_coordinator import atomic_json
    atomic_json(path, value)


def inventory(config):
    targets = config.get('targets', [])
    if not targets or len({t['id'] for t in targets}) != len(targets):
        raise ValueError('deployment inventory is empty or repeats a target')
    for target in targets:
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', target['id']):
            raise ValueError('invalid deployment target identity')
        for stage in ('observe', 'prepare', 'activate', 'rollback', 'check'):
            argv = target.get('workers', {}).get(stage)
            if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
                raise ValueError('deployment target needs every reconcilable worker')
    return targets


def invoke(target, stage, manifest, directory, previous=None):
    directory.mkdir(parents=True, exist_ok=True)
    source = directory / 'candidate.json'
    write(source, manifest)
    spec = directory / 'target.json'
    write(spec, {k: v for k, v in target.items() if k != 'workers'})
    stamp = str(time.time_ns())
    output = directory / (stage + '-' + stamp + '.json')
    prior = directory / 'previous.json'
    if previous is not None:
        write(prior, previous)
    env = dict(os.environ, GCHAT_RELEASE_MANIFEST=str(source),
               GCHAT_DEPLOYMENT_TARGET=str(spec), GCHAT_DEPLOYMENT_STAGE=stage,
               GCHAT_DEPLOYMENT_RECEIPT=str(output), GCHAT_DEPLOYMENT_PREVIOUS=str(prior))
    with (directory / (stage + '-' + stamp + '.log')).open('xb') as stream:
        result = subprocess.run(target['workers'][stage], env=env, stdout=stream,
                                stderr=subprocess.STDOUT, timeout=target.get('timeout', 120))
    if result.returncode == 75:
        return None
    if result.returncode:
        raise ValueError('deployment worker failed: ' + target['id'] + '/' + stage)
    proof = json.loads(output.read_text())
    if (proof.get('schema') != 1 or proof.get('target') != target['id']
            or proof.get('stage') != stage or proof.get('release_id') != manifest['release_id']
            or proof.get('sources') != manifest['sources']):
        raise ValueError('deployment receipt does not bind target, stage and source pair')
    if type(proof.get('observed_at')) is not int or not 0 <= time.time() - proof['observed_at'] <= 300:
        raise ValueError('deployment observation is stale or future-dated')
    if stage == 'observe':
        if type(proof.get('healthy')) is not bool or type(proof.get('matches')) is not bool:
            raise ValueError('deployment observation lacks health or artifact comparison')
        if not isinstance(proof.get('running'), dict):
            raise ValueError('deployment observation lacks actual running identity')
    elif proof.get('passed') is not True:
        raise ValueError('deployment worker did not pass: ' + target['id'] + '/' + stage)
    references = proof.get('evidence', [])
    if not references:
        raise ValueError('deployment worker retained no evidence')
    for ref in references:
        path = (directory / ref['path']).resolve()
        if not path.is_relative_to(directory.resolve()) or not path.is_file():
            raise ValueError('deployment evidence is missing or escapes worker directory')
        with path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != ref['sha256']:
                raise ValueError('deployment evidence changed')
    return proof


def reconcile(state, manifest, config, worker=invoke, now=None):
    """One bounded serial step. False means publication must keep waiting.

    Preparation is repeatable; activation is reconciled from its durable intent.
    A failed canary restores the previous artifact and blocks this exact rollout.
    Changing a failure condition requires a changed, reviewed inventory revision.
    """
    import fcntl  # The deployment owner runs on the POSIX coordinator.
    now = int(time.time()) if now is None else now
    targets = inventory(config)
    root = Path(state) / 'deployment'
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'rollout.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        owner = root / 'owner.json'
        if owner.exists():
            active = json.loads(owner.read_text())
            if active['release_id'] != manifest['release_id']:
                return False
        else:
            write(owner, {'release_id': manifest['release_id']})
        directory = root / manifest['release_id']
        directory.mkdir(exist_ok=True)
        journal = directory / 'journal.json'
        revision = hashlib.sha256(canonical(config)).hexdigest()
        report = json.loads(journal.read_text()) if journal.exists() else {
            'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
            'revision': revision, 'inventory': config, 'state': 'deploying', 'targets': {}}
        if report['revision'] != revision:
            if any(item.get('state') in {'activating', 'rollback_pending', 'rollback_failed'}
                   for item in report['targets'].values()):
                # Finish the original external effect before adopting a revised
                # inventory, which could remove the target needing rollback.
                targets = inventory(report['inventory'])
            else:
                # Preserve the failed revision; a correction does not erase it.
                write(directory / ('revision-' + report['revision'] + '-' + str(time.time_ns()) + '.json'), report)
                report.update(revision=revision, inventory=config, state='deploying')
        rolling_back = any(
            item.get('state') in {'rollback_pending', 'rollback_failed'} for item in report['targets'].values())
        if report['state'] == 'blocked' and not rolling_back:
            if not any(item.get('state') == 'activating' for item in report['targets'].values()):
                owner.unlink(missing_ok=True)
            return False
        try:
            if rolling_back:
                for target in targets:
                    item = report['targets'].get(target['id'], {})
                    if item.get('state') not in {'rollback_pending', 'rollback_failed'}:
                        continue
                    if now < item.get('retry_at', 0): return False
                    item['retry_at'] = now + 60
                    proof = worker(target, 'rollback', manifest, directory / target['id'], item['previous'])
                    if proof is not None: item['state'] = 'rolled_back'
                    return False
                return False
            report['state'] = 'deploying'
            observations = {}
            for target in targets:
                proof = worker(target, 'observe', manifest, directory / target['id'])
                if proof is None:
                    return False
                observations[target['id']] = proof
                item = report['targets'].setdefault(target['id'], {})
                item['observed'] = proof
            # No rollout may add a second unavailable target. An already broken
            # target is repaired first; disabled test workloads are not inventory.
            unhealthy = [t for t in targets if not observations[t['id']]['healthy']]
            pending = [t for t in targets if not (observations[t['id']]['healthy']
                       and observations[t['id']]['matches'])
                       or report['targets'][t['id']].get('state') == 'activating']
            if len(unhealthy) > 1:
                report['reason'] = 'More than one target is unhealthy; rollout deferred'
                return False
            if not pending:
                report.update(state='deployed', observed_at=now)
                report.pop('reason', None)
                owner.unlink(missing_ok=True)
                return True
            target = unhealthy[0] if unhealthy else pending[0]
            item = report['targets'][target['id']]
            work = directory / target['id']
            if item.get('state') != 'activating':
                prepared = worker(target, 'prepare', manifest, work)
                if prepared is None:
                    return False
                item.update(state='activating', started_at=now, previous=observations[target['id']], prepared=prepared)
                write(journal, report)  # activation intent precedes the external effect
            if now - item['started_at'] > target.get('activation_deadline_seconds', 900):
                raise ValueError('deployment activation exceeded its original deadline')
            observation = observations[target['id']]
            if not (observation['matches'] and observation['healthy']):
                if worker(target, 'activate', manifest, work, item['previous']) is None:
                    return False
                observation = worker(target, 'observe', manifest, work)
                if observation is None:
                    return False
                if not (observation['healthy'] and observation['matches']):
                    raise ValueError('activated artifact is not running and healthy: ' + target['id'])
            if worker(target, 'check', manifest, work) is None:
                return False
            item.update(state='deployed', observed=observation)
            return False  # observe the whole fleet again before the next mutation
        except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
            report.update(state='blocked', reason='Deployment failed; retained worker evidence requires correction')
            for target in targets:
                item = report['targets'].get(target['id'], {})
                if item.get('state') == 'activating':
                    try:
                        rollback = worker(target, 'rollback', manifest, directory / target['id'], item['previous'])
                        item['state'] = 'rolled_back' if rollback else 'rollback_pending'
                    except (ValueError, KeyError, OSError, subprocess.SubprocessError):
                        item['state'] = 'rollback_failed'
            if not any(item.get('state') in {'activating', 'rollback_pending', 'rollback_failed'}
                       for item in report['targets'].values()):
                owner.unlink(missing_ok=True)
            write(directory / ('failure-' + str(time.time_ns()) + '.json'), {'type': type(error).__name__})
            return False
        finally:
            write(journal, report)
            # Public status deliberately omits host addresses, paths and commands.
            write(Path(state) / 'public/deployment.json', {
                'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
                'state': report['state'], 'reason': report.get('reason', ''), 'observed_at': now,
                'targets': [{'id': ident, 'state': item.get('state', 'pending'),
                             'healthy': item.get('observed', {}).get('healthy'),
                             'matches': item.get('observed', {}).get('matches')}
                            for ident, item in report['targets'].items()]})
