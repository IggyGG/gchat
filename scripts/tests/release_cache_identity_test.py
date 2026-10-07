"""Compiler reuse cannot mistake a version bump for new external dependencies."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release_cache as cache


class CompilerCacheIdentity(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        for name in ('gchat', 'gcoms'):
            p = self.root / name
            p.mkdir()
            (p / 'rust-toolchain.toml').write_text('[toolchain]\nchannel = "1.98.0"\n')
            (p / 'Cargo.lock').write_text('''version = 4
[[package]]
name = "gchat-core"
version = "0.1.171"
[[package]]
name = "tokio"
version = "1.0.0"
source = "registry+https://example.invalid/index"
checksum = "aaa"
''')
            (p / 'package-lock.json').write_text(json.dumps({'packages': {
                '': {'version': '0.1.171'},
                'node_modules/@gcoms/rpc': {'version': '0.1.171', 'integrity': 'own'},
                'node_modules/external': {'version': '1', 'resolved': 'https://example.invalid/a', 'integrity': 'abc'},
            }}))

    def key(self, scope='gchat', image='ubuntu24/20261007'):
        return cache.identity(self.root, scope, image)

    def test_product_versions_and_source_changes_reuse_only_compiler_cache(self):
        before = self.key()
        for name in ('gchat', 'gcoms'):
            p = self.root / name
            for filename in ('Cargo.lock', 'package-lock.json'):
                path = p / filename
                path.write_text(path.read_text().replace('0.1.171', '0.1.172'))
            (p / 'changed.rs').write_text('new application source')
        self.assertEqual(before, self.key())
        self.assertFalse(before['qualification_reused'])

    def test_external_rust_and_npm_changes_change_exact_key(self):
        original = self.key()
        p = self.root / 'gchat/Cargo.lock'
        source = p.read_text()
        p.write_text(source.replace('checksum = "aaa"', 'checksum = "bbb"'))
        self.assertNotEqual(original['key'], self.key()['key'])
        self.assertEqual(original['restore_prefix'], self.key()['restore_prefix'])
        p.write_text(source)
        p = self.root / 'gchat/package-lock.json'
        value = json.loads(p.read_text())
        value['packages']['node_modules/external']['integrity'] = 'changed'
        p.write_text(json.dumps(value))
        self.assertNotEqual(original['key'], self.key()['key'])

    def test_toolchain_runner_and_role_isolate_compilation(self):
        original = self.key()
        for scope in ('gcoms', 'services'):
            self.assertNotEqual(original['restore_prefix'], self.key(scope)['restore_prefix'])
        self.assertNotEqual(original['restore_prefix'], self.key(image='ubuntu24/new')['restore_prefix'])
        for name in ('gchat', 'gcoms'):
            (self.root / name / 'rust-toolchain.toml').write_text('[toolchain]\nchannel = "1.99.0"\n')
        self.assertNotEqual(original['restore_prefix'], self.key()['restore_prefix'])

    def test_missing_lock_or_differing_toolchains_fail(self):
        p = self.root / 'gcoms/rust-toolchain.toml'
        p.write_text('[toolchain]\nchannel = "1.99.0"\n')
        with self.assertRaisesRegex(ValueError, 'toolchains differ'):
            self.key()
        p.write_text('[toolchain]\nchannel = "1.98.0"\n')
        (self.root / 'gcoms/Cargo.lock').unlink()
        with self.assertRaisesRegex(ValueError, 'dependency lock'):
            self.key()


if __name__ == '__main__':
    unittest.main()
