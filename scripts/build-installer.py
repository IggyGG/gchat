#!/usr/bin/env python3
"""Native signed Tauri bundles. Signing failure never produces a release report."""
import argparse
import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from release_signatures import verify

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    'linux-x86_64': ('Linux', 'x86_64', 'x86_64-unknown-linux-gnu', ['deb', 'appimage']),
    'windows-x86_64': ('Windows', 'x86_64', 'x86_64-pc-windows-msvc', ['nsis']),
    'macos-x86_64': ('Darwin', 'x86_64', 'x86_64-apple-darwin', ['dmg']),
    'macos-aarch64': ('Darwin', 'aarch64', 'aarch64-apple-darwin', ['dmg']),
}


def run(args, **kwargs):
    result = subprocess.run(args, cwd=ROOT, **kwargs)
    if result.returncode:
        # Never stringify command arguments: keychain tools accept secret arguments.
        raise RuntimeError(f'{Path(args[0]).name} failed ({result.returncode})')
    return result


def required(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(f'configure protected signing input {name}')
    return value


def fingerprint(name, lengths=(40, 64)):
    value = required(name).replace(' ', '')
    if len(value) not in lengths or not re.fullmatch('[a-fA-F0-9]+', value):
        raise ValueError(f'{name} is not a certificate/key fingerprint')
    return value


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


@contextmanager
def apple_keychain():
    with tempfile.TemporaryDirectory(prefix='gchat-sign-') as temp:
        temp = Path(temp); keychain = temp / 'release.keychain-db'; cert = temp / 'developer-id.p12'
        cert.write_bytes(base64.b64decode(required('APPLE_CERTIFICATE_BASE64'), validate=True)); cert.chmod(0o600)
        password = os.urandom(32).hex()
        original = subprocess.check_output(['security', 'list-keychains', '-d', 'user'], text=True)
        import shlex
        previous = shlex.split(original)
        try:
            run(['security', 'create-keychain', '-p', password, str(keychain)], capture_output=True)
            run(['security', 'set-keychain-settings', '-lut', '21600', str(keychain)], capture_output=True)
            run(['security', 'unlock-keychain', '-p', password, str(keychain)], capture_output=True)
            run(['security', 'import', str(cert), '-k', str(keychain), '-P', required('APPLE_CERTIFICATE_PASSWORD'), '-T', '/usr/bin/codesign', '-T', '/usr/bin/security'], capture_output=True)
            run(['security', 'set-key-partition-list', '-S', 'apple-tool:,apple:,codesign:', '-s', '-k', password, str(keychain)], capture_output=True)
            run(['security', 'list-keychains', '-d', 'user', '-s', str(keychain), *previous], capture_output=True)
            api_key = temp / 'AuthKey.p8'
            api_key.write_bytes(base64.b64decode(required('APPLE_API_KEY_BASE64'), validate=True)); api_key.chmod(0o600)
            environment = dict(os.environ, APPLE_API_KEY_PATH=str(api_key))
            required('APPLE_API_KEY'); required('APPLE_API_ISSUER')
            if not required('APPLE_SIGNING_IDENTITY').startswith('Developer ID Application:'):
                raise ValueError('macOS distribution requires Developer ID Application')
            team = required('APPLE_TEAM_ID')
            if not re.fullmatch('[A-Z0-9]{10}', team) or not required('APPLE_SIGNING_IDENTITY').endswith('('+team+')'):
                raise ValueError('Developer ID identity differs from expected team')
            yield environment
        finally:
            subprocess.run(['security', 'list-keychains', '-d', 'user', '-s', *previous], capture_output=True)
            subprocess.run(['security', 'delete-keychain', str(keychain)], capture_output=True)


def verify_windows(path):
    script = ROOT / 'scripts/verify-windows-signature.ps1'
    run(['powershell.exe', '-NoProfile', '-NonInteractive', '-File', str(script), '-Artifact', str(path), '-Thumbprint', fingerprint('WINDOWS_CERTIFICATE_THUMBPRINT', (40,))])


def bundle(target, output, environment):
    system, arch, triple, bundles = TARGETS[target]
    config = {'bundle': {}}
    if system == 'Windows':
        timestamp = required('WINDOWS_TIMESTAMP_URL')
        if not timestamp.startswith('https://'):
            raise ValueError('Windows timestamp service must use HTTPS')
        config['bundle']['windows'] = {'certificateThumbprint':fingerprint('WINDOWS_CERTIFICATE_THUMBPRINT', (40,)), 'digestAlgorithm':'sha256', 'timestampUrl':timestamp, 'tsp':True}
    if system == 'Linux':
        key = fingerprint('GCHAT_RELEASE_KEY')
        # Provision an unlocked signing subkey into the protected runner's GNUPGHOME.
        run(['gpg', '--batch', '--list-secret-keys', key], stdout=subprocess.DEVNULL)
        environment.update(SIGN='1', SIGN_KEY=key, APPIMAGETOOL_FORCE_SIGN='1', APPIMAGETOOL_SIGN_PASSPHRASE=required('GCHAT_RELEASE_PASSPHRASE'))
    with tempfile.TemporaryDirectory(prefix='gchat-bundle-') as temp:
        config_path = Path(temp)/'bundle.json'; config_path.write_text(json.dumps(config))
        # Fresh bundle output avoids accidentally reusing an older installer.
        build_root = output / 'build'
        if build_root.exists():
            raise ValueError('use a new output directory for each build')
        environment['CARGO_TARGET_DIR'] = str(build_root)
        run([sys.executable, 'scripts/collect-notices.py'], env=environment)
        npm = 'npm.cmd' if system == 'Windows' else 'npm'
        run([npm, 'run', 'tauri', '-w', '@gchat/client', '--', 'build', '--target', triple, '--bundles', ','.join(bundles), '--config', str(config_path)], env=environment)
        bundle_dir = build_root / triple / 'release/bundle'
        if system == 'Darwin':
            apps = list(bundle_dir.glob('macos/*.app'))
            if len(apps) != 1:
                raise ValueError('expected one signed application')
            run(['codesign', '--verify', '--deep', '--strict', '--verbose=2', str(apps[0])])
            details = subprocess.run(['codesign', '-d', '--verbose=4', str(apps[0])], capture_output=True, text=True, check=True)
            if 'TeamIdentifier='+required('APPLE_TEAM_ID') not in details.stderr.splitlines() or 'Authority='+required('APPLE_SIGNING_IDENTITY') not in details.stderr.splitlines():
                raise ValueError('signed application publisher differs from configured identity')
            run(['spctl', '--assess', '--type', 'execute', '--verbose=2', str(apps[0])])
        patterns = {'deb':'deb/*.deb', 'appimage':'appimage/*.AppImage', 'nsis':'nsis/*.exe', 'dmg':'dmg/*.dmg'}
        files = []
        for kind in bundles:
            matches = list(bundle_dir.glob(patterns[kind]))
            if len(matches) != 1:
                raise ValueError('expected exactly one artifact per bundle format')
            path = matches[0]
            if system == 'Windows': verify_windows(path)
            if system == 'Darwin': run(['xcrun', 'stapler', 'validate', str(path)])
            destination = output / path.name; shutil.copyfile(path, destination)
            if system == 'Linux':
                run(['gpg', '--batch', '--yes', '--pinentry-mode', 'loopback', '--passphrase-fd', '0', '--local-user', required('GCHAT_RELEASE_KEY'), '--armor', '--detach-sign', str(destination)], input=required('GCHAT_RELEASE_PASSPHRASE').encode(), env=environment)
                verify(str(destination)+'.asc', destination, required('GCHAT_RELEASE_KEY'))
            files.append({'name':destination.name,'format':kind,'sha256':sha(destination),'signing_verified':True})
        return files


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--target',choices=TARGETS,required=True);p.add_argument('--gcoms',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    system,arch,triple,_=TARGETS[a.target]
    actual={'amd64':'x86_64','arm64':'aarch64'}.get(platform.machine().lower(),platform.machine().lower())
    host=subprocess.check_output(['rustc','-vV'],text=True)
    if platform.system()!=system or actual!=arch or f'host: {triple}\n' not in host:
        raise ValueError('release builds require the selected native OS, architecture, and Rust host')
    if os.environ.get('GC_DEFAULT_RELAY_BOOTSTRAP'):
        raise ValueError('official installers must use the signed bundled relay defaults')
    publisher = json.loads((ROOT / 'release/publication.json').read_text())['publisher_identities']
    platform_key = {'Linux':'linux', 'Windows':'windows', 'Darwin':'macos'}[system]
    identity = publisher[platform_key]
    if system == 'Windows' and fingerprint('WINDOWS_CERTIFICATE_THUMBPRINT', (40,)).upper() != identity['certificate_fingerprint'].replace(' ', '').upper():
        raise ValueError('Windows signing identity differs from publication configuration')
    if system == 'Linux' and fingerprint('GCHAT_RELEASE_KEY').upper() != identity['certificate_fingerprint'].replace(' ', '').upper():
        raise ValueError('Linux signing identity differs from publication configuration')
    if system == 'Darwin' and required('APPLE_SIGNING_IDENTITY') != identity['name']:
        raise ValueError('Apple signing identity differs from publication configuration')
    sources={}
    for name,path in [('gchat',ROOT),('gcoms',a.gcoms.resolve())]:
        if subprocess.check_output(['git','status','--porcelain'],cwd=path).strip(): raise ValueError('release source must be clean')
        sources[name]=subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()
    output=a.output.resolve();output.mkdir(parents=True,exist_ok=False)
    if system=='Darwin':
        with apple_keychain() as environment: files=bundle(a.target,output,environment)
    else: files=bundle(a.target,output,dict(os.environ))
    for name,path in [('gchat',ROOT),('gcoms',a.gcoms.resolve())]:
        if subprocess.check_output(['git','status','--porcelain'],cwd=path).strip() or subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()!=sources[name]: raise ValueError('build changed source inputs')
    (output/'build.json').write_text(json.dumps({'schema':1,'target':a.target,'sources':sources,'files':files},indent=2)+'\n')
    print('Signed bundle report: '+str(output/'build.json'))


if __name__=='__main__': main()
