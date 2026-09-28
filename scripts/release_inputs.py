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
    'scripts/release_pair.py', 'release/automation/Dockerfile',
    'scripts/release_jobs.py', 'scripts/release_verify.py', 'scripts/release_recovery.py',
    'scripts/release_ios_recovery.py',
    'scripts/release_compatibility.py', 'scripts/release_stores.py',
    'scripts/release_store_worker.py', 'scripts/release_publish.py',
    'scripts/release_feed.py', 'scripts/release_apt.py',
    'scripts/ios-lifecycle.py', 'scripts/ios-verify-retained.py',
    'scripts/fixtures/ios-lifecycle/LifecycleTests.swift',
    'scripts/windows-network.py', 'scripts/test-native-network.py',
    'scripts/windows-rollback.py', 'scripts/tests/windows_rollback_test.py',
    'scripts/macos-rollback.py', 'scripts/tests/macos_rollback_test.py',
    '.github/workflows/macos-rollback.yml',
    '.github/workflows/macos-network-retained.yml', 'scripts/macos-network-retained.py',
    'scripts/tests/macos_network_retained_test.py',
    '.github/workflows/windows-rollback.yml', '.github/workflows/macos-catalog-check.yml',
    'scripts/website.py', 'scripts/deploy-website.py',
    'scripts/tests/website_test.py', 'scripts/tests/website_deploy_test.py',
    'release/downloads.json', 'website/index.template.html', 'website/privacy.html',
    'website/robots.txt', 'website/IMPORT.json',
    'scripts/test-windows-installer.py',
    '.github/workflows/ios-lifecycle.yml', '.github/workflows/ios-verify.yml',
    '.github/workflows/windows-verify.yml',
    'scripts/tests/native_network_test.py', 'scripts/tests/windows_installer_test.py',
    'scripts/tests/windows_release_test.py', 'scripts/tests/ios_lifecycle_test.py',
    'scripts/tests/ios_retained_test.py',
    'release/automation/qualification/windows36-4mib.json',
})


# Reviewed store-only assets are not referenced by application/build inputs.
# Enumerate exact files: a new asset or exporter still requires classification.
STORE_LISTING_FILES = frozenset({
    'marketing/app-store/retro-v1/README.md',
    'marketing/app-store/retro-v1/artboards.html',
    'marketing/app-store/retro-v1/export.mjs',
    'marketing/app-store/retro-v1/exports/ipad-01-conversation.jpg',
    'marketing/app-store/retro-v1/exports/ipad-02-channels.jpg',
    'marketing/app-store/retro-v1/exports/ipad-03-files.jpg',
    'marketing/app-store/retro-v1/exports/ipad-04-invitation.jpg',
    'marketing/app-store/retro-v1/exports/iphone-01-conversation.jpg',
    'marketing/app-store/retro-v1/exports/iphone-02-channels.jpg',
    'marketing/app-store/retro-v1/exports/iphone-03-files.jpg',
    'marketing/app-store/retro-v1/exports/iphone-04-invitation.jpg',
    'marketing/app-store/retro-v1/index.html',
    'marketing/app-store/retro-v1/listing.json',
    'marketing/app-store/retro-v1/listing.md',
    'marketing/app-store/retro-v1/preview.jpg',
    'marketing/app-store/retro-v1/publication.json',
    'marketing/app-store/retro-v1/source/ipad-channels.png',
    'marketing/app-store/retro-v1/source/ipad-chat.png',
    'marketing/app-store/retro-v1/source/ipad-files.png',
    'marketing/app-store/retro-v1/source/ipad-invitation.png',
    'marketing/app-store/retro-v1/source/iphone-channels.png',
    'marketing/app-store/retro-v1/source/iphone-chat.png',
    'marketing/app-store/retro-v1/source/iphone-files.png',
    'marketing/app-store/retro-v1/source/iphone-invitation.png',
    'marketing/app-store/retro-v1/validation.json',
    'marketing/play-store/retro-v1/README.md',
    'marketing/play-store/retro-v1/artboards.html',
    'marketing/play-store/retro-v1/export.mjs',
    'marketing/play-store/retro-v1/exports/01-conversation.jpg',
    'marketing/play-store/retro-v1/exports/02-channels.jpg',
    'marketing/play-store/retro-v1/exports/03-files.jpg',
    'marketing/play-store/retro-v1/exports/04-invitation.jpg',
    'marketing/play-store/retro-v1/exports/feature.png',
    'marketing/play-store/retro-v1/index.html',
    'marketing/play-store/retro-v1/listing.md',
    'marketing/play-store/retro-v1/preview.jpg',
    'marketing/play-store/retro-v1/prompts.md',
    'marketing/play-store/retro-v1/publication.json',
    'marketing/play-store/retro-v1/source/channels.png',
    'marketing/play-store/retro-v1/source/chat.png',
    'marketing/play-store/retro-v1/source/files.png',
    'marketing/play-store/retro-v1/source/invitation.png',
    'marketing/play-store/retro-v1/source/live-0.png',
    'marketing/play-store/retro-v1/source/live-1.png',
    'marketing/play-store/retro-v1/source/pixel-night.webp',
    'marketing/play-store/retro-v1/source/provenance.json',
    'marketing/play-store/retro-v1/validation.json',
})


def qualification_only(project, path):
    return project == 'gchat' and (path in CONTROL_FILES or path in STORE_LISTING_FILES or
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
