#!/usr/bin/env python3
"""Cache the exact locked WebKit before expensive native compilation.

Install only playwright-core in an isolated directory. The application workspace
needs paired SDK archives and cannot be installed from the public npm registry.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile


def locked_project(lock):
    core = lock['packages']['node_modules/playwright-core']
    version = core['version']
    if (core.get('dependencies') or core.get('optionalDependencies') or
            core.get('resolved') != f'https://registry.npmjs.org/playwright-core/-/playwright-core-{version}.tgz' or
            not core.get('integrity', '').startswith('sha512-')):
        raise ValueError('review changed Playwright dependency or integrity requirements')
    package = {'name': 'gchat-browser-preflight', 'version': '1.0.0', 'private': True,
               'devDependencies': {'playwright-core': version}}
    frozen = {'name': package['name'], 'version': package['version'], 'lockfileVersion': 3,
              'requires': True, 'packages': {'': package, 'node_modules/playwright-core': core}}
    return package, frozen


def main():
    source = Path(__file__).resolve().parents[1] / 'package-lock.json'
    original = source.read_bytes()
    package, lock = locked_project(json.loads(original))
    with tempfile.TemporaryDirectory(prefix='gchat-browser-preflight-') as directory:
        root = Path(directory)
        (root / 'package.json').write_text(json.dumps(package))
        (root / 'package-lock.json').write_text(json.dumps(lock))
        subprocess.run(['npm.cmd' if os.name == 'nt' else 'npm', 'ci', '--ignore-scripts',
                        '--no-audit', '--no-fund'], cwd=root, check=True, timeout=180)
        subprocess.run(['node', str(root / 'node_modules/playwright-core/cli.js'), 'install', 'webkit'],
                       cwd=root, check=True, timeout=480)
    if source.read_bytes() != original:
        raise ValueError('application lock changed during browser preflight')


if __name__ == '__main__': main()
