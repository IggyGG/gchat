#!/usr/bin/env python3
"""Real GChat daemon/IPC hosted journey on the installed protected network.

The operator provisions only the emitted channel ID, then creates root/enabled.
Profiles and evidence are retained; owned daemon processes are stopped on exit.
No route overrides, direct-HTTP messaging or fixture transports are available.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import time


class Journey:
    def __init__(self, args):
        self.args = args
        self.root = args.root.resolve()
        self.root.mkdir(mode=0o700)
        self.processes = {}
        self.started = time.monotonic()
        self.report = {
            'schema': 1, 'passed': False, 'transport': 'installed protected network',
            'artifacts': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (args.gchat, args.probe)}, 'steps': [],
        }
        self.secret = secrets.token_urlsafe(32)
        self.private('passphrase', self.secret)

    def private(self, name, value):
        path = self.root / name
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write(value)

    def note(self, step, **details):
        item = {'step': step, 'elapsed_ms': round((time.monotonic() - self.started) * 1000), **details}
        self.report['steps'].append(item)
        print(json.dumps(item), flush=True)
        (self.root / 'result.json').write_text(json.dumps(self.report, indent=2) + '\n')

    def start(self, who):
        folder = self.root / who
        folder.mkdir(mode=0o700, exist_ok=True)
        (folder / 'fixtures').mkdir(mode=0o700, exist_ok=True)
        argv = [str(self.args.gchat), 'daemon', '--home', str(folder),
                '--store', str(folder / 'profile'), '--chat-archive', str(folder / 'archive'),
                '--socket', str(folder / 'protocol.sock'), '--listen', '127.0.0.1:0',
                '--passphrase-file', str(self.root / 'passphrase'),
                '--chat-passphrase-file', str(self.root / 'passphrase'), '--gc2-carrier']
        if not (folder / 'profile').exists():
            argv.append('--create')
        with (folder / 'daemon.log').open('ab') as log:
            process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT,
                                       env=dict(os.environ, TOKIO_WORKER_THREADS='2'))
        self.processes[who] = process
        self.wait(f'{who} daemon ready', lambda: self.ready(who), timeout=180)

    def ready(self, who):
        process = self.processes[who]
        if process.poll() is not None:
            raise RuntimeError(f'{who} daemon exited {process.returncode}; retained daemon.log')
        if not (self.root / who / 'protocol.chat').exists():
            return False
        try:
            result = self.request(who, {'kind': 'snapshot'})
            return result['kind'] == 'snapshot'
        except (RuntimeError, subprocess.TimeoutExpired):
            return False

    def stop(self, who):
        process = self.processes.pop(who, None)
        if process is None:
            return
        process.terminate()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    def action(self, who, action):
        folder = self.root / who
        result = subprocess.run([str(self.args.probe), str(folder / 'protocol.chat'),
                                 str(folder / 'fixtures')], input=json.dumps(action),
                                text=True, capture_output=True, timeout=180)
        if not result.stdout.strip():
            raise RuntimeError(f'{who} probe returned no JSON ({result.returncode})')
        value = json.loads(result.stdout)
        if not value['ok']:
            raise RuntimeError(value.get('error', 'probe failed'))
        return value['value']

    def request(self, who, request):
        return self.action(who, {'action': 'request', 'request': request})

    def submit(self, who, text, channel=None):
        return self.request(who, {'kind': 'submit', 'operation_id': secrets.token_hex(16),
                                 'conversation': channel, 'text': text})

    def room(self, who, channel):
        snapshot = self.request(who, {'kind': 'snapshot'})['snapshot']
        return next((c for c in snapshot['conversations'] if c['id'] == channel), {})

    def history(self, who, channel):
        return self.request(who, {'kind': 'history', 'conversation': channel,
                                 'before': None, 'limit': 200})['page']['messages']

    def files(self, who, channel):
        return self.request(who, {'kind': 'files', 'request': {
            'action': 'list', 'conversation': channel}})['snapshot']['files']

    def file_action(self, who, action, file_id):
        return self.request(who, {'kind': 'files', 'request': {'action': action, 'id': file_id}})

    def file_journey(self, channel):
        # A moderated recipient must still authenticate verified completion.
        self.submit('alice', '/mode -v newcomer', channel)
        self.wait('file recipient unvoiced', lambda: any(
            m['nickname'] == 'newcomer' and m['capabilities'] == ['channel.member']
            for m in self.room('bob', channel)['members']))
        generated = self.action('alice', {'action': 'generate', 'name': 'hosted.bin',
                                          'size': 16 * 1024 * 1024, 'seed': 927})
        file_id = secrets.token_hex(16)
        self.action('alice', {'action': 'import', 'id': file_id,
                              'conversation': channel, 'name': 'hosted.bin'})
        incoming = self.wait('authenticated hosted file offer', lambda: next(
            (f for f in self.files('bob', channel) if f['name'] == 'hosted.bin'), None), 300)
        receiver_id = incoming['id']
        self.file_action('bob', 'accept', receiver_id)
        partial = self.wait('partial verified file', lambda: next(
            (f for f in self.files('bob', channel) if f['id'] == receiver_id
             and 0 < int(f['verified_bytes']) < generated['size']), None), 300)
        self.file_action('bob', 'pause', receiver_id)
        self.note('file paused', verified_bytes=int(partial['verified_bytes']))
        self.stop('bob')
        self.start('bob')
        retained = next(f for f in self.files('bob', channel) if f['id'] == receiver_id)
        assert int(retained['verified_bytes']) >= int(partial['verified_bytes'])
        assert retained['state'] == 'paused'
        resumed = time.monotonic()
        self.file_action('bob', 'resume', receiver_id)
        self.wait('whole file verified after resume', lambda: any(
            f['id'] == receiver_id and f['state'] == 'complete'
            and int(f['verified_bytes']) == generated['size']
            for f in self.files('bob', channel)), 300)
        exported = self.action('bob', {'action': 'export', 'id': receiver_id,
                                       'name': 'verified.bin', **generated})
        assert exported['verified']
        self.wait('unvoiced authenticated file completion', lambda: any(
            f['name'] == 'hosted.bin' and f['completed_by'] >= 1
            for f in self.files('alice', channel)), 120)
        self.note('file journey complete', size=generated['size'], sha256=generated['sha256'],
                  resume_ms=round((time.monotonic() - resumed) * 1000))

    def wait(self, label, predicate, timeout=120):
        started = time.monotonic()
        while time.monotonic() - started < timeout:
            result = predicate()
            if result:
                self.note(label, duration_ms=round((time.monotonic() - started) * 1000))
                return result
            time.sleep(1)
        raise TimeoutError(label)

    def run(self):
        try:
            self.start('alice')
            created = self.submit('alice', '/hosted create #qualification owner code')
            channel = created['conversation']
            assert channel.startswith('hosted/')
            self.private('channel.json', json.dumps({'channel': channel.split('/')[1]}))
            self.note('channel awaiting operator provisioning', channel=channel)
            self.wait('channel provisioned', lambda: (self.root / 'enabled').exists(), 600)
            self.wait('creator admitted', lambda: self.room('alice', channel).get('active'))
            self.submit('alice', '/topic authenticated offline handoff', channel)
            self.wait('topic accepted', lambda: self.room('alice', channel).get('topic') == 'authenticated offline handoff')
            links = self.submit('alice', '/links', channel)['output']['text']
            link = next(word for word in links.split() if word.startswith('gcoms-hosted:'))
            self.stop('alice')
            self.note('creator offline')
            self.start('bob')
            joined = self.submit('bob', f'/hosted join {link} #qualification newcomer')
            assert joined['conversation'] == channel
            self.wait('offline-owner newcomer admitted', lambda: self.room('bob', channel).get('active'))
            assert self.room('bob', channel)['topic'] == 'Topic pending'
            self.note('offline newcomer topic pending')
            self.start('alice')
            self.wait('authenticated topic handoff', lambda: self.room('bob', channel).get('topic') == 'authenticated offline handoff')
            started = time.monotonic()
            self.submit('bob', 'protected-hosted-message', channel)
            self.note('local message feedback', duration_ms=round((time.monotonic() - started) * 1000), target_ms=200, within_target=time.monotonic() - started <= 0.2)
            self.wait('peer plaintext received', lambda: any(m['body'] == 'protected-hosted-message' for m in self.history('alice', channel)))
            self.wait('authenticated recipient delivery', lambda: any(m['body'] == 'protected-hosted-message' and m.get('delivery') == 'delivered' for m in self.history('bob', channel)))
            self.note('online delivery and receipt', duration_ms=round((time.monotonic() - started) * 1000), target_ms=5000, within_target=time.monotonic() - started <= 5)
            self.submit('alice', '/mode +m', channel)
            self.wait('moderation converged', lambda: self.room('bob', channel).get('policy', {}).get('moderated'))
            try:
                self.submit('bob', 'must-not-pass-moderation', channel)
            except RuntimeError:
                self.note('unvoiced send refused')
            else:
                raise AssertionError('unvoiced send unexpectedly admitted')
            self.submit('alice', '/mode +v newcomer', channel)
            self.wait('voice converged', lambda: any(m['nickname'] == 'newcomer' and 'channel.voice' in m['capabilities'] for m in self.room('bob', channel)['members']))
            self.submit('bob', '/notice authenticated notice', channel)
            self.wait('voiced notice received', lambda: any(m['body'] == 'authenticated notice' and m.get('messageKind') == 'notice' for m in self.history('alice', channel)))
            self.stop('bob')
            self.submit('alice', 'retained-while-offline', channel)
            time.sleep(3)
            assert all(m.get('delivery') != 'delivered' for m in self.history('alice', channel) if m['body'] == 'retained-while-offline')
            self.start('bob')
            self.wait('offline message recovered', lambda: any(m['body'] == 'retained-while-offline' for m in self.history('bob', channel)))
            self.wait('recovered recipient acknowledged', lambda: any(m['body'] == 'retained-while-offline' and m.get('delivery') == 'delivered' for m in self.history('alice', channel)))
            self.file_journey(channel)
            self.report['passed'] = True
            self.note('journey passed')
        except Exception as error:
            self.report['error'] = str(error)
            self.note('journey failed', error=str(error))
            raise
        finally:
            for who in list(self.processes):
                self.stop(who)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--gchat', type=Path, required=True)
    parser.add_argument('--probe', type=Path, required=True)
    args = parser.parse_args()
    args.gchat = args.gchat.resolve()
    args.probe = args.probe.resolve()
    os.umask(0o077)
    Journey(args).run()
