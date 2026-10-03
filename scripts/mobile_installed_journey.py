"""Actual mobile upgrade and covered-network journey using an installed UI."""
import argparse
import hashlib
import shutil
import time
import uuid

from mobile_acceptance_inputs import require
from release_network_canary import module

network = module('test-native-network')
smoke = network.m


class MobileJourney:
    def __init__(self, current, baseline, peer, invitation, output, manifest):
        self.current, self.baseline, self.manifest = current, baseline, manifest
        self.start = time.monotonic()
        self.deadline = self.start + 600
        args = argparse.Namespace(binary=peer['binary'], build_manifest=peer['build_manifest'],
            native_receipt=peer['native_receipt'], binary_sha256=smoke.digest(peer['binary']),
            invitation=invitation, output=output / 'peer', bytes=16777216)
        self.peer = network.Journey(args)
        self.rollback = {'schema': 1, 'passed': False, 'phases': [], 'events': []}
        self.report = {'schema': 1, 'passed': False, 'events': [],
            'inputs': {'sources': manifest['sources']}, 'binary_sha256': current['binary_sha256']}
        self.cleanup_report = None
        self.stage = 'baseline-start'

    def until(self, fn, maximum=120):
        end = min(self.deadline, time.monotonic() + maximum)
        while time.monotonic() < end:
            result = fn()
            if result is not None and result is not False:
                require(time.monotonic() <= end, 'late installed mobile result')
                return result
            time.sleep(0.2)
        raise TimeoutError('original installed mobile deadline')

    def ack(self, ui, phase, output):
        for sender in (0, 1):
            body = 'mr-' + uuid.uuid4().hex
            if sender == 0:
                self.peer.submit(0, body)
                self.until(lambda: ui.received(body))
                def delivered():
                    rows = [row for row in self.peer.history(0) if row['body'] == body]
                    require(len(rows) <= 1, 'duplicate covered mobile message')
                    return len(rows) == 1 and rows[0]['mine'] and rows[0]['delivery'] == 'delivered'
                self.until(delivered)
            else:
                ui.send(body)
                def received():
                    rows = [row for row in self.peer.history(0) if row['body'] == body]
                    require(len(rows) <= 1, 'duplicate covered mobile message')
                    return len(rows) == 1 and not rows[0]['mine']
                self.until(received)
                self.until(lambda: ui.delivered(body))
            output['events'].append({'event': 'authenticated_ack', 'sender': sender, 'phase': phase})

    def offer(self, name, size):
        ident = uuid.uuid4().hex
        self.peer.files(0, 'prepare', id=ident, conversation=self.peer.channel, name=name, size_bytes=str(size))
        expected = hashlib.sha256()
        for piece in range(size // network.PIECE):
            data = hashlib.shake_256(('mobile-covered-piece-' + str(piece)).encode()).digest(network.PIECE)
            expected.update(data)
            self.peer.io(0, ident, piece, True, data)
        self.peer.files(0, 'commit', id=ident)
        return ident, expected.hexdigest()

    def run(self, ui):
        self.peer.start_client(0, True)
        self.peer.channel = self.peer.submit(0, '/create #mobile-release sender')['conversation']
        code = self.peer.invitation()
        ui.install(self.baseline)
        ui.unlock(create=True)
        ui.join(code)
        identity = ui.identity()
        self.ack(ui, 'baseline-initial', self.rollback)
        self.stage = 'baseline-cache'
        cache_name = 'baseline-cache.bin'
        cache_id, expected = self.offer(cache_name, network.PIECE)
        ui.file_action(cache_name, 'Download & share')
        self.until(lambda: ui.progress(cache_name, network.PIECE) == network.PIECE)
        require(ui.export(cache_name, 'initial') == expected, 'initial installed cached export differs')
        encrypted = ui.cache_hash(cache_id)
        require(encrypted != expected, 'cache piece is not the plaintext export')
        retained_bodies = [row['body'] for row in self.peer.history(0) if row['body'].startswith('mr-')]
        for phase, item in (('upgraded', self.current), ('baseline', self.baseline), ('restored', self.current)):
            self.stage = 'replacement-' + phase
            ui.install(item)
            ui.unlock()
            require(ui.identity() == identity, 'mobile cryptographic identity changed on replacement')
            ui.history(retained_bodies)
            require(ui.cache_hash(cache_id) == encrypted, 'retained encrypted mobile cache changed')
            require(ui.export(cache_name, phase) == expected, 'cached export after replacement differs')
            self.ack(ui, phase, self.rollback)
            self.rollback['phases'].append({'phase': phase, 'binary_sha256': item['binary_sha256'],
                'same_identity': True, 'history_retained': True, 'cache_sha256': expected,
                'encrypted_cache_sha256': encrypted, 'authenticated_bidirectional_ack': True})
            retained_bodies = [row['body'] for row in self.peer.history(0) if row['body'].startswith('mr-')]
        self.rollback['elapsed_seconds'] = time.monotonic() - self.start
        require(self.rollback['elapsed_seconds'] <= 600, 'original mobile rollback deadline')
        self.rollback['passed'] = True

        # This is the same independent 600-second network / 360-second file
        # contract as desktop acceptance. No time is borrowed from rollback.
        started = time.monotonic()
        self.deadline = started + 600
        self.peer.deadline = self.deadline
        self.stage = 'network-before'
        self.ack(ui, 'before', self.report)
        name = 'bounded-mobile.bin'
        ident, expected = self.offer(name, 16777216)
        file_started = time.monotonic()
        self.stage = 'file-interruption'
        ui.file_action(name, 'Download & share')
        def partial():
            value = ui.progress(name, 16777216)
            return value if value is not None and 0 < value < 16777216 else None
        retained = self.until(partial, 180)
        ui.stop()
        ui.unlock()
        require(ui.identity() == identity, 'mobile identity changed after interrupted transfer')
        resumed = self.until(lambda: ui.progress(name, 16777216), 30)
        require(resumed >= retained, 'verified mobile pieces were lost after force-stop')
        remaining = 360 - (time.monotonic() - file_started)
        require(remaining > 0, 'original mobile file completion deadline')
        self.stage = 'file-resume'
        self.until(lambda: ui.progress(name, 16777216) == 16777216, remaining)
        completion = time.monotonic() - file_started
        require(completion <= 360, 'late installed mobile file completion')
        require(ui.export(name, 'network') == expected, 'installed mobile export hash differs')
        self.stage = 'network-after'
        self.ack(ui, 'after', self.report)
        ui.stop()
        ui.unlock()
        self.stage = 'final-reopen'
        require(ui.identity() == identity, 'mobile identity changed after final reopen')
        require(ui.progress(name, 16777216) == 16777216, 'verified completed file lost on reopen')
        require(ui.export(name, 'reopened') == expected, 'reopened mobile export hash differs')
        self.ack(ui, 'reopened', self.report)
        self.report.update(file_check={'bytes': 16777216, 'sha256': expected,
            'completion_elapsed_seconds': completion, 'abrupt_stop': True,
            'verified_pieces_retained': True, 'hash_verified_after_reopen': True},
            elapsed_seconds=time.monotonic() - started, passed=True)
        require(self.report['elapsed_seconds'] <= 600, 'original mobile network journey deadline')
        self.stage = 'complete'

    def cleanup(self, ui):
        errors, results = [], []
        # Cleanup has its own bounded allowance even after the journey deadline.
        self.deadline = time.monotonic() + 120
        try:
            self.cleanup_report = ui.cleanup() if ui is not None else {'passed': False}
        except Exception as error:
            errors.append(type(error).__name__)
            self.cleanup_report = {'passed': False}
        for _, process, stop, log in reversed(self.peer.children):
            try:
                if process.poll() is None:
                    results.append(smoke.stop_service(process, stop, 10))
            except Exception as error:
                errors.append(type(error).__name__)
                try:
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=10)
                except Exception as failure:
                    errors.append(type(failure).__name__)
            finally:
                log.close()
        stopped = all(process.poll() == 0 for _, process, _, _ in self.peer.children)
        if stopped:
            for i in self.peer.clients:
                try:
                    shutil.rmtree(self.peer.root / f'c{i}')
                except OSError as error:
                    errors.append(type(error).__name__)
        removed = all(not (self.peer.root / f'c{i}').exists() for i in self.peer.clients)
        clean = stopped and removed and not errors and self.cleanup_report.get('passed') is True and all(
            item['stopped'] and not item['forced'] and item['exit_code'] == 0 for item in results)
        self.rollback.update(cleanup_complete=clean, profiles_removed=clean,
                             binaries_unchanged=False)
        self.report.update(children_stopped=stopped,
            temporary_profile_removed=removed,
            binary_unchanged=False, inputs_unchanged=False)
        # The caller independently rehashes every retained application after
        # cleanup and applies that verdict to both reports.
        self.rollback['passed'] = self.rollback['passed'] and clean
        self.report['passed'] = self.report['passed'] and clean
        return errors
