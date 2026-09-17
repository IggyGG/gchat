#!/usr/bin/env python3
"""Compare generated Rust contracts and checked-in schema/client artifacts."""
import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--cargo-config');a=p.parse_args()
root=Path(__file__).resolve().parents[1]
base=['cargo']+(['--config',a.cargo_config] if a.cargo_config else [])
def export(args):
    return subprocess.check_output(base+['run','--quiet']+args,cwd=root).decode()
assert export(['-p','gchat-api','--bin','gchat-types'])==(root/'ui/src/api.ts').read_text(), 'Rust UI type drift'
service=json.loads(export(['-p','gchat-api','--bin','gchat-types','--','--rpc']))
assert service==json.loads((root/'ui/schemas/chat-rpc.json').read_text()), 'Rust chat schema drift'
subprocess.run(['node','ui/scripts/generate-rpc.mjs','--check'],cwd=root,check=True)
print('Rust schemas and generated clients agree')
