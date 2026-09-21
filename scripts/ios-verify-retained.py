#!/usr/bin/env python3
"""Recheck a retained IPA against a completed same-source simulator lifecycle.

Original failed receipts and application archives remain immutable. This check
cannot qualify physical devices, messaging, push or App Store approval.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import platform
import plistlib
import re
import shutil
import subprocess
import zipfile

from paired_sources import dependency_identity, verify_retained_inputs
from release_evidence import source_identity

SPEC = importlib.util.spec_from_file_location('ios_journey', Path(__file__).with_name('ios-lifecycle.py'))
journey = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(journey)
ios = journey.ios
require = ios.require


def validate_inputs(original, cleanup, provenance, spec):
    journey.build_binding(original, spec)
    require(original.get('application') and original.get('simulator_archive')
            and original.get('simulator_executable'), 'both original application artifacts must exist')
    require(all(cleanup.get(key) is True for key in ('passed', 'original_keychain_search_restored',
                'temporary_keychain_removed', 'original_profiles_unchanged', 'private_certificate_removed'))
            and cleanup.get('errors') == [], 'original signing cleanup did not pass')
    require(provenance == original.get('dependency_inputs'), 'retained dependency inputs differ')
    identity = dependency_identity(provenance)
    require(identity['sources'] == original['sources'] and identity['target'] == 'aarch64-apple-ios',
            'retained dependency source/target mismatch')
    require(set(original.get('feature_graphs', {})) == set(ios.TARGETS), 'missing original feature graphs')
    for graph in original['feature_graphs'].values():
        require('network-client' in graph.get('gcoms', []) and not ({'embedded', 'launch'} & set(graph['gcoms']))
                and 'gcoms-node' in graph and 'relay-host' not in graph['gcoms-node'],
                'original graph does not prove a mobile network client')


def simulator_run_binding(run, artifact, spec):
    ios.policy.source_commit(spec['controller_commit'])
    require(type(spec['run_id']) is int and type(spec['artifact_id']) is int
            and re.fullmatch('[0-9a-f]{64}', spec['artifact_sha256']), 'invalid simulator identifiers')
    require(run.get('id') == spec['run_id'] and run.get('head_sha') == spec['controller_commit']
            and run.get('head_repository', {}).get('full_name') == 'IggyGG/gchat'
            and run.get('event') == 'workflow_dispatch' and run.get('status') == 'completed'
            and run.get('conclusion') in ('success', 'failure') and run.get('path') == '.github/workflows/ios-lifecycle.yml',
            'simulator workflow did not finish on the bound controller')
    ios.policy.release_ref(run['head_branch'])
    require(re.fullmatch('[A-Za-z0-9_-]+', spec['request_id'])
            and artifact.get('id') == spec['artifact_id']
            and artifact.get('name') == 'ios-lifecycle-' + spec['request_id']
            and artifact.get('expired') is False
            and artifact.get('workflow_run', {}).get('id') == spec['run_id']
            and artifact.get('digest') == 'sha256:' + spec['artifact_sha256'], 'simulator artifact binding mismatch')


def validate_simulator(candidate, original, spec, *, allow_incomplete=False):
    require(candidate.get('scope') == 'ios_exact_pair_xcode_simulator_lifecycle'
            and (candidate.get('passed') is True or (allow_incomplete and candidate.get('passed') is False))
            and candidate.get('sources_unchanged') is True
            and candidate.get('sources') == original['sources']
            and candidate.get('controller', {}).get('commit') == spec['controller_commit']
            and candidate.get('build_number') == original['build_number']
            and candidate.get('bundle') == ios.BUNDLE, 'simulator source, build or completed scope mismatch')
    require(candidate.get('device_rebuilt') is False and candidate.get('distribution_signer_used') is False,
            'simulator worker must not build or sign a device application')
    inputs = candidate['dependency_inputs']
    identity = dependency_identity(inputs)
    require(identity['sources'] == original['sources'] and identity['target'] == 'aarch64-apple-ios-sim',
            'simulator dependency source or target mismatch')
    for key in ('source_archive_sha256', 'npm_archives', 'npm_bindings'):
        require(inputs[key] == original['dependency_inputs'][key], 'simulator dependency input mismatch: ' + key)
    graph = candidate['feature_graph']
    require('network-client' in graph.get('gcoms', []) and not ({'embedded', 'launch'} & set(graph['gcoms']))
            and 'gcoms-node' in graph and 'relay-host' not in graph['gcoms-node'],
            'simulator is not an outbound network client')


def simulator_file(item, root):
    parts = PurePosixPath(item['path']).parts
    require(parts.count('ios-simulator-output') == 1, 'unexpected simulator evidence location')
    relative = PurePosixPath(*parts[parts.index('ios-simulator-output') + 1:])
    require(relative.parts and '..' not in relative.parts, 'unsafe simulator evidence location')
    path = root.joinpath(*relative.parts)
    require(path.is_file() and path.resolve().is_relative_to(root.resolve()) and not path.is_symlink()
            and ios.digest(path) == item['sha256']
            and path.stat().st_size == item['size'], 'simulator evidence hash mismatch')
    return path


def validate_linked_upload(report, original):
    """Keep the newly linked simulator proof separate from the unchanged IPA."""
    if report.get('simulator_reused_from_original') is True:
        validate_original_simulator_upload(report, original)
        return
    require(report.get('simulator_relinked_from_same_source') is True,
            'retained upload requires a separately linked same-source simulator')
    binding = report['simulator_binding']
    archive = ios.verify_reference(binding['archive'])
    require(ios.digest(archive) == report['inputs']['simulator']['artifact_sha256'],
            'simulator archive binding differs')
    candidate = json.loads(ios.verify_reference(binding['report']).read_text())
    validate_simulator(candidate, original, report['inputs']['simulator'], allow_incomplete=True)
    require(binding.get('lifecycle_rechecked') is True
            and binding.get('original_build_passed') is candidate.get('passed'),
            'original simulator verdict must be retained with a separate lifecycle check')
    proof = json.loads(ios.verify_reference(binding['verification']).read_text())
    authority = json.loads(ios.verify_reference(binding['linked_authority']).read_text())
    lifecycle = json.loads(ios.verify_reference(binding['lifecycle']).read_text())
    require(proof.get('scope') == 'ios_xcode_linked_simulator_authority' and proof.get('passed') is True
            and proof.get('device_qualified') is False and authority.get('passed') is True
            and proof.get('linked_simulator_authority') == authority.get('linked_simulator_authority')
            and proof.get('host_entitlements') == authority.get('host_entitlements'),
            'native simulator authority verification differs')
    require(lifecycle.get('scope') == 'ios_installed_simulator_profile_background_reopen'
            and lifecycle.get('passed') is True and lifecycle.get('cleanup_complete') is True
            and lifecycle.get('cleanup_errors') == [] and lifecycle.get('application_recompiled') is False
            and lifecycle.get('application_resigned') is False, 'simulator lifecycle or cleanup did not pass')
    journey.test_result(json.loads(ios.verify_reference(lifecycle['test_summary']).read_text()))
    ios.verify_reference(lifecycle['xctest_log'])
    original_lifecycle = json.loads(ios.verify_reference(binding['original_lifecycle']).read_text())
    require(original_lifecycle.get('cleanup_complete') is True and original_lifecycle.get('cleanup_errors') == [],
            'original simulator cleanup must remain complete')
    ios.verify_reference(binding['application'])
    for key in ('sha256', 'size'):
        require(binding['lifecycle'][key] == report['simulator'][key]
                and binding['original_lifecycle'][key] == candidate['lifecycle'][key]
                and binding['linked_authority'][key] == candidate['linked_authority'][key],
                'completed simulator evidence differs from its build')
        require(all(observed[key] == binding['application'][key] for observed in
                    (candidate['executable'], proof['executable'], authority['executable'], lifecycle['application'])),
                'simulator build, lifecycle or authority executable differs')


def lifecycle_file(item, root):
    parts = PurePosixPath(item['path']).parts
    require(parts.count('ios-lifecycle-output') == 1, 'unexpected lifecycle evidence location')
    relative = PurePosixPath(*parts[parts.index('ios-lifecycle-output') + 1:])
    require(relative.parts and '..' not in relative.parts, 'unsafe lifecycle evidence location')
    path = root.joinpath(*relative.parts)
    require(path.is_file() and path.resolve().is_relative_to(root.resolve()) and not path.is_symlink()
            and ios.digest(path) == item['sha256'] and path.stat().st_size == item['size'],
            'lifecycle evidence hash mismatch')
    return path


def validate_original_lifecycle(candidate, original, inputs, root):
    """An unchanged original simulator can qualify through a later completed run."""
    require(candidate.get('scope') == 'ios_retained_simulator_profile_background_reopen'
            and candidate.get('passed') is True and candidate.get('cleanup_complete') is True
            and candidate.get('cleanup_errors') == []
            and candidate.get('application_recompiled') is False
            and candidate.get('application_resigned') is False
            and candidate.get('simulator_keychain_fixture') is False
            and candidate.get('original_build_verdict_unchanged') is True,
            'original simulator lifecycle or cleanup did not pass unchanged')
    require(candidate.get('inputs') == {key: inputs[key] for key in
            ('run_id', 'artifact_id', 'artifact_sha256', 'gchat_commit', 'gcoms_commit', 'build_number')},
            'lifecycle original source/artifact binding differs')
    require(json.loads(lifecycle_file(candidate['original_build'], root).read_text()) == original
            and candidate.get('original_build_passed') is original.get('passed'),
            'lifecycle original verdict or build differs')
    journey.test_result(json.loads(lifecycle_file(candidate['test_summary'], root).read_text()))
    lifecycle_file(candidate['xctest_log'], root)
    for key in ('application', 'original_application'):
        require(all(candidate[key][field] == original['simulator_executable'][field]
                    for field in ('sha256', 'size')), 'lifecycle executable differs from original')
    authority = json.loads(lifecycle_file(candidate['linked_verification'], root).read_text())
    original_authority = json.loads(lifecycle_file(candidate['original_linked_authority'], root).read_text())
    for proof in (authority, original_authority):
        require(proof.get('scope') == 'ios_xcode_linked_simulator_authority' and proof.get('passed') is True
                and proof.get('device_qualified') is False and all(proof['executable'][field]
                    == original['simulator_executable'][field] for field in ('sha256', 'size')),
                'original simulator authority mismatch')
    for key in ('host_entitlements', 'linked_simulator_authority'):
        require(authority[key] == original_authority[key], 'simulator authority changed')
    native = json.loads(lifecycle_file(candidate['native_tests'], root).read_text())
    failed = json.loads(lifecycle_file(candidate['original_native_tests'], root).read_text())
    require(native.get('scope') == 'ios_app_hosted_native_push_validation_and_keychain_tests'
            and native.get('passed') is True and native.get('sources_unchanged') is True
            and native.get('cleanup_complete') is True and native.get('owned_device_removed') is True
            and native.get('cleanup_errors') == [] and failed.get('passed') is False
            and failed.get('sources_unchanged') is True and failed.get('cleanup_complete') is True,
            'native test recovery or cleanup did not pass')
    expected = {'Sources/PushNotifications.swift', 'Sources/UnlockVault.swift',
                'Tests/PluginTests/PushValidationTests.swift', 'Tests/PluginTests/UnlockVaultTests.swift'}
    require(set(native['sources']) == set(failed['sources']) == expected,
            'native test source inventory differs')
    require(all(native['sources'][name][field] == failed['sources'][name][field]
                for name in expected for field in ('sha256', 'size')), 'native source changed')
    summary = json.loads(lifecycle_file(native['test_summary'], root).read_text())
    require(summary.get('result') == 'Passed' and summary.get('passedTests') == 3
            and summary.get('failedTests') == 0 and summary.get('skippedTests') == 0
            and native.get('tests', {}).get('passed') == 3
            and native['tests'].get('failed') == 0 and native['tests'].get('skipped') == 0,
            'all three native tests must pass without exclusions')
    lifecycle_file(native['log'], root)
    return authority, native


def validate_original_simulator_upload(report, original):
    require(report.get('simulator_relinked_from_same_source') is False,
            'original simulator must not be relinked')
    binding = report['simulator_binding']
    archive = ios.verify_reference(binding['archive'])
    require(ios.digest(archive) == report['inputs']['simulator']['artifact_sha256'],
            'lifecycle archive binding differs')
    candidate_path = ios.verify_reference(binding['report'])
    candidate = json.loads(candidate_path.read_text())
    authority, _ = validate_original_lifecycle(candidate, original, report['inputs'], candidate_path.parent)
    require(binding['report'] == report['simulator'], 'upload lifecycle receipt differs')
    checked = json.loads(ios.verify_reference(binding['verification']).read_text())
    require(checked.get('passed') is True and checked.get('scope') == 'ios_xcode_linked_simulator_authority'
            and checked.get('device_qualified') is False, 'fresh native verification did not pass')
    for key in ('host_entitlements', 'linked_simulator_authority'):
        require(checked[key] == authority[key], 'fresh simulator authority differs')
    for field in ('sha256', 'size'):
        require(checked['executable'][field] == original['simulator_executable'][field]
                == binding['application'][field], 'fresh simulator executable differs')
    ios.verify_reference(binding['application'])


def verify_original_simulator(spec, original, inputs, destination, gchat):
    run = journey.api('actions/runs/' + str(spec['run_id']))
    artifact = journey.api('actions/artifacts/' + str(spec['artifact_id']))
    simulator_run_binding(run, artifact, spec)
    require(run['conclusion'] == 'success', 'retained lifecycle workflow must succeed')
    ios.write_json(destination / 'simulator-run.json', run)
    ios.write_json(destination / 'simulator-artifact.json', artifact)
    archive = destination / 'simulator-artifact.zip'
    with archive.open('wb') as stream:
        subprocess.run(['gh', 'api', 'repos/IggyGG/gchat/actions/artifacts/' + str(spec['artifact_id']) + '/zip'],
                       stdout=stream, check=True, timeout=600)
    require(ios.digest(archive) == spec['artifact_sha256'], 'lifecycle artifact digest mismatch')
    retained = destination / 'simulator-original'
    with zipfile.ZipFile(archive) as zipped:
        ios.inspect_zip(zipped)
        zipped.extractall(retained)
    root = retained / 'ios-lifecycle-output'
    nested = root / 'original-artifact.zip'
    require(ios.digest(nested) == inputs['artifact_sha256'], 'lifecycle original archive differs')
    with zipfile.ZipFile(nested) as zipped:
        ios.inspect_zip(zipped)
        zipped.extractall(root / 'original')
    receipt = root / 'report.json'
    candidate = json.loads(receipt.read_text())
    authority, native = validate_original_lifecycle(candidate, original, inputs, root)
    for name, item in native['sources'].items():
        path = gchat / 'apps/client/src-tauri/mobile-platform/ios' / name
        require(ios.digest(path) == item['sha256'] and path.stat().st_size == item['size'],
                'native tests differ from original application source')
    for field, path in (('harness', Path(__file__).with_name('ios-lifecycle.py')),
                         ('swift_test', Path(__file__).parent / 'fixtures/ios-lifecycle/LifecycleTests.swift')):
        require(ios.digest(path) == candidate[field]['sha256'], 'lifecycle controller source differs')
    app_zip = journey.relocated(original['simulator_archive'], destination / 'original/ios-output')
    app_root = destination / 'simulator-application'
    ios.run(['ditto', '-x', '-k', app_zip, app_root])
    apps = list(app_root.glob('*.app'))
    require(len(apps) == 1, 'original simulator archive must contain one app')
    helper_spec = importlib.util.spec_from_file_location('simulator_builder', Path(__file__).with_name('ios-simulator-build.py'))
    helper = importlib.util.module_from_spec(helper_spec)
    helper_spec.loader.exec_module(helper)
    verified = helper.verify_app(apps[0], destination / 'simulator-verification')
    checked = json.loads(Path(verified['path']).read_text())
    for key in ('host_entitlements', 'linked_simulator_authority'):
        require(checked[key] == authority[key], 'original simulator verification differs')
    return {'report': ios.reference(receipt), 'archive': ios.reference(archive),
            'application': checked['executable'], 'verification': verified}


def verify_simulator(spec, original, destination):
    run = journey.api('actions/runs/' + str(spec['run_id']))
    artifact = journey.api('actions/artifacts/' + str(spec['artifact_id']))
    simulator_run_binding(run, artifact, spec)
    ios.write_json(destination / 'simulator-run.json', run)
    ios.write_json(destination / 'simulator-artifact.json', artifact)
    archive = destination / 'simulator-artifact.zip'
    with archive.open('wb') as stream:
        subprocess.run(['gh', 'api', 'repos/IggyGG/gchat/actions/artifacts/' + str(spec['artifact_id']) + '/zip'],
                       stdout=stream, check=True, timeout=600)
    require(ios.digest(archive) == spec['artifact_sha256'], 'simulator artifact digest mismatch')
    retained = destination / 'simulator-original'
    with zipfile.ZipFile(archive) as zipped:
        ios.inspect_zip(zipped)
        zipped.extractall(retained)
    root = retained / 'ios-simulator-output'
    receipt = root / 'report.json'
    candidate = json.loads(receipt.read_text())
    validate_simulator(candidate, original, spec, allow_incomplete=True)
    verify_retained_inputs(root / 'paired/provenance', candidate['dependency_inputs'])
    require(set(candidate['source_archives']) == {'gchat', 'gcoms'}, 'missing simulator source archives')
    for name, item in candidate['source_archives'].items():
        require(ios.digest(simulator_file(item, root)) == original['dependency_inputs']['source_archive_sha256'][name],
                'simulator source archive mismatch')
    for key in ('generated_config', 'simulator_xcconfig', 'simulator_entitlements', 'effective_settings',
                'feature_graph_file', 'generated_project', 'xcode_invocations'):
        simulator_file(candidate[key], root)
    lifecycle_path = simulator_file(candidate['lifecycle'], root)
    lifecycle = json.loads(lifecycle_path.read_text())
    require(lifecycle.get('scope') == 'ios_installed_simulator_profile_background_reopen'
            and lifecycle.get('cleanup_complete') is True
            and lifecycle.get('cleanup_errors') == [] and lifecycle.get('application_recompiled') is False
            and lifecycle.get('application_resigned') is False, 'original simulator cleanup did not pass')
    simulator_file(lifecycle['xctest_log'], root)
    authority_path = simulator_file(candidate['linked_authority'], root)
    authority = json.loads(authority_path.read_text())
    require(authority.get('scope') == 'ios_xcode_linked_simulator_authority'
            and authority.get('passed') is True and authority.get('device_qualified') is False,
            'simulator linked-authority verification did not pass')
    app_zip = simulator_file(candidate['simulator_archive'], root)
    with zipfile.ZipFile(app_zip) as zipped:
        ios.inspect_zip(zipped)
    app_root = destination / 'simulator-application'
    ios.run(['ditto', '-x', '-k', app_zip, app_root])
    apps = list(app_root.glob('*.app'))
    require(len(apps) == 1, 'simulator archive must contain one app')
    app = apps[0]
    info = plistlib.loads((app / 'Info.plist').read_bytes())
    require(info.get('CFBundleVersion') == original['build_number'], 'simulator version changed')
    helper_spec = importlib.util.spec_from_file_location('simulator_builder', Path(__file__).with_name('ios-simulator-build.py'))
    helper = importlib.util.module_from_spec(helper_spec)
    helper_spec.loader.exec_module(helper)
    verified = helper.verify_app(app, destination / 'simulator-verification')
    checked = json.loads(Path(verified['path']).read_text())
    for observed in (candidate['executable'], lifecycle['application'], authority['executable']):
        for key in ('sha256', 'size'):
            require(observed[key] == checked['executable'][key], 'simulator build, lifecycle or authority executable differs')
    require(checked['linked_simulator_authority'] == authority['linked_simulator_authority']
            and checked['host_entitlements'] == authority['host_entitlements'], 'simulator authority changed')
    # Simulator01 built the correct app, but the native form tap did not submit.
    # Reuse those exact bytes with the corrected driver; never relabel that
    # failed receipt or recompile the application to rerun its UI journey.
    fresh_lifecycle = journey.run_application(app, destination / 'simulator-lifecycle')
    return {'report': ios.reference(receipt), 'archive': ios.reference(archive),
            'application': checked['executable'], 'verification': verified,
            'original_build_passed': candidate['passed'], 'lifecycle_rechecked': True,
            'original_lifecycle': ios.reference(lifecycle_path), 'lifecycle': fresh_lifecycle,
            'linked_authority': ios.reference(authority_path)}


def verify(args):
    require(platform.system() == 'Darwin' and platform.machine() == 'arm64', 'use an Apple Silicon Mac worker')
    spec = json.loads(args.spec.read_text())
    for name in ('gchat', 'gcoms'):
        ios.policy.source_commit(spec[name + '_commit'])
    ios.build_number(spec['build_number'])
    require(type(spec['run_id']) is int and type(spec['artifact_id']) is int
            and re.fullmatch('[0-9a-f]{64}', spec['artifact_sha256']), 'invalid original artifact identifiers')
    destination = args.output.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    checkouts = {'gchat': args.gchat.resolve(), 'gcoms': args.gcoms.resolve()}
    before = {name: source_identity(path) for name, path in checkouts.items()}
    report = {'schema': 1, 'scope': 'ios_retained_pair_simulator_and_signed_ipa', 'passed': False,
              'application_recompiled': False, 'device_resigned': False,
              'original_build_verdict_unchanged': True, 'inputs': spec,
              'bundle': ios.BUNDLE, 'team': ios.TEAM, 'app_store_id': ios.APP_STORE_ID,
              'physical_device_qualified': False, 'messaging_qualified': False, 'push_qualified': False,
              'harness': ios.reference(Path(__file__)), 'sources': before, 'build_number': spec['build_number']}
    try:
        run = journey.api('actions/runs/' + str(spec['run_id']))
        artifact = journey.api('actions/artifacts/' + str(spec['artifact_id']))
        journey.run_binding(run, artifact, spec)
        ios.write_json(destination / 'original-run.json', run)
        ios.write_json(destination / 'original-artifact.json', artifact)
        archive = destination / 'original-artifact.zip'
        with archive.open('wb') as stream:
            subprocess.run(['gh', 'api', 'repos/IggyGG/gchat/actions/artifacts/' + str(spec['artifact_id']) + '/zip'],
                           stdout=stream, check=True, timeout=600)
        require(ios.digest(archive) == spec['artifact_sha256'], 'downloaded artifact digest mismatch')
        report['original_archive'] = ios.reference(archive)
        retained = destination / 'original'
        with zipfile.ZipFile(archive) as zipped:
            ios.inspect_zip(zipped)
            zipped.extractall(retained)
        root = retained / 'ios-output'
        original_path = root / 'build.json'
        original = json.loads(original_path.read_text())
        cleanup_path = journey.relocated(original['signing_cleanup'], root)
        cleanup = json.loads(cleanup_path.read_text())
        provenance_path = root / 'paired/provenance/inputs.json'
        provenance = json.loads(provenance_path.read_text())
        validate_inputs(original, cleanup, provenance, spec)
        require(original['sources'] == before, 'selected source checkouts differ from original artifacts')
        verify_retained_inputs(root / 'paired/provenance', provenance)
        for name, checkout in checkouts.items():
            archived = subprocess.check_output(['git', 'archive', '--format=tar', spec[name + '_commit']], cwd=checkout)
            require(hashlib.sha256(archived).hexdigest() == provenance['source_archive_sha256'][name],
                    'original source archive mismatch')
        harness = (args.gchat / 'scripts/ios-build.py').read_bytes()
        require(hashlib.sha256(harness).hexdigest() == original['harness']['sha256'], 'original build harness mismatch')
        pin = ios.signing_pin()
        publication = args.gchat / 'release/publication.json'
        require(ios.digest(publication) == original['publication']['sha256'], 'original publisher policy mismatch')
        publisher = ios.publisher_policy(publication, pin)
        require(publisher == original['publisher'], 'original publisher identity differs')
        retained_publication = destination / 'publication.json'
        shutil.copyfile(publication, retained_publication)
        report.update(original_build=ios.reference(original_path), original_build_passed=original.get('passed'),
                      original_error=original.get('error'), original_final_derived_recheck_completed=original.get('passed') is True,
                      dependency_inputs=provenance, publication=ios.reference(retained_publication), publisher=publisher,
                      signing_cleanup=ios.reference(cleanup_path))
        report['xcode'] = ios.output(['xcodebuild', '-version'])
        require(report['xcode'].splitlines()[0] == 'Xcode 26.2', 'use the original pinned Xcode')
        ipa = journey.relocated(original['application']['ipa'], root)
        application = ios.verify_ipa(ipa, destination / 'ipa-verification', pin, spec['build_number'])
        for key in ('executable', 'entitlements', 'profile', 'build_number', 'bundle', 'architectures', 'minimum_ios'):
            require(application[key] == original['application'][key], 'IPA verification differs from original: ' + key)
        report['application'] = application
        # The original simulator failed after the device artifact completed.
        # Keep it unchanged and consume the separate normal-Xcode simulator
        # build on the same source pair. Post-link entitlement injection is not
        # a substitute for iOS simulator link authority.
        journey.relocated(original['simulator_archive'], root)
        if spec['simulator'].get('mode') == 'retained_original':
            binding = verify_original_simulator(spec['simulator'], original, spec, destination, args.gchat)
            report.update(simulator_binding=binding, simulator=binding['report'],
                          simulator_relinked_from_same_source=False, simulator_reused_from_original=True)
            validate_original_simulator_upload(report, original)
        else:
            require('mode' not in spec['simulator'], 'unknown simulator verification mode')
            binding = verify_simulator(spec['simulator'], original, destination)
            report.update(simulator_binding=binding, simulator=binding['lifecycle'],
                          simulator_relinked_from_same_source=True)
        require(ios.digest(ipa) == original['application']['ipa']['sha256'], 'original IPA changed')
        require(ios.digest(archive) == spec['artifact_sha256'], 'original artifact archive changed')
        require(ios.digest(original_path) == report['original_build']['sha256'], 'original build receipt changed')
        report['passed'] = True
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        report['sources_unchanged'] = all(source_identity(path) == before[name] for name, path in checkouts.items())
        report['passed'] = report['passed'] and report['sources_unchanged']
        ios.write_json(destination / 'build.json', report)
    require(report['passed'], 'retained iOS verification did not complete unchanged')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('spec', 'gchat', 'gcoms', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    verify(parser.parse_args())
