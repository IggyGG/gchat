## Independent contacts, preferences and presence

With the paired GComs checkout, run `cargo test --workspace --all-features contact
-- --nocapture` and the `chat_service::preferences` filter through the same
workspace feature set, then strict all-target/all-feature Clippy. The integration
case creates two real protocol identities without channels, exchanges signed
cards, verifies recipient delivery and away presence, tests aliases/highlights/
mute/ignore/unignore, and reopens the encrypted archive to verify block/history/
preference persistence. Unit cases cover exact-peer receipts, stable-ID dedup,
notice-loop prevention, presence opt-out/replay/expiry and rollback isolation.

Regenerate `gchat-types` and its `--rpc` export from the tested source, regenerate
the JavaScript RPC bindings, then run workspace Svelte checks, UI tests and the
production build. Preserve the normal ordinary-message bound; only explicit
contact-card import commands receive the larger bounded input envelope.

## IRC parity and hosted archive isolation

Run paired GComs runtime/service/MLS checks, then `cargo test --workspace
--all-features -- --test-threads=1` and strict workspace Clippy through the normal
paired-source configuration. Run `python3 scripts/check-source.py`, regenerate
Rust/TypeScript RPC contracts, and run `npm run check`, `npm test`, `npm run build`.
Require archive event sequence/dedup checks, separate service acceptance versus
recipient delivery, and a real encrypted sidecar downgrade/reopen test: an older
client rewriting `.service` must leave hosted messages and committed event cursor
intact. Corrupt hosted state must fail closed. Include notices/actions and bounded
IRC formatting in both TUI and shared UI validation. No notice may auto-reply.

Keep native, installed-network, 500-member churn/offline/files and timing evidence
separate from component tests. Large-channel recipient receipt completion remains
on covered transport and is measured separately, per the user's chosen tradeoff.

## Release tooling portability

`release-tools-check.yml` runs release tooling and retained Mac rollback orchestration
on native Linux and Windows without building applications. Manifest paths use ZIP
POSIX syntax on both hosts and reject drive, backslash, absolute and parent paths.
Only the POSIX coordinator daemon/flock test is platform-specific; ledger and
coordinator state-machine tests run on both. Artifact receipts remain source-bound.

## GCHAT-STORE-2 — Apple marketing asset checks

Run `node --check marketing/app-store/retro-v1/export.mjs`, the exporter with the
existing fixture server, and `python3 scripts/check-source.py`. Require four
1290 × 2796 and four 2048 × 2732 opaque JPEGs, zero capture overflow/browser
errors, no text/frame overlaps and a fitting gallery at 1440/768/375 pixels.
Apple must process every upload as `COMPLETE`; verify dimensions, file sizes,
ordered screenshot IDs and exact metadata readback. MD5 is supplied at upload
commit; do not claim checksum readback when Apple returns null. Preserve the old
assets before replacing them. The iOS draft's missing build and pending encryption
review remain separate release gates, not failures of the asset upload.

## GCHAT-STORE-1 — marketing asset checks

Run `node --check marketing/play-store/retro-v1/export.mjs` and
`python3 scripts/check-source.py`. Start `node ui/browser/server.mjs`, then run
`node marketing/play-store/retro-v1/export.mjs` to capture synthetic conversations
through the real Svelte UI and export the five artboards. Require zero browser
errors/capture overflow, decodable images, a 1024 × 500 opaque feature graphic,
and four 1080 × 1920 JPEGs. Review the gallery at desktop and mobile widths for
readable text and horizontal overflow. Compare every app frame with the released
Android build before upload; native parity is not established by browser renders.
Existing native/security/release acceptance requirements remain unchanged.

## Release admission and approved Windows size

Run release_inputs_test.py, release_prepare_test.py and the existing release
coordinator/ledger/config tests. Require controller-only changes to preserve the
artifact reservation and original manifest; unknown/runtime/build inputs and
executable modes must invalidate it. A pending qualification observation is not
a pass. Run native_network_test.py and windows_installer_test.py: reject 4 MiB
outside Windows, wrong retained binary/source/candidate, changed deadlines, and
all existing authentication/hash/reopen/cleanup failures. The actual signed
Windows 36 installer must separately pass its fresh 4 MiB interrupted journey.

## Windows 36 retained diagnostic inputs

Run `native_network_test.py` and `windows_installer_test.py`. The additional
immutable candidate uses the existing failure/cleanup verifier and original
180-second file budget. Fresh actual Windows network execution remains required.

## Retained iOS startup recovery

Run `ios_lifecycle_test.py` and `ios_retained_test.py` through unittest discovery.
Require exact original failed startup/native/binary bindings, owned-device removal,
new native and lifecycle passes, and complete fresh cleanup. Reject crashes, other
cleanup errors, substituted receipts, changed binaries, skipped native tests and
any attempt to promote the original failed verdict. Native simulator execution
remains a separate required gate before upload.

## Platform acceptance isolation

Run `python3 -m unittest discover -s scripts/tests -p 'release_config_test.py'`.
Require unique platform acceptance paths under a custom state directory for both
execution and reconciliation. SDK compatibility must continue using its own
consumer verifier. These checks do not qualify an application or installer.

## Mac network receipt binding

Run `python3 -m unittest discover -s scripts/tests -p "macos_*test.py"`.
The Mac wrapper consumes its protected invitation before spawning children and
removes it on failure. Tests reject failed network execution despite offline
success, substituted executable/harness receipts, absent post-recovery ACKs and
completion past the original 180-second deadline. Native real-package execution
remains separate from these mocked orchestration checks.

## Retained failed network artifacts

`windows-verify.yml` supports the explicitly pinned Windows 29 artifact after its
failed network journey. Reject unrelated installer failures, changed source/archive
bindings, incomplete cleanup, changed trust stores and failed offline service checks.
Explicit fixture diagnostics must retain provider/environment isolation. Cluster
`native_network_test` and `windows_installer_test`: 29 tests passed. The real Windows
journey remains separately required with the original 180/600-second budgets.

## Original Mac packaging identity

A packaging controller may differ from the native-qualified application. Its
optional coordinator manifest must match the exact original commit/tree pair and
committed app version; a modified digest, another source, or another version is
rejected. Bind and recheck that manifest throughout recovery, retain updater
artifacts, and attest the original candidate. Eighteen cluster packaging tests
pass; packaging/native application outcomes remain separate.

## Protected native worker inputs

Windows release verification now requires the explicit environment-backed network
fixture. Tests reject missing input before installation, consume it before child
execution, and remove the private temporary file even on failure. Existing exact
binary/native binding, authentication, failed-network rejection and cleanup tests
remain mandatory. Mac packaging checks require Developer ID inputs in both signing
stages and updater keys in the packaging stage. Cluster run: 42 focused tests pass;
native application gates retain their separate source-bound outcomes.

## iOS lifecycle input focus

Dismiss the native keyboard and wait for viewport geometry to settle before
revealing the confirmation field. Require that field to be fully inside the
main viewport before focusing and typing. Keep the original create/unlock,
default-off background lock, opted-in Keychain resume, relaunch and cleanup
assertions. Run the native XCTest against the retained app without rebuilding
or re-signing it; preserve the original workflow failure separately.
[Exact simulator evidence](docs/evidence/ios-lifecycle-focus-20260927/summary.json).

## Native external-probe exclusion inventory

Native CI records three additional explicit exclusions: the live deployed-relay
probe (requires a separately authorized fresh bundle), the external native
five-hop bootstrap probe, and the nested native TLS/HTTP2 probe. These require
separate provisioned artifacts and do not constitute desktop application coverage.
Accept only their exact GComs test names in receipt validation; reject unknown
names and using these exclusions in GChat reports. Keep failed native counts,
incomplete harnesses, source bindings and installer acceptance mandatory.
The Windows candidate's original verifier rejection remains retained. Its native
result is 1004 GComs passes / 9 explicit exclusions and 186 GChat passes / 1
namespace exclusion, not successful execution of the excluded tests.

## Ownership-transfer fixture admission

Subscribe to the owner's events before admitting the successor, then require the
authenticated bootstrap-metadata delivery event before requesting transfer. A
successful receiver join does not establish that its ACK has reached the owner.
Keep the production pending-message guard, event-lag failure, channel identity,
successor admission, authenticated leave/close and reopen assertions unchanged.

Retained-profile diagnostics must follow one checkpoint lineage. After a copy has
transmitted, do not restart an older snapshot of that identity: replay and sender
ratchet reuse can invalidate the result. Keep emulator and copied native instances
mutually exclusive, and label cross-platform diagnostics separately from app tests.

## Windows updater signing scope

Verify both updater-key environment entries belong to the NSIS build step,
then require the normal signed-installer, pinned signature and installed-profile
lifecycle checks. A certificate-only preflight cannot qualify updater signing.
Retain run 36328979195's missing-key failure and its completed native checks.

## Publisher host scope

Download-page feed-lock tests run on the POSIX publication host alongside signed
feed/APT tests. Native Windows retains all portable artifact selection and source
receipt tests; it does not host the Linux publisher. Keep all four page tests
mandatory in Linux CI. The retained Windows 0.1.18 failure was an unsupported
`fcntl` import in those four server-side tests, before native Rust validation.

## Current versus archived website downloads

Website tests require one Play link for both Android architectures, no archived
installer links for pending targets, and availability text limited to current
platforms. Reject arbitrary managed URLs and unsupported pending target names.

## Website follows qualified Linux publication

Run `release_publish_test.py`, `website_test.py` and `website_deploy_test.py`.
Require immutable package and signature links, exact source bindings, HTML escaping,
idempotent publication and refusal of stale replay or changed package bytes. The
website must link the managed Linux endpoint instead of an old static installer.
After deployment, verify public page bytes, package hash and unchanged live updater
identity. This changes release delivery only; no native build receipt is relabelled.

## Play release metadata

`release_stores_test.py` requires a display name at most 50 characters, exact
version code and complete immutable journal identity. Preserve unknown-outcome
reconciliation; never create a second edit/upload to repair metadata.

## Linux publication reference regression

Run `python3 -m unittest discover -s scripts/tests -p release_publish_test.py`.
Repeated references to the same verified file must publish once; conflicting
hashes, distinct Debian packages and missing/ambiguous signatures must fail.
Missing package evidence must fail before changing the updater pointer.

## Windows update-owner fixture

Run `maintenance_owner_lease_and_prepared_exit_are_enforced` with a directory
secured by the production cross-platform helper. Keep Windows ACL and Unix mode
checks enabled; do not skip the owner-lease and prepared-exit assertions.

## Portable SDK archive publication

Run `python3 -m unittest discover -s scripts/tests -p release_sdk_test.py`.
Require handles closed before archive verification and rename; interrupted or
corrupted copies leave no temporary file or published index. Retrying an exact
release is idempotent; another source pair cannot replace its version. Validate
on native Windows as part of its normal CI.

## Idle presentation CPU regression

Run the core library chat-service tests, full core integration tests and strict
all-target/all-feature core Clippy against the paired GComs source. Require four
waiting views with 4,096 retained operations to share one idle projection;
lock must wake every view and remove private cached results. Verify local send,
cancelled listener, incoming delivery/ACK, membership/topic, archive failure and
reopen behavior. Unchanged file observations must yield no sidecar candidate,
while a failed save leaves the same update retryable.

Run the ignored `idle_cpu_large_history_measurement` separately on a quiet Linux
worker for three 60-second samples of process CPU with four views:

```sh
cargo test --release -p gchat-core --features gc2-carrier --lib \
  idle_cpu_large_history_measurement -- --ignored --nocapture --test-threads=1
```
 Use the identical fixture and optimization profile on the unmodified
baseline and candidate. Export and hash each executable, verify its source
package and candidate-only test list, and retain both results. Debug-build
measurements remain separate; they are not installed-release CPU estimates.
Run the bounded application file/restart/hash gate; keep the 1 GiB campaign
independent. Never use the user's personal profile for destructive tests.

## Responsive carrier release binding (2026-09-25)

Release tooling accepts distinct profile-22 and profile-46 contracts and rejects
mismatched observed profiles. The three changed release tool/test files are
byte-identical to the paired GComs files tested by the 37 passing release-tool
checks. This is tooling validation; no existing native, installed, store or
privacy receipt is relabelled. Current GComs source sends real data immediately
with independent 10–10,000 ms randomized interactive cover. Older peer and policy
cache compatibility requires the staged rollout described in PRODUCTION_RELEASE.md.

## Runtime rollback data compatibility

On a copy of a completed encrypted application profile, run current → compatible
predecessor → current in an empty disconnected namespace. Require identical
identity and nonempty channel set, exact complete-file export on every phase,
clean shutdown and unchanged source fixture bytes. Keep signed installers,
network reconnection and pending-message delivery outside this limited proof.
[Candidate14/candidate12 receipt](docs/evidence/retained-rollback-20260924/summary.json).

## Disposable mobile lifecycle gates

Run four independent Android AVDs with explicit serials and private profiles,
retaining every failure and cleanup result. Use a verified node-local SDK copy
when shared image storage cannot meet the unchanged 180s boot deadline. Check
profile creation, background/relaunch and picker select/cancel, then visually
inspect retained screenshots. Use native XCTest for the Mac iOS simulator.
Keep exact APK/simulator-source bindings; lifecycle success cannot qualify
network messages, files, live push or a later protocol build. Physical devices
are deferred. [Completed baseline](docs/evidence/emulator-lifecycle-20260924/summary.json).

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


UX-1 local Linux installation completed 2026-09-25: signed Debian package from
GChat bf021883/GComs e8546096 installed and exact executable hash verified.
Packaged and installed lifecycle tests pass; native WebKit first-run, retained
identity, single-error retry, picker/cancel/original PNG, screenshot rejection,
keyboard and 320/1100px checks pass. Full coherent runtime gates pass (168 Rust,
25 native, 59 UI unit, 74 browser; Python 449 pass/5 skips), with strict unchanged
runtime/dependency binding for the final policy/tooling delta. Both dependency
audits pass; five-relay invitation/chat/file/restart journey passes in 182s.
Launchers, fleet process and updater preserved; verified rollback retained.
Evidence: docs/evidence/ux-cards/signed-local-summary.json and docs/UX-CARDS.md.
No public release. Native save/export/drop, other OS, screen-reader/usability
sessions and CMD target selection remain unfinished scopes.

## Bounded release files (2026-09-25)

Use `gchat-turnover.py --mode file-recovery --release-check` with the frozen paired build and qualification host: 16 MiB, 180-second completion and 600-second total ceiling. Require abrupt restart, retained pieces/identity, authenticated chat ACK, final hash and reopen/export. The separate 1 GiB campaign is nonblocking; retain its failed deadlines. Authentication, persistence, signatures and rollback remain mandatory.

## Disclosed latency policy (2026-09-27)

Owner-approved: publish with slow joins/reconnects disclosed and optimize latency
next. R04's 30-second join and R03's 10-second reconnect targets are nonblocking;
authentication, delivery, persistence, signatures and rollback remain mandatory.
Publish the limitation on the downloads page. Existing frozen candidate checks
and recorded failures retain their exact source and outcome bindings.
## Retained Windows network qualification (2026-09-28)

- `scripts.tests.native_network_test`: reject stage/global deadline overruns,
  including a successful response arriving after its original budget.
- `scripts.tests.windows_installer_test`: network failure, different executable
  binding, or a surviving child must fail even when offline lifecycle passed.
- The portable runner must pass against the retained signed Linux executable
  before its native Windows dispatch. Bind the final helper bytes, build manifest,
  native receipt, executable and source pair separately from its prototype run.
- Native Windows uses immutable artifact 10942212091 from successful run
  36345150554. Existing offline installer checks remain mandatory. Upload only
  reports/logs; exclude disposable profile directories and remove the temporary
  invitation. A native result is required before claiming Windows network success.

Release stabilization follow-up, 2026-09-28: retained Windows 36 run
36471307753 passed the owner-approved 4 MiB interruption/reopen/exact-hash journey
in 120.594 seconds (282.844 seconds overall), with authenticated bidirectional
messages and installation/profile/trust cleanup. The original 16 MiB failure is
retained. The same iOS 36 simulator executable passed profile/background/manual
unlock/consented Keychain/relaunch after the UI test committed native keyboard
input before observing the field. No app recompilation or signing change was
needed. These gates alone do not prove Windows rollback or iOS network recovery,
store availability, physical devices, live push or privacy qualification.

## IRC hosted/contact files

Qualify the existing FileRequest and binary piece API with hosted and independent
contact conversation IDs. Verify no legacy scope mapping, whole-file hash,
resumption, block/unblock and locking, handle-collision rejection and combined
cache quota accounting. Repeat the actual independent-contact journey and legacy
file controls after the routing change; the older contacts full-suite receipt
qualifies only its recorded source pair.

### Contact file authorization and recovery

Run the full workspace suite and strict Clippy. The independent-contact journey
must share, accept and export a file using DirectMessage permission without
ChannelMember, retain history across reopen, and reject new file offers after
block. File snapshots and binary I/O enforce the stored conversation's capability.
Quota, one-time scoped activity and retryable file errors have separate assertions.
Large partial-file restart and authenticated completion are also required in the
paired GComs runtime gate; a small complete file is not recovery qualification.

## Opt-in hosted directory and contact-only unlock

Require `/hosted list` globally and `/list` only in hosted context; preserve legacy
list behavior. Validate 64-hex pagination cursors and explicit operator `/publish`
controls against the paired service/runtime/IPC24 tests. Run the independent
contact file journey with DirectMessage but without ChannelMember authority;
IdentityRead alone must not unlock a messaging service.

## Scoped historical names

Run `hosted_name_history` and the hosted archive projection/rollback cases.
Require messages before and after a rename in one recovered batch to retain the
correct respective names even when the supplied snapshot already has the new
name. `/whowas` must retain observations after departure and reopen, remain bounded,
and never search another channel. Existing archives without observations must load.
The directory command-scope test also preserves global `/list` from a contact.

## Immediate hosted send feedback

Require a queued text/action/notice to appear as LocalAccepted before any network
event, with its operation ID retained in the encrypted archive. Replay its message
and service acceptance without adding another bubble or promoting it to Delivered.
Run the hosted archive cases and strict workspace Clippy against the paired runtime;
the runtime's stalled-response/retry/reopen test separately proves local admission
is not blocked by remote I/O.
