#!/usr/bin/env python3
"""Bind CI build identity to a coordinator manifest after protected-source checks."""
import base64
import json
import os
from pathlib import Path
from release_pair import identity, validate


def main():
    value = os.environ.get('GCHAT_RELEASE_MANIFEST_BASE64', '')
    if not value: return  # explicitly dispatched historical/manual jobs keep their scope
    if len(value) > 32768: raise ValueError('release input too large')
    manifest = validate(json.loads(base64.b64decode(value, validate=True)))
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        commit = manifest['sources']['gchat']['commit']
        ref = manifest['refs']['gchat']
        if (os.environ.get('GITHUB_SHA') != commit or os.environ.get('GITHUB_WORKFLOW_SHA') != commit
                or os.environ.get('GITHUB_REF') != ref or os.environ.get('GITHUB_REPOSITORY') != 'IggyGG/gchat'):
            raise ValueError('signing workflow is not the protected frozen candidate')
    roots = {project: Path(project).resolve() for project in ('gchat', 'gcoms')}
    if {project: identity(root) for project, root in roots.items()} != manifest['sources']:
        raise ValueError('workflow source differs from release manifest')
    config = json.loads((roots['gchat'] / 'apps/client/src-tauri/tauri.conf.json').read_text())
    desktop = [manifest['versions'][p] for p in ('linux-x86_64', 'macos-aarch64', 'macos-x86_64', 'windows-x86_64')]
    if any(v != config['version'] for v in desktop) or str(config['bundle']['android']['versionCode']) != manifest['versions']['android']:
        raise ValueError('committed application versions differ from candidate reservations')
    path = Path(os.environ['RUNNER_TEMP']) / 'gchat-release-manifest.json'
    path.write_text(json.dumps(manifest, sort_keys=True) + '\n')
    with Path(os.environ['GITHUB_ENV']).open('a') as stream:
        for name, value in {'GCHAT_RELEASE_MANIFEST': str(path), 'GCHAT_RELEASE_ID': manifest['release_id'],
                            'GCHAT_SOURCE_COMMIT': manifest['sources']['gchat']['commit'],
                            'GCOMS_SOURCE_COMMIT': manifest['sources']['gcoms']['commit'],
                            'GCHAT_APP_VERSION': config['version']}.items():
            if '\n' in value or '\r' in value: raise ValueError('invalid environment value')
            stream.write(name + '=' + value + '\n')


if __name__ == '__main__': main()
