"""Bounded installed-service network journey using fresh, disposable profiles.

The caller separately verifies the installer signature. This test binds the
executable to its native receipt, checks real recipient ACKs and interrupted
bounded export/reopen, and never changes a personal profile or relay service.
It does not qualify GUI behavior, steady-state latency, or rollback.
"""
import argparse, base64, hashlib, importlib.util, json, os, secrets, shutil, socket, struct, subprocess, sys, time, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
spec = importlib.util.spec_from_file_location('smoke', Path(__file__).resolve().parent / 'test-native-application.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
PIECE = 262144

def validate_file_bytes(value, platform):
    m.require(type(value) is int and (value == 16777216 or
              (platform == 'nt' and value == 4194304)),
              'release size must be 16 MiB, or the explicitly selected Windows 4 MiB check')

def fixture_environment(home):
    environment = m.isolated_environment(home)
    if os.environ.get('GCHAT_NETWORK_DIAGNOSTICS') == '1':
        # Explicit aggregate counters, never inherited provider/authority controls.
        environment['GCHAT_FILE_DIAGNOSTICS'] = '1'
        environment['GCHAT_LATENCY_DIAGNOSTICS'] = '1'
    return environment

def binary_worker():
    r = json.load(sys.stdin)
    body = base64.b64decode(r['frame'], validate=True)
    m.require(8 <= len(body) <= PIECE + 1024, 'invalid local file frame')

    def exchange(f):
        data = memoryview(struct.pack('!I', len(body)) + body)
        while data:
            n = f.write(data)
            m.require(n is not None and n > 0, 'file IPC stopped')
            data = data[n:]
        f.flush()
        size = struct.unpack('!I', m.read_exact(f, 4))[0]
        m.require(1 <= size <= PIECE + 1024, 'invalid file IPC size')
        answer = m.read_exact(f, size)
        m.require(answer[0] == 0, 'file IPC rejected request')
        return answer[1:]
    if os.name == 'nt':
        with open(m.pipe_name(r['endpoint']), 'r+b', buffering=0) as f:
            answer = exchange(f)
    else:
        with socket.socket(socket.AF_UNIX) as s:
            s.settimeout(r['timeout'])
            s.connect(r['endpoint'])
            with s.makefile('rwb', buffering=0) as f:
                answer = exchange(f)
    print(base64.b64encode(answer).decode())

class Journey:

    def __init__(self, args):
        self.args = args
        self.root = args.output.resolve()
        self.root.mkdir(parents=True, exist_ok=False)
        m.private_directory(self.root)
        self.start = time.monotonic()
        self.deadline = self.start + 600
        self.children = []
        self.clients = {}
        self.ids = {}
        self.passphrase = secrets.token_urlsafe(32)
        self.report = {'schema': 1, 'passed': False, 'scope': 'actual packaged service network messaging and bounded interrupted file recovery', 'binary_sha256': m.digest(args.binary), 'started_at': m.timestamp(), 'events': []}
        self.report['harness'] = m.reference(Path(__file__))
        self.report['ipc_helper'] = m.reference(Path(m.__file__))

    def event(self, name, **data):
        row = {'event': name, 'elapsed': time.monotonic() - self.start, **data}
        self.report['events'].append(row)
        print(json.dumps(row), flush=True)

    def timeout(self, maximum=120):
        left = min(maximum, self.deadline - time.monotonic())
        m.require(left > 0, 'original 600-second journey deadline')
        return left

    def until(self, fn, maximum=120):
        end = min(self.deadline, time.monotonic() + maximum)
        while time.monotonic() < end:
            result = fn()
            if result:
                m.require(time.monotonic() <= end, 'result arrived after original stage deadline')
                return result
            time.sleep(0.2)
        raise TimeoutError('original stage deadline')

    def start_client(self, i, create):
        home = self.root / f'c{i}'
        if create:
            home.mkdir()
            m.private_directory(home)
        stop = home / ('stop-' + uuid.uuid4().hex)
        command = m.service_command(self.args.binary.resolve(), home, stop)
        command.remove('--no-network-bootstrap')
        log = (self.root / (f'client{i}-' + uuid.uuid4().hex + '.log')).open('xb')
        environment = fixture_environment(home)
        if environment.get('GCHAT_FILE_DIAGNOSTICS') == '1':
            self.report['aggregate_diagnostics_enabled'] = True
        p = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        self.children.append((i, p, stop, log))
        c = m.Client(home / 'protocol.chat', self.timeout())
        self.clients[i] = c

        def identify():
            m.require(p.poll() is None, 'packaged process exited')
            try:
                return c.call('identify', timeout=self.timeout(2))
            except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired):
                return None
        self.until(identify, 30)
        info = m.snapshot_instance(c.call('unlock', passphrase=self.passphrase, create=create, timeout=self.timeout()), False)
        identity = (info['id'], info['safetyNumber'])
        m.require(create or identity == self.ids[i], 'retained identity changed')
        self.ids[i] = identity
        if create:
            self.call(i, 'import_network_invitation', code=self.args.invitation.read_text().strip())
            self.files(i, 'configure', quota_bytes=str(64 * 1024 * 1024), retention_days=1)
        self.until(lambda: self.call(i, 'network_status')['status']['state'] == 'connected')
        self.event('client_ready', client=i, create=create)

    def call(self, i, kind, **data):
        return self.clients[i].call(kind, timeout=self.timeout(), **data)

    def files(self, i, action='list', **data):
        if action == 'list':
            data.setdefault('conversation', None)
        return self.call(i, 'files', request={'action': action, **data})['snapshot']

    def submit(self, i, text):
        return self.call(i, 'submit', operation_id=uuid.uuid4().hex, conversation=getattr(self, 'channel', None), text=text)

    def history(self, i):
        return self.call(i, 'history', conversation=self.channel, before=None, limit=200)['page']['messages']

    def chat(self, label):
        for sender, receiver in ((0, 1), (1, 0)):
            body = f'bounded-{label}-{sender}-{uuid.uuid4().hex[:8]}'
            self.submit(sender, body)

            def delivered():
                sent = [r for r in self.history(sender) if r['body'] == body]
                received = [r for r in self.history(receiver) if r['body'] == body]
                m.require(len(sent) <= 1 and len(received) <= 1, 'duplicate message')
                if not sent or not received:
                    return None
                m.require(sent[0]['mine'] and (not received[0]['mine']) and (sent[0]['id'] == received[0]['id']), 'message identity mismatch')
                return sent[0] if sent[0]['delivery'] == 'delivered' else None
            row = self.until(delivered)
            self.event('authenticated_ack', sender=sender, message_id=row['id'])

    def io(self, i, ident, piece, upload, data=b''):
        header = json.dumps({'instance': self.clients[i].instance, 'id': ident, 'piece': piece, 'upload': upload}, separators=(',', ':')).encode()
        m.require(len(header) <= 512 and len(data) <= PIECE, 'file frame too large')
        frame = b'GCFIO1' + struct.pack('!H', len(header)) + header + data
        timeout = self.timeout(30)
        r = subprocess.run([sys.executable, __file__, '_binary'], input=json.dumps({'endpoint': str(self.clients[i].endpoint), 'timeout': timeout, 'frame': base64.b64encode(frame).decode()}), capture_output=True, text=True, timeout=timeout, check=True)
        return base64.b64decode(r.stdout.strip(), validate=True)

    def stop(self, i, abrupt=False):
        _, p, stop, log = next((row for row in reversed(self.children) if row[0] == i))
        if abrupt:
            p.kill()
            p.wait(timeout=10)
            result = {'stopped': True, 'forced': True, 'abrupt_requested': True}
        else:
            result = m.stop_service(p, stop, 10)
            m.require(result['stopped'] and (not result['forced']) and (result['exit_code'] == 0), 'orderly stop failed')
        log.close()
        self.event('client_stopped', client=i, **result)

    def row(self, i, ident):
        return next((r for r in self.files(i)['files'] if r['id'] == ident), None)

    def export(self, ident):
        info = self.row(1, ident)
        m.require(info['state'] == 'complete' and int(info['verified_bytes']) == self.args.bytes, 'file incomplete')
        h = hashlib.sha256()
        for piece in range(self.args.bytes // PIECE):
            block = self.io(1, ident, piece, False)
            m.require(len(block) == PIECE, 'export length mismatch')
            h.update(block)
        return h.hexdigest()

    def run(self):
        try:
            self.report['inputs'] = m.validate_artifacts(self.args.binary, self.args.build_manifest, self.args.native_receipt)
            m.require(self.args.invitation.is_file() and self.args.invitation.stat().st_size <= 180000, 'invalid invitation input')
            m.require(m.digest(self.args.binary) == self.args.binary_sha256, 'binary binding mismatch')
            for i in range(2):
                self.start_client(i, True)
            self.channel = self.submit(0, '/create #native-release sender')['conversation']
            code = self.until(lambda: self.submit(0, '/invite')['output'].get('link'))
            preview = self.call(1, 'networks', request={'kind': 'inspect', 'code': code})['response']
            m.require(preview['kind'] == 'preview' and (not preview['preview']['newNetwork']), 'unexpected network')
            network = preview['preview']['network']['id']
            joined = self.call(1, 'networks', request={'kind': 'join', 'code': code, 'nickname': 'receiver', 'accepted_network': network, 'operation_id': uuid.uuid4().hex})['response']
            m.require(joined['kind'] == 'result' and joined['network'] == network and (joined['response']['conversation'] == self.channel), 'join mismatch')
            self.event('joined')
            self.chat('before')
            ident = uuid.uuid4().hex
            self.files(0, 'prepare', id=ident, conversation=self.channel, name='bounded.bin', size_bytes=str(self.args.bytes))
            h = hashlib.sha256()
            for piece in range(self.args.bytes // PIECE):
                block = hashlib.shake_256(f'bounded-native-{piece}'.encode()).digest(PIECE)
                h.update(block)
                self.io(0, ident, piece, True, block)
            expected = h.hexdigest()
            self.files(0, 'commit', id=ident)
            self.until(lambda: self.row(1, ident))
            started = time.monotonic()
            self.files(1, 'accept', id=ident)

            def partial():
                row = self.row(1, ident)
                n = int(row['verified_bytes'])
                m.require(n < self.args.bytes, 'file completed before required interruption')
                return n if n >= PIECE else None
            retained = self.until(partial, 60)
            self.stop(1, True)
            self.start_client(1, False)
            row = self.row(1, ident)
            m.require(int(row['verified_bytes']) >= retained, 'verified pieces lost')
            self.event('pieces_retained', bytes=retained)
            remaining = 180 - (time.monotonic() - started)
            m.require(remaining > 0, 'file completion deadline')
            last_progress = float('-inf')

            def completed():
                nonlocal last_progress
                row = self.row(1, ident)
                now = time.monotonic()
                if now - last_progress >= 5 or row['state'] == 'complete':
                    self.event('file_progress', **{key: row.get(key) for key in
                        ('state', 'verified_bytes', 'size_bytes', 'sources', 'verified_sources', 'completed_by')})
                    last_progress = now
                return row['state'] == 'complete'
            self.until(completed, remaining)
            completion = time.monotonic() - started
            m.require(completion <= 180, 'late file completion')
            m.require(self.export(ident) == expected, 'export hash mismatch')
            self.chat('after')
            before = self.history(1)
            self.stop(1)
            self.start_client(1, False)
            m.require(self.history(1) == before, 'history changed after orderly reopen')
            m.require(self.export(ident) == expected, 'reopened export hash mismatch')
            self.report['file_check'] = {'bytes': self.args.bytes, 'sha256': expected, 'completion_elapsed_seconds': completion, 'abrupt_stop': True, 'verified_pieces_retained': True, 'hash_verified_after_reopen': True}
            self.report['passed'] = True
        except Exception as e:
            self.report['error'] = type(e).__name__ + ': ' + str(e)
        finally:
            results = []
            for i, p, stop, log in reversed(self.children):
                if p.poll() is None:
                    results.append(m.stop_service(p, stop, 10))
                log.close()
            self.report['cleanup'] = results
            self.report['children_stopped'] = all((p.poll() is not None for _, p, _, _ in self.children))
            self.report['passed'] = self.report['passed'] and self.report['children_stopped'] and all((not r['forced'] and r['exit_code'] == 0 for r in results))
            if self.report['children_stopped']:
                for i in self.clients:
                    try:
                        shutil.rmtree(self.root / f'c{i}')
                    except OSError as error:
                        self.report.setdefault('cleanup_errors', []).append(type(error).__name__)
            self.report['temporary_profile_removed'] = all((not (self.root / f'c{i}').exists() for i in self.clients))
            self.report['passed'] = self.report['passed'] and self.report['temporary_profile_removed']
            self.report['elapsed_seconds'] = time.monotonic() - self.start
            self.report['finished_at'] = m.timestamp()
            self.report['binary_unchanged'] = m.digest(self.args.binary) == self.args.binary_sha256
            if 'inputs' in self.report:
                self.report['inputs_unchanged'] = all(
                    m.reference(path) == self.report['inputs'][name]
                    for name, path in [('binary', self.args.binary),
                                       ('build_manifest', self.args.build_manifest),
                                       ('native_receipt', self.args.native_receipt)])
                self.report['passed'] = self.report['passed'] and self.report['inputs_unchanged']
            self.report['passed'] = self.report['passed'] and self.report['binary_unchanged'] and (self.report['elapsed_seconds'] <= 600)
            (self.root / 'report.json').write_text(json.dumps(self.report, indent=2))
            print(json.dumps({'passed': self.report['passed'], 'error': self.report.get('error')}), flush=True)
        return 0 if self.report['passed'] else 1
if __name__ == '__main__':
    if sys.argv[1:] == ['_binary']:
        try:
            binary_worker()
        except Exception:
            print('binary exchange failed', file=sys.stderr)
            sys.exit(1)
    else:
        p = argparse.ArgumentParser()
        p.add_argument('--binary', type=Path, required=True)
        p.add_argument('--build-manifest', type=Path, required=True)
        p.add_argument('--native-receipt', type=Path, required=True)
        p.add_argument('--invitation', type=Path, required=True)
        p.add_argument('--output', type=Path, required=True)
        p.add_argument('--bytes', type=int, default=16777216)
        a = p.parse_args()
        a.binary_sha256 = m.digest(a.binary)
        validate_file_bytes(a.bytes, os.name)
        sys.exit(Journey(a).run())
