"""Windows release evidence cannot substitute another source, binary or scope."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('windows_release', SCRIPTS / 'windows-build.py')
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)
REF = 'refs/heads/release/gchat-0.1.4'


def reference(data, path='frozen'):
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data)}


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True, stderr=subprocess.PIPE).strip()


class WindowsSourcesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repos, self.commits = [], []
        for name in ('gchat', 'gcoms'):
            root = Path(self.temp.name) / name
            root.mkdir()
            git(root, 'init', '-q')
            git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                'commit', '--allow-empty', '-qm', 'Frozen')
            commit = git(root, 'rev-parse', 'HEAD')
            git(root, 'update-ref', 'refs/remotes/origin/release/gchat-0.1.4', commit)
            self.repos.append(root)
            self.commits.append(commit)
        self.environment = {'GITHUB_SHA': self.commits[0], 'GITHUB_WORKFLOW_SHA': self.commits[0],
                            'GITHUB_REF': REF,
                            'GITHUB_WORKFLOW_REF': f'{worker.REPO}/.github/workflows/windows-release.yml@{REF}'}

    def verify(self):
        worker.verify_checkouts(*self.repos, *self.commits, REF, REF, self.environment)

    def test_frozen_release_without_main(self):
        self.verify()

    def test_ref_or_workflow_identity_mismatch_refused(self):
        for key, value in (('GITHUB_SHA', '0' * 40), ('GITHUB_WORKFLOW_SHA', '0' * 40),
                           ('GITHUB_REF', 'refs/heads/main'), ('GITHUB_WORKFLOW_REF',
                            f'{worker.REPO}/.github/workflows/macos-release.yml@{REF}')):
            with self.subTest(key=key), patch.dict(self.environment, {key: value}):
                with self.assertRaisesRegex(ValueError, 'workflow must run'):
                    self.verify()

    def test_advanced_application_ref_cannot_sign_old_checkout(self):
        root = self.repos[0]
        git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
            'commit', '--allow-empty', '-qm', 'Later')
        git(root, 'update-ref', 'refs/remotes/origin/release/gchat-0.1.4', git(root, 'rev-parse', 'HEAD'))
        git(root, 'checkout', '-q', '--detach', self.commits[0])
        with self.assertRaisesRegex(ValueError, 'ref moved'):
            self.verify()

    def test_protocol_commit_must_be_member_of_selected_branch(self):
        root = self.repos[1]
        git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
            'commit', '--allow-empty', '-qm', 'Later')
        self.commits[1] = git(root, 'rev-parse', 'HEAD')
        with self.assertRaises(subprocess.CalledProcessError):
            self.verify()

    def test_dispatch_uses_selected_release_and_exact_pair(self):
        with patch.object(worker.source, 'verify_remote_sources') as remote, patch.object(worker, 'gh') as gh:
            worker.dispatch(*self.commits, REF, REF, 'request')
        remote.assert_called_once_with(*self.commits, REF, REF)
        command = gh.call_args.args
        self.assertEqual(command[:3], ('workflow', 'run', 'windows-release.yml'))
        self.assertEqual(command[command.index('--ref') + 1], 'release/gchat-0.1.4')
        for name, value in zip(('gchat_commit', 'gcoms_commit'), self.commits):
            self.assertIn(name + '=' + value, command)

    def test_mirror_refusal_does_not_dispatch(self):
        with patch.object(worker.source, 'verify_remote_sources', side_effect=ValueError('moved')), \
             patch.object(worker, 'gh') as gh:
            with self.assertRaisesRegex(ValueError, 'moved'):
                worker.dispatch(*self.commits, REF, REF, 'request')
            gh.assert_not_called()


class WindowsEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.smoke = self.root / 'application-smoke'
        (self.smoke / 'service').mkdir(parents=True)
        (self.root / 'provenance').mkdir()
        (self.root / 'signing-evidence').mkdir()
        publication = json.loads((SCRIPTS.parent / 'release/publication.json').read_text())
        self.publisher = publication['publisher_identities']['windows']
        paths = ['scripts/test-windows-installer.py', 'scripts/test-native-application.py',
                 'scripts/verify-windows-signature.ps1', 'scripts/windows-signing.ps1', 'release/publication.json']
        self.archive = self.root / 'source.tar.gz'
        self.source_refs = {}
        with tarfile.open(self.archive, 'w:gz') as archive:
            for name in paths:
                data = (SCRIPTS.parent / name).read_bytes()
                member = tarfile.TarInfo(name)
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))
                self.source_refs[name] = reference(data, name)
        sources = {name: {'commit': letter * 40, 'tree': letter * 40}
                   for name, letter in (('gchat', 'a'), ('gcoms', 'b'))}
        self.installation = r'C:\private install\GChat'
        self.binary = reference(b'installed exe', self.installation + r'\gchat-desktop.exe')
        self.build = {'target': 'windows-x86_64', 'publisher': self.publisher,
                      'signing_policy': publication['signing_policy'], 'dependency_inputs': {'sources': sources},
                      'native_ci': {'identity': 'c' * 64}, 'executables': [
                          {'name': 'gchat-desktop.exe', **{key: self.binary[key] for key in ('size', 'sha256')}}],
                      'files': [{'name': 'GChat.exe', 'format': 'nsis', 'signing_verified': True}]}
        inputs = {}
        for name, path, data in [('installer', self.root / 'GChat.exe', b'installer'),
                                 ('build_manifest', self.root / 'build.json', b'bound build fixture'),
                                 ('native_receipt', self.root / 'provenance/native-ci.json', b'native receipt')]:
            path.write_bytes(data)
            inputs[name] = reference(data, path)
        inputs['publication'] = self.source_refs['release/publication.json']
        self.application = {'binary': self.binary, 'sources': sources, 'target': 'windows-x86_64',
                            'native_ci': self.build['native_ci'], 'build_manifest': inputs['build_manifest'],
                            'native_receipt': inputs['native_receipt']}
        self.service = {'schema': 1, 'scope': 'packaged_executable_offline_service_lifecycle',
                        'passed': True, 'inputs_unchanged': True, 'children_stopped': True,
                        'temporary_profile_removed': True, 'inputs': copy.deepcopy(self.application),
                        'harness': self.source_refs['scripts/test-native-application.py'],
                        'protocol_identity_sha256': 'f' * 64, 'steps': []}
        for phase in ('create', 'reopen'):
            log = self.smoke / 'service' / (phase + '.log')
            log.write_bytes(phase.encode())
            self.service['steps'].append({'phase': phase, 'passed': True, 'disconnected': True,
                'protocol_identity_sha256': 'f' * 64, 'log': reference(log.read_bytes(), log),
                'wrong_passphrase_rejected': True, 'cleanup': {'stopped': True, 'forced': False, 'exit_code': 0}})
        self.report = {'schema': 1, 'scope': 'windows_server_2022_current_user_nsis_service_lifecycle',
            'target': 'windows-x86_64', 'passed': True, 'inputs_unchanged': True, 'sources': sources,
            'gui_tested': False, 'windows_11_qualified': False, 'production_network_requested': False,
            'persistent_certificate_stores_unchanged': True, 'inputs': inputs,
            'host': {'system': 'Windows', 'architecture': 'x86_64', 'CurrentBuildNumber': '20348',
                     'InstallationType': 'Server'}, 'webview_runtime': [{'version': '1.2.3.4'}],
            'harness': self.source_refs['scripts/test-windows-installer.py'],
            'signature_verifier': self.source_refs['scripts/verify-windows-signature.ps1'],
            'application_inputs': self.application, 'installation_directory': self.installation,
            'registration': {'root': 'HKCU', 'location': self.installation,
                             'uninstall': self.installation + r'\uninstall.exe'}, 'commands': [],
            'cleanup': {'passed': True, 'uninstalled': True, 'registration_removed': True,
                        'installation_removed': True, 'children_stopped': True}}
        for name, artifact, parent in [('installer_signature', inputs['installer'], self.report),
                                      ('application_signature', self.binary, self.report),
                                      ('uninstaller_signature', reference(b'uninstaller', self.installation + r'\uninstall.exe'),
                                       self.report['cleanup'])]:
            parent[name] = {'artifact': artifact, 'thumbprint': self.publisher['certificate_fingerprint'],
                            'verification': 'pinned_authenticode', 'public_trust_claimed': False}
        trust = {scope + '/' + name: [] for scope in ('CurrentUser', 'LocalMachine')
                 for name in ('Root', 'CA', 'TrustedPublisher', 'My')}
        for name in ('initial-processes', 'trust-before', 'installer-signature', 'install', 'application-signature',
                     'service', 'cleanup-processes', 'uninstaller-signature', 'uninstall', 'trust-after'):
            command = {'name': name, 'exit_code': 0}
            for stream in ('stdout', 'stderr'):
                data = json.dumps(trust).encode() if name.startswith('trust-') and stream == 'stdout' else b''
                path = self.smoke / (name + '.' + stream)
                path.write_bytes(data)
                command[stream] = reference(data, path)
            self.report['commands'].append(command)
        self.imported = {'scope': 'isolated_current_user_signer_import', 'passed': True, 'store': 'CurrentUser/My',
            'certificate_fingerprint': self.publisher['certificate_fingerprint'],
            'certificate_sha256': self.publisher['certificate_sha256'], 'persistent_trust_stores_unchanged': True,
            'harness': self.source_refs['scripts/windows-signing.ps1'], 'publication': inputs['publication']}
        self.signing_cleanup = {'scope': 'isolated_current_user_signer_cleanup',
            'certificate_fingerprint': self.publisher['certificate_fingerprint'],
            'harness': self.source_refs['scripts/windows-signing.ps1'], **dict.fromkeys(
                ('passed', 'imported', 'private_key_removed', 'pfx_removed', 'my_store_restored',
                 'persistent_trust_stores_unchanged'), True)}

    def verify(self):
        path = self.smoke / 'service/report.json'
        data = json.dumps(self.service).encode()
        path.write_bytes(data)
        self.report['service_receipt'] = reference(data, path)
        (self.smoke / 'report.json').write_text(json.dumps(self.report))
        return worker.verify_installer_smoke(self.root, self.build, self.archive)

    def verify_signer(self):
        for name, report in (('import', self.imported), ('cleanup', self.signing_cleanup)):
            (self.root / 'signing-evidence' / (name + '.json')).write_text(json.dumps(report))
        worker.verify_signing_cleanup(self.root, self.publisher, self.archive)

    def test_exact_installed_binary_service_and_uninstall_evidence(self):
        self.verify()
        self.verify_signer()

    def test_linux_or_windows_11_receipt_cannot_qualify_server_worker(self):
        for key, value in [('system', 'Linux'), ('CurrentBuildNumber', '26100'), ('architecture', 'arm64')]:
            with self.subTest(key=key), patch.dict(self.report['host'], {key: value}):
                with self.assertRaisesRegex(ValueError, 'Server 2022'):
                    self.verify()

    def test_no_gui_or_network_qualification_inferred(self):
        for key in ('gui_tested', 'windows_11_qualified', 'production_network_requested'):
            with self.subTest(key=key), patch.dict(self.report, {key: True}):
                with self.assertRaisesRegex(ValueError, 'scope'):
                    self.verify()

    def test_installer_bytes_are_bound(self):
        (self.root / 'GChat.exe').write_bytes(b'other installer')
        with self.assertRaises(ValueError):
            self.verify()

    def test_installed_binary_cannot_differ_from_signed_native_build(self):
        self.binary['sha256'] = '0' * 64
        self.service['inputs'] = copy.deepcopy(self.application)
        with self.assertRaisesRegex(ValueError, 'executable differs'):
            self.verify()

    def test_service_source_swap_refused(self):
        self.service['inputs']['sources']['gcoms']['commit'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'different installed/native'):
            self.verify()

    def test_signature_wrong_pin_or_public_trust_claim_refused(self):
        for key, value in [('thumbprint', '0' * 40), ('public_trust_claimed', True)]:
            with self.subTest(key=key), patch.dict(self.report['application_signature'], {key: value}):
                with self.assertRaisesRegex(ValueError, 'signature binding'):
                    self.verify()

    def test_uninstaller_must_belong_to_owned_installation(self):
        self.report['registration']['uninstall'] = r'C:\other\uninstall.exe'
        with self.assertRaisesRegex(ValueError, 'escaped'):
            self.verify()

    def test_uninstall_and_process_cleanup_are_required(self):
        for key in ('uninstalled', 'registration_removed', 'installation_removed', 'children_stopped'):
            with self.subTest(key=key), patch.dict(self.report['cleanup'], {key: False}):
                with self.assertRaisesRegex(ValueError, 'cleanup'):
                    self.verify()

    def test_reopen_identity_and_rejected_unlock_required(self):
        for key, value in [('protocol_identity_sha256', '0' * 64), ('wrong_passphrase_rejected', False)]:
            with self.subTest(key=key), patch.dict(self.service['steps'][1], {key: value}):
                with self.assertRaises(ValueError):
                    self.verify()

    def test_forced_or_failed_service_shutdown_refused(self):
        for key, value in [('forced', True), ('exit_code', 1), ('stopped', False)]:
            with self.subTest(key=key), patch.dict(self.service['steps'][1]['cleanup'], {key: value}):
                with self.assertRaisesRegex(ValueError, 'shut down cleanly'):
                    self.verify()

    def test_missing_or_tampered_command_evidence_refused(self):
        command = self.report['commands'].pop()
        with self.assertRaisesRegex(ValueError, 'omits required'):
            self.verify()
        self.report['commands'].append(command)
        (self.smoke / 'uninstall.stdout').write_bytes(b'replaced output')
        with self.assertRaises(ValueError):
            self.verify()

    def test_actual_store_snapshots_must_match_boolean_claim(self):
        path = self.smoke / 'trust-after.stdout'
        value = json.loads(path.read_text())
        value['CurrentUser/Root'] = ['new-trusted-root']
        data = json.dumps(value).encode()
        path.write_bytes(data)
        self.report['commands'][-1]['stdout'] = reference(data, path)
        with self.assertRaisesRegex(ValueError, 'store snapshots differ'):
            self.verify()

    def test_signer_import_is_pinned_and_changes_no_root_trust(self):
        for key, value in [('certificate_fingerprint', '0' * 40), ('store', 'CurrentUser/Root'),
                           ('persistent_trust_stores_unchanged', False)]:
            with self.subTest(key=key), patch.dict(self.imported, {key: value}):
                with self.assertRaisesRegex(ValueError, 'pinned identity'):
                    self.verify_signer()

    def test_private_key_and_trust_cleanup_required(self):
        for key in ('private_key_removed', 'pfx_removed', 'my_store_restored', 'persistent_trust_stores_unchanged'):
            with self.subTest(key=key), patch.dict(self.signing_cleanup, {key: False}):
                with self.assertRaisesRegex(ValueError, 'cleanup'):
                    self.verify_signer()

    def test_signing_harness_is_bound_to_frozen_sources(self):
        self.imported['harness'] = reference(b'wrong code')
        with self.assertRaises(ValueError):
            self.verify_signer()


if __name__ == '__main__':
    unittest.main()
