#!/usr/bin/env python3
"""Re-sign an already qualified Mac app; notarize once, staple and assess it.

The application sources/native receipt remain the original pair. The separate
protected controller supplies the Developer ID policy. No compiler is invoked.
A pending Apple request is resumed by ID using the retained artifact, never
resubmitted. Keys exist only in the temporary signing context, outside output.
"""
import argparse
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time

from paired_sources import verify_native_ci_inputs, verify_retained_inputs
from release_evidence import digest, file_reference, read_json, require, source_identity

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('macos_notarize_package', ROOT / 'scripts/macos-package.py')
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)
wrapper = package.script('test-macos-bundle')
MACHO = {bytes.fromhex(value) for value in ('feedface', 'cefaedfe', 'feedfacf', 'cffaedfe',
                                          'cafebabe', 'bebafeca', 'cafebabf', 'bfbafeca')}
WORKFLOW = 'macos-notarize.yml'


def reference(root, path):
    return {'path': str(path.resolve().relative_to(root.resolve())), **package.reference(path)}


def save(output, report):
    package.write_json(output / 'report.json', report)


def publisher(publication):
    value = publication.get('publisher_identities', {}).get('macos', {})
    require(value.get('signing_policy') == 'publicly-trusted' and value.get('distribution') == 'developer-id' and
            re.fullmatch(r'[A-Z0-9]{10}', value.get('team_id', '')) is not None and
            re.fullmatch(r'[a-fA-F0-9]{64}', value.get('certificate_sha256', '')) is not None and
            re.fullmatch(r'[a-fA-F0-9]{40}', value.get('certificate_fingerprint', '')) is not None,
            'controller publication must pin a Developer ID certificate and team')
    return value


def validate_origin(run, artifact, args):
    workflow, name = {
        'native': ('macos-release.yml', args.target),
        'verified': ('macos-verify.yml', args.target + '-verified'),
        'resume': (WORKFLOW, args.target + '-notarized'),
    }[args.kind]
    require(run.get('id') == args.run_id and run.get('event') == 'workflow_dispatch' and
            run.get('path') == '.github/workflows/' + workflow and
            run.get('repository', {}).get('full_name') == package.REPO and
            run.get('status') == 'completed' and
            (args.kind == 'resume' or run.get('conclusion') == 'success'),
            'original run scope or terminal qualification differs')
    require(artifact.get('id') == args.artifact_id and artifact.get('name') == name and
            artifact.get('expired') is False and artifact.get('digest') == 'sha256:' + args.artifact_sha256 and
            artifact.get('workflow_run', {}).get('id') == args.run_id and
            artifact.get('workflow_run', {}).get('head_sha') == run.get('head_sha'),
            'original artifact identity or SHA-256 differs')
    if args.kind == 'native':
        require(run.get('head_sha') == args.gchat_commit, 'native workflow app commit differs')


def download(args, output):
    run = package.gh_json(f'repos/{package.REPO}/actions/runs/{args.run_id}')
    artifact = package.gh_json(f'repos/{package.REPO}/actions/artifacts/{args.artifact_id}')
    validate_origin(run, artifact, args)
    package.write_json(output / 'input-run.json', run)
    package.write_json(output / 'input-artifact.json', artifact)
    archive = output / 'input.zip'
    with archive.open('xb') as stream:
        subprocess.run(['gh', 'api', f'repos/{package.REPO}/actions/artifacts/{args.artifact_id}/zip',
                        '--allow-escape-sequences'], stdout=stream, check=True)
    require(digest(archive) == args.artifact_sha256, 'downloaded original artifact changed')
    package.extract_archive(archive, output / 'input')
    return run


def original_inputs(args, output):
    root = output / 'input'
    limitations = {}
    if args.kind == 'verified':
        recovered = root / 'verified'
        recovery = read_json(recovered / 'report.json')
        require(recovery.get('passed') is True and recovery.get('original_artifact_unchanged') is True and
                recovery.get('recompiled') is False and recovery.get('resigned') is False,
                'original retained-artifact recovery did not pass')
        native_root = recovered / 'original-package/retry-evidence/original-native'
        signed = recovered / 'signed'
        harness = recovered / 'controller.tar'
        limitations = {key: value for key, value in recovery.items() if key.startswith('original_post_build_') or
                       key in ('original_packaging_passed', 'original_native_executable_byte_comparison')}
    else:
        native_root = signed = root
        harness = None
    expected = {'gchat': args.gchat_commit, 'gcoms': args.gcoms_commit}
    repositories = {'gchat': args.gchat.resolve(), 'gcoms': args.gcoms.resolve()}
    require({name: source_identity(repo)['commit'] for name, repo in repositories.items()} == expected,
            'application checkouts do not match requested original commits')
    native = package.verify_native(native_root, args.target, expected, repositories)
    candidate = read_json(native_root / 'evidence/candidate.json')
    source_archive = file_reference(native_root / 'evidence', candidate['sources']['gchat']['archive'])
    build = read_json(signed / 'build.json')
    inputs = build.get('dependency_inputs', {})
    require(build.get('target') == args.target and inputs.get('sources') == native['sources'] and
            build.get('sources') == expected and build.get('native_ci') == native['native_ci'],
            'original installer/native source binding differs')
    require(verify_native_ci_inputs(signed / 'provenance/native-ci.json', inputs) == native['native_ci'],
            'original installer dependencies differ from native receipt')
    verify_retained_inputs(signed / 'provenance', inputs)
    smoke = package.script('macos-build').verify_application_smoke(signed, build, source_archive, harness)
    dmg = wrapper.select_dmg(build, signed / 'build.json')
    return signed, build, {
        'run': reference(output, output / 'input-run.json'),
        'artifact': reference(output, output / 'input-artifact.json'),
        'archive': reference(output, output / 'input.zip'),
        'build': reference(output, signed / 'build.json'),
        'application_smoke': reference(output, signed / 'application-smoke/report.json'),
        'native_ci': native['native_ci'], 'native_qualification': native,
        'native_receipt': reference(output, signed / 'provenance/native-ci.json'),
        'dmg': reference(output, dmg), 'limitations': limitations,
        'sources': smoke['sources'],
    }


@contextmanager
def mounted(commands, image, work, label):
    mount = work / label
    mount.mkdir()
    attempted = False
    try:
        attempted = True
        _, raw = commands.run(label + '-attach', ['hdiutil', 'attach', '-readonly', '-nobrowse',
                            '-noautoopen', '-plist', '-mountpoint', str(mount), str(image)])
        wrapper.validate_mount(raw, mount)
        require(bool(os.statvfs(mount).f_flag & os.ST_RDONLY), 'retained DMG mount is not read-only')
        yield wrapper.app_from_volume(mount)
    finally:
        if attempted:
            commands.run(label + '-detach', ['hdiutil', 'detach', str(mount)])
        mount.rmdir()


def macho(path):
    with path.open('rb') as stream:
        return stream.read(4) in MACHO


def bundle_identity(app, commands, label):
    """Hash original resources and signature-removed private executable copies.

    The app itself is untouched. Only Apple's _CodeSignature directory is omitted;
    all other files, internal symlinks and execute bits must compare exactly.
    """
    result = {}
    with tempfile.TemporaryDirectory(prefix='gchat-code-identity-', dir='/private/tmp' if platform.system() == 'Darwin' else None) as temp:
        for index, path in enumerate(sorted(app.rglob('*'))):
            relative = path.relative_to(app)
            if '_CodeSignature' in relative.parts:
                continue
            mode = path.lstat().st_mode
            key = relative.as_posix()
            if stat.S_ISLNK(mode):
                require(path.resolve().is_relative_to(app.resolve()), 'application symlink escapes its bundle')
                result[key] = {'kind': 'symlink', 'target': os.readlink(path)}
            elif stat.S_ISREG(mode):
                code = macho(path)
                normalized = path
                if code:
                    normalized = Path(temp) / str(index)
                    shutil.copy2(path, normalized)
                    commands.run(f'{label}-remove-signature-{index}', ['codesign', '--remove-signature', str(normalized)])
                result[key] = {'kind': 'macho' if code else 'file', 'sha256': digest(normalized),
                               'executable': bool(mode & 0o111)}
            else:
                require(stat.S_ISDIR(mode), 'unsupported special file in application')
    require(any(entry.get('kind') == 'macho' for entry in result.values()), 'application has no Mach-O code')
    return result


def parse_entitlements(raw):
    value = plistlib.loads(raw) if raw.strip() else {}
    require(isinstance(value, dict) and value.get('com.apple.security.get-task-allow') not in (True, 1),
            'Developer ID app must not retain debugger entitlement')
    return value


def sign_application(app, commands, output, identity):
    items = [path for path in app.rglob('*') if not path.is_symlink() and
             ((path.is_file() and macho(path)) or (path.is_dir() and path.suffix in ('.app', '.framework', '.xpc', '.appex')))]
    items.sort(key=lambda path: (-len(path.parts), str(path)))
    items.append(app)
    entitlement_root = output / 'entitlements'
    entitlement_root.mkdir()
    entitlements = []
    # Extract everything before changing any nested signature.
    for index, item in enumerate(items):
        _, raw = commands.run(f'entitlements-{index}', ['codesign', '-d', '--entitlements', ':-', str(item)])
        parsed = parse_entitlements(raw)
        path = entitlement_root / f'{index}.plist'
        path.write_bytes(plistlib.dumps(parsed))
        entitlements.append(path)
    for index, (item, entitlement) in enumerate(zip(items, entitlements)):
        command = ['codesign', '--force', '--sign', identity['certificate_fingerprint'], '--timestamp',
                   '--options', 'runtime', '--entitlements', str(entitlement), str(item)]
        commands.run(f'sign-code-{index}', command)
    signature = wrapper.verify_signature(commands, app, identity, 'developer-id-application')
    _, raw = commands.run('developer-id-details', ['codesign', '-d', '--verbose=4', str(app)])
    # codesign detail text is written to stderr, not stdout.
    details = (commands.output / 'developer-id-details.stderr').read_text(encoding='utf-8')
    require('Developer ID Application:' in details and 'TeamIdentifier=' + identity['team_id'] in details and
            re.search(r'flags=.*\bruntime\b', details) is not None,
            'signed application lacks Developer ID team or hardened runtime')
    return signature


def create_dmg(commands, stage, dmg):
    """Retry only DiskImages' transient busy error, within one packaging budget."""
    require(not dmg.exists() and not dmg.is_symlink(), 'refusing to replace an existing DMG')
    deadline = time.monotonic() + 300
    for attempt in range(3):
        remaining = deadline - time.monotonic()
        require(remaining > 0, 'create-dmg packaging deadline exhausted')
        label = 'create-dmg-' + str(attempt + 1)
        code, _ = commands.run(label, ['hdiutil', 'create', '-volname', 'GChat',
                                     '-srcfolder', str(stage), '-format', 'UDZO', str(dmg)],
                               timeout=remaining, allow_failure=True)
        if code == 0:
            require(dmg.is_file() and not dmg.is_symlink(), 'hdiutil produced no regular DMG')
            return
        error = (commands.output / (label + '.stderr')).read_text(errors='replace')
        require('hdiutil: create failed - Resource busy' in error and attempt < 2,
                f'{label} failed with exit {code}; see retained stderr')
        if dmg.exists() or dmg.is_symlink():
            require(dmg.is_file() and not dmg.is_symlink(), 'unexpected partial DMG type')
            dmg.unlink()  # Only our newly created, incomplete candidate.
        time.sleep(min(2 ** (attempt + 1), max(0, deadline - time.monotonic())))


def prepare_signed(args, output, report, commands, identity):
    signed, build, original = original_inputs(args, output)
    report.update(original=original, sources=build['dependency_inputs']['sources'])
    work = output / 'work'
    work.mkdir()
    image = file_reference(output, original['dmg'])
    wrapper.verify_signature(commands, image, build['publisher'], 'original-dmg')
    with mounted(commands, image, work, 'original') as source:
        wrapper.verify_signature(commands, source, build['publisher'], 'original-application')
        source_executable = wrapper.bundle_executable(source)
        wrapper.smoke.validate_artifacts(source_executable, signed / 'build.json', signed / 'provenance/native-ci.json')
        before = bundle_identity(source, commands, 'before')
        stage = work / 'image'
        stage.mkdir()
        app = stage / source.name
        commands.run('copy-original', ['ditto', '--rsrc', '--extattr', str(source), str(app)])
    sign_application(app, commands, output, identity)
    after = bundle_identity(app, commands, 'after')
    require(before == after, 're-signing changed application code or non-signature resources')
    report['code_identity'] = {'method': 'codesign_remove_signature_on_private_copies',
                               'before': before, 'after': after, 'unchanged': True}
    result = output / 'signed'
    result.mkdir()
    shutil.copytree(signed / 'provenance', result / 'provenance')
    dmg = result / (image.stem + '-notarized.dmg')
    (stage / 'Applications').symlink_to('/Applications', target_is_directory=True)
    try:
        create_dmg(commands, stage, dmg)
    finally:
        # Never let an artifact uploader traverse the system Applications link.
        (stage / 'Applications').unlink()
    commands.run('sign-dmg', ['codesign', '--sign', identity['certificate_fingerprint'], '--timestamp',
                             '--identifier', 'boo.gchat.app.diskimage', str(dmg)])
    wrapper.verify_signature(commands, dmg, identity, 'developer-id-dmg')
    executable = wrapper.bundle_executable(app)
    new_build = {**build, 'publisher': identity, 'signing_policy': 'publicly-trusted', 'public_ca_trust': True,
                 'apple_notarization': False, 'resigned_without_recompilation': True,
                 'signing_controller': report['controller'],
                 'files': [{'name': dmg.name, 'format': 'dmg', 'sha256': digest(dmg), 'signing_verified': True}],
                 'executables': [{'name': executable.name, **package.reference(executable)}]}
    package.write_json(result / 'build.json', new_build)
    report.update(dmg=reference(output, dmg), build=reference(output, result / 'build.json'))
    shutil.rmtree(work)
    save(output, report)
    return dmg


def notary_command(environment, *arguments):
    command = ['xcrun', 'notarytool', *arguments, '--key', environment['APPLE_API_KEY_PATH'],
               '--key-id', environment['APPLE_API_KEY'], '--issuer', environment['APPLE_API_ISSUER']]
    # `log` writes Apple's JSON log directly to its output-path argument.
    return command if arguments[0] == 'log' else [*command, '--output-format', 'json']


def submit_once(dmg, environment, output, report, commands):
    require('notarization' not in report, 'existing notarization must be resumed, never resubmitted')
    report['notarization'] = {'status': 'submission_outcome_unknown', 'submission_dmg_sha256': digest(dmg)}
    save(output, report)  # A transport failure must not cause a blind second upload.
    _, raw = commands.run('notary-submit', notary_command(environment, 'submit', str(dmg)), timeout=180)
    reply = json.loads(raw)
    require(re.fullmatch(r'[0-9a-fA-F-]{36}', reply.get('id', '')) is not None,
            'Apple submission did not return an identifiable request; do not resubmit')
    report['notarization'].update(id=reply['id'], status='In Progress',
                                  submission=reference(output, commands.output / 'notary-submit.stdout'))
    report['pending'] = True
    save(output, report)


def await_notary(environment, output, report, commands, seconds):
    request = report['notarization']
    require(request.get('id') and request.get('status') in ('In Progress', 'Accepted'),
            'pending notarization needs its retained request ID; do not resubmit')
    deadline = time.monotonic() + seconds
    while True:
        label = 'notary-info-' + str(len(report['commands']))
        _, raw = commands.run(label, notary_command(environment, 'info', request['id']))
        info = json.loads(raw)
        require(info.get('id') == request['id'], 'Apple status refers to another notarization')
        request.update(status=info.get('status'), info=reference(output, commands.output / (label + '.stdout')))
        save(output, report)
        if request['status'] in ('Accepted', 'Invalid', 'Rejected'):
            log = commands.output / ('notary-log-' + str(len(report['commands'])) + '.json')
            commands.run('notary-log-' + str(len(report['commands'])),
                         notary_command(environment, 'log', request['id'], str(log)))
            request['log'] = reference(output, log)
            save(output, report)
            require(request['status'] == 'Accepted', 'Apple rejected the retained notarization; see notary log')
            accepted = read_json(log)
            require(accepted.get('jobId') == request['id'] and accepted.get('status') == 'Accepted' and
                    accepted.get('sha256') == request['submission_dmg_sha256'],
                    'Apple accepted log does not bind the submitted DMG bytes')
            return True
        require(request['status'] == 'In Progress', 'unknown notarization state; retained for investigation')
        if time.monotonic() >= deadline:
            report['pending'] = True
            save(output, report)
            return False
        time.sleep(min(20, max(0, deadline - time.monotonic())))


def gatekeeper_preflight(output, report, commands):
    code, raw = commands.run('gatekeeper-preflight', ['spctl', '--status'], allow_failure=True)
    require(code == 0 and raw.decode('utf-8').strip() == 'assessments enabled',
            'Gatekeeper must be enabled on this worker before signing or Apple submission; no policy bypass is used')
    report['gatekeeper_preflight'] = {'assessment_policy_enabled': True, 'policy_modified': False,
                                    'evidence': [reference(output, commands.output / ('gatekeeper-preflight.' + stream))
                                                 for stream in ('stdout', 'stderr')]}
    save(output, report)


def assess_gatekeeper(dmg, output, report, commands, identity):
    commands.run('staple-dmg', ['xcrun', 'stapler', 'staple', str(dmg)])
    # Stapling changes DMG bytes. Retain the new hash before subsequent local
    # checks so their failure can resume the same accepted Apple request.
    report['post_staple_dmg_sha256'] = digest(dmg)
    report['dmg'] = reference(output, dmg)
    save(output, report)
    commands.run('validate-dmg-ticket', ['xcrun', 'stapler', 'validate', str(dmg)])
    wrapper.verify_signature(commands, dmg, identity, 'stapled-dmg')
    report['stapling'] = {'dmg_validated': True, 'standalone_app_ticket_stapled': False,
                         'evidence': [reference(output, commands.output / (label + '.' + stream))
                                      for label in ('staple-dmg', 'validate-dmg-ticket')
                                      for stream in ('stdout', 'stderr')]}
    quarantine = '0083;' + format(int(time.time()), 'x') + ';GChat qualification;'
    commands.run('quarantine-dmg', ['xattr', '-w', 'com.apple.quarantine', quarantine, str(dmg)])
    _, raw = commands.run('read-dmg-quarantine', ['xattr', '-p', 'com.apple.quarantine', str(dmg)])
    require(raw.decode().strip() == quarantine, 'DMG quarantine was not retained')
    commands.run('gatekeeper-enabled', ['spctl', '--status'])
    require('assessments enabled' in (commands.output / 'gatekeeper-enabled.stdout').read_text(),
            'Gatekeeper assessments are disabled on this worker')
    commands.run('gatekeeper-dmg', ['spctl', '--assess', '--type', 'open', '--verbose=2',
                                   '--context', 'context:primary-signature', str(dmg)])
    with tempfile.TemporaryDirectory(prefix='gchat-gatekeeper-', dir='/private/tmp') as temp:
        work = Path(temp)
        with mounted(commands, dmg, work, 'gatekeeper') as source:
            app = work / source.name
            commands.run('copy-gatekeeper-app', ['ditto', '--rsrc', '--extattr', str(source), str(app)])
            require(bundle_identity(app, commands, 'final') == report['code_identity']['before'],
                    'actual DMG app differs from original normalized application')
            commands.run('quarantine-app', ['xattr', '-w', 'com.apple.quarantine', quarantine, str(app)])
            _, raw = commands.run('read-app-quarantine', ['xattr', '-p', 'com.apple.quarantine', str(app)])
            require(raw.decode().strip() == quarantine, 'copied application quarantine was not retained')
            wrapper.verify_signature(commands, app, identity, 'gatekeeper-application')
            commands.run('gatekeeper-app', ['spctl', '--assess', '--type', 'execute', '--verbose=2', str(app)])
            commands.run('app-notarization', ['codesign', '--verify', '--strict', '-R=notarized',
                                             '--check-notarization', str(app)])
    report['gatekeeper'] = {'quarantine_applied': True, 'dmg_assessment_passed': True,
                           'app_assessment_passed': True, 'app_notarization_requirement_passed': True,
                           'cleanup_complete': True, 'assessment_policy_enabled': True,
                           'interactive_first_launch_dialog_tested': False,
                           'evidence': [reference(output, commands.output / (label + '.' + stream))
                                        for label in ('read-dmg-quarantine', 'read-app-quarantine',
                                                      'gatekeeper-enabled', 'gatekeeper-dmg',
                                                      'gatekeeper-app', 'app-notarization')
                                        for stream in ('stdout', 'stderr')]}


def finish(args, output, report, commands, identity):
    dmg = file_reference(output, report['dmg'])
    require(digest(dmg) == report.get('post_staple_dmg_sha256', report['notarization']['submission_dmg_sha256']),
            'submitted/stapled DMG changed before accepted-request recovery')
    assess_gatekeeper(dmg, output, report, commands, identity)
    build_path = output / 'signed/build.json'
    build = read_json(build_path)
    build['apple_notarization'] = True
    build['files'][0]['sha256'] = digest(dmg)
    package.write_json(build_path, build)
    report.update(build=reference(output, build_path), dmg=reference(output, dmg))
    previous_smoke = output / 'signed/application-smoke'
    if previous_smoke.exists():
        failures = output / 'previous-attempts'
        failures.mkdir(exist_ok=True)
        previous_smoke.rename(failures / ('application-smoke-' + str(len(report['commands']))))
    command = [sys.executable, str(ROOT / 'scripts/test-macos-bundle.py'), '--build-manifest', str(build_path),
               '--native-receipt', str(output / 'signed/provenance/native-ci.json'),
               '--publication', str(output / 'publication.json'), '--output', str(output / 'signed/application-smoke'),
               '--temp-parent', '/private/tmp', '--timeout', '30']
    commands.run('installed-application-smoke', command, timeout=900, process_group=True)
    smoke_path = output / 'signed/application-smoke/report.json'
    smoke = read_json(smoke_path)
    require(smoke.get('passed') is True and smoke.get('gui_startup_passed') is True and
            smoke.get('inputs_unchanged') is True and smoke.get('cleanup', {}).get('passed') is True and
            smoke.get('sources') == report['sources'] and smoke.get('target') == args.target,
            'new signed application smoke or cleanup did not pass')
    require(smoke['inputs']['dmg']['sha256'] == digest(dmg) and
            smoke['inputs']['build_manifest']['sha256'] == digest(build_path) and
            smoke['inputs']['publication']['sha256'] == digest(output / 'publication.json'),
            'new signed application smoke tested different inputs')
    report.update(application_smoke=reference(output, smoke_path), passed=True, pending=False)


def validate_resume(report, args, controller):
    status = report.get('notarization', {}).get('status')
    require(report.get('scope') == 'retained_macos_developer_id_notarization' and
            report.get('controller') == controller and
            ((status == 'In Progress' and report.get('pending') is True) or status == 'Accepted') and
            report.get('passed') is False and report.get('cleanup_complete') is True and
            report.get('target') == args.target and
            {key: value['commit'] for key, value in report.get('sources', {}).items()} ==
            {'gchat': args.gchat_commit, 'gcoms': args.gcoms_commit} and
            report.get('notarization', {}).get('id'), 'resume artifact is not this pending frozen request')


def run(args):
    require(platform.system() == 'Darwin' and wrapper.smoke.native_target() == args.target,
            'retained Mac signing requires the matching native host')
    controller = package.verify_controller(ROOT, os.environ, WORKFLOW)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {'schema': 1, 'scope': 'retained_macos_developer_id_notarization', 'controller': controller,
              'target': args.target, 'passed': False, 'pending': False, 'commands': [],
              'recompiled': False, 'resigned': True, 'native_tests_rerun': False,
              'production_network_requested': False, 'cleanup_complete': False}
    try:
        origin = download(args, output)
        if args.kind == 'resume':
            # Move the downloaded artifact aside before restoring its complete original layout.
            downloaded = output / 'input'
            prior = read_json(downloaded / 'notarized/report.json')
            validate_resume(prior, args, controller)
            require(origin['head_sha'] == controller['commit'], 'pending request was made by another controller')
            downloaded.rename(output / 'resume-input')
            for name in ('input-run.json', 'input-artifact.json', 'input.zip'):
                (output / name).rename(output / ('resume-' + name))
            for path in (output / 'resume-input/notarized').iterdir():
                if path.name.startswith('resume-'):
                    continue
                if path.is_dir():
                    shutil.copytree(path, output / path.name)
                else:
                    shutil.copy2(path, output / path.name)
            report = prior
            report['pending'] = False
            report.pop('error', None)  # The unchanged prior receipt is retained below.
            shutil.copy2(output / 'resume-input/notarized/report.json', output / 'resume-previous-report.json')
            report['resumed_from'] = reference(output, output / 'resume-previous-report.json')
        else:
            shutil.copyfile(ROOT / 'release/publication.json', output / 'publication.json')
            subprocess.run(['git', 'archive', '--format=tar', '--output', str(output / 'controller.tar'), controller['commit']], cwd=ROOT, check=True)
            report.update(publication=reference(output, output / 'publication.json'),
                          controller_archive=reference(output, output / 'controller.tar'))
        require((output / 'publication.json').read_bytes() == (ROOT / 'release/publication.json').read_bytes(),
                'controller publisher policy differs from retained signing authority')
        identity = publisher(read_json(output / 'publication.json'))
        report['publisher'] = identity
        logs = output / 'logs' / ('attempt-' + str(len(report.get('attempts', [])) + 1))
        logs.mkdir(parents=True)
        report.setdefault('attempts', []).append({'logs': str(logs.relative_to(output)),
                                                  'kind': args.kind, 'started_at': wrapper.smoke.timestamp()})
        commands = wrapper.Commands(logs, report)
        gatekeeper_preflight(output, report, commands)
        installer = package.script('build-installer')
        report['cleanup_complete'] = False
        with installer.apple_keychain('publicly-trusted') as environment:
            if args.kind != 'resume':
                dmg = prepare_signed(args, output, report, commands, identity)
                submit_once(dmg, environment, output, report, commands)
            else:
                require(digest(file_reference(output, report['dmg'])) == report.get(
                            'post_staple_dmg_sha256', report['notarization']['submission_dmg_sha256']),
                        'pending notarization DMG no longer matches submitted bytes')
            accepted = await_notary(environment, output, report, commands, args.poll_seconds)
        report['cleanup_complete'] = True
        # Accepted-request recovery does not need private signing material.
        # Keychain cleanup is complete before staple/Gatekeeper/app checks.
        save(output, report)
        if accepted:
            finish(args, output, report, commands, identity)
        require(package.verify_controller(ROOT, os.environ, WORKFLOW) == controller, 'controller source changed')
        for name, repo in (('gchat', args.gchat), ('gcoms', args.gcoms)):
            require(source_identity(repo) == report['sources'][name], 'original application source changed')
    except (OSError, ValueError, RuntimeError, KeyError, plistlib.InvalidFileException, subprocess.SubprocessError) as error:
        report['passed'] = False
        report['pending'] = bool(report.get('notarization', {}).get('id') and
                                 report['notarization'].get('status') == 'In Progress')
        report['error'] = str(error)
    finally:
        save(output, report)
    print(json.dumps({'passed': report['passed'], 'pending': report['pending'], 'report': str(output / 'report.json')}))
    return 0 if report['passed'] else 2 if report['pending'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=('native', 'verified', 'resume'), required=True)
    parser.add_argument('--target', choices=package.TARGETS, required=True)
    parser.add_argument('--run-id', type=int, required=True)
    parser.add_argument('--artifact-id', type=int, required=True)
    parser.add_argument('--artifact-sha256', required=True)
    parser.add_argument('--gchat', type=Path, required=True)
    parser.add_argument('--gcoms', type=Path, required=True)
    parser.add_argument('--gchat-commit', required=True)
    parser.add_argument('--gcoms-commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--poll-seconds', type=int, default=600)
    args = parser.parse_args()
    for value, size in ((args.gchat_commit, 40), (args.gcoms_commit, 40), (args.artifact_sha256, 64)):
        require(re.fullmatch('[0-9a-f]{' + str(size) + '}', value) is not None, 'full immutable hashes required')
    require(args.run_id > 0 and args.artifact_id > 0 and 0 <= args.poll_seconds <= 900, 'bounded run/poll inputs required')
    return run(args)


if __name__ == '__main__':
    sys.exit(main())
