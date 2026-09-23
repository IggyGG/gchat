# Application delivery plan

## Recovery candidate, 2026-09-23

Exact GChat `48ccdfb` / GComs `15be948` now has a source-bound Linux package
and signed Android 1015. The correction lets durably installed replacement
inboxes return without waiting for stalled peer notification; retained updates
use the existing maintenance retry schedule. Node 333/0/2 and GChat core 65/0/2
passed, with strict Clippy. The two ignored GChat cases require the disconnected
namespace harness; this run does not replace those receipts.

Both updated actual Linux applications reopened their retained test profiles,
exchanged messages with matching IDs and authenticated delivery acknowledgements,
and transferred a fresh 59,392-byte file with matching hash. The receiver also
reopened/exported the prior 75,776-byte file unchanged. A transient independent-
route failure after laptop restart recovered on a later retry; startup latency
is not declared fixed. The personal laptop profile was not changed.

Android 1015 passed build/signing and the installed emulator lifecycle/picker
checks, and its ARM64 APK was independently verified against the publisher pin.
The phone is disconnected from USB: installation, actual phone delivery,
background notifications and the original personal file transfer remain pending.
No new public/store release is claimed. The earlier cold-join deadline/late
Welcome issue is separate and remains unresolved.

[Exact sources, artifacts and evidence](docs/evidence/inbox-recovery-20260923/summary.json).
The release matrix below retains its explicitly dated historical checkpoint.


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
3. The upload helper's false success is fixed in `59b4f5f` (81 checks passed): `altool` returned process status zero
   while its structured result contained `product-errors` and Apple error 409,
   Invalid Export Compliance Code. The original workflow/upload receipt remains
   retained as a false positive; no build was accepted into App Store Connect.
   Prepare the first encryption declaration with the owner, then bind the actual
   Apple-approved configuration to a new verified package before retrying.
   [Retained lifecycle and rejection evidence](docs/evidence/ios-lifecycle-upload-20260921/summary.json)
   keeps upload acceptance, Apple processing and tester availability distinct.
   See the [iOS release procedure](docs/IOS_RELEASE.md).

The owner has selected **France in the first iOS release**. Prepare the French
encryption filing and Apple's export-compliance documentation using the exact
signed application's technical inventory. Publisher contact details and draft
filings stay outside public source and release bundles. No declaration approval,
export code or accepted App Store upload is implied by the completed simulator
checks.

## Repair Mac downloaded-app verification

The owner reported Gatekeeper blocking the published Apple Silicon DMG. Retain
that self-signed release and prepare a separately tagged Developer ID replacement
from the tested application. Apple's certificate API refused creation because it
requires the Account Holder; a CSR is prepared for that account action. The new
controller must re-sign without recompilation, preserve original code/resources
and native provenance, obtain Accepted notarization, staple the ticket and pass
quarantined Gatekeeper and application-lifecycle checks. The Mac signer policy is
separate from the existing Linux/Windows policies and the Gh0st release key.

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
