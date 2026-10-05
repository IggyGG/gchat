#!/usr/bin/env python3
"""Run the existing isolated relay gate once for a frozen native release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from release_evidence import source_identity
from release_linux_qualification import checked_sources, context
from release_pair import canonical, validate


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def retain_journey(source, destination):
    """Retain original reports and their evidence, never profile/key folders."""
    source, destination = Path(source), Path(destination)
    names = {'report.json', 'worker.json', 'driver.py', 'boundary-helper.py'}
    for report in ('report.json', 'worker.json'):
        if (source / report).is_file():
            names.update(json.loads((source / report).read_text()).get('evidence', {}))
    total = 0
    for name in sorted(names):
        relative = Path(name)
        path = source / relative
        if relative.is_absolute() or '..' in relative.parts or path.is_symlink():
            raise ValueError('journey evidence escapes its isolated directory')
        if not path.exists():
            continue  # Failed workers retain the original partial evidence.
        if not path.is_file() or not path.resolve().is_relative_to(source.resolve()):
            raise ValueError('journey evidence is not a regular retained file')
        total += path.stat().st_size
        if total > 8 * 1024 ** 3:
            raise ValueError('relay journey evidence exceeds retained budget')
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def execute(command, workspace, log, timeout):
    print('Starting ' + log.stem, flush=True)
    began = time.monotonic()
    with log.open('xb') as stream:
        completed = subprocess.run(list(map(str, command)), cwd=workspace,
                                   stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
    print(f'{log.stem}: exit {completed.returncode}, {time.monotonic() - began:.1f}s', flush=True)
    completed.check_returncode()


def run(workspace, output, work, target):
    workspace, output, work = map(lambda p: Path(p).resolve(), (workspace, output, work))
    manifest = validate(json.loads(Path(os.environ['GCHAT_RELEASE_MANIFEST']).read_text()))
    provider = context(manifest, os.environ)
    checked_sources(workspace, manifest)
    output.mkdir(parents=True, exist_ok=False)
    work.mkdir(parents=True, exist_ok=False)
    report = {'schema': 1, 'kind': 'relay_load', 'release_id': manifest['release_id'],
              'sources': manifest['sources'], 'provider': provider, 'passed': False,
              'source_unchanged': False, 'evidence': {}, 'started_at': int(time.time()),
              'hardware': {'logical_cpus': os.cpu_count(),
                           'memory_bytes': os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')}}
    build = work / 'build'
    try:
        execute(['python3', workspace / 'gcoms/scripts/build-fleet-files.py',
                 '--gchat', workspace / 'gchat', '--output', build, '--target-dir', target, '--fetch'],
                workspace, output / 'build.log', 1800)
        for mode, name, timeout in [('relay-preflight', 'preflight', 330), ('relay-load', 'load', 4530)]:
            command = ['python3', workspace / 'gcoms/scripts/gchat-turnover.py',
                       '--build', build, '--fixture-host', build / 'bin/turnover_daemon',
                       '--mode', mode, '--out', work / name]
            if mode == 'relay-load':
                command += ['--load-seconds', '1800', '--load-relay-circuits', '2048',
                            '--load-relay-connections', '4096']
            try:
                execute(command, workspace, output / (name + '.log'), timeout)
            finally:
                retain_journey(work / name, output / name)
        checked_sources(workspace, manifest)
        report['source_unchanged'] = True
        report['passed'] = True
    finally:
        if (build / 'build.json').is_file():
            shutil.copyfile(build / 'build.json', output / 'build.json')
        report['completed_at'] = int(time.time())
        try:
            report['source_unchanged'] = all(source_identity(workspace / name) == source
                                             for name, source in manifest['sources'].items())
        except (ValueError, OSError, subprocess.CalledProcessError):
            report['source_unchanged'] = False
            report['source_check_failed'] = True
        if not report['source_unchanged']:
            report['passed'] = False
        report['evidence'] = {p.relative_to(output).as_posix(): digest(p)
                              for p in sorted(output.rglob('*')) if p.is_file()}
        (output / 'summary.json').write_bytes(canonical(report))
    from release_relay_load import verify
    try:
        verify(output, manifest, provider)
    except (ValueError, KeyError, OSError):
        report['passed'] = False
        (output / 'summary.json').write_bytes(canonical(report))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--target-dir', type=Path, required=True)
    args = parser.parse_args()
    run(args.workspace, args.output, args.work, args.target_dir)
