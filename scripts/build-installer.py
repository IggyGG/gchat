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
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
from release_signatures import verify
from paired_sources import prepare_pair, verify_derived_inputs, verify_resolved_protocol, verify_native_ci_inputs, verify_retained_inputs

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    'linux-x86_64': ('Linux', 'x86_64', 'x86_64-unknown-linux-gnu', ['deb', 'appimage']),
    'windows-x86_64': ('Windows', 'x86_64', 'x86_64-pc-windows-msvc', ['nsis']),
    'macos-x86_64': ('Darwin', 'x86_64', 'x86_64-apple-darwin', ['dmg']),
    'macos-aarch64': ('Darwin', 'aarch64', 'aarch64-apple-darwin', ['dmg']),
}


def run(args, **kwargs):
    result = subprocess.run(args, cwd=kwargs.pop('cwd', ROOT), **kwargs)
    if result.returncode:
        # Never stringify command arguments: keychain tools accept secret arguments.
        message = f'{Path(args[0]).name} failed ({result.returncode})'
        if Path(args[0]).name == 'security':
            # Security diagnostics can contain paths and supplied credentials.
            # Classify known errors using fixed text; never echo raw stderr.
            diagnostic = result.stderr or b''
            if isinstance(diagnostic, bytes):
                diagnostic = diagnostic.decode('utf-8', errors='replace')
            known_errors = (
                ('MAC verification failed during PKCS12 import',
                 'PKCS#12 MAC verification failed; check the passphrase and container algorithm compatibility'),
                ('Unknown format in import', 'signing input format is not recognized'),
                ('User interaction is not allowed', 'keychain access requires unavailable user interaction'),
                ('The specified keychain could not be found', 'temporary signing keychain was not found'),
            )
            for marker, detail in known_errors:
                if marker in diagnostic:
                    message += ': ' + detail
                    break
        raise RuntimeError(message)
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


def signing_policy():
    publication = json.loads((ROOT / 'release/publication.json').read_text())
    policy = publication.get('signing_policy', 'publicly-trusted')
    if policy not in ('publicly-trusted', 'self-signed-preview', 'self-signed'):
        raise ValueError('unknown signing policy')
    if policy == 'self-signed-preview' and publication.get('channel') != 'developer-preview':
        raise ValueError('self-signed policy is limited to developer previews')
    return policy

@contextmanager
def apple_keychain(policy):
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
            environment = dict(os.environ)
            if policy == 'publicly-trusted':
                api_key = temp / 'AuthKey.p8'
                api_key.write_bytes(base64.b64decode(required('APPLE_API_KEY_BASE64'), validate=True)); api_key.chmod(0o600)
                environment['APPLE_API_KEY_PATH'] = str(api_key)
                required('APPLE_API_KEY'); required('APPLE_API_ISSUER')
            else:
                # Self-signed previews cannot be notarized. Do not accidentally
                # consume unrelated developer credentials from the runner.
                for name in ('APPLE_API_KEY', 'APPLE_API_KEY_PATH', 'APPLE_API_ISSUER',
                             'APPLE_API_KEY_BASE64', 'APPLE_ID', 'APPLE_PASSWORD',
                             'APPLE_TEAM_ID', 'APPLE_PROVIDER_SHORT_NAME'):
                    environment.pop(name, None)
            yield environment
        finally:
            try:
                run(['security', 'list-keychains', '-d', 'user', '-s', *previous], capture_output=True)
            finally:
                run(['security', 'delete-keychain', str(keychain)], capture_output=True)


def verify_windows(path, policy):
    script = ROOT / 'scripts/verify-windows-signature.ps1'
    command = ['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'RemoteSigned', '-File', str(script), '-Artifact', str(path), '-Thumbprint', fingerprint('WINDOWS_CERTIFICATE_THUMBPRINT', (40,))]
    if policy in ('self-signed-preview', 'self-signed'):
        command.append('-SelfSignedPreview')
    run(command)


def configured_identity(system):
    publishers = json.loads((ROOT / 'release/publication.json').read_text())['publisher_identities']
    identity = publishers[{'Linux':'linux', 'Windows':'windows', 'Darwin':'macos'}[system]]
    if not isinstance(identity.get('name'), str) or not identity['name'].strip():
        raise ValueError('configure the public publisher name')
    configured = identity.get('certificate_fingerprint')
    if not isinstance(configured, str) or not re.fullmatch(r'(?:[a-fA-F0-9]{40}|[a-fA-F0-9]{64})', configured.replace(' ', '')):
        raise ValueError('configure a verified public signing fingerprint for '+system)
    expected = configured.replace(' ', '').upper()
    if system == 'Windows' and fingerprint('WINDOWS_CERTIFICATE_THUMBPRINT', (40,)).upper() != expected:
        raise ValueError('Windows signing identity differs from publication configuration')
    if system == 'Linux' and fingerprint('GCHAT_RELEASE_KEY').upper() != expected:
        raise ValueError('Linux signing identity differs from publication configuration')
    if system == 'Darwin':
        if signing_policy() in ('self-signed-preview', 'self-signed'):
            if required('APPLE_SIGNING_IDENTITY').replace(' ', '').upper() != expected:
                raise ValueError('self-signed Apple identity must be the pinned certificate fingerprint')
            return identity
        team = required('APPLE_TEAM_ID')
        if not re.fullmatch('[A-Z0-9]{10}', team):
            raise ValueError('invalid Apple team identifier')
        # The human publisher name is distinct from Apple's certificate CN.
        expected_name = f"Developer ID Application: {identity['name']} ({team})"
        if required('APPLE_SIGNING_IDENTITY') != expected_name:
            raise ValueError('Apple signing identity differs from publication configuration')
    return identity


@contextmanager
def application_from_dmg(bundle_dir):
    """Inspect the shipped app even when Tauri removes its intermediate bundle."""
    images = list((bundle_dir / 'dmg').glob('*.dmg'))
    if len(images) != 1 or not images[0].is_file() or images[0].is_symlink():
        raise ValueError('expected one signed disk image')
    image = images[0]
    before = sha(image)
    run(['codesign', '--verify', '--strict', str(image)])
    work = Path(tempfile.mkdtemp(prefix='gchat-inspect-dmg-')).resolve()
    mount = work / 'volume'
    mount.mkdir(mode=0o700)
    attempted = False
    try:
        attempted = True
        result = run(['hdiutil', 'attach', '-readonly', '-nobrowse', '-noautoopen',
                      '-plist', '-mountpoint', str(mount), str(image)], capture_output=True)
        entities = plistlib.loads(result.stdout).get('system-entities', [])
        mounts = [entity for entity in entities if entity.get('mount-point')]
        if len(mounts) != 1 or Path(mounts[0]['mount-point']).resolve() != mount:
            raise ValueError('disk image did not use the owned mountpoint')
        if not os.statvfs(mount).f_flag & os.ST_RDONLY:
            raise ValueError('disk image inspection requires a read-only mount')
        apps = list(mount.glob('*.app'))
        if len(apps) != 1 or not apps[0].is_dir() or apps[0].is_symlink():
            raise ValueError('expected one signed application in the disk image')
        yield apps[0]
    finally:
        # Never recursively remove a directory while its volume is still mounted.
        if attempted:
            run(['hdiutil', 'detach', str(mount)], capture_output=True)
        shutil.rmtree(work)
    if sha(image) != before:
        raise ValueError('disk image changed during application verification')


def bundle(target, output, environment, identity, policy, checkout):
    system, arch, triple, bundles = TARGETS[target]
    config = {'bundle': {'publisher': identity['name']}}
    if system == 'Windows':
        config['bundle']['windows'] = {'certificateThumbprint':fingerprint('WINDOWS_CERTIFICATE_THUMBPRINT', (40,)), 'digestAlgorithm':'sha256'}
        if policy == 'publicly-trusted':
            timestamp = required('WINDOWS_TIMESTAMP_URL')
            if not timestamp.startswith('https://'):
                raise ValueError('Windows timestamp service must use HTTPS')
            config['bundle']['windows'].update(timestampUrl=timestamp, tsp=True)
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
        run([sys.executable, 'scripts/collect-notices.py'], env=environment, cwd=checkout)
        npm = 'npm.cmd' if system == 'Windows' else 'npm'
        run([npm, 'run', 'tauri', '-w', '@gchat/client', '--', 'build', '--target', triple, '--bundles', ','.join(bundles), '--config', str(config_path)], env=environment, cwd=checkout)
        graph = json.loads(subprocess.check_output(
            ['cargo', 'metadata', '--manifest-path', 'apps/client/src-tauri/Cargo.toml',
             '--locked', '--filter-platform', triple, '--format-version=1'],
            cwd=checkout, env=environment))
        verify_resolved_protocol(graph, checkout.parent / 'gcoms')
        bundle_dir = build_root / triple / 'release/bundle'
        executables = []
        if system == 'Darwin':
            with application_from_dmg(bundle_dir) as app:
                run(['codesign', '--verify', '--deep', '--strict', '--verbose=2', str(app)])
                details = subprocess.run(['codesign', '-d', '--verbose=4', str(app)], capture_output=True, text=True, check=True)
                if policy == 'publicly-trusted':
                    if 'TeamIdentifier='+required('APPLE_TEAM_ID') not in details.stderr.splitlines() or 'Authority='+required('APPLE_SIGNING_IDENTITY') not in details.stderr.splitlines():
                        raise ValueError('signed application publisher differs from configured identity')
                elif 'Authority='+identity['name'] not in details.stderr.splitlines():
                    raise ValueError('self-signed application publisher differs from configured identity')
                certificate_prefix = Path(temp) / 'signer-'
                run(['codesign', '-d', '--extract-certificates=' + str(certificate_prefix), str(app)], capture_output=True)
                certificate = Path(str(certificate_prefix)+'0').read_bytes()
                expected = identity['certificate_fingerprint'].replace(' ', '').upper()
                actual = hashlib.new('sha256' if len(expected) == 64 else 'sha1', certificate).hexdigest().upper()
                if actual != expected:
                    raise ValueError('signed application certificate differs from configured fingerprint')
                if policy == 'publicly-trusted':
                    run(['spctl', '--assess', '--type', 'execute', '--verbose=2', str(app)])
                metadata = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
                name = metadata.get('CFBundleExecutable')
                if not isinstance(name, str) or Path(name).name != name or name in ('', '.', '..'):
                    raise ValueError('unsafe application executable name')
                executable = app / 'Contents/MacOS' / name
                executables.append({'name': name, 'sha256': sha(executable), 'size': executable.stat().st_size})
        elif system == 'Windows':
            executable = build_root / triple / 'release/gchat-desktop.exe'
            verify_windows(executable, policy)
            executables.append({'name': executable.name, 'sha256': sha(executable), 'size': executable.stat().st_size})
        patterns = {'deb':'deb/*.deb', 'appimage':'appimage/*.AppImage', 'nsis':'nsis/*.exe', 'dmg':'dmg/*.dmg'}
        files = []
        for kind in bundles:
            matches = list(bundle_dir.glob(patterns[kind]))
            if len(matches) != 1:
                raise ValueError('expected exactly one artifact per bundle format')
            path = matches[0]
            if system == 'Windows': verify_windows(path, policy)
            if system == 'Darwin':
                run(['codesign', '--verify', '--strict', str(path)])
                if policy == 'publicly-trusted': run(['xcrun', 'stapler', 'validate', str(path)])
            destination = output / path.name; shutil.copyfile(path, destination)
            if system == 'Linux':
                run(['gpg', '--batch', '--yes', '--pinentry-mode', 'loopback', '--passphrase-fd', '0', '--local-user', required('GCHAT_RELEASE_KEY'), '--armor', '--detach-sign', str(destination)], input=required('GCHAT_RELEASE_PASSPHRASE').encode(), env=environment)
                verify(str(destination)+'.asc', destination, required('GCHAT_RELEASE_KEY'))
            files.append({'name':destination.name,'format':kind,'sha256':sha(destination),'signing_verified':True})
        return files, executables


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--target',choices=TARGETS,required=True);p.add_argument('--gcoms',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--native-ci-report', type=Path, required=True, help='successful paired native-ci.json from this target and source pair')
    a=p.parse_args(argv)
    system,arch,triple,_=TARGETS[a.target]
    actual={'amd64':'x86_64','arm64':'aarch64'}.get(platform.machine().lower(),platform.machine().lower())
    host=subprocess.check_output(['rustc','-vV'],text=True)
    if platform.system()!=system or actual!=arch or f'host: {triple}\n' not in host:
        raise ValueError('release builds require the selected native OS, architecture, and Rust host')
    if os.environ.get('GC_DEFAULT_RELAY_BOOTSTRAP'):
        raise ValueError('official installers must use the signed bundled relay defaults')
    identity = configured_identity(system)
    policy = signing_policy()
    sources={}
    for name,path in [('gchat',ROOT),('gcoms',a.gcoms.resolve())]:
        if subprocess.check_output(['git','status','--porcelain'],cwd=path).strip(): raise ValueError('release source must be clean')
        sources[name]=subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()
    output=a.output.resolve();output.mkdir(parents=True,exist_ok=False)
    checkout, dependency_inputs = prepare_pair(ROOT, a.gcoms, output, triple, dict(os.environ))
    ci_report = output / 'provenance/native-ci.json'
    shutil.copyfile(a.native_ci_report.resolve(), ci_report)
    native_ci = verify_native_ci_inputs(ci_report, dependency_inputs)
    if system=='Darwin':
        with apple_keychain(policy) as environment: files,executables=bundle(a.target,output,environment,identity,policy,checkout)
    else: files,executables=bundle(a.target,output,dict(os.environ),identity,policy,checkout)
    verify_derived_inputs(checkout, dependency_inputs)
    verify_retained_inputs(output / 'provenance', dependency_inputs)
    for name,path in [('gchat',ROOT),('gcoms',a.gcoms.resolve())]:
        if subprocess.check_output(['git','status','--porcelain'],cwd=path).strip() or subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()!=sources[name]: raise ValueError('build changed source inputs')
    (output/'build.json').write_text(json.dumps({'schema':1,'target':a.target,'sources':sources,'publisher':identity,'signing_policy':policy,'public_ca_trust':policy=='publicly-trusted','apple_notarization':system=='Darwin' and policy=='publicly-trusted','dependency_inputs':dependency_inputs,'native_ci':native_ci,'files':files,'executables':executables},indent=2)+'\n')
    print('Signed bundle report: '+str(output/'build.json'))


if __name__=='__main__': main()
