"""Owned iOS simulator and XCTest-only command bridge for retained app UI."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import queue
import re
import secrets
import shutil
import subprocess
import threading
import time
import uuid
from urllib.parse import unquote, urlparse

from mobile_acceptance_inputs import require
from release_network_canary import module

ios = module('ios-build')
lifecycle = module('ios-lifecycle')
UI_PHASES = frozenset(('ready', 'finish', 'stop', 'unlock', 'join', 'identity', 'send',
    'received', 'delivered', 'history', 'file_action', 'progress', 'export',
    'unlock-start', 'unlock-passphrase', 'unlock-confirm', 'unlock-submit', 'unlock-ready',
    'join-arrival', 'join-review', 'join-preview', 'join-input', 'join-accept', 'join-connected',
    'export-picker', 'export-unlock', 'export-result'))
UI_CONTROLS = frozenset(('review_invitation', 'create_identity', 'reconnect', 'connect_to_gchat',
    'close_dialog', 'nickname', 'joined', 'composer', 'webview', 'foreground'))


def runner_diagnostics(path, exit_code, polls):
    """Public categories only; XCTest output can contain private UI data."""
    text = Path(path).read_text(errors='replace')[-16 * 1024**2:] if Path(path).is_file() else ''
    return {'exit_code': exit_code, 'bridge_polls': polls,
        'compile_error_locations': sorted(set(re.findall(r'AcceptanceTests\.swift:(\d+:\d+): error:', text))),
        'configuration_ready': 'GCHAT_ACCEPTANCE_BRIDGE_CONFIGURATION=1' in text,
        'transport_codes': sorted(set(int(value) for value in
            re.findall(r'GCHAT_ACCEPTANCE_BRIDGE_TRANSPORT=(-?\d+)\b', text))),
        'http_status_codes': sorted(set(int(value) for value in
            re.findall(r'GCHAT_ACCEPTANCE_BRIDGE_HTTP=(\d+)\b', text))),
        'ui_phases': [phase for phase in re.findall(r'GCHAT_ACCEPTANCE_UI_PHASE=([a-z-]+)\b', text)
                      if phase in UI_PHASES],
        'runner_progress': {'swift_compile': 'SwiftCompile' in text or 'SwiftEmitModule' in text,
            'link': '\nLd ' in text, 'build_description': 'Build description' in text,
            'testing_started': 'Testing started' in text or 'Test Suite ' in text,
            'runner_launch_failure': 'Failed to launch' in text or 'failed to launch' in text,
            'simulator_failure': 'Failed to boot' in text or 'Unable to boot' in text,
            'test_failure': '** TEST FAILED **' in text},
        'build_failed': '** TEST BUILD FAILED **' in text or '** BUILD FAILED **' in text}


class Bridge:
    def __init__(self):
        self.token = secrets.token_urlsafe(32)
        self.commands = queue.Queue()
        self.results = {}
        self.polls = 0
        self.ready = threading.Condition()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                if self.headers.get('Authorization') != 'Bearer ' + owner.token:
                    self.send_error(403)
                    return
                try:
                    size = int(self.headers.get('Content-Length', '0'))
                    require(0 < size <= 196608, 'bounded XCTest bridge request required')
                    value = json.loads(self.rfile.read(size))
                    if self.path == '/next':
                        require(value == {'ready': True}, 'invalid XCTest poll')
                        owner.polls += 1
                        try:
                            result = owner.commands.get(timeout=3)
                        except queue.Empty:
                            result = {'op': 'idle'}
                    elif self.path == '/result':
                        require(re.fullmatch('[0-9a-f]{32}', value.get('id', ''))
                                and type(value.get('passed')) is bool
                                and (value.get('phase') is None or value['phase'] in UI_PHASES)
                                and len(json.dumps(value).encode()) <= 65536,
                                'invalid XCTest result')
                        observation = value.get('observation')
                        require(observation is None or (isinstance(observation, dict)
                            and set(observation) <= UI_CONTROLS
                            and all(type(flag) is bool for flag in observation.values())),
                            'invalid public XCTest observation')
                        with owner.ready:
                            require(value['id'] in owner.results and owner.results[value['id']] is None,
                                    'unknown or duplicate XCTest result')
                            owner.results[value['id']] = value
                            owner.ready.notify_all()
                        result = {'accepted': True}
                    else:
                        self.send_error(404)
                        return
                    data = json.dumps(result).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except Exception:
                    self.send_error(400)

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)

    def call(self, op, timeout=120, alive=None, **values):
        ident = uuid.uuid4().hex
        with self.ready:
            self.results[ident] = None
            self.commands.put({'id': ident, 'op': op, **values})
            end = time.monotonic() + timeout
            while self.results[ident] is None:
                remaining = end - time.monotonic()
                require(remaining > 0, 'original XCTest command deadline')
                require(alive is None or alive(), 'owned XCTest runner exited')
                self.ready.wait(min(remaining, 1) if alive is not None else remaining)
            result = self.results.pop(ident)
        if result['passed'] is not True:
            error = ValueError('installed iOS UI observation failed')
            error.ios_observation_phase = result.get('phase')
            error.ios_observation_controls = result.get('observation')
            raise error
        return result.get('value')

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=10)


class IOSUI:
    def __init__(self, output, passphrase, deadline, initial=None):
        require(ios.output(['xcodebuild', '-version']).splitlines()[0] == 'Xcode 26.2',
                'retained app requires the pinned Xcode')
        self.output, self.passphrase, self.deadline = output, passphrase, deadline
        self.device, self.bridge, self.runner, self.log = None, None, None, None
        self.bodies = set()
        self.installed = False
        self.active_binary_sha256 = None
        self.unlock_attempted = False
        runtime = ios.simulator_runtime()
        types = json.loads(ios.output(['xcrun', 'simctl', 'list', 'devicetypes', '--json']))['devicetypes']
        devices = json.loads(ios.output(['xcrun', 'simctl', 'list', 'devices', 'available', '--json']))['devices']
        phone = ios.simulator_phone(runtime, types, devices)
        self.device = ios.output(['xcrun', 'simctl', 'create', 'GChatAcceptance-' + secrets.token_hex(6), phone, runtime])
        require(re.fullmatch('[0-9A-Fa-f-]{36}', self.device), 'owned simulator ID differs')
        try:
            ios.run(['xcrun', 'simctl', 'boot', self.device], timeout=120)
            ios.run(['xcrun', 'simctl', 'bootstatus', self.device, '-b'], timeout=180)
            # XCTest must attach to a simulator that already has the unchanged
            # application, as the retained lifecycle worker does.
            if initial is not None:
                self.install(initial)
            self.bridge = Bridge()
            runner = output / 'runner'
            runner.mkdir()
            fixture = Path(__file__).with_name('fixtures') / 'ios-acceptance' / 'AcceptanceTests.swift'
            shutil.copyfile(fixture, runner / 'AcceptanceTests.swift')
            spec = lifecycle.runner_project()
            spec['targets']['LifecycleTests']['sources'] = ['AcceptanceTests.swift']
            spec['schemes']['GChatLifecycle']['test']['environmentVariables'] = {
                'GCHAT_TEST_BRIDGE_URL': self.bridge.url, 'GCHAT_TEST_BRIDGE_TOKEN': self.bridge.token}
            project = runner / 'project.json'
            project.write_text(json.dumps(spec))
            project.chmod(0o600)
            ios.run(['xcodegen', 'generate', '--spec', project.name], cwd=runner, timeout=120)
            self.log = (output / 'xctest.private.log').open('wb')
            # Only the UI test runner is compiled. No production app, framework,
            # signature, entitlement or library is rebuilt or changed.
            command = ['xcodebuild', 'test', '-project', runner / 'GChatLifecycle.xcodeproj',
                '-scheme', 'GChatLifecycle', '-destination', 'platform=iOS Simulator,id=' + self.device,
                '-derivedDataPath', output / 'runner-derived', '-parallel-testing-enabled', 'NO',
                '-maximum-concurrent-test-simulator-destinations', '1',
                '-only-testing:LifecycleTests/GChatAcceptanceTests/testRetainedNetworkJourney',
                'CODE_SIGNING_ALLOWED=NO']
            environment = {key: value for key, value in __import__('os').environ.items()
                           if key not in ('GH_TOKEN', 'GITHUB_TOKEN', 'GCHAT_NETWORK_INVITATION')}
            self.runner = subprocess.Popen(list(map(str, command)), stdout=self.log,
                                           stderr=subprocess.STDOUT, env=environment)
            self.call('ready', maximum=240)
        except Exception as error:
            cleaned = self.cleanup()
            error.owned_device_cleanup = cleaned
            error.ios_setup_diagnostics = runner_diagnostics(
                output / 'xctest.private.log', self.runner.poll() if self.runner is not None else None,
                self.bridge.polls if self.bridge is not None else 0)
            raise

    def call(self, op, maximum=120, **values):
        require(self.runner is not None and self.runner.poll() is None, 'owned XCTest runner exited')
        left = min(maximum, self.deadline() - time.monotonic())
        require(left > 0, 'original mobile journey deadline')
        return self.bridge.call(op, timeout=left, alive=lambda: self.runner.poll() is None, **values)

    def install(self, item):
        if self.installed and self.active_binary_sha256 == item['binary_sha256']:
            return
        if self.installed:
            self.stop()
        ios.run(['xcrun', 'simctl', 'install', self.device, item['app']], timeout=120)
        self.installed = True
        self.active_binary_sha256 = item['binary_sha256']

    def diagnostics(self):
        return runner_diagnostics(self.output / 'xctest.private.log',
            self.runner.poll() if self.runner is not None else None,
            self.bridge.polls if self.bridge is not None else 0)

    def stop(self):
        self.call('stop')

    def unlock(self, create=False):
        fresh = create and not self.unlock_attempted
        self.unlock_attempted = True
        try:
            self.call('unlock', create=create, passphrase=self.passphrase)
        except Exception as error:
            # A new owned simulator, before the first input or invitation, is
            # the only iOS screen eligible for retained startup pixels.
            if fresh and getattr(error, 'ios_observation_phase', None) == 'unlock-start':
                try:
                    ios.run(['xcrun', 'simctl', 'io', self.device, 'screenshot',
                             self.output.parent / 'fresh-startup.png'], timeout=30)
                except Exception:
                    pass
            raise

    def join(self, invitation):
        require(invitation.startswith('gcoms:') and len(invitation.encode()) <= 180000,
                'bounded mobile conversation invitation required')
        # Exercise the real cold OS activation path. Termination also verifies
        # that the newly created identity survives before network enrollment.
        self.stop()
        # The retained app consumes its normal deep-link path. Never print the
        # URI or return a CalledProcessError containing private command arguments.
        result = subprocess.run(['xcrun', 'simctl', 'openurl', self.device, invitation],
                                capture_output=True, timeout=30)
        require(result.returncode == 0, 'owned iOS invitation activation failed')
        self.call('join')

    def identity(self):
        value = self.call('identity')
        require(isinstance(value, str) and re.fullmatch(
            r'[0-9a-f]{64}\n[A-Z2-7]{8}(?: [A-Z2-7]{8}){4}', value), 'actual iOS identity unavailable')
        return hashlib.sha256(value.encode()).hexdigest()

    def send(self, body):
        self.bodies.add(body)
        self.call('send', body=body)

    def received(self, body):
        self.bodies.add(body)
        return self.call('received', maximum=20, body=body) is True

    def delivered(self, body):
        return self.call('delivered', maximum=20, body=body, known_bodies=sorted(self.bodies)) is True

    def history(self, bodies):
        self.bodies.update(bodies)
        require(self.call('history', bodies=sorted(bodies)) is True,
                'rendered mobile history was lost after replacement')

    def file_action(self, name, action):
        self.call('file_action', name=name, action=action)

    def progress(self, name, size):
        value = self.call('progress', maximum=20, name=name, size=size)
        require(value is None or (type(value) is int and 0 <= value <= size), 'invalid actual mobile progress')
        return value

    def container(self):
        require(self.installed, 'owned iOS application is not installed')
        path = Path(ios.output(['xcrun', 'simctl', 'get_app_container', self.device, ios.BUNDLE, 'data']))
        require(self.device in str(path) and path.is_dir() and not path.is_symlink(),
                'owned simulator data container differs')
        return path

    def cache_hash(self, ident):
        require(re.fullmatch('[0-9a-f]{32}', ident), 'invalid retained mobile file ID')
        paths = [path for path in self.container().rglob('0.piece')
                 if path.parent.name == ident and path.is_file() and not path.is_symlink()]
        require(len(paths) == 1, 'one retained encrypted mobile cache piece required')
        return hashlib.sha256(paths[0].read_bytes()).hexdigest()

    def export(self, name, phase):
        uri = self.call('export', name=name)
        require(isinstance(uri, str), 'actual iOS saved document URI unavailable')
        parsed = urlparse(uri)
        root = next((parent / 'data' for parent in self.container().parents if parent.name == self.device), None)
        path = Path(unquote(parsed.path))
        require(root is not None and parsed.scheme == 'file' and parsed.netloc in ('', 'localhost')
                and path.name == name and path.is_file() and not path.is_symlink()
                and path.resolve().is_relative_to(root.resolve()),
                'actual owned iOS document export missing')
        value = hashlib.sha256(path.read_bytes()).hexdigest()
        # Remove only this exact, newly exported disposable document. A fresh
        # export at each reopen cannot be satisfied by an earlier saved copy.
        path.unlink()
        return value

    def cleanup(self):
        errors = []
        if self.bridge is not None and self.runner is not None and self.runner.poll() is None:
            try:
                self.bridge.call('finish', timeout=30)
                self.runner.wait(timeout=60)
            except Exception as error:
                errors.append(type(error).__name__)
                if self.runner.poll() is None:
                    self.runner.kill()
                    self.runner.wait(timeout=10)
        if self.runner is not None and self.runner.poll() != 0:
            errors.append('XCTestFailed')
        if self.log is not None:
            self.log.close()
        if self.bridge is not None:
            self.bridge.close()
        report = {}
        if self.device is not None:
            lifecycle.cleanup_device(self.device, report)
        return {'passed': report.get('cleanup_complete') is True and not errors,
                'errors': errors + report.get('cleanup_errors', [])}
