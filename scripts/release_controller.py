"""Qualify controller-only revisions without reserving application versions.

Intents and provider identities are immutable. The only activation output is an
exact-release inventory overlay consumed by the ordinary deployment runner.
"""
import argparse
import base64
import copy
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from release_pair import canonical, validate

WORKFLOW = 'controller-release.yml'
PREFIX = 'Forgejo Controller '
ARTIFACT = 'controller-qualified'


def save(path, value):
    from release_coordinator import atomic_json
    atomic_json(path, value)


def sha(path):
    from release_feed import digest
    return digest(path)


def read(path):
    return json.loads(Path(path).read_text())


def validate_intent(value):
    unsigned = {key: item for key, item in value.items() if key != 'id'}
    if (value.get('schema') != 1 or value.get('kind') != 'controller-update'
            or value.get('id') != hashlib.sha256(canonical(unsigned)).hexdigest()):
        raise ValueError('controller intent identity changed')
    baseline = validate(value['baseline'])
    for project in ('gchat', 'gcoms'):
        source = value['sources'][project]
        if set(source) != {'commit', 'tree'} or any(
                not re.fullmatch('[0-9a-f]{40}', str(v)) for v in source.values()):
            raise ValueError('controller intent source is invalid')
    for name in ('artifacts', 'infrastructure', 'controller', 'qualification'):
        if any(not re.fullmatch('[0-9a-f]{64}', str(value[key].get(name, '')))
               for key in ('inputs', 'baseline_inputs')):
            raise ValueError('controller intent fingerprint is missing')
    if any(value['inputs'][key] != value['baseline_inputs'][key]
           for key in ('artifacts', 'infrastructure')):
        raise ValueError('controller intent changes application or native infrastructure inputs')
    if value['inputs']['controller'] == value['baseline_inputs']['controller']:
        raise ValueError('controller intent has no image change')
    return baseline


def verify_inputs(intent, repositories):
    from release_inputs import fingerprints
    baseline = validate_intent(intent)
    for sources, expected in ((intent['sources'], intent['inputs']),
                             (baseline.get('upstream', baseline['sources']), intent['baseline_inputs'])):
        if fingerprints(repositories, sources) != expected:
            raise ValueError('controller intent does not match committed input inventories')
    return baseline


def qualification_ref(intent):
    return 'refs/heads/release/qualification-controller-' + intent['id'][:20]


def queue(state, baseline, sources, before, after):
    value = {'schema': 1, 'kind': 'controller-update', 'baseline': baseline,
             'sources': sources, 'inputs': after, 'baseline_inputs': before}
    value['id'] = hashlib.sha256(canonical(value)).hexdigest()
    validate_intent(value)
    path = Path(state) / 'controller-updates' / value['id'] / 'intent.json'
    if path.exists() and read(path) != value:
        raise ValueError('retained controller intent changed')
    if not path.exists(): save(path, value)
    save(Path(state) / 'controller-updates/desired.json', {'id': value['id']})
    return value


def deployment_config(state, manifest, config):
    """A qualified overlay is scoped to its original application release only."""
    path = Path(state) / 'controller-updates/active' / (manifest['release_id'] + '.json')
    if not path.is_file(): return config
    value = read(path)
    work = Path(state) / 'controller-updates' / value['id']
    intent = read(work / 'intent.json')
    if validate_intent(intent) != manifest or value.get('release_id') != manifest['release_id']:
        raise ValueError('controller overlay baseline changed')
    proof = work / 'qualification.json'
    if sha(proof) != value.get('qualification_sha256'):
        raise ValueError('controller overlay qualification changed')
    result = copy.deepcopy(config)
    matches = [t for t in result['targets'] if t.get('id') == 'controller']
    if len(matches) != 1: raise ValueError('controller overlay target is missing or ambiguous')
    target = matches[0]
    target.update(controller_qualification=str(proof),
                  controller_qualification_sha256=sha(proof),
                  controller_qualification_release_id=manifest['release_id'])
    from release_kubernetes_worker import expected_image
    expected_image(target, {'release_id': manifest['release_id'], 'images': {}})
    return result


def collect(intent, work):
    """One dispatch; immutable provider archive, no retry on ambiguous outcome."""
    from release_jobs import extract, REPO
    from release_provider import github, github_download
    def gh(path, **kwargs): return github(path, repo=REPO, **kwargs)
    marker, run_path = work / 'dispatch.json', work / 'run.json'
    run = gh(f'actions/runs/{read(run_path)["id"]}') if run_path.exists() else None
    if run is None:
        matches = []
        for page in range(1, 11):
            runs = gh(f'actions/workflows/{WORKFLOW}/runs?event=workflow_dispatch&per_page=100&page={page}')['workflow_runs']
            matches += [item for item in runs if item.get('display_title') == PREFIX + intent['id']]
            if matches or len(runs) < 100: break
        if len(matches) > 1: raise ValueError('duplicate controller dispatch needs reconciliation')
        run = matches[0] if matches else None
    if run is None:
        if marker.exists():
            if time.time() - read(marker)['at'] > 1800:
                raise ValueError('controller dispatch outcome unknown; no blind redispatch')
            return None
        ref = qualification_ref(intent)
        visible = gh('git/ref/' + ref.removeprefix('refs/'))
        if visible.get('object', {}).get('sha') != intent['sources']['gchat']['commit']:
            raise ValueError('controller protected ref changed')
        save(marker, {'id': intent['id'], 'at': int(time.time())})
        gh(f'actions/workflows/{WORKFLOW}/dispatches', method='POST', body={
            'ref': ref.removeprefix('refs/heads/'), 'inputs': {'request_id': intent['id'],
                'intent': base64.b64encode(canonical(intent)).decode()}})
        return None
    if (run.get('head_sha') != intent['sources']['gchat']['commit']
            or run.get('event') != 'workflow_dispatch'
            or run.get('display_title') != PREFIX + intent['id']
            or run.get('path') != '.github/workflows/' + WORKFLOW
            or run.get('head_repository', {}).get('full_name') != REPO):
        raise ValueError('controller provider run source or workflow changed')
    save(run_path, run)
    if run['status'] != 'completed': return None
    if run['conclusion'] != 'success': raise ValueError('controller original qualification failed')
    artifacts = gh(f'actions/runs/{run["id"]}/artifacts?per_page=100')['artifacts']
    selected = [a for a in artifacts if a.get('name') == ARTIFACT and not a.get('expired')]
    if len(selected) != 1: raise ValueError('controller archive missing or ambiguous')
    artifact = selected[0]
    if (not re.fullmatch('sha256:[0-9a-f]{64}', artifact.get('digest', ''))
            or not 0 < artifact.get('size_in_bytes', 0) <= 3 * 1024 ** 3):
        raise ValueError('controller provider archive lacks a bounded immutable digest')
    archive = work / 'provider.zip'
    if not archive.exists():
        partial = work / 'provider.zip.partial'
        with partial.open('wb') as stream:
            github_download(f'actions/artifacts/{artifact["id"]}/zip', repo=REPO, stream=stream, timeout=900)
        if 'sha256:' + sha(partial) != artifact['digest']:
            raise ValueError('controller provider archive digest differs')
        os.replace(partial, archive)
    if 'sha256:' + sha(archive) != artifact['digest']:
        raise ValueError('retained controller provider archive changed')
    bundle = work / 'bundle'
    # Re-extract from the authenticated archive, never trust cache-only hashes.
    extract(archive, bundle)
    validate_bundle(intent, bundle)
    save(work / 'provider.json', {'schema': 1, 'run_id': run['id'], 'run_attempt': run['run_attempt'],
        'artifact_id': artifact['id'], 'artifact_sha256': artifact['digest'],
        'source': intent['sources']['gchat'], 'url': run['html_url']})
    save(bundle / 'source-build.json', read(bundle / 'build.json'))
    return bundle


def validate_bundle(intent, bundle):
    build = read(bundle / 'build.json')
    if build.get('intent') != intent or build.get('passed') is not True:
        raise ValueError('controller artifact does not bind its immutable intent')
    required = {'controller.tar', 'controller-runtime.json', 'controller-runtime.log', 'runtime-request.json'}
    if set(build.get('sha256', {})) != required:
        raise ValueError('controller bundle inventory differs')
    for name, expected in build['sha256'].items():
        if sha(bundle / name) != expected: raise ValueError('controller bundle file changed: ' + name)
    from controller_runtime import validate as validate_runtime
    runtime = read(bundle / 'controller-runtime.json')
    validate_runtime(runtime, intent['sources']['gchat'], build['controller_config'])
    if runtime.get('log_sha256') != sha(bundle / 'controller-runtime.log'):
        raise ValueError('controller runtime log changed')
    request = read(bundle / 'runtime-request.json')
    if (request.get('source') != intent['sources']['gchat']
            or runtime['inventory_sha256'] != hashlib.sha256(canonical(request['files'])).hexdigest()):
        raise ValueError('controller runtime request inventory changed')
    return build


def kubernetes_qualify(intent, bundle, image, target, work):
    """Run the retained image's actual runtime suite without production state."""
    name = 'controller-check-' + intent['id'][:20]
    namespace = target['probe_namespace']
    dns = target.get('probe_dns_nameservers')
    if dns is not None:
        if not isinstance(dns, list) or not 1 <= len(dns) <= 3:
            raise ValueError('controller probe requires one to three DNS addresses')
        dns = [str(ipaddress.ip_address(value)) for value in dns]
    def kube(*args, value=None):
        return subprocess.check_output(['kubectl', '-n', namespace, *args],
            input=None if value is None else canonical(value), stderr=subprocess.PIPE, timeout=120)
    request = read(bundle / 'runtime-request.json')
    job = {'apiVersion': 'batch/v1', 'kind': 'Job', 'metadata': {'name': name}, 'spec': {
        'backoffLimit': 0, 'activeDeadlineSeconds': 600,
        'template': {'metadata': {'labels': {'gchat-controller-qualification': intent['id'][:20]}}, 'spec': {
            'restartPolicy': 'Never', 'automountServiceAccountToken': False,
            'affinity': {'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {
                'nodeSelectorTerms': [{'matchExpressions': [{'key': 'kubernetes.io/hostname',
                    'operator': 'NotIn', 'values': ['triform-1']}]}]}}},
            'securityContext': {'runAsUser': 10001, 'runAsGroup': 10001, 'fsGroup': 10001},
            'containers': [{'name': 'qualify', 'image': image, 'imagePullPolicy': 'Always',
                'command': ['python3', '-c', 'import json,os;from controller_runtime import check;'
                    'print(json.dumps(check(json.loads(os.environ["QUALIFICATION_REQUEST"]))))'],
                'env': [{'name': key, 'value': value} for key, value in {
                    'QUALIFICATION_REQUEST': json.dumps(request, separators=(',', ':')),
                    'TMPDIR': '/tmp', 'PYTHONDONTWRITEBYTECODE': '1',
                    'PYTHONPATH': '/opt/gchat/scripts:/opt/gchat/scripts/tests'}.items()],
                'resources': {'requests': {'cpu': '250m', 'memory': '256Mi'},
                              'limits': {'cpu': '2', 'memory': '1Gi'}},
                'securityContext': {'allowPrivilegeEscalation': False, 'readOnlyRootFilesystem': True,
                                    'capabilities': {'drop': ['ALL']}},
                'volumeMounts': [{'name': 'tmp', 'mountPath': '/tmp'}]}],
            # Match CI's bounded tmpfs; test fsync must not depend on host journal load.
            'volumes': [{'name': 'tmp', 'emptyDir': {'medium': 'Memory', 'sizeLimit': '256Mi'}}]}}}}
    if dns is not None:
        job['spec']['template']['spec'].update(dnsPolicy='None', dnsConfig={'nameservers': dns})
    marker = work / 'kubernetes-request.json'
    if marker.exists() and read(marker) != job:
        raise ValueError('controller Kubernetes qualification request changed')
    if not marker.exists(): save(marker, job)
    raw = kube('get', 'job', name, '--ignore-not-found', '-o', 'json')
    if not raw.strip():
        # Deterministic API identity makes create timeout safe to reconcile.
        kube('create', '-f', '-', value=job)
        return None
    actual = json.loads(raw)
    spec = actual['spec']['template']['spec']
    container = spec['containers'][0]
    wanted = job['spec']['template']['spec']
    if (len(spec['containers']) != 1 or spec.get('initContainers')
            or container['image'] != image or container.get('command') != wanted['containers'][0]['command']
            or container.get('env') != wanted['containers'][0]['env']
            or spec.get('automountServiceAccountToken') is not False
            or spec.get('restartPolicy') != 'Never'
            or spec.get('affinity') != wanted['affinity']
            or (dns is not None and (spec.get('dnsPolicy') != 'None'
                                    or spec.get('dnsConfig') != wanted['dnsConfig']))
            or spec.get('volumes') != wanted['volumes']
            or any(spec.get('securityContext', {}).get(k) != v for k,v in wanted['securityContext'].items())
            or any(container.get('securityContext', {}).get(k) != v for k,v in wanted['containers'][0]['securityContext'].items())
            or container.get('volumeMounts') != wanted['containers'][0]['volumeMounts']
            or actual['spec'].get('backoffLimit') != 0
            or actual['spec'].get('activeDeadlineSeconds') != 600):
        raise ValueError('controller Kubernetes qualification job changed')
    status = actual.get('status', {})
    if status.get('failed'):
        failure = {'job': actual}
        save(work / 'kubernetes-failure.json', failure)
        try:
            failure['pods'] = json.loads(kube('get', 'pods', '-l', 'job-name=' + name, '-o', 'json'))['items']
            save(work / 'kubernetes-failure.json', failure)
            for index, pod in enumerate(failure['pods']):
                logs = kube('logs', pod['metadata']['name'], '-c', 'qualify')
                (work / f'kubernetes-failure-{index}.log').write_bytes(logs)
        except (subprocess.SubprocessError, ValueError) as error:
            failure['diagnostic_error'] = str(error)
            save(work / 'kubernetes-failure.json', failure)
        raise ValueError('controller Kubernetes runtime qualification failed')
    if not status.get('succeeded'): return None
    pods = json.loads(kube('get', 'pods', '-l', 'job-name=' + name, '-o', 'json'))['items']
    if len(pods) != 1: raise ValueError('controller qualification pod is ambiguous')
    pod = pods[0]
    states = pod.get('status', {}).get('containerStatuses', [])
    if (len(states) != 1 or not states[0].get('imageID', '').endswith(image.rsplit('@', 1)[1])
            or states[0].get('state', {}).get('terminated', {}).get('exitCode') != 0):
        raise ValueError('controller Kubernetes image or exit status differs')
    logs = kube('logs', pod['metadata']['name'], '-c', 'qualify')
    (work / 'kubernetes-runtime.log').write_bytes(logs)
    lines = [line for line in logs.decode().splitlines() if line.startswith('{')]
    if len(lines) != 1: raise ValueError('controller Kubernetes runtime proof is ambiguous')
    proof = json.loads(lines[0])
    original = read(bundle / 'controller-runtime.json')
    proof['configuration_digest'] = original['configuration_digest']
    from controller_runtime import validate as validate_runtime
    validate_runtime(proof, intent['sources']['gchat'], original['configuration_digest'])
    for key in ('tests', 'source_files_verified', 'inventory_sha256', 'suites'):
        if proof[key] != original[key]: raise ValueError('controller Kubernetes runtime differs from CI')
    save(work / 'kubernetes-runtime.json', {**proof, 'pod_uid': pod['metadata']['uid'],
        'image_id': states[0]['imageID'], 'log_sha256': sha(work / 'kubernetes-runtime.log')})
    return proof


def step(state, config, ident=None, local_bundle=None):
    state = Path(state)
    desired = state / 'controller-updates/desired.json'
    if not desired.exists(): return
    ident = ident or read(desired)['id']
    if not re.fullmatch('[0-9a-f]{64}', ident): raise ValueError('invalid controller intent selection')
    work = state / 'controller-updates' / ident
    intent = read(work / 'intent.json')
    baseline = verify_inputs(intent, {p: config['discovery'][p]['mirror'] for p in ('gchat', 'gcoms')})
    selected = state / 'deployment/desired.json'
    journal = state / 'deployment' / baseline['release_id'] / 'journal.json'
    if (not selected.exists() or read(selected).get('release_id') != baseline['release_id']
            or not journal.exists() or read(journal).get('state') != 'deployed'
            or read(journal).get('sources') != baseline['sources']):
        save(work / 'status.json', {'state': 'waiting_baseline', 'at': int(time.time())}); return
    active = state / 'controller-updates/active' / (baseline['release_id'] + '.json')
    if active.exists() and read(active).get('id') == ident: return
    import shutil
    if shutil.disk_usage(state).free < config.get('minimum_free_bytes', 0):
        save(work / 'status.json', {'state': 'waiting_storage', 'at': int(time.time())}); return
    if local_bundle is None:
        bundle = collect(intent, work)
    else:
        # Explicit bootstrap: exact committed bytes pass the same Docker and
        # Kubernetes suites. This is controller qualification, not app signing.
        import shutil
        local_bundle = Path(local_bundle).resolve()
        build = validate_bundle(intent, local_bundle)
        bundle = work / 'bundle'; bundle.mkdir(exist_ok=True)
        for name in ('build.json', *build['sha256']):
            destination = bundle / name
            if destination.exists() and sha(destination) != sha(local_bundle / name):
                raise ValueError('retained local controller bundle changed')
            if not destination.exists(): shutil.copyfile(local_bundle / name, destination)
        validate_bundle(intent, bundle)
        save(bundle / 'source-build.json', build)
        save(work / 'provider.json', {'schema': 1, 'origin': 'local-controller-bootstrap',
            'source': intent['sources']['gchat'], 'build_sha256': sha(bundle / 'build.json')})
    if bundle is None:
        save(work / 'status.json', {'state': 'building', 'at': int(time.time())}); return
    inventory = read(config['deployment_file'])
    targets = [t for t in inventory['targets'] if t.get('id') == 'controller']
    if len(targets) != 1: raise ValueError('controller deployment target is missing')
    target = targets[0]
    from release_infrastructure_bundle import publish
    image = publish(bundle, read(target['infrastructure_config']), 'controller-' + ident, 'controller')
    native = kubernetes_qualify(intent, bundle, image, target, work)
    if native is None:
        save(work / 'status.json', {'state': 'qualifying_kubernetes', 'at': int(time.time())}); return
    from release_kubernetes_worker import resource, images
    previous = images(resource(target)['spec'], target['containers'])
    from release_rollback_image import retain, repair
    for old in set(previous.values()): retain(old, target); repair(old, target)
    runtime = read(bundle / 'controller-runtime.json')
    proof = {'schema': 1, 'source': intent['sources']['gchat'], 'image': image,
        'configuration': runtime['configuration_digest'], 'runtime': runtime,
        'registry_configuration_verified': True, 'intent_id': ident,
        'artifact_release_id': baseline['release_id'], 'previous_images': previous,
        'provider_sha256': sha(work / 'provider.json'),
        'kubernetes_runtime_sha256': sha(work / 'kubernetes-runtime.json'),
        'kubernetes_validation': {'source': intent['sources']['gchat']['commit'],
            'tests': native['tests'], 'source_files_verified': native['source_files_verified'],
            'previous_digest_retained_and_repaired': True}}
    save(work / 'qualification.json', proof)
    # Activation is performed later by the sole coordinator at a quiescent
    # boundary, through its unchanged deployment runner and canary policy.
    save(work / 'ready.json', {'id': ident, 'release_id': baseline['release_id'],
                             'qualification_sha256': sha(work / 'qualification.json')})
    save(work / 'status.json', {'state': 'qualified', 'at': int(time.time())})


def close(controller):
    item = getattr(controller, '_controller_worker', None)
    if item is None: return
    process, log = item['process'], item['log']
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try: process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=5)
    log.close(); controller._controller_worker = None


def acceptance_intents(jobs):
    """Visit writer-owned job/followup directories, never extracted artifacts."""
    pending = [jobs] if jobs.exists() else []
    while pending:
        group = pending.pop()
        if group.is_symlink():
            raise ValueError('acceptance intent directory is a symlink')
        with os.scandir(group) as entries:
            directories = []
            for entry in entries:
                if entry.is_symlink():
                    raise ValueError('acceptance job or followup is a symlink')
                if entry.is_dir(follow_symlinks=False):
                    directories.append(Path(entry.path))
        for work in directories:
            intent = work / 'acceptance-intent.json'
            if intent.is_symlink():
                raise ValueError('acceptance intent is a symlink')
            if intent.is_file():
                yield intent
            # failed_followup() can recursively create further followups. A
            # cleaned parent must not hide an active child or sibling request.
            followups = work / 'followups'
            if followups.is_symlink():
                raise ValueError('acceptance followup directory is a symlink')
            if followups.exists():
                pending.append(followups)


def quiescent(controller):
    if controller.running_workers or getattr(controller.deployment_runner, 'pending', None): return False
    # A remote reader may have no local subprocess. Wait for all native/mobile
    # acceptance grants to finish their ordinary cleanup before replacing nginx's
    # colocated coordinator pod and its sole Service endpoint.
    now = time.time()
    for path in acceptance_intents(controller.state / 'jobs'):
        intent = read(path)
        if intent.get('cleaned') is True: continue
        delivery = path.parent / 'sealed-delivery.json'
        expires = read(delivery).get('expires_at') if delivery.exists() else None
        # Old secret-based grants expire one hour after their recorded issue.
        # Unknown legacy timing fails closed rather than assuming revocation.
        if expires is None and intent.get('dispatch_reserved') and not intent.get('delivery_protocol'):
            if type(intent.get('created_at')) is not int: return False
            expires = intent['created_at'] + 3600
        if expires is not None and (type(expires) is not int or expires > now): return False
        run = path.parent / 'acceptance-run.json'
        if run.exists() and read(run).get('status') == 'completed': continue
        if (path.parent / 'acceptance-failed.json').exists(): continue
        ledger = getattr(controller, 'ledger', None)
        if ledger is not None:
            row = ledger.db.execute('''SELECT p.state FROM effects e JOIN platforms p
                ON p.candidate=e.candidate AND p.platform=e.platform
                WHERE e.id=? AND e.kind LIKE 'acceptance%' AND e.state='reserved' ''',
                (path.relative_to(controller.state / 'jobs').parts[0],)).fetchone()
            if row and row[0] not in ('blocked', 'failed', 'superseded', 'available'):
                return False
    return True


def reconcile(controller):
    if not controller.config.get('discovery') or not controller.config.get('deployment_file'): return
    desired = controller.state / 'controller-updates/desired.json'
    if not desired.exists(): return
    item = getattr(controller, '_controller_worker', None)
    if item is not None:
        if item['process'].poll() is None:
            if time.monotonic() > item['deadline']:
                close(controller)
                save(controller.state / 'controller-update-blocked.json', {'reason': 'controller worker deadline'})
            return
        item['log'].close(); controller._controller_worker = None
        if item['process'].returncode:
            return  # Durable status retains the precise failure; no blind retry.
    ident = read(desired)['id']
    if not re.fullmatch('[0-9a-f]{64}', ident): raise ValueError('invalid controller desired ID')
    work = controller.state / 'controller-updates' / ident
    if (work / 'blocked.json').exists(): return
    ready = work / 'ready.json'
    if ready.exists():
        value = read(ready)
        path = controller.state / 'controller-updates/active' / (value['release_id'] + '.json')
        if path.exists() and read(path) == value: return
        if quiescent(controller): save(path, value)
        return
    schedule = work / 'poll.json'
    if schedule.exists() and time.time() < read(schedule)['next_poll_at']: return
    from release_provider import cooldown
    if cooldown(controller.state / 'provider-poll', 'github'): return
    work.mkdir(parents=True, exist_ok=True)
    save(schedule, {'next_poll_at': int(time.time()) + controller.github_poll_interval})
    config_path = work / 'worker-config.json'; save(config_path, controller.config)
    log = (work / 'worker.log').open('ab')
    try:
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
            '--state', str(controller.state), '--config', str(config_path), '--intent-id', ident],
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    except OSError: log.close(); raise
    controller._controller_worker = {'process': process, 'log': log, 'deadline': time.monotonic() + 1500}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--intent-id')
    parser.add_argument('--local-bundle', type=Path, help='Explicit controller-only bootstrap; never app qualification')
    args = parser.parse_args()
    root = args.state / 'controller-updates'; root.mkdir(parents=True, exist_ok=True)
    from release_provider import locked, ProviderWait
    os.environ['GCHAT_RELEASE_PROVIDER_STATE'] = str(args.state / 'provider-poll')
    ident = args.intent_id or read(root / 'desired.json')['id']
    if not re.fullmatch('[0-9a-f]{64}', ident): raise ValueError('invalid controller intent ID')
    with locked(root / 'worker.lock'):
        try: step(args.state, read(args.config), ident, args.local_bundle)
        except ProviderWait as error:
            save(root / ident / 'status.json', {'state': 'waiting_provider', **error.value})
            raise SystemExit(75)
        except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
            save(root / ident / 'blocked.json', {'reason': type(error).__name__,
                'message': str(error)[:500], 'at': int(time.time())})
            raise


if __name__ == '__main__': main()
