## Owner-budget reopen candidate

[Exact source/artifact receipt](docs/evidence/owner-recovery-20260924/summary.json):
GChat 20979ba / GComs 296d3b6; node 334/0/2 and application core 65/0/2, strict
node/workspace Clippy, paired Linux daemon/desktop builds and signed Android 1017
emulator lifecycle checks passed. The real constructor regression first reproduced
`active owner alias expired before publication` with the old implementation.
Personal encrypted profiles were preserved during installation; successful user
unlock and the original conversation/file completion remain required.

## Retained 12.5 MiB application workload follow-up

Use the actual NetworkClient and normal Linux sender, one admitted channel/file
and one queued message. Flush/reopen after 1 MiB, retain exact file identity and
bytes, export the completed file and compare SHA-256. The original 600-second
case failed at 10 MiB; its separate continuation completed with matching hash,
queued-message delivery and successful shutdown. See PLAN.md for both receipts.
The later bounded-referral pair likewise missed its original deadline at
11,010,048 bytes; its separate continuation completed the same 13,107,200-byte
file with hash equality, authenticated queued-message delivery and shutdown flush.
Do not relabel either original deadline or infer Android OS responsiveness. The
physical-phone uncertain-persistence pause requires a captured first cause and
its own repair validation.

# Application qualification status and remaining checks

## Inbox recovery candidate, 2026-09-23

[Bound receipt](docs/evidence/inbox-recovery-20260923/summary.json): GChat
`48ccdfb` / GComs `15be948`; node library 333 passed/2 existing exclusions,
GChat core 65 passed/2 disconnected-namespace exclusions, strict node and GChat
workspace Clippy, unchanged paired sources, Linux packaging, signed Android
1015 and emulator installation/reopen/picker checks. Preserve the original
Linux missing-development-library failure and the successful packaging-only
retry. Transport interruptions during evidence export are retained separately.

Actual Linux application checks use two preserved test profiles and the same
installed executable hash: reopen both, verify two inbox subscriptions, submit
once in each direction, match recipient IDs/content and authenticated sender
delivery, then transfer/export and hash-check the new 59,392-byte file. The old
75,776-byte file must also export unchanged after receiver restart. These passed;
transient route recovery delay is still recorded.

Physical-device checks now have a [separate receipt](docs/evidence/inbox-recovery-20260923/physical-device-check.json):
profile-preserving 1015 installation, fresh control-channel join, two-way
authenticated delivery, retained channel/messages and actual 59,392-byte file
export with matching SHA-256 passed. Generic activity notifications were observed
while backgrounded; this does not uniquely identify their triggering message.
The earlier retained-sender join timed out. A later background/reopen attempt
initially failed retained and replacement inbox recovery with TLS EOF and a
replacement-install deadline. Preserve that failed checkpoint. The
[later follow-up](docs/evidence/inbox-recovery-20260923/delayed-recovery-followup.json)
records authenticated delivery after roughly ten minutes/seven recovery attempts
and the completed file surviving reopen; do not call its latency acceptable.

The [cluster control](docs/evidence/inbox-recovery-20260923/cluster-reopen-control.json)
passed fresh provisioning and two normal InstanceHost flush/reopen cycles using
explicit NetworkClient on a current-thread runtime. Readiness was observed at
84.621/61.293/61.526 seconds, polling every ten seconds. It uses the frozen
48ccdfb/15be948 sources with no additional registry packages. It is Linux, has
no channel/file backlog, and does not qualify Android suspend/resume or explain
the longer physical-phone failure. Preserve the initial missing-policy-selector
run and the unchanged-binary retry separately. The worker is disposable; logs,
probe source/lockfile and executable hash remain retained.

Keep the original personal conversation/file and cold-join/late-Welcome failures
open. The personal file remained at 92,274,688/122,980,700 verified bytes after
normal pause/resume. Save As also surfaced an unwanted transient background-paused
UI error. No speculative runtime repair or new Android build follows from these
controls alone.


Recorded checkpoint: **2026-09-21 17:36 UTC**. The completed scopes below come
from retained release manifests and publication receipts. Windows16 failed in
GComs after GChat native CI passed. iOS installed simulator validation passed,
but the Apple upload was rejected. The workflow reported a false upload success;
its original evidence remains retained and does not qualify distribution.
The [compact iOS receipt](docs/evidence/ios-lifecycle-upload-20260921/summary.json)
binds the passing lifecycle, rejected upload and tested parser correction.

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
The reported Gatekeeper warning now has a dedicated repair: a new Developer ID
artifact must retain the original app/native identity, compare code/resources
without signatures, retain Apple's Accepted submission, validate the stapled DMG
and pass quarantine-aware assessments with Gatekeeper enabled. Repeat the copied
application service/GUI lifecycle on the replacement. Helper unit passes alone
do not qualify the new signature, Apple acceptance or downloaded-app launch.
Android ARM64 compilation/signing does not establish physical-phone execution;
the same-source x86_64 emulator receipt retains that distinction. See
[Android qualification](docs/ANDROID_RELEASE.md) for the exact workload.

## Pending Windows gate

[Windows16](https://github.com/IggyGG/gchat/actions/runs/35624488869) retains its
passing GChat native CI and failed GComs `node_profile` ownership checks. The
correction makes both pre-created fixture directories private on Windows as
well as Unix and explicitly tests refusal to repair an existing nonprivate
directory. Production ownership checks remain unchanged. Validate the corrected
frozen pair, then require pinned Authenticode signing, actual NSIS installation,
matching installed executable/uninstaller signatures, profile reopening,
uninstall/resource cleanup and unchanged persistent certificate stores.

The result is Windows Server 2022 x64 MSVC/installer-service qualification.
Windows 11 graphical interaction, SmartScreen reputation and installed
live-network messaging/files remain separate. Local Python fixture checks are
not a substitute for that native result. See [Windows release checks](docs/WINDOWS_RELEASE.md).

## Pending iOS gate

[Retained verification](https://github.com/IggyGG/gchat/actions/runs/35631610692)
passed the native installed simulator journey: one test, zero failures/skips,
75.851 seconds. It used the existing simulator executable, exercised fresh
profile creation, background locking, manual reopening, consented Keychain
resume and process relaunch, and completed cleanup. Original source/device IPA
and previous failed journey receipts retain their identities and verdicts.

The subsequent `altool` upload returned zero but reported `product-errors`:
Apple 409 Invalid Export Compliance Code. Treat that upload as rejected despite
the original helper/workflow success. The upload-result regression must reject
error JSON, failure markers, empty or ambiguous output regardless of exit status;
only explicit structured success can establish upload acceptance. The first
Apple encryption declaration is not yet configured. Preserve the signed IPA;
any later package configuration/signature needs its own binding. Physical
devices, live onboarding/chat/files, battery and live APNs remain unqualified.
An APNs entitlement is not a push result. See [iOS release checks](docs/IOS_RELEASE.md).
France is included by owner instruction. The unsigned declaration draft and
technical inventory do not constitute a filing, approval or export-compliance
code. Retain the original Apple rejection until an actual accepted upload and
processing result exist.

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
