#!/usr/bin/env python3
"""Independent GChat daemons over the installed protected hosted service.

A 12-member smoke run does not qualify the 500-member campaign. Every daemon
uses its own retained encrypted profile. The operator allowlists only channel.json
and creates enabled; invitations and profiles remain private. No direct service
transport, synthetic receipt, changed routing or shared MLS identity is used.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import threading
import time

spec = importlib.util.spec_from_file_location('hosted_live', Path(__file__).with_name('hosted-live.py'))
live = importlib.util.module_from_spec(spec)
spec.loader.exec_module(live)

RECOVERY_POLICY = 'ordinary-message-10s-visible-membership-replay'


def membership_replay_passes(elapsed_ms, applied_progress, observation_seconds):
    return (0 <= elapsed_ms <= observation_seconds * 1000
            and (elapsed_ms <= 10000 or any(value > 0 for value in applied_progress)))


def verify_roster(room, count):
    members = room.get('members', [])
    return (room.get('active') is True and len(members) == count
            and len({m['id'] for m in members}) == count
            and sum(m.get('isSelf', False) for m in members) == 1)


def qualifies(report):
    observed = report.get('observations', {})
    return (report.get('requested_members') == 500 and report.get('passed') is True
            and report.get('recovery_policy') == RECOVERY_POLICY
            and report.get('latency_passed') is True and report.get('cleanup_passed') is True
            and report.get('resources_complete') is True
            and report.get('peak_active_profiles', 0) >= 500
            and observed.get('independent_members') == 500
            and all(observed.get(case) is True for case in
                    ('membership_catchup', 'offline_recovery', 'verified_file_resume', 'churn_and_exclusion'))
            and all(observed.get(case) == {'senders': 10, 'recipients_per_sender': 499}
                    for case in ('baseline', 'mixed_file')))


class Capacity(live.Journey):
    def __init__(self, args):
        self.report_lock = threading.RLock()
        super().__init__(args)
        self.names = ['alice', 'bob'] + [f'member-{i}' for i in range(2, args.members)]
        self.report.update(scope='independent GChat protected-network capacity',
                           requested_members=args.members, qualified_500=False,
                           startup_concurrency=args.startup_concurrency,
                           recovery_policy=RECOVERY_POLICY,
                           receipt_deadline_seconds=600, observations={})
        self.sampler_stop = threading.Event()
        self.file_resumed = threading.Event()
        self.sampled_profiles = set()
        self.resource_error = None
        self.peak_active_profiles = 0
        self.sampler = threading.Thread(target=self.sample, daemon=True)

    def note(self, step, **details):
        with self.report_lock:
            super().note(step, **details)

    def sample(self):
        try:
            self.sample_resources()
        except Exception as error:
            self.resource_error = str(error)

    def sample_resources(self):
        with (self.root / 'resources.jsonl').open('w') as stream:
            while not self.sampler_stop.is_set():
                rows = []
                for who, process in self.processes.copy().items():
                    try:
                        root = Path(f'/proc/{process.pid}')
                        status = dict(line.split(':', 1) for line in (root / 'status').read_text().splitlines())
                        io = dict((key, int(value)) for key, value in
                                  (line.split(':', 1) for line in (root / 'io').read_text().splitlines()))
                        stat = (root / 'stat').read_text().rpartition(')')[2].split()
                        rows.append({'client': who, 'pid': process.pid,
                                     'rss_kib': int(status['VmRSS'].split()[0]), 'io': io,
                                     'cpu_ticks': int(stat[11]) + int(stat[12])})
                        self.sampled_profiles.add(who)
                    except (FileNotFoundError, ProcessLookupError, KeyError):
                        continue
                self.peak_active_profiles = max(self.peak_active_profiles, len(rows))
                stream.write(json.dumps({'elapsed_seconds': time.monotonic() - self.started,
                                         'clock_ticks_per_second': os.sysconf('SC_CLK_TCK'),
                                         'clients': rows}) + '\n')
                stream.flush()
                self.sampler_stop.wait(10)

    def parallel(self, function, items):
        with ThreadPoolExecutor(max_workers=10) as pool:
            return list(pool.map(function, items))

    def file_action(self, who, action, file_id):
        result = super().file_action(who, action, file_id)
        if who == 'bob' and action == 'resume':
            self.file_resumed.set()
        return result

    def timed(self, step, started, target_ms, **details):
        elapsed = (time.monotonic() - started) * 1000
        self.note(step, duration_ms=round(elapsed), target_ms=target_ms,
                  within_target=elapsed <= target_ms, **details)

    def join(self, who, channel, link):
        nickname = 'newcomer' if who == 'bob' else who
        started = time.monotonic()
        joined = self.submit(who, f'/hosted join {link} #capacity {nickname}')
        assert joined['conversation'] == channel
        self.wait(f'{who} admitted', lambda: self.room(who, channel).get('active'), 120)
        self.timed('admission', started, 30000, client=who)

    def all_rosters(self, channel, names):
        count = len(names)
        self.parallel(lambda who: self.wait(f'{who} roster converged', lambda:
                      verify_roster(self.room(who, channel), count), 300), names)
        identities = []
        for who in names:
            room = self.room(who, channel)
            identities.append(next(m['id'] for m in room['members'] if m.get('isSelf')))
        assert len(set(identities)) == count, 'profiles must have independent MLS identities'
        self.report['observations']['independent_members'] = count
        self.note('independent rosters verified', members=count)

    def messages(self, channel, names, label):
        senders = names[2:12]
        bodies = {who: f'{label}:{who}' for who in senders}
        barrier = threading.Barrier(10)
        def send(who):
            barrier.wait(timeout=30)
            started = time.monotonic()
            self.submit(who, bodies[who], channel)
            self.timed('concurrent local feedback', started, 200, client=who, phase=label)
        started = time.monotonic()
        self.parallel(send, senders)
        def received(who):
            expected = set(bodies.values())
            self.wait(f'{label} plaintext {who}', lambda: expected <=
                      {m['body'] for m in self.history(who, channel)}, 600)
        self.parallel(received, names)
        self.note('ten-sender plaintext verified', phase=label, members=len(names),
                  duration_ms=round((time.monotonic() - started) * 1000))
        def acknowledged(who):
            self.wait(f'{label} covered delivery {who}', lambda: any(
                m['body'] == bodies[who] and m.get('delivery') == 'delivered'
                for m in self.history(who, channel)), 600)
        self.parallel(acknowledged, senders)
        self.note('ten-sender authenticated delivery', phase=label,
                  duration_ms=round((time.monotonic() - started) * 1000),
                  required_recipient_signatures=10 * (len(names) - 1))
        self.report['observations'][label] = {'senders': 10, 'recipients_per_sender': len(names)-1}

    def run(self):
        self.sampler.start()
        try:
            self.start('alice')
            channel = self.submit('alice', '/hosted create #capacity owner code')['conversation']
            assert channel.startswith('hosted/')
            self.private('channel.json', json.dumps({'channel': channel.split('/')[1]}))
            self.note('channel awaiting operator provisioning', channel=channel)
            self.wait('channel provisioned', lambda: (self.root / 'enabled').exists(), 600)
            self.wait('creator admitted', lambda: self.room('alice', channel).get('active'))
            links = self.submit('alice', '/links', channel)['output']['text']
            link = next(word for word in links.split() if word.startswith('gcoms-hosted:'))
            self.stop('alice')
            self.note('owner offline for all admissions')
            # Bootstrap independent profiles in bounded batches. Membership
            # writes remain sequential, with the same admission deadlines.
            for offset in range(1, len(self.names), self.args.startup_concurrency):
                batch = self.names[offset:offset + self.args.startup_concurrency]
                with ThreadPoolExecutor(max_workers=self.args.startup_concurrency) as pool:
                    list(pool.map(self.start, batch))
                for who in batch:
                    self.join(who, channel, link)
            self.start('alice')
            recovered = time.monotonic()
            progress = []
            def owner_current():
                room = self.room('alice', channel)
                status = room.get('catchUp')
                if status is not None:
                    applied = status['appliedRecords']
                    if not progress or progress[-1] != applied:
                        progress.append(applied)
                        self.note('owner membership catch-up progress', applied_records=applied)
                return verify_roster(room, self.args.members) and status is None
            # Ordinary message recovery below keeps its ten-second target.
            # A small room can also have a long membership backlog. Classify
            # replay by observed work, rather than the room's nominal capacity.
            observation_seconds = 1800 if self.args.members > 32 else 300
            self.wait('owner recovered complete roster', owner_current, observation_seconds)
            elapsed_ms = (time.monotonic() - recovered) * 1000
            assert membership_replay_passes(elapsed_ms, progress, observation_seconds), \
                'slow membership replay needs visible applied progress within the observation bound'
            self.note('membership backlog recovered', duration_ms=round(elapsed_ms),
                      observation_deadline_seconds=observation_seconds,
                      progress_required=elapsed_ms > 10000, applied_progress=progress)
            self.report['observations']['membership_catchup'] = True
            self.all_rosters(channel, self.names)
            self.messages(channel, self.names, 'baseline')
            # Every expected receipt remains outstanding while this actual member is offline.
            self.stop('bob')
            self.submit('alice', 'capacity-offline-message', channel)
            self.wait('offline message accepted', lambda: any(
                m['body'] == 'capacity-offline-message' and m.get('delivery') == 'service_accepted'
                for m in self.history('alice', channel)), 120)
            assert not any(m['body'] == 'capacity-offline-message' and m.get('delivery') == 'delivered'
                           for m in self.history('alice', channel))
            self.start('bob')
            recovered = time.monotonic()
            self.wait('offline plaintext recovered', lambda: any(
                m['body'] == 'capacity-offline-message' for m in self.history('bob', channel)), 120)
            self.timed('offline plaintext recovery after network ready', recovered, 10000)
            self.wait('offline authenticated delivery', lambda: any(
                m['body'] == 'capacity-offline-message' and m.get('delivery') == 'delivered'
                for m in self.history('alice', channel)), 600)
            self.report['observations']['offline_recovery'] = True
            with ThreadPoolExecutor(max_workers=1) as pool:
                transfer = pool.submit(self.file_journey, channel)
                self.wait('file resumed for mixed traffic', self.file_resumed.is_set, 300)
                partial = next(f for f in self.files('bob', channel) if f['name'] == 'hosted.bin')
                assert 0 < int(partial['verified_bytes']) < 16 * 1024 * 1024
                self.note('mixed traffic partial file', verified_bytes=int(partial['verified_bytes']))
                self.messages(channel, self.names, 'mixed_file')
                transfer.result()
            self.report['observations']['verified_file_resume'] = True
            victim = self.names[-1]
            victim_id = next(m['id'] for m in self.room(victim, channel)['members'] if m.get('isSelf'))
            self.submit('alice', f'/kick {victim} capacity churn', channel)
            self.wait('removed member inactive', lambda: self.room(victim, channel).get('active') is False, 300)
            self.submit('alice', 'after-capacity-removal', channel)
            self.wait('post-removal recipient delivery', lambda: any(
                m['body'] == 'after-capacity-removal' and m.get('delivery') == 'delivered'
                for m in self.history('alice', channel)), 600)
            assert not any(m['body'] == 'after-capacity-removal' for m in self.history(victim, channel))
            replacement = 'replacement'
            self.start(replacement)
            self.join(replacement, channel, link)
            current = self.names[:-1] + [replacement]
            self.all_rosters(channel, current)
            replacement_id = next(m['id'] for m in self.room(replacement, channel)['members'] if m.get('isSelf'))
            assert replacement_id != victim_id
            assert not any(m['body'] == 'after-capacity-removal' for m in self.history(replacement, channel))
            self.report['observations']['churn_and_exclusion'] = True
            self.report['passed'] = True
            self.report['latency_passed'] = all(s['within_target'] for s in self.report['steps'] if 'within_target' in s)
        except Exception as error:
            self.report['error'] = str(error)
            self.note('capacity failed', error=str(error))
            raise
        finally:
            self.sampler_stop.set()
            self.sampler.join(timeout=15)
            self.report['resources_complete'] = (not self.sampler.is_alive()
                and self.resource_error is None and set(self.names) <= self.sampled_profiles)
            self.report['resource_error'] = self.resource_error
            self.report['peak_active_profiles'] = self.peak_active_profiles
            cleanup_errors = []
            for who in list(self.processes):
                try:
                    self.stop(who)
                except Exception as error:
                    cleanup_errors.append(f'{who}: {error}')
            self.report['cleanup_passed'] = not cleanup_errors and not self.processes
            self.report['cleanup_errors'] = cleanup_errors
            self.report['qualified_500'] = qualifies(self.report)
            self.note('capacity finished', passed=self.report['passed'],
                      latency_passed=self.report['latency_passed'], qualified_500=self.report['qualified_500'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--gchat', type=Path, required=True)
    parser.add_argument('--probe', type=Path, required=True)
    parser.add_argument('--invitation-file', type=Path, required=True)
    parser.add_argument('--members', type=int, choices=(12, 500), required=True)
    parser.add_argument('--startup-concurrency', type=int, choices=(1, 4), default=1)
    args = parser.parse_args()
    args.gchat = args.gchat.resolve()
    args.probe = args.probe.resolve()
    os.umask(0o077)
    Capacity(args).run()
