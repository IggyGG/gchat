"""Exercise rollback orchestration and failure cleanup; not native app evidence."""
import argparse
from contextlib import ExitStack
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('windows_rollback', SCRIPTS / 'windows-rollback.py')
rollback = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rollback)


class FlowTests(unittest.TestCase):
    def run_case(self, failure=None):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binaries = {}
            for name in ('windows36', 'windows18'):
                binary = root / (name + '.exe'); binary.write_bytes(name.encode())
                binaries[name] = {'binary': binary, 'build_manifest': root / 'build.json',
                    'native_receipt': root / 'native.json', 'build': {'publisher': {'name': 'test'},
                    'sources': {'fixture': name}}, 'signature': {}, 'archive_sha256': 'a' * 64}
            data = hashlib.shake_256(b'windows-rollback-cache').digest(rollback.network.PIECE)
            digest = hashlib.sha256(data).hexdigest()
            phases = []

            class Journey:
                def __init__(self, args):
                    self.args = args; self.root = args.output; self.root.mkdir()
                    self.start = time.monotonic(); self.children = []; self.clients = {}
                    self.report = {'events': []}; self.channel = 'test-channel'

                def start_client(self, i, create):
                    self.clients[i] = object()
                    (self.root / f'c{i}').mkdir(exist_ok=True)
                    if failure == 'restart' and not create:
                        raise RuntimeError('restart failed')

                def submit(self, i, text):
                    return {'conversation': self.channel, 'output': {'link': 'fixture'}}

                def until(self, fn): return fn()

                def call(self, i, kind, request):
                    if request['kind'] == 'inspect':
                        return {'response': {'kind': 'preview', 'preview': {
                            'newNetwork': False, 'network': {'id': 'fixture'}}}}
                    return {'response': {'kind': 'result', 'response': {'conversation': self.channel}}}

                def chat(self, phase):
                    if failure == 'ack' and phase == 'baseline':
                        raise RuntimeError('authenticated ACK missing')
                    phases.append((phase, self.args.binary.name))

                def files(self, *a, **kw): pass
                def io(self, *a): pass
                def row(self, *a): return {'state': 'complete'}
                def stop(self, i): pass
                def history(self, i): return [{'id': 'same-message'}]
                def export(self, ident):
                    return 'wrong' if failure == 'cache' and 'windows18' in self.args.binary.name else digest

            output = root / 'receipt'
            args = argparse.Namespace(output=output)
            with ExitStack() as stack:
                # Keep pathlib's real host type; replace only this module's os facade.
                from types import SimpleNamespace
                stack.enter_context(patch.object(rollback, 'os', SimpleNamespace(name='nt',
                    environ={'GITHUB_ACTIONS': 'true', 'GCHAT_NETWORK_INVITATION': 'fixture'})))
                stack.enter_context(patch.object(rollback.argparse.ArgumentParser, 'parse_args', return_value=args))
                stack.enter_context(patch.object(rollback, 'acquire', side_effect=lambda name, *a: binaries[name]))
                stack.enter_context(patch.object(rollback.network, 'Journey', Journey))
                stack.enter_context(patch.object(rollback.smoke, 'private_directory'))
                stack.enter_context(patch.object(rollback.smoke, 'private_fixture_path'))
                stack.enter_context(patch('sys.stdout', io.StringIO()))
                result = rollback.main()
            report = json.loads((output / 'report.json').read_text())
            self.assertTrue(report['cleanup_complete'])
            self.assertTrue(report['profiles_removed'])
            self.assertTrue(report['invitation_removed'])
            return result, report, phases

    def test_current_baseline_current_and_cleanup(self):
        result, report, phases = self.run_case()
        self.assertEqual(result, 0)
        self.assertTrue(report['passed'])
        self.assertEqual(phases, [('current', 'windows36.exe'), ('baseline', 'windows18.exe'),
                                  ('restored', 'windows36.exe')])
        self.assertEqual([p['phase'] for p in report['phases']], ['baseline', 'restored'])

    def test_failed_restart_ack_or_cache_never_becomes_a_pass(self):
        for failure in ('restart', 'ack', 'cache'):
            with self.subTest(failure=failure):
                result, report, _ = self.run_case(failure)
                self.assertEqual(result, 1)
                self.assertFalse(report['passed'])
                self.assertIn('error', report)


if __name__ == '__main__': unittest.main()
