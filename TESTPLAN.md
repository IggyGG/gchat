# Application qualification status and remaining checks

Recorded checkpoint: **2026-09-21 17:29 UTC**. The completed scopes below come
from retained release manifests and publication receipts. Windows16 and the
iOS retained-artifact verifier are still pending at this checkpoint. A running
job, a source test, and an installed application pass are distinct evidence.

## Completed release evidence

| Artifact | Exact source pair (GChat / GComs) | Completed checks |
| --- | --- | --- |
| Linux 0.1.3 `.deb` / AppImage | `102e846` / `27c3bf1` | Retained Linux qualification and signed public delivery; [release manifest](https://github.com/IggyGG/gchat/releases/download/v0.1.3/release-manifest.json). |
| Mac ARM64 0.1.4 DMG | `d78b644` / `3185715` | Native GChat 171 Rust passes / 1 explicit exclusion; GComs 876 / 6. The unchanged signed DMG passed separate signature, copied-app profile/reopen, graphical startup and cleanup checks; [manifest](https://github.com/IggyGG/gchat/releases/download/v0.1.4-macos-aarch64.1/platform-release.json). |
| Mac Intel 0.1.4 DMG | `ab3697a` / `398c751` | Native GChat 160 Rust passes / 1 explicit exclusion; GComs 926 / 6. Signed packaging and actual copied-app service/GUI startup with cleanup passed; [manifest](https://github.com/IggyGG/gchat/releases/download/v0.1.4-macos-x86_64.1/platform-release.json). |
| Android 0.1.4 ARM64 / x86_64 APKs | `ab3697a` / `398c751` | Both native packages, pinned signing and 16 KiB alignment passed. Actual x86_64 API35 profile creation, background locking, reopening, process restart and DocumentsUI cancellation/selection passed; [ARM64 manifest](https://github.com/IggyGG/gchat/releases/download/v0.1.4-android-arm64.1/platform-release.json), [x86_64 manifest](https://github.com/IggyGG/gchat/releases/download/v0.1.4-android-x86_64.1/platform-release.json). |

The ARM Mac verification reused the signed DMG after an earlier packaging-helper
failure. That failed receipt remains failed: its original post-build source and
derived-input rechecks did not execute, and the original optimized native-CI
executable was unavailable for byte comparison. The separate recovery verified
retained source/dependency inputs, native signatures and the actual artifact.
The manifest preserves these limitations; they do not apply by inference to
the independently completed Intel build.

Mac startup checks cover the native window, authenticated IPC, default GC2
service selection, encrypted-profile reopen and wrong-passphrase refusal with
network bootstrap disabled. They do not prove an installed live-network
chat/file journey or full rendered interaction. The pinned Mac signatures do
not establish Apple notarization or downloaded-app Gatekeeper acceptance.
Android ARM64 compilation/signing does not establish physical-phone execution;
the same-source x86_64 emulator receipt retains that distinction. See
[Android qualification](docs/ANDROID_RELEASE.md) for the exact workload.

## Pending Windows gate

[Windows16](https://github.com/IggyGG/gchat/actions/runs/35624488869) must complete
both native CI entrypoints, then pinned Authenticode signing and the actual NSIS
installation. Require matching installed executable and uninstaller signatures,
fresh/unlock/shutdown/reopen service behavior, uninstall/resource cleanup, and
unchanged persistent certificate stores. Retain earlier failures separately.

The result is Windows Server 2022 x64 MSVC/installer-service qualification.
Windows 11 graphical interaction, SmartScreen reputation and installed
live-network messaging/files remain separate. Local Python fixture checks are
not a substitute for that native result. See [Windows release checks](docs/WINDOWS_RELEASE.md).

## Pending iOS gate

[Retained verification](https://github.com/IggyGG/gchat/actions/runs/35631610692)
must reverify the existing signed build 1.0.9 IPA and same-source simulator app,
then run the corrected full XCTest on those simulator bytes. Require one passing
test, zero failures/skips, unchanged executable, profile/background/reopen
assertions and complete simulator cleanup. Original build and journey failures
must retain their verdicts and hashes.

Only after this pass may the verified original IPA be uploaded. Record upload
acceptance, Apple processing, export compliance and tester availability as
separate outcomes. Physical devices, live network onboarding/chat/files, battery
and live APNs delivery remain unqualified by this fixture. An APNs entitlement
is not a push-delivery result. See [iOS release checks](docs/IOS_RELEASE.md).

## Evidence and regression rules

- Bind each check to the complete source pair, dependency inputs, executable and
  installer hashes; preserve original logs, failures and cleanup receipts.
- Keep source browser tests separate from installed-app execution. Use completed
  native receipts for an unchanged packaging/harness retry; rerun affected checks
  when source or effective dependencies change.
- Follow [TESTING.md](TESTING.md) for Rust, generated-contract, UI and consumer
  checks, and [platform delivery](docs/PLATFORM_RELEASES.md) for signed publication.
- Keep the earlier shared Rust consumer/cache regression and Linux/macOS SDK
  size evidence in the [GComs integration report](https://github.com/IggyGG/gcoms/blob/main/docs/RUST_INTEGRATIONS.md)
  bound to its original inputs.
- Apply [production-minutes-v1](docs/PRODUCTION_RELEASE.md): statistical privacy
  and 24-hour campaigns are no longer release gates. Privacy improvements and
  the other unqualified scopes stay explicitly disclosed; no privacy pass is
  inferred from these releases.
