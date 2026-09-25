#!/usr/bin/env python3
"""Publish qualified desktop updates and observe their exact public bytes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.request
from release_pair import canonical, validate
from release_coordinator import atomic_json, read_receipt
from release_feed import publish, digest
from release_apt import build as publish_apt


def job(state, manifest, platform, stage):
    key=hashlib.sha256(canonical([manifest['release_id'],platform,stage])).hexdigest()
    return state/'jobs'/key


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--state',type=Path,required=True);p.add_argument('--config',type=Path,required=True);a=p.parse_args()
    config=json.loads(a.config.read_text());manifest=validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()))
    platform=os.environ['GCHAT_RELEASE_TARGET'];output=Path(os.environ['GCHAT_RELEASE_RECEIPT'])
    verified=job(a.state,manifest,platform,'verify')/'receipt.json'
    compatibility=job(a.state,manifest,platform,'compatibility')/'receipt.json'
    proof,_=read_receipt(verified,manifest,platform,'verify');read_receipt(compatibility,manifest,platform,'compatibility')
    paths=[verified.parent/i['path'] for i in proof['evidence']]
    endings={'linux-x86_64':'.AppImage','macos-aarch64':'.app.tar.gz','macos-x86_64':'.app.tar.gz','windows-x86_64':'.exe'}
    payloads=[x for x in paths if x.name.endswith(endings[platform])]
    # Installers and updater payloads can be the same NSIS bytes; deduplicate by hash.
    payloads=list({digest(x):x for x in payloads}.values())
    if len(payloads)!=1:raise ValueError('verified updater payload missing or ambiguous')
    payload=payloads[0]
    # Verification stored names as SHA256-originalname. Match the original basename.
    original=payload.name[65:]
    signatures=[x for x in paths if x.name[65:]==original+'.sig']
    if len(signatures)!=1:raise ValueError('verified updater signature missing or ambiguous')
    root=Path(config['public_root'])
    feed=publish(manifest,platform,payload,signatures[0].read_text(),root,config['public_url'],
                 manifest['policy']['updater_public_key'],config['signer'],verified,compatibility)
    if platform=='linux-x86_64':
        packages=[x for x in paths if x.name.endswith('.deb')]
        if len(packages)!=1:raise ValueError('verified Debian package missing')
        signatures=[x for x in paths if x.name[65:]==packages[0].name[65:]+'.asc']
        if len(signatures)!=1:raise ValueError('verified Debian signature missing')
        publish_apt(manifest,packages[0],signatures[0],verified,compatibility,root/'apt',config['gpg_key'])
    # Availability requires the actual public URL to serve the candidate pointer.
    binding=json.loads(feed['binding']);os_name,arch=binding['target'].split('-',1)
    url=config['public_url'].rstrip('/')+'/desktop/'+os_name+'/'+arch+'/latest.json'
    with urllib.request.urlopen(url,timeout=30) as response:
        if response.url!=url:raise ValueError('public update endpoint redirected')
        public=json.loads(response.read(32769))
    if public!=feed:raise ValueError('public feed has not reached the qualified candidate')
    # Read the public artifact too: a healthy pointer cannot mask a missing or
    # corrupted payload, including after a interrupted volume restore.
    observed = hashlib.sha256(); size = 0
    with urllib.request.urlopen(feed['url'], timeout=60) as response:
        if response.url != feed['url']: raise ValueError('public artifact redirected')
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > binding['size']: raise ValueError('public artifact exceeds signed size')
            observed.update(chunk)
    if size != binding['size'] or observed.hexdigest() != binding['sha256']:
        raise ValueError('public artifact bytes differ from signed binding')
    result=output.parent/'public-feed.json' ;atomic_json(result,public)
    atomic_json(output,{'schema':1,'release_id':manifest['release_id'],'sources':manifest['sources'],
        'platform':platform,'stage':'publish','passed':True,'source_unchanged':True,
        'evidence':[{'path':result.name,'sha256':digest(result)}]})


if __name__=='__main__':main()
