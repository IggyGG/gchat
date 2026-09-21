# Application delivery plan

Recorded checkpoint: **2026-09-21 17:29 UTC**. Linux, Apple Silicon Mac,
Intel Mac and Android downloads are published. Windows and iOS qualification
runs are pending at this checkpoint; neither is recorded as released here.

## Published clients

Each release retains its own exact GChat/GComs sources and signed manifest.
The [download index](release/downloads.json) records those bindings and asset
URLs; a newer source checkout does not qualify or replace an older artifact.

| Platform | Published release | Completed delivery scope |
| --- | --- | --- |
| Linux x86_64 | [v0.1.3](https://github.com/IggyGG/gchat/releases/tag/v0.1.3) | Signed Debian package and AppImage; retained Linux release evidence. |
| Apple Silicon Mac | [v0.1.4-macos-aarch64.1](https://github.com/IggyGG/gchat/releases/tag/v0.1.4-macos-aarch64.1) | Native CI, pinned Gh0st-signed DMG, copied-app profile/service lifecycle, graphical startup and cleanup. |
| Intel Mac | [v0.1.4-macos-x86_64.1](https://github.com/IggyGG/gchat/releases/tag/v0.1.4-macos-x86_64.1) | Native CI, signed DMG, copied-app profile/service lifecycle, graphical startup and cleanup. |
| Android ARM64 and x86_64 | [ARM64](https://github.com/IggyGG/gchat/releases/tag/v0.1.4-android-arm64.1), [x86_64](https://github.com/IggyGG/gchat/releases/tag/v0.1.4-android-x86_64.1) | Signed APKs and 16 KiB alignment; actual x86_64 emulator profile/background/reopen and DocumentsUI picker checks. |

The Mac downloads are self-signed and not Apple-notarized. Android physical-device,
battery and live push qualification remains open. Installed live-network journeys
and privacy claims require their own evidence; see [TESTPLAN.md](TESTPLAN.md) and
the individual signed manifests for the completed scope and limits.

## Finish Windows and iOS

1. Complete the current [Windows16 native run](https://github.com/IggyGG/gchat/actions/runs/35624488869),
   then its signed NSIS installation, service/reopen, uninstall and signing-store
   cleanup checks. Publish only its exact verified installer. This worker covers
   Windows Server 2022 x64; Windows 11 graphical interaction remains a separate
   follow-up. The [Windows release procedure](docs/WINDOWS_RELEASE.md) defines
   the bindings and checks.
2. Complete the [retained iOS verification run](https://github.com/IggyGG/gchat/actions/runs/35631610692).
   Reuse the already signed build 1.0.9 IPA and the separately linked simulator
   app on the same source pair. The corrected XCTest must pass the full installed
   profile/background/reopen lifecycle with cleanup before upload. Preserve the
   previous failed build and journey receipts. No device-app rebuild is needed
   for this driver retry.
3. After iOS verification, upload the unchanged IPA and record App Store Connect
   acceptance, Apple processing, export-compliance requirements and actual
   TestFlight availability separately. A signed IPA or successful upload alone
   is not an available TestFlight or App Store release. See the
   [iOS release procedure](docs/IOS_RELEASE.md).

Use retained completed native inputs for packaging or harness retries whenever
their source/artifact bindings still apply. Do not rerun a completed platform or
replace a published asset merely to align all platforms on one commit.

## Release policy and continuing work

The owner-approved [production policy](docs/PRODUCTION_RELEASE.md) removes the
24-hour campaigns and statistical privacy release gates. Published clients remain
explicitly **not privacy-qualified**. Authentication, persistence, exact input
bindings, configured signing and the applicable cleanup checks remain required.
Track live-network application journeys, full installed UI interaction and mobile
device/push behavior as explicit unfinished scopes rather than inferring them
from compilation or an offline startup check.

The shared Rust integration is already implemented: GChat uses the GComs
application facade/runtime while retaining its chat archive, encrypted cache
paths/keys and UI responsibilities. Its earlier Linux integration and native
Linux/macOS SDK test/size matrix remain recorded in the
[GComs integration report](https://github.com/IggyGG/gcoms/blob/main/docs/RUST_INTEGRATIONS.md).
Those receipts keep their original source scope. Use the
[platform release procedure](docs/PLATFORM_RELEASES.md) for each new application
download and [TESTING.md](TESTING.md) for consumer development checks.
