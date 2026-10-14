from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_worker_identity import fingerprint, implementation


class WorkerIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.put('release_coordinator', 'def atomic_json(path, value):\n    return value\n\ndef status():\n    return "old status"\n')
        self.put('provider', 'def fetch():\n    return 1\n')
        self.put('builder', 'from release_coordinator import atomic_json\nfrom provider import fetch\ndef main():\n    return atomic_json("result", fetch())\n')
        self.put('store', 'def main():\n    return "independent store worker"\n')
        self.recipe = {'run': ['python3', str(self.root / 'builder.py')], 'timeout': 900}

    def put(self, name, text):
        (self.root / (name + '.py')).write_text(text)

    def revision(self, **kwargs):
        return fingerprint(self.recipe, 'linux-x86_64', 'build', root=self.root, **kwargs)

    def test_stale_configured_revision_cannot_hide_or_manufacture_source_changes(self):
        first = self.revision(legacy_revision='old-pinned-controller')
        self.assertEqual(first, self.revision(legacy_revision='different-release-label'))
        self.put('provider', 'def fetch():\n    return 2\n')
        self.assertNotEqual(first, self.revision(legacy_revision='old-pinned-controller'))

    def test_unrelated_worker_and_status_edits_do_not_reopen_native_failure(self):
        first = self.revision()
        self.put('store', 'def main():\n    return "store correction"\n')
        self.put('release_coordinator', 'def atomic_json(path, value):\n    return value\n\ndef status():\n    return "new status display"\n')
        self.assertEqual(first, self.revision())
        self.put('release_coordinator', 'def atomic_json(path, value):\n    return dict(value)\n\ndef status():\n    return "new status display"\n')
        self.assertNotEqual(first, self.revision())

    def test_configuration_and_platform_are_bound(self):
        config = self.root / 'worker.json'; config.write_text('{"qualification_commit":"one"}')
        self.recipe['run'] += ['--config', str(config)]
        first = self.revision()
        config.write_text('{"qualification_commit":"two"}')
        self.assertNotEqual(first, self.revision())
        self.assertNotEqual(self.revision(), fingerprint(self.recipe, 'ios', 'build', root=self.root))

    def test_projected_configuration_binds_bytes_without_epoch_path_churn(self):
        first = self.root / 'generation-one'; first.write_text('{"value":1}')
        second = self.root / 'generation-two'; second.write_text('{"value":1}')
        config = self.root / 'config.json'; config.symlink_to(first)
        self.recipe['run'] += ['--config', str(config)]
        before = self.revision()
        config.unlink(); config.symlink_to(second)
        self.assertEqual(before, self.revision())
        second.write_text('{"value":2}')
        self.assertNotEqual(before, self.revision())

    def test_cycles_are_bounded_and_dynamic_native_helpers_are_included(self):
        self.put('provider', 'from builder import main\ndef fetch():\n    return module("native-helper")\n')
        self.put('native-helper', 'def verify():\n    return True\n')
        files = implementation('builder', self.root)
        self.assertEqual(set(files), {'builder.py', 'provider.py', 'release_coordinator.py', 'native-helper.py'})

    def test_qualified_script_links_and_unknown_control_helpers_refuse(self):
        self.put('builder', 'from release_coordinator import not_a_real_helper\nnot_a_real_helper()\n')
        with self.assertRaisesRegex(ValueError, 'unrecognized'):
            self.revision()
        (self.root / 'builder.py').unlink()
        (self.root / 'builder.py').symlink_to(self.root / 'store.py')
        with self.assertRaises(ValueError): self.revision()

    def test_opaque_administrator_recipes_keep_their_explicit_revision(self):
        recipe = {'run': ['external-worker'], 'reconcile': ['external-worker', '--reconcile']}
        first = fingerprint(recipe, 'ios', 'build', root=self.root, legacy_revision='one')
        self.assertNotEqual(first, fingerprint(recipe, 'ios', 'build', root=self.root, legacy_revision='two'))

    def test_cached_identity_rechecks_source_metadata_and_new_local_imports(self):
        cache = {}
        first = self.revision(cache=cache)
        self.assertEqual(first, self.revision(cache=cache))
        self.put('provider', 'from new_helper import fetch\n')
        second = self.revision(cache=cache)
        self.assertNotEqual(first, second)
        self.put('new_helper', 'def fetch():\n    return 3\n')
        self.assertNotEqual(second, self.revision(cache=cache))
