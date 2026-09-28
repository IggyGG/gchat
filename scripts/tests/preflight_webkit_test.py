"""Browser preflight must use the locked core without unrelated private SDKs."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location('preflight',ROOT/'scripts/preflight-webkit.py')
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)

class PreflightTests(unittest.TestCase):
    def test_preserves_locked_integrity_without_application_dependencies(self):
        original=json.loads((ROOT/'package-lock.json').read_text())
        before=copy.deepcopy(original)
        package,lock=m.locked_project(original)
        self.assertEqual(set(lock['packages']),{'','node_modules/playwright-core'})
        self.assertEqual(lock['packages']['node_modules/playwright-core'],original['packages']['node_modules/playwright-core'])
        self.assertEqual(set(package['devDependencies']),{'playwright-core'})
        self.assertEqual(original,before)

    def test_changed_download_origin_or_dependency_graph_requires_review(self):
        original=json.loads((ROOT/'package-lock.json').read_text())
        for key,value in [('resolved','https://untrusted.invalid/core.tgz'),('integrity',''),('dependencies',{'new':'1'})]:
            lock=copy.deepcopy(original);lock['packages']['node_modules/playwright-core'][key]=value
            with self.assertRaises(ValueError):m.locked_project(lock)
