#!/usr/bin/env python3
"""Maintain node disk headroom using unused runtime images and Docker build images."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

MINIMUM_FREE_PERCENT = 17
ENDPOINT = 'unix:///run/containerd/containerd.sock'
DOCKER_ENDPOINT = 'unix:///run/docker.sock'
DOCKER_MINIMUM_IMAGE_AGE = '1h'


def maintain(stat=os.statvfs, run=subprocess.run, exists=os.path.exists):
    before = stat('/')
    total = before.f_blocks * before.f_frsize
    available = before.f_bavail * before.f_frsize
    result = {'schema': 1, 'at': int(time.time()), 'minimum_free_percent': MINIMUM_FREE_PERCENT,
        'total_bytes': total, 'before_available_bytes': available, 'unused_image_cleanup': False,
        'docker_dangling_image_cleanup': False}
    if available * 100 < total * MINIMUM_FREE_PERCENT:
        cleaned = run(['/usr/bin/crictl', '--runtime-endpoint', ENDPOINT,
            '--image-endpoint', ENDPOINT, 'rmi', '--prune'], capture_output=True, timeout=120)
        if cleaned.returncode:
            raise RuntimeError('Unused container-image cleanup failed')
        result['unused_image_cleanup'] = True
        result['removed_images'] = cleaned.stdout.count(b'Deleted:')
    after = stat('/')
    if (after.f_bavail * after.f_frsize * 100 < total * MINIMUM_FREE_PERCENT
            and exists('/usr/bin/docker') and exists('/run/docker.sock')):
        cleaned = run(['/usr/bin/docker', '--host', DOCKER_ENDPOINT, 'image', 'prune',
            '--force', '--filter', 'until=' + DOCKER_MINIMUM_IMAGE_AGE],
            capture_output=True, timeout=120)
        if cleaned.returncode:
            raise RuntimeError('Unused dangling Docker-image cleanup failed')
        result['docker_dangling_image_cleanup'] = True
        result['docker_minimum_image_age'] = DOCKER_MINIMUM_IMAGE_AGE
        result['docker_removed_images'] = cleaned.stdout.count(b'deleted:')
        after = stat('/')
    result['after_available_bytes'] = after.f_bavail * after.f_frsize
    result['headroom_ok'] = result['after_available_bytes'] * 100 >= total * MINIMUM_FREE_PERCENT
    return result


def main():
    with Path('/run/gchat-node-image-headroom/lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = maintain()
        path = Path('/var/lib/gchat-node-image-headroom/status.json')
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(result, sort_keys=True) + '\n')
        temporary.chmod(0o600)
        os.replace(temporary, path)
        print(json.dumps(result, sort_keys=True))
        return 0 if result['headroom_ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
