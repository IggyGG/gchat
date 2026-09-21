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
import zipfile
from unittest.mock import patch, Mock

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('android_build', SCRIPTS / 'android-build.py')
android = importlib.util.module_from_spec(spec)
spec.loader.exec_module(android)
PIN = 'ab' * 32


class MobileLauncher(unittest.TestCase):
    def test_selects_windows_command_shim_without_dropping_arguments(self):
        with patch.object(android.os, 'name', 'nt'):
            self.assertEqual(android.tauri_command('android', 'init', '--ci'),
                             ['npm.cmd', 'run', 'tauri', '--', 'android', 'init', '--ci'])
        with patch.object(android.os, 'name', 'posix'):
            self.assertEqual(android.tauri_command('android', 'init', '--ci'),
                             ['npm', 'run', 'tauri', '--', 'android', 'init', '--ci'])

    def test_package_runner_survives_gradle_src_tauri_working_directory(self):
        # Exercise real npm's parent package lookup and lifecycle context without
        # compiling or invoking an Android SDK. This is the Gradle callback cwd.
        with tempfile.TemporaryDirectory() as scratch:
            app = Path(scratch) / 'client'
            native = app / 'src-tauri'
            native.mkdir(parents=True)
            (app / 'package.json').write_text(json.dumps({
                'name': 'gchat-android-callback-fixture', 'private': True,
                'scripts': {'tauri': 'node runner.cjs'},
            }))
            (app / 'runner.cjs').write_text(
                'require("fs").writeFileSync("observed.json", JSON.stringify({'
                'cwd:process.cwd(),args:process.argv.slice(2),event:process.env.npm_lifecycle_event,'
                'manager:process.env.npm_execpath}));')
            args = ['android', 'android-studio-script', '--target', 'aarch64']
            subprocess.run(android.tauri_command(*args), cwd=native, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            observed = json.loads((app / 'observed.json').read_text())
            self.assertEqual(Path(observed['cwd']).resolve(), app.resolve())
            self.assertEqual(observed['args'], args)
            self.assertEqual(observed['event'], 'tauri')
            self.assertEqual(Path(observed['manager']).name, 'npm-cli.js')


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

    def test_package_manager_uid_requires_one_exact_user_zero_app(self):
        self.assertEqual(android.installed_package_uid('package:boo.gchat.app uid:10123\n'), 10123)
        for text in ('package:boo.gchat.app.debug uid:10123', 'package:boo.gchat.app uid:0',
                     'package:boo.gchat.app uid:1000', 'package:boo.gchat.app uid:110123',
                     'package:boo.gchat.app uid:10123\npackage:boo.gchat.app.debug uid:10124',
                     'appId=10123', 'userId=10123', ''):
            with self.subTest(text=text), self.assertRaises(ValueError):
                android.installed_package_uid(text)

    def test_listener_scan_filters_uid_and_connected_sockets(self):
        row = '0: 00000000:1234 00000000:0000 0A 0:0 0:0 0 10123 0 42\n'
        self.assertEqual(android.listener_rows(row, 10123), [{'local_address': '00000000:1234', 'inode': '42'}])
        self.assertEqual(android.listener_rows(row, 10124), [])
        self.assertEqual(android.listener_rows(row.replace(' 0A ', ' 01 '), 10123), [])


class ActivityDriver(unittest.TestCase):
    def test_resumed_activity_ignores_retained_background_task_records(self):
        home = ('  topResumedActivity=ActivityRecord{abc u0 com.google.android.apps.nexuslauncher/.NexusLauncher t2}\n'
                '  * Hist #1: ActivityRecord{def u0 boo.gchat.app/.MainActivity t3}\n')
        self.assertEqual(android.resumed_packages(home), ['com.google.android.apps.nexuslauncher'])
        app = (' mResumedActivity: ActivityRecord{def u0 boo.gchat.app/.MainActivity t3}\n'
               ' topResumedActivity=ActivityRecord{def u0 boo.gchat.app/.MainActivity t3}\n')
        self.assertEqual(android.resumed_packages(app), [android.PACKAGE])
        with self.assertRaisesRegex(ValueError, 'resumed'):
            android.resumed_packages('* Hist #1: ActivityRecord{def u0 boo.gchat.app/.MainActivity t3}')


class KeyboardDriver(unittest.TestCase):
    def test_visibility_requires_actual_ime_state(self):
        self.assertTrue(android.keyboard_shown('mRequestedShowExplicitly=false\n mInputShown=true\n'))
        self.assertFalse(android.keyboard_shown(' mInputShown=false\n'))
        self.assertTrue(android.keyboard_shown('mInputShown=false\nmInputShown=true'))
        with self.assertRaisesRegex(ValueError, 'visibility'):
            android.keyboard_shown('mInputShown=unknown')

    def test_waits_for_two_settled_visibility_samples(self):
        shell = Mock(side_effect=['mInputShown=true', 'mInputShown=false', 'mInputShown=true',
                                  'mInputShown=false', 'mInputShown=false'])
        with patch.object(android.time, 'sleep'):
            android.wait_keyboard(shell, False)
        self.assertEqual(shell.call_count, 5)
        shell.assert_called_with('dumpsys', 'input_method')

    def test_visibility_timeout_does_not_continue_to_click(self):
        shell = Mock(return_value='mInputShown=true')
        with patch.object(android.time, 'monotonic', side_effect=[0, 0, 11]), \
                patch.object(android.time, 'sleep'), self.assertRaisesRegex(ValueError, 'expected visibility'):
            android.wait_keyboard(shell, False)


class ArtifactReuse(unittest.TestCase):
    def test_relocated_original_receipt_keeps_hash_and_size_binding(self):
        with tempfile.TemporaryDirectory() as scratch:
            original = Path(scratch) / 'old.apk'
            original.write_bytes(b'signed original fixture')
            item = android.reference(original)
            relocated = Path(scratch) / 'new.apk'
            original.rename(relocated)
            self.assertEqual(android.verify_copy(relocated, item), relocated)
            with self.assertRaisesRegex(ValueError, 'changed'):
                android.verify_copy(relocated, {**item, 'size': item['size'] + 1})
            relocated.write_bytes(b'tampered original fixture')
            with self.assertRaisesRegex(ValueError, 'changed'):
                android.verify_copy(relocated, item)

    def test_original_failed_workflow_requires_exact_build_identity_and_artifact(self):
        args = argparse.Namespace(build_run=123, artifact_id=456, gchat_commit='a' * 40,
                                  gcoms_commit='b' * 40, artifact_sha256='c' * 64)
        original = dict(id=123, head_sha=args.gchat_commit, head_repository={'full_name': android.policy.REPO},
                        event='workflow_dispatch', status='completed', conclusion='failure',
                        path='.github/workflows/android-release.yml', head_branch='release/gchat-mobile-0.1.4')
        artifact = dict(id=456, expired=False, name=f'android-{args.gchat_commit}-{args.gcoms_commit}',
                        digest='sha256:' + args.artifact_sha256)
        self.assertEqual(android.verify_original_artifact(args, original, [artifact]), artifact)
        for changed in ({'id': 124}, {'head_sha': 'd' * 40}, {'event': 'pull_request'}, {'status': 'in_progress'},
                        {'head_repository': {'full_name': 'another/repository'}},
                        {'path': '.github/workflows/other.yml'}, {'head_branch': 'unreviewed'}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                android.verify_original_artifact(args, {**original, **changed}, [artifact])
        for changed in ({'id': 457}, {'expired': True}, {'name': 'another-pair'}, {'digest': 'sha256:' + 'd' * 64}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                android.verify_original_artifact(args, original, [{**artifact, **changed}])
        with self.assertRaises(ValueError):
            android.verify_original_artifact(args, original, [artifact, artifact])

    def test_archive_rejects_traversal_absolute_paths_and_symlinks(self):
        for name, mode in (('../escape', 0), ('/absolute', 0), ('directory\\escape', 0),
                           ('C:escape', 0), ('link', 0o120777)):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as scratch:
                root = Path(scratch)
                archive = root / 'input.zip'
                with zipfile.ZipFile(archive, 'w') as bundle:
                    member = zipfile.ZipInfo(name)
                    member.external_attr = mode << 16
                    bundle.writestr(member, b'fixture')
                with self.assertRaisesRegex(ValueError, 'unsafe'):
                    android.extract_artifact(archive, root / 'original')
                self.assertFalse((root / 'escape').exists())

    def test_extract_preserves_original_failed_report_bytes(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            archive = root / 'input.zip'
            raw = b'{"passed":false,"error":"original AVD failure"}\n'
            with zipfile.ZipFile(archive, 'w') as bundle:
                bundle.writestr('emulator-driver.json', raw)
            android.extract_artifact(archive, root / 'original')
            self.assertEqual((root / 'original/emulator-driver.json').read_bytes(), raw)
            with self.assertRaises(FileExistsError):
                android.extract_artifact(archive, root / 'original')


class EmulatorDriver(unittest.TestCase):
    def test_avd_tools_share_explicit_private_directory(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            inherited = dict(ANDROID_SDK_HOME='/stale/legacy', ANDROID_AVD_HOME='/stale/avd',
                             ANDROID_EMULATOR_HOME='/stale/emulator', KEEP='yes')
            env, avds = android.emulator_environment(root, inherited)
            self.assertEqual(env['ANDROID_AVD_HOME'], str(root / 'android-user/avd'))
            self.assertEqual(env['ANDROID_USER_HOME'], env['ANDROID_EMULATOR_HOME'])
            self.assertEqual(Path(env['ANDROID_USER_HOME']) / 'avd', avds)
            self.assertNotIn('ANDROID_SDK_HOME', env)
            self.assertEqual(inherited['ANDROID_SDK_HOME'], '/stale/legacy')
            self.assertEqual(env['KEEP'], 'yes')

    def test_missing_registration_fails_before_emulator_and_retains_cleanup(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            with patch.object(android, 'sdk', return_value=root / 'sdk'), \
                    patch.object(android.subprocess, 'run'), patch.object(android.subprocess, 'Popen') as popen:
                with self.assertRaisesRegex(ValueError, 'requested AVD directory'):
                    android.emulator(argparse.Namespace(output=root))
                popen.assert_not_called()
            report = json.loads((root / 'emulator-driver.json').read_text())
            self.assertFalse(report['passed'])
            self.assertFalse(report['started'])
            self.assertTrue(report['process_stopped'])

    def test_smoke_failure_stops_owned_emulator_even_if_adb_kill_stalls(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            process = Mock()
            process.poll.return_value = None
            def kill():
                process.poll.return_value = -9
            process.kill.side_effect = kill
            create_env = []
            def execute(command, **kwargs):
                if 'create' in command:
                    env = kwargs['env']
                    create_env.append(env)
                    avd = Path(command[command.index('--path') + 1])
                    avd.mkdir()
                    (avd / 'config.ini').write_text('fixture')
                    (Path(env['ANDROID_AVD_HOME']) / 'gchat-release-fixture.ini').write_text('fixture')
                elif command[-2:] == ['emu', 'kill']:
                    raise subprocess.TimeoutExpired(command, 30)
                return subprocess.CompletedProcess(command, 0, stdout='1')
            with patch.object(android, 'sdk', return_value=root / 'sdk'), \
                    patch.object(android.subprocess, 'run', side_effect=execute), \
                    patch.object(android.subprocess, 'Popen', return_value=process) as popen, \
                    patch.object(android, 'smoke', side_effect=ValueError('injected app failure')):
                with self.assertRaisesRegex(ValueError, 'injected app failure'):
                    android.emulator(argparse.Namespace(output=root))
            self.assertEqual(popen.call_args.kwargs['env'], create_env[0])
            process.kill.assert_called_once()
            report = json.loads((root / 'emulator-driver.json').read_text())
            self.assertTrue(report['started'])
            self.assertTrue(report['process_stopped'])
            self.assertFalse(report['passed'])
            self.assertIn('injected app failure', report['error'])


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
