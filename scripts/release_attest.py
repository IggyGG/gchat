#!/usr/bin/env python3
"""Retain an immutable build-to-candidate binding inside a native CI artifact."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from release_pair import validate


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--platform',required=True);a=p.parse_args()
    source=os.environ.get('GCHAT_RELEASE_MANIFEST')
    if not source:return
    manifest=validate(json.loads(Path(source).read_text()))
    root=a.output.resolve(); report=root/'build.json';build=json.loads(report.read_text())
    identities=build.get('sources',{})
    expected={k:v['commit'] for k,v in manifest['sources'].items()}
    actual={k:v.get('commit') if isinstance(v,dict) else v for k,v in identities.items()}
    if actual!=expected:raise ValueError('build sources do not match the coordinator manifest')
    if a.platform in ('ios','android') and (build.get('passed') is not True or build.get('sources_unchanged') is not True):
        raise ValueError('mobile build did not pass on unchanged inputs')
    (root/'release-binding.json').write_text(json.dumps({'schema':1,'candidate':manifest,'platform':a.platform,
        'build_sha256':hashlib.sha256(report.read_bytes()).hexdigest()},sort_keys=True,indent=2)+'\n')


if __name__=='__main__':main()
