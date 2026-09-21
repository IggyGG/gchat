#!/usr/bin/env python3
"""Verify and smoke-test an existing signed DMG without rebuilding or resigning it."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

from release_evidence import digest, file_reference, read_json, require, source_identity
from paired_sources import verify_native_ci_inputs, verify_retained_inputs

# Reuse bounded artifact extraction and exact paired-native verification.
import importlib.util
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('macos_package_recovery', ROOT / 'scripts/macos-package.py')
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


def validate_origin(run, artifact, args):
    require(run.get('id') == args.package_run_id and run.get('event') == 'workflow_dispatch' and
            run.get('path') == '.github/workflows/macos-package.yml' and
            run.get('repository', {}).get('full_name') == package.REPO and run.get('status') == 'completed',
            'retained package run identity differs')
    require(artifact.get('id') == args.artifact_id and artifact.get('name') == args.target + '-package' and
            artifact.get('expired') is False and artifact.get('digest') == 'sha256:' + args.artifact_sha256 and
            artifact.get('workflow_run', {}).get('id') == args.package_run_id and
            artifact.get('workflow_run', {}).get('head_sha') == run.get('head_sha'),
            'retained package artifact identity differs')


def retained_inputs(retained, args, run):
    retry = retained / 'retry-evidence'
    prepared = read_json(retry / 'prepared.json')
    failed = read_json(retry / 'packaging-helper.json')
    expected = {'gchat': args.gchat_commit, 'gcoms': args.gcoms_commit}
    repositories = {'gchat': args.gchat.resolve(), 'gcoms': args.gcoms.resolve()}
    sources = {name: source_identity(path) for name, path in repositories.items()}
    require({name: source['commit'] for name, source in sources.items()} == expected and
            prepared.get('sources') == sources and failed.get('sources') == sources,
            'retained package/application sources differ')
    require(prepared.get('prepared') is True and prepared.get('target') == args.target and
            prepared.get('controller') == failed.get('controller') and
            failed.get('controller', {}).get('commit') == run['head_sha'] and
            failed.get('scope') == 'controller_packaging_original_native_application',
            'retained packaging controller differs')
    # The original failure stays failed. Recovery does not invent missing checks.
    require(failed.get('passed') is False, 'this recovery is for the retained incomplete packaging attempt')
    require(package.reference(retry / 'original-native.zip') == prepared.get('original_archive'),
            'retained original native archive changed')
    native = package.verify_native(retry / 'original-native', args.target, expected, repositories)
    require(native == prepared.get('native'), 'original native evidence changed')
    provenance = retained / 'signed/provenance'
    inputs = read_json(provenance / 'inputs.json')
    require(inputs.get('sources') == sources and inputs.get('target') == package.TARGETS[args.target],
            'packaged dependency sources/target differ')
    native_binding = verify_native_ci_inputs(provenance / 'native-ci.json', inputs)
    verify_retained_inputs(provenance, inputs)
    require(native_binding == native['native_ci'], 'packaged dependencies differ from original native qualification')
    matches = list((retained / 'signed/build' / package.TARGETS[args.target] / 'release/bundle/dmg').glob('*.dmg'))
    require(len(matches) == 1 and matches[0].is_file() and not matches[0].is_symlink(),
            'retained package must contain exactly one real signed DMG')
    return sources, inputs, native_binding, matches[0], prepared


def run(args):
    require(platform.system() == 'Darwin', 'retained DMG verification requires native macOS')
    controller = package.verify_controller(ROOT, os.environ, 'macos-verify.yml')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {'schema': 1, 'scope': 'retained_signed_dmg_verification_and_application_smoke',
              'controller': controller, 'target': args.target, 'passed': False,
              'recompiled': False, 'resigned': False, 'native_tests_rerun': False,
              'original_packaging_passed': False,
              'original_post_build_source_recheck': 'not executed; original packaging failed before this check',
              'original_post_build_derived_input_recheck': 'not executed; retained provenance independently checked here',
              'original_native_executable_byte_comparison': 'unavailable; original optimized executable was not retained'}
    try:
        origin = package.gh_json(f'repos/{package.REPO}/actions/runs/{args.package_run_id}')
        artifact = package.gh_json(f'repos/{package.REPO}/actions/artifacts/{args.artifact_id}')
        validate_origin(origin, artifact, args)
        package.write_json(output / 'package-run.json', origin)
        package.write_json(output / 'package-artifact.json', artifact)
        archive = output / 'package.zip'
        with archive.open('wb') as stream:
            subprocess.run(['gh', 'api', f'repos/{package.REPO}/actions/artifacts/{args.artifact_id}/zip',
                            '--allow-escape-sequences'], stdout=stream, check=True)
        require(digest(archive) == args.artifact_sha256, 'downloaded package artifact digest differs')
        retained = output / 'original-package'
        package.extract_archive(archive, retained)
        sources, inputs, native, original_dmg, prepared = retained_inputs(retained, args, origin)
        report.update(sources=sources, original_artifact=package.reference(archive),
                      original_packaging=package.reference(retained / 'retry-evidence/packaging-helper.json'),
                      original_package_log=package.reference(retained / 'retry-evidence/package.log'),
                      original_native=prepared['native'], dependency_inputs_verified=True)
        publication_path = args.gchat.resolve() / 'release/publication.json'
        publication = read_json(publication_path)
        require(publication.get('signing_policy') == 'self-signed', 'recovery currently supports the configured self-signed policy')
        identity = publication['publisher_identities']['macos']
        signed = output / 'signed'
        signed.mkdir()
        shutil.copytree(retained / 'signed/provenance', signed / 'provenance')
        dmg = signed / original_dmg.name
        shutil.copyfile(original_dmg, dmg)
        wrapper = package.script('test-macos-bundle')
        require(wrapper.smoke.native_target() == args.target, 'retained DMG target differs from native host')
        verification = output / 'artifact-verification'
        verification.mkdir()
        signature_report = {'commands': []}
        commands = wrapper.Commands(verification, signature_report)
        signature_report['dmg'] = wrapper.verify_signature(commands, dmg, identity, 'dmg')
        installer = package.script('build-installer')
        with installer.application_from_dmg(original_dmg.parent.parent) as app:
            signature_report['application'] = wrapper.verify_signature(commands, app, identity, 'application')
            executable = wrapper.bundle_executable(app)
            executable_binding = {'name': executable.name, 'sha256': digest(executable), 'size': executable.stat().st_size}
        package.write_json(verification / 'report.json', signature_report)
        build = {'schema': 1, 'target': args.target,
                 'sources': {name: source['commit'] for name, source in sources.items()},
                 'publisher': identity, 'signing_policy': 'self-signed', 'public_ca_trust': False,
                 'apple_notarization': False, 'dependency_inputs': inputs, 'native_ci': native,
                 'files': [{'name': dmg.name, 'format': 'dmg', 'sha256': digest(dmg), 'signing_verified': True}],
                 'executables': [executable_binding],
                 'manifest_recovered_from_retained_artifact': True,
                 'recovery_controller': controller,
                 'original_package_archive_sha256': args.artifact_sha256,
                 'original_post_build_source_recheck_performed': False}
        package.write_json(signed / 'build.json', build)
        controller_archive = output / 'controller.tar'
        subprocess.run(['git', 'archive', '--format=tar', '--output', str(controller_archive), controller['commit']], cwd=ROOT, check=True)
        command = [sys.executable, str(ROOT / 'scripts/test-macos-bundle.py'), '--build-manifest', str(signed / 'build.json'),
                   '--native-receipt', str(signed / 'provenance/native-ci.json'), '--publication', str(publication_path),
                   '--output', str(signed / 'application-smoke'), '--temp-parent', '/private/tmp', '--timeout', '30']
        subprocess.run(command, check=True, timeout=900)
        evidence = retained / 'retry-evidence/original-native/evidence'
        candidate = read_json(evidence / 'candidate.json')
        source_archive = file_reference(evidence, candidate['sources']['gchat']['archive'])
        package.script('macos-build').verify_application_smoke(signed, build, source_archive, controller_archive)
        require(digest(dmg) == digest(original_dmg), 'DMG changed during verification')
        retained_inputs(retained, args, origin)
        require(package.verify_controller(ROOT, os.environ, 'macos-verify.yml') == controller, 'verification controller changed')
        report.update(passed=True, original_artifact_unchanged=True,
                      build=package.reference(signed / 'build.json'),
                      application_smoke=package.reference(signed / 'application-smoke/report.json'),
                      controller_archive=package.reference(controller_archive),
                      artifact_verification=package.reference(verification / 'report.json'))
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
    finally:
        package.write_json(output / 'report.json', report)
    print(json.dumps({'passed': report['passed'], 'report': str(output / 'report.json')}))
    return 0 if report['passed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gchat', type=Path, required=True)
    parser.add_argument('--gcoms', type=Path, required=True)
    parser.add_argument('--gchat-commit', required=True)
    parser.add_argument('--gcoms-commit', required=True)
    parser.add_argument('--target', choices=package.TARGETS, required=True)
    parser.add_argument('--package-run-id', type=int, required=True)
    parser.add_argument('--artifact-id', type=int, required=True)
    parser.add_argument('--artifact-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for value, length in ((args.gchat_commit, 40), (args.gcoms_commit, 40), (args.artifact_sha256, 64)):
        require(re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None, 'full immutable hashes required')
    require(args.package_run_id > 0 and args.artifact_id > 0, 'positive run/artifact IDs required')
    return run(args)


if __name__ == '__main__':
    sys.exit(main())
