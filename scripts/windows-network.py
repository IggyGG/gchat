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
RETAINED = {
    'windows18': {'run': RUN, 'artifact': ARTIFACT, 'archive': ARCHIVE, 'sources': SOURCES,
        'conclusion': 'success', 'executable': {'name': 'gchat-desktop.exe',
            'sha256': 'fb855b2d7542be38e0f520536680fd00d02f37392b73a5536f1a6db2e954a612', 'size': 47503648}},
    'windows29': {'run': 36385120193, 'artifact': 10958490222,
        'archive': 'f0651e5a0cbebf9a362c3ce46f1596385ea629524dbb9d92179c19b1eb82eaf8',
        'sources': {'gchat': '9c3ef0573f87fa15b44d14fdd1b20fcd8f60a517',
                    'gcoms': '0b41cb2ef16f8ddab81ca8b38182522a31735900'},
        'conclusion': 'failure', 'executable': {'name': 'gchat-desktop.exe',
            'sha256': '072ff89231d1f2b333a75a5c7bd8cc3ee01d16eeb89f3abb394e5a0d207445ac', 'size': 47525664}},
    'windows36': {'run': 36413216786, 'artifact': 10970753773,
        'archive': '4d567ce80b4bb813570f2c5439f74b4e0fc5512fef56f2e4bd77d76c007172b2',
        'sources': {'gchat': '21ad84ed266fdc237fd745e4b1aca6139b6d6728',
                    'gcoms': '8cdfd3fee2ab7809f1c348dc3a60ef24393b4101'},
        'conclusion': 'failure', 'executable': {'name': 'gchat-desktop.exe',
            'sha256': 'd37a2e334c76d5988dc9a8aefbec3c6db18e1cb14a74826a47cfb784ece9b100', 'size': 47526688}},
}


def original_network_failure(original):
    report = json.loads((original / 'application-smoke/report.json').read_text())
    network = json.loads((original / 'application-smoke/network/report.json').read_text())
    service = json.loads((original / 'application-smoke/service/report.json').read_text())
    require(report.get('passed') is False and report.get('error') == 'installed network delivery/recovery failed'
            and report.get('cleanup', {}).get('passed') is True
            and report.get('persistent_certificate_stores_unchanged') is True
            and network.get('passed') is False and network.get('inputs_unchanged') is True
            and network.get('children_stopped') is True and service.get('passed') is True,
            'retained failure is not the expected cleaned-up network failure')


def qualification_policy(candidate, file_bytes):
    if file_bytes == 16777216:
        return None
    require(candidate == 'windows36' and type(file_bytes) is int and file_bytes == 4194304,
            '4 MiB authorization binds only the retained Windows 36 artifact')
    path = ROOT / 'release/automation/qualification/windows36-4mib.json'
    policy = json.loads(path.read_text())
    bound = RETAINED[candidate]
    require(policy.get('schema') == 1 and policy.get('platform') == 'windows-x86_64'
            and policy.get('release_id') == 'c6165120748d3adc093e7a0cfff84f6ad99546e3b48a08eb980b1758b34b637b'
            and policy.get('sources') == bound['sources']
            and policy.get('binary_sha256') == bound['executable']['sha256']
            and policy.get('original_bytes') == 16777216 and policy.get('bytes') == file_bytes
            and policy.get('completion_seconds') == 180 and policy.get('total_seconds') == 600,
            'retained Windows qualification authorization differs')
    return path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--candidate', choices=sorted(RETAINED), default='windows18')
    p.add_argument('--file-bytes', type=int, choices=(4194304, 16777216), default=16777216)
    args = p.parse_args()
    bound = RETAINED[args.candidate]
    policy = qualification_policy(args.candidate, args.file_bytes)
    require(os.name == 'nt' and os.environ.get('GITHUB_ACTIONS') == 'true',
            'requires isolated native Windows Actions worker')
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    installer.smoke.private_directory(root)
    receipt = {'passed': False, 'scope': 'retained_' + args.candidate + '_native_installer_network',
               'application_rebuilt': False, 'native_ci_repeated': False,
               'run_id': bound['run'], 'artifact_id': bound['artifact'], 'archive_sha256': bound['archive'],
               'sources': bound['sources'], 'original_workflow_conclusion': bound['conclusion']}
    receipt['file_qualification_bytes'] = args.file_bytes
    if policy is not None:
        shutil.copy2(policy, root / 'qualification-policy.json')
        receipt['qualification_policy_sha256'] = digest(policy)
    invitation = Path(os.environ['RUNNER_TEMP']) / ('gchat-network-' + os.urandom(16).hex())
    try:
        run = package.api(f"repos/IggyGG/gchat/actions/runs/{bound['run']}")
        artifact = package.api(f"repos/IggyGG/gchat/actions/artifacts/{bound['artifact']}")
        require(run['status'] == 'completed' and run['conclusion'] == bound['conclusion']
                and run['head_sha'] == bound['sources']['gchat'] and artifact['workflow_run']['id'] == bound['run']
                and run.get('path') == '.github/workflows/windows-release.yml'
                and not artifact['expired'] and artifact['digest'] == 'sha256:' + bound['archive'],
                'retained artifact workflow binding changed')
        archive = root / 'original.zip'
        with archive.open('xb') as stream:
            subprocess.run(['gh', 'api', f"repos/IggyGG/gchat/actions/artifacts/{bound['artifact']}/zip"],
                           stdout=stream, check=True, timeout=180)
        require(digest(archive) == bound['archive'] and archive.stat().st_size == artifact['size_in_bytes'],
                'retained archive bytes differ')
        original = root / 'original'
        package.extract(archive, original)
        build = json.loads((original / 'build.json').read_text())
        require(build['sources'] == bound['sources'], 'retained application source differs')
        require(build['executables'] == [bound['executable']], 'retained executable binding differs')
        if bound['conclusion'] == 'failure':
            original_network_failure(original)
            receipt['original_failed_network_receipt_sha256'] = digest(original / 'application-smoke/network/report.json')
        code = os.environ.pop('GCHAT_NETWORK_INVITATION', '')
        require(0 < len(code.encode()) <= 180000, 'missing bounded fixture invitation')
        with invitation.open('x', encoding='utf-8') as stream:
            stream.write(code)
        installer.smoke.private_fixture_path(invitation, directory=False)
        result = installer.run(argparse.Namespace(build_manifest=original / 'build.json',
            native_receipt=original / 'provenance/native-ci.json', publication=ROOT / 'release/publication.json',
            installer=None, output=root / 'execution', temp_parent=None, timeout=30,
            network_invitation=invitation, file_bytes=args.file_bytes))
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
        if policy is not None:
            shutil.copy2(root / 'qualification-policy.json', public / 'qualification-policy.json')
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
