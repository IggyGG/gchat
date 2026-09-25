#!/usr/bin/env python3
"""Dispatch once and reconcile exact-source GitHub workers by durable request ID."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
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


def gh(path, *, method='GET', body=None):
    command = ['gh', 'api', '--method', method, 'repos/' + REPO + '/' + path]
    if body is not None: command += ['--input', '-']
    raw = subprocess.check_output(command, input=None if body is None else canonical(body), stderr=subprocess.PIPE)
    return json.loads(raw) if raw.strip() else None


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
            path = Path(original)
            if (path.is_absolute() or '..' in path.parts or '\\' in original or '\0' in original or
                ':' in original or path.as_posix() in seen or
                (entry.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError('unsafe worker archive path')
            seen.add(path.as_posix())
        bundle.extractall(destination)


def collect(manifest, target, work, request_id, reconcile=False):
    workflow, prefix = WORKFLOWS[target]
    marker = work / 'dispatch.json'
    expected = manifest['sources']['gchat']['commit']
    matches = []
    # Reconciliation never trusts a branch name or the most recent run alone.
    for page in range(1, 11):
        runs = gh(f'actions/workflows/{workflow}/runs?event=workflow_dispatch&per_page=100&page={page}')['workflow_runs']
        matches += [r for r in runs if r.get('display_title') == prefix + request_id]
        if len(runs) < 100 or matches: break
    if len(matches) > 1: raise ValueError('duplicate external request IDs require reconciliation')
    if not matches:
        if marker.exists():
            if marker.exists() and time.time() - json.loads(marker.read_text())['at'] > 1800:
                raise ValueError('worker dispatch not visible after 30 minutes; no blind resubmission')
            return None
        refs = manifest['refs']
        for project in ('gchat', 'gcoms'):
            ref_path = refs[project].removeprefix('refs/')
            try:
                visible = json.loads(subprocess.check_output(['gh','api',f'repos/IggyGG/{project}/git/ref/{ref_path}'],stderr=subprocess.PIPE))
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
    run = matches[0]
    if (run['head_sha'] != expected or run['event'] != 'workflow_dispatch'
            or run.get('head_repository', {}).get('full_name') != REPO
            or run['path'] != '.github/workflows/' + workflow):
        raise ValueError('worker run does not bind the requested source/workflow')
    if run['status'] != 'completed': return None
    if run['conclusion'] != 'success': raise ValueError('native worker failed; retained provider run ' + str(run['id']))
    artifacts = gh(f'actions/runs/{run["id"]}/artifacts?per_page=100')['artifacts']
    name = target if target.startswith(('linux', 'macos', 'windows')) else f'{target}-{expected}-{manifest["sources"]["gcoms"]["commit"]}'
    if target == 'ios': name += '-' + manifest['versions']['ios']
    selected = [a for a in artifacts if a['name'] == name and not a['expired']]
    if len(selected) != 1: raise ValueError('exact native artifact is missing or ambiguous')
    artifact = selected[0]; digest = artifact.get('digest', '')
    if not re.fullmatch('sha256:[0-9a-f]{64}', digest): raise ValueError('provider artifact has no immutable digest')
    if not 0 < artifact['size_in_bytes'] <= 12 * 1024 ** 3:
        raise ValueError('native archive exceeds download budget')
    archive = work / 'native.zip'
    if not archive.exists():
        partial = work / 'native.partial'
        with partial.open('wb') as stream:
            subprocess.run(['gh', 'api', f'repos/{REPO}/actions/artifacts/{artifact["id"]}/zip'],
                           stdout=stream, stderr=subprocess.PIPE, check=True, timeout=600)
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
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--reconcile', action='store_true')
    args = p.parse_args()
    manifest = validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()))
    output = Path(os.environ['GCHAT_RELEASE_RECEIPT']); work = output.parent
    result = collect(manifest, os.environ['GCHAT_RELEASE_TARGET'], work, os.environ['GCHAT_RELEASE_REQUEST_ID'], args.reconcile)
    if result is None: raise SystemExit(75)
    atomic_json(output, result)


if __name__ == '__main__': main()
