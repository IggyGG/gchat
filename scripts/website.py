#!/usr/bin/env python3
"""Build the static GChat site from verified release metadata; no browser API calls."""
import argparse
import hashlib
import html
import json
import re
import shutil
import tempfile
import subprocess
import uuid
from release_signatures import fingerprint, verify
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPOSITORIES = ('https://github.com/IggyGG/gchat', 'https://github.com/IggyGG/gcoms')
TARGETS = {
    ('windows-x86_64', 'nsis'): 'Windows · 64-bit installer',
    ('macos-aarch64', 'dmg'): 'macOS · Apple Silicon',
    ('macos-x86_64', 'dmg'): 'macOS · Intel',
    ('linux-x86_64', 'deb'): 'Ubuntu / Debian · .deb',
    ('linux-x86_64', 'appimage'): 'Linux · AppImage',
    ('android-arm64', 'apk'): 'Android · ARM64 APK',
    ('android-x86_64', 'apk'): 'Android · x86_64 APK',
}
DESKTOP_TARGETS = {key for key in TARGETS if not key[0].startswith('android-')}
PLATFORMS = {'linux': 'Linux', 'macos': 'macOS', 'windows': 'Windows', 'android': 'Android'}


def validate(data):
    if data.get('schema') == 2:
        return validate_platforms(data)
    if data.get('schema') != 1 or data.get('channel') not in ('developer-preview', 'production'):
        raise ValueError('unsupported download manifest')
    artifacts = data.get('artifacts')
    if not isinstance(artifacts, list):
        raise ValueError('artifacts must be a list')
    version = data.get('version')
    if version is None:
        if artifacts:
            raise ValueError('unreleased manifest cannot contain downloads')
        return data
    if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', version):
        raise ValueError('invalid release version')
    key = data.get('release_key', {})
    fingerprint(key.get('fingerprint'))
    if key.get('url') != f'https://github.com/IggyGG/gchat/releases/download/v{version}/gchat-release-key.asc' or not re.fullmatch(r'[0-9a-f]{64}', key.get('sha256', '')):
        raise ValueError('release key must be a pinned asset in this release')
    seen = set()
    prefix = f'https://github.com/IggyGG/gchat/releases/download/v{version}/'
    for artifact in artifacts:
        key = (artifact.get('target'), artifact.get('format'))
        if key not in TARGETS or key in seen:
            raise ValueError('unexpected or duplicate download target')
        seen.add(key)
        for field in ('url', 'signature_url'):
            value = artifact.get(field, '')
            name = value.removeprefix(prefix)
            if not value.startswith(prefix) or not re.fullmatch(r'[A-Za-z0-9_.+-]+', name) or name in ('.', '..'):
                raise ValueError('downloads must reference immutable assets in this release')
        if not re.fullmatch(r'[0-9a-f]{64}', artifact.get('sha256', '')):
            raise ValueError('missing artifact checksum')
        if artifact['signature_url'] != artifact['url'] + '.asc' or not re.fullmatch(r'[0-9a-f]{64}', artifact.get('signature_sha256', '')):
            raise ValueError('missing matching signature checksum')
        if artifact.get('signing_verified') is not True:
            raise ValueError('unverified artifact cannot be advertised')
    required = {key for key in TARGETS if key[0] == 'linux-x86_64'} if data['channel'] == 'production' else DESKTOP_TARGETS
    if not required <= seen:
        raise ValueError('the complete signed platform set is required')
    return data


def release_asset(value, tag):
    prefix = f'https://github.com/IggyGG/gchat/releases/download/{tag}/'
    name = value.removeprefix(prefix) if isinstance(value, str) else ''
    if not isinstance(value, str) or not value.startswith(prefix) or not re.fullmatch(r'[A-Za-z0-9_.+-]+', name) or name in ('.', '..'):
        raise ValueError('downloads must reference immutable assets in their own release')
    return name


def validate_platforms(data):
    if data.get('channel') != 'production' or data.get('version') is not None:
        raise ValueError('independent platform releases have no shared version')
    pin = fingerprint(data.get('publisher_fingerprint'))
    releases = data.get('releases')
    if not isinstance(releases, dict) or not releases:
        raise ValueError('platform releases are required')
    for tag, release in releases.items():
        if not re.fullmatch(r'v\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', tag):
            raise ValueError('invalid platform release tag')
        version = release.get('version')
        if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+', version) or not (tag == 'v' + version or tag.startswith('v' + version + '-')):
            raise ValueError('platform version differs from tag')
        if release.get('manifest_format') not in ('platform-v1', 'legacy-v1'):
            raise ValueError('unsupported signed platform manifest')
        sources = release.get('sources', {})
        if set(sources) != {'gchat', 'gcoms'} or not all(isinstance(x, str) and re.fullmatch('[0-9a-f]{40}', x) for x in sources.values()):
            raise ValueError('platform source pair is required')
        key = release.get('release_key', {})
        if fingerprint(key.get('fingerprint')) != pin or release_asset(key.get('url'), tag) != 'gchat-release-key.asc':
            raise ValueError('platform release key differs from pinned publisher')
        manifest = release.get('manifest', {})
        expected = 'platform-release.json' if release['manifest_format'] == 'platform-v1' else 'release-manifest.json'
        if release_asset(manifest.get('url'), tag) != expected or manifest.get('signature_url') != manifest['url'] + '.asc':
            raise ValueError('signed release manifest missing')
        for value in (key.get('sha256'), manifest.get('sha256'), manifest.get('signature_sha256')):
            if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
                raise ValueError('platform metadata checksum missing')
    seen, used = set(), set()
    artifacts = data.get('artifacts')
    if not isinstance(artifacts, list):
        raise ValueError('artifacts must be a list')
    for artifact in artifacts:
        target = (artifact.get('target'), artifact.get('format'))
        tag = artifact.get('release')
        if target not in TARGETS or target in seen or tag not in releases:
            raise ValueError('unexpected, duplicate or unbound platform artifact')
        seen.add(target); used.add(tag)
        release_asset(artifact.get('url'), tag)
        release_asset(artifact.get('signature_url'), tag)
        if artifact.get('signature_url') != artifact['url'] + '.asc' or artifact.get('signing_verified') is not True:
            raise ValueError('unverified platform artifact')
        for field in ('sha256', 'signature_sha256'):
            if not re.fullmatch('[0-9a-f]{64}', artifact.get(field, '')):
                raise ValueError('platform artifact checksum missing')
    if used != set(releases) or not {('linux-x86_64', 'deb'), ('linux-x86_64', 'appimage')} <= seen:
        raise ValueError('preserve complete Linux downloads and reference each release')
    return data


def validate_signed_manifest(release, manifest, artifacts):
    if manifest.get('version') != release['version']:
        raise ValueError('signed manifest version mismatch')
    sources = manifest.get('sources', {})
    commits = {name: value.get('commit') if isinstance(value, dict) else value for name, value in sources.items()}
    if commits != release['sources']:
        raise ValueError('signed manifest source pair mismatch')
    if release['manifest_format'] == 'platform-v1':
        if manifest.get('kind') != 'platform-release' or manifest.get('schema') != 1 or not artifacts or manifest.get('tag') != artifacts[0]['release']:
            raise ValueError('wrong signed platform manifest type')
        packages = manifest.get('artifacts', {})
    else:
        packages = {item['name']: item for item in manifest.get('packages', [])}
    for artifact in artifacts:
        item = packages.get(artifact['url'].rsplit('/', 1)[-1], {})
        if item.get('sha256') != artifact['sha256'] or item.get('format') != artifact['format']:
            raise ValueError('artifact differs from signed release manifest')
        if release['manifest_format'] == 'platform-v1' and item.get('target') != artifact['target']:
            raise ValueError('signed artifact target mismatch')


def client_status(data):
    if data['version'] is None and data.get('schema') != 2:
        return 'Desktop and mobile applications. Signed public installers are being prepared.'
    present = {item['target'].split('-', 1)[0] for item in data['artifacts']}
    platforms = ', '.join(label for key, label in PLATFORMS.items() if key in present)
    return ('Signed downloads available above for ' + platforms + '. '
            'Privacy improvements and platform testing limits are documented in the release notes.')


def remote_check(data):
    for repo in REPOSITORIES:
        with open_public(repo, timeout=30, method='HEAD') as response:
            if response.status != 200:
                raise ValueError('public source mirror unavailable')
    if data.get('schema') == 2:
        for tag, release in data['releases'].items():
            with tempfile.TemporaryDirectory(prefix='gchat-platform-check-') as temporary:
                temp = Path(temporary); home = temp / 'gnupg'; home.mkdir(mode=0o700)
                key = temp / 'key.asc'; key_info = release['release_key']
                fetch(key_info['url'], key_info['sha256'], key)
                subprocess.run(['gpg', '--homedir', str(home), '--batch', '--import', str(key)], check=True, capture_output=True)
                manifest = temp / 'manifest.json'; signature = temp / 'manifest.asc'; info = release['manifest']
                fetch(info['url'], info['sha256'], manifest); fetch(info['signature_url'], info['signature_sha256'], signature)
                verify(signature, manifest, data['publisher_fingerprint'], home)
                artifacts = [a for a in data['artifacts'] if a['release'] == tag]
                validate_signed_manifest(release, json.loads(manifest.read_text()), artifacts)
                for artifact in artifacts:
                    path = temp / 'installer'; signature = temp / 'installer.asc'
                    fetch(artifact['url'], artifact['sha256'], path)
                    fetch(artifact['signature_url'], artifact['signature_sha256'], signature)
                    verify(signature, path, data['publisher_fingerprint'], home)
        return
    if data['version'] is None:
        return
    with tempfile.TemporaryDirectory(prefix='gchat-download-check-') as temp:
        temp = Path(temp); home = temp / 'gnupg'; home.mkdir(mode=0o700)
        key = temp / 'key.asc'
        fetch(data['release_key']['url'], data['release_key']['sha256'], key)
        subprocess.run(['gpg', '--homedir', str(home), '--batch', '--import', str(key)], check=True, capture_output=True)
        for artifact in data['artifacts']:
            path = temp / 'installer'; signature = temp / 'installer.asc'
            fetch(artifact['url'], artifact['sha256'], path)
            fetch(artifact['signature_url'], artifact['signature_sha256'], signature)
            verify(signature, path, data['release_key']['fingerprint'], home)


def open_public(url, timeout, method=None):
    for attempt in range(2):
        # A failed cached GitHub redirect can outlive the underlying outage.
        # Retry only transient gateway errors; the canonical link and required
        # artifact digest remain unchanged.
        request_url = url if attempt == 0 else url + '?gchat-verification=' + uuid.uuid4().hex
        try:
            request = Request(request_url, method=method) if method else request_url
            return urlopen(request, timeout=timeout)
        except HTTPError as error:
            if attempt or error.code not in (502, 503, 504):
                raise


def fetch(url, expected, path):
    digest = hashlib.sha256()
    with open_public(url, timeout=120) as response, path.open('wb') as output:
        while chunk := response.read(1024 * 1024):
            digest.update(chunk); output.write(chunk)
    if digest.hexdigest() != expected:
        raise ValueError('public asset checksum mismatch')


def downloads(data):
    escape = html.escape
    if data.get('schema') == 2:
        links = '<p>Production downloads · versions qualified independently by platform.</p><ul>'
        for a in data['artifacts']:
            release = data['releases'][a['release']]
            links += (f'<li><a href="{escape(a["url"])}">Download {TARGETS[(a["target"], a["format"])]}</a>'
                      f' · {escape(release["version"])} · <a href="{escape(a["signature_url"])}">Signature</a>'
                      f' · <a href="{escape(release["manifest"]["url"])}">Build evidence</a></li>')
        key = next(iter(data['releases'].values()))['release_key']
        links += '</ul><p><a href="' + escape(key['url']) + '">Release signing key</a> · Fingerprint: <code>' + escape(data['publisher_fingerprint']) + '</code></p>'
    elif data['version'] is None:
        links = '<p>Desktop and mobile apps are being prepared. Downloads will appear here after installation and signing checks pass.</p>'
    else:
        links = '<p>' + ('Production ' if data['channel'] == 'production' else 'Developer preview ') + escape(data['version']) + '</p><ul>'
        for a in data['artifacts']:
            links += f'<li><a href="{escape(a["url"])}">Download {TARGETS[(a["target"], a["format"])]}</a> · <a href="{escape(a["signature_url"])}">Signature</a></li>'
        links += '</ul><p><a href="' + escape(data['release_key']['url']) + '">Release signing key</a> · Fingerprint: <code>' + escape(data['release_key']['fingerprint']) + '</code></p>'
    return '''<section id="downloads"><div class="wrap">
<div class="sec-head"><p class="sec-label">Get GChat</p><h2>Download. Connect. Start talking.</h2>
<p>Secure communication over GComs. Your relay settings are included.</p></div>
''' + links + '''
<p><a href="https://github.com/IggyGG/gchat">GChat source</a> · <a href="https://github.com/IggyGG/gcoms">GComs protocol</a> · <a href="https://github.com/IggyGG/gchat/releases">Release notes</a></p>
<ol class="steps">
<li class="step"><span class="n">01</span><h3>Install</h3><p>Windows: run the installer. macOS: open the DMG and drag GChat to Applications. Ubuntu/Debian: open the .deb with your package installer. AppImage: allow execution, then launch it.</p></li>
<li class="step"><span class="n">02</span><h3>Create your identity</h3><p>Open GChat and choose a passphrase. It protects your identity and history. Keep it safe; there is no passphrase reset.</p></li>
<li class="step"><span class="n">03</span><h3>Join</h3><p>Choose Join and paste a conversation invitation from someone you trust. It can include the network and channel together. Review its details and choose your nickname.</p></li>
<li class="step"><span class="n">04</span><h3>Start talking</h3><p>The green network dot shows when you are connected. A network-only invitation connects without joining a channel; use Create to start your own conversation.</p></li>
</ol><p><a href="https://github.com/IggyGG/gchat/blob/main/docs/INSTALL.md">Installation, signature verification, and upgrades</a></p>
</div></section>'''


def build(output, data):
    output = output.resolve()
    if output == ROOT or ROOT.is_relative_to(output) or output.is_relative_to(ROOT / 'website'):
        raise ValueError('build output must not overwrite source')
    output.mkdir(parents=True, exist_ok=True)
    page = (ROOT / 'website/index.template.html').read_text(encoding='utf-8')
    if page.count('@@DOWNLOADS@@') != 1 or page.count('@@CLIENT_STATUS@@') != 1:
        raise ValueError('website template must contain both content slots exactly once')
    page = page.replace('@@DOWNLOADS@@', downloads(data)).replace('@@CLIENT_STATUS@@', client_status(data))
    if '@@' in page:
        raise ValueError('unresolved website template marker')
    rendered = page.encode('utf-8')
    (output / 'index.html').write_bytes(rendered)
    (output / 'downloads.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8', newline='\n')
    shutil.copyfile(ROOT / 'website/robots.txt', output / 'robots.txt')
    (output / 'fonts').mkdir(exist_ok=True)
    for name in ('fixedsys-excelsior.ttf', 'LICENSE-CC0'):
        shutil.copyfile(ROOT / 'apps/client/public/fonts' / name, output / 'fonts' / name)
    (output / 'build.json').write_text(json.dumps({'index_sha256': hashlib.sha256(rendered).hexdigest(), 'version': data['version']}) + '\n', encoding='utf-8', newline='\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'release/downloads.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/website')
    parser.add_argument('--check-remote', action='store_true')
    args = parser.parse_args()
    data = validate(json.loads(args.manifest.read_text(encoding='utf-8')))
    if args.check_remote:
        remote_check(data)
    build(args.output, data)


if __name__ == '__main__':
    main()
