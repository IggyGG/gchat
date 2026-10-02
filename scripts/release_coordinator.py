#!/usr/bin/env python3
"""Persistent release coordinator. Recipes are administrator-owned argv arrays.

Workers must return source-bound receipts, never just exit zero. External build
and store actions use the effect ID as their provider request ID. Reconciliation
is mandatory after a lost response; automatic blind re-submission is forbidden.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from release_ledger import Ledger
from release_pair import canonical, validate


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(canonical(value))
            stream.flush()
            os.fsync(stream.fileno())
            stream.close()
            os.replace(temporary, path)
            if os.name != "nt":
                directory = os.open(path.parent, os.O_RDONLY)
                try: os.fsync(directory)
                finally: os.close(directory)
        finally:
            temporary.unlink(missing_ok=True)


def read_receipt(path, manifest, platform, stage):
    path = Path(path).resolve()
    raw = path.read_bytes()
    report = json.loads(raw)
    if (report.get('schema') != 1 or report.get('release_id') != manifest['release_id']
            or report.get('sources') != manifest['sources'] or report.get('platform') != platform
            or report.get('stage') != stage):
        raise ValueError('worker receipt does not bind the exact candidate, platform and stage')
    if report.get('passed') is not True or report.get('source_unchanged') is not True:
        raise ValueError('worker did not pass on unchanged inputs')
    references = report.get('evidence')
    if not isinstance(references, list) or not references:
        raise ValueError('worker receipt has no retained evidence')
    for item in references:
        relative = Path(item['path'])
        reference = (path.parent / relative).resolve()
        if relative.is_absolute() or not reference.is_relative_to(path.parent) or not reference.is_file():
            raise ValueError('evidence escapes receipt directory or is missing')
        with reference.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != item['sha256']:
            raise ValueError('worker evidence changed')
    return report, hashlib.sha256(raw).hexdigest()


class Coordinator:
    def __init__(self, state, config):
        self.poll_interval = config.get('poll_interval_seconds', 30)
        if type(self.poll_interval) is not int or not 10 <= self.poll_interval <= 300:
            raise ValueError('poll_interval_seconds must be an integer between 10 and 300')
        self.state = Path(state).resolve()
        self.state.mkdir(parents=True, exist_ok=True)
        self.ledger = Ledger(self.state / 'ledger.sqlite')
        self.config = config

    def deployment_ready(self, manifest):
        if not manifest['policy'].get('deployment_required', False):
            return True
        path = self.state / 'deployment' / manifest['release_id'] / 'journal.json'
        if not path.is_file():
            return False
        report = json.loads(path.read_text())
        configured = self.config.get('deployment_file')
        if not configured or not Path(configured).is_file():
            return False
        revision = hashlib.sha256(canonical(json.loads(Path(configured).read_text()))).hexdigest()
        desired = self.state / 'deployment/desired.json'
        return (desired.is_file() and json.loads(desired.read_text())['release_id'] == manifest['release_id']
                and report.get('state') == 'deployed' and report.get('sources') == manifest['sources']
                and report.get('revision') == revision
                and 0 <= time.time() - report.get('observed_at', 0) <= 300)

    def recovery_path(self, release, platform):
        return self.state / 'recovery' / release / (platform + '.json')

    def worker_revision(self, platform, stage):
        return hashlib.sha256(canonical({'controller': self.config.get('controller_revision', os.environ.get('GCHAT_CONTROLLER_REVISION')),
            'worker': self.config.get('workers', {}).get(platform, {}).get(stage)})).hexdigest()

    def resume_corrected(self, release, platform, target):
        path = self.recovery_path(release, platform)
        if not path.exists(): return False
        recovery = json.loads(path.read_text())
        changed = recovery['revision'] != self.worker_revision(platform, recovery['stage'])
        retry = (self.config.get('automatic_recovery', False) and recovery.get('transient')
                 and recovery['attempts'] <= 5 and time.time() >= recovery['retry_at'])
        if not changed and not retry: return False
        self.ledger.transition(release, platform, target['resume_state'], evidence=target['evidence'])
        # execute() still reconciles the original durable effect ID and marker.
        # A retry never skips gates or creates a second external submission.
        return True

    def record_failure(self, release, platform, stage, error):
        path = self.recovery_path(release, platform)
        previous = json.loads(path.read_text()) if path.exists() else {}
        revision = self.worker_revision(platform, stage)
        attempts = previous.get('attempts', 0) + 1 if previous.get('revision') == revision else 1
        atomic_json(path, {'stage': stage, 'revision': revision, 'attempts': attempts,
                          'transient': isinstance(error, (TimeoutError, ConnectionError, subprocess.TimeoutExpired)),
                          'retry_at': int(time.time()) + min(300, 30 * 2 ** min(attempts - 1, 4))})

    def reconcile_deployment(self):
        """Select monotonically; a late old build must never downgrade the fleet."""
        configured = self.config.get('deployment_file')
        if not configured:
            return
        from release_deployment import reconcile
        desired_path = self.state / 'deployment/desired.json'
        previous = json.loads(desired_path.read_text()) if desired_path.exists() else None
        owner_path = self.state / 'deployment/owner.json'
        active = json.loads(owner_path.read_text()) if owner_path.exists() else None
        infrastructure_required = 'infrastructure' in self.config.get('workers', {}).get('linux-x86_64', {})
        if active:
            selected = self.ledger.db.execute('SELECT id,seq FROM candidates WHERE id=?',
                                              (active['release_id'],)).fetchone()
        else:
            selected = self.ledger.db.execute('''SELECT c.id,c.seq FROM candidates c
                WHERE EXISTS (SELECT 1 FROM platforms p WHERE p.candidate=c.id
                    AND ((? AND p.platform='linux-x86_64') OR (NOT ? AND p.platform!='sdk')) AND p.state IN
                    ('verified','publishing','submitting','processing','in_review','available'))
                ORDER BY c.seq DESC LIMIT 1''', (infrastructure_required, infrastructure_required)).fetchone()
        if selected is None or (previous and selected['seq'] < previous['sequence']):
            return
        manifest = self.ledger.manifest(selected['id'])
        if not manifest['policy'].get('deployment_required', False):
            return
        try:
            if infrastructure_required:
                if self.execute(manifest, 'linux-x86_64', 'infrastructure') is None:
                    atomic_json(self.state / 'public/deployment.json', {
                        'schema': 1, 'release_id': selected['id'], 'state': 'waiting_artifacts',
                        'reason': 'Waiting for the qualified infrastructure bundle'})
                    return
            # Selecting a mobile artifact is not a deployment intent. Advance
            # the monotonic pointer only after its exact infrastructure receipt
            # is available, so queued/superseded Linux work cannot stall rollout.
            atomic_json(desired_path, {'release_id': selected['id'], 'sequence': selected['seq']})
            reconcile(self.state, manifest, json.loads(Path(configured).read_text()))
        except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
            atomic_json(self.state / 'public/deployment.json', {
                'schema': 1, 'release_id': selected['id'], 'state': 'blocked',
                'reason': 'Deployment inventory or worker is unavailable; publication is waiting',
                'error_type': type(error).__name__})

    def execute(self, manifest, platform, stage, action='run'):
        recipe = self.config['workers'][platform][stage]
        if stage == 'build':
            import shutil
            if shutil.disk_usage(self.state).free < self.config.get('minimum_free_bytes', 16 * 1024 ** 3):
                raise ValueError('release storage is below reserved headroom; export retained artifacts before retrying')
        effect_kind = stage if stage != 'observe' else 'observe-' + str(time.time_ns())
        if stage == 'acceptance' and 'max_age_seconds' in recipe:
            age = recipe['max_age_seconds']
            if type(age) is not int or not 60 <= age <= 3000:
                raise ValueError('acceptance max_age_seconds must be an integer from 60 to 3000')
            pointer = self.state / 'acceptance-effects' / manifest['release_id'] / (platform + '.json')
            if pointer.exists(): effect_kind = json.loads(pointer.read_text())['kind']
            previous = self.ledger.effect(manifest['release_id'], platform, effect_kind)
            receipt = self.state / 'jobs' / previous['id'] / 'receipt.json'
            if receipt.exists():
                proof, retained_digest = read_receipt(receipt, manifest, platform, stage)
                completed = proof.get('completed_at')
                if type(completed) is not int or completed > time.time():
                    raise ValueError('native acceptance completion time is invalid')
                if time.time() - completed > age:
                    # Only a completed attempt may expire. Unknown dispatches
                    # retain their request ID and reconcile. Old evidence stays.
                    self.ledger.complete_effect(previous['id'], str(proof.get('external_id', previous['id'])), retained_digest)
                    effect_kind = 'acceptance-after-' + previous['id']
                    atomic_json(pointer, {'kind': effect_kind})
        effect = self.ledger.effect(manifest['release_id'], platform, effect_kind)
        work = self.state / 'jobs' / effect['id']
        work.mkdir(parents=True, exist_ok=True)
        source = work / 'candidate.json'
        encoded = canonical(manifest)
        if source.exists() and source.read_bytes() != encoded:
            raise ValueError('worker input changed')
        if not source.exists():
            source.write_bytes(encoded)
        output = work / 'receipt.json'
        # A dispatch receipt is durable before the next polling cycle. On restart
        # its absence means an unknown external outcome, not permission to repeat.
        marker = work / 'attempted.json'
        if output.exists():
            report, digest = read_receipt(output, manifest, platform, stage)
            self.ledger.complete_effect(effect['id'], str(report.get('external_id', effect['id'])), digest)
            return report, digest
        mode = 'reconcile' if marker.exists() else action
        argv = recipe.get(mode)
        if not argv:
            raise ValueError('external outcome requires reconciliation: ' + stage)
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) for x in argv):
            raise ValueError('worker recipe must be an argv array')
        # A fixed environment contract keeps untrusted source and version strings
        # out of shell commands. No shell=True and no textual command expansion.
        environment = dict(os.environ, GCHAT_RELEASE_MANIFEST=str(source),
                           GCHAT_RELEASE_RECEIPT=str(output), GCHAT_RELEASE_TARGET=platform,
                           GCHAT_RELEASE_STAGE=stage, GCHAT_RELEASE_REQUEST_ID=effect['id'])
        atomic_json(marker, {'request_id': effect['id'], 'attempted': int(time.time())})
        with (work / (str(time.time_ns()) + '.log')).open('xb') as log:
            result = subprocess.run(argv, env=environment, cwd=work, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=recipe.get('timeout', 120))
        if result.returncode == 75:
            return None  # asynchronous job accepted/running; next cycle reconciles
        if result.returncode:
            raise ValueError(stage + ' worker failed; inspect retained worker log')
        report, digest = read_receipt(output, manifest, platform, stage)
        self.ledger.complete_effect(effect['id'], str(report.get('external_id', effect['id'])), digest)
        return report, digest

    def step(self, release, platform):
        manifest = self.ledger.manifest(release)
        target = self.ledger.target(release, platform)
        state = target['state']
        if state == 'blocked' and self.resume_corrected(release, platform, target):
            target = self.ledger.target(release, platform)
            state = target['state']
        if state in {'available', 'failed', 'superseded', 'blocked'}:
            return
        if platform not in self.config.get('workers', {}):
            self.ledger.transition(release, platform, 'blocked', reason='platform worker is not configured')
            return
        stage = None
        try:
            if state in {'verified', 'publishing', 'submitting'} and platform != 'sdk' and not self.deployment_ready(manifest):
                return
            if state == 'verified' and platform in {'ios', 'android'}:
                other = self.ledger.db.execute("""SELECT 1 FROM platforms WHERE platform=? AND candidate!=?
                    AND (state IN ('submitting','processing','in_review') OR
                    (state='blocked' AND resume_state IN ('submitting','processing','in_review')))""", (platform, release)).fetchone()
                if other: return  # retain the candidate while the current review finishes
            if state == 'queued':
                active = self.ledger.db.execute("""SELECT 1 FROM platforms
                    WHERE platform=? AND candidate!=? AND state IN ('building','verifying')""",
                    (platform, release)).fetchone()
                if active:
                    return  # Coalesce newer commits before dispatch; preserve frozen workers.
                self.ledger.transition(release, platform, 'building')
                state = 'building'
            stage = {'building': 'build', 'verifying': 'verify', 'verified': 'compatibility',
                     'publishing': 'publish', 'submitting': 'submit',
                     'processing': 'observe', 'in_review': 'observe'}[state]
            if state == 'verified' and 'acceptance' in self.config['workers'][platform]:
                stage = 'acceptance'
                if self.execute(manifest, platform, stage) is None:
                    return
                stage = 'compatibility'
            completed = self.execute(manifest, platform, stage)
            if completed is None:
                return
            report, evidence = completed
            if state == 'verified':
                if platform != 'sdk' and report.get('relay_compatible') is not True:
                    raise ValueError('compatible deployed relay receipt is missing')
                if platform == 'sdk' and report.get('consumers_compatible') is not True:
                    raise ValueError('SDK consumer compatibility receipt is missing')
                next_state = 'submitting' if platform in {'ios', 'android'} else 'publishing'
            else:
                next_state = {'building': 'verifying', 'verifying': 'verified',
                              'publishing': 'available'}.get(state)
                if next_state is None:
                    next_state = report.get('provider_state')
                    if next_state not in {'processing', 'in_review', 'available'}:
                        raise ValueError('provider did not report a supported terminal/progress state')
                    if next_state == state:
                        return
            self.ledger.transition(release, platform, next_state, evidence=evidence)
        except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
            # Do not emit provider bodies, command arguments or credentials into
            # the public status. Detailed worker logs stay in private state.
            message = str(error) if isinstance(error, ValueError) else type(error).__name__
            if stage is not None:
                self.record_failure(release, platform, stage, error)
            self.ledger.transition(release, platform, 'blocked', reason=message[:240])

    def tick(self):
        if self.config.get('discovery'):
            from release_discovery import discover
            try:
                discover(self.config['discovery'], self.state, self.ledger)
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                atomic_json(self.state / 'discovery-blocked.json', {'reason': type(error).__name__, 'at': int(time.time())})
        if self.config.get('maintenance'):
            from release_maintenance import maintain
            try:
                maintain(self.state, self.ledger, self.config['maintenance'])
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                atomic_json(self.state / 'maintenance-blocked.json', {'reason': type(error).__name__, 'at': int(time.time())})
        incoming = self.state / 'incoming'
        incoming.mkdir(exist_ok=True)
        for source in sorted(incoming.glob('*.json')):
            try:
                manifest = validate(json.loads(source.read_text()))
                self.ledger.add(manifest)
            except (ValueError, KeyError, TypeError):
                quarantine = self.state / 'rejected'
                quarantine.mkdir(exist_ok=True)
                os.replace(source, quarantine / (str(time.time_ns()) + '-' + source.name))
        self.ledger.coalesce()
        if self.config.get('discovery'):
            from release_discovery import coalesce_equivalent_queued
            try:
                coalesce_equivalent_queued(self.config['discovery'], self.ledger)
            except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
                atomic_json(self.state / 'coalescing-blocked.json',
                            {'reason': type(error).__name__, 'at': int(time.time())})
        rows = self.ledger.db.execute('SELECT candidate,platform FROM platforms ORDER BY rowid').fetchall()
        for row in rows:
            self.step(row['candidate'], row['platform'])
        self.reconcile_deployment()
        atomic_json(self.state / 'public/status.json', self.ledger.status())
        os.chmod(self.state / 'public/status.json', 0o644)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--resume', nargs=2, metavar=('RELEASE', 'PLATFORM'))
    args = parser.parse_args()
    # One coordinator owns this state; flock is released by the kernel on death.
    import fcntl
    args.state.mkdir(parents=True, exist_ok=True)
    with (args.state / 'coordinator.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        controller = Coordinator(args.state, json.loads(args.config.read_text()))
        try:
            if args.resume:
                release, platform = args.resume
                item = controller.ledger.target(release, platform)
                if item['state'] != 'blocked':
                    raise ValueError('only a blocked stage can be resumed')
                controller.ledger.transition(release, platform, item['resume_state'], evidence=item['evidence'])
            while True:
                controller.tick()
                if args.once:
                    break
                time.sleep(controller.poll_interval)
        finally:
            controller.ledger.close()


if __name__ == '__main__':
    main()
