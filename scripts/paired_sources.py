"""Prepare isolated installer inputs from two exact, clean source commits.

Registry manifests stay unchanged in the real repositories. Derived lockfiles,
local package archives and Cargo overrides belong only to the retained build
directory. Signing uses this directory after verifying the resolved sources.
"""
import base64
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tarfile
import tomllib
from urllib.parse import unquote

from release_evidence import digest, require, source_identity


def execute(command, cwd, environment=None):
    subprocess.run([str(part) for part in command], cwd=cwd, env=environment, check=True)


def verify_resolved_protocol(metadata, protocol):
    protocol = Path(protocol).resolve()
    packages = []
    for package in metadata['packages']:
        if not package['name'].startswith('gcoms-'):
            continue
        manifest = Path(package['manifest_path']).resolve()
        require(package.get('source') is None and manifest.is_relative_to(protocol),
                'resolved GComs dependency differs from the frozen source pair: ' + package['name'])
        source = tomllib.loads(manifest.read_text())['package']
        require(source['name'] == package['name'], 'resolved GComs package name mismatch')
        packages.append({'name': package['name'], 'version': package['version'],
                         'manifest': manifest.relative_to(protocol).as_posix()})
    require({'gcoms-node', 'gcoms-sdk', 'gcoms-rpc'} <= {p['name'] for p in packages},
            'desktop graph omits the expected GComs implementation')
    return sorted(packages, key=lambda item: item['name'])


def verify_npm_protocol(chat, archives):
    lock = json.loads((chat / 'package-lock.json').read_text())
    expected = {}
    for archive in archives:
        with tarfile.open(archive) as stream:
            source = json.load(stream.extractfile('package/package.json'))
        name = source['name']
        require(name in {'@gcoms/rpc', '@gcoms/rpc-codegen'} and name not in expected,
                'unexpected or duplicate GComs npm archive')
        item = lock['packages']['node_modules/' + name]
        resolved = item.get('resolved', '')
        require(resolved.startswith('file:') and
                (chat / unquote(resolved[5:])).resolve() == archive.resolve(),
                'npm graph does not use the frozen archive: ' + name)
        integrity = 'sha512-' + base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()
        require(item.get('integrity') == integrity and item.get('version') == source['version'],
                'npm archive integrity/version mismatch: ' + name)
        expected[name] = {'version': source['version'], 'archive_sha256': digest(archive)}
    require(set(expected) == {'@gcoms/rpc', '@gcoms/rpc-codegen'}, 'missing GComs npm archive')
    return expected


def verify_derived_inputs(chat, report):
    for name, expected in report['derived_lock_sha256'].items():
        require(digest(chat / name) == expected, 'derived dependency lock changed during build: ' + name)
    require(digest(chat / '.cargo/config.toml') == report['cargo_config_sha256'],
            'Cargo source binding changed during build')
    archives = sorted((chat / 'target/paired-packages').glob('*.tgz'))
    require(verify_npm_protocol(chat, archives) == report['npm_bindings'],
            'npm source binding changed during build')


def prepare_pair(chat, protocol, output, triple, environment=None):
    roots = {'gchat': Path(chat).resolve(), 'gcoms': Path(protocol).resolve()}
    sources = {name: source_identity(root) for name, root in roots.items()}
    output = Path(output).resolve()
    inputs = output / 'inputs'
    inputs.mkdir(parents=True, exist_ok=False)
    provenance = output / 'provenance'
    provenance.mkdir(exist_ok=False)
    archives = {}
    for name, root in roots.items():
        archive = inputs / (name + '.tar')
        execute(['git', 'archive', '--format=tar', '--output', archive, sources[name]['commit']], root)
        archives[name] = digest(archive)
        checkout = inputs / name
        checkout.mkdir()
        with tarfile.open(archive) as stream:
            stream.extractall(checkout, filter='data')
        require(source_identity(root) == sources[name], 'source changed while preparing build inputs')

    chat, protocol = inputs / 'gchat', inputs / 'gcoms'
    workspace = tomllib.loads((protocol / 'Cargo.toml').read_text())['workspace']
    patches = ['[patch.crates-io]']
    for member in workspace['members']:
        for directory in sorted(protocol.glob(member)):
            require(directory.resolve().is_relative_to(protocol), 'workspace member escapes source input')
            package = tomllib.loads((directory / 'Cargo.toml').read_text())['package']
            if package['name'].startswith('gcoms-'):
                patches.append(f'{json.dumps(package["name"])} = {{ path = {json.dumps(str(directory))} }}')
    cargo_dir = chat / '.cargo'
    cargo_dir.mkdir(exist_ok=True)
    config = cargo_dir / 'config.toml'
    require(not config.exists(), 'review existing Cargo configuration before preparing source overrides')
    config.write_text('\n'.join(patches) + '\n')

    npm = 'npm.cmd' if platform.system() == 'Windows' else 'npm'
    execute([npm, 'ci', '--ignore-scripts', '--no-audit', '--no-fund'], protocol, environment)
    execute([npm, 'run', 'build'], protocol, environment)
    packages = chat / 'target/paired-packages'
    packages.mkdir(parents=True)
    execute([npm, 'pack', '--workspace', '@gcoms/rpc', '--workspace', '@gcoms/rpc-codegen',
             '--pack-destination', packages], protocol, environment)
    npm_archives = sorted(packages.glob('*.tgz'))
    require(len(npm_archives) == 2, 'expected two frozen GComs npm archives')
    execute([npm, 'install', '--ignore-scripts', '--no-audit', '--no-fund', '--package-lock-only',
             *npm_archives], chat, environment)
    execute([npm, 'ci', '--ignore-scripts', '--no-audit', '--no-fund'], chat, environment)
    npm_bindings = verify_npm_protocol(chat, npm_archives)

    graphs = {}
    for name, manifest in [('workspace', 'Cargo.toml'),
                           ('desktop', 'apps/client/src-tauri/Cargo.toml')]:
        command = ['cargo', 'metadata', '--manifest-path', manifest, '--all-features',
                   '--filter-platform', triple, '--format-version=1']
        metadata = json.loads(subprocess.check_output(command, cwd=chat, env=environment))
        graphs[name] = verify_resolved_protocol(metadata, protocol)
    locks = ['Cargo.lock', 'apps/client/src-tauri/Cargo.lock', 'package-lock.json']
    report = {'schema': 1, 'kind': 'frozen_source_pair', 'sources': sources,
              'source_archive_sha256': archives, 'rust_sources_verified': True,
              'rust_graphs': graphs, 'target': triple,
              'cargo_config_sha256': digest(config),
              'derived_lock_sha256': {name: digest(chat / name) for name in locks},
              'npm_archives': {path.name: digest(path) for path in npm_archives},
              'npm_sources_verified': True, 'npm_bindings': npm_bindings}
    for name, root in roots.items():
        require(source_identity(root) == sources[name], 'source changed during dependency preparation')
    (provenance / 'inputs.json').write_text(json.dumps(report, indent=2) + '\n')
    return chat, report
