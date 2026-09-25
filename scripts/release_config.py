#!/usr/bin/env python3
"""Render the production controller configuration; credentials remain references."""
import argparse,json
from pathlib import Path
from release_coordinator import atomic_json
from release_ledger import PLATFORMS


def configuration(state=Path('/state'),scripts=Path('/opt/gchat/scripts'),config=Path('/config')):
    def recipe(name,*args,timeout=120):
        argv=['python3',str(scripts/name),*map(str,args)]
        return {'run':argv,'reconcile':argv,'timeout':timeout}
    workers={}
    for target in PLATFORMS:
        if target=='sdk':
            sdk=recipe('release_sdk.py','--state',state,'--public-root',state/'public/updates','--public-url','https://gchat.boo/updates',timeout=1800)
            workers[target]={stage:sdk for stage in ('build','verify','compatibility','publish')};continue
        build=recipe('release_jobs.py',timeout=900)
        build['reconcile']=[*build['run'],'--reconcile']
        workers[target]={'build':build,
            'verify':recipe('release_verify.py','--state',state,'--android-tools','/usr/bin',timeout=600),
            'compatibility':recipe('release_compatibility.py','--receipts',state/'acceptance')}
        if target in ('android','ios'):
            workers[target].update({stage:recipe('release_store_worker.py','--state',state,'--config',config/'stores.json',timeout=600) for stage in ('submit','observe')})
        else:workers[target]['publish']=recipe('release_publish.py','--state',state,'--config',config/'publisher.json',timeout=900)
    return {'schema':1,'maintenance':{'apt':{'root':str(state/'public/updates/apt'),'key':'F4F6F8550D2AA952A189640D58430838AA3230BB'}},'minimum_free_bytes':16*1024**3,'workers':workers,
        'discovery':{'gchat':{'mirror':str(state/'mirrors/gchat.git'),'url':'https://github.com/IggyGG/gchat.git'},
            'gcoms':{'mirror':str(state/'mirrors/gcoms.git'),'url':'https://github.com/IggyGG/gcoms.git'},
            'version_floor':{'desktop':'0.1.4','android':'1019','ios':'1.0.23'},'settle_seconds':60,
            'candidate_remotes':['https://github.com/IggyGG/gchat.git'],
            'companion_remotes':['https://github.com/IggyGG/gcoms.git']}}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    atomic_json(a.output/'controller.json',configuration())
    policy=json.loads((Path(__file__).resolve().parents[1]/'release/automation/policy.json').read_text())
    atomic_json(a.output/'publisher.json',{'public_root':'/state/public/updates','public_url':'https://gchat.boo/updates',
        'public_key':policy['updater_public_key'],'signer':['python3','/opt/gchat/automation/sign-update'],
        'gpg_key':'F4F6F8550D2AA952A189640D58430838AA3230BB'})
    atomic_json(a.output/'stores.json',{'android':{'credentials':'/keys/google-service-account.json',
        'service_account':'firebase-adminsdk-fbsvc@gchat-23115.iam.gserviceaccount.com','package':'boo.gchat.app','track':'production'},
        'ios':{'key':'/keys/apple-api.p8','key_id':'69NXP2NMH3','issuer':'b95de41a-e38c-4659-ad6a-0c53dfc5f166',
            'app_id':'6814308446','encryption_declaration':'670c5156-d5db-40f6-a137-3417dae28965'}})

if __name__=='__main__':main()
