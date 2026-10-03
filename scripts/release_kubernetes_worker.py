"""Serial digest-pinned deployment adapter; never replaces PVCs or identities."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from release_coordinator import atomic_json
from release_pair import validate


def kubectl(target, *args):
    return subprocess.check_output(['kubectl', '--namespace', target['namespace'], *args],
                                   stderr=subprocess.PIPE, timeout=120)


def resource(target):
    if target['kind'] not in ('statefulset', 'deployment'):
        raise ValueError('only installed application workloads may be rolled')
    return json.loads(kubectl(target, 'get', target['kind'], target['name'], '-o', 'json'))


def image_digest(value):
    match = re.search(r'(sha256:[0-9a-f]{64})$', value)
    return match.group(1) if match else None


def observe(target, expected):
    current = resource(target)
    if current['spec'].get('replicas', 1) == 0:
        raise ValueError('disabled workloads are not deployment targets')
    if target['kind'] == 'statefulset':
        pods = [json.loads(kubectl(target, 'get', 'pod', target['pod'], '-o', 'json'))]
    else:
        labels = current['spec']['selector']['matchLabels']
        selector = ','.join(key + '=' + value for key, value in sorted(labels.items()))
        pods = json.loads(kubectl(target, 'get', 'pods', '-l', selector, '-o', 'json'))['items']
    live = [pod for pod in pods if not pod['metadata'].get('deletionTimestamp')]
    expected_count = 1 if target['kind'] == 'statefulset' else current['spec'].get('replicas', 1)
    healthy = len(live) == expected_count and all(
        any(c['type'] == 'Ready' and c['status'] == 'True' for c in p.get('status', {}).get('conditions', []))
        for p in live)
    images = []
    matches = bool(live)
    for pod in live:
        states = {c['name']: c for c in [*pod.get('status', {}).get('containerStatuses', []),
                                        *pod.get('status', {}).get('initContainerStatuses', [])]}
        for name in target['containers']:
            actual = states.get(name, {}).get('imageID', '')
            matches = matches and image_digest(actual) == image_digest(expected)
            images.append({'pod_uid': pod['metadata']['uid'], 'container': name, 'image_id': actual})
    return {'healthy': healthy, 'matches': bool(matches), 'running': {'images': images}}


def images(spec, names):
    containers = spec['template']['spec']
    found = {c['name']: c['image'] for c in [*containers.get('containers', []),
                                          *containers.get('initContainers', [])] if c['name'] in names}
    if set(found) != set(names):
        raise ValueError('inventory container does not exist in installed workload')
    return found


def identities(target):
    paths = target.get('identity_paths', [])
    if target['kind'] != 'statefulset': return {}
    if not paths or any(not p.startswith('/var/lib/gc/') for p in paths):
        raise ValueError('stateful relay identity paths must be explicit')
    raw = kubectl(target, 'exec', target['pod'], '-c', target['identity_container'],
                  '--', 'sha256sum', *paths).decode()
    result = {}
    for line in raw.splitlines():
        sha, path = line.split(maxsplit=1)
        if not re.fullmatch('[0-9a-f]{64}', sha) or path not in paths:
            raise ValueError('invalid relay identity observation')
        result[path] = sha
    if set(result) != set(paths): raise ValueError('relay identity observation incomplete')
    return result


def patch_images(target, current, replacement, partition=None, on_delete=False):
    # Strategic merge updates only named images. Environment, commands, volumes,
    # identities, services, limits and replica counts retain their current values.
    pod = {}
    for group in ('containers', 'initContainers'):
        selected = [{'name': c['name'], 'image': replacement[c['name']]}
                    for c in current['spec']['template']['spec'].get(group, []) if c['name'] in replacement]
        if selected: pod[group] = selected
    patch = {'metadata': {'resourceVersion': current['metadata']['resourceVersion']},
             'spec': {'template': {'spec': pod}}}
    if on_delete:
        patch['spec']['updateStrategy'] = {'type': 'OnDelete', 'rollingUpdate': None}
    elif partition is not None:
        patch['spec']['updateStrategy'] = {'type': 'RollingUpdate', 'rollingUpdate': {'partition': partition}}
    kubectl(target, 'patch', target['kind'], target['name'], '--type=strategic', '-p', json.dumps(patch))


def rollback_stateful(target, current, before, journal):
    # A lower ordinal's previous template may already be the new image from
    # the higher ordinal. Its own running image is the rollback authority.
    # Freeze automatic rolling while replacing just the failed pod, then
    # restore the preceding template/partition so healthy ordinals stay put.
    pod = json.loads(kubectl(target, 'get', 'pod', target['pod'], '-o', 'json'))
    if 'rollback' not in before:
        before['rollback'] = {'pod_uid': pod['metadata']['uid'], 'state': 'replacing'}
        atomic_json(journal, before)
    if before['rollback']['state'] != 'complete':
        if (current['spec'].get('updateStrategy', {}).get('type') != 'OnDelete'
                or images(current['spec'], target['containers']) != before['pod_images']):
            patch_images(target, current, before['pod_images'], on_delete=True)
        if pod['metadata']['uid'] == before['rollback']['pod_uid']:
            kubectl(target, 'delete', 'pod', target['pod'], '--wait=false')
            return None
        observed = observe(target, next(iter(before['pod_images'].values())))
        if not observed['healthy'] or not observed['matches']: return None
        if identities(target) != before['identities']:
            raise ValueError('relay identities changed during rollback')
        current = resource(target)
        patch_images(target, current, before['images'], before['partition'])
        before['rollback']['state'] = 'complete'
        atomic_json(journal, before)
    observed = observe(target, next(iter(before['pod_images'].values())))
    if not observed['healthy'] or not observed['matches']: return None
    if identities(target) != before['identities']:
        raise ValueError('relay identities changed during rollback')
    return {'passed': True, **observed}


def expected_image(target, build):
    """A reviewed controller upgrade has its own exact-source image receipt."""
    path = target.get('controller_qualification')
    if not path:
        return build['images'][target['image']]
    if (target.get('kind') != 'deployment' or target.get('namespace') != 'ghost-com'
            or target.get('name') != 'gchat-release' or target.get('image') != 'controller'):
        raise ValueError('independent controller qualification is outside the installed controller')
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != target.get('controller_qualification_sha256'):
        raise ValueError('operator controller qualification changed')
    proof = json.loads(raw)
    source = proof.get('source', {})
    if (proof.get('schema') != 1 or not re.fullmatch('[0-9a-f]{40}', str(source.get('commit', '')))
            or not re.fullmatch('[0-9a-f]{40}', str(source.get('tree', '')))
            or proof.get('registry_configuration_verified') is not True):
        raise ValueError('controller source or registry qualification is incomplete')
    from controller_runtime import validate
    validate(proof['runtime'], source, proof['configuration'])
    native = proof.get('kubernetes_validation', {})
    if (native.get('source') != source['commit']
            or native.get('tests') != proof['runtime']['tests']
            or native.get('source_files_verified') != proof['runtime']['source_files_verified']
            or native.get('previous_digest_retained_and_repaired') is not True):
        raise ValueError('controller did not pass its actual Kubernetes image validation')
    image = proof.get('image', '')
    if not re.fullmatch(r'[^\s]+@sha256:[0-9a-f]{64}', image):
        raise ValueError('qualified controller image must be digest-pinned')
    return image


def run(target, manifest, stage, output):
    directory = Path(target['artifact_root']) / manifest['release_id']
    build = json.loads((directory / 'build.json').read_text())
    if build.get('sources') != manifest['sources'] or build.get('qualified') is not True:
        raise ValueError('image bundle is not qualified on this exact source')
    expected = expected_image(target, build)
    if not re.fullmatch(r'[^\s]+@sha256:[0-9a-f]{64}', expected):
        raise ValueError('deployment image must be pinned by digest')
    if stage == 'observe': return observe(target, expected)
    journal = output.parent / 'kubernetes-before.json'
    current = resource(target)
    if stage == 'prepare':
        # A cached successful artifact receipt cannot prove registry availability.
        # Re-publish retained qualified OCI blobs before the cold pull check.
        if target.get('infrastructure_config'):
            from release_infrastructure_bundle import collect
            config = json.loads(Path(target['infrastructure_config']).read_text())
            if collect(Path(target['artifact_root']).parent, manifest, config) is None:
                return None
        if not journal.exists():
            pod_images = {}
            if target['kind'] == 'statefulset':
                pod = json.loads(kubectl(target, 'get', 'pod', target['pod'], '-o', 'json'))
                pod_images = images({'template': {'spec': pod['spec']}}, target['containers'])
            atomic_json(journal, {'uid': current['metadata']['uid'],
                                  'images': images(current['spec'], target['containers']),
                                  'pod_images': pod_images,
                                  'partition': current['spec'].get('updateStrategy', {}).get('rollingUpdate', {}).get('partition', 0),
                                  'identities': identities(target),
                                  'volume_claims': current['spec'].get('volumeClaimTemplates', [])})
        if target.get('rollback_image_root'):
            from release_rollback_image import retain
            before = json.loads(journal.read_text())
            for image in set([*before['images'].values(), *before.get('pod_images', {}).values()]):
                retain(image, target)
        # An Always-pull probe catches a digest missing from the registry before
        # any working replica is replaced. The Job is deterministic after a crash.
        attempts_path = output.parent / 'pull-attempts.json'
        attempts = json.loads(attempts_path.read_text()) if attempts_path.exists() else {'generation': 0}
        job = 'gchat-pull-' + hashlib.sha256((expected + ':' + str(attempts['generation'])).encode()).hexdigest()[:24]
        probe = {'apiVersion': 'batch/v1', 'kind': 'Job', 'metadata': {'name': job}, 'spec': {
            'backoffLimit': 0, 'activeDeadlineSeconds': 180, 'ttlSecondsAfterFinished': 86400,
            'template': {'spec': {'automountServiceAccountToken': False, 'restartPolicy': 'Never',
                'affinity': {'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {
                    'nodeSelectorTerms': [{'matchExpressions': [{'key': 'kubernetes.io/hostname',
                        'operator': 'NotIn', 'values': ['triform-1']}]}]}}},
                'containers': [{'name': 'pull', 'image': expected, 'imagePullPolicy': 'Always',
                    'command': ['/bin/sh', '-c', 'exit 0'],
                    'securityContext': {'allowPrivilegeEscalation': False, 'readOnlyRootFilesystem': True,
                                        'capabilities': {'drop': ['ALL']}},
                    'resources': {'requests': {'cpu': '10m', 'memory': '16Mi'},
                                  'limits': {'cpu': '100m', 'memory': '64Mi'}}}]}}}}
        probe_target = {'namespace': target.get('probe_namespace', target['namespace'])}
        subprocess.run(['kubectl', '-n', probe_target['namespace'], 'apply', '-f', '-'],
                       input=json.dumps(probe).encode(), check=True, stdout=subprocess.DEVNULL, timeout=30)
        state = json.loads(kubectl(probe_target, 'get', 'job', job, '-o', 'json'))['status']
        if state.get('failed') or any(c['type'] == 'Failed' and c['status'] == 'True' for c in state.get('conditions', [])):
            if target.get('infrastructure_config') and attempts['generation'] < 3:
                atomic_json(attempts_path, {'generation': attempts['generation'] + 1})
                return None
            raise ValueError('candidate image cannot be pulled; working replicas retained')
        if not state.get('succeeded'): return None
        return {'passed': True, 'pull_job': job, 'image': expected}
    before = json.loads(journal.read_text())
    if current['metadata']['uid'] != before['uid'] or current['spec'].get('volumeClaimTemplates', []) != before['volume_claims']:
        raise ValueError('workload identity or persistent claim definition changed')
    if stage == 'check':
        if identities(target) != before['identities']:
            raise ValueError('relay identities changed during rollout')
        proof = output.with_suffix('.canary.json')
        result = subprocess.run(target['canary'], env=dict(os.environ, GCHAT_CANARY_RECEIPT=str(proof)),
                                timeout=target.get('canary_timeout', 900))
        if result.returncode == 75: return None
        if result.returncode: raise ValueError('installed-network canary failed')
        value = json.loads(proof.read_text())
        if (value.get('passed') is not True or value.get('authenticated_delivery') is not True
                or value.get('release_id') != manifest['release_id'] or value.get('sources') != manifest['sources']
                or value.get('target') != target['id']
                or value.get('network_check', 'full') != target.get('network_check', 'full')):
            raise ValueError('canary does not bind this rollout')
        return value
    if stage not in ('activate', 'rollback'): raise ValueError('unsupported rollout stage')
    if stage == 'rollback' and target.get('rollback_image_root'):
        from release_rollback_image import repair
        for image in set([*before['images'].values(), *before.get('pod_images', {}).values()]):
            repair(image, target)
    desired = {name: expected for name in target['containers']} if stage == 'activate' else before['images']
    actual = images(current['spec'], target['containers'])
    if any(actual[name] not in (before['images'][name], before.get('pod_images', {}).get(name), expected) for name in actual):
        raise ValueError('another operator changed the target image')
    if stage == 'rollback' and target['kind'] == 'statefulset':
        return rollback_stateful(target, current, before, journal)
    partition = (target['ordinal'] if stage == 'activate' else before['partition']) if target['kind'] == 'statefulset' else None
    current_partition = current['spec'].get('updateStrategy', {}).get('rollingUpdate', {}).get('partition', 0)
    if actual != desired or (partition is not None and current_partition != partition):
        patch_images(target, current, desired, partition)
    observed_image = expected if stage == 'activate' else next(iter(before['images'].values()))
    observation = observe(target, observed_image)
    if not observation['healthy'] or not observation['matches']: return None
    if identities(target) != before['identities']:
        raise ValueError('relay identities changed during rollout')
    return {'passed': True, **observation}


def main():
    manifest = validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()))
    target = json.loads(Path(os.environ['GCHAT_DEPLOYMENT_TARGET']).read_text())
    stage = os.environ['GCHAT_DEPLOYMENT_STAGE']; output = Path(os.environ['GCHAT_DEPLOYMENT_RECEIPT'])
    value = run(target, manifest, stage, output)
    if value is None: raise SystemExit(75)
    evidence = output.with_suffix('.observation.json'); atomic_json(evidence, value)
    atomic_json(output, {**value, 'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
        'target': target['id'], 'stage': stage, 'observed_at': int(time.time()),
        'evidence': [{'path': evidence.name, 'sha256': hashlib.sha256(evidence.read_bytes()).hexdigest()}]})


if __name__ == '__main__': main()
