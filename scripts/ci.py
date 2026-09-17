#!/usr/bin/env python3
"""Native CI gate; runners are disposable and contain the pinned toolchain."""
import json, os, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def run(args):
    subprocess.run(args,cwd=root,check=True)
run([sys.executable,'scripts/check-source.py'])
run(['cargo','fmt','--all','--','--check'])
run(['cargo','test','--workspace','--all-features','--locked','--','--test-threads=1'])
run(['cargo','clippy','--workspace','--all-targets','--all-features','--locked','--','-D','warnings'])
run(['npm','ci','--ignore-scripts'])
run(['npm','run','check'])
run(['npm','test'])
run(['npm','run','build'])
run([sys.executable,'scripts/check-generated.py'])
run(['cargo','fmt','--manifest-path','apps/client/src-tauri/Cargo.toml','--','--check'])
run(['cargo','check','--manifest-path','apps/client/src-tauri/Cargo.toml','--locked'])
run(['npm','run','tauri','-w','@gchat/client','--','build','--no-bundle'])
if sys.platform=='linux':
    run(['cargo','deny','check'])
    run(['cargo','deny','--manifest-path','apps/client/src-tauri/Cargo.toml','--config','deny.toml','check'])
run(['git','diff','--exit-code','--','Cargo.lock','package-lock.json','packages','ui'])
