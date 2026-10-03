"""Keep one serial rollout worker separate from the sole ledger writer."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

from release_pair import canonical


class DeploymentRunner:
    def __init__(self, state, timeout=1800):
        self.state = Path(state)
        self.timeout = timeout
        self.pending = None

    def close(self):
        if self.pending is None:
            return
        item = self.pending
        process = item['process']
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        item['log'].close()
        self.pending = None

    def step(self, manifest, config):
        from release_coordinator import atomic_json
        if self.pending is not None:
            item = self.pending
            process = item['process']
            if process.poll() is None:
                if time.monotonic() >= item['deadline']:
                    self.close()
                    raise ValueError('deployment step exceeded its deadline; retained intent needs observation')
                return
            item['log'].close()
            self.pending = None
            if process.returncode or not item['output'].is_file():
                raise ValueError('deployment step failed or returned no bound receipt')
            proof = json.loads(item['output'].read_text())
            if (proof.get('schema') != 1 or proof.get('release_id') != item['manifest']['release_id']
                    or proof.get('sources') != item['manifest']['sources']
                    or proof.get('revision') != item['revision']
                    or proof.get('step_completed') is not True or type(proof.get('deployed')) is not bool):
                raise ValueError('deployment step receipt differs from its frozen inputs')
            return  # A completed step is observed before the next serial step.
        revision = hashlib.sha256(canonical(config)).hexdigest()
        work = self.state / 'deployment' / manifest['release_id'] / 'steps' / uuid.uuid4().hex
        work.mkdir(parents=True)
        source, inventory = work / 'candidate.json', work / 'inventory.json'
        atomic_json(source, manifest)
        atomic_json(inventory, config)
        output = work / 'receipt.json'
        argv = [sys.executable, str(Path(__file__).with_name('release_deployment.py')),
                '--state', str(self.state), '--manifest', str(source), '--inventory', str(inventory),
                '--receipt', str(output)]
        log = (work / 'worker.log').open('xb')
        started = int(time.time())
        try:
            process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        except OSError:
            log.close()
            raise
        self.pending = {'process': process, 'log': log, 'output': output, 'manifest': manifest,
                        'revision': revision, 'deadline': time.monotonic() + self.timeout,
                        'started_at': started, 'deadline_at': started + self.timeout}
        atomic_json(work / 'request.json', {'release_id': manifest['release_id'], 'sources': manifest['sources'],
                    'revision': revision, 'started_at': started, 'deadline_at': started + self.timeout})

    def progress(self):
        if self.pending is None:
            return None
        item = self.pending
        value = {'release_id': item['manifest']['release_id'], 'started_at': item['started_at'],
                 'deadline_at': item['deadline_at'], 'process_alive': item['process'].poll() is None}
        path = self.state / 'deployment' / value['release_id'] / 'progress.json'
        if path.is_file():
            recorded = json.loads(path.read_text())
            value.update({key: recorded[key] for key in ('target', 'stage', 'started_at', 'deadline_at')
                          if key in recorded})
        return value
