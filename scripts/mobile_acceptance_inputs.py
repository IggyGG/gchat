"""Retained mobile acceptance inputs, separate from desktop provider receipts."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import plistlib
import re
import subprocess
import zipfile

from release_jobs import gh, extract, acceptance_archive
from release_network_canary import module

TARGETS = ('android', 'ios')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_provider(item):
    require(isinstance(item, dict)
            and all(type(item.get(key)) is int and item[key] > 0 for key in ('run', 'artifact'))
            and item.get('conclusion') == 'success'
            and re.fullmatch('[0-9a-f]{64}', item.get('archive', ''))
            and re.fullmatch('[0-9a-f]{40}', item.get('controller', ''))
            and set(item.get('sources', {})) == {'gchat', 'gcoms'}
            and all(re.fullmatch('[0-9a-f]{40}', value) for value in item['sources'].values()),
            'invalid retained mobile provider identity')
    name = item.get('manifest', '')
    path = PurePosixPath(name)
    require(name and '\\' not in name and ':' not in name and not path.is_absolute()
            and '..' not in path.parts and path.name == 'build.json',
            'invalid retained mobile manifest path')
    return item


def validate_inputs(value):
    require(value.get('target') in TARGETS, 'unsupported mobile acceptance target')
    for name in ('current', 'baseline', 'peer'):
        validate_provider(value[name])
    current, previous = value['current'], value['baseline']
    require(all(current[key] != previous[key] for key in ('run', 'artifact', 'archive', 'sources')),
            'mobile upgrade needs distinct retained releases')
    require(value.get('peer_target') == ('linux-x86_64' if value['target'] == 'android' else 'macos-aarch64')
            and value['peer']['sources'] == current['sources'],
            'mobile network peer must use the current exact pair on its native host')
    return value


def acquire(name, spec, target, output, manifest=None):
    validate_provider(spec)
    require(target in TARGETS, 'mobile artifact cannot use desktop binding rules')
    recovered = spec.get('recovery')
    if recovered is not None:
        require(target == 'ios' and recovered.get('kind') == 'ios-retained', 'unknown retained mobile recovery')
    run = gh(f'actions/runs/{spec["run"]}')
    root = output / name; root.mkdir()
    archive = root / 'artifact.zip'
    artifact = acceptance_archive(spec, archive)
    retained = artifact is not None
    if not retained: artifact = gh(f'actions/artifacts/{spec["artifact"]}')
    require(run.get('status') == 'completed' and run.get('conclusion') == 'success'
            and run.get('head_sha') == spec['controller']
            and run.get('head_repository', {}).get('full_name') == 'IggyGG/gchat'
            and run.get('path') == ('.github/workflows/ios-verify.yml' if recovered else f'.github/workflows/{target}-release.yml')
            and run.get('event') == 'workflow_dispatch'
            and artifact.get('workflow_run', {}).get('id') == spec['run']
            and (retained or artifact.get('expired') is False)
            and artifact.get('digest') == 'sha256:' + spec['archive']
            and type(artifact.get('size_in_bytes')) is int
            and 0 < artifact['size_in_bytes'] <= 2 * 1024**3,
            'retained mobile workflow/archive binding differs')
    if not retained:
        with archive.open('xb') as stream:
            subprocess.run(['gh', 'api', f'repos/IggyGG/gchat/actions/artifacts/{spec["artifact"]}/zip'],
                           stdout=stream, stderr=subprocess.PIPE, check=True, timeout=600)
    require(digest(archive) == spec['archive'] and archive.stat().st_size == artifact['size_in_bytes'],
            'retained mobile archive bytes differ')
    extract(archive, root / 'original')
    report_path = root / 'original' / spec['manifest']
    report = json.loads(report_path.read_text())
    if recovered:
        from release_pair import validate
        import release_ios_recovery as recovery
        candidate = validate(recovered['candidate'])
        rule = recovered['rule']; reviewed = recovery.reviewed_inputs(candidate, rule)
        require(recovered['inputs'] == reviewed and spec['manifest'] == 'ios-verification/build.json'
                and {key: value['commit'] for key, value in candidate['sources'].items()} == spec['sources']
                and (manifest is None or candidate == manifest), 'retained iOS acceptance candidate differs')
        recovery.validate_run(candidate, run, artifact, rule, retained=retained)
        recovery.validate_report(candidate, report, rule, reviewed)
        require(artifact.get('name') == 'ios-verified-' + rule['request'], 'retained iOS verification artifact name differs')
        original_path = recovery.reference(report['original_build'], report_path.parent)
        original = json.loads(original_path.read_text())
        require(original.get('passed') is False
                and original.get('sources') == candidate['sources'], 'retained original iOS verdict/source changed')
        gates = [recovery.reference(item, report_path.parent) for item in
                 (report['signing_cleanup'], report['simulator'], report['simulator_binding']['verification'])]
        require(all(json.loads(path.read_text()).get('passed') is True for path in gates),
                'retained iOS verification gate failed')
        return {'root': original_path.parent, 'build': original, 'build_manifest': original_path,
                'retained_lifecycle': gates[1], 'archive_sha256': spec['archive'], 'sources': spec['sources']}
    expected_name = f'android-{spec["sources"]["gchat"]}-{spec["sources"]["gcoms"]}' if target == 'android' else (
        f'ios-{spec["sources"]["gchat"]}-{spec["sources"]["gcoms"]}-{report.get("build_number")}')
    require(artifact.get('name') == expected_name, 'retained mobile artifact name differs')
    require(report.get('passed') is True and report.get('sources_unchanged') is True
            and {key: item.get('commit') for key, item in report.get('sources', {}).items()} == spec['sources'],
            'retained mobile native build/source checks failed')
    if manifest is not None:
        binding = json.loads((report_path.parent / 'release-binding.json').read_text())
        require(binding.get('candidate') == manifest and binding.get('platform') == target
                and binding.get('build_sha256') == digest(report_path),
                'retained mobile reservation differs')
    return {'root': report_path.parent, 'build': report, 'build_manifest': report_path,
            'archive_sha256': spec['archive'], 'sources': spec['sources']}


def android_application(item, pin):
    android = module('android-build')
    root = item['root']
    signed = json.loads((root / 'signing.json').read_text())
    require(signed.get('passed') is True and signed.get('private_keystore_removed') is True
            and signed.get('certificate_sha256') == pin
            and signed.get('sources') == item['build']['sources']
            and digest(root / 'build.json') == signed.get('build', {}).get('sha256'),
            'retained Android publisher/source binding differs')
    artifact, _, paths = android.bundle_smoke_inputs(root, signed)
    tools = android.sdk(require_ndk=False) / 'build-tools' / android.BUILD_TOOLS
    for path in paths:
        android.verify_signature(path, tools, pin)
    # The app code, rather than a changed outer APK resource/version, identifies
    # the executable actually installed from these verified AAB-derived splits.
    libraries = []
    for path in paths:
        with zipfile.ZipFile(path) as zipped:
            for name in zipped.namelist():
                if name == 'lib/x86_64/libgchat_native.so':
                    libraries.append(hashlib.sha256(zipped.read(name)).hexdigest())
    require(len(libraries) == 1, 'one retained x86 mobile executable required')
    item.update(apks=paths, activity=artifact['activity'], binary_sha256=libraries[0],
                publisher=pin, application_rebuilt=False, application_resigned=False)
    return item


def ios_application(item, pin, output):
    ios = module('ios-build')
    lifecycle = module('ios-lifecycle')
    root, build = item['root'], item['build']
    require(build.get('bundle') == ios.BUNDLE and build.get('team') == ios.TEAM
            and build.get('application', {}).get('profile', {}).get('certificate_sha256') == pin,
            'retained iOS publisher differs')
    for key in ('simulator', 'signing_cleanup', 'simulator_linked_authority'):
        proof_path = (item['retained_lifecycle'] if key == 'simulator' and 'retained_lifecycle' in item
                      else lifecycle.relocated(build[key], root))
        require(json.loads(proof_path.read_text()).get('passed') is True,
                'retained iOS native authority/signing gate failed')
    archive = lifecycle.relocated(build['simulator_archive'], root)
    with zipfile.ZipFile(archive) as zipped:
        ios.inspect_zip(zipped)
    app_root = output / 'application'
    ios.run(['ditto', '-x', '-k', archive, app_root])
    apps = list(app_root.glob('*.app'))
    require(len(apps) == 1, 'one retained simulator app required')
    app = apps[0]
    info = plistlib.loads((app / 'Info.plist').read_bytes())
    executable = info.get('CFBundleExecutable', '')
    require(info.get('CFBundleIdentifier') == ios.BUNDLE
            and info.get('CFBundleSupportedPlatforms') == ['iPhoneSimulator']
            and info.get('CFBundleVersion') == build['build_number']
            and executable and Path(executable).name == executable,
            'retained iOS simulator identity differs')
    binary = app / executable
    expected = build['simulator_executable']
    require(digest(binary) == expected['sha256'] and binary.stat().st_size == expected['size'],
            'retained iOS executable changed')
    verified = ios.simulator_tools().verify_app(app, output / 'linked-verification')
    actual = json.loads(Path(verified['path']).read_text())
    original = json.loads(lifecycle.relocated(build['simulator_linked_authority'], root).read_text())
    require(actual['linked_simulator_authority'] == original['linked_simulator_authority']
            and actual['host_entitlements'] == original['host_entitlements'],
            'retained iOS linked authority changed')
    item.update(app=app, binary=binary, binary_sha256=digest(binary), publisher=pin,
                application_rebuilt=False, application_resigned=False)
    return item
