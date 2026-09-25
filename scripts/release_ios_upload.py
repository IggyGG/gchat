#!/usr/bin/env python3
"""Upload the original qualified IPA on a native worker without recompilation.

Only reference paths are relocated. Every relocated file retains the native
worker's original SHA256 and size; the original report is retained unchanged.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
from release_pair import validate
from release_coordinator import atomic_json
from release_jobs import gh, extract
from release_verify import verify, load_module, sha


def relocate(value, root):
    if isinstance(value,dict):
        if set(('path','sha256','size')) <= value.keys():
            matches=[p for p in root.rglob(Path(value['path']).name) if p.is_file() and p.stat().st_size==value['size'] and sha(p)==value['sha256']]
            if not matches:raise ValueError('original upload evidence is missing')
            return {**value,'path':str(matches[0].resolve())}
        return {k:relocate(v,root) for k,v in value.items()}
    if isinstance(value,list):return [relocate(v,root) for v in value]
    return value


def main():
    manifest=validate(json.loads(base64.b64decode(os.environ['RELEASE_MANIFEST_BASE64'],validate=True)))
    commit=manifest['sources']['gchat']['commit']
    if (os.environ['GITHUB_SHA']!=commit or os.environ['GITHUB_WORKFLOW_SHA']!=commit or
        os.environ['GITHUB_REF']!=manifest['refs']['gchat'] or os.environ['GITHUB_REPOSITORY']!='IggyGG/gchat'):
        raise ValueError('upload worker is not the frozen protected workflow')
    output=Path('upload-output').resolve();output.mkdir(exist_ok=True)
    artifact_id=int(os.environ['ARTIFACT_ID']);expected=os.environ['ARTIFACT_SHA256']
    metadata=gh(f'actions/artifacts/{artifact_id}');run=gh(f'actions/runs/{metadata["workflow_run"]["id"]}')
    if (run['head_sha']!=commit or run['conclusion']!='success' or run['path']!='.github/workflows/ios-release.yml'
        or metadata.get('digest')!='sha256:'+expected or metadata['size_in_bytes']>12*1024**3):
        raise ValueError('qualified iOS archive identity differs')
    archive=output/'original.zip'
    with archive.open('wb') as stream:subprocess.run(['gh','api',f'repos/IggyGG/gchat/actions/artifacts/{artifact_id}/zip'],stdout=stream,stderr=subprocess.PIPE,check=True)
    if sha(archive)!=expected:raise ValueError('iOS archive download changed')
    original=output/'original';extract(archive,original)
    verify(manifest,'ios',original,output/'verification.json')
    report=next(p for p in original.rglob('build.json') if json.loads(p.read_text()).get('scope')=='ios_exact_pair_simulator_and_signed_ipa')
    frozen=json.loads(report.read_text());relocated=json.loads(report.read_text())
    for field in ('signing_cleanup','simulator','publication'):
        relocated[field]=relocate(frozen[field],original)
    relocated['application']['ipa']=relocate(frozen['application']['ipa'],original)
    # The original source publication file is included in the retained inputs.
    # Native archive identity and source-bound verification remain attached here.
    (output/'build.json').write_text(json.dumps(relocated,indent=2)+'\n')
    atomic_json(output/'relocation.json',{'original_report_sha256':sha(report),'original_archive_sha256':expected,
        'release_id':manifest['release_id'],'sources':manifest['sources'],'recompiled':False,'resigned':False})
    native = load_module('ios-build')
    checked = native.verify_ipa(Path(relocated['application']['ipa']['path']), output/'ipa-check',
                                manifest['policy']['ios_certificate_sha256'], manifest['versions']['ios'])
    if checked['marketing_version'] != manifest['versions']['linux-x86_64']:
        raise ValueError('native IPA marketing version differs from the release reservation')
    native.upload(SimpleNamespace(output=output))

if __name__=='__main__':main()
