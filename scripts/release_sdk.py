#!/usr/bin/env python3
"""Distribute exact-source SDK qualification archives, never hot-update consumers.

Runs the existing native Rust matrix and both mobile variants (base/push). All
three jobs bind the immutable companion ref; unchanged SDK inputs reuse receipts.
"""
from release_provider import github_download
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import tempfile
import urllib.request
import re
from release_pair import canonical, validate
from release_coordinator import atomic_json, read_receipt
from release_feed import digest, version
from release_jobs import extract
from release_publish import job

REPO='IggyGG/gcoms'
JOBS={'rust':('rust-integrations.yml','GComs SDK Rust ',{}),
      'mobile-base':('mobile-integrations.yml','GComs SDK Mobile ',{'platform':'all','role':'all','push':False}),
      'mobile-push':('mobile-integrations.yml','GComs SDK Mobile ',{'platform':'all','role':'all','push':True})}

def api(path,body=None):
    from release_provider import github
    return github(path, repo=REPO, method='POST' if body is not None else 'GET', body=body)

def expected_names(kind,commit):
    if kind=='rust':return {f'rust-integrations-{runner}-{commit}' for runner in ('ubuntu-24.04','macos-15','macos-15-intel','windows-2022')}
    variant='push' if kind.endswith('push') else 'base'
    return {f'mobile-{platform}-{role}-{variant}-{commit}' for platform in ('android','apple') for role in ('client','relay')}

def matching_run(run, kind, commit, request, prefix):
    if run.get('head_sha') != commit:
        return False
    if run.get('event') == 'workflow_dispatch':
        return run.get('display_title') == prefix + request
    # Main already runs the full native Rust and base mobile matrices. Reuse
    # that exact-source work; the optional push variant still needs its own job.
    return (kind in ('rust', 'mobile-base') and run.get('event') == 'push'
            and run.get('head_branch') == 'main'
            and run.get('display_title') == prefix + commit)


def select_run(found, commit, workflow, dispatched):
    for run in found:
        if (run.get('head_sha') != commit
                or run.get('head_repository', {}).get('full_name') != REPO
                or run.get('path') != '.github/workflows/' + workflow):
            raise ValueError('SDK workflow/source mismatch')
    requested = [run for run in found if run.get('event') == 'workflow_dispatch']
    if len(requested) > 1 or (not requested and len(found) > 1):
        raise ValueError('duplicate SDK dispatch requires reconciliation')
    if requested:
        return requested[0]
    # An attempted/observed dispatch owns this request even while GitHub's
    # listing is incomplete. A main-push pass cannot replace its unknown result.
    return None if dispatched or not found else found[0]


def qualification_inputs(repository, commit):
    """Retain every build, test, feature, platform and toolchain input."""
    from release_inputs import GCOMS_STATUS_FILES
    # Python validators remain inputs even when application admission calls
    # them controller-only. Only reviewed prose/status can share qualification.
    excluded = {name for name in GCOMS_STATUS_FILES
                if name.endswith('.md') or name.startswith('docs/evidence/')}
    raw = subprocess.check_output(['git', '-C', str(repository), 'ls-tree', '-rz', '--full-tree', commit],
                                  stderr=subprocess.PIPE, timeout=30)
    entries = []
    for record in raw.split(b'\0'):
        if not record:
            continue
        metadata, path = record.split(b'\t', 1)
        name = path.decode('utf-8')
        if name not in excluded:
            entries.append([name, *metadata.decode('ascii').split()])
    return hashlib.sha256(canonical(sorted(entries))).hexdigest()


def reuse_qualification(manifest, cache, kind=None):
    """Reuse a completed provider matrix; preserve all original source labels."""
    commit = manifest['sources']['gcoms']['commit']
    mirror = cache.parent / 'mirrors/gcoms.git'
    if not mirror.is_dir() or not cache.is_dir():
        return None
    wanted = qualification_inputs(mirror, commit)
    required = {kind: JOBS[kind]} if kind is not None else JOBS
    candidates = [p for p in cache.iterdir() if p.is_dir() and not p.is_symlink()
                  and re.fullmatch('[0-9a-f]{40}', p.name) and p.name != commit]
    for root in sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[:32]:
        try:
            if qualification_inputs(mirror, root.name) != wanted:
                continue
        except subprocess.CalledProcessError:
            continue  # A missing old source cannot qualify a cache hit.
        paths, runs = [], []
        for matrix, (workflow, prefix, _) in required.items():
            directory = root / matrix
            marker = directory / 'run.json'
            if not marker.is_file():
                break
            original = json.loads(marker.read_text())
            if (original.get('conclusion') != 'success' or original.get('head_sha') != root.name
                    or original.get('path') != '.github/workflows/' + workflow):
                break
            names = expected_names(matrix, root.name)
            if any(not (directory / (name + '.zip')).is_file() for name in names):
                break
            # Recheck provider identity and immutable archive hashes. A local
            # cache marker or a cancelled/partial job cannot manufacture a pass.
            run = api('actions/runs/' + str(original['id']))
            if (run.get('id') != original['id'] or run.get('status') != 'completed'
                    or run.get('conclusion') != 'success' or run.get('head_sha') != root.name
                    or run.get('path') != original['path']
                    or run.get('head_repository', {}).get('full_name') != REPO):
                break
            metadata = api(f"actions/runs/{run['id']}/artifacts?per_page=100")['artifacts']
            selected = [a for a in metadata if a['name'] in names and not a.get('expired')]
            if len(selected) != len(names) or {a['name'] for a in selected} != names:
                break
            for artifact in selected:
                path = directory / (artifact['name'] + '.zip')
                if (path.stat().st_size != artifact['size_in_bytes']
                        or 'sha256:' + digest(path) != artifact.get('digest')):
                    raise ValueError('cached qualification archive changed')
                paths.append(path)
            paths.append(marker)
            runs.append({'kind': matrix, 'id': run['id'], 'source': root.name})
        else:
            output = cache / commit / ((kind + '-' if kind is not None else '') + 'qualification-reuse.json')
            binding = {'schema': 1, 'requested_source': commit, 'original_qualification_source': root.name,
                       'qualification_inputs_sha256': wanted, 'provider_runs': runs,
                       'original_source_labels_preserved': True,
                       'archives': [{'name': p.name, 'sha256': digest(p)} for p in paths if p.suffix == '.zip']}
            atomic_json(output, binding)
            return [*paths, output]
    return None

def build(manifest,cache):
    original_cache = cache
    commit=manifest['sources']['gcoms']['commit'];cache=cache/commit;cache.mkdir(parents=True,exist_ok=True)
    complete=True;archives=[]
    for kind,(workflow,prefix,inputs) in JOBS.items():
        reused = reuse_qualification(manifest, original_cache, kind)
        if reused is not None:
            archives.extend(reused)
            continue
        work=cache/kind;work.mkdir(exist_ok=True);request=hashlib.sha256(canonical([commit,kind])).hexdigest()
        marker=work/'dispatch.json'
        found=[]
        for page in range(1,11):
            runs=api(f'actions/workflows/{workflow}/runs?per_page=100&page={page}')['workflow_runs']
            found += [r for r in runs if matching_run(r,kind,commit,request,prefix)
                      or (r.get('event') == 'workflow_dispatch' and r.get('display_title') == prefix + request)]
            if len(runs)<100:break
        # Retain both independently created provider records; selecting one
        # neither cancels the other nor changes its source or original result.
        for run in found:
            retained = work / ('observed-run-' + str(int(run['id'])) + '.json')
            if not retained.exists():atomic_json(retained,run)
        run=select_run(found,commit,workflow,marker.exists())
        if run is None:
            if not marker.exists():
                atomic_json(marker,{'at':int(time.time()),'request':request,'commit':commit})
                api(f'actions/workflows/{workflow}/dispatches',{'ref':manifest['refs']['gcoms'].removeprefix('refs/heads/'),
                    'inputs':{'request_id':request,**inputs}})
            elif time.time()-json.loads(marker.read_text())['at']>1800:
                raise ValueError('SDK dispatch outcome unknown; no blind resubmission')
            complete=False;continue
        if run.get('event') == 'workflow_dispatch' and not marker.exists():
            atomic_json(marker,{'at':int(time.time()),'request':request,'commit':commit,'observed_run':run['id']})
        if run['status']!='completed':complete=False;continue
        if run['conclusion']!='success':raise ValueError('native SDK qualification failed: '+str(run['id']))
        values=api(f'actions/runs/{run["id"]}/artifacts?per_page=100')['artifacts'];names=expected_names(kind,commit)
        selected=[a for a in values if a['name'] in names and not a['expired']]
        if {a['name'] for a in selected}!=names or len(selected)!=len(names):raise ValueError('SDK matrix artifacts missing')
        for artifact in selected:
            path=work/(artifact['name']+'.zip');expected=artifact.get('digest','')
            if not expected.startswith('sha256:') or len(expected)!=71:raise ValueError('SDK archive has no immutable digest')
            if not 0<artifact['size_in_bytes']<=2*1024**3:raise ValueError('SDK archive exceeds storage budget')
            if not path.exists():
                temporary=path.with_suffix('.partial')
                with temporary.open('wb') as stream:github_download(f'actions/artifacts/{artifact["id"]}/zip', repo=REPO, stream=stream, timeout=600)
                if 'sha256:'+digest(temporary)!=expected:raise ValueError('SDK archive download mismatch')
                os.replace(temporary,path)
            if 'sha256:'+digest(path)!=expected:raise ValueError('retained SDK archive changed')
            archives.append(path)
        atomic_json(work/'run.json',{k:run[k] for k in ('id','head_sha','path','conclusion','html_url')})
        archives.append(work/'run.json')
    return archives if complete else None

def publish_archives(manifest, paths, public, qualification_reuse=None):
    """Copy immutable archives before atomically advertising the complete set."""
    public.mkdir(parents=True, exist_ok=True)
    with (public / '.publication.lock').open('a+b') as lock:
        if os.name == 'nt':
            import msvcrt
            lock.seek(0); lock.write(b'\0'); lock.flush(); lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
        return publish_locked(manifest, paths, public, qualification_reuse)


def publish_locked(manifest, paths, public, qualification_reuse):
    public.mkdir(parents=True, exist_ok=True)
    pointer = public / 'latest.json'
    number = manifest['versions']['sdk']
    historical = False
    if pointer.exists():
        previous = json.loads(pointer.read_text())
        historical = version(previous['version']) > version(number)
        if previous['version'] == number and previous['release_id'] != manifest['release_id']:
            raise ValueError('SDK version already belongs to another source pair')
    records = []
    for path, expected in paths:
        target = public / manifest['release_id'] / path.name
        target.parent.mkdir(exist_ok=True)
        if not target.exists():
            stream = tempfile.NamedTemporaryFile(dir=target.parent, delete=False)
            temporary = Path(stream.name)
            try:
                with stream:
                    with path.open('rb') as source: shutil.copyfileobj(source, stream)
                    stream.flush(); os.fsync(stream.fileno())
                # Windows forbids reopening/renaming/deleting this file while
                # NamedTemporaryFile still holds its non-sharing handle.
                if digest(temporary) != expected: raise ValueError('SDK source archive changed')
                temporary.chmod(0o644); os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
        if digest(target) != expected: raise ValueError('published SDK archive changed')
        records.append({'path': target.relative_to(public).as_posix(), 'sha256': expected,
                        'size': target.stat().st_size})
    if not records: raise ValueError('SDK publication has no archives')
    report = {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'],
              'version': number, 'qualification': 'native desktop and emulator/simulator; physical devices and live push deferred',
              'archives': records}
    if qualification_reuse is not None:
        report['qualification_reuse'] = qualification_reuse
    index = public / manifest['release_id'] / 'index.json'
    if index.exists() and json.loads(index.read_text()) != report:
        raise ValueError('immutable SDK index changed')
    atomic_json(index, report); index.chmod(0o644)
    if not historical:
        atomic_json(pointer, report); pointer.chmod(0o644)
    return report


def verify_public(report, base):
    """Availability includes the publicly served immutable bytes."""
    url = base.rstrip('/') + '/sdk/' + report['release_id'] + '/index.json'
    with urllib.request.urlopen(url, timeout=30) as response:
        if response.url != url or json.loads(response.read(65537)) != report:
            raise ValueError('public SDK index differs from the candidate')
    for item in report['archives']:
        url = base.rstrip('/') + '/sdk/' + item['path']
        sha = hashlib.sha256(); size = 0
        with urllib.request.urlopen(url, timeout=60) as response:
            if response.url != url: raise ValueError('public SDK archive redirected')
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > item['size']: raise ValueError('public SDK archive exceeds qualified size')
                sha.update(chunk)
        if size != item['size'] or sha.hexdigest() != item['sha256']:
            raise ValueError('public SDK archive differs from qualification')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--state',type=Path,required=True);p.add_argument('--public-root',type=Path,required=True);p.add_argument('--public-url',required=True);a=p.parse_args()
    manifest=validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()));stage=os.environ['GCHAT_RELEASE_STAGE'];output=Path(os.environ['GCHAT_RELEASE_RECEIPT'])
    evidence=[]
    qualification_reuse = None
    if stage=='build':
        paths=build(manifest,a.state/'sdk-cache')
        if paths is None:raise SystemExit(75)
        retained=output.parent/'archives';retained.mkdir(exist_ok=True)
        for i,path in enumerate(paths):
            if path.name.endswith('qualification-reuse.json'):
                if qualification_reuse is None:
                    qualification_reuse = {'schema': 1, 'matrices': []}
                qualification_reuse['matrices'].append(json.loads(path.read_text()))
            target=retained/(str(i)+'-'+path.name)
            if not target.exists():os.link(path,target)
            evidence.append({'path':target.relative_to(output.parent).as_posix(),'sha256':digest(target)})
    elif stage in ('verify','compatibility','publish'):
        previous='build' if stage=='verify' else 'verify'
        source=job(a.state,manifest,'sdk',previous)/'receipt.json';proof,_=read_receipt(source,manifest,'sdk',previous)
        qualification_reuse = proof.get('qualification_reuse')
        retained=output.parent/'evidence';retained.mkdir(exist_ok=True)
        for item in proof['evidence']:
            path=source.parent/item['path'];target=retained/path.name
            if stage=='verify' and path.suffix=='.zip':
                import tempfile
                with tempfile.TemporaryDirectory(prefix='sdk-check-') as temporary:extract(path,Path(temporary))
            if not target.exists():os.link(path,target)
            evidence.append({'path':target.relative_to(output.parent).as_posix(),'sha256':digest(target)})
        if stage=='publish':
            paths=[(output.parent/item['path'],item['sha256']) for item in evidence if item['path'].endswith('.zip')]
            report=publish_archives(manifest, paths, a.public_root/'sdk', qualification_reuse)
            verify_public(report, a.public_url)
            result=output.parent/'public-sdk.json';atomic_json(result,report)
            evidence.append({'path':result.name,'sha256':digest(result)})
    else:raise ValueError('unknown SDK stage')
    atomic_json(output,{'schema':1,'release_id':manifest['release_id'],'sources':manifest['sources'],'platform':'sdk','stage':stage,
        'passed':True,'source_unchanged':True,'consumers_compatible':True,'evidence':evidence,
        **({'qualification_reuse':qualification_reuse} if qualification_reuse is not None else {})})

if __name__ == '__main__':
    from release_provider import worker_main
    worker_main(main)
