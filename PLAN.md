## Android retained-role recovery, 2026-09-24

The original laptop unlocked successfully on Android 1017's paired protocol
revision. The phone subsequently captured a separate checkpoint failure:
`invalid owner alias binding or duplicate queue`. GComs live recovery appended
saved draining queues to an already populated owner record. Its regression fails
with that exact error, then passes when applying the complete record replaces the
nonactive collections. Android 1018 carries that repair after cluster validation.
Original identity, channel membership and 92,274,688 verified file bytes remain;
actual two-way message acknowledgments and the full personal transfer are pending.
The paired Linux core passed 65 tests (two existing namespace exclusions), strict
workspace Clippy and both service/desktop release builds. The package is installed
without restarting the original laptop session. A separate retained test profile
reopened and recovered both inboxes without a checkpoint pause.
[Receipt](docs/evidence/owner-role-recovery-20260924/summary.json).
Android 1018 remains in its build workflow; no new store promotion is claimed.

## Owner-budget reopen repair candidate, 2026-09-24

Android 1017 and the next Linux candidate pair with GComs 296d3b6. The new
regression reproduced the laptop's exact "active owner alias expired before
publication" error, then passed with sealed-deadline filtering of public addresses.
The entire node library passed 334 tests (two existing exclusions) and strict
Clippy. Membership, private expired authority and original deadlines remain intact;
normal recovery obtains replacement authority. This pair also contains the bounded
incomplete-referral recovery and first-checkpoint diagnostics. The paired application core passed 65 tests (two existing exclusions) and strict
workspace Clippy. The verified release daemon is installed on the original laptop
profile, with an encrypted backup and no profile reset. Actual user unlock passed;
personal-file continuation remains pending. The exact desktop package is installed
without restarting the view. Android 1017 passed its full build/signing/emulator
workflow and independent publisher-signature verification, then was installed
with `install -r`; UID, initial installation time and saved data are preserved.
[Source/artifact receipt](docs/evidence/owner-recovery-20260924/summary.json).
The phone reopened its original profile. Its later retained-role checkpoint failure
is recorded above; the personal conversation/transfer is not yet qualified.

## Bounded-referral application follow-up, 2026-09-24

The actual NetworkClient workload on 9392040/7cb83b4 missed its original
600-second deadline at 11,010,048 of 13,107,200 bytes, after flushing/reopening
at 1 MiB. A separate continuation on the same profile and exact file completed,
exported SHA-256 937cc6963af82cc978ba3651d87e52888d7b22a754381dae6d7a0d8af716cffd,
and flushed successfully. The normal Linux sender received an authenticated ACK
for the message queued during reopen and the receiver's completion reply.
[Original failure](docs/evidence/owner-recovery-20260924/referral-workload-deadline.json)
and [separate continuation](docs/evidence/owner-recovery-20260924/referral-workload-continuation.json)
remain distinct. The first run shared its cluster worker with compilation, and
profile-save counters include substantial storage time; neither is an isolated
throughput result or a definitive attribution. No durability barrier was removed.

## Android checkpoint diagnostics candidate, 2026-09-24

Android 1016 pairs this application with GComs `b6188f7` to retain the first
checkpoint encoding/storage/lifecycle failure in bounded local native logs.
Physical Android 1015 entered the sticky uncertain-persistence state; restarting
reopened the confirmed encrypted profile without clearing it. This candidate
changes diagnostics, not persistence policy, and is not a repair qualification.
Cluster node failure regressions/Clippy passed. The signed artifact passed a
separate emulator retry and was installed with the existing phone profile retained.
The original emulator ADB failure is retained. This diagnostic installation does
not establish that the uncertain-persistence defect is fixed.

## Actual file/reopen workload, 2026-09-24

The original 12.5 MiB NetworkClient workload on 48ccdfb/15be948 missed its
600-second deadline at 10 MiB. It had flushed/reopened the same encrypted profile
at 1 MiB, retained the channel and resumed automatically. Preserve that
[failed receipt](docs/evidence/inbox-recovery-20260923/cluster-workload-deadline.json).
A separate continuation of the exact file/profile completed and exported all
13,107,200 bytes with SHA-256 4424c323effb2fae3d6a19f391261a20fe2216d8486eba1ea794a5a1dd7b765f.
The normal Linux sender received the recovery reply and authenticated delivery for
the message queued during reopen. [Continuation receipt](docs/evidence/inbox-recovery-20260923/cluster-workload-continuation.json).
A temporary lack of usable independent routes was observed across the hour
boundary despite two ready entries; the complete five-hop route needs additional
fresh middle credentials. A later authenticated read of all eight relays found
eight fresh introductions each; that later read does not prove the missing state
during the outage. No authority extension, short-path fallback or timeout
increase was used. This closes eventual retained-workload completion, not latency
or Android suspend/recovery qualification.

Android 1015 separately entered `owner lifecycle persistence outcome is unconfirmed`.
The retained log lacks the first cause. A process-only restart reopened its saved
profile and recovered both subscriptions; the original personal file remains
retained. Android 1016 adds bounded first-failure diagnostics, passed signed-artifact
emulator retry and is installed on the preserved phone profile. Its original
emulator ADB/cleanup failure remains retained.
The diagnostic GComs source passed 333 node tests, two existing exclusions and
strict Clippy; no underlying persistence repair is claimed.

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
Physical Android 1015 was installed with `install -r`, preserving the profile.
A fresh control channel passed two-way authenticated delivery and a 59,392-byte
download/Save As hash check. Channel/messages survived reopening and generic
activity notifications appeared. The earlier retained-sender join still timed
out. Background recovery initially failed with repeated TLS EOF and a replacement
installation deadline. A [later observation](docs/evidence/inbox-recovery-20260923/delayed-recovery-followup.json)
confirmed recovery on attempt seven after roughly ten minutes: the queued message
became visible and authenticated delivery reached the sender, and the completed
file remained available. This is not a responsiveness pass. The original personal
file remains at 92,274,688 of 122,980,700 verified bytes; its brief pause/resume
experiment preserved those bytes and does not establish a recovery root cause.
The original [physical-device failure checkpoint](docs/evidence/inbox-recovery-20260923/physical-device-check.json)
remains intact.

A separate [cluster NetworkClient control](docs/evidence/inbox-recovery-20260923/cluster-reopen-control.json)
used the same runtime sources with a fresh encrypted profile and no channel/file
backlog. Initial readiness took 84.621 seconds; two flush/reopen cycles took
61.293 and 61.526 seconds. All cycles restored both inbox subscriptions and
flushed successfully. This Linux in-process control confirms baseline recovery
latency but does not reproduce the Android seven-attempt delay. Its initial
missing egress-policy selector failure is retained; the retry reused the exact
binary after selecting the existing policy. No relay policy/runtime was changed.
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
