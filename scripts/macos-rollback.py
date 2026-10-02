#!/usr/bin/env python3
"""Native retained Mac application upgrade/rollback on disposable profiles.

No installed personal application is accessed. Existing signed disk images are
mounted read-only and independently checked, then exercised with actual network IPC. This
qualifies profile/history/cache compatibility, not personal installations or rendered UI interaction.
"""
import argparse
import hashlib
import json
import os
import platform
import re
import tempfile
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import time
import uuid

import importlib.util
ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


from release_jobs import gh, extract, acceptance_archive

MOUNTS = []
INPUTS = {}
PUBLICATION = ROOT / 'release/publication.json'
network = load('test-native-network')
installer = load('test-macos-bundle')
smoke = network.m


def validate_inputs(value):
    smoke.require(value.get('target') in ('macos-aarch64', 'macos-x86_64'), 'unknown Mac target')
    for name in ('current', 'baseline'):
        item = value[name]
        smoke.require(all(type(item[k]) is int and item[k] > 0 for k in ('run', 'artifact'))
                      and re.fullmatch('[0-9a-f]{64}', item['archive'])
                      and re.fullmatch('[0-9a-f]{40}', item['controller'])
                      and set(item['sources']) == {'gchat', 'gcoms'}
                      and all(re.fullmatch('[0-9a-f]{40}', c) for c in item['sources'].values()),
                      'invalid retained artifact identity')
        path = PurePosixPath(item['manifest'])
        smoke.require('\\' not in item['manifest'] and ':' not in item['manifest']
                      and not path.is_absolute() and '..' not in path.parts and path.name == 'build.json',
                      'invalid retained manifest path')
    return value


def acquire(name, output, commands):
    bound = INPUTS[name]
    run = gh(f"actions/runs/{bound['run']}")
    root = output / name; root.mkdir()
    archive = root / 'artifact.zip'
    artifact = acceptance_archive(bound, archive)
    retained = artifact is not None
    if not retained: artifact = gh(f"actions/artifacts/{bound['artifact']}")
    smoke.require(run.get('status') == 'completed' and run.get('conclusion') == 'success'
                  and run.get('head_repository', {}).get('full_name') == 'IggyGG/gchat'
                  and run.get('path') in ('.github/workflows/macos-release.yml', '.github/workflows/macos-notarize.yml')
                  and run.get('head_sha') == bound['controller'] and run.get('event') == 'workflow_dispatch'
                  and artifact.get('workflow_run', {}).get('id') == bound['run']
                  and (retained or artifact.get('expired') is False)
                  and artifact.get('digest') == 'sha256:' + bound['archive']
                  and type(artifact.get('size_in_bytes')) is int and 0 < artifact['size_in_bytes'] <= 2 * 1024**3,
                  'retained Mac source/artifact identity differs')
    if not retained:
        with archive.open('xb') as stream:
            subprocess.run(['gh', 'api', f"repos/IggyGG/gchat/actions/artifacts/{bound['artifact']}/zip"],
                           stdout=stream, check=True, timeout=300)
    smoke.require(smoke.digest(archive) == bound['archive'] and archive.stat().st_size == artifact['size_in_bytes'],
                  'retained Mac archive differs')
    extract(archive, root / 'original')
    manifest = root / 'original' / bound['manifest']; build = json.loads(manifest.read_text())
    smoke.require(build.get('sources') == bound['sources'] and build.get('target') == INPUTS['target'],
                  'Mac source-bound native manifest differs')
    identity = installer.publisher_identity(build, json.loads(PUBLICATION.read_text()))
    dmg = installer.select_dmg(build, manifest)
    signature = {'dmg': installer.verify_signature(commands, dmg, identity, name + '-dmg')}
    work = Path(tempfile.mkdtemp(prefix='gchat-rollback-' + name + '-'))
    work.chmod(0o700); mount = work / 'volume'; mount.mkdir()
    MOUNTS.append((work, mount))
    _, data = commands.run(name + '-attach', ['hdiutil', 'attach', '-readonly', '-nobrowse', '-noautoopen',
        '-plist', '-mountpoint', str(mount), str(dmg)])
    installer.validate_mount(data, mount)
    smoke.require(os.statvfs(mount).f_flag & os.ST_RDONLY, 'DMG mount is not read-only')
    source = installer.app_from_volume(mount); app = work / source.name
    commands.run(name + '-copy', ['ditto', '--rsrc', '--extattr', str(source), str(app)])
    signature['app'] = installer.verify_signature(commands, app, identity, name + '-app')
    binary = installer.bundle_executable(app)
    smoke.validate_artifacts(binary, manifest, manifest.parent / 'provenance/native-ci.json')
    return {'binary': binary, 'build_manifest': manifest, 'native_receipt': manifest.parent / 'provenance/native-ci.json',
            'build': build, 'signature': signature, 'archive_sha256': bound['archive']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--inputs',type=Path,required=True);a=p.parse_args()
    INPUTS.clear(); MOUNTS.clear()
    INPUTS.update(validate_inputs(json.loads(a.inputs.read_text())))
    smoke.require(platform.system()=='Darwin' and os.environ.get('GITHUB_ACTIONS')=='true','isolated native Mac worker required')
    expected_arch={'macos-aarch64':'arm64','macos-x86_64':'x86_64'}[INPUTS['target']]
    smoke.require(platform.machine()==expected_arch,'native Mac architecture differs')
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);smoke.private_directory(out)
    report={'schema':1,'passed':False,'scope':'native Mac copied signed application profile/history/cache rollback',
            'application_rebuilt':False,'personal_profiles_accessed':False,'rendered_gui_qualified':False,'commands':[],'phases':[]}
    commands=installer.Commands(out,report);journey=None; invitation=out/'invitation.private'
    try:
        current=acquire('current',out,commands); baseline=acquire('baseline',out,commands)
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
        journey.channel=journey.submit(0,'/create #mac-rollback sender')['conversation']
        code=journey.until(lambda:journey.submit(0,'/invite')['output'].get('link'))
        preview=journey.call(1,'networks',request={'kind':'inspect','code':code})['response']
        smoke.require(preview['kind']=='preview' and not preview['preview']['newNetwork'],'unexpected fixture network')
        joined=journey.call(1,'networks',request={'kind':'join','code':code,'nickname':'receiver',
            'accepted_network':preview['preview']['network']['id'],'operation_id':uuid.uuid4().hex})['response']
        smoke.require(joined['kind']=='result' and joined['response']['conversation']==journey.channel,'join differs')
        journey.chat('current')
        ident=uuid.uuid4().hex;data=hashlib.shake_256(b'mac-rollback-cache').digest(network.PIECE)
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
                for i in (0, 1):
                    try:shutil.rmtree(journey.root/f'c{i}')
                    except FileNotFoundError:pass
                    except OSError as error:
                        report.setdefault('cleanup_errors',[]).append(type(error).__name__)
                        report['passed']=False
            report['cleanup_complete']=stopped and all(r['stopped'] and not r['forced'] and r['exit_code']==0 for r in results)
            report['profiles_removed']=all(not (journey.root/f'c{i}').exists() for i in (0, 1))
        invitation.unlink(missing_ok=True)
        report['invitation_removed']=not invitation.exists()
        report['passed']=report['passed'] and report.get('cleanup_complete',False) and report.get('profiles_removed',False) and report['invitation_removed']
        report['installation_cleanup'] = []
        for work, mount in reversed(MOUNTS):
            cleanup = installer.cleanup_installation(commands, work, mount, True, report.get('cleanup_complete', journey is None))
            report['installation_cleanup'].append(cleanup)
            report['passed'] = report['passed'] and cleanup['passed']
        (out/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'passed':report['passed'],'error':report.get('error')}))
    return 0 if report['passed'] else 1


if __name__=='__main__':sys.exit(main())
