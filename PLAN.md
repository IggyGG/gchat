## Current IRC small-room gate — 2026-09-30

The same `40b440d` / `c5bbfe8` release binary also passes live09: 113ms local
feedback, 3.933s display plus covered recipient receipt, 7.857s offline-owner
admission, 164.709s resumed 16MiB verification and 329.148s full file workflow.
Topic pending followed by authenticated handoff, moderation/voice/notices,
offline recovery, retained partial pieces and the exact exported hash pass.
Owned daemons stopped and the bootstrap grant was revoked. Evidence:
`docs/evidence/irc-hosted-live-20260930/replay-09.json`. The separate 500-profile
protected-network campaign has now started; it has no passing result yet.

## Current IRC protected-network smoke — 2026-09-30

GComs `40b440d` / GChat `c5bbfe8` passes the actual 12-profile correctness and
latency campaign. Returning-owner recovery is 6.130s against the unchanged 10s
target; ordinary offline plaintext recovery is 6ms. Ten simultaneous senders
produce 110 verified covered recipient signatures in each of the baseline and
mixed-file phases. Resumed 16MiB verification takes 106.008s, with the full file
workflow at 257.472s and the exact expected export hash. Removal confidentiality,
independent replacement/no old ciphertext, resource sampling and cleanup pass.
All owned daemons stopped and the bootstrap-only grant was revoked. The original
14.537s recovery miss remains retained. See
`docs/evidence/irc-hosted-capacity-20260930/smoke-12-02.json`.

Cold startup used four independent profiles at a time, with sequential joins;
whole-run elapsed improvement is not a production-code-only comparison. The
current small-room live09, full workspace/paired archive gates and separate
500-member runtime/application/native qualifications remain open.

The follow-up `contacts-10.log` passes the same contact unit/integration checks and
strict Clippy on paired GComs `4e5df35`. A full receipt outbox now leaves incoming
messages durable while continuing to process other receipts and drain outbound
ACKs. `/server-info` also displays service extensions and configured request rates.

## IRC contact and workflow checkpoint (2026-09-29, Codex)

Independent signed-card contacts now deliver through the durable application
inbox without a shared channel. Exact-content authenticated receipts, stable IDs,
block persistence, encrypted sidecar rollback isolation and opt-in expiring
presence have focused and real two-instance coverage. Local mute, scoped ignore,
highlights and command aliases use the same service API in every attached UI.
`contacts-09.log` passes four contact-related unit tests, the real two-instance
contact/presence/preferences/reopen test, and strict workspace Clippy. Earlier
fixture, input-limit, durable-send and binary-presence-codec failures are retained.
`contacts-07.log` separately passes the scoped preference/alias unit test.

`contacts-ui-02.log` passes both Svelte checks, 63 UI tests and a production build
with refreshed generated API/RPC contracts. `contacts-ui-01.log` retains a stale
generator-output failure; regeneration from the touched source corrected it.
Full updated workspace,
independent and hosted files, service deployment and actual 500-member network/
native qualification remain open. This checkpoint is not a parity release.

## IRC parity implementation (2026-09-29, Codex)

In progress: the shared application now projects opt-in hosted channels from the
GComs runtime, with durable event consumption, explicit channel moderation,
single-use invitations, typed actions/notices, role/presence display and generated
API v3 contracts. Legacy archives remain separate. Hosted history has its own
versioned encrypted sidecar to survive an older GChat rewriting legacy settings.
A failed archive save retains runtime events for retry and is visible as an error.

Component evidence is retained under `test-evidence/irc-parity/`: initial UI
checks, 62 UI tests and production build passed in `hosted-ui-01.log`; the initial
strict Rust workspace check passed in `hosted-client-05.log`. The fresh full Rust
suite (`hosted-client-07.log`) and subsequent archive-isolation checks have their
own source boundary. These are component checks, not installed-network/native
qualification. The full deliverable ledger remains in paired GComs
`docs/IRC_PARITY.md`; receipt recovery, independent contacts/files, encrypted topic
handoff, remaining client workflows and 500-member end-to-end qualification are
not complete.
## Owner-controlled membership recovery (2026-09-29)

Added shared desktop/mobile recovery preview and explicit confirmation, `/recover-membership`, and normal SDK/local IPC support. The disposable GChat test reproduces a pending epoch-2 commit, revokes the selected unavailable leaves, then proves ordinary invitation admission, message ACK, kick and reopen. Exact affected-source and installed-profile results belong to the paired membership-recovery receipt.

## Remaining native checks completed — transfers still block (2026-09-29)

The preserved Intel run 36507553193 and Windows run 36511023125 both finished.
Full native qualification and configured installer signing passed; each actual
installed-network check failed its original 16 MiB / 180-second file deadline.
Intel 0.1.49 reached 13893632 bytes (13.25 MiB); Windows 0.1.50 reached
9699328 bytes (9.25 MiB). Both retained pieces across restart, recorded two
pre-recovery authenticated message ACKs, and passed child/profile/installation
cleanup with unchanged inputs and binaries. Neither completed file export or
post-recovery ACK qualification. No Mac rollback was dispatched after failure.

Immutable archives and source-bound reports are retained in coordinator state;
independent download hashes and report bindings are recorded at
`target/release-closeout-20260929/mac49-intel-review.json` and
`target/release-closeout-20260929/windows50-review.json`. The older published
Windows release and its separate approved 4 MiB receipt remain unchanged.
SDK 0.1.49 is available; iOS encryption remains IN_REVIEW with France included.
Further Mac throughput investigation awaits the pending scope decision after
this plan's one retained-installer diagnostic. No deadline, protocol, API,
profile format or personal session was changed by this final inspection.

## SDK 0.1.49 published (2026-09-29)

The normal coordinator published all 12 Rust/base-mobile/optional-push archives
from GComs `2313cf6`, release4bb8ea74. Native matrices36507413858,36507413757
and36507577440 passed. Publication verified public archive bytes; independent
public manifest readback matches the publication receipt. Evidence:
`target/release-closeout-20260929/sdk49/review.json`.
This updates reusable integrations; it does not qualify the pending Mac apps,
physical mobile devices or live push delivery. Prior archives remain available.

## Mac closeout — retained throughput failure (2026-09-29)

Apple silicon run 36507549220 on GChat77223e52/GComs `2313cf6` passed
full native qualification and signing/notarization, then failed the unchanged
16 MiB / 180-second interrupted-file gate. It retained 262144 bytes across
restart, received two authenticated pre-recovery message ACKs and cleaned up
all children/profiles with unchanged inputs and binary. The last sample was
13369344 bytes (12.75 MiB), versus 9699328 bytes in the preceding candidate.
Source rediscovery improved from 57.448 to 15.626 seconds after reopen; this
measured improvement does not qualify publication or establish the remaining
throughput cause. No rollback/publication was dispatched for this failed run.

Immutable archive11010657350 SHA256
`6959afe259514f4d3db185597eada7f4716046b6d6831dbe61a9cb93feb94736`.
Full archive retained in release coordinator state; local review and report
hashes: `target/release-closeout-20260929/mac49-arm-review.json`.
Intel36507553193 remains independently running. Existing public downloads and
prepared iOS submission awaiting Apple encryption approval are preserved.
A further installed throughput diagnostic exceeds this closeout plan's single
diagnostic allowance and awaits user direction; no acceptance limit was changed.

## Release closeout — Windows tooling portability (2026-09-29)

Run 36507558001 failed before application compilation: host-dependent manifest
parsing, a path-separator assertion and a POSIX daemon test on Windows. Correct
the tooling and qualify on both native hosts; retain the original failed archive.
Focused Mac checks pass: 103 release tests (5 platform exclusions), 3 rollback
tests. Native Windows/Linux run 36510827112 passed on 19ee71f: 103 tests each
(11/4 platform exclusions), plus all 3 rollback checks on each host. No new
Windows application/installer qualification is claimed by these tooling checks.
Mac 36507549220/36507553193 remain frozen and running independently.

## GCHAT-STORE-2 — Apple listing creative (2026-09-29)

Codex: the matching iPhone/iPad pack is in `marketing/app-store/retro-v1/`:
four 1290 × 2796 iPhone images, four 2048 × 2732 iPad images, WebKit captures of
the shared UI with synthetic content, editable artboards and English metadata.
App Store Connect target is iOS 1.0, `en-US`; receipt: `publication.json` in the
pack. Apple asset processing, dimensions/order and metadata readback are checked.
The original images and listing are backed up in retained evidence. This changes
the draft listing only: its iOS build is absent and encryption is still in review.
The existing binary qualification and release workflow remains authoritative.

## GCHAT-STORE-1 — old-school Play Store creative (2026-09-29)

Codex: creative pack complete in `marketing/play-store/retro-v1/`: original
pixel artwork, feature graphic, four images of the shared UI with synthetic
conversations, editable artboards, preview gallery and proposed English listing
copy. Leads with the conversation experience instead of the live listing's two
setup screens. Render evidence: `marketing/play-store/retro-v1/validation.json`.
Google accepted the user-requested submission to the default `en-GB` listing on
2026-09-29: feature graphic, four screenshots and listing text. Image hashes/order
and provider validation passed; icon and tracks were unchanged. Shared UI source
matches published Android build 1055. Browser captures are not native device
screenshots. Public visibility remains pending; the immediate public check showed
the old listing. Receipt: `marketing/play-store/retro-v1/publication.json`.

## Production stabilization (2026-09-28)

R07: pause automatic discovery without cancelling frozen workers. Separate
reviewed controller/qualification changes from conservative artifact fingerprints;
unknown/build/runtime inputs still reserve new versions. Qualification-only
observations cannot advance publication. Use the explicitly approved, source and
binary-bound Windows 36 4 MiB recovery check with unchanged 180/600-second budgets.
Original 16 MiB failures remain failed. Implementation checks and actual native
acceptance have separate receipts under target/release-ready-20260927/stabilization-20260928.
This boundary does not qualify or publish Windows/iOS/Mac artifacts.

## Retained Windows 36 diagnosis (2026-09-28)

R07: native compilation, signatures and offline install/reopen passed, but the
interrupted transfer stopped at 6.5 MiB when the original 180-second budget expired.
Use the exact immutable installer with aggregate diagnostics and fresh disposable
profiles. Do not rebuild, extend deadlines or qualify the failed run.

## Retained iOS startup recovery (2026-09-28)

R07: support the specific post-native-test simulator launch timeout after verified
owned-device removal. Keep its failed cleanup record, require fresh native and
actual profile/reopen lifecycle passes, and verify the original IPA without
rebuilding or re-signing. Other startup failures remain refused.

## Platform acceptance isolation (2026-09-28)

R07: generated coordinator configurations now use a distinct installed-acceptance
directory for each platform in execution and reconciliation. This preserves the
live configuration correction across regeneration. SDK consumers keep their own
checks; completed receipts and active builds retain their original bindings.

## Mac installed-network automation (2026-09-28)

R06/R07/R12: both Mac release targets now require the explicit protected network
fixture after signed copy-install, offline service and GUI startup checks. Drive
the exact packaged executable through two-way recipient ACKs, a 16 MiB abrupt
receiver restart, retained pieces, exact export hash and orderly reopen. Keep
the 180-second file and 600-second journey budgets. Original frozen offline
receipts retain their scope; installed-network compatibility and rollback remain
separate publication requirements. No personal profile or runtime changes.

## Windows 29 retained recovery diagnosis (2026-09-28)

The signed Windows 29 installer passed native/offline installation and two-way
message ACKs, but its interrupted 16 MiB recovery exceeded the unchanged 180-second
budget. Preserve that failed receipt. Reuse its pinned immutable installer for a
single diagnostic journey with aggregate file counters and periodic byte progress;
no application rebuild, deadline extension, personal profile or publication claim.

## Native publication follow-up (2026-09-28)

Windows retained candidate18 failed its actual network journey when SDK named-pipe
admission terminated the service (1368). GComs 7be1757 fixes authentication after a
bounded preserved byte; native Windows checks and the original-source negative
control passed. Keep the failed application gate; a newly built Windows installer
must run the 16 MiB interrupted chat/file/reopen check using the protected fixture
invitation. Remove that invitation after success or failure.

Mac packaging recovery selected obsolete preview signing inputs while the main
release already used Developer ID. Align both preflight and packaging with the
pinned Developer ID certificate and supply updater signing keys to packaging.
Reuse Intel19's passing native receipts; its two original packaging failures stay
failed. This does not qualify MacARM's failed 24-node overlay.

## Retained Windows network gate (2026-09-28)

R06/R07/R12: run the already-signed Windows installer through the existing native
installation/signature/cleanup checks, followed by a portable service-IPC journey.
Use fresh fixture profiles and an explicit protected network invitation. Require
actual recipient ACKs, a 16 MiB abrupt receiver stop, retained verified pieces,
the original 180-second completion/600-second total budgets, and matching export
hashes after reopening. Keep original installer/native receipt bindings; do not
compile or sign another application just to run this gate. This is not GUI,
Windows 11, steady-state latency, rollback, or publication evidence by itself.

## Windows updater signature environment (2026-09-27)

Supply the protected Tauri updater key to the actual NSIS packaging step. The
previous workflow scoped it only to certificate preflight: Authenticode signing
completed but updater signing then refused the missing key. Preserve certificate
pinning, cleanup and required updater signatures; do not disable updater output.
Frozen prior runs remain bound to their original workflow.
[Scope and validation](docs/evidence/windows-updater-env-20260927/summary.json).

## Current-network download availability (2026-09-27)

R07: Google Play reports Android1028 available. Link that store record instead of
old standalone APKs. The archived Mac/Windows installers select profile22; hide
them from current downloads while profile46 replacements finish qualification.
Keep their immutable signed metadata and artifacts; no historical pass is erased.
Linux uses the qualified managed page. Store/native states remain independent.

## Current Linux website downloads (2026-09-27)

R07: point new Linux installs at the release coordinator’s qualified download page.
Publish immutable package/source/signature details and atomically advance the human
page only while its exact updater feed remains current. Existing archived release
metadata and independently qualified platform downloads remain retained. Tests cover
replayed releases, changed package/signature bytes and stale website links.

## CPU optimization delivery (2026-09-27)

Signed Linux 0.1.13 is published through the update/APT feeds and installed locally.
Four authenticated message acknowledgments, the 16 MiB interrupted/resumed/reopened
file hash and packaged upgrade/rollback checks passed against all eight upgraded
relays. The controlled benchmark measured 92.45% less idle presentation CPU; a
separate 30-second relay observation measured 0.33–0.90% of one core. Running
profiles were preserved; the old fleet host picks up the packaged executable at
its next start. [Exact scope and bindings](docs/evidence/idle-cpu-20260925/deployment-20260927.json).
Android 1028 is in review. Other platforms and large-file/privacy claims remain separate.

## Play release display name (2026-09-27)

R07: retain the full source identity in the submission journal, but use a bounded
version/hash display name within Play's 50-character limit. The original HTTP 400
validation is retained; retry reconciles the same edit and uploaded bundle.

## Linux publisher duplicate references (2026-09-27)

R07: the verified Linux receipt can name one file as both installer and updater.
Deduplicate identical paths after checking every evidence hash; reject distinct
Debian candidates and ambiguous signatures. Validate the complete selection before
changing either public feed. Five focused regressions pass; the original failed
production publication remains retained. Application binaries are unchanged.

## Windows update-owner fixture (2026-09-27)

The native Windows gate correctly rejected the update test's temporary directory:
it set Unix permissions only. Use the existing cross-platform private-directory
helper before opening the fixture. Runtime ownership checks and updater behavior
are unchanged. The focused cluster check passed (one test); formatting and source
audits passed. [Evidence](docs/evidence/windows-update-fixture-20260927/summary.json)
retains the native Windows failure. The corrected native Windows rerun remains open.

## Release blocker follow-up (2026-09-27)

Windows native CI exposed an open temporary archive handle in SDK publication.
Close and fsync the file before digest verification, atomic replacement and
cleanup; preserve immutable-version and incomplete-publication checks. Four
focused cases and the release-script suite pass (62 passed, four native-only
exclusions). Native Windows requalification remains required. Original failure:
run 36161747998. No runtime or installed profile change. The macOS release worker now gives
browser CDN setup a bounded 120-second socket timeout instead of 30 seconds;
application-test deadlines are unchanged.

## Idle presentation CPU (2026-09-25)

The service caches its UI projection across attachments and waits for archive or
local-state changes instead of rebuilding every 200 ms. Presence and operation
expiry still wake views at their deadlines. Locks discard cached private state;
notifications never imply delivery. File observation copies the encrypted UI
sidecar only when its retained file set actually changes. No routing, retry,
cover schedule or public API change.

The optimized, identical four-view/4,096-operation fixture measured 9.933%
of one core before and 0.750% after (three 60-second samples each, 92.45% lower;
all candidate samples below 1%). Full core validation passed 83 tests with three
explicit exclusions, plus strict all-target/all-feature core Clippy. The CPU
fixture is run separately from those ordinary exclusions. Debug measurements and
an invalid shared-cache comparison are retained separately. The original laptop
observation was 5.79% with authority retries and is not this quiescent benchmark
or a relay CPU measurement. The actual GChat 16 MiB abrupt-stop/resume/reopen
journey passed in 108.91 seconds including capture cleanup, retaining 1,835,008
verified bytes through restart, three authenticated chat ACKs, and the final
file hash after reopen. No residual fixture processes or host link changes.
The running personal app remains unchanged; signed publication/installed-network
acceptance stays with the normal release pipeline.
[Source-bound evidence](docs/evidence/idle-cpu-20260925/summary.json).

## Responsive carrier release binding (2026-09-25)

Release tooling accepts distinct profile-22 and profile-46 contracts and rejects
mismatched observed profiles. The three changed release tool/test files are
byte-identical to the paired GComs files tested by the 37 passing release-tool
checks. This is tooling validation; no existing native, installed, store or
privacy receipt is relabelled. Current GComs source sends real data immediately
with independent 10–10,000 ms randomized interactive cover. Older peer and policy
cache compatibility requires the staged rollout described in PRODUCTION_RELEASE.md.

## Retained data rollback compatibility, 2026-09-24

A disposable copy of the successful 1 GiB receiver profile reopened under
candidate14, the earlier candidate12, then candidate14 again. Each real GChat
core/service retained the same identity/channel and exported the exact file hash.
The source profile remained byte-identical; all three processes exited cleanly
and the disconnected namespace was empty. This selects a compatible runtime
predecessor, not a historical production binary. Signed installer upgrade/rollback
and pending-message compatibility still need their own qualification.
[Receipt](docs/evidence/retained-rollback-20260924/summary.json).

## Emulator and simulator lifecycle batch, 2026-09-24

Four concurrent disposable Android emulators passed profile creation, background/
foreground, relaunch and invitation file-picker selection/cancellation with the
retained signed Android1019 APK. Each owned emulator stopped and its AVD was
removed. The prior boot timeout was resolved by moving byte-verified SDK images
to node-local storage, without increasing the boot deadline. All 102 retained
evidence files rehashed; onboarding screenshots were visually checked.

The Mac iOS simulator separately passed the real application profile lifecycle
and three native Keychain/push-hint-validation tests on candidate11. These are
lifecycle baselines, not mobile network/file, latest-runtime or live-push passes.
Physical Android/iPhone checks are deferred by the user.
[Exact scope and source bindings](docs/evidence/emulator-lifecycle-20260924/summary.json).

## Current completion plan, 2026-09-24

Follow the [requirements-linked test matrix](docs/RELIABILITY_TEST_PLAN.md).
Cluster batched runtime/device validation precedes another release build; physical devices are deferred. Android
1019's completed workflow failed its installed-app smoke/cleanup step; compilation
and signing passed, but it is not a qualified release. Preserve its failed result.

## Android 1019 diagnostic candidate

Identify which protected-route stage fails during the reproduced Android resume
problem. Preserve the original completed file, profile, and pending phone message;
no resubmission or relay deployment. Pair the exact GComs diagnostic commit after
cluster routing/transport validation. This is not a claimed recovery repair.

## Android retained-role recovery, 2026-09-24

The original laptop unlocked successfully on Android 1017's paired protocol
revision. The phone subsequently captured a separate checkpoint failure:
`invalid owner alias binding or duplicate queue`. GComs live recovery appended
saved draining queues to an already populated owner record. Its regression fails
with that exact error, then passes when applying the complete record replaces the
nonactive collections. Android 1018 carries that repair after cluster validation.
Original identity and membership remain. Android 1018 resumed the original partial
to all 122,980,700 bytes; native Save export exactly matches the laptop source SHA-256.
The old laptop message is acknowledged; a fresh phone message reached the laptop.
After the Save picker background/reopen, cached completion persists but phone inbox
recovery stalls and its return ACK is still pending. This is not a full recovery pass.
[Physical-device receipt](docs/evidence/original-device-transfer-20260924/summary.json).
The paired Linux core passed 65 tests (two existing namespace exclusions), strict
workspace Clippy and both service/desktop release builds. The package is installed
without restarting the original laptop session. A separate retained test profile
reopened and recovered both inboxes without a checkpoint pause.
[Receipt](docs/evidence/owner-role-recovery-20260924/summary.json).
Android 1018 is installed with existing data preserved; no new store promotion is claimed.

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

## Bounded release qualification (2026-09-25)

Owner-approved: replace the release-blocking 1 GiB campaign with a 16 MiB interrupted-transfer/hash/reopen check, 180-second completion and 600-second overall ceiling. Preserve both failed large-file attempts; capacity qualification runs separately. Authentication, persistence, signatures and rollback remain required. Implementation and cluster validation are tracked in GChat `target/release-automation-20260925/`; no new installed or fleet qualification is inferred.

## Disclosed latency policy (2026-09-27)

Owner-approved: publish with slow joins/reconnects disclosed and optimize latency
next. R04's 30-second join and R03's 10-second reconnect targets are nonblocking;
authentication, delivery, persistence, signatures and rollback remain mandatory.
Publish the limitation on the downloads page. Existing frozen candidate checks
and recorded failures retain their exact source and outcome bindings.

IRC checkpoint update: the initial full workspace run passed 175 tests with three
explicit existing ignores (`hosted-client-07.log`), plus a separate four-test
runtime recovery rerun. The newer encrypted sidecar rollback test, two hosted
projection tests and strict workspace Clippy pass in paired GComs
`test-evidence/irc-parity/receipt-02.log`. That run also validates covered recipient
receipts and opt-in presence renewal in the paired runtime. Global network,
status/list, create/join and lifecycle commands remain available from hosted
windows. The full updated suite is being rerun; native/network claims remain open.

## IRC-4 modern file routing — 2026-09-29

The existing file controls and binary I/O now route explicit hosted/contact
conversations through GComs sharing_v2, retaining separate legacy scopes and
rejecting cross-profile handle collisions. Contact changes synchronize the
worker's authorization; failure leaves modern transfers disabled. This checkpoint
is under qualification and does not claim full file parity or deployment.
The preceding contacts checkpoint passed the full workspace suite in
`test-evidence/irc-parity/contacts-full-01.log` (paired GComs `4c651a1`/GChat `d6c0235`).

### IRC-4 file recovery follow-up — 2026-09-29

`files-routing-06.log` passes the real independent-contact file journey, three
quota/activity unit cases and strict workspace Clippy. Files share one admission
budget across both caches, emit scoped activity once and expose retryable provider
errors. File authorization now follows the conversation capability; the full
workspace run with no channel permission in the contact journey remains pending.
The underlying large contact restart failure is being diagnosed in GComs; no
claim of full file recovery, protected-network capacity or release qualification.

### IRC directory and contact-only permissions — 2026-09-29

GChat browses opt-in public hosted rooms through `/hosted list` (or `/list` in a
hosted room), with explicit `/publish` and withdrawal. Labels include the pinned
channel identity; encrypted topics are excluded. The paired IPC contract is 24.
Contact-only unlock now accepts DirectMessage authority without ChannelMember;
file and conversation operations retain their individual capability checks.
`files-contact-only-08.log` passes the real file/chat/persistence journey and
strict workspace Clippy; `directory-01.log` passes command/cursor checks and
strict Clippy. The full updated workspace run remains in progress.

### IRC-5 historical names — qualification in progress

Added channel-scoped `/whowas` with a bounded encrypted observation history and
corrected per-event name projection across recovered rename batches. A contact
window's `/list` again reaches the existing global list handler. All five focused hosted history/archive/command-scope cases pass in
`history-regression-03.log`; remaining integration capture and strict Clippy are
still running. Older archives seed names from retained authenticated messages.

### IRC-2 immediate hosted feedback — 2026-09-30

GChat now archives and projects a locally queued text/action/notice immediately
as LocalAccepted, preserving the operation identity before returning to the UI.
Later service events deduplicate the bubble and cannot imply recipient delivery.
Historical-name results show readable observation ages. `hosted-feedback-06.log`
passes all five hosted cases and strict workspace Clippy against GComs 255f9cd;
the first compile failure (05) remains retained. The preceding paired04 run
passes five hosted plus 60 TUI tests and strict Clippy; history03 retains 62
focused/integration passes, with its separate Clippy invocation setup failure.
Protected-network, installed/native and 500-member release gates remain open.

### IRC-8 protected-network journey — 2026-09-30

The paired release binaries (GComs `255f9cd`/GChat `1248dd9`) built successfully and
were hash-checked after transfer. The live two-client driver now runs on the
installed network against the HEL ciphertext service, with no messaging transport
overrides. Creator-offline join/topic, real receipts, moderation, restart and
16 MiB partial-file recovery are under qualification. Channel creation remains
operator-provisioned. No passing live or 500-member network result is claimed.

Live setup correction: run01 retained the expected invitation-required failure;
the driver now imports an operator-issued, bootstrap-only, time-limited network
invitation before starting hosted work. Run02 connected through the installed
network in 66.3 seconds, then exposed the paired runtime's missing hosted-origin
authorization. GComs `6b8764c` fixes that gate; the updated source-bound binaries are
being built before a fresh live attempt. These failed attempts remain retained.

### IRC shared contract and UI checkpoint — 2026-09-30

Current Rust types/RPC schema match the checked-in contracts. The paired source
RPC packages pass generated-binding checks, both Svelte workspaces report zero
errors/warnings, all 63 UI tests pass and the production bundle builds (existing
large-chunk warning retained). Evidence: docs/evidence/irc-ui-20260930/summary.json.
The missing unpublished-package offline-cache attempt remains recorded as setup
failure; only the scratch lock's package archive resolutions were replaced.

### IRC-8 live correctness checkpoint — 2026-09-30

The actual two-daemon GChat journey on the installed protected network passed
offline-owner admission, Topic pending, authorized handoff, messages/receipts,
moderation/voice/notices, offline recovery and verified 16 MiB partial restart
with an unvoiced completion receipt. Feedback was 119ms. Small-room delivery/ACK
was 9.165s and resumed verification about 299s: latency remains failed. Exact
artifacts, observations and retained report hash are in
docs/evidence/irc-hosted-live-20260930/summary.json. GComs is qualifying a combined
covered poll to reduce the measured sequential-request cost. No 500-member or
installed-release pass is implied. The harness now reports correctness and
latency separately, measures join/file budgets and rejects late positive probes.

### IRC-8 combined polling qualification — 2026-09-30

The paired workspace passes 185 tests (three explicit ignores) and strict
Clippy against GComs `8687749`; source-bound evidence is in
`docs/evidence/irc-covered-poll-paired-20260930/summary.json`. The next live
protected-network journey also passes correctness, including Topic pending and
verified 16 MiB restart. Feedback is 112ms, offline-owner admission 6.669s,
small-room receipt 6.146s, resumed verification 285.756s and file workflow
624.321s. Receipt and file latency targets remain failed. Retained run04 is not
superseded or relabeled. See `docs/evidence/irc-hosted-live-20260930/poll-05.json`.

### IRC-8 bounded replay paired regression — 2026-09-30

The GComs 3be4455 runtime passes the complete paired GChat regression and strict
workspace Clippy: 185 passes, three explicit ignores, no failures. Evidence is
`docs/evidence/irc-checkpoint-batch-paired-20260930/summary.json`. The release
executable built and its hash was verified before the new live06 journey. The
live journey and the separate 500-client capacity test are still running.

### IRC-8 live latency progress — 2026-09-30

Live06 on GComs 3be4455 again passes correctness. Small-room delivery plus its
recipient ACK is 3.429s and the full 16MiB workflow is 478.544s, within their
respective 5s and 600s targets. Resumed verification is 234.873s and still misses
180s. Earlier failed measurements are retained. This run sampled local IPC at
250ms; artifact hashes and exact observations are in
`docs/evidence/irc-hosted-live-20260930/batch-06.json`. Both daemons stopped and
the temporary bootstrap grant was revoked through the ordinary operator tool.
A bounded two-piece runtime window is now undergoing component qualification.

### IRC-8 file-window paired gate — 2026-09-30

GChat passes its full 185-test paired workspace and strict Clippy against GComs
907e54f (three explicit ignores). Source-bound evidence is
`docs/evidence/irc-blob-window-paired-20260930/summary.json`. The release client
built and was hash-verified before starting live07; the fixed file verification
and workflow deadlines remain under measurement. No installed release or
500-member protected-network pass is implied.

### IRC-8 live file-window qualification — 2026-09-30

Live07 passes the fixed two-client protected-network correctness and latency
gates on GComs `907e54f`/GChat `1775a40`: 110ms feedback, 2.409s delivery plus covered
ACK, 3.328s offline-owner admission after network readiness, 170.050s resumed
16MiB verification and 297.114s complete file workflow. Topic pending/handoff,
moderation, offline recovery and unvoiced authenticated file completion pass.
`docs/evidence/irc-hosted-live-20260930/window-07.json` binds the real binaries,
raw report and timings. The temporary bootstrap grant was revoked after shutdown.
Earlier failures remain retained. Full 500-member and installed/native release
qualification remain open. The paired package/API/frontend/Linux desktop compile
gate also passes on current GComs `65b54c7`/GChat `d4ff03d`; GComs retains its receipt.

### IRC-8 current trunk integration — 2026-09-30

Merge current trunk `8df1805` with the hosted/contact work, preserving explicit owner
membership recovery and its rollback-compatible journal projection. Shared UI
contracts are regenerated from Rust. Legacy owner recovery is shown only for
legacy channels; hosted channels retain their signed removal/rekey controls.
The paired GComs integration preserves released IPC22 recovery encodings and
requires IPC25 for new hosted/file operations. Merged Rust/UI/package validation
is in progress; previous evidence remains bound to its original source pair.

Merged qualification passes: 188 GChat Rust tests (three explicit
ignores), strict paired Clippy, all 63 UI tests, both workspace Svelte checks,
production build and six browser checks at 390/1100px. The released-recovery
SDK tests also pass. Evidence: `docs/evidence/irc-trunk-integration-20260930/summary.json`.
Current archive, full workspace and installed/capacity qualification remain
separate; setup failures are retained alongside their corrected runs.

The full merged browser suite now passes all 80 cases. Current package consumers
also pass on GComs `0e7db6a` and GChat `5533b1e`, including generated contracts,
frontend and Linux desktop compilation. The new live binary and the full merged
GComs workspace are under qualification; large-room and native installed release
claims remain open.

### IRC-8 current merged live journey and capacity harness — 2026-09-30

The actual GComs `0e7db6a`/GChat `5533b1e` binary passes live08 correctness and all
fixed latency targets: 118ms local feedback, 1.905s display plus covered receipt,
4.044s offline-owner join, 100.142s resumed 16MiB verification and 179.396s file
workflow. Topic pending/encrypted handoff, moderation, offline recovery, exact
hash export and unvoiced completion pass. Receipt:
`docs/evidence/irc-hosted-live-20260930/merged-08.json`. The temporary bootstrap grant
was revoked after the owned daemons stopped; all retained state is preserved.

A new protected-network capacity harness runs 12-member smoke or 500 independent
GChat profiles, ten senders, covered receipts, offline recovery, mixed file traffic
and kick/replacement confidentiality. Four harness/deadline checks and the source
audit pass. The actual smoke and campaign remain unqualified. Current full GComs
workspace validation and the separate durable-runtime 500-client campaigns remain
running; native installed release and normal trunk publication remain open.

### IRC-8 twelve-profile protected-network smoke — 2026-09-30

The GComs `0e7db6a`/GChat `5533b1e` smoke with harness `b36e077` finished with
correctness and cleanup passing, but latency failing. Twelve independent MLS
identities verified all baseline and mixed-file messages and 220 actual recipient
signatures across ten simultaneous senders per phase. Offline delivery, removal
confidentiality, replacement admission and a 16MiB interrupted file pass; resumed
verification took 142.586s and the full file workflow 308.480s. The returning
owner's eleven-admission catch-up took 14.537s after network readiness, exceeding
10s. Receipt: `docs/evidence/irc-hosted-capacity-20260930/smoke-12-01.json`.
All owned daemons stopped and the temporary bootstrap-only grant was revoked.
This remains a 12-profile smoke, not a 500-member pass. Paired GComs is validating
a bounded two-request deferred-replay window before a fresh application run.

The complete current GChat Rust workspace also passes on `40b440d` / `c5bbfe8`:
188 tests, three unchanged explicit exclusions and strict all-target/all-feature
Clippy. See `docs/evidence/irc-trunk-integration-20260930/replay-paired.json`.
The initial link attempt exhausted a 12GiB scratch PVC before tests; its failure
is retained. Expanding only the owned build scratch to 32GiB preserved the cache
and allowed the unchanged source/commands to pass. Runtime capacity limits were
not changed. The current archive-consumer gate remains active.
