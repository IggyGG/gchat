"""Simulator link authority must not become restricted host/device authority."""
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('ios_simulator', SCRIPTS / 'ios-simulator-build.py')
sim = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sim)


def macho(entitlements=None, include_der=True):
    value = entitlements if entitlements is not None else {
        'application-identifier': sim.ios.BUNDLE, 'keychain-access-groups': [sim.ios.BUNDLE], 'get-task-allow': True}
    rows = [(b'__entitlements', plistlib.dumps(value))]
    if include_der:
        rows.append((b'__ents_der', b'fixture DER section'))
    size = 72 + 80 * len(rows)
    offset = 32 + size
    total = offset + sum(len(raw) for _, raw in rows)
    header = struct.pack('<8I', 0xfeedfacf, 0x100000c, 0, 2, 1, size, 0, 0)
    segment = struct.pack('<II16s4Q4I', 0x19, size, b'__TEXT', 0, total, 0, total, 5, 5, len(rows), 0)
    sections, payload = b'', b''
    for name, raw in rows:
        sections += struct.pack('<16s16sQQ8I', name, b'__TEXT', offset, len(raw), offset, 0, 0, 0, 0, 0, 0, 0)
        payload += raw
        offset += len(raw)
    return header + segment + sections + payload


class SimulatorBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binary = self.root / 'GChat'
        self.binary.write_bytes(macho())

    def test_linked_identity_and_both_sections_are_bound(self):
        result = sim.ios.simulator_linked_entitlements(self.binary)
        self.assertEqual(result['entitlements']['keychain-access-groups'], [sim.ios.BUNDLE])
        self.assertEqual(set(result['sections']), {'__entitlements', '__ents_der'})
        self.assertTrue(all(len(row['sha256']) == 64 for row in result['sections'].values()))

    def test_unlinked_original_cannot_be_fixed_by_signature_entitlements(self):
        self.binary.write_bytes(struct.pack('<8I', 0xfeedfacf, 0x100000c, 0, 2, 0, 0, 0, 0))
        with self.assertRaisesRegex(ValueError, 'must be linked'):
            sim.ios.simulator_linked_entitlements(self.binary)
        self.binary.write_bytes(macho(include_der=False))
        with self.assertRaisesRegex(ValueError, 'must be linked'):
            sim.ios.simulator_linked_entitlements(self.binary)

    def test_malformed_offset_or_truncated_command_fails_closed(self):
        valid = macho()
        bad = bytearray(valid)
        struct.pack_into('<I', bad, 32 + 72 + 48, len(valid) + 100)
        for data in (b'short', valid[:100], bad):
            self.binary.write_bytes(data)
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                sim.ios.simulator_linked_entitlements(self.binary)

    def test_foreign_or_broad_keychain_identity_rejected(self):
        for change in ({'keychain-access-groups': ['other.app']}, {'keychain-access-groups': [sim.ios.BUNDLE, '*']},
                       {'application-identifier': 'other.app'}, {'com.apple.developer.team-identifier': sim.ios.TEAM}):
            value = {'application-identifier': sim.ios.BUNDLE, 'keychain-access-groups': [sim.ios.BUNDLE],
                     'get-task-allow': True} | change
            self.binary.write_bytes(macho(value))
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'unexpected linked'):
                sim.ios.simulator_linked_entitlements(self.binary)

    def test_effective_xcode_settings_require_ad_hoc_simulator_and_no_team(self):
        _, entitlements = sim.configure_simulator(self.root / 'settings')
        value = {'PRODUCT_BUNDLE_IDENTIFIER': sim.ios.BUNDLE, 'CODE_SIGNING_ALLOWED': 'YES',
                 'CODE_SIGN_IDENTITY': '-', 'CODE_SIGN_STYLE': 'Manual', 'CODE_SIGN_ENTITLEMENTS': str(entitlements),
                 'SDKROOT': '/Applications/Xcode_26.2.app/Contents/Developer/Platforms/iPhoneSimulator.platform/SDK'}
        sim.verify_settings([{'buildSettings': value}], entitlements)
        for key, replacement in (('CODE_SIGNING_ALLOWED', 'NO'), ('CODE_SIGN_IDENTITY', 'Apple Distribution'),
                ('DEVELOPMENT_TEAM', sim.ios.TEAM), ('PROVISIONING_PROFILE_SPECIFIER', 'profile'),
                ('CODE_SIGN_ENTITLEMENTS', '/other.plist'), ('SDKROOT', '/iPhoneOS.sdk')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                sim.verify_settings([{'buildSettings': value | {key: replacement}}], entitlements)

    def test_wrapper_removes_account_access_and_preserves_build_arguments(self):
        config, _ = sim.configure_simulator(self.root / 'settings')
        folder = self.root / 'wrapper'
        sim.simulator_environment(folder, {'PATH': os.environ['PATH'], 'DEVELOPER_DIR': '/fixture/Xcode'},
                                  config, executable=sys.executable)
        program = 'import json,os,sys;print(json.dumps([sys.argv[1:],os.environ["XCODE_XCCONFIG_FILE"]]))'
        args = ['-c', program, '-sdk', 'iphonesimulator', '-allowProvisioningUpdates', 'archive']
        result = subprocess.run([sys.executable, str(folder / 'invoke.py'), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [['-sdk', 'iphonesimulator', 'archive'], str(config)])
        for extra in (['-exportArchive'], ['-sdk', 'iphoneos'], ['-authenticationKeyID', 'forbidden'],
                      ['CODE_SIGNING_ALLOWED=NO'], ['CODE_SIGN_IDENTITY=Apple Distribution'], ['DEVELOPMENT_TEAM=TEAM']):
            failed = subprocess.run([sys.executable, str(folder / 'invoke.py'), '-c', program, *extra],
                                    capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)

    def test_host_signature_cannot_carry_linked_ios_authority(self):
        app = self.root / 'GChat.app'
        app.mkdir()
        (app / 'Info.plist').write_bytes(plistlib.dumps({'CFBundleIdentifier': sim.ios.BUNDLE,
            'CFBundleSupportedPlatforms': ['iPhoneSimulator'], 'CFBundleExecutable': 'GChat'}))
        (app / 'GChat').write_bytes(macho())
        for index, host in enumerate(({'keychain-access-groups': [sim.ios.BUNDLE]}, {'get-task-allow': True})):
            with patch.object(sim.ios, 'output', side_effect=['arm64', 'platform IOSSIMULATOR']), \
                 patch.object(sim.ios, 'run'), patch.object(sim.subprocess, 'check_output', return_value=plistlib.dumps(host)), \
                 self.subTest(host=host), self.assertRaisesRegex(ValueError, 'host simulator signature'):
                sim.verify_app(app, self.root / str(index))

    def test_xcode_empty_host_entitlements_preserve_linked_simulator_authority(self):
        app = self.root / 'GChat.app'
        app.mkdir()
        (app / 'Info.plist').write_bytes(plistlib.dumps({'CFBundleIdentifier': sim.ios.BUNDLE,
            'CFBundleSupportedPlatforms': ['iPhoneSimulator'], 'CFBundleExecutable': 'GChat'}))
        (app / 'GChat').write_bytes(macho())
        before = (app / 'GChat').read_bytes()
        with patch.object(sim.ios, 'output', side_effect=['arm64', 'platform IOSSIMULATOR', 'Signature=adhoc']), \
             patch.object(sim.ios, 'run'), patch.object(sim.subprocess, 'check_output', return_value=b''):
            receipt = sim.verify_app(app, self.root / 'verified')
        report = json.loads(Path(receipt['path']).read_text())
        self.assertIs(report['passed'], True)
        self.assertEqual(report['host_entitlements'], {})
        self.assertEqual(report['linked_simulator_authority']['entitlements']['keychain-access-groups'], [sim.ios.BUNDLE])
        self.assertEqual((app / 'GChat').read_bytes(), before)


class CombinedReleaseSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.generated = self.root / 'chat/apps/client/src-tauri/gen/apple'
        self.generated.mkdir(parents=True)
        self.project = self.generated / 'gchat-desktop.xcodeproj'
        self.config = self.root / 'ios-config.json'
        self.config.write_text(json.dumps({'identifier': sim.ios.BUNDLE, 'bundle': {'iOS': {
            'developmentTeam': sim.ios.TEAM, 'minimumSystemVersion': '15.0', 'bundleVersion': '1.0.10'}}}))
        self.original = self.config.read_bytes()
        self.destination = self.root / 'output'
        self.environment = {'PATH': os.environ['PATH'], 'DEVELOPER_DIR': '/Applications/Xcode_26.2.app/Contents/Developer',
                            'APPLE_DEVELOPMENT_TEAM': sim.ios.TEAM}
        self.commands = []

    def settings(self, command, **kwargs):
        self.assertEqual(command[command.index('-sdk') + 1], 'iphonesimulator')
        self.assertNotIn('APPLE_DEVELOPMENT_TEAM', kwargs['env'])
        return json.dumps([{'buildSettings': {'PRODUCT_BUNDLE_IDENTIFIER': sim.ios.BUNDLE,
            'CODE_SIGNING_ALLOWED': 'YES', 'CODE_SIGN_IDENTITY': '-', 'CODE_SIGN_STYLE': 'Manual',
            'CODE_SIGN_ENTITLEMENTS': str(self.destination / 'simulator-xcode/link-settings/Simulator.entitlements'),
            'SDKROOT': '/Applications/Xcode_26.2.app/Contents/Developer/Platforms/iPhoneSimulator.platform/SDK'}}])

    def native_command(self, command, **kwargs):
        self.commands.append(command)
        if command[0] == 'npm':
            self.assertIn('--archive-only', command)
            self.assertNotIn('--no-sign', command)
            self.assertNotIn('APPLE_DEVELOPMENT_TEAM', kwargs['env'])
            config = Path(command[command.index('--config') + 1])
            self.assertNotIn('developmentTeam', json.loads(config.read_text())['bundle']['iOS'])
            app = self.generated / 'build/GChat.xcarchive/Products/Applications/GChat.app'
            app.mkdir(parents=True)
            (app / 'Info.plist').write_bytes(plistlib.dumps({'CFBundleIdentifier': sim.ios.BUNDLE,
                'CFBundleExecutable': 'GChat', 'CFBundleVersion': '1.0.10', 'CFBundleSupportedPlatforms': ['iPhoneSimulator']}))
            (app / 'GChat').write_bytes(macho())
            (self.destination / 'simulator-xcode/link-driver/invocations.jsonl').write_text('{}\n')
        elif command[0] == 'ditto':
            Path(command[-1]).write_bytes(b'fixture archive')
        else:
            self.fail('unexpected build command')

    def verify_app(self, app, destination):
        self.assertNotIn(self.generated, app.parents)
        self.assertEqual(sim.ios.simulator_linked_entitlements(app / 'GChat')['entitlements'], {
            'application-identifier': sim.ios.BUNDLE, 'keychain-access-groups': [sim.ios.BUNDLE], 'get-task-allow': True})
        destination.mkdir(parents=True)
        sim.ios.write_json(destination / 'report.json', {'passed': True, 'executable': sim.ios.reference(app / 'GChat')})
        return sim.ios.reference(destination / 'report.json')

    def test_full_builder_uses_existing_link_guard_and_keeps_device_authority_separate(self):
        report = {}
        with patch.object(sim.ios, 'simulator_tools', return_value=sim), \
                patch.object(sim.ios, 'output', side_effect=self.settings), \
                patch.object(sim.ios, 'run', side_effect=self.native_command), \
                patch.object(sim, 'verify_app', side_effect=self.verify_app) as verify, \
                patch.object(sim.ios, 'sign_simulator', side_effect=AssertionError('no post-link patching')):
            app = sim.ios.build_simulator(self.root / 'chat', self.generated, self.project, self.config,
                                         self.destination, self.environment, report)
        verify.assert_called_once()
        self.assertEqual(self.config.read_bytes(), self.original)
        self.assertEqual(self.environment['APPLE_DEVELOPMENT_TEAM'], sim.ios.TEAM)
        self.assertEqual(len(self.commands), 2)
        original = self.generated / 'build/GChat.xcarchive/Products/Applications/GChat.app/GChat'
        original.write_bytes(b'later device archive replacement')
        self.assertEqual(sim.ios.digest(app / 'GChat'), report['simulator_executable']['sha256'])
        self.assertNotIn('simulator_signing', report)
        self.assertIn('simulator_linked_authority', report)

    def test_invalid_effective_link_settings_stop_before_compilation(self):
        def unsigned(command, **kwargs):
            return self.settings(command, **kwargs).replace('"YES"', '"NO"')
        with patch.object(sim.ios, 'simulator_tools', return_value=sim), \
                patch.object(sim.ios, 'output', side_effect=unsigned), \
                patch.object(sim.ios, 'run') as execute, self.assertRaisesRegex(ValueError, 'exact simulator'):
            sim.ios.build_simulator(self.root / 'chat', self.generated, self.project, self.config,
                                   self.destination, self.environment, {})
        execute.assert_not_called()
        self.assertEqual(self.config.read_bytes(), self.original)


if __name__ == '__main__':
    unittest.main()
