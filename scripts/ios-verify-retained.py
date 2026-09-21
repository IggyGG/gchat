#!/usr/bin/env python3
"""Recheck a retained signed IPA and an owned simulator copy without rebuilding.

Original failed receipts and application archives remain immutable. This check
cannot qualify physical devices, messaging, push or App Store approval.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
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
        app_zip = journey.relocated(original['simulator_archive'], root)
        with zipfile.ZipFile(app_zip) as zipped:
            ios.inspect_zip(zipped)
        app_root = destination / 'application'
        ios.run(['ditto', '-x', '-k', app_zip, app_root])
        apps = list(app_root.glob('*.app'))
        require(len(apps) == 1, 'retained simulator archive must contain one app')
        app = apps[0]
        info = plistlib.loads((app / 'Info.plist').read_bytes())
        require(info.get('CFBundleIdentifier') == ios.BUNDLE and info.get('CFBundleVersion') == spec['build_number'],
                'retained simulator identity mismatch')
        name = info.get('CFBundleExecutable', '')
        require(name and Path(name).name == name, 'invalid simulator executable name')
        expected = original['simulator_executable']
        require(ios.digest(app / name) == expected['sha256'] and (app / name).stat().st_size == expected['size'],
                'retained simulator executable differs')
        app, binding = journey.application_for_journey(app, destination, keychain_fixture=True)
        report.update(simulator_binding=binding)
        derived_archive = destination / 'simulator-app.zip'
        ios.run(['ditto', '-c', '-k', '--keepParent', app, derived_archive])
        report['simulator_archive'] = ios.reference(derived_archive)
        report['simulator'] = ios.simulator_smoke(app, destination / 'simulator-smoke')
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
