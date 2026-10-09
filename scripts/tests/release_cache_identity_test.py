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

    def key(self, scope='gchat', image='ubuntu24/20261007', environment=None):
        return cache.identity(self.root, scope, image, {} if environment is None else environment)

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
        self.assertNotEqual(original['restore_prefix'], self.key(image='ubuntu22/20261007')['restore_prefix'])
        for name in ('gchat', 'gcoms'):
            (self.root / name / 'rust-toolchain.toml').write_text('[toolchain]\nchannel = "1.99.0"\n')
        self.assertNotEqual(original['restore_prefix'], self.key()['restore_prefix'])
        self.assertNotEqual(original['legacy_restore_key'], self.key()['legacy_restore_key'])

    def test_weekly_runner_rollout_changes_exact_key_but_keeps_compatible_restore(self):
        original = self.key(image='ubuntu24/20260927.320.1')
        current = self.key(image='ubuntu24/20261004.327.1')
        self.assertNotEqual(original['key'], current['key'])
        self.assertEqual(original['restore_prefix'], current['restore_prefix'])
        self.assertTrue(original['key'].startswith(current['restore_prefix']))
        self.assertTrue(current['key'].startswith('linux-compiler-v2-'))
        self.assertFalse(current['qualification_reused'])

    def test_compiler_flags_and_profiles_cannot_share_compatible_restore(self):
        original = self.key()
        for name, value in [('RUSTFLAGS', '-C target-cpu=native'), ('CARGO_ENCODED_RUSTFLAGS', '-Copt-level=1'),
                            ('CARGO_BUILD_TARGET', 'aarch64-unknown-linux-gnu'), ('CARGO_INCREMENTAL', '1'),
                            ('CARGO_PROFILE_DEV_DEBUG', '2'), ('CARGO_PROFILE_TEST_DEBUG', '2'),
                            ('CARGO_PROFILE_RELEASE_LTO', 'false'), ('CARGO_PROFILE_DEV_OPT_LEVEL', '1'),
                            ('CARGO_PROFILE_TEST_DEBUG_ASSERTIONS', 'false')]:
            with self.subTest(name=name):
                self.assertNotEqual(original['restore_prefix'], self.key(environment={name: value})['restore_prefix'])
                self.assertEqual(self.key(environment={name: value})['legacy_restore_key'], '')

    def test_v1_migration_matches_frozen_exact_key_without_broadening_profile(self):
        original = self.key()
        # Captured from the previous v1 implementation on these fixed inputs.
        self.assertEqual(original['legacy_restore_key'],
                         'linux-compiler-v1-gchat-acf4b375a8c3bf19872e-'
                         '0735c49aa7fcbd4a4dc5295a06ab5e2ff6378de4060e09651af86a394b44ea89')
        for scope, image in [('services', 'ubuntu24/20261007'), ('gchat', 'ubuntu24/20261008'),
                             ('gchat', 'ubuntu22/20261007')]:
            self.assertNotEqual(original['legacy_restore_key'], self.key(scope, image)['legacy_restore_key'])
        lock = self.root / 'gchat/Cargo.lock'
        lock.write_text(lock.read_text().replace('checksum = "aaa"', 'checksum = "bbb"'))
        self.assertNotEqual(original['legacy_restore_key'], self.key()['legacy_restore_key'])

    def test_missing_runner_os_or_version_is_rejected(self):
        for image in ('', '/', 'ubuntu24', 'ubuntu24/', '/20261007', 'ubuntu24/20261007/extra'):
            with self.subTest(image=image), self.assertRaisesRegex(ValueError, 'runner image required'):
                self.key(image=image)

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
