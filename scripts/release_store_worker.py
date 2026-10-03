#!/usr/bin/env python3
"""Source-qualified mobile publication adapter with durable provider journals."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import time
from release_pair import canonical,validate
from release_coordinator import atomic_json,read_receipt
from release_publish import job
from release_feed import digest
from release_stores import google,apple,submit_google,submit_apple,observe_google,observe_apple
from release_jobs import gh


def observe_encryption(api,config,manifest,work):
    declaration=api.request('GET','/v1/appEncryptionDeclarations/'+config['encryption_declaration'])['data']
    atomic_json(work/'encryption-observation.json', {'schema':1,'release_id':manifest['release_id'],
        'sources':manifest['sources'],'at':int(time.time()),
        'declaration':config['encryption_declaration'],
        'state':declaration['attributes'].get('appEncryptionDeclarationState'),
        'includes_france':declaration['attributes'].get('availableOnFrenchStore') is True})
    return declaration


def ios_build(api,config,manifest,build_job,work):
    # Apple's external encryption decision blocks only the iOS lane. The same
    # already-qualified IPA is uploaded after approval; it is never rebuilt.
    declaration=observe_encryption(api,config,manifest,work)
    if declaration['attributes'].get('appEncryptionDeclarationState')!='APPROVED':
        return None,'Apple encryption declaration is still awaiting approval'
    if declaration['attributes'].get('availableOnFrenchStore') is not True:raise ValueError('approved declaration must include France')
    number=manifest['versions']['ios']
    builds=api.request('GET','/v1/builds',params={'filter[app]':config['app_id'],'filter[version]':number,'include':'app','limit':10})['data']
    if len(builds)>1:raise ValueError('multiple Apple builds use the reserved build number')
    marker=work/'upload-dispatch.json';request=hashlib.sha256(canonical([manifest['release_id'],'ios','upload'])).hexdigest()
    proof,_=read_receipt(build_job/'receipt.json',manifest,'ios','build')
    recovered=proof.get('retained_ios_followup') is True
    workflow='ios-upload.yml';title='GChat iOS upload ';controller=manifest['sources']['gchat']['commit']
    if recovered:
        from release_ios_recovery import RULE, reviewed_inputs
        rule_path=build_job/'ios-recovery.json'
        if rule_path.is_file():
            if not any(e['path']=='ios-recovery.json' and e['sha256']==digest(rule_path) for e in proof['evidence']):
                raise ValueError('retained iOS upload registration is not source-bound')
            rule=json.loads(rule_path.read_text())
        else:
            rule=RULE  # Legacy retained release before registrations were data.
        if manifest['release_id']!=rule['release_id']:raise ValueError('unregistered retained iOS upload')
        reviewed=reviewed_inputs(manifest,rule)
        workflow='ios-verify.yml';title='iOS retained verification ';controller=rule['controller']
    runs=gh('actions/workflows/'+workflow+'/runs?event=workflow_dispatch&per_page=100')['workflow_runs']
    matches=[r for r in runs if r.get('display_title')==title+request]
    if len(matches)>1:raise ValueError('duplicate Apple upload workers require reconciliation')
    if not matches:
        if not marker.exists():
            if builds:raise ValueError('Apple build number is already used without this source-bound upload')
            archive=next(e['sha256'] for e in proof['evidence'] if e['path']=='native.zip')
            if recovered:
                if archive!=rule['sha256']:raise ValueError('retained iOS archive differs before upload')
                inputs={'request_id':request,'original_run_id':str(reviewed['run_id']),
                    'artifact_id':str(reviewed['artifact_id']),'artifact_sha256':reviewed['artifact_sha256'],
                    'simulator_input':json.dumps(reviewed['simulator']),
                    'gchat_commit':reviewed['gchat_commit'],'gcoms_commit':reviewed['gcoms_commit'],
                    'build_number':reviewed['build_number'],'upload_testflight':True}
                ref=rule['registration']['verification']['ref'] if 'registration' in rule else 'release/gchat-'+controller[:16]
            else:
                inputs={'request_id':request,'release_manifest':base64.b64encode(canonical(manifest)).decode(),
                        'artifact_id':str(proof['worker']['artifact_id']),'artifact_sha256':archive}
                ref=manifest['refs']['gchat'].removeprefix('refs/heads/')
            atomic_json(marker,{'at':int(time.time()),'request':request})
            gh('actions/workflows/'+workflow+'/dispatches',method='POST',body={'ref':ref,'inputs':inputs})
        elif time.time()-json.loads(marker.read_text())['at']>1800:
            raise ValueError('Apple upload dispatch outcome unknown; no automatic duplicate upload')
        return None,'Waiting for the native Apple upload worker'
    run=matches[0]
    if (run['head_sha']!=controller or run['path']!='.github/workflows/'+workflow
        or run.get('event')!='workflow_dispatch'
        or run.get('head_repository',{}).get('full_name')!='IggyGG/gchat'):
        raise ValueError('Apple upload workflow source mismatch')
    if run['status']!='completed':return None,'Uploading the exact qualified IPA'
    if run['conclusion']!='success':raise ValueError('Apple upload worker failed: '+str(run['id']))
    if not builds or builds[0]['attributes']['processingState']=='PROCESSING':return None,'Apple is processing the uploaded build'
    if builds[0]['attributes']['processingState']!='VALID':raise ValueError('Apple rejected the uploaded build')
    # Successful immutable workflow attests that the reserved build uploaded from
    # the original verified IPA. Store response only supplies its provider ID.
    atomic_json(work/'upload-worker.json',{k:run[k] for k in ('id','head_sha','path','conclusion','html_url')})
    return builds[0]['id'],None


def retain_external_wait(manifest, work, verification, compatibility):
    observation=json.loads((work/'encryption-observation.json').read_text())
    if (observation['release_id']!=manifest['release_id'] or observation['sources']!=manifest['sources']
        or observation['state']!='IN_REVIEW' or observation['includes_france'] is not True):
        return
    # Both complete native gates were independently read before querying Apple.
    # This is a prerequisite wait, never an upload/submission/availability pass.
    atomic_json(work/'external-prerequisite.json', {'schema':1,'release_id':manifest['release_id'],
        'sources':manifest['sources'],'platform':'ios','kind':'apple_encryption_review',
        'at':int(time.time()),'uploaded':False,'submitted':False,
        'encryption_observation_sha256':digest(work/'encryption-observation.json'),
        'verification_sha256':digest(verification),'compatibility_sha256':digest(compatibility)})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--state',type=Path,required=True);p.add_argument('--config',type=Path,required=True);a=p.parse_args()
    manifest=validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()));platform=os.environ['GCHAT_RELEASE_TARGET'];stage=os.environ['GCHAT_RELEASE_STAGE']
    output=Path(os.environ['GCHAT_RELEASE_RECEIPT']);config=json.loads(a.config.read_text())[platform]
    verification=job(a.state,manifest,platform,'verify')/'receipt.json';proof,_=read_receipt(verification,manifest,platform,'verify')
    compatibility=job(a.state,manifest,platform,'compatibility')/'receipt.json';compatible,_=read_receipt(compatibility,manifest,platform,'compatibility')
    if compatible.get('relay_compatible') is not True:raise ValueError('publication requires qualified deployed relay compatibility')
    if stage=='prerequisite':
        if platform!='ios':raise ValueError('read-only encryption prerequisite is iOS-only')
        work=job(a.state,manifest,platform,stage);work.mkdir(exist_ok=True)
        observed=observe_encryption(apple(config),config,manifest,work)
        if (observed['attributes'].get('appEncryptionDeclarationState')=='IN_REVIEW'
                and observed['attributes'].get('availableOnFrenchStore') is True):
            retain_external_wait(manifest,work,verification,compatibility)
        atomic_json(work/'waiting.json',{'reason':'Store lane is active; encryption prerequisite observed without submission','at':int(time.time())})
        raise SystemExit(75)
    work=job(a.state,manifest,platform,'submit');work.mkdir(exist_ok=True)
    paths=[verification.parent/i['path'] for i in proof['evidence']]
    api=google(config) if platform=='android' else apple(config)
    if platform=='android':
        bundles=[p for p in paths if p.suffix=='.aab']
        if len(bundles)!=1:raise ValueError('qualified Android bundle missing or ambiguous')
        candidate={'release_id':manifest['release_id'],'version_code':manifest['versions']['android'],'aab_sha256':digest(bundles[0])}
        result=submit_google(api,config,candidate,bundles[0],work/'provider.json') if stage=='submit' else observe_google(api,candidate['version_code'],config.get('track','production'))
    else:
        binding=work/'apple-build.json'
        if not binding.exists():
            build,reason=ios_build(api,config,manifest,job(a.state,manifest,'ios','build'),work)
            if build is None:
                if reason=='Apple encryption declaration is still awaiting approval':
                    retain_external_wait(manifest,work,verification,compatibility)
                atomic_json(work/'waiting.json',{'reason':reason,'at':int(time.time())});raise SystemExit(75)
            marketing=manifest['versions']['linux-x86_64']
            versions=api.request('GET','/v1/apps/'+config['app_id']+'/appStoreVersions',params={'filter[platform]':'IOS','limit':50})['data']
            matching=[v for v in versions if v['attributes']['versionString']==marketing]
            if len(matching)>1:raise ValueError('ambiguous App Store marketing version')
            if not matching:
                drafts=[v for v in versions if v['attributes']['appStoreState']=='PREPARE_FOR_SUBMISSION']
                if len(drafts)>1:raise ValueError('multiple App Store drafts require reconciliation')
                if drafts:
                    draft=drafts[0]
                    associated=api.request('GET','/v1/appStoreVersions/'+draft['id']+'/relationships/build').get('data')
                    if associated:raise ValueError('existing App Store draft already has a different build')
                    updated=api.request('PATCH','/v1/appStoreVersions/'+draft['id'],json={'data':{'type':'appStoreVersions','id':draft['id'],'attributes':{'versionString':marketing}}})
                    matching=[updated['data']]
                else:
                    marker=work/'version-attempted.json'
                    if marker.exists():raise ValueError('App Store version creation outcome unknown; do not duplicate')
                    atomic_json(marker,{'marketing_version':marketing})
                    created=api.request('POST','/v1/appStoreVersions',json={'data':{'type':'appStoreVersions',
                        'attributes':{'platform':'IOS','versionString':marketing,'releaseType':'AFTER_APPROVAL'},
                        'relationships':{'app':{'data':{'type':'apps','id':config['app_id']}}}}})
                    matching=[created['data']]
            versions=matching
            ipas=[p for p in paths if p.suffix=='.ipa']
            if len(ipas)!=1:raise ValueError('qualified IPA missing')
            atomic_json(binding,{'release_id':manifest['release_id'],'build_id':build,'version_id':versions[0]['id'],
                'build_number':manifest['versions']['ios'],'ipa_sha256':digest(ipas[0])})
        candidate=json.loads(binding.read_text())
        result=submit_apple(api,config,candidate,work/'provider.json') if stage=='submit' else observe_apple(api,candidate['version_id'],candidate['build_id'])
    if result['state']=='blocked':raise ValueError(result.get('reason','Provider action required'))
    report=output.parent/'provider-state.json';atomic_json(report,{'release_id':manifest['release_id'],'at':int(time.time()),**result})
    atomic_json(output,{'schema':1,'release_id':manifest['release_id'],'sources':manifest['sources'],'platform':platform,'stage':stage,
        'passed':True,'source_unchanged':True,'provider_state':result['state'],'evidence':[{'path':report.name,'sha256':digest(report)}]})

if __name__=='__main__':main()
