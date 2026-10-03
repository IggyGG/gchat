#!/usr/bin/env python3
"""Qualify retained signed mobile apps through actual native UI on owned devices."""
import argparse
import json
import os
from pathlib import Path
import platform
import secrets
import shutil
import time
import traceback

from mobile_acceptance_inputs import (
    acquire, android_application, digest, ios_application, require, validate_inputs)
from mobile_installed_journey import MobileJourney
from release_coordinator import atomic_json
from release_network_canary import module, verify_journey
from release_pair import validate


def error_frames(error):
    # Static locations diagnose harness errors without exception messages,
    # native arguments, UI hierarchies or local profile paths.
    return [{'file': Path(frame.filename).name, 'function': frame.name, 'line': frame.lineno}
            for frame in traceback.extract_tb(error.__traceback__, limit=16)]


def unchanged(items, target):
    for item in items:
        if target == 'ios':
            if digest(item['binary']) != item['binary_sha256']:
                return False
        else:
            signed = json.loads((item['root'] / 'signing.json').read_text())
            bound = signed['bundle_apks']['artifacts']
            if any(digest(item['root'] / ref['relative_path']) != ref['sha256'] for ref in bound):
                return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    inputs = validate_inputs(json.loads(args.inputs.read_text()))
    manifest = validate(json.loads(args.manifest.read_text()))
    target = inputs['target']
    require(inputs['current']['sources'] == {key: value['commit'] for key, value in manifest['sources'].items()},
            'mobile acceptance does not bind the reserved pair')
    require(os.environ.get('GITHUB_ACTIONS') == 'true'
            and (platform.system(), platform.machine()) in (
                [('Linux', 'x86_64'), ('Linux', 'AMD64')] if target == 'android' else [('Darwin', 'arm64')]),
            'disposable native mobile worker required')
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    root.chmod(0o700)
    report = {'schema': 1, 'passed': False, 'platform': target, 'sources': manifest['sources'],
        'release_id': manifest['release_id'], 'application_rebuilt': False, 'application_resigned': False,
        'personal_profiles_accessed': False, 'physical_device_qualified': False, 'ui_driven': True,
        'invitation_removed': False, 'installation_cleanup': []}
    invitation = root / 'invitation.private'
    journey, ui, peer = None, None, None
    peer_sha = None
    desktop = module('test-native-upgrade')
    items = []
    setup_deadline = time.monotonic() + 600
    try:
        for name in ('current', 'baseline'):
            item = acquire(name, inputs[name], target, root, manifest if name == 'current' else None)
            if target == 'android':
                android_application(item, manifest['policy']['android_certificate_sha256'])
            else:
                ios_application(item, manifest['policy']['ios_certificate_sha256'], root / name)
            items.append(item)
        current, baseline = items
        require(current['binary_sha256'] != baseline['binary_sha256'],
                'mobile current and baseline executables are identical')
        report['artifacts'] = {name: {key: item[key] for key in (
            'archive_sha256', 'sources', 'binary_sha256', 'application_rebuilt', 'application_resigned')}
            for name, item in zip(('current', 'baseline'), items)}
        if target == 'android':
            peer = desktop.linux_acquire('peer-application', inputs['peer'], root)
        else:
            desktop.mac.INPUTS.clear()
            desktop.mac.MOUNTS.clear()
            desktop.mac.INPUTS.update(target=inputs['peer_target'], current=inputs['peer'])
            commands = desktop.mac.installer.Commands(root, {'commands': []})
            (root / 'peer-application').mkdir()
            peer = desktop.mac.acquire('current', root / 'peer-application', commands)
        peer_sha = digest(peer['binary'])
        code = os.environ.pop('GCHAT_NETWORK_INVITATION', '')
        require(0 < len(code.encode()) <= 180000, 'bounded private bootstrap invitation required')
        invitation.write_text(code)
        invitation.chmod(0o600)
        del code
        owned = root / 'owned-device'
        owned.mkdir(mode=0o700)
        passphrase = secrets.token_urlsafe(32)
        setup_deadline = time.monotonic() + 600
        deadline = lambda: journey.deadline if journey is not None else setup_deadline

        def run_android(serial):
            nonlocal journey, ui
            from mobile_android_ui import AndroidUI
            ui = AndroidUI(serial, owned, passphrase, deadline)
            try:
                journey = MobileJourney(current, baseline, peer, invitation, root, manifest)
                journey.run(ui)
            finally:
                if journey is not None:
                    journey.cleanup(ui)
                else:
                    report['installation_cleanup'].append(ui.cleanup())
                    ui = None

        if target == 'android':
            android = module('android-build')
            android.emulator(argparse.Namespace(output=owned, port=5554), installed_journey=run_android)
            driver = json.loads((owned / 'emulator-driver.json').read_text())
            require(driver.get('passed') is True and driver.get('process_stopped') is True,
                    'owned mobile emulator driver did not finish')
        else:
            from mobile_ios_ui import IOSUI
            ui = IOSUI(owned, passphrase, deadline)
            journey = MobileJourney(current, baseline, peer, invitation, root, manifest)
            try:
                journey.run(ui)
            finally:
                journey.cleanup(ui)
        require(unchanged(items, target) and digest(peer['binary']) == peer_sha,
                'retained installed application changed during acceptance')
        journey.report.update(inputs_unchanged=True, binary_unchanged=True)
        journey.rollback['binaries_unchanged'] = True
        verify_journey(journey.report, manifest)
        require(journey.rollback['passed'] is True, 'actual mobile upgrade/rollback did not pass')
        report['passed'] = True
    except Exception as error:
        # No raw native command, UI hierarchy, invitation or grant is uploaded.
        report['error'] = type(error).__name__
        report['error_frames'] = error_frames(error)
        report['stage'] = journey.stage if journey is not None else 'retained-inputs-or-device-setup'
        if target == 'ios' and hasattr(error, 'ios_setup_diagnostics'):
            report['runner_setup'] = error.ios_setup_diagnostics
            report['installation_cleanup'].append(error.owned_device_cleanup)
    finally:
        if target == 'android' and ui is not None:
            report['ui_observation'] = dict(ui.ui_observation)
        invitation.unlink(missing_ok=True)
        report['invitation_removed'] = not invitation.exists()
        if journey is not None:
            report['installation_cleanup'].append(journey.cleanup_report or {'passed': False})
            for name, value in (('rollback', journey.rollback), ('network', journey.report)):
                path = root / name
                path.mkdir(exist_ok=True)
                atomic_json(path / 'report.json', value)
        else:
            try:
                result = ui.cleanup() if ui is not None else None
            except Exception as error:
                result = {'passed': False, 'error': type(error).__name__}
            if result is not None:
                report['installation_cleanup'].append(result)
            elif not report['installation_cleanup']:
                report['installation_cleanup'].append({'passed': False})
        if target == 'ios':
            for work, mount in reversed(desktop.mac.MOUNTS):
                try:
                    result = desktop.mac.installer.cleanup_installation(
                        desktop.mac.installer.Commands(root, {'commands': []}),
                        work, mount, True, children_stopped=(
                            journey is None or journey.report.get('children_stopped') is True))
                    report['installation_cleanup'].append(result)
                except Exception as error:
                    report['installation_cleanup'].append({'passed': False, 'error': type(error).__name__})
        owned = root / 'owned-device'
        # Device deletion/process exit is verified before deleting the test
        # runner's private token, AVD state or simulator diagnostic attachments.
        if journey is not None and journey.cleanup_report and journey.cleanup_report.get('passed') is True:
            if target == 'ios' or (owned / 'emulator-driver.json').is_file() and json.loads(
                    (owned / 'emulator-driver.json').read_text()).get('process_stopped') is True:
                if owned.exists():
                    shutil.rmtree(owned)
        report['completed_at'] = int(time.time())
        report['passed'] = report['passed'] and report['invitation_removed'] and all(
            item.get('passed') is True for item in report['installation_cleanup'])
        if journey is not None and report['passed'] is not True:
            for name, value in (('rollback', journey.rollback), ('network', journey.report)):
                value['passed'] = False
                atomic_json(root / name / 'report.json', value)
        atomic_json(root / 'report.json', report)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
