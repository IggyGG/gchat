"""Durable, bounded provider waits; never authorize another external mutation."""
from contextlib import contextmanager
from functools import lru_cache
from email.utils import parsedate_to_datetime
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time
import uuid

PROVIDERS = ('github', 'play', 'apple')
QUOTA_MIN = 900
QUOTA_MAX = 21600


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.' + path.name + '-' + uuid.uuid4().hex)
    try:
        with temporary.open('x') as stream:
            json.dump(value, stream, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        if os.name != 'nt':
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        if os.name == 'nt':
            import msvcrt
            if stream.tell() == 0:
                stream.write(b'0'); stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == 'nt':
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def read(path):
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return None


def state_root():
    value = os.environ.get('GCHAT_RELEASE_PROVIDER_STATE')
    return Path(value) if value else None


class ProviderWait(RuntimeError):
    def __init__(self, value):
        self.value = value
        super().__init__(f'{value["provider"]} provider quota; next check at {value["next_poll_at"]}')


def cooldown(root, provider, now=None):
    if root is None:
        return None
    now = int(time.time()) if now is None else now
    value = read(Path(root) / (provider + '.json'))
    if value is None:
        return None
    if (value.get('schema') != 1 or value.get('provider') != provider
            or type(value.get('next_poll_at')) is not int
            or type(value.get('observed_at')) is not int
            or value['next_poll_at'] < value['observed_at']):
        raise ValueError('provider cooldown identity is invalid')
    return value if now < value['next_poll_at'] else None


def before_request(provider):
    value = cooldown(state_root(), provider)
    if value:
        raise ProviderWait(value)


def reset_after_success(provider):
    root = state_root()
    if root is None:
        return
    with locked(root / (provider + '.lock')):
        value = read(root / (provider + '.json'))
        # A concurrent successful request cannot erase a newer quota response.
        if value and value['next_poll_at'] <= int(time.time()):
            (root / (provider + '.json')).unlink(missing_ok=True)


def retry_time(headers, now):
    headers = {k.lower(): str(v) for k, v in headers.items()}
    values = [now]
    retry = headers.get('retry-after', '')
    try:
        values.append(now + max(0, int(retry)))
    except ValueError:
        try:
            values.append(int(parsedate_to_datetime(retry).timestamp()))
        except (ValueError, TypeError, OverflowError):
            pass
    try:
        values.append(int(headers.get('x-ratelimit-reset', '')) + 1)
    except ValueError:
        pass
    return max(values)


def quota(provider, status, headers, reason):
    if provider not in PROVIDERS or reason not in ('rate_limit', 'listing_quota'):
        raise ValueError('unsupported provider quota')
    root = state_root()
    now = int(time.time())
    def value(previous):
        attempts = min(32, int((previous or {}).get('attempts', 0)) + 1)
        delay = min(QUOTA_MAX, QUOTA_MIN * 2 ** min(attempts - 1, 5))
        delay = min(QUOTA_MAX, delay + random.SystemRandom().randint(0, max(1, delay // 10)))
        return {'schema': 1, 'provider': provider, 'reason': reason, 'http_status': status,
                'observed_at': now, 'attempts': attempts,
                'next_poll_at': max(now + delay, retry_time(headers, now),
                                    (previous or {}).get('next_poll_at', 0))}
    if root is None:
        result = value(None)
    else:
        with locked(root / (provider + '.lock')):
            result = value(read(root / (provider + '.json')))
            atomic(root / (provider + '.json'), result)
    raise ProviderWait(result)


def classify(provider, method, path, status, headers, body):
    """Only known quota responses qualify; an ordinary 403 remains an error."""
    normalized = {k.lower(): str(v) for k, v in headers.items()}
    if status == 429 or (provider == 'github' and status == 403 and
            (normalized.get('x-ratelimit-remaining') == '0' or 'retry-after' in normalized)):
        quota(provider, status, headers, 'rate_limit')
    error = body.get('error', {}) if isinstance(body, dict) else {}
    if (provider == 'play' and method == 'GET' and path.startswith('/tracks/')
            and path.endswith('/releases') and status == 403
            and error.get('status') == 'PERMISSION_DENIED'
            and error.get('message') == 'Listing releases quota exceeded.'):
        quota(provider, status, headers, 'listing_quota')


def github(path, *, repo, method='GET', body=None, refresh=False):
    """Preserve response headers without logging provider bodies or credentials."""
    before_request('github')
    root = state_root()
    key = hashlib.sha256(json.dumps([repo, path]).encode()).hexdigest()
    cache = root / 'cache' / (key + '.json') if root and method == 'GET' and path.startswith('actions/') else None
    if cache and not refresh:
        value = read(cache)
        if value and value.get('repo') == repo and value.get('path') == path and 0 <= time.time() - value['at'] < 120:
            return value['response']
    command = ['gh', 'api', '--include', '--method', method, 'repos/' + repo + '/' + path]
    if body is not None:
        command += ['--input', '-']
    payload = None if body is None else json.dumps(body, sort_keys=True, separators=(',', ':')).encode()
    result = subprocess.run(command, input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw = result.stdout.replace(b'\r\n', b'\n')
    header, separator, content = raw.partition(b'\n\n')
    headers = {}
    status = 0
    if separator and header.startswith(b'HTTP/'):
        status = int(header.splitlines()[0].split()[1])
        headers = {line.split(b':', 1)[0].decode().lower(): line.split(b':', 1)[1].decode().strip()
                   for line in header.splitlines()[1:] if b':' in line}
    else:
        content = raw
    try:
        decoded = json.loads(content) if content.strip() else None
    except (ValueError, UnicodeDecodeError):
        decoded = None
    classify('github', method, path, status, headers, decoded)
    if status in (502, 503, 504):
        from release_failure import WorkerFailure
        raise WorkerFailure('provider_unavailable', reconcile_retry=True)
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, command, stderr=result.stderr)
    reset_after_success('github')
    decoded = json.loads(content) if content.strip() else None
    if cache:
        atomic(cache, {'repo': repo, 'path': path, 'at': int(time.time()), 'response': decoded})
    return decoded


def worker_main(main):
    try:
        main()
    except ProviderWait as error:
        output = os.environ.get('GCHAT_RELEASE_RECEIPT')
        source = os.environ.get('GCHAT_RELEASE_MANIFEST')
        if output and source:
            manifest = json.loads(Path(source).read_text())
            atomic(Path(output).parent / 'provider-wait.json', {
                **error.value, 'release_id': manifest['release_id'],
                'request_id': os.environ['GCHAT_RELEASE_REQUEST_ID'],
                'platform': os.environ['GCHAT_RELEASE_TARGET'],
                'stage': os.environ['GCHAT_RELEASE_STAGE']})
        print(str(error))
        raise SystemExit(75)
    except Exception as error:
        from release_failure import retain_worker_failure
        try:
            retain_worker_failure(error)
        except (ValueError, OSError, KeyError):
            # Keep the original error/exit and private log even if diagnostics
            # cannot be retained. Missing classification never authorizes retry.
            print('Structured worker failure could not be retained', file=sys.stderr)
        raise


def recipe_provider(recipe, platform):
    if recipe.get('provider') in PROVIDERS:
        return recipe['provider']
    names = {Path(arg).name for arg in recipe.get('run', [])}
    if names & {'release_jobs.py', 'release_sdk.py', 'release_acceptance.py', 'release_relay_load.py', 'release_failure.py'}:
        return 'github'
    if 'release_store_worker.py' in names:
        return 'play' if platform == 'android' else 'apple'
    return None


def schedule_path(state, release, platform, stage):
    return Path(state) / 'provider-schedule' / release / platform / (stage + '.json')


def schedule(state, release, platform, stage):
    value = read(schedule_path(state, release, platform, stage))
    if value and (value.get('schema') != 1 or value.get('release_id') != release
                  or value.get('platform') != platform or value.get('stage') != stage
                  or type(value.get('next_poll_at')) is not int):
        raise ValueError('provider polling schedule identity is invalid')
    return value


def defer_effect(state, release, platform, stage, request, provider, interval, wait=None):
    now = int(time.time())
    value = {'schema': 1, 'release_id': release, 'platform': platform, 'stage': stage,
             'request_id': request, 'provider': provider, 'observed_at': now,
             'next_poll_at': now + interval, 'reason': 'poll_interval'}
    if wait:
        if any(wait.get(k) != value[k] for k in ('release_id', 'platform', 'stage', 'request_id', 'provider')):
            raise ValueError('provider wait belongs to a different operation')
        if (wait.get('reason') not in ('rate_limit', 'listing_quota')
                or wait.get('http_status') not in (403, 429)
                or type(wait.get('observed_at')) is not int or type(wait.get('next_poll_at')) is not int
                or not 0 <= wait['observed_at'] <= now
                or wait['next_poll_at'] < wait['observed_at']):
            raise ValueError('provider wait has invalid quota timing or status')
        value.update({k: wait[k] for k in ('provider', 'reason', 'observed_at', 'next_poll_at', 'http_status')})
    atomic(schedule_path(state, release, platform, stage), value)
    return value


def quota_waiting(state, release, platform):
    now = time.time()
    for path in (Path(state) / 'provider-schedule' / release / platform).glob('*.json'):
        value = schedule(state, release, platform, path.stem)
        if value and value.get('reason') in ('rate_limit', 'listing_quota') and now < value['next_poll_at']:
            return True
    return False


def public_waits(state):
    now = time.time()
    result = []
    for path in sorted((Path(state) / 'provider-schedule').glob('*/*/*.json')):
        value = schedule(state, path.parent.parent.name, path.parent.name, path.stem)
        if value and now < value['next_poll_at']:
            result.append({key: value[key] for key in ('release_id', 'platform', 'stage',
                'provider', 'reason', 'observed_at', 'next_poll_at')})
    return result


def external_wait_fresh(state, release, platform, stage, request, observed_at):
    now = time.time()
    if type(observed_at) is not int or observed_at > now:
        return False
    value = schedule(state, release, platform, stage)
    if not value:
        return now - observed_at <= 600  # Compatibility with an unscheduled older controller.
    if value.get('provider') != 'apple' or value.get('request_id') != request:
        return False
    if value.get('reason') in ('rate_limit', 'listing_quota'):
        return observed_at <= value['observed_at'] <= now <= value['next_poll_at'] + 120
    return now - observed_at <= max(600, value['next_poll_at'] - value['observed_at'] + 120)


def github_download(path, *, repo, stream, timeout, private_diagnostic=False, maximum_bytes=None):
    """Stream large archives; classify quota headers before hash verification."""
    before_request('github')
    options = github_log_options() if private_diagnostic else []
    command = ['gh', 'api', '--include', *options, 'repos/' + repo + '/' + path]
    error = None
    try:
        if private_diagnostic:
            if type(maximum_bytes) is not int or not 1 <= maximum_bytes <= 256 * 1024 * 1024:
                raise ValueError('private diagnostic download needs a bounded size')
            bounded_diagnostic_download(command, stream, maximum_bytes + 65536, timeout)
        else:
            subprocess.run(command, stdout=stream, stderr=subprocess.PIPE, check=True, timeout=timeout)
    except subprocess.CalledProcessError as caught:
        error = caught
    stream.flush()
    # Strip only bounded HTTP headers in place: no second multi-gigabyte archive.
    with open(stream.name, 'rb') as source:
        prefix = source.read(65536)
        offset, status, headers = 0, 0, {}
        while prefix[offset:].startswith(b'HTTP/'):
            remaining = prefix[offset:]
            separator = b'\r\n\r\n' if b'\r\n\r\n' in remaining else b'\n\n'
            head, found, _ = remaining.partition(separator)
            if not found:
                raise ValueError('provider archive response headers exceed bound')
            status = int(head.splitlines()[0].split()[1])
            headers = {line.split(b':', 1)[0].decode().lower(): line.split(b':', 1)[1].decode().strip()
                       for line in head.splitlines()[1:] if b':' in line}
            offset += len(head) + len(separator)
        try:
            body = json.loads(prefix[offset:]) if error else None
        except (ValueError, UnicodeDecodeError):
            body = None
        classify('github', 'GET', path, status, headers, body)
        if error:
            raise error
        if offset:
            source.seek(offset); stream.seek(0)
            while chunk := source.read(1024 * 1024):
                stream.write(chunk)
            stream.truncate(); stream.flush()
    reset_after_success('github')


def bounded_diagnostic_download(command, stream, maximum, timeout):
    """Stream to the owned file with an enforced byte cap, not just metadata."""
    import concurrent.futures
    from release_coordinator import stop_worker
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=os.name != 'nt')
    def copy():
        size = 0
        while chunk := process.stdout.read(min(65536, maximum + 1 - size)):
            size += len(chunk)
            if size > maximum: return False
            stream.write(chunk)
        return True
    def errors():
        prefix = bytearray()
        while chunk := process.stderr.read(8192): prefix.extend(chunk[:max(0, 16384 - len(prefix))])
        return bytes(prefix)
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    output, error = pool.submit(copy), pool.submit(errors)
    try:
        try: complete = output.result(timeout=timeout)
        except concurrent.futures.TimeoutError: raise subprocess.TimeoutExpired(command, timeout) from None
        if not complete:
            stop_worker(process)
            raise ValueError('diagnostic download exceeded its byte cap')
        process.wait(timeout=15)
        stderr = error.result(timeout=15)
        if process.returncode: raise subprocess.CalledProcessError(process.returncode, command, stderr=stderr)
    finally:
        if process.poll() is None: stop_worker(process)
        pool.shutdown(wait=True)
        process.stdout.close(); process.stderr.close()


@lru_cache(maxsize=1)
def github_log_options():
    # New gh releases refuse ANSI-bearing logs even on a pipe. The receiver is
    # bounded private storage, never a terminal. Older qualified images do not
    # have this flag; detect the local capability without a provider request.
    result = subprocess.run(['gh', 'api', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            check=True, timeout=15)
    return ['--allow-escape-sequences'] if b'--allow-escape-sequences' in result.stdout else []


def github_log(path, *, repo, maximum_bytes=4 * 1024 * 1024, timeout=60):
    """Read a bounded private log prefix; never buffer an unlimited provider log."""
    import concurrent.futures
    import re
    if (repo not in ('IggyGG/gchat', 'IggyGG/gcoms')
            or not re.fullmatch(r'actions/jobs/[1-9][0-9]*/logs', path)
            or type(maximum_bytes) is not int or not 1 <= maximum_bytes <= 4 * 1024 * 1024
            or not 0 < timeout <= 120):
        raise ValueError('invalid native diagnostic log request')
    before_request('github')
    command = ['gh', 'api', '--include', *github_log_options(), 'repos/' + repo + '/' + path]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=os.name != 'nt')
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    output = pool.submit(process.stdout.read, maximum_bytes + 65536 + 1)
    def drain_errors():
        prefix = bytearray()
        while chunk := process.stderr.read(8192):
            prefix.extend(chunk[:max(0, 16384 - len(prefix))])
        return bytes(prefix)
    errors = pool.submit(drain_errors)
    try:
        try:
            raw = output.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise subprocess.TimeoutExpired(command, timeout) from None
        capped = len(raw) > maximum_bytes + 65536
        if capped:
            from release_coordinator import stop_worker
            stop_worker(process)
        else:
            process.wait(timeout=15)
        stderr = errors.result(timeout=15)
    finally:
        if process.poll() is None:
            from release_coordinator import stop_worker
            stop_worker(process)
        pool.shutdown(wait=True)
        process.stdout.close(); process.stderr.close()
    offset, status, headers = 0, 0, {}
    while raw[offset:].startswith(b'HTTP/'):
        rest = raw[offset:]
        separator = b'\r\n\r\n' if b'\r\n\r\n' in rest[:65536] else b'\n\n'
        header, found, _ = rest.partition(separator)
        if not found or offset + len(header) + len(separator) > 65536:
            raise ValueError('native log HTTP headers exceed bound')
        status = int(header.splitlines()[0].split()[1])
        headers = {line.split(b':', 1)[0].decode('ascii', errors='replace').lower():
                   line.split(b':', 1)[1].decode('latin1').strip()
                   for line in header.splitlines()[1:] if b':' in line}
        offset += len(header) + len(separator)
    body = raw[offset:]
    try:
        decoded = json.loads(body) if status >= 400 else None
    except (ValueError, UnicodeDecodeError): decoded = None
    classify('github', 'GET', path, status, headers, decoded)
    if process.returncode and not capped:
        raise subprocess.CalledProcessError(process.returncode, command, stderr=stderr[:16384])
    if status != 200: raise ValueError('native diagnostic log response was not successful')
    reset_after_success('github')
    return body[:maximum_bytes], capped or len(body) > maximum_bytes
