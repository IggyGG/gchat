#!/usr/bin/env python3
"""Share verified artifact copies and image layers while retaining every path."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import time
import uuid
import zipfile

from release_coordinator import atomic_json, read_receipt


def identity(value):
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
            value.st_ctime_ns, stat.S_IMODE(value.st_mode), value.st_uid, value.st_gid)


def artifact_stream(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | getattr(os, 'O_NOFOLLOW', 0))
    return os.fdopen(descriptor, 'rb')


def file_digest(path):
    with artifact_stream(path) as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('compaction requires regular artifacts')
        result = hashlib.file_digest(stream, 'sha256').hexdigest()
        if identity(before) != identity(os.fstat(stream.fileno())):
            raise ValueError('artifact changed during compaction')
    if path.is_symlink() or identity(before) != identity(path.stat()):
        raise ValueError('artifact path changed during compaction')
    return result, before


def share_files(duplicates, relative_root):
    """Atomically share already authenticated files with identical ownership/mode."""
    changes, reclaimed, unlinked = [], 0, set()
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
                # Replacing one pre-existing alias changes the old inode's
                # ctime. Reauthenticate another alias before accepting only
                # that metadata change caused by our own replacement.
                stable = lambda v: identity(v)[:4] + identity(v)[5:]
                if (current.st_dev, current.st_ino) not in unlinked or stable(current) != stable(previous):
                    raise ValueError('duplicate artifact changed during compaction')
                digest, previous = file_digest(path)
                if digest != key[-1]:
                    raise ValueError('duplicate artifact bytes changed during compaction')
            temporary = path.parent / ('.compact-' + uuid.uuid4().hex)
            try:
                os.link(first, temporary, follow_symlinks=False)
                linked = first.stat()
                if (linked.st_dev, linked.st_ino, linked.st_size, linked.st_mtime_ns,
                        stat.S_IMODE(linked.st_mode), linked.st_uid, linked.st_gid) != (
                        before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
                        stat.S_IMODE(before.st_mode), before.st_uid, before.st_gid):
                    raise ValueError('canonical artifact changed while linking')
                if identity(path.stat()) != identity(previous) or path.is_symlink():
                    raise ValueError('duplicate artifact changed before replacement')
                os.replace(temporary, path)
                unlinked.add((previous.st_dev, previous.st_ino))
                before = first.stat()
                directory = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
                if previous.st_nlink == 1:
                    reclaimed += previous.st_blocks * 512
                changes.append({'path': path.relative_to(relative_root).as_posix(),
                                'canonical': first.relative_to(relative_root).as_posix(),
                                'sha256': key[-1], 'bytes': previous.st_size})
            finally:
                temporary.unlink(missing_ok=True)
    return changes, reclaimed


def checked_metadata(path, maximum_bytes):
    if path.is_symlink():
        raise ValueError('rollback image metadata cannot be a symlink')
    with artifact_stream(path) as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('rollback image metadata must be a regular file')
        raw = stream.read(maximum_bytes + 1)
        if identity(before) != identity(os.fstat(stream.fileno())):
            raise ValueError('rollback image metadata changed while reading')
    if len(raw) > maximum_bytes:
        raise ValueError('rollback image metadata exceeds its bound')
    if path.is_symlink() or identity(before) != identity(path.stat()):
        raise ValueError('rollback image metadata changed while reading')
    digest = hashlib.sha256(raw).hexdigest()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('rollback image metadata must be an object')
    return value, (digest, before)


def compact_rollback_images(state, maximum_images=32, minimum_bytes=16 * 1024**2):
    """Retain every image path while sharing digest-authenticated controller layers."""
    import fcntl
    if type(maximum_images) is not int or not 1 <= maximum_images <= 256:
        raise ValueError('rollback image compaction limit must be between 1 and 256')
    state = Path(state).resolve()
    root = state / 'rollback-images'
    if not root.exists():
        return None
    if root.is_symlink():
        raise ValueError('rollback image root cannot be a symlink')
    retained = state / 'maintenance/compaction'
    retained.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (retained / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        duplicates, controls, images = {}, [], []
        for directory in sorted(root.iterdir()):
            if len(images) >= maximum_images:
                break
            receipt = directory / 'retained.json'
            if not receipt.is_file():
                continue  # An incomplete image is never inferred qualified.
            if directory.is_symlink() or receipt.is_symlink() or receipt.stat().st_size > 65536:
                raise ValueError('unsafe rollback image receipt')
            proof, receipt_binding = checked_metadata(receipt, 65536)
            image_name = proof.get('image', '')
            if not isinstance(image_name, str):
                raise ValueError('rollback image identity must be text')
            match = re.fullmatch(r'[^\s]+/ghost/gchat-release@sha256:([0-9a-f]{64})', image_name)
            if not match:
                continue  # Other workloads retain their independent storage policy.
            expected = match[1]
            if (directory.name != expected or type(proof.get('schema')) is not int or proof.get('schema') != 1
                    or proof.get('manifest_sha256') != 'sha256:' + expected
                    or proof.get('transport') not in (None, 'dir')):
                raise ValueError('rollback image receipt identity differs')
            controls.append((receipt, receipt_binding))
            if proof.get('transport') == 'dir':
                image = directory / 'image'
                manifest_path = image / 'manifest.json'
                blob_root = image
            else:
                image = directory / 'oci'
                if image.is_symlink():
                    raise ValueError('rollback image directory cannot be a symlink')
                blob_root = image / 'blobs/sha256'
                manifest_path = blob_root / expected
                index_path = image / 'index.json'
                if index_path.is_symlink() or index_path.stat().st_size > 65536:
                    raise ValueError('unsafe rollback image index')
                index, index_binding = checked_metadata(index_path, 65536)
                entries = index.get('manifests', [])
                if (not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict)
                        or entries[0].get('digest') != 'sha256:' + expected):
                    raise ValueError('rollback image index identity differs')
                controls.append((index_path, index_binding))
            if (image.is_symlink() or manifest_path.is_symlink()
                    or not manifest_path.resolve().is_relative_to(directory)
                    or manifest_path.stat().st_size > 2 * 1024**2):
                raise ValueError('unsafe rollback image manifest')
            manifest, (actual, before) = checked_metadata(manifest_path, 2 * 1024**2)
            if actual != expected:
                raise ValueError('rollback image manifest digest differs')
            controls.append((manifest_path, (actual, before)))
            layers = manifest.get('layers')
            if not isinstance(layers, list) or len(layers) > 128 or not isinstance(manifest.get('config'), dict):
                raise ValueError('rollback image manifest has no bounded layer inventory')
            for descriptor in [manifest['config'], *layers]:
                if not isinstance(descriptor, dict):
                    raise ValueError('invalid rollback image layer descriptor')
                digest = descriptor.get('digest', '')
                size = descriptor.get('size')
                if (not isinstance(digest, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', digest)
                        or type(size) is not int or not 0 < size <= 12 * 1024**3):
                    raise ValueError('invalid rollback image layer digest or size')
                path = blob_root / digest.removeprefix('sha256:')
                if path.is_symlink() or not path.resolve().is_relative_to(directory):
                    raise ValueError('unsafe rollback image layer path')
                actual, before = file_digest(path)
                if actual != digest.removeprefix('sha256:') or before.st_size != size:
                    raise ValueError('rollback image layer digest or size differs')
                if size >= minimum_bytes:
                    key = (before.st_dev, size, stat.S_IMODE(before.st_mode), before.st_uid, before.st_gid, actual)
                    duplicates.setdefault(key, []).append((path, before))
            images.append({'image': proof['image'], 'manifest_sha256': expected})
        # Authenticate every image before the first link, including small blobs.
        for path, (digest, before) in controls:
            if identity(path.stat()) != identity(before) or path.is_symlink():
                raise ValueError('rollback image provenance changed during compaction')
        changes, reclaimed = share_files(duplicates, state)
        for path, (digest, before) in controls:
            if path.is_symlink() or identity(path.stat()) != identity(before):
                raise ValueError('rollback image provenance changed during compaction')
        report = {'schema': 1, 'images': images, 'all_paths_retained': True,
                  'all_image_manifests_and_blobs_verified': True,
                  'estimated_reclaimed_bytes': reclaimed, 'changes': changes,
                  'completed_at': int(time.time())}
        atomic_json(retained / ('rollback-images-' + str(time.time_ns()) + '.json'), report)
        return report


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
        changes, reclaimed = share_files(duplicates, work.parent)
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


def retained_path(root, name):
    path = PurePosixPath(name)
    if (path.is_absolute() or '..' in path.parts or '\\' in name or '\0' in name
            or ':' in name or not path.parts):
        raise ValueError('unsafe SDK artifact path')
    candidate = root / path
    if (any((root / Path(*path.parts[:i])).is_symlink() for i in range(1, len(path.parts) + 1))
            or not candidate.resolve().is_relative_to(root.resolve())):
        raise ValueError('SDK artifact path escapes retained storage')
    return candidate


def compact_public_sdk(state, maximum_publications=256, minimum_bytes=16 * 1024**2):
    """Share completed public copies, keeping private provider archives separate."""
    import fcntl
    from release_pair import canonical, validate
    if type(maximum_publications) is not int or not 1 <= maximum_publications <= 256:
        raise ValueError('SDK compaction limit must be between 1 and 256')
    state = Path(state).resolve()
    jobs, public = state / 'jobs', state / 'public/updates/sdk'
    if not jobs.exists() or not public.exists():
        return None
    if (jobs.is_symlink() or any(path.is_symlink() for path in
            (state / 'public', state / 'public/updates', public))
            or not public.resolve().is_relative_to(state)):
        raise ValueError('SDK compaction root escapes retained storage')
    retained = state / 'maintenance/compaction'
    retained.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (retained / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        controls, publications, candidates = [], [], {}

        def metadata(path):
            value, binding = checked_metadata(path, 2 * 1024**2)
            controls.append((path, binding))
            return value, binding[0]

        def receipt(path, manifest, stage):
            proof, _ = metadata(path)
            if (proof.get('schema') != 1 or proof.get('release_id') != manifest['release_id']
                    or proof.get('sources') != manifest['sources'] or proof.get('platform') != 'sdk'
                    or proof.get('stage') != stage or proof.get('passed') is not True
                    or proof.get('source_unchanged') is not True):
                raise ValueError('SDK receipt does not bind a completed exact-source publication')
            return proof

        # Revisit recent completed publications so bounded maintenance keeps
        # handling new releases as the retained history grows.
        directories = [p for p in jobs.iterdir() if (p / 'receipt.json').is_file()]
        directories.sort(key=lambda p: (p / 'receipt.json').stat().st_mtime_ns, reverse=True)
        for directory in directories:
            if len(publications) >= maximum_publications:
                break
            path = directory / 'receipt.json'
            if not path.is_file():
                continue
            initial, _ = checked_metadata(path, 2 * 1024**2)
            if initial.get('platform') != 'sdk' or initial.get('stage') != 'publish':
                continue
            if initial.get('passed') is not True:
                continue
            if directory.is_symlink():
                raise ValueError('SDK publication directory cannot be a symlink')
            manifest, _ = metadata(directory / 'candidate.json')
            validate(manifest)
            release = manifest['release_id']
            expected = hashlib.sha256(canonical([release, 'sdk', 'publish'])).hexdigest()
            if directory.name != expected:
                raise ValueError('SDK publication has another durable effect identity')
            published = receipt(path, manifest, 'publish')
            refs = [ref for ref in published['evidence'] if ref['path'] == 'public-sdk.json']
            report, report_sha = metadata(directory / 'public-sdk.json')
            if (len(refs) != 1 or refs[0]['sha256'] != report_sha
                    or report.get('release_id') != release or report.get('sources') != manifest['sources']
                    or report.get('version') != manifest['versions']['sdk']):
                raise ValueError('public SDK index differs from its exact-source receipt')
            build = jobs / hashlib.sha256(canonical([release, 'sdk', 'build'])).hexdigest()
            if build.is_symlink():
                raise ValueError('SDK build directory cannot be a symlink')
            original = receipt(build / 'receipt.json', manifest, 'build')
            archives = {ref['sha256']: retained_path(build, ref['path'])
                        for ref in original['evidence'] if ref['path'].endswith('.zip')}
            for item in report['archives']:
                name, sha, size = item['path'], item['sha256'], item['size']
                if (not re.fullmatch('[0-9a-f]{64}', sha) or type(size) is not int or size <= 0
                        or not PurePosixPath(name).parts or PurePosixPath(name).parts[0] != release
                        or not name.endswith('.zip')
                        or sha not in archives):
                    raise ValueError('public SDK archive is not bound by the original build')
                if size < minimum_bytes:
                    continue
                target = retained_path(public, name)
                if target in candidates:
                    raise ValueError('public SDK archive path is repeated')
                value = target.stat()
                if not stat.S_ISREG(value.st_mode) or value.st_size != size:
                    raise ValueError('public SDK archive size or type changed')
                key = (value.st_dev, size, stat.S_IMODE(value.st_mode), value.st_uid, value.st_gid, sha)
                candidates[target] = (key, archives[sha])
            publications.append(release)

        groups = {}
        for path, (key, original) in candidates.items():
            groups.setdefault(key, []).append((path, original))
        duplicates, verified, inodes, authorities = {}, {}, {}, {}
        for key, entries in groups.items():
            if len(entries) < 2:
                continue
            public_inodes = {(p.stat().st_dev, p.stat().st_ino) for p, _ in entries}
            if any((p.stat().st_dev, p.stat().st_ino) in public_inodes for _, p in entries):
                raise ValueError('public SDK archive already shares a private provider inode')
            for path, original in entries:
                for artifact in (original, path):
                    if artifact not in verified:
                        before = artifact.stat()
                        if artifact.is_symlink() or not stat.S_ISREG(before.st_mode):
                            raise ValueError('SDK compaction requires regular archives')
                        stamp = identity(before)
                        if stamp not in inodes:
                            inodes[stamp] = file_digest(artifact)[0]
                        verified[artifact] = (inodes[stamp], before)
                    sha, before = verified[artifact]
                    if sha != key[-1] or before.st_size != key[1]:
                        raise ValueError('SDK archive bytes differ from the original source-bound build')
                authorities[original] = verified[original][1]
                duplicates.setdefault(key, []).append((path, verified[path][1]))
        for path, before in authorities.items():
            if path.is_symlink() or identity(path.stat()) != identity(before):
                raise ValueError('original SDK archive changed during compaction')
        for path, (_, before) in controls:
            if path.is_symlink() or identity(path.stat()) != identity(before):
                raise ValueError('SDK provenance changed during compaction')
        changes, reclaimed = share_files(duplicates, state)
        for path, before in authorities.items():
            if path.is_symlink() or identity(path.stat()) != identity(before):
                raise ValueError('original SDK archive changed during replacement')
        for path, (_, before) in controls:
            if path.is_symlink() or identity(path.stat()) != identity(before):
                raise ValueError('SDK provenance changed during replacement')
        report = {'schema': 1, 'publications': publications,
                  'original_provider_archives_retained': True, 'private_provider_archives_shared': False,
                  'all_paths_retained': True, 'estimated_reclaimed_bytes': reclaimed,
                  'changes': changes, 'completed_at': int(time.time())}
        atomic_json(retained / ('public-sdk-' + str(time.time_ns()) + '.json'), report)
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--maximum-builds', type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.maximum_builds <= 256:
        parser.error('maximum builds must be between 1 and 256')
    print(json.dumps({'completed': compact(args.state, args.maximum_builds),
                      'rollback_images': compact_rollback_images(args.state),
                      'public_sdk': compact_public_sdk(args.state)}), flush=True)


if __name__ == '__main__':
    main()
