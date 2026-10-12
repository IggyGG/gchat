"""Supervise the cluster Android agent lane from the existing coordinator.

This lane serves boo.gcoms.agent. It has its own component graph and cluster
receipts; the boo.gchat.app store submission worker remains independent.
"""
import json
import os
from pathlib import Path
import subprocess
import time


class AndroidAgent:
    def __init__(self, state, config=None):
        self.state = Path(state) / 'android-agent'
        self.config = config
        self.pending = None
        self.last = None
        if config is None:
            return
        argv = config.get('command')
        if (not isinstance(argv, list) or not argv or any(not isinstance(v, str) or not v for v in argv)
                or not Path(argv[0]).is_absolute()):
            raise ValueError('Android agent coordinator command must be an explicit argv array')
        timeout = config.get('timeout_seconds', 240)
        if type(timeout) is not int or not 30 <= timeout <= 300:
            raise ValueError('Android agent reconciliation timeout must be 30..300 seconds')
        self.timeout = timeout
        self.state.mkdir(parents=True, exist_ok=True)

    def close(self):
        if self.pending is None:
            return
        from release_coordinator import stop_worker
        try:
            if self.pending['process'].poll() is None:
                stop_worker(self.pending['process'])
        finally:
            self.pending['log'].close()
            self.pending = None

    def tick(self):
        if self.config is None:
            return
        from release_coordinator import atomic_json
        if self.pending is not None:
            item = self.pending
            process = item['process']
            code = process.poll()
            if code is None:
                if time.monotonic() < item['deadline']:
                    return
                self.close()
                self.last = {'state': 'observation_failed', 'reason': 'reconciliation_timeout',
                             'observed_at': int(time.time())}
            else:
                item['log'].close()
                self.pending = None
                try:
                    # Only the small cluster status is public. Detailed errors,
                    # requests and credential-bearing process output stay private.
                    if code or item['path'].stat().st_size > 64 * 1024:
                        raise ValueError('cluster reconciliation failed')
                    value = json.loads(item['path'].read_text())
                    if value.get('schema') != 1 or value.get('execution') != 'kubernetes':
                        raise ValueError('cluster reconciliation omitted its status binding')
                    self.last = {key: value[key] for key in ('schema', 'execution', 'state', 'observed_at', 'active')}
                except (ValueError, OSError, KeyError):
                    self.last = {'state': 'observation_failed', 'reason': 'cluster_reconciliation_failed',
                                 'observed_at': int(time.time())}
            atomic_json(self.state / 'status.json', self.last)
            return
        path = self.state / 'reconciliation.log'
        log = path.open('wb')
        os.chmod(path, 0o600)
        try:
            process = subprocess.Popen(self.config['command'], stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
        except OSError:
            log.close()
            raise
        self.pending = {'process': process, 'log': log, 'path': path,
                        'deadline': time.monotonic() + self.timeout}

    def progress(self):
        if self.config is None:
            return None
        value = dict(self.last or {'state': 'starting'})
        value['observing'] = self.pending is not None
        return value
