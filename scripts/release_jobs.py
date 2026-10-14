#!/usr/bin/env python3
"""Dispatch once and reconcile exact-source GitHub workers by durable request ID."""
from release_provider import github_artifact, locked
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import time
import zipfile

from release_pair import canonical, validate
from release_coordinator import atomic_json

REPO = 'IggyGG/gchat'
WORKFLOWS = {'linux-x86_64': ('linux-release.yml', 'Forgejo Linux '), 'macos-aarch64': ('macos-release.yml', 'Forgejo macOS '),
             'macos-x86_64': ('macos-release.yml', 'Forgejo macOS '),
             'windows-x86_64': ('windows-release.yml', 'Forgejo Windows '),
             'android': ('android-release.yml', 'Forgejo Android '),
             'ios': ('ios-release.yml', 'Forgejo iOS ')}


def acceptance_archive(spec, destination):
    if not os.environ.get('GCHAT_ACCEPTANCE_RETAINED_ROOT'):
        return None
    from acceptance_delivery import copy_retained
    return copy_retained(spec, destination)


def gh(path, *, method='GET', body=None, refresh=False):
    from release_provider import github
    return github(path, repo=REPO, method=method, body=body, **({'refresh': True} if refresh else {}))


def extract(archive, destination):
    with zipfile.ZipFile(archive) as bundle:
        entries = bundle.infolist()
        if len(entries) > 200000 or sum(i.file_size for i in entries) > 12 * 1024 ** 3:
            raise ValueError('worker archive exceeds extraction budget')
        seen = set()
        for entry in entries:
            # ZipInfo normalizes host separators and truncates NULs; validate the
            # original archive spelling before the host filesystem sees it.
            original = entry.orig_filename
            path = PurePosixPath(original)
            if (path.is_absolute() or '..' in path.parts or '\\' in original or '\0' in original or
                ':' in original or path.as_posix() in seen or
                (entry.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError('unsafe worker archive path')
            seen.add(path.as_posix())
        bundle.extractall(destination)


def validate_run(run, expected, workflow, title, ident=None):
    if (not isinstance(run, dict) or type(run.get('id')) is not int or run['id'] <= 0
            or (ident is not None and run['id'] != ident)
            or run.get('head_sha') != expected or run.get('event') != 'workflow_dispatch'
            or run.get('display_title') != title
            or not isinstance(run.get('head_repository'), dict)
            or run.get('head_repository', {}).get('full_name') != REPO
            or run.get('path') != '.github/workflows/' + workflow):
        raise ValueError('worker run does not bind the requested source/workflow')


def resolve_run(manifest, target, work, request_id, api=None):
    api = gh if api is None else api
    workflow, prefix = WORKFLOWS[target]
    expected = manifest['sources']['gchat']['commit']
    run_path = work / 'run.json'
    binding = {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
               'platform': target, 'request_id': request_id}
    if run_path.exists():
        retained = json.loads(run_path.read_text())
        if (not isinstance(retained, dict) or type(retained.get('schema')) is not int
                or any(retained.get(k) != v for k, v in binding.items())
                or type(retained.get('id')) is not int or retained['id'] <= 0):
            raise ValueError('retained worker run binding changed')
        # A known run must never become an unseen dispatch merely because a
        # later workflow listing omits it. Missing IDs fail without redispatch.
        run = api(f'actions/runs/{retained["id"]}')
        validate_run(run, expected, workflow, prefix + request_id, retained['id'])
    else:
        matches = []
        # Discover a legacy/unseen request; never trust the newest run alone.
        for page in range(1, 11):
            runs = api(f'actions/workflows/{workflow}/runs?event=workflow_dispatch&per_page=100&page={page}')['workflow_runs']
            matches += [r for r in runs if r.get('display_title') == prefix + request_id]
            if len(runs) < 100 or matches: break
        if len(matches) > 1: raise ValueError('duplicate external request IDs require reconciliation')
        run = matches[0] if matches else None
        if run is not None:
            validate_run(run, expected, workflow, prefix + request_id)
            atomic_json(run_path, {**binding, 'id': run['id']})
    return run


# These are build workflows only. Store submission and encrypted acceptance
# requests have different side-effect contracts and are deliberately excluded.
NATIVE_JOBS = {'linux-x86_64': ('native-build', 'qualify', 'qualify-gcoms', 'relay-load', 'linux'),
               'macos-aarch64': ('macos (macos-aarch64)',), 'macos-x86_64': ('macos (macos-x86_64)',),
               'windows-x86_64': ('windows',), 'android': ('android',), 'ios': ('ios',)}
MAX_NATIVE_ATTEMPTS = 2
RETRY_AUTHORIZATION_SECONDS = 7200


def native_checks(run, target, work, api=None):
    """Select the newest execution of each job, never an older passing fallback."""
    api = gh if api is None else api
    attempt = run.get('run_attempt')
    if type(attempt) is not int or attempt < 1:
        raise ValueError('native provider attempt is invalid')
    if attempt > 10:
        raise ValueError('native job attempt history exceeds its bound')
    jobs = []
    for original_attempt in range(attempt, 0, -1):
        rows_for_attempt = []
        for page in range(1, 11):
            rows = api(f'actions/runs/{run["id"]}/attempts/{original_attempt}/jobs?per_page=100&page={page}')['jobs']
            if any(j.get('run_attempt') != original_attempt for j in rows):
                raise ValueError('native job attempt endpoint identity changed')
            rows_for_attempt.extend(rows)
            if len(rows) < 100: break
        else:
            raise ValueError('native job inventory exceeds its bound')
        if original_attempt == attempt and not rows_for_attempt:
            break  # Current attempt is not visible yet; never fall back to an old pass.
        jobs.extend(rows_for_attempt)
    selected = {}
    seen = set()
    for item in jobs:
        name, original = item.get('name'), item.get('run_attempt')
        valid_name = (name in NATIVE_JOBS[target] if target != 'sdk' else
                      isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9 ()_,.\-/]{1,160}', name))
        if (not valid_name or type(original) is not int or not 1 <= original <= attempt
                or type(item.get('run_id')) is not int or item.get('run_id') != run['id'] or item.get('head_sha') != run['head_sha']
                or type(item.get('id')) is not int or item['id'] <= 0 or (name, original) in seen):
            raise ValueError('native job source/run/attempt identity is invalid or ambiguous')
        seen.add((name, original))
        if name in selected and selected[name]['attempt'] > original: continue
        steps = item.get('steps', [])
        current = next((s for s in steps if s.get('status') == 'in_progress'), None)
        failed = next((s for s in steps if s.get('conclusion') in ('failure', 'cancelled', 'timed_out')), None)
        selected[name] = {'job_id': item['id'], 'attempt': original,
                          **{k: item.get(k) for k in ('status', 'conclusion', 'started_at', 'completed_at')},
                          'step': (failed or current or {}).get('name')}
    report = {'schema': 1, 'run_id': run['id'], 'workflow_commit': run['head_sha'],
              'run_attempt': attempt, 'status': run['status'], 'conclusion': run.get('conclusion'),
              'observed_at': int(time.time()), 'jobs': selected}
    atomic_json(work / 'native-checks.json', report)
    return report


def authorize_native_retry(manifest, target, work, request_id, operator_id):
    """Record operator intent only; the worker rechecks the actual provider jobs."""
    path = work / 'run.json'
    if target not in NATIVE_JOBS or not path.is_file(): return None
    run = json.loads(path.read_text())
    binding = {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
               'platform': target, 'request_id': request_id}
    if (type(run.get('schema')) is not int or any(run.get(k) != v for k, v in binding.items()) or type(run.get('id')) is not int
            or run['id'] <= 0):
        raise ValueError('native retry retained run binding changed')
    path = work / 'native-retry-authorization.json'
    binding['run_id'] = run['id']
    if path.exists():
        previous = json.loads(path.read_text())
        if any(previous.get(k) != v for k, v in binding.items()):
            raise ValueError('native retry authorization binding changed')
        return previous  # Another resume cannot rearm an already consumed retry.
    now = int(time.time())
    value = {**binding, 'operator_request_id': operator_id, 'authorized_at': now,
             'expires_at': now + RETRY_AUTHORIZATION_SECONDS, 'maximum_attempts': MAX_NATIVE_ATTEMPTS}
    atomic_json(path, value)
    return value


def retry_failed_jobs(manifest, target, work, request_id, run, checks, api=None):
    """At most one POST, durably recorded before I/O; unknown outcomes only reconcile."""
    api = gh if api is None else api
    authorization = work / 'native-retry-authorization.json'
    if not authorization.is_file(): return False
    with locked(work / 'native-retry.lock'):
        # A policy intent owns the same provider operation, including a lost
        # response. An operator resume cannot create a second POST alongside it.
        automatic = work / 'native-policy-retry.json'
        if automatic.is_file():
            retained = json.loads(automatic.read_text())
            if retained.get('run_id') != run['id']: raise ValueError('native policy retry run changed')
            if run['run_attempt'] <= retained['from_attempt']:
                if time.time() > retained['requested_at'] + 1800:
                    raise ValueError('native retry outcome remains unknown; original intent retained, no redispatch')
                return True
            return False
        grant = json.loads(authorization.read_text())
        binding = {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
                   'platform': target, 'request_id': request_id, 'run_id': run['id']}
        if (type(grant.get('schema')) is not int or any(grant.get(k) != v for k, v in binding.items())
                or grant.get('maximum_attempts') != MAX_NATIVE_ATTEMPTS
                or type(grant.get('authorized_at')) is not int
                or grant.get('expires_at') != grant['authorized_at'] + RETRY_AUTHORIZATION_SECONDS):
            raise ValueError('native retry authorization binding changed')
        marker = work / 'native-retry.json'
        if marker.exists():
            retained = json.loads(marker.read_text())
            if (any(retained.get(k) != v for k, v in binding.items())
                    or retained.get('authorization_sha256') != hashlib.sha256(authorization.read_bytes()).hexdigest()
                    or retained.get('from_attempt') != 1):
                raise ValueError('native retry intent binding changed')
            if run['run_attempt'] > retained['from_attempt']:
                if retained.get('state') != 'observed':
                    atomic_json(marker, {**retained, 'state': 'observed', 'observed_attempt': run['run_attempt']})
                return False
            if time.time() > retained['requested_at'] + 1800:
                raise ValueError('native retry outcome remains unknown; original intent retained, no redispatch')
            return True
        failed = {name: value for name, value in checks['jobs'].items()
                  if value['status'] == 'completed' and value['conclusion'] in ('failure', 'cancelled', 'timed_out')}
        if not failed: return False
        if run['status'] != 'completed': return True  # Preserve active/protected siblings.
        if run['run_attempt'] >= MAX_NATIVE_ATTEMPTS:
            raise ValueError('native failed-job retry limit reached; original failures retained')
        if time.time() > grant['expires_at']:
            raise ValueError('native failed-job retry authorization expired')
        # Bypass the metadata cache for the final compare-and-swap observation.
        fresh = api(f'actions/runs/{run["id"]}', refresh=True)
        workflow, prefix = WORKFLOWS[target]
        validate_run(fresh, manifest['sources']['gchat']['commit'], workflow, prefix + request_id, run['id'])
        if (type(fresh.get('run_attempt')) is not int or fresh.get('run_attempt') != run['run_attempt']
                or fresh.get('status') != 'completed'):
            return True
        if fresh.get('conclusion') not in ('failure', 'cancelled', 'timed_out'):
            return False
        value = {**binding, 'authorization_sha256': hashlib.sha256(authorization.read_bytes()).hexdigest(),
                 'operator_request_id': grant['operator_request_id'], 'from_attempt': run['run_attempt'],
                 'failed_jobs': failed, 'requested_at': int(time.time()), 'state': 'intent'}
        atomic_json(marker, value)
        api(f'actions/runs/{run["id"]}/rerun-failed-jobs', method='POST')
        atomic_json(marker, {**value, 'state': 'accepted'})
        return True


def require_passed_checks(checks, names):
    failed = [(name, checks['jobs'].get(name)) for name in names
              if checks['jobs'].get(name, {}).get('conclusion') in ('failure', 'cancelled', 'timed_out')]
    if failed:
        name, value = failed[0]
        raise ValueError(f'native check {name} {value["conclusion"]} (run {checks["run_id"]}, '
                         f'job {value["job_id"]}, attempt {value["attempt"]}); '
                         'resume authorizes one bounded failed-job retry')
    passed = all(checks['jobs'].get(name, {}).get('status') == 'completed' and
                 checks['jobs'][name]['conclusion'] == 'success' for name in names)
    if not passed and checks['status'] == 'completed':
        missing = [name for name in names if checks['jobs'].get(name, {}).get('conclusion') != 'success']
        raise ValueError('completed native workflow lacks required successful checks: ' + ', '.join(missing))
    return passed


def policy_retry(manifest, target, work, run, checks, diagnostics, *, repo=REPO, validate_fresh, api=None):
    """One policy-authorized failed-job retry, on the original immutable run.

    Shared SDK callers use the same source/matrix directory and lock. Neither a
    new GChat candidate nor a controller restart can rearm that provider run.
    """
    from release_provider import github
    from datetime import datetime
    api = (lambda path, **kwargs: github(path, repo=repo, **kwargs)) if api is None else api
    path = work / 'native-policy-retry.json'
    source = manifest['sources']['gcoms' if target == 'sdk' else 'gchat']['commit']
    binding = {'schema': 1, 'policy': 'native-transient-v1', 'repo': repo,
               'platform': target, 'run_id': run['id'], 'source': source, 'from_attempt': 1}
    with locked(work / 'native-retry.lock'):
        if path.is_file():
            retained = json.loads(path.read_text())
            if any(retained.get(k) != v for k, v in binding.items()):
                raise ValueError('native policy retry binding changed')
            if run['run_attempt'] > 1:
                if retained['state'] != 'observed':
                    atomic_json(path, {**retained, 'state': 'observed', 'observed_attempt': run['run_attempt']})
                return False
            if time.time() > retained['requested_at'] + 1800:
                raise ValueError('native policy retry outcome unknown; no redispatch')
            return True
        if ((work / 'native-retry.json').exists() or (work / 'native-retry-authorization.json').exists()
                or os.environ.get('GCHAT_RELEASE_NATIVE_RETRY_POLICY') != 'native-transient-v1'
                or os.environ.get('GCHAT_RELEASE_RECONCILE_ONLY') == '1'
                or run['run_attempt'] != 1 or run['status'] != 'completed'
                or diagnostics is None or diagnostics.get('native_retry_eligible') is not True):
            return False
        if (diagnostics.get('sources') != manifest['sources'] or diagnostics.get('run_id') != run['id']
                or diagnostics.get('run_attempt') != run['run_attempt'] or diagnostics.get('repo') != repo
                or diagnostics.get('platform') != target):
            raise ValueError('native policy diagnostics source/run changed')
        try:
            created = int(datetime.fromisoformat(run['created_at'].replace('Z', '+00:00')).timestamp())
        except (KeyError, ValueError, TypeError):
            return False  # Unknown original deadline cannot authorize a retry.
        deadline = created + RETRY_AUTHORIZATION_SECONDS
        if not created <= time.time() < deadline: return False
        fresh = api(f'actions/runs/{run["id"]}', refresh=True)
        validate_fresh(fresh)
        if fresh.get('run_attempt') != 1 or fresh.get('status') != 'completed': return True
        if fresh.get('conclusion') not in ('failure', 'timed_out', 'startup_failure'): return False
        from release_failure import failed_jobs, immutable
        proof = {'diagnostics': diagnostics, 'checks': checks}
        proof_sha = hashlib.sha256(canonical(proof)).hexdigest()
        immutable(work / 'native-policy-evidence' / (proof_sha + '.json'), proof)
        intent = {**binding, 'actor': 'policy', 'requested_at': int(time.time()), 'deadline_at': deadline,
                  'diagnostic_sha256': proof_sha, 'failed_jobs': failed_jobs(checks), 'state': 'intent'}
        atomic_json(path, intent)
        api(f'actions/runs/{run["id"]}/rerun-failed-jobs', method='POST')
        atomic_json(path, {**intent, 'state': 'accepted'})
        return True


def collect(manifest, target, work, request_id, reconcile=False):
    workflow, prefix = WORKFLOWS[target]
    marker = work / 'dispatch.json'
    expected = manifest['sources']['gchat']['commit']
    run = resolve_run(manifest, target, work, request_id)
    if run is None:
        if marker.exists():
            if marker.exists() and time.time() - json.loads(marker.read_text())['at'] > 1800:
                raise ValueError('worker dispatch not visible after 30 minutes; no blind resubmission')
            return None
        if os.environ.get('GCHAT_RELEASE_RECONCILE_ONLY') == '1':
            raise ValueError('build deadline expired before provider dispatch; original request retained')
        refs = manifest['refs']
        for project in ('gchat', 'gcoms'):
            ref_path = refs[project].removeprefix('refs/')
            try:
                from release_provider import github
                visible = github('git/ref/' + ref_path, repo='IggyGG/' + project)
            except subprocess.CalledProcessError:
                return None  # publication of the immutable companion ref is still pending
            if visible.get('object', {}).get('sha') != manifest['sources'][project]['commit']:
                raise ValueError('protected worker ref differs from frozen source')
        inputs = {'gchat_commit': expected, 'gcoms_commit': manifest['sources']['gcoms']['commit'],
                  'gchat_ref': refs['gchat'], 'gcoms_ref': refs['gcoms'], 'request_id': request_id,
                  'release_manifest': base64.b64encode(canonical(manifest)).decode()}
        if target.startswith('macos'): inputs['target'] = target
        if target == 'ios':
            inputs.update(build_number=manifest['versions']['ios'], upload_testflight=False)
        atomic_json(marker, {'at': int(time.time()), 'request_id': request_id, 'commit': expected})
        gh(f'actions/workflows/{workflow}/dispatches', method='POST', body={'ref': refs['gchat'].removeprefix('refs/heads/'), 'inputs': inputs})
        return None
    checks = native_checks(run, target, work)
    from release_failure import native_diagnostics, failed_jobs, WorkerFailure
    from release_provider import github_log
    diagnostic = reference = None
    if failed_jobs(checks):
        diagnostic, reference = native_diagnostics(manifest, target, work, run, checks, repo=REPO, download=github_log)
    retrying = policy_retry(manifest, target, work, run, checks, diagnostic,
        validate_fresh=lambda fresh: validate_run(fresh, expected, workflow, prefix + request_id, run['id']))
    retrying = retrying or retry_failed_jobs(manifest, target, work, request_id, run, checks)
    required = ('qualify', 'qualify-gcoms', 'linux') if target == 'linux-x86_64' else NATIVE_JOBS[target]
    if any(checks['jobs'].get(n, {}).get('conclusion') != 'success' for n in required):
        if retrying: return None
        if diagnostic:
            if run['status'] == 'completed' and os.environ.get('GCHAT_RELEASE_RECONCILE_ONLY') != '1':
                from release_recovery import registered, collect as collect_recovery
                if registered(manifest, target): return collect_recovery(manifest, target, work, run)
            raise WorkerFailure(diagnostic['code'], diagnostics=reference)
    if not require_passed_checks(checks, required): return None
    artifacts = gh(f'actions/runs/{run["id"]}/artifacts?per_page=100')['artifacts']
    name = target if target.startswith(('linux', 'macos', 'windows')) else f'{target}-{expected}-{manifest["sources"]["gcoms"]["commit"]}'
    if target == 'ios': name += '-' + manifest['versions']['ios']
    selected = [a for a in artifacts if a['name'] == name and not a['expired']]
    if len(selected) != 1: raise ValueError('exact native artifact is missing or ambiguous')
    artifact = selected[0]; digest = artifact.get('digest', '')
    if checks and (artifact.get('workflow_run', {}).get('id') != run['id'] or
                   artifact.get('workflow_run', {}).get('head_sha') != expected):
        raise ValueError('native artifact belongs to another run/source')
    if not re.fullmatch('sha256:[0-9a-f]{64}', digest): raise ValueError('provider artifact has no immutable digest')
    if not 0 < artifact['size_in_bytes'] <= 12 * 1024 ** 3:
        raise ValueError('native archive exceeds download budget')
    archive = work / 'native.zip'
    if not archive.exists():
        partial = work / 'native.partial'
        github_artifact(f'actions/artifacts/{artifact["id"]}/zip', repo=REPO, partial=partial,
                        size=artifact['size_in_bytes'], sha256=digest.removeprefix('sha256:'), timeout=600)
        with partial.open('rb') as stream: actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if 'sha256:' + actual != digest: raise ValueError('native artifact download hash mismatch')
        os.replace(partial, archive)
    with archive.open('rb') as stream: actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if 'sha256:' + actual != digest: raise ValueError('retained native archive changed')
    extracted = work / 'native'
    if not (work / 'extracted.json').exists():
        if extracted.exists():
            # Only our incomplete derived extraction, never retained source/profile.
            import shutil
            shutil.rmtree(extracted)
        extract(archive, extracted)
        atomic_json(work / 'extracted.json', {'sha256': actual})
    report = {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
              'platform': target, 'stage': 'build', 'passed': True, 'source_unchanged': True,
              'external_id': str(run['id']), 'evidence': [{'path': 'native.zip', 'sha256': actual}],
              'worker': {'url': run['html_url'], 'workflow_commit': expected, 'artifact_id': artifact['id']}}
    if checks:
        # Immutable receipt closure records which original job attempts passed.
        proof = work / 'native-checks-passed.json'
        atomic_json(proof, checks)
        report['evidence'].append({'path': proof.name, 'sha256': hashlib.sha256(proof.read_bytes()).hexdigest()})
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--reconcile', action='store_true')
    args = p.parse_args()
    manifest = validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()))
    output = Path(os.environ['GCHAT_RELEASE_RECEIPT']); work = output.parent
    result = collect(manifest, os.environ['GCHAT_RELEASE_TARGET'], work, os.environ['GCHAT_RELEASE_REQUEST_ID'], args.reconcile)
    if result is None: raise SystemExit(75)
    atomic_json(output, result)


if __name__ == '__main__':
    from release_provider import worker_main
    worker_main(main)
