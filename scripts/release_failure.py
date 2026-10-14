"""Source-bound, private failure evidence and conservative public classifications.

A diagnostic is never an application qualification receipt. Log text remains
private; public status uses fixed descriptions and numeric provider identities.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid
import zipfile

from release_pair import canonical

CATEGORIES = {'infrastructure', 'code', 'operator', 'unclassified'}
DESCRIPTIONS = {
    'native_check_failed': ('code', 'Native qualification failed; repair the recorded failed job.'),
    'native_posix_import': ('code', 'Portable native tooling imports the POSIX-only fcntl module on Windows.'),
    'native_runner_unavailable': ('infrastructure', 'The native runner or its infrastructure was unavailable.'),
    'native_operator_action': ('operator', 'Native signing or account configuration needs operator attention.'),
    'native_diagnostics_pending': ('unclassified', 'Native qualification failed; original job diagnostics are pending.'),
    'native_log_truncated': ('unclassified', 'Native qualification failed; inspect the original full provider log.'),
    'native_failure_unknown': ('unclassified', 'Native qualification failed; inspect the recorded job and retained log.'),
    'worker_timeout': ('infrastructure', 'Worker observation timed out; reconcile the original request.'),
    'provider_unavailable': ('infrastructure', 'Provider temporarily unavailable; reconcile the original request.'),
    'store_action_required': ('operator', 'Store account or authorization requires operator attention; preserve the original submission.'),
    'provider_outcome_unknown': ('unclassified', 'Provider outcome requires reconciliation of the original request; do not resubmit it.'),
    'worker_failed': ('unclassified', 'Worker failed; inspect the retained execution log.'),
}


class WorkerFailure(ValueError):
    def __init__(self, code, *, diagnostics=None, reconcile_retry=False):
        if code not in DESCRIPTIONS: raise ValueError('unknown worker failure code')
        self.code = code
        self.category, message = DESCRIPTIONS[code]
        self.diagnostics = diagnostics
        self.reconcile_retry = reconcile_retry
        super().__init__(message)


def immutable(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    raw = canonical(value)
    if path.exists():
        if path.is_symlink() or path.read_bytes() != raw:
            raise ValueError('retained diagnostic evidence changed')
        return
    with path.open('xb') as stream:
        os.chmod(path, 0o600)
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def classify_native_log(text, *, complete):
    """Only positive infrastructure evidence permits a native retry.

    A truncated log or actual test/compiler failure never becomes a transient
    merely because a fixture or dependency message mentions a network error.
    """
    text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)
    if any(len(line) > 16384 for line in text.splitlines()):
        return 'native_log_truncated'
    if "ModuleNotFoundError: No module named 'fcntl'" in text:
        return 'native_posix_import'
    if re.search(r'(?im)(test result: FAILED|^\s*FAILED\s|^FAIL(?:ED)?:\s|^ERROR:\s|AssertionError|error\[E\d+\]|error: (?:could not compile|failed to compile|test failed)|\bFAILURES?={1}\d|FAILED \([^\n]*(?:failures|errors)=|Test (?:Case|Suite) [^\n]+ failed)', text):
        return 'native_check_failed'
    if re.search(r'(?im)(no signing certificate|signing certificate.*expired|provisioning profile.*(?:not found|expired)|resource not accessible by integration|invalid client secret|authentication credentials.*(?:invalid|missing))', text):
        return 'native_operator_action'
    if not complete: return 'native_log_truncated'
    infrastructure = (
        r'(?im)^.*##\[error\].*(?:hosted runner lost communication with the server|runner has received a shutdown signal|runner unexpectedly disconnected)',
        r'(?im)^.*##\[error\].*(?:failed to download action|unable to download action).*(?:502|503|504|timed out|connection reset)',
        r'(?im)^.*##\[error\].*(?:runner service|hosted runner).*(?:unavailable|internal server error)',
    )
    return 'native_runner_unavailable' if any(re.search(pattern, text) for pattern in infrastructure) else 'native_failure_unknown'


def read_json(path, limit=65536):
    if path.is_symlink(): raise ValueError('diagnostic JSON must not be a link')
    with path.open('rb') as stream: raw = stream.read(limit + 1)
    if len(raw) > limit: raise ValueError('diagnostic JSON exceeds its bound')
    return json.loads(raw)


def read_log(path):
    if path.is_symlink(): raise ValueError('diagnostic log must not be a link')
    with path.open('rb') as stream: raw = stream.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024: raise ValueError('diagnostic log exceeds its retained bound')
    return raw


def failed_jobs(checks):
    return {name: job for name, job in checks.get('jobs', {}).items()
            if job.get('status') == 'completed' and job.get('conclusion') in
             ('failure', 'cancelled', 'timed_out', 'startup_failure')}


def artifact_names(manifest, platform, run, checks):
    """Known evidence exporters only; a new archive spelling needs review."""
    if platform.startswith(('macos', 'windows', 'linux')): return {platform}
    if platform in ('ios', 'android'):
        name = platform + '-' + manifest['sources']['gchat']['commit'] + '-' + manifest['sources']['gcoms']['commit']
        return {name + '-' + manifest['versions']['ios'] if platform == 'ios' else name}
    source = manifest['sources']['gcoms']['commit']
    names = set()
    for name, job in failed_jobs(checks).items():
        match = re.fullmatch(r'intel-consumers \((embedded|network-client|ipc)\)', name)
        if match: names.add(f'rust-integrations-intel-{match[1]}-{source}-{job["attempt"]}')
        match = re.fullmatch(r'native \((ubuntu-24\.04|macos-15|macos-15-intel|windows-2022)\)', name)
        if match: names.add(f'native-backend-{match[1]}-{source}-{job["attempt"]}')
        match = re.fullmatch(r'(android|apple) \((client|relay)\)', name)
        if match:
            names.update(f'mobile-{match[1]}-{match[2]}-{variant}-{source}' for variant in ('base', 'push'))
    return names


def archive_diagnostics(manifest, platform, work, run, checks, *, repo, api=None, download=None):
    """Inspect bounded child logs when a wrapper hides the actual failing check.

    Archives and member bytes stay private and immutable. Nothing is extracted
    to archive-supplied paths, executed, or accepted as passing qualification.
    Child evidence may refine a failure, never authorize a native retry.
    """
    from release_provider import github, github_download
    api = (lambda path: github(path, repo=repo)) if api is None else api
    download = github_download if download is None else download
    names = artifact_names(manifest, platform, run, checks)
    artifacts = api(f'actions/runs/{run["id"]}/artifacts?per_page=100')['artifacts']
    selected = [a for a in artifacts if a.get('name') in names and a.get('expired') is False]
    if len(selected) > 8 or len({a['name'] for a in selected}) != len(selected):
        raise ValueError('diagnostic artifact inventory is ambiguous or exceeds bound')
    root = Path(work) / 'native-diagnostics' / str(run['id']) / str(run['run_attempt']) / 'artifacts'
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    evidence = []
    total = 0
    for artifact in selected:
        sha = str(artifact.get('digest', '')).removeprefix('sha256:')
        size = artifact.get('size_in_bytes')
        if (type(artifact.get('id')) is not int or artifact['id'] <= 0
                or artifact.get('workflow_run', {}).get('id') != run['id']
                or artifact.get('workflow_run', {}).get('head_sha') != run['head_sha']
                or not re.fullmatch('[0-9a-f]{64}', sha) or type(size) is not int or size <= 0):
            raise ValueError('diagnostic artifact does not bind the original run/source')
        if total + size > 256 * 1024 * 1024:
            evidence.append({'artifact_id': artifact['id'], 'sha256': sha, 'state': 'archive_exceeds_diagnostic_budget'})
            continue
        total += size
        path = root / (sha + '.zip')
        if not path.is_file():
            import shutil
            if shutil.disk_usage(root).free < 16 * 1024 ** 3 + size:
                evidence.append({'artifact_id': artifact['id'], 'sha256': sha, 'state': 'waiting_storage_headroom'})
                continue
            partial = root / (sha + '-' + uuid.uuid4().hex + '.partial')
            with partial.open('wb') as stream:
                os.chmod(partial, 0o600)
                download(f'actions/artifacts/{artifact["id"]}/zip', repo=repo, stream=stream, timeout=180,
                         private_diagnostic=True, maximum_bytes=size)
            if partial.stat().st_size != size:
                raise ValueError('diagnostic archive size differs from provider inventory')
            with partial.open('rb') as stream: digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if digest != sha: raise ValueError('diagnostic archive hash differs from original run')
            if path.exists():
                partial.unlink()  # Concurrent source-identical diagnostics share the verified archive below.
            else:
                os.replace(partial, path)
        if path.is_symlink() or path.stat().st_size != size:
            raise ValueError('retained diagnostic archive changed')
        with path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != sha: raise ValueError('retained diagnostic archive changed')
        members = []
        with zipfile.ZipFile(path) as archive:
            if len(archive.infolist()) > 10000: raise ValueError('diagnostic archive member inventory exceeds bound')
            logs = [m for m in archive.infolist() if m.filename.endswith(('.log', '.stderr')) and not m.is_dir()]
            logs.sort(key=lambda m: m.filename)
            for member in logs[:32]:
                with archive.open(member) as stream: raw = stream.read(512 * 1024 + 1)
                truncated = len(raw) > 512 * 1024 or member.file_size > 512 * 1024
                raw = raw[:512 * 1024]
                digest = hashlib.sha256(raw).hexdigest()
                retained = root / (digest + '.log')
                if not retained.exists():
                    with retained.open('xb') as stream: os.chmod(retained, 0o600); stream.write(raw)
                if retained.is_symlink() or read_log(retained) != raw: raise ValueError('retained diagnostic member changed')
                members.append({'member': member.filename[:512], 'sha256': digest, 'truncated': truncated,
                                'log': str(retained.relative_to(work)),
                                'code': classify_native_log(raw.decode('utf-8', errors='replace'), complete=not truncated)})
        evidence.append({'artifact_id': artifact['id'], 'sha256': sha, 'state': 'retained',
                         'archive': str(path.relative_to(work)), 'members': members})
    return evidence


def native_diagnostics(manifest, platform, work, run, checks, *, repo, download):
    from release_provider import atomic, ProviderWait
    work = Path(work)
    expected_repo = 'IggyGG/gcoms' if platform == 'sdk' else 'IggyGG/gchat'
    source = manifest['sources']['gcoms' if platform == 'sdk' else 'gchat']['commit']
    if (repo != expected_repo or run.get('head_sha') != source
            or type(run.get('id')) is not int or run['id'] <= 0
            or checks.get('run_id') != run['id'] or checks.get('workflow_commit') != source
            or checks.get('run_attempt') != run.get('run_attempt')):
        raise ValueError('native diagnostics do not bind the original source/run')
    directory = work / 'native-diagnostics' / str(run['id']) / str(checks['run_attempt'])
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    evidence = []
    jobs = []
    for name, job in failed_jobs(checks).items():
        ident = job['job_id']
        if type(ident) is not int or ident <= 0: raise ValueError('invalid diagnostic job identity')
        marker = directory / (str(ident) + '.json')
        detail = None
        if marker.exists():
            detail = read_json(marker)
            if (not isinstance(detail.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', detail['sha256'])
                    or detail.get('file') != detail['sha256'] + '.log'
                    or type(detail.get('truncated')) is not bool):
                raise ValueError('invalid retained diagnostic log identity')
            path = directory / detail['file']
            if (path.name != detail['sha256'] + '.log' or path.is_symlink()
                    or hashlib.sha256(read_log(path)).hexdigest() != detail['sha256']):
                raise ValueError('retained native diagnostic log changed')
        if detail is None:
            try:
                raw, truncated = download(f'actions/jobs/{ident}/logs', repo=repo)
                if len(raw) > 4 * 1024 * 1024: raise ValueError('native diagnostic downloader exceeded its bound')
                digest = hashlib.sha256(raw).hexdigest()
                path = directory / (digest + '.log')
                if path.exists():
                    if path.is_symlink() or read_log(path) != raw: raise ValueError('diagnostic log collision')
                else:
                    with path.open('xb') as stream:
                        os.chmod(path, 0o600); stream.write(raw)
                detail = {'file': path.name, 'sha256': digest, 'truncated': truncated}
                immutable(marker, detail)
            except (ProviderWait, OSError, TimeoutError, subprocess.SubprocessError) as error:
                jobs.append({**job, 'name': name, 'code': 'native_diagnostics_pending',
                             'diagnostic_error': type(error).__name__})
                continue
        text = read_log(path).decode('utf-8', errors='replace')
        code = classify_native_log(text, complete=not detail['truncated'])
        # Human cancellation is not permission for an automatic re-dispatch.
        if job.get('conclusion') == 'cancelled': code = 'native_failure_unknown'
        jobs.append({**job, 'name': name, 'code': code,
                     'log': str(path.relative_to(work)), 'log_sha256': detail['sha256'],
                     'truncated': detail['truncated']})
        evidence.append({'path': str(path.relative_to(work)), 'sha256': detail['sha256']})
    if not jobs: raise ValueError('native diagnostic request has no failed jobs')
    codes = {job['code'] for job in jobs}
    child_evidence = []
    # A runner's terminal wrapper error is not its nested compiler/test cause.
    # Only the GET-only diagnostic worker enriches archives, keeping ordinary
    # native collection lightweight and its original deadlines unchanged.
    if os.environ.get('GCHAT_RELEASE_STAGE') == 'diagnose' and codes & {'native_failure_unknown', 'native_log_truncated'}:
        try:
            child_evidence = archive_diagnostics(manifest, platform, work, run, checks, repo=repo)
            child_codes = {m['code'] for a in child_evidence for m in a.get('members', [])
                           if DESCRIPTIONS[m['code']][0] in ('code', 'operator')}
            codes.update(child_codes)
        except (ProviderWait, OSError, TimeoutError, subprocess.SubprocessError) as error:
            child_evidence = [{'state': 'pending', 'error_type': type(error).__name__}]
    order = ('native_operator_action', 'native_posix_import', 'native_check_failed', 'native_diagnostics_pending',
             'native_log_truncated', 'native_failure_unknown', 'native_runner_unavailable')
    code = next(value for value in order if value in codes)
    report = {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
              'platform': platform, 'repo': repo, 'run_id': run['id'],
              'request_type': run.get('event'),
              'workflow_commit': source, 'run_attempt': checks['run_attempt'],
              'workflow_status': run['status'], 'code': code, 'category': DESCRIPTIONS[code][0],
              'native_retry_eligible': codes == {'native_runner_unavailable'} and run['status'] == 'completed',
              'diagnostics_pending': ('native_diagnostics_pending' in codes or
                  any(a['state'] in ('pending', 'waiting_storage_headroom') for a in child_evidence)),
              'jobs': jobs, 'evidence': evidence, 'child_evidence': child_evidence}
    digest = hashlib.sha256(canonical(report)).hexdigest()
    path = directory / (digest + '.json')
    immutable(path, report)
    from release_provider import locked
    with locked(work / 'native-failure.lock'):
        previous = retained_diagnostics(work, manifest, platform)
        old = previous[0] if previous else {}
        older_attempt = old.get('run_id') == run['id'] and old.get('run_attempt', 0) > checks['run_attempt']
        displaced_push = platform == 'sdk' and old.get('request_type') == 'workflow_dispatch' and run.get('event') == 'push'
        if not older_attempt and not displaced_push:
            atomic(work / 'native-failure.json', {'path': str(path.relative_to(work)), 'sha256': digest})
    return report, {'path': str(path.relative_to(work)), 'sha256': digest}


def retain_worker_failure(error):
    """Called at a worker boundary; preserve one report per actual execution."""
    source = os.environ.get('GCHAT_RELEASE_MANIFEST')
    output = os.environ.get('GCHAT_RELEASE_RECEIPT')
    execution = os.environ.get('GCHAT_RELEASE_EXECUTION_ID')
    if not source or not output or not execution: return
    if not re.fullmatch(r'[0-9a-f-]+\.log', execution):
        raise ValueError('invalid failure execution identity')
    manifest = json.loads(Path(source).read_text())
    from release_pair import validate
    validate(manifest)
    work = Path(output).parent
    request = os.environ['GCHAT_RELEASE_REQUEST_ID']
    if not re.fullmatch('[0-9a-f]{64}', request) or work.name != request:
        raise ValueError('worker failure request identity differs')
    code = error.code if isinstance(error, WorkerFailure) else (
        'worker_timeout' if isinstance(error, (TimeoutError, subprocess.TimeoutExpired)) else
        'provider_unavailable' if isinstance(error, ConnectionError) else 'worker_failed')
    from release_stores import ProviderError
    if isinstance(error, ProviderError):
        code = ('provider_unavailable' if error.transient else 'store_action_required' if error.status in (401, 403)
                else 'provider_outcome_unknown')
    category, description = DESCRIPTIONS[code]
    report = {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
              'platform': os.environ['GCHAT_RELEASE_TARGET'], 'stage': os.environ['GCHAT_RELEASE_STAGE'],
              'request_id': request, 'execution_id': execution, 'at': int(time.time()),
              'code': code, 'category': category, 'summary': description,
              'reconcile_retry': (error.reconcile_retry if isinstance(error, WorkerFailure) else
                                  code in ('worker_timeout', 'provider_unavailable')),
              'diagnostics': error.diagnostics if isinstance(error, WorkerFailure) else None}
    digest = hashlib.sha256(canonical(report)).hexdigest()
    immutable(work / 'failures' / (digest + '.json'), report)
    from release_provider import atomic
    atomic(work / 'worker-failure.json', {'sha256': digest})


def read_worker_failure(work, manifest, platform, stage, execution):
    work = Path(work)
    pointer = work / 'worker-failure.json'
    if not pointer.exists(): return None
    value = read_json(pointer)
    digest = value.get('sha256', '')
    if not re.fullmatch('[0-9a-f]{64}', digest): raise ValueError('invalid worker failure digest')
    path = work / 'failures' / (digest + '.json')
    with path.open('rb') as stream: raw = stream.read(65537)
    if path.is_symlink() or len(raw) > 65536 or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('worker failure evidence changed')
    report = json.loads(raw)
    if report.get('execution_id') != execution: return None
    expected = {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
                'platform': platform, 'stage': stage, 'request_id': work.name}
    if (any(report.get(k) != v for k, v in expected.items()) or not isinstance(report.get('code'), str)
            or report['code'] not in DESCRIPTIONS or type(report.get('reconcile_retry')) is not bool):
        raise ValueError('worker failure is not bound to this stage')
    category, summary = DESCRIPTIONS[report['code']]
    if report.get('category') != category or report.get('summary') != summary:
        raise ValueError('worker failure classification changed')
    if report['reconcile_retry'] and report['code'] not in ('worker_timeout', 'provider_unavailable'):
        raise ValueError('failure does not authorize reconciliation retry')
    return report


def retained_diagnostics(work, manifest, platform):
    """Verify a private diagnostic pointer, never treat it as a passing gate."""
    pointer = Path(work) / 'native-failure.json'
    if not pointer.is_file(): return None
    ref = read_json(pointer)
    relative = Path(ref.get('path', ''))
    root = Path(work).resolve()
    path = (root / relative).resolve()
    if (relative.is_absolute() or not path.is_relative_to(root)
            or not re.fullmatch('[0-9a-f]{64}', str(ref.get('sha256')))):
        raise ValueError('native diagnostic reference escapes worker')
    with path.open('rb') as stream: raw = stream.read(512 * 1024 + 1)
    if len(raw) > 512 * 1024 or hashlib.sha256(raw).hexdigest() != ref['sha256']:
        raise ValueError('native diagnostic evidence changed')
    report = json.loads(raw)
    # SDK runs are shared by companion source across app candidates. Never
    # relabel their original release/source provenance; compare the SDK source.
    bound = (report.get('sources', {}).get('gcoms') == manifest['sources']['gcoms'] if platform == 'sdk'
             else report.get('sources') == manifest['sources'] and report.get('release_id') == manifest['release_id'])
    if not bound or report.get('platform') != platform or report.get('code') not in DESCRIPTIONS:
        raise ValueError('native diagnostic source binding changed')
    return report, ref


def diagnostic_identity(state, manifest, platform):
    request = hashlib.sha256(canonical([manifest['release_id'], platform, 'build'])).hexdigest()
    roots = [Path(state) / 'jobs' / request]
    if platform == 'sdk':
        roots = [Path(state) / 'sdk-cache' / manifest['sources']['gcoms']['commit'] / kind
                 for kind in ('rust', 'mobile-base', 'mobile-push')]
    runs = []
    for root in roots:
        result = retained_diagnostics(root, manifest, platform)
        if result:
            report, _ = result
            runs.append((report['repo'], report['run_id'], report['run_attempt']))
    return hashlib.sha256(canonical(sorted(runs))).hexdigest()


def diagnose(manifest, platform, state, output):
    """GET-only follow-up for retained failures, including legacy controllers."""
    from release_coordinator import atomic_json
    from release_jobs import resolve_run, native_checks
    from release_provider import github_log
    state, output = Path(state), Path(output)
    request = hashlib.sha256(canonical([manifest['release_id'], platform, 'build'])).hexdigest()
    work = state / 'jobs' / request
    reports = []
    if platform == 'sdk':
        from release_sdk import JOBS, observe_run, native_failure
        commit = manifest['sources']['gcoms']['commit']
        for kind in JOBS:
            shared = state / 'sdk-cache' / commit / kind
            shared.mkdir(parents=True, exist_ok=True)
            run = observe_run(shared, kind, commit)
            if run and run['conclusion'] not in (None, 'success'):
                report, ref = native_failure(manifest, shared, kind, run, retry=False)
                if report: reports.append({'matrix': kind, 'report': report, 'reference': ref})
    else:
        run = resolve_run(manifest, platform, work, request)
        if run:
            checks = native_checks(run, platform, work)
            if failed_jobs(checks):
                report, ref = native_diagnostics(manifest, platform, work, run, checks,
                                                repo='IggyGG/gchat', download=github_log)
                reports.append({'report': report, 'reference': ref})
    result = {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
              'platform': platform, 'reports': reports, 'observed_at': int(time.time()),
              'diagnostics_pending': not reports or any(r['report']['diagnostics_pending'] for r in reports)}
    digest = hashlib.sha256(canonical(result)).hexdigest()
    name = 'diagnosis-' + digest + '.json'
    immutable(output.parent / name, result)
    atomic_json(output.parent / 'diagnosis.json', result)
    if result['diagnostics_pending']: return None
    return {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
            'platform': platform, 'stage': 'diagnose', 'passed': True, 'source_unchanged': True,
            'scope': 'diagnostics_only', 'evidence': [{'path': name, 'sha256': digest}]}


def main():
    import argparse
    from release_pair import validate
    from release_coordinator import atomic_json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    args = parser.parse_args()
    manifest = validate(read_json(Path(os.environ['GCHAT_RELEASE_MANIFEST'])))
    if os.environ['GCHAT_RELEASE_STAGE'] != 'diagnose': raise ValueError('diagnostic worker stage changed')
    output = Path(os.environ['GCHAT_RELEASE_RECEIPT'])
    report = diagnose(manifest, os.environ['GCHAT_RELEASE_TARGET'], args.state, output)
    if report is None: raise SystemExit(75)
    atomic_json(output, report)


if __name__ == '__main__':
    from release_provider import worker_main
    worker_main(main)
