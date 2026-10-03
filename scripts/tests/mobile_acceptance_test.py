import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mobile_acceptance_inputs as inputs
from mobile_android_ui import delivery_row
from mobile_ios_ui import Bridge
import release_acceptance as acceptance
import mobile_android_ui as android_ui
from release_acceptance_test import fixture
from release_network_canary import module


def mobile_fixture(target='android'):
    manifest, specs, report, rollback, network = fixture()
    specs.update(target=target, peer_target='linux-x86_64' if target == 'android' else 'macos-aarch64',
                 peer=copy.deepcopy(specs['current']))
    report.update(platform=target, application_resigned=False, ui_driven=True,
                  physical_device_qualified=False, installation_cleanup=[{'passed': True}])
    for phase in rollback['phases']:
        phase['encrypted_cache_sha256'] = '9' * 64
    return manifest, specs, report, rollback, network


class MobileAcceptanceTests(unittest.TestCase):
    def owned_android_ui(self, root, *, sdk_setup=False, qemu=True, avd=True, installed=False):
        def command(argv, **kwargs):
            args = tuple(argv[3:])
            result, code = '', 0
            if args == ('shell', 'getprop', 'ro.kernel.qemu'): result = '1' if qemu else '0'
            elif args == ('emu', 'avd', 'name'): result = 'gchat-release-fixture-5554\nOK' if avd else 'another-owned-avd\nOK'
            elif args[:3] == ('shell', 'pm', 'path'):
                present = installed if args[3] == android_ui.android.PACKAGE else sdk_setup
                result, code = ('package:/fixture.apk', 0) if present else ('', 1)
            elif args[:3] == ('shell', 'pm', 'disable-user'): result = 'disabled-user'
            elif args[:2] == ('shell', 'settings') and 'get' in args: result = '1'
            elif args == ('shell', 'locksettings', 'get-disabled'): result = 'true'
            elif args == ('shell', 'getprop', 'ro.product.cpu.abi'): result = 'x86_64'
            elif args == ('shell', 'getprop', 'ro.build.version.sdk'): result = '35'
            return SimpleNamespace(returncode=code, stdout=result.encode(), stderr=b'')
        with patch.object(android_ui.android, 'sdk', return_value=root), \
             patch.object(android_ui.android, 'root_emulator') as rooted, \
             patch.object(android_ui.subprocess, 'run', side_effect=command) as adb:
            ui = android_ui.AndroidUI('emulator-5554', root, 'fixture-private-value', lambda: time.monotonic()+60)
        return ui, rooted, adb

    def test_mobile_android_ui_runs_shared_disposable_setup_with_absent_optional_package(self):
        for installed in (False, True):
            with self.subTest(sdk_setup=installed), tempfile.TemporaryDirectory() as temporary:
                ui, rooted, adb = self.owned_android_ui(Path(temporary), sdk_setup=installed)
                self.assertFalse(ui.installed)
                rooted.assert_called_once()
                calls = [call.args[0][3:] for call in adb.call_args_list]
                self.assertIn(['shell', 'pm', 'path', 'com.google.android.googlesdksetup'], calls)
                self.assertIn(['shell', 'locksettings', 'get-disabled'], calls)
                self.assertEqual(any('disable-user' in argv for argv in calls), installed)

    def test_mobile_setup_still_refuses_physical_other_or_preinstalled_device(self):
        for options in ({'qemu': False}, {'avd': False}, {'installed': True}):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as temporary, self.assertRaises(ValueError):
                self.owned_android_ui(Path(temporary), **options)

    def test_mobile_failure_locations_exclude_exception_messages_and_private_paths(self):
        driver = module('test-mobile-upgrade')
        try:
            raise TypeError('private-test-invitation /private/profile/path')
        except TypeError as error:
            frames = driver.error_frames(error)
        self.assertTrue(frames)
        self.assertEqual(set(frames[0]), {'file','function','line'})
        self.assertEqual(frames[0]['file'], Path(__file__).name)
        encoded = json.dumps(frames)
        self.assertNotIn('private-test-invitation', encoded)
        self.assertNotIn('/private/profile/path', encoded)

    def test_mobile_inputs_require_distinct_releases_and_matching_native_peer(self):
        for target in ('android', 'ios'):
            _, specs, *_ = mobile_fixture(target)
            self.assertEqual(inputs.validate_inputs(specs), specs)
            for field in ('run', 'artifact', 'archive', 'sources'):
                changed = copy.deepcopy(specs)
                changed['baseline'][field] = changed['current'][field]
                with self.subTest(target=target, field=field), self.assertRaises(ValueError):
                    inputs.validate_inputs(changed)
            for field, value in (('peer_target', 'windows-x86_64'), ('target', 'linux-x86_64')):
                changed = copy.deepcopy(specs)
                changed[field] = value
                with self.assertRaises(ValueError):
                    inputs.validate_inputs(changed)
            changed = copy.deepcopy(specs)
            changed['peer']['sources']['gcoms'] = '0' * 40
            with self.assertRaises(ValueError):
                inputs.validate_inputs(changed)

    def test_provider_identity_and_escaping_paths_fail_before_native_mutation(self):
        _, specs, *_ = mobile_fixture()
        for field, value in (('run', True), ('artifact', 0), ('conclusion', 'failure'),
                             ('controller', 'main'), ('archive', 'unverified'),
                             ('manifest', '../build.json'), ('manifest', '/build.json'),
                             ('manifest', r'C:\build.json'), ('manifest', 'report.json')):
            changed = copy.deepcopy(specs['current'])
            changed[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                inputs.validate_provider(changed)

    def test_real_mobile_ui_and_unchanged_ciphertext_are_required_for_receipt(self):
        for target in ('android', 'ios'):
            manifest, specs, report, rollback, network = mobile_fixture(target)
            acceptance.qualify_native(report, rollback, network, manifest, target, specs, 110)
            for field, bad in (('ui_driven', False), ('application_resigned', True),
                               ('physical_device_qualified', True)):
                changed = copy.deepcopy(report)
                changed[field] = bad
                with self.subTest(target=target, field=field), self.assertRaises(ValueError):
                    acceptance.qualify_native(changed, rollback, network, manifest, target, specs, 110)
            for bad in ('unverified', '8' * 64):
                changed = copy.deepcopy(rollback)
                changed['phases'][1]['encrypted_cache_sha256'] = bad
                with self.assertRaises(ValueError):
                    acceptance.qualify_native(report, changed, network, manifest, target, specs, 110)
            changed = copy.deepcopy(rollback)
            for phase in changed['phases']:
                phase['encrypted_cache_sha256'] = phase['cache_sha256']
            with self.assertRaises(ValueError):
                acceptance.qualify_native(report, changed, network, manifest, target, specs, 110)
            with self.assertRaises(ValueError):
                acceptance.qualify_native({**report,'installation_cleanup':[]},rollback,network,
                                          manifest,target,specs,110)

    def test_desktop_or_ordinary_picker_receipt_cannot_qualify_mobile(self):
        manifest, specs, report, rollback, network = mobile_fixture()
        for changed in ({**report, 'platform': 'linux-x86_64'},
                        {**report, 'ui_driven': None},
                        {**report, 'passed': False}):
            with self.assertRaises(ValueError):
                acceptance.qualify_native(changed, rollback, network, manifest, 'android', specs, 110)
        changed = copy.deepcopy(network)
        changed['file_check']['bytes'] = 262144
        with self.assertRaises(ValueError):
            acceptance.qualify_native(report, rollback, changed, manifest, 'android', specs, 110)

    def test_delivery_suffix_for_another_message_is_not_a_receipt(self):
        tree = ET.fromstring('<hierarchy><node><node><node text="mr-old"/>'
                            '<node text=" · delivered"/></node><node><node text="mr-new"/>'
                            '<node text=" · accepted locally"/></node></node></hierarchy>')
        self.assertFalse(delivery_row(tree, 'mr-new', {'mr-new', 'mr-old'}))
        self.assertTrue(delivery_row(tree, 'mr-old', {'mr-new', 'mr-old'}))
        tree.find('.//node[@text=" · delivered"]').set('text', '· delivered')
        self.assertTrue(delivery_row(tree, 'mr-old', {'mr-new', 'mr-old'}))
        missing = ET.fromstring('<hierarchy><node text=" · delivered"/></hierarchy>')
        self.assertFalse(delivery_row(missing, 'mr-new', {'mr-new'}))

    def test_xctest_bridge_requires_its_private_token_and_one_matching_result(self):
        bridge = Bridge()
        answers = []
        def post(path, value, token=None):
            headers = {'Content-Type': 'application/json',
                       'Authorization': 'Bearer ' + (bridge.token if token is None else token)}
            request = Request(bridge.url + path, data=json.dumps(value).encode(), headers=headers)
            with urlopen(request, timeout=5) as response:
                return json.load(response)
        worker = threading.Thread(target=lambda: answers.append(bridge.call('ready', timeout=5)))
        try:
            with self.assertRaises(HTTPError) as denied:
                post('/next', {'ready': True}, token='wrong')
            self.assertEqual(denied.exception.code, 403)
            denied.exception.close()
            worker.start()
            command = post('/next', {'ready': True})
            with self.assertRaises(HTTPError) as unknown:
                post('/result', {'id': '0' * 32, 'passed': True})
            self.assertEqual(unknown.exception.code, 400)
            unknown.exception.close()
            self.assertEqual(post('/result', {'id': command['id'], 'passed': True, 'value': True}),
                             {'accepted': True})
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive())
            self.assertEqual(answers, [True])
            with self.assertRaises(HTTPError) as duplicate:
                post('/result', {'id': command['id'], 'passed': True, 'value': True})
            self.assertEqual(duplicate.exception.code, 400)
            duplicate.exception.close()
            with self.assertRaisesRegex(ValueError, 'original XCTest command deadline'):
                bridge.call('ready', timeout=0.02)
        finally:
            worker.join(timeout=5) if worker.ident is not None else None
            bridge.close()

    def test_post_journey_artifact_check_observes_changed_bytes(self):
        driver = module('test-mobile-upgrade')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary = root / 'native'
            binary.write_bytes(b'original')
            item = {'binary': binary, 'binary_sha256': hashlib.sha256(b'original').hexdigest()}
            self.assertTrue(driver.unchanged([item], 'ios'))
            binary.write_bytes(b'changed')
            self.assertFalse(driver.unchanged([item], 'ios'))

    def test_mobile_dispatch_uses_its_own_workflow_and_retains_unknown_reply(self):
        manifest, specs, *_ = mobile_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            grant = root / 'grant.json'
            grant.write_text('{}')
            providers = {target: specs['current'] for target in ('android', 'linux-x86_64')}
            def api(path, **kwargs):
                return {'workflow_runs': []}
            with patch.object(acceptance, 'provider', side_effect=lambda state, manifest, target: providers[target]), \
                 patch.object(acceptance, 'baseline', return_value=specs['baseline']), \
                 patch.object(acceptance, 'gh', side_effect=api) as provider_api, \
                 patch.object(acceptance, 'ssh', return_value=b'{"invitation":"fixture-no-authority"}'), \
                 patch.object(acceptance.subprocess, 'run'):
                self.assertIsNone(acceptance.collect(root, {'grant_config': str(grant), 'qualification_commit': None},
                                                     manifest, 'android', root, '1' * 64))
                marker = json.loads((root / 'acceptance-intent.json').read_text())
                self.assertTrue(marker['dispatch_reserved'])
                self.assertEqual(marker['inputs']['peer_target'], 'linux-x86_64')
                self.assertNotIn('invitation', marker)
                calls = [call for call in provider_api.call_args_list if call.args[0].endswith('/dispatches')]
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0].args[0], 'actions/workflows/mobile-acceptance.yml/dispatches')
                self.assertIsNone(acceptance.collect(root, {'grant_config': str(grant), 'qualification_commit': None},
                                                     manifest, 'android', root, '1' * 64))
                self.assertEqual(sum(call.args[0].endswith('/dispatches')
                                     for call in provider_api.call_args_list), 1)

    def test_missing_current_native_peer_waits_without_issuing_a_grant(self):
        manifest, specs, *_ = mobile_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            grant = root / 'grant.json'
            grant.write_text('{}')
            with patch.object(acceptance, 'provider', side_effect=[specs['current'], None]), \
                 patch.object(acceptance, 'baseline', return_value=specs['baseline']), \
                 patch.object(acceptance, 'ssh') as ssh:
                self.assertIsNone(acceptance.collect(root, {'grant_config': str(grant)},
                                                     manifest, 'android', root, '1' * 64))
                ssh.assert_not_called()
                self.assertFalse((root / 'acceptance-intent.json').exists())


if __name__ == '__main__':
    unittest.main()
