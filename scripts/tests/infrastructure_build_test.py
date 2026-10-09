import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import tarfile
import unittest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

spec = importlib.util.spec_from_file_location('infrastructure_build', Path(__file__).resolve().parents[1] / 'build-infrastructure.py')
build = importlib.util.module_from_spec(spec); spec.loader.exec_module(build)
import linux_build_artifacts as artifacts
from release_automation_test import candidate
from release_pair import canonical


class ArchiveConfigurationTests(unittest.TestCase):
    def test_configuration_digest_comes_from_retained_bytes_not_image_index(self):
        config = b'{"config":{"Env":["GCHAT_CONTROLLER_REVISION=frozen-source"]}}'
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'image.tar'
            with tarfile.open(path, 'w') as archive:
                for name, data in {'manifest.json': json.dumps([{'RepoTags': ['qualified:source'],
                    'Config': 'blobs/sha256/configuration'}]).encode(), 'blobs/sha256/configuration': config}.items():
                    entry = tarfile.TarInfo(name); entry.size = len(data); archive.addfile(entry, io.BytesIO(data))
            self.assertEqual(build.archive_config(path, 'qualified:source'), 'sha256:' + hashlib.sha256(config).hexdigest())
            with self.assertRaisesRegex(ValueError, 'exact build tag'): build.archive_config(path, 'another:tag')


class RetainedServiceTests(unittest.TestCase):
    def test_production_compiles_once_then_container_packaging_uses_identical_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); source = root / 'gcoms'; source.mkdir()
            target = root / 'target/release'; target.mkdir(parents=True)
            manifest = candidate(); manifest_path = root / 'manifest.json'; manifest_path.write_bytes(canonical(manifest))
            environment = {'GCHAT_RELEASE_MANIFEST': str(manifest_path), 'CARGO_TARGET_DIR': str(target.parent),
                           'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': 'IggyGG/gchat',
                           'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '1', 'RUSTFLAGS': '',
                           'GITHUB_WORKFLOW_SHA': manifest['sources']['gchat']['commit'],
                           'GITHUB_SHA': manifest['sources']['gchat']['commit']}
            retained = root / 'native'; packaged = root / 'packaged'; commands = []
            certificates = root / 'fixture-ca.crt'
            certificates.write_bytes(b'fixture trust bundle\n')
            copy_file = build.shutil.copy2
            certificate_copies = []

            def copy_fixture(source, destination, *args, **kwargs):
                if source == '/etc/ssl/certs/ca-certificates.crt':
                    certificate_copies.append(destination)
                    source = certificates
                return copy_file(source, destination, *args, **kwargs)

            def execute(command, **kwargs):
                commands.append(command)
                if command[0] == 'cargo':
                    self.assertEqual(command, artifacts.SERVICE_COMMAND)
                    for name in build.BINARIES: (target / name).write_bytes(('production ' + name).encode())
                elif command[:2] == ['docker', 'save']:
                    Path(command[command.index('-o') + 1]).write_bytes(b'container archive')
                elif command[:2] == ['git', 'archive']:
                    with tarfile.open(fileobj=kwargs['stdout'], mode='w') as archive:
                        entry = tarfile.TarInfo('release/automation/Dockerfile'); entry.size = 13
                        archive.addfile(entry, io.BytesIO(b'FROM scratch\n'))
                elif command[0] == 'python3':
                    context = Path(command[command.index('--output') + 1]); context.mkdir()
                    (context / 'context-manifest.json').write_text('{}')

            def qualification(*args):
                (packaged / 'controller-runtime.json').write_text('{"passed":true}')
                (packaged / 'controller-runtime.log').write_text('actual image tests retained')

            with patch.dict(os.environ, environment, clear=True), \
                 patch.object(build, 'identity', side_effect=lambda path: manifest['sources']['gcoms' if path == source else 'gchat']), \
                 patch.object(artifacts, 'rustc', return_value='rustc pinned\nhost: ' + artifacts.TARGET + '\n'), \
                 patch.object(build.subprocess, 'run', side_effect=execute), \
                 patch.object(build.shutil, 'copy2', side_effect=copy_fixture), \
                 patch.object(build, 'archive_config', return_value='sha256:' + 'e' * 64), \
                 patch.object(build, 'qualify_controller', side_effect=qualification), \
                 patch.object(sys, 'argv', ['build', '--gcoms', str(source), '--output', str(retained), '--binaries-only']):
                build.main()
                self.assertEqual(commands, [artifacts.SERVICE_COMMAND])
                record = artifacts.verify(retained, manifest, 'linux_native_services', environment)
                self.assertFalse((retained / 'build.json').exists())
                with patch.object(sys, 'argv', ['build', '--gcoms', str(source), '--output', str(packaged), '--native-build', str(retained)]):
                    build.main()
            self.assertEqual(sum(command[0] == 'cargo' for command in commands), 1)
            self.assertEqual(sum(command[:2] == ['docker', 'build'] for command in commands), 3)
            self.assertEqual(certificate_copies, [packaged / 'ca-certificates.crt'])
            self.assertEqual((packaged / 'ca-certificates.crt').read_bytes(), certificates.read_bytes())
            for name in build.BINARIES:
                self.assertEqual(artifacts.digest(packaged / name), record['files'][name])
            # The live controller's verifier requires the existing exact public
            # inventory. Build-once receipts remain in the upstream artifact.
            from release_infrastructure_bundle import FILES, RUNTIME_FILES
            self.assertEqual(set(json.loads((packaged / 'build.json').read_text())['sha256']),
                             set(FILES + RUNTIME_FILES))
            self.assertEqual(json.loads((packaged / 'build.json').read_text())['sha256']['ca-certificates.crt'],
                             artifacts.digest(certificates))
            self.assertFalse((packaged / 'native-build.json').exists())


if __name__ == '__main__': unittest.main()
