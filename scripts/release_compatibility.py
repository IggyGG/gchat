#!/usr/bin/env python3
"""Bind a recent, successful installed-network acceptance run to publication.

The fleet owner writes this receipt after its normal canary/serial rollout. The
coordinator cannot turn component CI, an old relay observation, or upload success
into a live compatibility pass.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
from release_pair import validate
from release_coordinator import atomic_json


def verify(proof, manifest, now):
    if (proof.get('schema') != 1 or proof.get('passed') is not True or
        proof.get('sources') != manifest['sources'] or proof.get('release_id') != manifest['release_id'] or
        proof.get('carrier_profile') != manifest['policy']['carrier_profile']):
        raise ValueError('installed network acceptance does not bind this exact candidate')
    if type(proof.get('completed_at')) is not int or not 0 <= now - proof['completed_at'] <= 3600:
        raise ValueError('installed network acceptance is missing, stale or future-dated')
    required = set(manifest['policy']['required_checks'])
    checks = proof.get('checks', {})
    if any(checks.get(name) is not True for name in required):
        raise ValueError('required application/upgrade acceptance remains incomplete')
    relays = proof.get('relays', [])
    if len(relays) != 8 or len({r.get('id') for r in relays}) != 8 or any(
            r.get('healthy') is not True or r.get('gcoms_commit') != manifest['sources']['gcoms']['commit']
            or r.get('carrier_profile') != manifest['policy']['carrier_profile'] for r in relays):
        raise ValueError('all eight compatible relay observations are required')
    if proof.get('rollback_state_compatible') is not True:
        raise ValueError('rollback does not preserve the active profile format')
    return proof


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipts',type=Path,required=True);a=p.parse_args()
    manifest=validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()))
    source=a.receipts/(manifest['release_id']+'.json')
    if not source.is_file(): raise SystemExit(75)
    proof=verify(json.loads(source.read_text()),manifest,int(time.time()))
    output=Path(os.environ['GCHAT_RELEASE_RECEIPT']);dest=output.parent/'network-acceptance.json';shutil.copyfile(source,dest)
    linked=[]
    for ref in proof.get('evidence',[]):
        path=(source.parent/ref['path']).resolve()
        if not path.is_relative_to(source.parent.resolve()) or not path.is_file():raise ValueError('acceptance evidence missing or outside its directory')
        with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if digest!=ref['sha256']:raise ValueError('acceptance evidence changed')
        copy=output.parent/('acceptance-'+digest);shutil.copyfile(path,copy);linked.append({'path':copy.name,'sha256':digest})
    if not linked:raise ValueError('acceptance has no retained evidence')
    linked.append({'path':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
    atomic_json(output,{'schema':1,'release_id':manifest['release_id'],'sources':manifest['sources'],'platform':os.environ['GCHAT_RELEASE_TARGET'],
                       'stage':'compatibility','passed':True,'source_unchanged':True,'relay_compatible':True,'evidence':linked})


if __name__=='__main__':main()
