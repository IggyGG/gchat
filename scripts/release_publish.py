#!/usr/bin/env python3
"""Publish qualified desktop updates and observe their exact public bytes."""
import argparse
import hashlib
import html
import json
import os
import tempfile
from pathlib import Path
import urllib.request
from release_pair import canonical, validate
from release_coordinator import atomic_json, read_receipt
from release_feed import publish, digest
from release_apt import build as publish_apt


def write_public(path, data, immutable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if immutable and path.exists():
        if path.read_bytes() != data:
            raise ValueError('immutable download details changed')
        return
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
            temporary.chmod(0o644); os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def linux_download_page(manifest, feed, apt, signature, root, url):
    """Expose the already qualified publication to humans without a browser API.

    The caller has verified source receipts, signatures and public updater bytes.
    Hold the feed lock so replaying an older publication cannot regress this page.
    """
    import fcntl
    validate(manifest)
    binding = json.loads(feed['binding'])
    release = manifest['release_id']; number = manifest['versions']['linux-x86_64']
    if (binding['release_id'], binding['version'], binding['target'], feed['version']) != (
            release, number, 'linux-x86_64', number):
        raise ValueError('download page differs from qualified release')
    package_path = f'pool/{release}/g-chat_{number}_amd64.deb'
    if apt['package'] != package_path or digest(root / 'apt' / package_path) != apt['sha256']:
        raise ValueError('download package differs from published APT artifact')
    url = url.rstrip('/')
    # Same origin and immutable path as the signed updater binding.
    prefix = f'{url}/artifacts/{release}/{binding["sha256"]}'
    if not feed['url'].startswith(prefix) or '/' in feed['url'][len(prefix):] or not feed['url'].endswith('.AppImage'):
        raise ValueError('unexpected public updater URL')
    base = f'{url}/downloads/linux-x86_64/{release}'
    escape = html.escape
    details = {'schema': 1, 'release_id': release, 'sources': manifest['sources'],
               'version': number, 'updater': feed,
               'debian': {'url': f'{url}/apt/{package_path}', 'sha256': apt['sha256'],
                          'signature_url': base + '/package.asc'}}
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Cache-Control" content="no-cache">
<title>GChat {escape(number)} for Linux</title>
<style>body{{font:1rem/1.6 system-ui,sans-serif;max-width:44rem;margin:3rem auto;padding:0 1rem;background:#191d21;color:#e7edf3}}a{{color:#9ed1ff}}code{{overflow-wrap:anywhere}}li{{margin:1rem 0}}</style></head><body>
<a href="https://gchat.boo/#downloads">← GChat downloads</a>
<h1>GChat {escape(number)} for Linux</h1><p>64-bit Intel / AMD. Signed production download.</p>
<ul><li><a href="{escape(details['debian']['url'])}">Download Ubuntu / Debian package</a><br>
Open with your package installer. <a href="{escape(base)}/package.asc">GPG signature</a><br>
SHA-256: <code>{escape(apt['sha256'])}</code></li>
<li><a href="{escape(feed['url'])}">Download AppImage</a><br>Allow execution, then launch it.<br>
SHA-256: <code>{escape(binding['sha256'])}</code></li></ul>
<p>{escape(feed['notes'])}</p>
<p><a href="{escape(base)}/release.json">Exact source, hashes and signed updater details</a> ·
<a href="https://github.com/IggyGG/gchat/blob/main/docs/INSTALL.md">Install and verify signatures</a></p>
<p>Existing APT installations receive the same qualified package through their configured repository.
Your open instance keeps running until its next normal start.</p></body></html>'''.encode()
    destination = root / 'downloads/linux-x86_64'
    with (root / '.publish.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if json.loads((root / 'desktop/linux/x86_64/latest.json').read_text()) != feed:
            raise ValueError('a different release is now public; do not regress downloads')
        write_public(destination / release / 'release.json', canonical(details), immutable=True)
        write_public(destination / release / 'package.asc', Path(signature).read_bytes(), immutable=True)
        write_public(destination / release / 'index.html', page, immutable=True)
        latest = destination / 'latest.html'
        write_public(latest, page)
    return latest


def job(state, manifest, platform, stage):
    key=hashlib.sha256(canonical([manifest['release_id'],platform,stage])).hexdigest()
    return state/'jobs'/key


def installer_download_page(manifest, platform, feed, installer, verified, root, url):
    """Publish a human download for the same qualified Windows/Mac candidate."""
    import fcntl
    import shutil
    from release_feed import TARGETS
    validate(manifest)
    labels = {'windows-x86_64': ('Windows', '.exe', 'Run the installer.'),
              'macos-aarch64': ('Mac with Apple silicon', '.dmg', 'Open the disk image and drag GChat to Applications.'),
              'macos-x86_64': ('Mac with Intel processor', '.dmg', 'Open the disk image and drag GChat to Applications.')}
    label, suffix, instructions = labels[platform]
    proof, _ = read_receipt(verified, manifest, platform, 'verify')
    sha = digest(installer); size = installer.stat().st_size
    if (not installer.name.endswith(suffix) or not 0 < size <= 512 * 1024**2
            or not any(e['sha256'] == sha for e in proof['evidence'])):
        raise ValueError('installer is not covered by the qualified platform receipt')
    binding = json.loads(feed['binding']); release = manifest['release_id']
    number = manifest['versions'][platform]; os_name, arch = TARGETS[platform]
    if (binding['release_id'], binding['version'], binding['target'], feed['version']) != (
            release, number, os_name + '-' + arch, number):
        raise ValueError('installer page differs from qualified release')
    root = Path(root); url = url.rstrip('/')
    relative = f'artifacts/{release}/{sha}{suffix}'
    artifact = root / relative
    destination = root / 'downloads' / platform
    base = f'{url}/downloads/{platform}/{release}'
    details = {'schema': 1, 'release_id': release, 'sources': manifest['sources'],
               'version': number, 'updater': feed,
               'installer': {'url': f'{url}/{relative}', 'sha256': sha, 'size': size}}
    escape = html.escape
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GChat {escape(number)} for {escape(label)}</title>
<style>body{{font:1rem/1.6 system-ui,sans-serif;max-width:44rem;margin:3rem auto;padding:0 1rem;background:#191d21;color:#e7edf3}}a{{color:#9ed1ff}}code{{overflow-wrap:anywhere}}</style></head><body>
<a href="https://gchat.boo/#downloads">← GChat downloads</a>
<h1>GChat {escape(number)} for {escape(label)}</h1>
<p><a href="{escape(details['installer']['url'])}">Download signed installer</a></p>
<p>{escape(instructions)}</p><p>SHA-256: <code>{sha}</code></p>
<p>{escape(feed['notes'])}</p>
<p><a href="{escape(base)}/release.json">Exact sources, installer hash and signed update details</a></p>
</body></html>'''.encode()
    with (root / '.publish.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if json.loads((root / f'desktop/{os_name}/{arch}/latest.json').read_text()) != feed:
            raise ValueError('a different release is now public; do not regress downloads')
        artifact.parent.mkdir(parents=True, exist_ok=True)
        if artifact.exists():
            if artifact.stat().st_size != size or digest(artifact) != sha:
                raise ValueError('immutable public installer changed')
        else:
            with tempfile.NamedTemporaryFile(dir=artifact.parent, delete=False) as stream:
                temporary = Path(stream.name)
                try:
                    with installer.open('rb') as source: shutil.copyfileobj(source, stream)
                    stream.flush(); os.fsync(stream.fileno())
                    if digest(temporary) != sha: raise ValueError('installer changed during copy')
                    temporary.chmod(0o644); os.replace(temporary, artifact)
                finally: temporary.unlink(missing_ok=True)
        write_public(destination / release / 'release.json', canonical(details), immutable=True)
        write_public(destination / release / 'index.html', page, immutable=True)
        write_public(destination / 'latest.html', page)
    return details


def select_artifacts(paths, platform):
    # A file may be referenced as both an installer and an updater artifact.
    # read_receipt verifies every reference before selection; deduplicate paths,
    # never distinct installer candidates or conflicting signature files.
    paths = list(dict.fromkeys(paths))
    endings={'linux-x86_64':'.AppImage','macos-aarch64':'.app.tar.gz','macos-x86_64':'.app.tar.gz','windows-x86_64':'.exe'}
    payloads=[x for x in paths if x.name.endswith(endings[platform])]
    # Installers and updater payloads can be the same NSIS bytes; deduplicate by hash.
    payloads=list({digest(x):x for x in payloads}.values())
    if len(payloads)!=1:raise ValueError('verified updater payload missing or ambiguous')
    payload=payloads[0]
    # Verification stored names as SHA256-originalname. Match the original basename.
    original=payload.name[65:]
    signatures=[x for x in paths if x.name[65:]==original+'.sig']
    if len(signatures)!=1:raise ValueError('verified updater signature missing or ambiguous')
    updater_signature = signatures[0]
    package = package_signature = None
    if platform == 'linux-x86_64':
        packages = [x for x in paths if x.name.endswith('.deb')]
        if len(packages) != 1:
            raise ValueError('verified Debian package missing or ambiguous')
        package = packages[0]
        signatures = [x for x in paths if x.name[65:] == package.name[65:] + '.asc']
        if len(signatures) != 1:
            raise ValueError('verified Debian signature missing or ambiguous')
        package_signature = signatures[0]
    return payload, updater_signature, package, package_signature



def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--state',type=Path,required=True);p.add_argument('--config',type=Path,required=True);a=p.parse_args()
    config=json.loads(a.config.read_text());manifest=validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()))
    platform=os.environ['GCHAT_RELEASE_TARGET'];output=Path(os.environ['GCHAT_RELEASE_RECEIPT'])
    verified=job(a.state,manifest,platform,'verify')/'receipt.json'
    compatibility=job(a.state,manifest,platform,'compatibility')/'receipt.json'
    proof,_=read_receipt(verified,manifest,platform,'verify');read_receipt(compatibility,manifest,platform,'compatibility')
    paths=[verified.parent/i['path'] for i in proof['evidence']]
    payload, signature, package, package_signature = select_artifacts(paths, platform)
    installer = None
    if package is None:
        installers = {digest(p): p for p in paths if p.name.endswith('.exe' if platform == 'windows-x86_64' else '.dmg')}
        if len(installers) != 1: raise ValueError('qualified installer missing or ambiguous')
        installer = next(iter(installers.values()))
    root=Path(config['public_root'])
    feed=publish(manifest,platform,payload,signature.read_text(),root,config['public_url'],
                 manifest['policy']['updater_public_key'],config['signer'],verified,compatibility)
    apt = None
    if package is not None:
        apt = publish_apt(manifest,package,package_signature,verified,compatibility,root/'apt',config['gpg_key'])
    # Availability requires the actual public URL to serve the candidate pointer.
    binding=json.loads(feed['binding']);os_name,arch=binding['target'].split('-',1)
    url=config['public_url'].rstrip('/')+'/desktop/'+os_name+'/'+arch+'/latest.json'
    with urllib.request.urlopen(url,timeout=30) as response:
        if response.url!=url:raise ValueError('public update endpoint redirected')
        public=json.loads(response.read(32769))
    if public!=feed:raise ValueError('public feed has not reached the qualified candidate')
    # Read the public artifact too: a healthy pointer cannot mask a missing or
    # corrupted payload, including after a interrupted volume restore.
    observed = hashlib.sha256(); size = 0
    with urllib.request.urlopen(feed['url'], timeout=60) as response:
        if response.url != feed['url']: raise ValueError('public artifact redirected')
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > binding['size']: raise ValueError('public artifact exceeds signed size')
            observed.update(chunk)
    if size != binding['size'] or observed.hexdigest() != binding['sha256']:
        raise ValueError('public artifact bytes differ from signed binding')
    if apt is not None:
        linux_download_page(manifest, public, apt, package_signature, root, config['public_url'])
    else:
        details = installer_download_page(manifest, platform, public, installer,
                                         verified, root, config['public_url'])
        expected = details['installer']; observed = hashlib.sha256(); size = 0
        with urllib.request.urlopen(expected['url'], timeout=60) as response:
            if response.url != expected['url']: raise ValueError('public installer redirected')
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > expected['size']: raise ValueError('public installer exceeds qualified size')
                observed.update(chunk)
        if size != expected['size'] or observed.hexdigest() != expected['sha256']:
            raise ValueError('public installer differs from qualified bytes')
    result=output.parent/'public-feed.json' ;atomic_json(result,public)
    atomic_json(output,{'schema':1,'release_id':manifest['release_id'],'sources':manifest['sources'],
        'platform':platform,'stage':'publish','passed':True,'source_unchanged':True,
        'evidence':[{'path':result.name,'sha256':digest(result)}]})


if __name__=='__main__':main()
