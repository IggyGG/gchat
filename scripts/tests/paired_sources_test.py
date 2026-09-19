"""A recorded companion commit must actually supply installer dependencies."""
import base64
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paired_sources import verify_npm_protocol, verify_resolved_protocol
from release_evidence import EvidenceError


class PairedSourcesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def graph(self):
        packages = []
        for name in ('gcoms-node', 'gcoms-rpc', 'gcoms-sdk'):
            manifest = self.root / name / 'Cargo.toml'
            manifest.parent.mkdir()
            manifest.write_text(f'[package]\nname="{name}"\nversion="0.1.0"\n')
            packages.append({'name': name, 'version': '0.1.0', 'source': None,
                             'manifest_path': str(manifest)})
        return {'packages': packages}

    def test_registry_or_other_checkout_cannot_claim_the_supplied_source(self):
        graph = self.graph()
        self.assertEqual(len(verify_resolved_protocol(graph, self.root)), 3)
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
