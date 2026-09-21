#!/usr/bin/env python3
"""Early native daemon diagnostic on immutable source archives, without changing locks."""
import argparse
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import tarfile
import tomllib

from release_evidence import digest, source_identity


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def source_map(root):
    return {path.relative_to(root).as_posix(): digest(path)
            for path in sorted(root.rglob('*')) if path.is_file()}


def execute(command, cwd, environment, log, timeout):
    options = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}
    with log.open('wb') as output:
        process = subprocess.Popen(command, cwd=cwd, env=environment, stdout=output, stderr=subprocess.STDOUT, **options)
        try:
            return process.wait(timeout=timeout), False
        except subprocess.TimeoutExpired:
            if os.name == 'nt':
                subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                               stdout=output, stderr=subprocess.STDOUT, check=True)
            else:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=30)
            return 124, True


def check(gchat, gcoms, output, target, timeout=600):
    roots = {'gchat': gchat.resolve(), 'gcoms': gcoms.resolve()}
    sources = {name: source_identity(root) for name, root in roots.items()}
    output.mkdir(parents=True, exist_ok=False)
    snapshots = output / 'inputs'
    snapshots.mkdir()
    report = {'scope': 'native_standalone_daemon_diagnostic', 'sources': sources,
              'passed': False, 'source_unchanged': False, 'archives': {}}
    try:
        for name, root in roots.items():
            archive = output / (name + '.tar')
            subprocess.run(['git', 'archive', '--format=tar', '--output', str(archive), sources[name]['commit']], cwd=root, check=True)
            report['archives'][name] = {'path': archive.name, 'sha256': digest(archive)}
            checkout = snapshots / name
            checkout.mkdir()
            with tarfile.open(archive) as stream:
                stream.extractall(checkout, filter='data')
        chat, protocol = snapshots / 'gchat', snapshots / 'gcoms'
        patches = ['[patch.crates-io]']
        workspace = tomllib.loads((protocol / 'Cargo.toml').read_text(encoding='utf-8'))['workspace']
        for member in workspace['members']:
            for directory in sorted(protocol.glob(member)):
                if not directory.resolve().is_relative_to(protocol):
                    raise ValueError('workspace member escapes source snapshot')
                name = tomllib.loads((directory / 'Cargo.toml').read_text(encoding='utf-8'))['package']['name']
                if name.startswith('gcoms-') or name == 'gcoms':
                    patches.append(f'{json.dumps(name)} = {{ path = {json.dumps(str(directory))} }}')
        config = chat / '.cargo/config.toml'
        if config.exists():
            raise ValueError('refuse to overwrite archived Cargo configuration')
        config.parent.mkdir(exist_ok=True)
        config.write_text('\n'.join(patches) + '\n', encoding='utf-8')
        # upload-artifact filters hidden directories by default. Keep this
        # generated input outside .cargo as well as in the checked snapshot.
        shutil.copyfile(config, output / 'cargo-config.toml')
        before = {name: source_map(snapshots / name) for name in roots}
        write_json(output / 'before.json', before)
        report['before'] = {'path': 'before.json', 'sha256': digest(output / 'before.json')}
        command = ['cargo', 'test', '-p', 'gchat-tui', '--all-features', '--test', 'standalone_daemon', '--', '--nocapture']
        environment = dict(os.environ, CARGO_TARGET_DIR=str(target.resolve()))
        log = output / 'test.log'
        code, timed_out = execute(command, chat, environment, log, timeout)
        report.update(command=command, exit_code=code, timed_out=timed_out,
                      log={'path': log.name, 'sha256': digest(log)})
        print(log.read_text(encoding='utf-8', errors='replace'), flush=True)
        after = {name: source_map(snapshots / name) for name in roots}
        write_json(output / 'after.json', after)
        report['after'] = {'path': 'after.json', 'sha256': digest(output / 'after.json')}
        # Cargo may derive one workspace lock for these path-patched sources.
        # Every original file and the patch config must otherwise remain exact.
        expected = {name: {path: sha for path, sha in files.items() if not (name == 'gchat' and path == 'Cargo.lock')}
                    for name, files in before.items()}
        actual = {name: {path: sha for path, sha in files.items() if not (name == 'gchat' and path == 'Cargo.lock')}
                  for name, files in after.items()}
        report['snapshot_sources_unchanged'] = expected == actual
        lock = chat / 'Cargo.lock'
        report['derived_lock'] = {'path': 'inputs/gchat/Cargo.lock', 'sha256': digest(lock)}
        report['cargo_config'] = {'path': 'cargo-config.toml', 'sha256': digest(config)}
        report['source_unchanged'] = all(source_identity(root) == sources[name] for name, root in roots.items())
        report['passed'] = code == 0 and report['source_unchanged'] and report['snapshot_sources_unchanged']
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        log = output / 'test.log'
        if log.exists():
            report['log'] = {'path': log.name, 'sha256': digest(log)}
        write_json(output / 'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gchat', type=Path, required=True)
    parser.add_argument('--gcoms', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--target-dir', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args()
    result = check(args.gchat, args.gcoms, args.output.resolve(), args.target_dir, args.timeout)
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
