"""Conservative artifact identity independent of release-controller revisions.

Only reviewed orchestration/qualification files are excluded. Unknown files,
build/signing scripts, application resources, locks and workflow changes all
invalidate artifacts. The original source manifest is never rewritten.
"""
import hashlib
import subprocess

from release_pair import canonical


CONTROL_FILES = frozenset({
    'docs/evidence/controller-automation-20261007/provider-validation.json',
    'scripts/release_minutes.py', 'scripts/tests/release_minutes_test.py',
    'docs/evidence/stabilization-20261001/node-image-headroom.json',
    'scripts/node-image-headroom.py', 'scripts/tests/node_image_headroom_test.py',
    'release/automation/node-image-headroom.service', 'release/automation/node-image-headroom.timer',
    'PLAN.md', 'TESTPLAN.md', 'README.md', 'docs/AUTOMATIC_RELEASES.md',
    'docs/PRODUCTION_RELEASE.md',
    'scripts/release_inputs.py', 'scripts/release_coordinator.py',
    'scripts/release_discovery.py', 'scripts/release_config.py',
    'scripts/release_ledger.py', 'scripts/release_maintenance.py',
    'scripts/release.py', 'scripts/release_control.py',
    'scripts/release_flight.py', 'scripts/tests/release_flight_test.py',
    '.github/workflows/contracts-check.yml',
    'scripts/release_deployment_runner.py', 'scripts/tests/release_deployment_runner_test.py',
    'scripts/release_deployment.py', 'scripts/release_host_worker.py',
    'scripts/release_host_install.py', 'release/automation/kubernetes.yaml',
    'scripts/release_inventory.py', 'scripts/release_sdk.py',
    'scripts/release_network_canary.py', 'scripts/release_kubernetes_worker.py',
    'scripts/release_canary_grant.py', 'scripts/release_host_serve.py',
    'scripts/release_evidence.py',
    'scripts/release_compaction.py', 'release/automation/compaction.yaml',
    'scripts/controller_runtime.py',
    'scripts/release_pair.py', 'release/automation/Dockerfile', 'release/automation/requirements.txt',
    'scripts/release_jobs.py', 'scripts/release_verify.py', 'scripts/release_recovery.py',
    'scripts/release_ios_recovery.py',
    'scripts/release_macos_recovery.py', 'scripts/tests/release_macos_recovery_test.py',
    'release/automation/qualification/native-recoveries.json',
    'scripts/copy-release-registry.py', 'scripts/tests/copy_release_registry_test.py',
    'release/automation/registry.yaml',
    'scripts/release_compatibility.py', 'scripts/release_stores.py',
    'scripts/release_store_worker.py', 'scripts/release_publish.py',
    'scripts/release_feed.py', 'scripts/release_apt.py',
    'scripts/ios-lifecycle.py', 'scripts/ios-verify-retained.py',
    'scripts/macos-package.py', '.github/workflows/macos-package.yml',
    'scripts/tests/macos_package_test.py',
    'scripts/fixtures/ios-lifecycle/LifecycleTests.swift',
    'scripts/windows-network.py', 'scripts/test-native-network.py',
    'scripts/windows-rollback.py', 'scripts/tests/windows_rollback_test.py',
    'scripts/macos-rollback.py', 'scripts/tests/macos_rollback_test.py',
    '.github/workflows/macos-rollback.yml', '.github/workflows/release-tools-check.yml',
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
    'scripts/release_acceptance.py', 'scripts/test-native-upgrade.py',
    'scripts/acceptance_delivery.py', 'scripts/release_acceptance_delivery.py',
    '.github/workflows/native-acceptance.yml',
    'scripts/mobile_acceptance_inputs.py', 'scripts/mobile_android_ui.py',
    'scripts/mobile_installed_journey.py', 'scripts/mobile_ios_ui.py',
    'scripts/test-mobile-upgrade.py', 'scripts/tests/mobile_acceptance_test.py',
    'scripts/fixtures/ios-acceptance/AcceptanceTests.swift',
    '.github/workflows/mobile-acceptance.yml',
    'docs/evidence/stabilization-20261001/mobile-acceptance.json',
    'docs/evidence/stabilization-20261001/live-controller-and-acceptance.json',
    'docs/evidence/stabilization-20261001/image-retention.json',
    'docs/evidence/stabilization-20261001/contract-checkpoint.json',
    'docs/evidence/stabilization-20261001/ios-build-allocation.json',
    'docs/evidence/stabilization-20261001/ios-passphrase-control.json',
    'docs/evidence/stabilization-20261001/native-desktop-artifacts-verified.json',
    'docs/evidence/stabilization-20261001/invitation-fixture-correction.json',
    'docs/evidence/stabilization-20261001/public-sdk-compaction-activated.json',
    'docs/evidence/stabilization-20261001/native-relay-egress-correction.json',
    'docs/evidence/stabilization-20261001/host-install-permissions.json',
    'docs/evidence/stabilization-20261001/launch-simplification.json',
})

# Only these reviewed controller paths may change independently of native
# infrastructure. Unknown scripts, packaging, native workflows and all GComs
# runtime/test inputs still require their ordinary release qualification.
CONTROLLER_FILES = frozenset({
    'scripts/release_provider.py', 'scripts/release_controller.py',
    'scripts/release_platform_deployment.py', 'scripts/release_compatibility.py',
    'scripts/build-controller.py', '.github/workflows/controller-release.yml',
    'scripts/release_inputs.py', 'scripts/release_discovery.py',
    'scripts/release_coordinator.py', 'scripts/release_config.py',
    'scripts/release_ledger.py', 'scripts/release_maintenance.py',
    'scripts/release.py', 'scripts/release_control.py', 'scripts/release_flight.py',
    'scripts/release_minutes.py', 'scripts/release_jobs.py', 'scripts/release_sdk.py',
    'scripts/release_recovery.py', 'scripts/release_relay_load.py',
    'scripts/release_stores.py', 'scripts/release_store_worker.py',
    'scripts/release_acceptance.py', 'scripts/release_acceptance_delivery.py',
    'scripts/release_deployment_runner.py', 'scripts/release_deployment.py',
    'scripts/release_inventory.py', 'scripts/release_kubernetes_worker.py',
    'scripts/release_host_worker.py', 'scripts/release_host_install.py',
    'scripts/release_host_serve.py', 'scripts/release_canary_grant.py',
    'scripts/release_network_canary.py', 'scripts/release_evidence.py',
    'scripts/release_compaction.py', 'scripts/controller_runtime.py',
    'release/automation/Dockerfile', 'release/automation/requirements.txt',
    'release/automation/kubernetes.yaml', 'release/automation/compaction.yaml',
})
CONTROL_FILES = CONTROL_FILES | CONTROLLER_FILES


def controller_only(path):
    return path in CONTROLLER_FILES or (
        path.startswith('scripts/tests/release_') and path.endswith('_test.py'))


# Reviewed status/validation documents do not enter GComs application code or
# packaging. Rust, locks and unclassified evidence remain artifact inputs.
GCOMS_STATUS_FILES = frozenset({
    'PLAN.md', 'README.md', 'TESTPLAN.md',
    'docs/evidence/stabilization-20261001/durable-reopen.json',
    'docs/evidence/stabilization-20261001/contact-request-window.json',
    'docs/evidence/stabilization-20261001/windows-locked-storage-tests.json',
    'docs/evidence/stabilization-20261001/sdk-size-policy.json',
    'docs/evidence/stabilization-20261001/sdk-native-90d7eac.json',
    'crates/file-transfer/README.md',
    'scripts/release_evidence.py',
    'scripts/tests/release_evidence_test.py',
    'docs/evidence/stabilization-20261001/native-capacity-exclusion-policy.json',
    'docs/evidence/stabilization-20261001/sdk-apple-8f8fdb3.json',
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
    return (project == 'gcoms' and path in GCOMS_STATUS_FILES or
        project == 'gchat' and (path in CONTROL_FILES or path in STORE_LISTING_FILES or
            (path.startswith('scripts/tests/release_') and path.endswith('_test.py'))))


def fingerprints(repositories, sources):
    artifacts, qualification, infrastructure, controller = {}, {}, {}, {}
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
        # Controller bytes receive their own exact-source image qualification.
        # They do not invalidate unchanged client/native-service artifacts.
        infrastructure[project] = [entry for entry in entries if
            (project == 'gcoms' and entry[0] not in GCOMS_STATUS_FILES) or
            (project == 'gchat' and not controller_only(entry[0]) and (entry[0].startswith(('scripts/', 'release/')) or
                                    entry[0] in ('.dockerignore',
                                        '.github/workflows/native-acceptance.yml',
                                        '.github/workflows/mobile-acceptance.yml')))]
        if project == 'gchat':
            controller[project] = [entry for entry in entries if
                entry[0].startswith(('scripts/', 'release/')) or
                entry[0] == '.github/workflows/controller-release.yml']
        artifacts[project] = [entry for entry in entries
                              if not qualification_only(project, entry[0])]
    return {'schema': 1,
            'artifacts': hashlib.sha256(canonical(artifacts)).hexdigest(),
            'infrastructure': hashlib.sha256(canonical(infrastructure)).hexdigest(),
            'qualification': hashlib.sha256(canonical(qualification)).hexdigest(),
            'controller': hashlib.sha256(canonical(controller)).hexdigest()}
