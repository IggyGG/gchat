"""A recorded companion commit must actually supply installer dependencies."""
import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paired_sources import verify_npm_protocol, verify_resolved_protocol, verify_native_ci_inputs, verify_retained_inputs
from release_evidence import EvidenceError


class PairedSourcesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def qualification(self):
        inputs = {'schema': 1, 'kind': 'frozen_source_pair',
                  'sources': {'gchat': {'commit': 'a' * 40}, 'gcoms': {'commit': 'b' * 40}},
                  'source_archive_sha256': {'gchat': 'a' * 64, 'gcoms': 'b' * 64},
                  'target': 'x86_64-unknown-linux-gnu', 'rust_graphs': {'workspace': ['fixture']},
                  'derived_lock_sha256': {'Cargo.lock': 'c' * 64},
                  'npm_archives': {'fixture.tgz': 'd' * 64}, 'npm_bindings': {'fixture': 'd' * 64},
                  'cargo_config_sha256': 'e' * 64,
                  'rust_sources_verified': True, 'npm_sources_verified': True}
        report = {'sources': inputs['sources'], 'inputs': copy.deepcopy(inputs),
                  'exit_code': 0, 'source_unchanged': True}
        path = self.root / 'native-ci.json'
        path.write_text(json.dumps(report))
        return inputs, report, path

    def test_installer_may_relocate_but_not_reresolve_qualified_dependencies(self):
        inputs, report, path = self.qualification()
        inputs['cargo_config_sha256'] = 'f' * 64
        binding = verify_native_ci_inputs(path, inputs)
        self.assertEqual(binding['report_sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        for key in ('derived_lock_sha256', 'npm_archives', 'npm_bindings', 'rust_graphs',
                    'source_archive_sha256', 'sources'):
            changed = copy.deepcopy(inputs)
            changed[key]['unexpected'] = 'different bytes'
            with self.subTest(key=key), self.assertRaises(EvidenceError):
                verify_native_ci_inputs(path, changed)
        inputs['target'] = 'aarch64-apple-darwin'
        with self.assertRaisesRegex(EvidenceError, 'dependencies differ'):
            verify_native_ci_inputs(path, inputs)

    def test_failed_changed_or_unverified_native_inputs_cannot_authorize_signing(self):
        inputs, original, path = self.qualification()
        for changes in ({'exit_code': 1}, {'exit_code': False}, {'source_unchanged': False},
                        {'sources': {}}, {'inputs': {}}):
            path.write_text(json.dumps({**original, **changes}))
            with self.subTest(changes=changes), self.assertRaises(EvidenceError):
                verify_native_ci_inputs(path, inputs)
        original['inputs']['npm_sources_verified'] = False
        path.write_text(json.dumps(original))
        with self.assertRaisesRegex(EvidenceError, 'not verified'):
            verify_native_ci_inputs(path, inputs)

    def test_uploaded_inputs_must_retain_the_hashed_locks_config_and_archives(self):
        inputs, _, _ = self.qualification()
        values = {'derived/Cargo.lock': b'locked dependencies',
                  'derived/.cargo/config.toml': b'local source overrides',
                  'npm/fixture.tgz': b'archive bytes'}
        for name, data in values.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        inputs['derived_lock_sha256']['Cargo.lock'] = hashlib.sha256(values['derived/Cargo.lock']).hexdigest()
        inputs['cargo_config_sha256'] = hashlib.sha256(values['derived/.cargo/config.toml']).hexdigest()
        inputs['npm_archives']['fixture.tgz'] = hashlib.sha256(values['npm/fixture.tgz']).hexdigest()
        verify_retained_inputs(self.root, inputs)
        for name, data in values.items():
            path = self.root / name
            path.write_bytes(data + b'changed')
            with self.subTest(name=name), self.assertRaisesRegex(EvidenceError, 'hash mismatch'):
                verify_retained_inputs(self.root, inputs)
            path.unlink()
            with self.assertRaisesRegex(EvidenceError, 'missing evidence'):
                verify_retained_inputs(self.root, inputs)
            path.write_bytes(data)

    def graph(self):
        packages = []
        for name in ('gcoms', 'gcoms-runtime', 'gcoms-node', 'gcoms-rpc', 'gcoms-sdk'):
            manifest = self.root / name / 'Cargo.toml'
            manifest.parent.mkdir()
            manifest.write_text(f'[package]\nname="{name}"\nversion="0.1.0"\n')
            packages.append({'name': name, 'version': '0.1.0', 'source': None,
                             'manifest_path': str(manifest)})
        return {'packages': packages}

    def test_registry_or_other_checkout_cannot_claim_the_supplied_source(self):
        graph = self.graph()
        self.assertEqual(len(verify_resolved_protocol(graph, self.root)), 5)
        graph['packages'][0]['source'] = 'registry+https://example.invalid/index'
        with self.assertRaisesRegex(EvidenceError, 'frozen source pair'):
            verify_resolved_protocol(graph, self.root)
        graph['packages'][0]['source'] = None
        graph['packages'][0]['manifest_path'] = str(self.root.parent / 'elsewhere/Cargo.toml')
        with self.assertRaisesRegex(EvidenceError, 'frozen source pair'):
            verify_resolved_protocol(graph, self.root)

    def test_partial_graph_and_changed_package_identity_are_rejected(self):
        graph = self.graph()
        graph['packages'][0]['name'] = 'gcoms-other'
        with self.assertRaisesRegex(EvidenceError, 'name mismatch'):
            verify_resolved_protocol(graph, self.root)
        graph['packages'].pop(0)
        with self.assertRaisesRegex(EvidenceError, 'omits'):
            verify_resolved_protocol(graph, self.root)

    def test_npm_requires_exact_archives_and_integrity(self):
        archives, packages = [], {}
        for name in ('rpc', 'rpc-codegen'):
            archive = self.root / (name + '.tgz')
            data = json.dumps({'name': '@gcoms/' + name, 'version': '0.1.0'}).encode()
            with tarfile.open(archive, 'w:gz') as stream:
                info = tarfile.TarInfo('package/package.json')
                info.size = len(data)
                stream.addfile(info, io.BytesIO(data))
            archives.append(archive)
            packages['node_modules/@gcoms/' + name] = {
                'version': '0.1.0', 'resolved': 'file:' + archive.name,
                'integrity': 'sha512-' + base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode(),
            }
        lock = self.root / 'package-lock.json'
        lock.write_text(json.dumps({'packages': packages}))
        self.assertEqual(len(verify_npm_protocol(self.root, archives)), 2)
        packages['node_modules/@gcoms/rpc']['resolved'] = 'https://example.invalid/old.tgz'
        lock.write_text(json.dumps({'packages': packages}))
        with self.assertRaisesRegex(EvidenceError, 'frozen archive'):
            verify_npm_protocol(self.root, archives)
        packages['node_modules/@gcoms/rpc']['resolved'] = 'file:rpc.tgz'
        packages['node_modules/@gcoms/rpc']['integrity'] = 'sha512-wrong'
        lock.write_text(json.dumps({'packages': packages}))
        with self.assertRaisesRegex(EvidenceError, 'integrity'):
            verify_npm_protocol(self.root, archives)


if __name__ == '__main__':
    unittest.main()
