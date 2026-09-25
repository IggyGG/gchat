#!/usr/bin/env python3
"""Convert retained native-worker results to a source-bound coordinator receipt.

This does not turn a CI pass into fleet/privacy qualification. Compatibility and
installed-release acceptance remain separate publication prerequisites.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from paired_sources import verify_native_ci_inputs, verify_retained_inputs
from release_coordinator import atomic_json, read_receipt
from release_pair import validate


def load_module(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def source_pair(value, expected):
    return all(isinstance(value.get(p), dict) and
               all(value[p].get(k) == v for k, v in expected[p].items()) for p in expected)


def verify(manifest, platform, directory, output, tools=None):
    validate(manifest); directory = Path(directory).resolve(); output = Path(output).resolve()
    expected = {p: v['commit'] for p, v in manifest['sources'].items()}
    reports = list(directory.rglob('build.json'))
    reports = [p for p in reports if not any(part in ('inputs', 'build', 'native-tests') for part in p.relative_to(directory).parts[:-1])]
    if len(reports) != 1: raise ValueError('native build receipt missing or ambiguous')
    report = reports[0]; build = json.loads(report.read_text()); root = report.parent
    binding = json.loads((root / 'release-binding.json').read_text())
    if binding.get('candidate') != manifest or binding.get('platform') != platform or binding.get('build_sha256') != sha(report):
        raise ValueError('native worker did not attest to this exact reserved candidate')
    artifacts = []
    if platform in ('android', 'ios'):
        if build.get('passed') is not True or build.get('sources_unchanged') is not True or not source_pair(build.get('sources', {}), manifest['sources']):
            raise ValueError('mobile build failed or source binding differs')
        if platform == 'android':
            signed = json.loads((root / 'signing.json').read_text())
            smoke = json.loads((root / 'emulator-smoke/report.json').read_text())
            driver = json.loads((root / 'emulator-driver.json').read_text())
            if (signed.get('passed') is not True or signed.get('private_keystore_removed') is not True
                    or signed.get('sources') != build['sources'] or smoke.get('passed') is not True
                    or smoke.get('inputs_unchanged') is not True or smoke.get('cleanup', {}).get('passed') is not True
                    or driver.get('passed') is not True or driver.get('process_stopped') is not True):
                raise ValueError('Android signature, installed-app, source or cleanup check failed')
            pin = signed['certificate_sha256']
            if pin != manifest['policy']['android_certificate_sha256']: raise ValueError('Android publisher differs from release policy')
            android = load_module('android-build')
            for item in signed['artifacts']:
                path = root / 'signed' / Path(item['path']).name
                if sha(path) != item['sha256']: raise ValueError('APK bytes changed')
                if tools is None: raise ValueError('independent Android signature tools are required')
                android.verify_signature(path, Path(tools), pin)
                artifacts.append(path)
            bundle = signed['bundle']; path = root / 'signed' / Path(bundle['path']).name
            if sha(path) != bundle['sha256'] or str(bundle['version_code']) != manifest['versions']['android']:
                raise ValueError('AAB bytes or reserved version code differ')
            import subprocess
            verified = json.loads(subprocess.check_output(['java', str(Path(__file__).with_name('VerifyAndroidBundle.java')), str(path), pin]))
            if verified.get('passed') is not True or verified.get('certificate_sha256') != pin: raise ValueError('AAB publisher verification failed')
            artifacts.append(path)
        else:
            if (build.get('build_number') != manifest['versions']['ios'] or build.get('bundle') != 'boo.gchat.app'
                    or build.get('application', {}).get('marketing_version') != manifest['versions']['linux-x86_64']):
                raise ValueError('iOS bundle/version differs from reservation')
            for field in ('simulator', 'signing_cleanup'):
                item = build[field]; matches = [p for p in root.rglob(Path(item['path']).name) if p.is_file() and sha(p) == item['sha256']]
                if len(matches) != 1: raise ValueError('iOS linked qualification evidence is missing')
                proof = json.loads(matches[0].read_text())
                if proof.get('passed') is not True: raise ValueError('iOS native gate did not pass')
            ipa = build['application']['ipa']; matches = list(root.glob('*.ipa'))
            if len(matches) != 1 or sha(matches[0]) != ipa['sha256']: raise ValueError('iOS artifact changed')
            if build['application']['profile']['certificate_sha256'] != manifest['policy']['ios_certificate_sha256']:
                raise ValueError('iOS publisher differs from release policy')
            artifacts += matches
    else:
        if build.get('sources') != expected or build.get('target') != platform:
            raise ValueError('desktop source or target differs')
        inputs = build['dependency_inputs']
        if not source_pair(inputs.get('sources', {}), manifest['sources']): raise ValueError('desktop dependency source mismatch')
        native = verify_native_ci_inputs(root / 'provenance/native-ci.json', inputs)
        verify_retained_inputs(root / 'provenance', inputs)
        if build.get('native_ci') != native: raise ValueError('desktop native dependency binding differs')
        if platform == 'linux-x86_64':
            smoke = json.loads((root / 'application-smoke/report.json').read_text())
            if smoke.get('passed') is not True or smoke.get('inputs_unchanged') is not True or smoke.get('children_stopped') is not True:
                raise ValueError('packaged Linux lifecycle/cleanup did not pass')
            from release_signatures import verify as verify_gpg
            for item in build['files']:
                verify_gpg(root / (item['name'] + '.asc'), root / item['name'], 'F4F6F8550D2AA952A189640D58430838AA3230BB')
        if platform == 'windows-x86_64':
            load_module('windows-build').collect(root, expected)
        elif platform.startswith('macos'):
            mac = load_module('macos-build')
            evidence = root / 'evidence'; candidate = json.loads((evidence / 'candidate.json').read_text())
            mac.validate_sources(candidate, evidence)
            for project in ('gchat', 'gcoms'):
                name = 'native.' + project + '.' + platform
                result = json.loads(mac.file_reference(evidence, candidate['checks'][name]).read_text())
                mac.validate_report(name, result, candidate, evidence, candidate['artifacts'])
            mac.verify_application_smoke(root, build, mac.file_reference(evidence, candidate['sources']['gchat']['archive']))
        for item in build['files']:
            path = root / item['name']
            if path.parent != root or sha(path) != item['sha256'] or item.get('signing_verified') is not True:
                raise ValueError('desktop installer binding differs')
            artifacts.append(path)
            if platform == 'linux-x86_64': artifacts.append(Path(str(path) + '.asc'))
        updater = json.loads((root / 'updater-artifacts.json').read_text())
        from release_feed import minisign_verify
        for item in updater:
            path = (root / item['name']).resolve()
            if not path.is_relative_to(root / 'updater') or sha(path) != item['sha256']:
                raise ValueError('updater payload changed')
            signature = Path(str(path) + '.sig')
            if sha(signature) != item['signature_sha256']: raise ValueError('updater signature changed')
            minisign_verify(path, signature.read_text().strip(), manifest['policy']['updater_public_key'])
            artifacts += [path, signature]
    # Copy evidence under this receipt; references cannot escape its directory.
    # Native extraction stays immutable and can be hardlinked on the same volume.
    import shutil
    retained = output.parent / 'verified'; retained.mkdir(exist_ok=True)
    evidence = []
    for path in [report, *artifacts]:
        name = sha(path) + '-' + path.name
        destination = retained / name
        if not destination.exists(): shutil.copyfile(path, destination)
        if sha(destination) != sha(path): raise ValueError('retained verified evidence changed')
        evidence.append({'path': destination.relative_to(output.parent).as_posix(), 'sha256': sha(destination)})
    result = {'schema': 1, 'release_id': manifest['release_id'], 'sources': manifest['sources'], 'platform': platform,
              'stage': 'verify', 'passed': True, 'source_unchanged': True, 'evidence': evidence}
    atomic_json(output, result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--state', type=Path, required=True); p.add_argument('--android-tools', type=Path)
    args = p.parse_args()
    manifest = validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text())); platform = os.environ['GCHAT_RELEASE_TARGET']
    key = hashlib.sha256(__import__('release_pair').canonical([manifest['release_id'], platform, 'build'])).hexdigest()
    build = args.state / 'jobs' / key
    read_receipt(build / 'receipt.json', manifest, platform, 'build')
    verify(manifest, platform, build / 'native', Path(os.environ['GCHAT_RELEASE_RECEIPT']), args.android_tools)


if __name__ == '__main__': main()
