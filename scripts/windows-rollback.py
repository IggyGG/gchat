#!/usr/bin/env python3
"""Native retained Windows executable upgrade/rollback on disposable profiles.

No installed personal application is accessed. Existing signed installers are
extracted, independently checked, then exercised with actual network IPC. This
qualifies profile/history/cache compatibility, not NSIS upgrade UI or Windows 11.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
from release_jobs import acceptance_archive

import importlib.util
ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


retained = load('windows-network')
network = load('test-native-network')
installer = load('test-windows-installer')
smoke = network.m


def acquire(name, output, commands):
    bound = retained.RETAINED[name]
    run = retained.package.api(f"repos/IggyGG/gchat/actions/runs/{bound['run']}")
    root = output / name; root.mkdir()
    archive = root / 'artifact.zip'
    artifact = acceptance_archive(bound, archive)
    local = artifact is not None
    if not local: artifact = retained.package.api(f"repos/IggyGG/gchat/actions/artifacts/{bound['artifact']}")
    smoke.require(run.get('status') == 'completed' and run.get('conclusion') == bound['conclusion']
                  and run.get('head_sha') == bound.get('controller', bound['sources']['gchat'])
                  and run.get('path') == '.github/workflows/windows-release.yml'
                  and artifact.get('workflow_run', {}).get('id') == bound['run']
                  and (local or artifact.get('expired') is False)
                  and artifact.get('digest') == 'sha256:' + bound['archive'],
                  'retained Windows source/artifact identity differs')
    if not local:
        with archive.open('xb') as stream:
            subprocess.run(['gh','api',f"repos/IggyGG/gchat/actions/artifacts/{bound['artifact']}/zip"],
                           stdout=stream,check=True,timeout=180)
    smoke.require(smoke.digest(archive) == bound['archive'] and archive.stat().st_size == artifact['size_in_bytes'],
                  'retained Windows archive differs')
    retained.package.extract(archive, root / 'original')
    manifest = root / 'original/build.json'; build = json.loads(manifest.read_text())
    smoke.require(build['sources'] == bound['sources'] and build['executables'] == [bound['executable']],
                  'retained Windows binary/source differs')
    nsis = installer.select_installer(build, manifest)
    destination = root / 'extracted'
    subprocess.run(['7z','x',str(nsis),'-o'+str(destination),'-y'],check=True,stdout=subprocess.DEVNULL,
                   stderr=subprocess.PIPE,timeout=120)
    matches=list(destination.rglob('gchat-desktop.exe'))
    smoke.require(len(matches)==1 and smoke.digest(matches[0])==bound['executable']['sha256'],
                  'extracted executable differs from native artifact')
    binary=matches[0]
    pin=build['publisher']['certificate_fingerprint'].replace(' ','').upper()
    signature=installer.verify_signature(commands,binary,pin,build['signing_policy'],name+'-signature')
    smoke.validate_artifacts(binary, manifest, root / 'original/provenance/native-ci.json')
    return {'binary':binary,'build_manifest':manifest,'native_receipt':root/'original/provenance/native-ci.json',
            'build':build,'signature':signature,'archive_sha256':bound['archive']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    smoke.require(os.name=='nt' and os.environ.get('GITHUB_ACTIONS')=='true','isolated native Windows worker required')
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);smoke.private_directory(out)
    report={'schema':1,'passed':False,'scope':'native Windows retained executable profile/history/cache rollback',
            'application_rebuilt':False,'personal_profiles_accessed':False,'nsis_upgrade_ui_qualified':False,
            'windows_11_qualified':False,'commands':[],'phases':[]}
    commands=installer.Commands(out,report);journey=None; invitation=out/'invitation.private'
    try:
        current=acquire('windows36',out,commands); baseline=acquire('windows18',out,commands)
        smoke.require(current['build']['publisher']==baseline['build']['publisher'],'rollback publisher differs')
        report['artifacts']={name:{'binary_sha256':smoke.digest(item['binary']),'sources':item['build']['sources'],
                                   'archive_sha256':item['archive_sha256'],'signature':item['signature']}
                             for name,item in [('current',current),('baseline',baseline)]}
        code=os.environ.pop('GCHAT_NETWORK_INVITATION','');smoke.require(0<len(code.encode())<=180000,'missing bounded fixture invitation')
        invitation.write_text(code);smoke.private_fixture_path(invitation,directory=False)
        args=argparse.Namespace(binary=current['binary'],build_manifest=current['build_manifest'],
            native_receipt=current['native_receipt'],invitation=invitation,output=out/'journey',bytes=network.PIECE,
            binary_sha256=smoke.digest(current['binary']))
        journey=network.Journey(args)
        for i in (0,1):journey.start_client(i,True)
        journey.channel=journey.submit(0,'/create #windows-rollback sender')['conversation']
        code=journey.invitation()
        journey.join_peer(code)
        journey.chat('current')
        ident=uuid.uuid4().hex;data=hashlib.shake_256(b'windows-rollback-cache').digest(network.PIECE)
        expected=hashlib.sha256(data).hexdigest()
        journey.files(0,'prepare',id=ident,conversation=journey.channel,name='rollback.bin',size_bytes=str(network.PIECE))
        journey.io(0,ident,0,True,data);journey.files(0,'commit',id=ident)
        journey.until(lambda:journey.row(1,ident));journey.files(1,'accept',id=ident)
        journey.until(lambda:journey.row(1,ident)['state']=='complete')
        smoke.require(journey.export(ident)==expected,'initial export differs')
        for phase,item in [('baseline',baseline),('restored',current)]:
            before={i:journey.history(i) for i in (0,1)}
            for i in (0,1):journey.stop(i)
            args.binary=item['binary']
            for i in (0,1):
                journey.start_client(i,False)
                smoke.require(journey.history(i)==before[i],'history changed across binary replacement')
            smoke.require(journey.export(ident)==expected,'encrypted cache export changed across replacement')
            journey.chat(phase)
            report['phases'].append({'phase':phase,'binary_sha256':smoke.digest(item['binary']),
                'same_identity':True,'history_retained':True,'cache_sha256':expected,'authenticated_bidirectional_ack':True})
        report['passed']=True
    except Exception as error:
        report['error']=type(error).__name__+': '+str(error)
    finally:
        results=[]
        if journey is not None:
            for _,proc,stop,log in reversed(journey.children):
                if proc.poll() is None:results.append(smoke.stop_service(proc,stop,10))
                log.close()
            stopped=all(proc.poll() is not None for _,proc,_,_ in journey.children)
            report['events']=journey.report['events'];report['elapsed_seconds']=time.monotonic()-journey.start
            report['passed']=report['passed'] and report['elapsed_seconds']<=600
            if stopped:
                for i in journey.clients:
                    try:shutil.rmtree(journey.root/f'c{i}')
                    except OSError as error:
                        report.setdefault('cleanup_errors',[]).append(type(error).__name__)
                        report['passed']=False
            report['cleanup_complete']=stopped and all(r['stopped'] and not r['forced'] and r['exit_code']==0 for r in results)
            report['profiles_removed']=all(not (journey.root/f'c{i}').exists() for i in journey.clients)
        invitation.unlink(missing_ok=True)
        report['invitation_removed']=not invitation.exists()
        report['passed']=report['passed'] and report.get('cleanup_complete',False) and report.get('profiles_removed',False) and report['invitation_removed']
        (out/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'passed':report['passed'],'error':report.get('error')}))
    return 0 if report['passed'] else 1


if __name__=='__main__':sys.exit(main())
