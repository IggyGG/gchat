"""Release branches must not weaken the frozen signing-worker source boundary."""
import importlib.util
import json
import hashlib
import io
import tarfile
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))


def script(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


macos = script('macos-build')
dispatcher = script('dispatch-macos')
REF = 'refs/heads/release/gchat-0.1.3'


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True, stderr=subprocess.PIPE).strip()


class WorkerSourceTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repos = [self.root / name for name in ('gchat', 'gcoms')]
        self.commits = []
        for root in self.repos:
            root.mkdir()
            git(root, 'init', '-q')
            git(root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                'commit', '-qm', 'Initial', '--allow-empty')
            commit = git(root, 'rev-parse', 'HEAD')
            self.commits.append(commit)
            git(root, 'update-ref', 'refs/remotes/origin/release/gchat-0.1.3', commit)
        self.environment = {
            'GITHUB_SHA': self.commits[0], 'GITHUB_WORKFLOW_SHA': self.commits[0],
            'GITHUB_REF': REF,
            'GITHUB_WORKFLOW_REF': f'{macos.REPO}/.github/workflows/macos-release.yml@{REF}',
        }

    def verify(self, refs=(REF, REF)):
        macos.verify_checkouts(*self.repos, *self.commits, *refs, self.environment)

    def test_frozen_release_branch_does_not_need_main_membership(self):
        self.verify()

    def test_wrong_workflow_sha_or_ref_cannot_sign_release(self):
        for key, value in [('GITHUB_SHA', '0' * 40), ('GITHUB_WORKFLOW_SHA', '0' * 40),
                           ('GITHUB_REF', 'refs/heads/main'), ('GITHUB_WORKFLOW_REF',
                            f'{macos.REPO}/.github/workflows/macos-release.yml@refs/heads/main')]:
            with self.subTest(key=key), patch.dict(self.environment, {key: value}):
                with self.assertRaisesRegex(ValueError, 'workflow must run'):
                    self.verify()

    def test_gchat_release_ref_must_not_advance_after_dispatch(self):
        root = self.repos[0]
        git(root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
            'commit', '-qm', 'Later', '--allow-empty')
        git(root, 'update-ref', 'refs/remotes/origin/release/gchat-0.1.3', git(root, 'rev-parse', 'HEAD'))
        git(root, 'checkout', '-q', '--detach', self.commits[0])
        with self.assertRaisesRegex(ValueError, 'release ref moved'):
            self.verify()

    def test_gcoms_source_must_belong_to_selected_branch(self):
        root = self.repos[1]
        git(root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
            'commit', '-qm', 'Later', '--allow-empty')
        newer = git(root, 'rev-parse', 'HEAD')
        git(root, 'update-ref', 'refs/remotes/origin/release/gchat-0.1.3', newer)
        git(root, 'checkout', '-q', '--detach', self.commits[1])
        self.verify()  # A frozen ancestor is a valid branch member.
        old = self.commits[1]
        self.commits[1] = newer
        git(root, 'checkout', '-q', '--detach', newer)
        git(root, 'update-ref', 'refs/remotes/origin/release/gchat-0.1.3', old)
        with self.assertRaises(subprocess.CalledProcessError):
            self.verify()

    def test_annotated_version_tags_bind_exact_source(self):
        for root in self.repos:
            git(root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                'tag', '-am', 'Approved', 'v0.1.3')
        tag = 'refs/tags/v0.1.3'
        self.environment.update(GITHUB_REF=tag,
                                GITHUB_WORKFLOW_REF=f'{macos.REPO}/.github/workflows/macos-release.yml@{tag}')
        self.verify((tag, tag))
        root = self.repos[1]
        git(root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
            'commit', '-qm', 'Later', '--allow-empty')
        git(root, 'tag', '-f', 'v0.1.3')
        git(root, 'checkout', '-q', '--detach', self.commits[1])
        with self.assertRaisesRegex(ValueError, 'release ref moved'):
            self.verify((tag, tag))


class DispatchTest(unittest.TestCase):
    def test_rejects_unapproved_and_ambiguous_ref_names(self):
        for ref in ('agent/task', 'refs/heads/agent/task', 'HEAD', '0' * 40,
                    'release/gchat-..evil', 'release/gchat-test.lock', 'refs/tags/arbitrary'):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                macos.release_ref(ref)
        self.assertEqual(macos.release_ref('release/gchat-0.1.3'), REF)
        self.assertEqual(macos.release_ref('v0.1.3'), 'refs/tags/v0.1.3')
        self.assertEqual(macos.release_ref('main'), 'refs/heads/main')

    def test_dispatch_uses_selected_release_ref_and_paired_ref(self):
        commits = ('a' * 40, 'b' * 40)
        with patch.object(macos, 'remote_ref_commit', side_effect=commits), patch.object(macos, 'gh') as gh:
            macos.dispatch(*commits, REF, REF, 'request')
        args = gh.call_args.args
        self.assertEqual(args[args.index('--ref') + 1], 'release/gchat-0.1.3')
        self.assertIn('gchat_ref=' + REF, args)
        self.assertIn('gcoms_ref=' + REF, args)

    def test_single_target_dispatch_and_default_both_keep_exact_source_refs(self):
        for target in ('both', 'macos-x86_64', 'macos-aarch64'):
            with self.subTest(target=target), \
                 patch.object(macos, 'remote_ref_commit', side_effect=['a' * 40, 'b' * 40]), \
                 patch.object(macos, 'gh') as gh:
                macos.dispatch('a' * 40, 'b' * 40, REF, REF, 'request', target)
                self.assertIn('target=' + target, gh.call_args.args)
                self.assertIn('gchat_commit=' + 'a' * 40, gh.call_args.args)
        with patch.object(macos, 'gh') as gh, self.assertRaisesRegex(ValueError, 'select both'):
            macos.dispatch('a' * 40, 'b' * 40, REF, REF, 'request', 'arbitrary')
        gh.assert_not_called()

    def test_collector_requires_exact_requested_architectures(self):
        both = {'macos-x86_64', 'macos-aarch64'}
        for target in ('both', *sorted(both)):
            expected = both if target == 'both' else {target}
            macos.verify_collected_targets(expected, target)
            for wrong in (set(), {'macos-aarch64'} if target != 'macos-aarch64' else both, {'other'}):
                with self.subTest(target=target, wrong=wrong), self.assertRaisesRegex(ValueError, 'requested architectures'):
                    macos.verify_collected_targets(wrong, target)

    def test_workflow_selects_target_without_omitting_native_or_installation_gates(self):
        workflow = (SCRIPTS.parent / '.github/workflows/macos-release.yml').read_text()
        self.assertIn('default: both', workflow)
        self.assertIn('options: [both, macos-aarch64, macos-x86_64]', workflow)
        self.assertIn('fromJSON(inputs.target', workflow)
        self.assertIn("matrix.target == 'macos-aarch64' && 'macos-15' || 'macos-15-intel'", workflow)
        self.assertIn('--check native.gchat.${{ matrix.target }}', workflow)
        self.assertIn('--check native.gcoms.${{ matrix.target }}', workflow)
        self.assertIn('scripts/test-macos-bundle.py', workflow)
        self.assertIn('numpy==2.3.5', workflow)
        self.assertIn('include-hidden-files: true', workflow)
        self.assertIn('signed/build/*/release/bundle/dmg/*.dmg', workflow)

    def test_mirror_mismatch_stops_before_dispatch(self):
        with patch.object(macos, 'remote_ref_commit', return_value='c' * 40), patch.object(macos, 'gh') as gh:
            with self.assertRaisesRegex(ValueError, 'selected GChat ref'):
                macos.dispatch('a' * 40, 'b' * 40, REF, REF, 'request')
            gh.assert_not_called()

    def test_remote_paired_branch_rejects_unrelated_source(self):
        with patch.object(macos, 'remote_ref_commit', side_effect=['a' * 40, 'c' * 40]), \
             patch.object(macos, 'gh', return_value=json.dumps({'status': 'diverged'})):
            with self.assertRaisesRegex(ValueError, 'belong to'):
                macos.verify_remote_sources('a' * 40, 'b' * 40, REF, REF)

    def test_annotated_remote_tag_is_peeled_and_exact(self):
        tag = 'refs/tags/v0.1.3'
        responses = [
            json.dumps({'object': {'type': 'tag', 'sha': 'b' * 40}}),
            json.dumps({'object': {'type': 'commit', 'sha': 'a' * 40}}),
        ]
        with patch.object(macos, 'gh', side_effect=responses):
            self.assertEqual(macos.remote_ref_commit(macos.REPO, tag), 'a' * 40)
        with patch.object(macos, 'remote_ref_commit', side_effect=['a' * 40, 'c' * 40]):
            with self.assertRaisesRegex(ValueError, 'GComs tag'):
                macos.verify_remote_sources('a' * 40, 'b' * 40, tag, tag)

    def test_collected_run_must_bind_frozen_workflow(self):
        macos.verify_run({'head_sha': 'a' * 40, 'event': 'workflow_dispatch'}, 'a' * 40)
        for sha, event in [('b' * 40, 'workflow_dispatch'), ('a' * 40, 'push')]:
            with self.assertRaisesRegex(ValueError, 'different commit or event'):
                macos.verify_run({'head_sha': sha, 'event': event}, 'a' * 40)

    def test_forgejo_wrapper_preserves_detached_release_ref(self):
        with patch.dict(os.environ, {'GITHUB_REF': REF, 'GCOMS_REF': REF,
                                     'GCOMS_COMMIT': 'b' * 40, 'GCHAT_MACOS_TARGET': 'macos-x86_64'}, clear=True), \
             patch.object(dispatcher.subprocess, 'check_output', return_value='a' * 40 + '\n'), \
             patch.object(dispatcher.subprocess, 'run') as run:
            dispatcher.main()
        command = run.call_args.args[0]
        self.assertEqual(command[command.index('--gchat-ref') + 1], REF)
        self.assertEqual(command[command.index('--gcoms-ref') + 1], REF)
        self.assertEqual(command[command.index('--gchat-commit') + 1], 'a' * 40)
        self.assertEqual(command[command.index('--target') + 1], 'macos-x86_64')


class ApplicationCollectorTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.smoke = self.root / 'application-smoke'
        (self.smoke / 'service').mkdir(parents=True)
        (self.smoke / 'gui').mkdir()
        (self.root / 'provenance').mkdir()
        self.sources = {name: {'commit': letter * 40, 'tree': letter * 40}
                        for name, letter in (('gchat', 'a'), ('gcoms', 'b'))}
        certificate = b'pinned test certificate'
        sha = hashlib.sha256(certificate).hexdigest()
        self.publisher = {'name': 'Gh0st', 'certificate_fingerprint': sha.upper(), 'certificate_sha256': sha}
        publication = json.dumps({'publisher_identities': {'macos': self.publisher}}).encode()
        self.archived = {'scripts/test-macos-bundle.py': b'wrapper source',
                         'scripts/test-native-application.py': b'service source',
                         'release/publication.json': publication}
        self.archive = self.root / 'gchat.tar'
        with tarfile.open(self.archive, 'w') as archive:
            for name, body in self.archived.items():
                info = tarfile.TarInfo(name)
                info.size = len(body)
                archive.addfile(info, io.BytesIO(body))
        binary = self.ref('/private/tmp/install/GChat.app/Contents/MacOS/gchat-desktop', b'executable')
        self.build = {'target': 'macos-aarch64', 'dependency_inputs': {'sources': self.sources},
                      'native_ci': {'qualified': 'exact-input-binding'}, 'publisher': self.publisher,
                      'files': [{'name': 'GChat.dmg', 'format': 'dmg', 'sha256': hashlib.sha256(b'dmg').hexdigest()}],
                      'executables': [{'name': 'gchat-desktop', 'sha256': binary['sha256'], 'size': binary['size']}]}
        self.inputs = {'dmg': self.write('GChat.dmg', b'dmg'),
                       'build_manifest': self.write('build.json', json.dumps(self.build).encode()),
                       'native_receipt': self.write('provenance/native-ci.json', b'{}'),
                       'publication': self.ref('/worker/gchat/release/publication.json', publication)}
        application_inputs = {'binary': binary, 'build_manifest': self.inputs['build_manifest'],
                              'native_receipt': self.inputs['native_receipt'], 'sources': self.sources,
                              'native_ci': self.build['native_ci'], 'target': self.build['target']}
        self.service = {'schema': 1, 'scope': 'packaged_executable_offline_service_lifecycle',
                        'passed': True, 'inputs_unchanged': True, 'children_stopped': True,
                        'temporary_profile_removed': True, 'inputs': application_inputs,
                        'harness': self.ref('/worker/gchat/scripts/test-native-application.py', self.archived['scripts/test-native-application.py']),
                        'protocol_identity_sha256': 'd' * 64,
                        'steps': [{'phase': phase, 'passed': True, 'disconnected': True,
                                   'protocol_identity_sha256': 'd' * 64, 'wrong_passphrase_rejected': True,
                                   'cleanup': {'stopped': True, 'forced': False, 'exit_code': 0},
                                   'log': self.write('application-smoke/service/' + phase + '.log', b'service log')}
                                  for phase in ('create', 'reopen')]}
        self.report = {'schema': 1, 'scope': 'macos_dmg_private_copy_install_service_lifecycle',
                       'passed': True, 'inputs_unchanged': True, 'target': self.build['target'], 'sources': self.sources,
                       'cleanup': {'passed': True, 'detached': True, 'installation_removed': True, 'service_children_stopped': True},
                       'gui_tested': False, 'gatekeeper_tested': False, 'notarization_tested': False,
                       'system_applications_modified': False, 'production_network_requested': False,
                       'inputs': self.inputs, 'application_inputs': application_inputs,
                       'application': {'executable': binary},
                       'harness': self.ref('/worker/gchat/scripts/test-macos-bundle.py', self.archived['scripts/test-macos-bundle.py']),
                       'commands': []}
        self.gui = {'scope': 'native_window_and_ui_autostarted_ipc', 'passed': True,
                    'rendered_interaction_tested': False, 'network_journey_tested': False,
                    'profile_locked': True, 'protocol_locked': True, 'network_state': 'locked',
                    'pid': 100, 'temporary_profile': '/private/tmp/gui-profile',
                    'command': [binary['path'], '--home', '/private/tmp/gui-profile', '--no-network-bootstrap'],
                    'windows': [{'owner_pid': 100, 'width': 1100, 'height': 720, 'number': 5}],
                    'carrier_selection': 'official_application_default', 'protocol_selection_observed': True,
                    'service': {'pid': 101, 'command': binary['path'] + ' --interactive --gc2-carrier --no-network-bootstrap'},
                    'cleanup': {'passed': True, 'children_stopped': True, 'endpoints_removed': True,
                                'temporary_profile_removed': True, 'forced': False,
                                'gui': {'pid': 100, 'stopped': True, 'forced': False},
                                'services': [{'pid': 101, 'stopped': True, 'forced': False}]},
                    'log': self.write('application-smoke/gui/gui.log', b'GUI log')}
        self.report['gui_startup_passed'] = True
        for kind in ('dmg', 'application'):
            self.report[kind + '_signature'] = {'fingerprint': sha.upper(), 'sha256': sha,
                                               'certificate': self.write('application-smoke/' + kind + '-leaf-0', certificate)}
        for name in ('dmg-integrity', 'dmg-certificate', 'attach', 'copy',
                     'application-integrity', 'application-certificate', 'service', 'detach'):
            self.report['commands'].append({'name': name, 'exit_code': 0,
                                            **{stream: self.write('application-smoke/' + name + '.' + stream, b'command log')
                                               for stream in ('stdout', 'stderr')}})

    def ref(self, path, data):
        return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data)}

    def write(self, relative, data):
        path = self.root / relative
        path.write_bytes(data)
        return self.ref(path, data)

    def verify(self):
        self.report['service_receipt'] = self.write('application-smoke/service/report.json', json.dumps(self.service).encode())
        self.report['gui_startup'] = self.write('application-smoke/gui/report.json', json.dumps(self.gui).encode())
        self.write('application-smoke/report.json', json.dumps(self.report).encode())
        return macos.verify_application_smoke(self.root, self.build, self.archive)

    def test_complete_relocated_receipt_is_accepted_without_original_installation(self):
        self.assertTrue(self.verify()['passed'])

    def test_wrong_source_and_failed_cleanup_are_rejected(self):
        self.report['sources'] = {'other': {}}
        with self.assertRaisesRegex(ValueError, 'source binding'):
            self.verify()
        self.report['sources'] = self.sources
        self.report['cleanup']['detached'] = False
        with self.assertRaisesRegex(ValueError, 'cleanup is incomplete'):
            self.verify()

    def test_changed_dmg_or_native_receipt_is_rejected(self):
        for path, original in [('GChat.dmg', b'dmg'), ('provenance/native-ci.json', b'{}')]:
            with self.subTest(path=path):
                (self.root / path).write_bytes(b'changed artifact')
                with self.assertRaisesRegex(ValueError, 'digest/size'):
                    self.verify()
                (self.root / path).write_bytes(original)

    def test_different_installed_binary_is_rejected(self):
        self.report['application_inputs']['binary']['sha256'] = 'e' * 64
        with self.assertRaisesRegex(ValueError, 'installed executable'):
            self.verify()

    def test_unbound_harness_and_publisher_are_rejected(self):
        original = self.report['harness']['sha256']
        self.report['harness']['sha256'] = 'e' * 64
        with self.assertRaisesRegex(ValueError, 'frozen source archive'):
            self.verify()
        self.report['harness']['sha256'] = original
        self.report['dmg_signature']['fingerprint'] = 'e' * 64
        with self.assertRaisesRegex(ValueError, 'publisher pin'):
            self.verify()

    def test_service_failure_or_forced_shutdown_is_rejected(self):
        self.service['passed'] = False
        with self.assertRaisesRegex(ValueError, 'lifecycle failed'):
            self.verify()
        self.service['passed'] = True
        self.service['steps'][1]['cleanup']['forced'] = True
        with self.assertRaisesRegex(ValueError, 'shut down cleanly'):
            self.verify()

    def test_modified_retained_log_is_rejected(self):
        (self.smoke / 'service/reopen.log').write_bytes(b'replaced log')
        with self.assertRaisesRegex(ValueError, 'digest/size'):
            self.verify()

    def test_missing_copy_command_is_rejected(self):
        self.report['commands'] = [command for command in self.report['commands'] if command['name'] != 'copy']
        with self.assertRaisesRegex(ValueError, 'omits required'):
            self.verify()

    def test_missing_gui_window_or_graphical_cleanup_is_rejected(self):
        self.gui['windows'] = []
        with self.assertRaisesRegex(ValueError, 'no owned native window'):
            self.verify()
        self.gui['windows'] = [{'owner_pid': 100, 'width': 1100, 'height': 720}]
        self.gui['cleanup']['endpoints_removed'] = False
        with self.assertRaisesRegex(ValueError, 'graphical startup cleanup'):
            self.verify()

    def test_gui_using_explicit_carrier_does_not_qualify_desktop_default(self):
        self.gui['command'].append('--gc2-carrier')
        with self.assertRaisesRegex(ValueError, 'copied application default'):
            self.verify()

    def test_missing_daemon_carrier_proof_is_rejected(self):
        original = self.gui['service']['command']
        for replacement in ('', '--gc2-carrier-other'):
            self.gui['service']['command'] = original.replace('--gc2-carrier', replacement)
            with self.assertRaisesRegex(ValueError, 'default GC/2 daemon selection'):
                self.verify()
        self.gui['service']['command'] = original
        self.gui['protocol_selection_observed'] = False
        with self.assertRaisesRegex(ValueError, 'default GC/2 daemon selection'):
            self.verify()


if __name__ == '__main__':
    unittest.main()
