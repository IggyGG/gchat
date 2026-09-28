"""Conservative artifact identity independent of release-controller revisions.

Only reviewed orchestration/qualification files are excluded. Unknown files,
build/signing scripts, application resources, locks and workflow changes all
invalidate artifacts. The original source manifest is never rewritten.
"""
import hashlib
import subprocess

from release_pair import canonical


CONTROL_FILES = frozenset({
    'PLAN.md', 'TESTPLAN.md', 'README.md', 'docs/AUTOMATIC_RELEASES.md',
    'docs/PRODUCTION_RELEASE.md',
    'scripts/release_inputs.py', 'scripts/release_coordinator.py',
    'scripts/release_discovery.py', 'scripts/release_config.py',
    'scripts/release_ledger.py', 'scripts/release_maintenance.py',
    'scripts/release_jobs.py', 'scripts/release_verify.py', 'scripts/release_recovery.py',
    'scripts/release_compatibility.py', 'scripts/release_stores.py',
    'scripts/release_store_worker.py', 'scripts/release_publish.py',
    'scripts/release_feed.py', 'scripts/release_apt.py',
    'scripts/ios-lifecycle.py', 'scripts/ios-verify-retained.py',
    'scripts/fixtures/ios-lifecycle/LifecycleTests.swift',
    'scripts/windows-network.py', 'scripts/test-native-network.py',
    'scripts/test-windows-installer.py',
    '.github/workflows/ios-lifecycle.yml', '.github/workflows/ios-verify.yml',
    '.github/workflows/windows-verify.yml',
    'scripts/tests/native_network_test.py', 'scripts/tests/windows_installer_test.py',
    'scripts/tests/windows_release_test.py', 'scripts/tests/ios_lifecycle_test.py',
    'scripts/tests/ios_retained_test.py',
    'release/automation/qualification/windows36-4mib.json',
})


def qualification_only(project, path):
    return project == 'gchat' and (path in CONTROL_FILES or
        (path.startswith('scripts/tests/release_') and path.endswith('_test.py')))


def fingerprints(repositories, sources):
    artifacts, qualification = {}, {}
    for project in ('gchat', 'gcoms'):
        raw = subprocess.check_output(['git', '-C', str(repositories[project]),
            'ls-tree', '-rz', '--full-tree', sources[project]['commit']])
        entries = []
        for record in raw.split(b'\0'):
            if not record:
                continue
            metadata, path = record.split(b'\t', 1)
            mode, kind, oid = metadata.decode('ascii').split()
            entries.append([path.decode('utf-8'), mode, kind, oid])
        entries.sort()
        qualification[project] = entries
        artifacts[project] = [entry for entry in entries
                              if not qualification_only(project, entry[0])]
    return {'schema': 1,
            'artifacts': hashlib.sha256(canonical(artifacts)).hexdigest(),
            'qualification': hashlib.sha256(canonical(qualification)).hexdigest()}
