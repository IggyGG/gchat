#!/usr/bin/env python3
"""Native network qualification of one retained, immutable Windows installer."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from release_evidence import digest, require


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


package = load('retained_windows_package', 'windows-package.py')
installer = load('retained_windows_installer', 'test-windows-installer.py')
RUN = 36345150554
ARTIFACT = 10942212091
ARCHIVE = '1677df7de66c126c2fc01f0664e4826c3614ffc7e3ebde71119eafb310eba6cd'
SOURCES = {'gchat': 'f3584d9b108c800981c4f7235cf3dd6fb7b52b0e',
           'gcoms': '2aeb86ebfb57ffece666a23803f90f014f3768ef'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    require(os.name == 'nt' and os.environ.get('GITHUB_ACTIONS') == 'true',
            'requires isolated native Windows Actions worker')
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    installer.smoke.private_directory(root)
    receipt = {'passed': False, 'scope': 'retained_windows18_native_installer_network',
               'application_rebuilt': False, 'native_ci_repeated': False,
               'run_id': RUN, 'artifact_id': ARTIFACT, 'archive_sha256': ARCHIVE,
               'sources': SOURCES}
    invitation = Path(os.environ['RUNNER_TEMP']) / ('gchat-network-' + os.urandom(16).hex())
    try:
        run = package.api(f'repos/IggyGG/gchat/actions/runs/{RUN}')
        artifact = package.api(f'repos/IggyGG/gchat/actions/artifacts/{ARTIFACT}')
        require(run['status'] == 'completed' and run['conclusion'] == 'success'
                and run['head_sha'] == SOURCES['gchat'] and artifact['workflow_run']['id'] == RUN
                and not artifact['expired'] and artifact['digest'] == 'sha256:' + ARCHIVE,
                'retained artifact workflow binding changed')
        archive = root / 'original.zip'
        with archive.open('xb') as stream:
            subprocess.run(['gh', 'api', f'repos/IggyGG/gchat/actions/artifacts/{ARTIFACT}/zip'],
                           stdout=stream, check=True, timeout=180)
        require(digest(archive) == ARCHIVE and archive.stat().st_size == artifact['size_in_bytes'],
                'retained archive bytes differ')
        original = root / 'original'
        package.extract(archive, original)
        build = json.loads((original / 'build.json').read_text())
        require(build['sources'] == SOURCES, 'retained application source differs')
        require(build['executables'] == [{'name': 'gchat-desktop.exe',
            'sha256': 'fb855b2d7542be38e0f520536680fd00d02f37392b73a5536f1a6db2e954a612',
            'size': 47503648}], 'retained executable binding differs')
        code = os.environ.pop('GCHAT_NETWORK_INVITATION', '')
        require(0 < len(code.encode()) <= 180000, 'missing bounded fixture invitation')
        with invitation.open('x', encoding='utf-8') as stream:
            stream.write(code)
        installer.smoke.private_fixture_path(invitation, directory=False)
        result = installer.run(argparse.Namespace(build_manifest=original / 'build.json',
            native_receipt=original / 'provenance/native-ci.json', publication=ROOT / 'release/publication.json',
            installer=None, output=root / 'execution', temp_parent=None, timeout=30,
            network_invitation=invitation))
        require(result == 0, 'native installer/network qualification failed')
        receipt['passed'] = True
    except Exception as error:
        # Requests and the temporary invitation never enter exception details.
        receipt['error_type'] = type(error).__name__
    finally:
        invitation.unlink(missing_ok=True)
        receipt['invitation_removed'] = not invitation.exists()
        receipt['passed'] = receipt['passed'] and receipt['invitation_removed']
        (root / 'summary.json').write_text(json.dumps(receipt, indent=2))
        public = root / 'evidence'
        public.mkdir()
        shutil.copy2(root / 'summary.json', public / 'summary.json')
        execution = root / 'execution'
        if execution.exists():
            for path in execution.rglob('*'):
                relative = path.relative_to(execution)
                if any(part in ('c0', 'c1') for part in relative.parts):
                    continue
                if path.is_file() and path.suffix in ('.json', '.log', '.stdout', '.stderr'):
                    destination = public / 'execution' / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, destination)
    print(json.dumps(receipt))
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
