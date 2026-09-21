#!/usr/bin/env python3
"""Roll out the GChat website using immutable Kubernetes ConfigMaps."""
import argparse
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from urllib.request import Request, urlopen
import uuid
import website

ROOT = Path(__file__).resolve().parents[1]
FILES = {'index.html', 'privacy.html', 'downloads.json', 'build.json', 'robots.txt', 'fonts/fixedsys-excelsior.ttf', 'fonts/LICENSE-CC0'}
ORIGIN = 'https://gchat.boo'


def bundle(directory, commit):
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('website source must be a full commit ID')
    actual = {f.relative_to(directory).as_posix() for f in directory.rglob('*') if f.is_file()}
    if actual != FILES or any(f.is_symlink() for f in directory.rglob('*')):
        raise ValueError('unexpected website bundle contents')
    hashes = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in sorted(FILES)}
    build = json.loads((directory / 'build.json').read_text())
    if build['index_sha256'] != hashes['index.html']:
        raise ValueError('website build report differs from rendered page')
    identity = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:16]
    return commit + '-' + identity, hashes, build


def configmap(directory, commit, namespace, deployment):
    revision, hashes, _ = bundle(directory, commit)
    name = deployment + '-' + commit[:12] + '-' + revision.rsplit('-', 1)[1]
    data, binary = {}, {}
    for path in sorted(FILES):
        raw = (directory / path).read_bytes()
        key = path.replace('/', '--')
        if path.endswith('.ttf'):
            binary[key] = base64.b64encode(raw).decode('ascii')
        else:
            data[key] = raw.decode('utf-8')
    if sum(len((directory / path).read_bytes()) for path in FILES) > 1024 * 1024:
        raise ValueError('website exceeds the Kubernetes ConfigMap size limit')
    return {
        'apiVersion': 'v1', 'kind': 'ConfigMap', 'immutable': True,
        'metadata': {'name': name, 'namespace': namespace,
                     'labels': {'app.kubernetes.io/name': deployment},
                     'annotations': {'gchat.boo/source-commit': commit,
                                     'gchat.boo/bundle-version': revision}},
        'data': data, 'binaryData': binary,
    }, hashes


def verify_source(directory):
    # A valid build.json alone does not bind dist/ to the source commit.
    # Rebuild from the checkout so stale or hand-edited output cannot be labeled
    # as a release of that source.
    with tempfile.TemporaryDirectory(prefix='gchat-site-verify-') as temp:
        expected = Path(temp)
        website.build(expected, website.validate(json.loads((ROOT / 'release/downloads.json').read_text())))
        if any((directory / path).read_bytes() != (expected / path).read_bytes() for path in FILES):
            raise ValueError('website bundle differs from current source; rebuild before deployment')


def content_volume(deployment):
    pod = deployment['spec']['template']['spec']
    matches = [(i, v) for i, v in enumerate(pod['volumes']) if v['name'] == 'content']
    if len(matches) != 1 or 'configMap' not in matches[0][1]:
        raise ValueError('expected the existing content ConfigMap volume')
    mounts = [m for c in pod['containers'] for m in c.get('volumeMounts', []) if m['name'] == 'content']
    if len(mounts) != 1 or mounts[0].get('mountPath') != '/usr/share/nginx/html' or not mounts[0].get('readOnly') or 'subPath' in mounts[0] or 'subPathExpr' in mounts[0]:
        raise ValueError('expected the read-only GChat Nginx document root')
    return matches[0]


def version_volume(name):
    return {'name': 'content', 'configMap': {'name': name, 'defaultMode': 0o644,
            'items': [{'key': path.replace('/', '--'), 'path': path} for path in sorted(FILES)]}}


def volume_patch(deployment, volume):
    index, previous = content_volume(deployment)
    path = f'/spec/template/spec/volumes/{index}'
    return [
        {'op': 'test', 'path': '/metadata/uid', 'value': deployment['metadata']['uid']},
        {'op': 'test', 'path': '/metadata/generation', 'value': deployment['metadata']['generation']},
        {'op': 'test', 'path': path, 'value': previous},
        {'op': 'replace', 'path': path, 'value': volume},
    ]


class Kubernetes:
    def __init__(self, namespace, context):
        self.command = ['kubectl', '--request-timeout=30s', '--namespace', namespace]
        if context:
            self.command += ['--context', context]

    def run(self, *args, body=None):
        result = subprocess.run(self.command + list(args), input=json.dumps(body) if body is not None else None,
                                capture_output=True, text=True)
        if result.returncode:
            # Do not echo payloads, kubeconfig contents, or authentication plugin output.
            raise RuntimeError('kubectl ' + args[0] + ' failed; inspect cluster access and the named website resource')
        return json.loads(result.stdout) if result.stdout.strip() else None

    def get(self, kind, name):
        return self.run('get', kind, name, '--ignore-not-found', '-o', 'json')

    def patch(self, deployment, volume, dry_run=False):
        return self.run('patch', 'deployment', deployment['metadata']['name'], '--type=json',
                        '--patch-file=/dev/stdin', '-o', 'json',
                        *(['--dry-run=server'] if dry_run else []), body=volume_patch(deployment, volume))


def ensure_configmap(kube, desired, dry_run=False):
    current = kube.get('configmap', desired['metadata']['name'])
    if current:
        if any(current.get(k) != desired.get(k) for k in ('immutable', 'data', 'binaryData')) or current['metadata'].get('annotations', {}).get('gchat.boo/bundle-version') != desired['metadata']['annotations']['gchat.boo/bundle-version']:
            raise ValueError('existing website version differs; immutable content cannot be replaced')
        return
    kube.run('create', '-f', '-', '-o', 'json', *(['--dry-run=server'] if dry_run else []), body=desired)


def wait_ready(kube, expected, timeout=180):
    deadline = time.monotonic() + timeout
    while True:
        current = kube.get('deployment', expected['metadata']['name'])
        if not current or current['metadata']['uid'] != expected['metadata']['uid'] or current['spec']['template'] != expected['spec']['template']:
            raise RuntimeError('website deployment changed concurrently; stopping verification')
        status = current.get('status', {})
        replicas = current['spec'].get('replicas', 1)
        if replicas > 0 and status.get('observedGeneration') == current['metadata']['generation'] and all(status.get(k, 0) == replicas for k in ('replicas', 'updatedReplicas', 'readyReplicas', 'availableReplicas')):
            return current
        if time.monotonic() >= deadline or any(c.get('reason') == 'ProgressDeadlineExceeded' for c in status.get('conditions', [])):
            raise RuntimeError('website replicas did not become ready')
        time.sleep(2)


def verify_public(hashes, timeout=30):
    deadline = time.monotonic() + timeout
    while True:
        try:
            for path, expected in hashes.items():
                route = '/' if path == 'index.html' else '/' + path
                request = Request(ORIGIN + route + '?gchat-build=' + expected[:16] + '&probe=' + uuid.uuid4().hex,
                                  headers={'Cache-Control': 'no-cache', 'Connection': 'close'})
                with urlopen(request, timeout=max(1, min(10, deadline - time.monotonic()))) as response:
                    if response.status != 200 or hashlib.sha256(response.read()).hexdigest() != expected:
                        raise ValueError('public website digest mismatch: ' + path)
            return
        except (OSError, ValueError):
            # Ingress may briefly retain an old upstream after the new pods are
            # ready. Require a complete matching bundle within the same bound.
            if time.monotonic() >= deadline:
                raise
            time.sleep(max(0, min(2, deadline - time.monotonic())))


def activate(kube, previous, volume, hashes):
    expected = copy.deepcopy(previous)
    index, old_volume = content_volume(previous)
    expected['spec']['template']['spec']['volumes'][index] = volume
    try:
        # Guarded by UID, generation, and the exact old volume. A concurrent
        # deployment is never overwritten, including during recovery.
        kube.patch(previous, volume)
        current = wait_ready(kube, expected)
        verify_public(hashes)
        return current
    except Exception as failure:
        current = kube.get('deployment', previous['metadata']['name'])
        if current and current['metadata']['uid'] == previous['metadata']['uid'] and current['spec']['template'] == expected['spec']['template'] and old_volume != volume:
            restored = kube.patch(current, old_volume)
            wait_ready(kube, restored)
            raise RuntimeError('website update failed; previous content restored') from failure
        raise RuntimeError('website update failed; no newer deployment was overwritten') from failure


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', type=Path, default=ROOT / 'dist/website')
    p.add_argument('--namespace', default=os.environ.get('GCHAT_WEB_NAMESPACE') or 'ghost-com')
    p.add_argument('--deployment', default=os.environ.get('GCHAT_WEB_DEPLOYMENT') or 'gchat-site')
    p.add_argument('--context', default=os.environ.get('GCHAT_KUBE_CONTEXT') or None)
    p.add_argument('--rollback', help='retained versioned website ConfigMap to activate')
    p.add_argument('--dry-run', action='store_true', help='validate with the API server without changing cluster state')
    a = p.parse_args()
    for name in (a.namespace, a.deployment):
        if len(name) > 63 or not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?', name):
            raise ValueError('invalid Kubernetes namespace or deployment name')
    kube = Kubernetes(a.namespace, a.context)
    previous = kube.get('deployment', a.deployment)
    if not previous:
        raise ValueError('existing website deployment was not found')
    _, old_volume = content_volume(previous)
    if a.rollback:
        if not re.fullmatch(re.escape(a.deployment) + r'-[0-9a-f]{12}-[0-9a-f]{16}', a.rollback):
            raise ValueError('rollback requires a retained versioned website ConfigMap name')
        desired = kube.get('configmap', a.rollback)
        if not desired or not desired.get('immutable'):
            raise ValueError('retained immutable website version was not found')
        hashes = {}
        for path in FILES:
            key = path.replace('/', '--')
            raw = base64.b64decode(desired['binaryData'][key], validate=True) if path.endswith('.ttf') else desired['data'][key].encode()
            hashes[path] = hashlib.sha256(raw).hexdigest()
    else:
        if not a.dry_run and subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip():
            raise ValueError('commit the validated website changes before deployment')
        verify_source(a.directory.resolve())
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        desired, hashes = configmap(a.directory.resolve(), commit, a.namespace, a.deployment)
    volume = version_volume(desired['metadata']['name'])
    # Validate both operations before creating a retained version or activating it.
    ensure_configmap(kube, desired, dry_run=True)
    kube.patch(previous, volume, dry_run=True)
    report = {'namespace': a.namespace, 'deployment': a.deployment, 'configmap': desired['metadata']['name'],
              'previous_configmap': old_volume['configMap']['name'], 'hashes': hashes, 'deployed': False}
    if a.dry_run:
        print(json.dumps(report, indent=2))
        return
    evidence = ROOT / 'test-evidence/website-deploy' / (desired['metadata']['name'] + '-' + uuid.uuid4().hex[:8])
    evidence.mkdir(parents=True, mode=0o700)
    for name, obj in [('deployment-before', previous), ('content-before', kube.get('configmap', old_volume['configMap']['name']))]:
        path = evidence / (name + '.json')
        path.write_text(json.dumps(obj, indent=2) + '\n'); path.chmod(0o600)
    ensure_configmap(kube, desired)
    activate(kube, previous, volume, hashes)
    report['deployed'] = True
    report['evidence'] = str(evidence)
    (evidence / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
