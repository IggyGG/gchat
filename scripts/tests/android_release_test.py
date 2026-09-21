"""Pure Android release boundaries; no emulator, credentials or builds needed."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('android_build', SCRIPTS / 'android-build.py')
android = importlib.util.module_from_spec(spec)
spec.loader.exec_module(android)
PIN = 'ab' * 32


class ArtifactGuards(unittest.TestCase):
    def test_feature_graph_allows_ipc_types_but_not_hosting(self):
        graph = 'gcoms v0.1.0|files,ipc,network-client\ngcoms-node v0.1.0|client-persist\ngcoms-runtime v0.1.0|network-client'
        self.assertIn('ipc', android.feature_graph(graph)['gcoms'])
        for bad in (graph.replace('files,', 'embedded,files,'), graph.replace('files,', 'launch,files,'),
                    graph.replace('client-persist', 'client-persist,relay-host'), graph.replace(',network-client', '')):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                android.feature_graph(bad)

    def test_stale_hash_and_size_fail_before_consumer(self):
        with tempfile.TemporaryDirectory() as scratch:
            path = Path(scratch) / 'fixture.apk'
            path.write_bytes(b'original APK fixture')
            item = android.reference(path)
            self.assertEqual(android.verify_reference(item), path.resolve())
            with self.assertRaises(ValueError):
                android.verify_reference({**item, 'size': item['size'] + 1})
            path.write_bytes(b'modified APK fixture')
            with self.assertRaises(ValueError):
                android.verify_reference(item)

    def test_signer_is_single_exact_pin_and_v2(self):
        valid = 'Signer #1 certificate SHA-256 digest: ' + PIN + '\nVerified using v2 scheme (APK Signature Scheme v2): true'
        with patch.object(android, 'output', return_value=valid):
            self.assertEqual(android.verify_signature(Path('app.apk'), Path('/sdk'), PIN), PIN)
        for bad in (valid.replace(PIN, 'cd' * 32), valid.replace(': true', ': false'),
                    valid + '\nSigner #2 certificate SHA-256 digest: ' + PIN):
            with self.subTest(bad=bad), patch.object(android, 'output', return_value=bad), self.assertRaises(ValueError):
                android.verify_signature(Path('app.apk'), Path('/sdk'), PIN)

    def test_smoke_rejects_changed_build_before_adb(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            build = root / 'build.json'
            build.write_text('{"passed":true}')
            signing = {'passed': True, 'private_keystore_removed': True, 'build': android.reference(build)}
            (root / 'signing.json').write_text(json.dumps(signing))
            build.write_text('{"passed":false}')
            with patch.object(android, 'sdk') as sdk, self.assertRaisesRegex(ValueError, 'changed'):
                android.smoke(argparse.Namespace(output=root, serial='emulator-5554'))
            sdk.assert_not_called()

    def test_alignment_checks_all_load_segments(self):
        data = bytearray(176)
        data[:6] = b'\x7fELF\x02\x01'
        struct.pack_into('<Q', data, 32, 64)
        struct.pack_into('<HH', data, 54, 56, 2)
        for offset, align in ((64, 16384), (120, 65536)):
            struct.pack_into('<I', data, offset, 1)
            struct.pack_into('<Q', data, offset + 48, align)
        self.assertEqual(android.verify_elf_alignment(data), [16384, 65536])
        struct.pack_into('<Q', data, 168, 4096)
        with self.assertRaisesRegex(ValueError, 'alignment'):
            android.verify_elf_alignment(data)


class EmulatorCleanup(unittest.TestCase):
    def test_uninstalls_after_every_owned_rule_even_if_first_rule_fails(self):
        calls = []
        def shell(*args, **kwargs):
            calls.append(args)
            if args[0] == 'iptables':
                raise RuntimeError('injected cleanup failure')
            return ''
        with patch.object(android, 'run') as run:
            result = android.cleanup_emulator(shell, ['adb', '-s', 'emulator-5554'], True, 10123,
                                              ['iptables', 'ip6tables'])
        self.assertFalse(result['passed'])
        self.assertEqual(len(result['errors']), 1)
        self.assertTrue(any(x[0] == 'ip6tables' for x in calls))
        self.assertIn(('am', 'force-stop', android.PACKAGE), calls)
        self.assertIn(('rm', '-f', '/sdcard/gchat-fixture-ui.xml'), calls)
        run.assert_called_once_with(['adb', '-s', 'emulator-5554', 'uninstall', android.PACKAGE], timeout=60)

    def test_success_verifies_uninstall_and_cleans_dump(self):
        calls = []
        def shell(*args, **kwargs):
            calls.append((args, kwargs))
            return ''
        with patch.object(android, 'run'):
            result = android.cleanup_emulator(shell, ['adb'], True, 10123, ['iptables', 'ip6tables'])
        self.assertTrue(result['passed'])
        self.assertIn((('pm', 'path', android.PACKAGE), {'absent_ok': True}), calls)

    def test_failed_uninstall_cannot_pass_cleanup(self):
        with patch.object(android, 'run', side_effect=RuntimeError('uninstall failed')):
            result = android.cleanup_emulator(lambda *a, **k: '', ['adb'], True, 10123, [])
        self.assertFalse(result['passed'])

    def test_listener_scan_filters_uid_and_connected_sockets(self):
        row = '0: 00000000:1234 00000000:0000 0A 0:0 0:0 0 10123 0 42\n'
        self.assertEqual(android.listener_rows(row, 10123), [{'local_address': '00000000:1234', 'inode': '42'}])
        self.assertEqual(android.listener_rows(row, 10124), [])
        self.assertEqual(android.listener_rows(row.replace(' 0A ', ' 01 '), 10123), [])


class FrozenSources(unittest.TestCase):
    def test_wrong_workflow_identity_refused_without_git(self):
        args = argparse.Namespace(gchat=Path('/unused/chat'), gcoms=Path('/unused/coms'),
                                  gchat_ref='main', gcoms_ref='main', gchat_commit='a' * 40, gcoms_commit='b' * 40)
        with patch.dict(os.environ, {}, clear=True), patch.object(android, 'source_identity') as identity:
            with self.assertRaisesRegex(ValueError, 'workflow/source/ref'):
                android.verify_checkouts(args)
            identity.assert_not_called()

    def test_real_committed_source_and_moved_branch(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            repos = [root / 'gchat', root / 'gcoms']
            commits = []
            def git(repo, *args):
                return subprocess.check_output(['git', *args], cwd=repo, text=True, stderr=subprocess.PIPE).strip()
            for repo in repos:
                repo.mkdir()
                git(repo, 'init', '-q')
                git(repo, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture', '--allow-empty')
                commits.append(git(repo, 'rev-parse', 'HEAD'))
                git(repo, 'update-ref', 'refs/remotes/origin/main', commits[-1])
            args = argparse.Namespace(gchat=repos[0], gcoms=repos[1], gchat_ref='main', gcoms_ref='main',
                                      gchat_commit=commits[0], gcoms_commit=commits[1])
            env = {'GITHUB_SHA': commits[0], 'GITHUB_WORKFLOW_SHA': commits[0], 'GITHUB_REF': 'refs/heads/main',
                   'GITHUB_WORKFLOW_REF': 'IggyGG/gchat/.github/workflows/android-release.yml@refs/heads/main'}
            with patch.dict(os.environ, env):
                android.verify_checkouts(args)
                git(repos[0], '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'new', '--allow-empty')
                git(repos[0], 'update-ref', 'refs/remotes/origin/main', git(repos[0], 'rev-parse', 'HEAD'))
                git(repos[0], 'checkout', '-q', '--detach', commits[0])
                with self.assertRaisesRegex(ValueError, 'ref moved'):
                    android.verify_checkouts(args)


if __name__ == '__main__':
    unittest.main()
