#!/usr/bin/env python3
"""Distribute exact-source SDK qualification archives, never hot-update consumers.

Runs the existing native Rust matrix and both mobile variants (base/push). All
three jobs bind the immutable companion ref; unchanged SDK inputs reuse receipts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
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
    args=['gh','api','--method','POST' if body is not None else 'GET','repos/'+REPO+'/'+path]
    if body is not None:args+=['--input','-']
    result=subprocess.check_output(args,input=canonical(body) if body is not None else None,stderr=subprocess.PIPE)
    return json.loads(result) if result.strip() else None

def expected_names(kind,commit):
    if kind=='rust':return {f'rust-integrations-{runner}-{commit}' for runner in ('ubuntu-24.04','macos-15','macos-15-intel','windows-2022')}
    variant='push' if kind.endswith('push') else 'base'
    return {f'mobile-{platform}-{role}-{variant}-{commit}' for platform in ('android','apple') for role in ('client','relay')}

def build(manifest,cache):
    commit=manifest['sources']['gcoms']['commit'];cache=cache/commit;cache.mkdir(parents=True,exist_ok=True)
    complete=True;archives=[]
    for kind,(workflow,prefix,inputs) in JOBS.items():
        work=cache/kind;work.mkdir(exist_ok=True);request=hashlib.sha256(canonical([commit,kind])).hexdigest()
        found=[]
        for page in range(1,11):
            runs=api(f'actions/workflows/{workflow}/runs?event=workflow_dispatch&per_page=100&page={page}')['workflow_runs']
            found += [r for r in runs if r.get('display_title')==prefix+request]
            if len(runs)<100 or found:break
        if len(found)>1:raise ValueError('duplicate SDK dispatch requires reconciliation')
        if not found:
            marker=work/'dispatch.json'
            if not marker.exists():
                atomic_json(marker,{'at':int(time.time()),'request':request,'commit':commit})
                api(f'actions/workflows/{workflow}/dispatches',{'ref':manifest['refs']['gcoms'].removeprefix('refs/heads/'),
                    'inputs':{'request_id':request,**inputs}})
            elif time.time()-json.loads(marker.read_text())['at']>1800:
                raise ValueError('SDK dispatch outcome unknown; no blind resubmission')
            complete=False;continue
        run=found[0]
        if run['head_sha']!=commit or run.get('head_repository',{}).get('full_name')!=REPO or run['path']!='.github/workflows/'+workflow:
            raise ValueError('SDK workflow/source mismatch')
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
                with temporary.open('wb') as stream:subprocess.run(['gh','api',f'repos/{REPO}/actions/artifacts/{artifact["id"]}/zip'],stdout=stream,stderr=subprocess.PIPE,check=True,timeout=600)
                if 'sha256:'+digest(temporary)!=expected:raise ValueError('SDK archive download mismatch')
                os.replace(temporary,path)
            if 'sha256:'+digest(path)!=expected:raise ValueError('retained SDK archive changed')
            archives.append(path)
        atomic_json(work/'run.json',{k:run[k] for k in ('id','head_sha','path','conclusion','html_url')})
        archives.append(work/'run.json')
    return archives if complete else None

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--state',type=Path,required=True);p.add_argument('--public-root',type=Path,required=True);a=p.parse_args()
    manifest=validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()));stage=os.environ['GCHAT_RELEASE_STAGE'];output=Path(os.environ['GCHAT_RELEASE_RECEIPT'])
    evidence=[]
    if stage=='build':
        paths=build(manifest,a.state/'sdk-cache')
        if paths is None:raise SystemExit(75)
        retained=output.parent/'archives';retained.mkdir(exist_ok=True)
        for i,path in enumerate(paths):
            target=retained/(str(i)+'-'+path.name)
            if not target.exists():os.link(path,target)
            evidence.append({'path':target.relative_to(output.parent).as_posix(),'sha256':digest(target)})
    elif stage in ('verify','compatibility','publish'):
        previous='build' if stage=='verify' else 'verify'
        source=job(a.state,manifest,'sdk',previous)/'receipt.json';proof,_=read_receipt(source,manifest,'sdk',previous)
        retained=output.parent/'evidence';retained.mkdir(exist_ok=True)
        for item in proof['evidence']:
            path=source.parent/item['path'];target=retained/path.name
            if stage=='verify' and path.suffix=='.zip':
                import tempfile
                with tempfile.TemporaryDirectory(prefix='sdk-check-') as temporary:extract(path,Path(temporary))
            if not target.exists():os.link(path,target)
            evidence.append({'path':target.relative_to(output.parent).as_posix(),'sha256':digest(target)})
        if stage=='publish':
            public=a.public_root/'sdk';public.mkdir(parents=True,exist_ok=True)
            pointer=public/'latest.json';number=manifest['versions']['sdk']
            if pointer.exists() and version(json.loads(pointer.read_text())['version'])>version(number):raise ValueError('cannot regress SDK publication')
            records=[]
            for item in evidence:
                path=output.parent/item['path']
                if path.suffix!='.zip':continue
                target=public/manifest['release_id']/path.name;target.parent.mkdir(exist_ok=True)
                if not target.exists():shutil.copyfile(path,target)
                if digest(target)!=item['sha256']:raise ValueError('published SDK archive changed')
                target.chmod(0o644);records.append({'path':target.relative_to(public).as_posix(),'sha256':item['sha256']})
            atomic_json(pointer,{'schema':1,'release_id':manifest['release_id'],'sources':manifest['sources'],'version':number,
                'qualification':'native desktop and emulator/simulator; physical devices and live push deferred','archives':records})
            pointer.chmod(0o644)
    else:raise ValueError('unknown SDK stage')
    atomic_json(output,{'schema':1,'release_id':manifest['release_id'],'sources':manifest['sources'],'platform':'sdk','stage':stage,
        'passed':True,'source_unchanged':True,'consumers_compatible':True,'evidence':evidence})

if __name__=='__main__':main()
