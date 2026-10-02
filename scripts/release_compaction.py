#!/usr/bin/env python3
"""Share identical extracted artifacts while retaining their original archives."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import time
import uuid
import zipfile

from release_coordinator import atomic_json, read_receipt


def identity(value):
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
            value.st_ctime_ns, stat.S_IMODE(value.st_mode), value.st_uid, value.st_gid)


def file_digest(path):
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('compaction requires regular artifacts')
        result = hashlib.file_digest(stream, 'sha256').hexdigest()
        if identity(before) != identity(os.fstat(stream.fileno())):
            raise ValueError('artifact changed during compaction')
    if path.is_symlink() or identity(before) != identity(path.stat()):
        raise ValueError('artifact path changed during compaction')
    return result, before


def compact_build(work, minimum_bytes=16 * 1024**2, verified_work=None):
    work = Path(work).resolve()
    receipt = work / 'receipt.json'
    proof = json.loads(receipt.read_text())
    if proof.get('stage') != 'build' or proof.get('passed') is not True:
        raise ValueError('compaction requires a completed native build')
    manifest = {key: proof[key] for key in ('release_id', 'sources')}
    verified, receipt_sha = read_receipt(receipt, manifest, proof['platform'], 'build')
    if verified != proof:
        raise ValueError('native receipt changed during compaction')
    archive = work / 'native.zip'
    references = [item for item in proof['evidence'] if item['path'] == 'native.zip']
    if len(references) != 1 or not archive.is_file() or archive.is_symlink():
        raise ValueError('compaction requires the original source-bound archive')
    if json.loads((work / 'extracted.json').read_text()).get('sha256') != references[0]['sha256']:
        raise ValueError('extracted artifacts belong to a different archive')
    archive_before = identity(archive.stat())
    native = work / 'native'
    if not native.is_dir() or native.is_symlink():
        raise ValueError('compaction requires the original extraction directory')
    native = native.resolve()
    groups = {}
    changes = []
    reclaimed = 0
    extras = []
    if verified_work is not None:
        verified_work = Path(verified_work).resolve()
        if not verified_work.is_relative_to(work.parent):
            raise ValueError('verified artifacts escape the release jobs')
        verification, _ = read_receipt(verified_work / 'receipt.json', manifest,
                                       proof['platform'], 'verify')
        extras = [(verified_work / item['path'], item['sha256'])
                  for item in verification['evidence']
                  if (verified_work / item['path']).stat().st_size >= minimum_bytes]
    with zipfile.ZipFile(archive) as bundle:
        entries = bundle.infolist()
        names = set()
        for item in entries:
            path = PurePosixPath(item.orig_filename)
            if (path.is_absolute() or '..' in path.parts or '\\' in item.orig_filename
                    or '\0' in item.orig_filename or ':' in item.orig_filename
                    or path.as_posix() in names
                    or (item.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError('unsafe retained artifact path')
            names.add(path.as_posix())
            if item.is_dir() or item.file_size < minimum_bytes:
                continue
            candidate = native / path
            if (candidate.is_symlink() or not candidate.is_file()
                    or not candidate.resolve().is_relative_to(native)):
                raise ValueError('retained artifact path is missing or changed')
            value = candidate.stat()
            if value.st_size != item.file_size:
                raise ValueError('retained artifact size differs from its original archive')
            key = (item.file_size, stat.S_IMODE(value.st_mode), value.st_uid, value.st_gid)
            groups.setdefault(key, []).append((candidate, item))
        for path, expected in extras:
            value = path.stat()
            if path.is_symlink() or not stat.S_ISREG(value.st_mode):
                raise ValueError('verified artifact path changed')
            key = (value.st_size, stat.S_IMODE(value.st_mode), value.st_uid, value.st_gid)
            groups.setdefault(key, []).append((path, expected))
        # Verify every candidate before the first replacement in this build.
        duplicates = {}
        for key, items in groups.items():
            if len(items) < 2:
                continue
            for path, item in items:
                expected, before = file_digest(path)
                if isinstance(item, str):
                    original = item
                else:
                    with bundle.open(item) as stream:
                        original = hashlib.file_digest(stream, 'sha256').hexdigest()
                if expected != original:
                    raise ValueError('retained artifact bytes differ from the verified archive')
                duplicates.setdefault((*key, expected), []).append((path, before))
        if identity(archive.stat()) != archive_before or hashlib.sha256(receipt.read_bytes()).hexdigest() != receipt_sha:
            raise ValueError('native archive or receipt changed during compaction')
        for key, items in duplicates.items():
            first, before = items[0]
            for path, previous in items[1:]:
                if first.is_symlink() or identity(first.stat()) != identity(before):
                    raise ValueError('canonical artifact changed during compaction')
                current = path.stat()
                if path.is_symlink():
                    raise ValueError('duplicate artifact path changed during compaction')
                if (before.st_dev, before.st_ino) == (current.st_dev, current.st_ino):
                    continue
                if identity(current) != identity(previous):
                    raise ValueError('duplicate artifact changed during compaction')
                temporary = path.parent / ('.compact-' + uuid.uuid4().hex)
                try:
                    os.link(first, temporary, follow_symlinks=False)
                    # link() changes the canonical inode's ctime and link count.
                    linked = first.stat()
                    if (linked.st_dev, linked.st_ino, linked.st_size, linked.st_mtime_ns,
                            stat.S_IMODE(linked.st_mode), linked.st_uid, linked.st_gid) != (
                            before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
                            stat.S_IMODE(before.st_mode), before.st_uid, before.st_gid):
                        raise ValueError('canonical artifact changed while linking')
                    if identity(path.stat()) != identity(previous) or path.is_symlink():
                        raise ValueError('duplicate artifact changed before replacement')
                    os.replace(temporary, path)
                    before = first.stat()
                    directory = os.open(path.parent, os.O_RDONLY)
                    try:
                        os.fsync(directory)
                    finally:
                        os.close(directory)
                    if previous.st_nlink == 1:
                        reclaimed += previous.st_blocks * 512
                    changes.append({'path': path.relative_to(work.parent).as_posix(),
                                    'canonical': first.relative_to(work.parent).as_posix(),
                                    'sha256': key[-1], 'bytes': previous.st_size})
                finally:
                    temporary.unlink(missing_ok=True)
    return {'schema': 1, 'release_id': proof['release_id'], 'sources': proof['sources'],
            'platform': proof['platform'], 'receipt_sha256': receipt_sha,
            'archive_sha256': references[0]['sha256'], 'original_archive_retained': True,
            'all_paths_retained': True, 'estimated_reclaimed_bytes': reclaimed,
            'changes': changes, 'completed_at': int(time.time())}


def compact(state, maximum_builds=8):
    import fcntl  # The release publisher and its filesystem are POSIX.
    state = Path(state)
    retained = state / 'maintenance/compaction'
    retained.mkdir(parents=True, exist_ok=True, mode=0o700)
    completed = []
    with (retained / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for work in sorted((state / 'jobs').iterdir()):
            if len(completed) >= maximum_builds:
                break
            marker = retained / (work.name + '.json')
            if marker.exists() or not all((work / name).is_file()
                    for name in ('receipt.json', 'native.zip', 'extracted.json')):
                continue
            proof = json.loads((work / 'receipt.json').read_text())
            if proof.get('stage') != 'build' or proof.get('passed') is not True:
                continue
            from release_pair import canonical
            key = hashlib.sha256(canonical([proof['release_id'], proof['platform'], 'verify'])).hexdigest()
            verified_work = state / 'jobs' / key
            if not (verified_work / 'receipt.json').is_file():
                verified_work = None
            # Inspect headers only to find possible duplicate bytes. An archive
            # must still pass its full source-bound digest before any mutation.
            with zipfile.ZipFile(work / 'native.zip') as archive:
                counts = {}
                for item in archive.infolist():
                    if not item.is_dir() and item.file_size >= 16 * 1024**2:
                        key = (item.file_size, item.CRC)
                        counts[key] = counts.get(key, 0) + 1
                if not any(value > 1 for value in counts.values()) and verified_work is None:
                    continue
            report = compact_build(work, verified_work=verified_work)
            atomic_json(marker, report)
            completed.append(report)
    return completed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--maximum-builds', type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.maximum_builds <= 256:
        parser.error('maximum builds must be between 1 and 256')
    print(json.dumps({'completed': compact(args.state, args.maximum_builds)}), flush=True)


if __name__ == '__main__':
    main()
