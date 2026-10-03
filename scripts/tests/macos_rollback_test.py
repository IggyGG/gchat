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
SPEC = importlib.util.spec_from_file_location('macos_rollback', SCRIPTS / 'macos-rollback.py')
rollback = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rollback)


class FlowTests(unittest.TestCase):
    def test_manifest_escape_and_unbound_sources_rejected(self):
        import copy
        item={'run':1,'artifact':2,'archive':'a'*64,'controller':'b'*40,
              'sources':{'gchat':'c'*40,'gcoms':'d'*40},'manifest':'signed/build.json'}
        value={'target':'macos-x86_64','current':item,'baseline':copy.deepcopy(item)}
        self.assertEqual(rollback.validate_inputs(value),value)
        for bad in ('../build.json','/build.json','signed/not-build.json',
                    'C:/build.json',r'signed\build.json',r'\build.json'):
            candidate=copy.deepcopy(value);candidate['current']['manifest']=bad
            with self.assertRaisesRegex(ValueError,'manifest path'):rollback.validate_inputs(candidate)
        candidate=copy.deepcopy(value);candidate['baseline']['sources']['gcoms']='main'
        with self.assertRaisesRegex(ValueError,'artifact identity'):rollback.validate_inputs(candidate)

    def run_case(self, failure=None):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binaries = {}
            for name in ('current', 'baseline'):
                binary = root / (name + '.app'); binary.write_bytes(name.encode())
                binaries[name] = {'binary': binary, 'build_manifest': root / 'build.json',
                    'native_receipt': root / 'native.json', 'build': {'publisher': {'name': 'test'},
                    'sources': {'fixture': name}}, 'signature': {}, 'archive_sha256': 'a' * 64}
            data = hashlib.shake_256(b'mac-rollback-cache').digest(rollback.network.PIECE)
            digest = hashlib.sha256(data).hexdigest()
            phases = []

            class Journey:
                invitation = rollback.network.Journey.invitation
                join_peer = rollback.network.Journey.join_peer

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
                    return {'conversation': self.channel, 'output': {'kind': 'invitation', 'link': 'fixture'}}

                def until(self, fn): return fn()

                def call(self, i, kind, **data):
                    if kind == 'snapshot':
                        return {'snapshot': {'conversations': [{'id': self.channel, 'active': True}]}}
                    if data['request']['kind'] == 'inspect':
                        return {'response': {'kind': 'preview', 'preview': {
                            'newNetwork': False, 'network': {'id': 'fixture'}}}}
                    return {'response': {'kind': 'result', 'network': 'fixture',
                        'response': {'kind': 'applied', 'conversation': self.channel}}}

                def event(self, name): self.report['events'].append({'event': name})

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
                    return 'wrong' if failure == 'cache' and 'baseline' in self.args.binary.name else digest

            output = root / 'receipt'
            inputs=root/'inputs.json'; inputs.write_text('{}')
            args = argparse.Namespace(output=output,inputs=inputs)
            with ExitStack() as stack:
                # Keep pathlib's real host type; replace only this module's os facade.
                from types import SimpleNamespace
                stack.enter_context(patch.object(rollback, 'os', SimpleNamespace(name='posix',
                    environ={'GITHUB_ACTIONS': 'true', 'GCHAT_NETWORK_INVITATION': 'fixture'})))
                stack.enter_context(patch.object(rollback.argparse.ArgumentParser, 'parse_args', return_value=args))
                stack.enter_context(patch.object(rollback,'validate_inputs',return_value={'target':'macos-aarch64'}))
                stack.enter_context(patch.object(rollback.platform,'system',return_value='Darwin'))
                stack.enter_context(patch.object(rollback.platform,'machine',return_value='arm64'))
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
        self.assertEqual(phases, [('current', 'current.app'), ('baseline', 'baseline.app'),
                                  ('restored', 'current.app')])
        self.assertEqual([p['phase'] for p in report['phases']], ['baseline', 'restored'])

    def test_failed_restart_ack_or_cache_never_becomes_a_pass(self):
        for failure in ('restart', 'ack', 'cache'):
            with self.subTest(failure=failure):
                result, report, _ = self.run_case(failure)
                self.assertEqual(result, 1)
                self.assertFalse(report['passed'])
                self.assertIn('error', report)


if __name__ == '__main__': unittest.main()
