#!/usr/bin/env python3
"""Attach the public release key, per-project manifests, and detached signatures."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from release_evidence import digest, file_reference, bindings, validate_sources
from release_signatures import fingerprint, verify

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('candidate_tool', ROOT / 'scripts/release-candidate.py')
candidate_tool = importlib.util.module_from_spec(spec); spec.loader.exec_module(candidate_tool)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--gchat', type=Path, required=True)
    p.add_argument('--gcoms', type=Path, required=True)
    a = p.parse_args(); manifest = a.candidate.resolve(); base = manifest.parent
    publication = json.loads((a.gchat / 'release/publication.json').read_text())
    key = fingerprint(publication['publisher_identities']['linux']['certificate_fingerprint'])
    if fingerprint(os.environ.get('GCHAT_RELEASE_KEY')) != key:
        raise ValueError('runner release key differs from recorded publisher')
    password = os.environ.get('GCHAT_RELEASE_PASSPHRASE')
    if password is None: raise ValueError('configure protected GCHAT_RELEASE_PASSPHRASE')
    # Hold the same candidate lock as artifact/record commands throughout signing.
    with candidate_tool.manifest_lock(manifest), tempfile.TemporaryDirectory(prefix='gchat-sign-assets-') as temp:
        candidate = json.loads(manifest.read_text())
        validate_sources(candidate, base, {'gchat':a.gchat.resolve(), 'gcoms':a.gcoms.resolve()})
        temp = Path(temp)
        def attach(name, path, project, kind):
            if not re.fullmatch(r'[A-Za-z0-9_.+-]+', name): raise ValueError('unsafe asset name')
            sha = digest(path); existing = candidate['artifacts'].get(name)
            if existing:
                if existing['sha256'] != sha or existing['project'] != project or existing['kind'] != kind:
                    raise ValueError('candidate already has a different asset; retain it and use a new candidate')
                file_reference(base, existing)
                return
            destination = base / 'artifacts' / (sha[:16] + '-' + name)
            destination.parent.mkdir(exist_ok=True)
            if destination.exists():
                if digest(destination) != sha: raise ValueError('retained asset digest mismatch')
            else:
                with destination.open('xb') as output: output.write(path.read_bytes())
            candidate['artifacts'][name] = {'path':destination.relative_to(base).as_posix(), 'sha256':sha, 'project':project, 'kind':kind, 'target':None}
        for project in ('gcoms', 'gchat'):
            public = temp / (project + '-release-key.asc')
            public.write_bytes(subprocess.check_output(['gpg','--batch','--armor','--export',key]))
            if not public.stat().st_size: raise ValueError('public release key unavailable')
            attach(public.name, public, project, 'inventory')
            name = project + '-release-manifest.json'
            inventory = {'schema':1, 'version':candidate['version'], 'sources':bindings(candidate), 'release_key':key,
                         'artifacts':{n: {'sha256':v['sha256'], 'kind':v['kind'], 'target':v.get('target')} for n,v in candidate['artifacts'].items() if v['project']==project and v['kind']!='signature' and n!=name}}
            path = temp / name; path.write_text(json.dumps(inventory, sort_keys=True, indent=2)+'\n')
            attach(name, path, project, 'inventory')
        for name, item in list(candidate['artifacts'].items()):
            if item['kind'] == 'signature': continue
            artifact = file_reference(base, item)
            existing = candidate['artifacts'].get(name+'.asc')
            if existing:
                verify(file_reference(base, existing), artifact, key)
                continue
            signature = temp / (name+'.asc')
            result = subprocess.run(['gpg','--batch','--pinentry-mode','loopback','--passphrase-fd','0','--local-user',key,'--armor','--output',str(signature),'--detach-sign',str(artifact)], input=password.encode(), capture_output=True)
            if result.returncode: raise RuntimeError('release signing failed; candidate was not updated')
            verify(signature, artifact, key)
            attach(name+'.asc', signature, item['project'], 'signature')
        candidate_tool.write_json(manifest, candidate)
    print('Signed candidate assets and retained public keys; qualification evidence is still required.')


if __name__ == '__main__': main()
