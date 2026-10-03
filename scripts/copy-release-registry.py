#!/usr/bin/env python3
"""Copy a quiesced registry into a new volume, verifying every byte and mode.

The source is read-only. This tool never removes or changes either volume's
existing files. Switch the Deployment only after this receipt passes and the
original registry writer has stopped. Keep the original PVC for rollback.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inventory(root):
    require(root.is_dir() and not root.is_symlink(), 'registry root must be a real directory')
    result = {}
    for directory, names, files in os.walk(root, followlinks=False):
        for name in sorted(names + files):
            path = Path(directory) / name
            before = path.lstat()
            require(stat.S_ISDIR(before.st_mode) or stat.S_ISREG(before.st_mode),
                    'registry contains a link or nonregular entry')
            entry = {'mode': stat.S_IMODE(before.st_mode), 'directory': stat.S_ISDIR(before.st_mode)}
            if not entry['directory']:
                with path.open('rb') as stream:
                    entry['sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
                after = path.lstat()
                require((before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                        (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
                        'registry source changed while hashing')
                entry['size'] = before.st_size
            result[path.relative_to(root).as_posix()] = entry
    require(result and any(name.startswith('docker/registry/v2/') for name in result),
            'source is not a populated distribution registry')
    return result


def fingerprint(entries):
    return hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def copy(source, destination, quiesced=False):
    source, destination = Path(source).absolute(), Path(destination).absolute()
    require(quiesced, 'stop the registry writer before authorizing its copy')
    require(not source.is_symlink() and not destination.is_symlink() and
            not source.resolve().is_relative_to(destination.resolve()) and
            not destination.resolve().is_relative_to(source.resolve()), 'registry volumes overlap or are linked')
    require(all(not p.is_symlink() for p in (source, *source.parents, destination, *destination.parents)),
            'registry volume path contains a link')
    original = inventory(source)
    destination.mkdir(parents=True, exist_ok=True)
    for name, entry in sorted(original.items()):
        old, new = source / name, destination / name
        require(not new.is_symlink(), 'destination entry is linked')
        if entry['directory']:
            new.mkdir(exist_ok=True)
            continue
        new.parent.mkdir(parents=True, exist_ok=True)
        require(not new.exists() or new.is_file(), 'destination file has another type')
        with tempfile.NamedTemporaryFile(prefix='.registry-copy-', dir=new.parent, delete=False) as stream:
            temporary = Path(stream.name)
        try:
            shutil.copy2(old, temporary)
            with temporary.open('rb') as stream:
                require(hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256'],
                        'registry source changed during copy')
            os.replace(temporary, new)
        finally:
            temporary.unlink(missing_ok=True)
    # Set directory modes after copying so restrictive source modes do not block
    # creation. Entries in a retained destination are never silently deleted.
    for name, entry in sorted(original.items(), reverse=True):
        if entry['directory']:
            (destination / name).chmod(entry['mode'])
    require(inventory(source) == original, 'registry source changed; writer was not quiesced')
    require(inventory(destination) == original, 'registry destination bytes, paths or modes differ')
    return {'schema': 1, 'passed': True, 'source_unchanged': True, 'original_volume_preserved': True,
            'tree_sha256': fingerprint(original), 'entries': len(original),
            'files': sum(not v['directory'] for v in original.values()),
            'bytes': sum(v.get('size', 0) for v in original.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('--writer-stopped', action='store_true')
    args = parser.parse_args()
    require(not args.receipt.resolve().is_relative_to(args.source.resolve()) and
            not args.receipt.resolve().is_relative_to(args.destination.resolve()),
            'copy receipt must be outside the registry data')
    proof = copy(args.source, args.destination, args.writer_stopped)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
