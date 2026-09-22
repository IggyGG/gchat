#!/usr/bin/env python3
"""Native CI gate; runners are disposable and contain the pinned toolchain."""
import argparse, json, os, shutil, subprocess, sys, uuid
from pathlib import Path
NPM = 'npm.cmd' if os.name == 'nt' else 'npm'
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--gcoms', type=Path, help='qualify exact unpublished companion sources in an isolated snapshot')
parser.add_argument('--provenance-output', type=Path, help='new directory for retained paired CI provenance')
args=parser.parse_args()
if args.gcoms:
    from paired_sources import execute, prepare_pair, verify_derived_inputs
    from release_evidence import source_identity
    protocol=args.gcoms.resolve()
    output=root/'target/paired-ci'/uuid.uuid4().hex
    triple=next(line.removeprefix('host: ') for line in
                subprocess.check_output(['rustc','-vV'],text=True).splitlines() if line.startswith('host: '))
    checkout, inputs=prepare_pair(root,protocol,output,triple,dict(os.environ))
    # The derived locks are this disposable checkout's baseline. Canonical
    # source commits and the exact derived inputs remain in provenance.
    execute(['git','init','-q'],checkout)
    # Evidence regressions inspect retained historical source objects. Import
    # history without replacing the independently derived paired build files.
    execute(['git','fetch','--quiet','--no-tags',str(root),
             inputs['sources']['gchat']['commit']],checkout)
    execute(['git','add','.'],checkout)
    execute(['git','-c','user.name=Gh0st build','-c','user.email=build@example.invalid',
             'commit','-qm','Frozen paired build inputs'],checkout)
    result=subprocess.run([sys.executable,'-u','scripts/ci.py'],cwd=checkout)
    verify_derived_inputs(checkout,inputs)
    unchanged=all(source_identity(path)==inputs['sources'][name]
                  for name,path in [('gchat',root),('gcoms',protocol)])
    (output/'provenance/native-ci.json').write_text(json.dumps({
        'sources':inputs['sources'],'exit_code':result.returncode,
        'source_unchanged':unchanged,'inputs':inputs,
    },indent=2)+'\n')
    if args.provenance_output:
        shutil.copytree(output/'provenance',args.provenance_output.resolve())
    print('Paired native evidence:',output/'provenance',flush=True)
    raise SystemExit(result.returncode if unchanged else 1)
def run(args):
    subprocess.run(args,cwd=root,check=True)
run([sys.executable,'scripts/check-source.py'])
run([sys.executable,'-m','unittest','discover','-s','scripts/tests','-p','*_test.py'])
if sys.platform=='win32':
    run(['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','RemoteSigned',
         '-File','scripts/test-windows-signature.ps1'])
run(['cargo','fmt','--all','--','--check'])
run(['cargo','clippy','--workspace','--all-targets','--all-features','--locked','--','-D','warnings'])
run(['cargo','test','--workspace','--all-features','--locked','--','--test-threads=1'])
run([NPM,'ci','--ignore-scripts'])
run([NPM,'run','check'])
run([NPM,'test'])
if sys.platform=='linux':
    run([NPM,'exec','--workspace','@gchat/ui','--','playwright','install','chromium'])
    run([NPM,'run','test:browser','--workspace','@gchat/ui'])
elif sys.platform=='darwin':
    run([NPM,'exec','--workspace','@gchat/ui','--','playwright','install','webkit'])
    run([NPM,'run','test:browser','--workspace','@gchat/ui','--','--browser=webkit'])
run([NPM,'run','build'])
run([sys.executable,'scripts/website.py'])
run([sys.executable,'scripts/check-generated.py'])
run([sys.executable,'scripts/collect-notices.py'])
run(['cargo','fmt','--manifest-path','apps/client/src-tauri/Cargo.toml','--','--check'])
run(['cargo','check','--manifest-path','apps/client/src-tauri/Cargo.toml','--locked'])
run(['cargo','test','--manifest-path','apps/client/src-tauri/Cargo.toml','--lib','--locked'])
run([NPM,'run','tauri','-w','@gchat/client','--','build','--no-bundle'])
if sys.platform=='linux':
    run(['cargo','deny','check'])
    run(['cargo','deny','--manifest-path','apps/client/src-tauri/Cargo.toml','--config','deny-desktop.toml','check'])
run(['git','diff','--exit-code','--','Cargo.lock','package-lock.json','packages','ui'])
