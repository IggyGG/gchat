#!/usr/bin/env python3
"""Collect resolved dependency notices into a native-bundle resource directory.

Preserves upstream files and records missing notices for release review. This
inventory does not decide ownership or certify license compliance.
"""
import argparse, hashlib, json, subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--rust-metadata', type=Path, action='append', default=[])
parser.add_argument('--cargo-config', type=Path)
parser.add_argument('--output', type=Path, default=root / 'third-party/generated')
args = parser.parse_args()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=True)
metadata = []
if args.rust_metadata:
    metadata = [json.loads(p.read_text()) for p in args.rust_metadata]
else:
    cmd = ['cargo', 'metadata', '--manifest-path', 'apps/client/src-tauri/Cargo.toml',
           '--locked', '--all-features', '--format-version=1']
    if args.cargo_config:
        cmd += ['--config', str(args.cargo_config.resolve())]
    metadata.append(json.loads(subprocess.check_output(cmd, cwd=root)))
records = []
seen = set()
optional_not_installed = []

def collect(ecosystem, name, version, location, license, source, authors):
    key = (ecosystem, name, version)
    if key in seen:
        return
    seen.add(key)
    record = dict(ecosystem=ecosystem, name=name, version=version,
                  license=license, source=source, authors=authors, notices=[])
    destination = out / ecosystem / name.replace('/', '__') / version
    destination.mkdir(parents=True, exist_ok=True)
    for file in sorted(location.rglob('*')):
        relative = file.relative_to(location)
        if any(part in {'node_modules', '.git', 'target'} for part in relative.parts):
            continue
        if not file.is_file() or file.is_symlink():
            continue
        upper = file.name.upper()
        if not any(word in upper for word in ('LICENSE', 'LICENCE', 'COPYRIGHT', 'NOTICE')):
            continue
        data = file.read_bytes()
        if b'\x00' in data or len(data) > 2 * 1024 * 1024:
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        record['notices'].append(dict(path=target.relative_to(out).as_posix(),
                                     sha256=hashlib.sha256(data).hexdigest()))
    record['review_required'] = not bool(record['notices'])
    records.append(record)

for graph in metadata:
    for pkg in graph['packages']:
        if pkg.get('source') is None:
            continue
        collect('cargo', pkg['name'], pkg['version'], Path(pkg['manifest_path']).parent,
                pkg.get('license'), pkg.get('source'), pkg.get('authors', []))

lock = json.loads((root / 'package-lock.json').read_text())
for key, item in lock.get('packages', {}).items():
    if 'node_modules/' not in key or item.get('link'):
        continue
    location = root / key
    manifest = location / 'package.json'
    if not manifest.is_file():
        if item.get('optional'):
            optional_not_installed.append(key)
            continue
        raise SystemExit('Run npm ci before collecting notices: missing ' + key)
    pkg = json.loads(manifest.read_text())
    if pkg['version'] != item['version']:
        raise SystemExit('Installed npm version differs from lockfile: ' + key)
    collect('npm', pkg['name'], pkg['version'], location, pkg.get('license'),
            item.get('resolved'), pkg.get('contributors', [pkg.get('author')]))

records.sort(key=lambda p: (p['ecosystem'], p['name'], p['version']))
manifest = dict(scope='Resolved Rust and installed npm dependencies, including build tools',
                compliance_review='required before distribution', packages=records,
                optional_npm_not_installed=optional_not_installed)
(out / 'inventory.json').write_text(json.dumps(manifest, indent=2) + '\n')
missing = [p['name'] + '@' + p['version'] for p in records if p['review_required']]
(out / 'REVIEW.txt').write_text(
    'Upstream notice files are preserved; final distribution rights review is required.\n'
    'Packages without discoverable notice files:\n' + '\n'.join(missing) + '\n')
print(f"{len(records)} dependency inventories collected; {len(missing)} need notice-file review")
if missing:
    print('\n'.join(missing))
