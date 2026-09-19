#!/usr/bin/env python3
"""Forgejo dispatches Mac builds, retrieves one exact run, and verifies source hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import uuid

from release_evidence import file_reference, validate_sources, validate_report

REPO='IggyGG/gchat'


def gh(*args):
    return subprocess.check_output(['gh',*args],text=True).strip()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--gchat-commit',required=True);p.add_argument('--gcoms-commit',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    for commit in (a.gchat_commit,a.gcoms_commit):
        if not re.fullmatch('[0-9a-f]{40}',commit): raise ValueError('full source commit IDs required')
    current=json.loads(gh('api',f'repos/{REPO}/git/ref/heads/main'))['object']['sha']
    if current!=a.gchat_commit: raise ValueError('mirror main must equal the frozen GChat source before dispatch')
    request_id=uuid.uuid4().hex
    gh('workflow','run','macos-release.yml','--repo',REPO,'--ref','main','-f','gchat_commit='+a.gchat_commit,'-f','gcoms_commit='+a.gcoms_commit,'-f','request_id='+request_id)
    deadline=time.monotonic()+21600;run=None
    while time.monotonic()<deadline:
        if run is None:
            runs=json.loads(gh('api',f'repos/{REPO}/actions/workflows/macos-release.yml/runs?event=workflow_dispatch&per_page=100'))['workflow_runs']
            run=next((r for r in runs if r['display_title']=='Forgejo macOS '+request_id),None)
        else:
            run=json.loads(gh('api',f'repos/{REPO}/actions/runs/{run["id"]}'))
            if run['status']=='completed': break
        time.sleep(15)
    if not run or run['status']!='completed' or run['conclusion']!='success': raise RuntimeError('macOS build failed or timed out; retain the GitHub run for diagnosis')
    if run['head_sha']!=a.gchat_commit: raise ValueError('workflow ran from a different commit')
    output=a.output.resolve();output.mkdir(parents=True,exist_ok=False)
    gh('run','download',str(run['id']),'--repo',REPO,'--dir',str(output))
    expected={'gchat':a.gchat_commit,'gcoms':a.gcoms_commit};targets=set()
    for report in output.glob('macos-*/build.json'):
        data=json.loads(report.read_text())
        if data['sources']!=expected or data['target'] in targets: raise ValueError('Mac artifact source binding mismatch')
        inputs=data.get('dependency_inputs', {})
        if (inputs.get('kind') != 'frozen_source_pair' or
            inputs.get('rust_sources_verified') is not True or
            inputs.get('npm_sources_verified') is not True or
            {name:value.get('commit') for name,value in inputs.get('sources',{}).items()} != expected):
            raise ValueError('Mac dependency inputs do not bind the frozen source pair')
        if json.loads((report.parent/'provenance/inputs.json').read_text()) != inputs:
            raise ValueError('Mac retained dependency provenance mismatch')
        targets.add(data['target'])
        evidence = report.parent / 'evidence'
        candidate = json.loads((evidence / 'candidate.json').read_text())
        validate_sources(candidate, evidence)
        if {name:value['commit'] for name,value in candidate['sources'].items()} != expected:
            raise ValueError('native evidence source binding mismatch')
        for project in ('gchat', 'gcoms'):
            check = f'native.{project}.{data["target"]}'
            result = json.loads(file_reference(evidence, candidate['checks'][check]).read_text())
            validate_report(check, result, candidate, evidence, candidate['artifacts'])
        if len(data['files']) != 1 or data['files'][0]['format'] != 'dmg':
            raise ValueError('expected exactly one qualified DMG per Mac architecture')
        for item in data['files']:
            path=report.parent/item['name']
            if path.name!=item['name'] or not path.resolve().is_relative_to(report.parent.resolve()): raise ValueError('unsafe artifact name')
            with path.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
            if digest!=item['sha256'] or item['signing_verified'] is not True: raise ValueError('Mac artifact digest/signing mismatch')
    if targets!={'macos-x86_64','macos-aarch64'}: raise ValueError('both native Mac builds are required')
    (output/'github-run.json').write_text(json.dumps({'run_id':run['id'],'url':run['html_url'],'workflow_commit':run['head_sha'],'sources':expected},indent=2)+'\n')
    print('Retrieved verified source-bound macOS artifacts: '+str(output))


if __name__=='__main__': main()
