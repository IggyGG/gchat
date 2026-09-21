# Application delivery plan

Recorded checkpoint: **2026-09-21 17:36 UTC**. Linux, Apple Silicon Mac,
Intel Mac and Android downloads are published. Windows needs a native retry
after a test-fixture correction. The iOS simulator lifecycle passed, but Apple
rejected the upload for missing export-compliance information; neither Windows
nor iOS is recorded as released here.

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

1. Preserve the [Windows16 native run](https://github.com/IggyGG/gchat/actions/runs/35624488869):
   its GChat native CI passed; GComs rejected two pre-created routing directories
   because the tests configured private ownership only on Unix. Apply the tested
   cross-platform fixture setup without changing production access controls,
   then finish native qualification, signed NSIS installation, service/reopen,
   uninstall and signing-store cleanup. The
   [Windows release procedure](docs/WINDOWS_RELEASE.md) defines the bindings.
2. Preserve the passing installed iOS simulator profile/background/Keychain/reopen
   journey from [retained verification](https://github.com/IggyGG/gchat/actions/runs/35631610692).
   It tested the existing simulator app and reverified signed build 1.0.9 without
   recompiling or resigning the device app. Physical-device and live-network
   behavior remain separate scopes.
3. Fix the upload helper's false success: `altool` returned process status zero
   while its structured result contained `product-errors` and Apple error 409,
   Invalid Export Compliance Code. The original workflow/upload receipt remains
   retained as a false positive; no build was accepted into App Store Connect.
   Prepare the first encryption declaration with the owner, then bind the actual
   Apple-approved configuration to a new verified package before retrying.
   Upload acceptance, Apple processing and tester availability remain distinct.
   See the [iOS release procedure](docs/IOS_RELEASE.md).

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
