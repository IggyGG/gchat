## Stable contracts and released clients (2026-10-01)

Run `release_ios_versions_test.py` and `release_prepare_test.py`. Require patch
and minor carries, monotonic allocation above retained invalid reservations,
exhaustion refusal, invalid-number rejection before Git preparation or partial
ledger writes, and idempotent reservation after a lost source-ref publication.
Reproduce a historical invalid reservation for the same source pair and after a
documentation change. Require a distinct valid immutable ref, unchanged original
row/ref, idempotent lost publication recovery, and rejection of a corrupted original
manifest even when its iOS number overflows.
Use the signing worker's existing numeric constraints throughout. Retain the
original failed `1.0.100` worker and require a fresh native build with the automatically reserved valid `1.1.0`
reservation. Controller generation 50 passes 82 independent checks; these controls
do not qualify the signed application.

For retained iOS lifecycle qualification, use the exact labelled visibility
Switch exposed in the real XCTest hierarchy. Verify the exact plaintext input
through normal Show/Hide actions within ten seconds, restore secure entry, and
retain the original 45-second joint unlocked-state assertion. Rerun the same
unmodified application; fixture checks alone cannot qualify its lifecycle.

Run `scripts/check_contracts.py`, the `contracts_test.py` negative controls,
`scripts/check-generated.py` and `scripts/check-released-client.py`. The retained
consumer must use unchanged API 2 client/RPC source, attach to the current real
local endpoint, unlock, send the same operation twice, observe one message and
reopen the profile with identical instance and safety number. Wrong-instance
attachment must fail. Pair preparation binds this consumer graph and lock to
the same companion source used by the application.

Run the API compatibility tests: legacy decoders reject unprojected modern states;
the adapter never promotes service acceptance or failure to delivered, preserves
IDs/text/cursors, handles nested network history and rejects unsupported versions
before admission. UI tests cover identify-only version negotiation, pinned identity,
single mutation admission and optional-method capability selection.

## Deployment reconciliation and idle activation (2026-09-30)

Run `release_linux_qualification_test.py` for the separate Linux qualification
and packaging jobs. Reject missing/failed CI, boolean exit codes, changed source
or dependency inputs, altered/missing logs and locks, another run's artifact and
a digest different from the qualifying job output. A packaging-only retry may
reuse the earlier successful qualification attempt in the same run. Failed
attempts must keep separate archives, and no signing key is available to the
qualification job. Actual native execution remains required; original cancelled
Linux runs retain their original conclusions. Android failure artifacts must
retain `shell-errors.jsonl` without changing the installed smoke/retry policy.

Run `release_acceptance_test.py` for exact native source/archive/platform
bindings, baseline → current → baseline → current identity/history/cache preservation,
covered ACKs, unchanged 16 MiB/360-second/600-second bounds, cleanup, lost dispatch
replies and oversized invitation revocation. Only completed acceptance receipts
can refresh; unknown effects cannot create another worker. Retain the old receipt
and logs. Actual completion requires matching native workers executing retained
signed applications without rebuilding or touching personal profiles, followed by
fresh observations of all eight running relays. A desktop pass cannot qualify a
mobile platform. Component tests are not native acceptance evidence.
Reject identical baseline/current provider runs, archives, sources or installed
binaries. Cleanup failure must still stop other owned children and retain a failed
report. Attribute acceptance failures to their own recovery stage.

Run `python3 -m unittest discover -s scripts/tests -p 'mobile_acceptance_test.py'`.
Reject desktop/ordinary-picker receipts, changed ciphertext, re-signing, changed
post-journey binaries, another message's delivery marker and missing exact-pair
native peers. The actual XCTest loopback bridge must reject incorrect credentials.
It must also reject unknown or duplicate replies and expired command deadlines. Then execute
`mobile-acceptance.yml` on the native Android/iOS workers with retained signed
applications and distinct successful providers. Require baseline-created identity,
rendered history and encrypted cache across all three replacements, genuine picker
export hashes, covered ACKs, the original 16 MiB/360-second/600-second interrupted
network check and verified owned-device/process cleanup. Compile only the XCTest
runner. No application debug API, re-signing or personal-device state can qualify
this gate. Verify iOS passphrase entry through the normal Show/Hide control and
require the exact value in the original ten-second assertion, then hide it again.
The original masked-field failure remains failed; real native rerun is required.
Native UI execution is pending. Controller `5b89c81` passes 76 checks
in an independent Kubernetes Job and is active with both mobile recipes and
verified retained baselines. Retain its first registry-policy failure, corrected
retention/repair result, ready-image observation and independent watchdog success.
Also probe registry access using the real pinned watchdog image and labels: the
original policy must fail, and the scoped registry-pod TCP 5000 correction must
allow actual repair of the exact retained previous digest. Preserve both Jobs and
their logs. A successful routine no-op watchdog is insufficient for this check.
Run `release_config_test.py` to require a reconcilable acceptance recipe and its
freshness limit for every installed platform, with SDK qualification separate.
Run `release_inputs_test.py`: reviewed acceptance/status files change qualification
identity while preserving artifact identity. Reviewed GComs status documents
must also preserve infrastructure identity, so discovery can retain the original
artifact without reserving another app version. Require real-ledger baseline
rotation to the latest available predecessor before seed fallback; current/newer
candidates and identical source pairs cannot qualify. Missing historical archives
may fall back; corrupt source-bound receipts must fail. Unclassified mobile files, application
build scripts/workflows and unreviewed GComs evidence must still change artifacts.
Windows fixture cleanup must close SQLite and temporary upload handles before
removal. Linux grant-store ownership and Kubernetes rollout locks require their
POSIX host; portable invalid-authority guards still execute on every platform.
The first Windows Python failure and corrected native results remain separate.
Windows run `36824009006` passes GChat checks and fails the paired GComs stage;
Android run `36824016393` passes the ordinary profile/picker/no-listener lifecycle.
Neither satisfies the installed network acceptance gate. Controller `dfd65d4`
passes independent watchdog validation, digest-preserving retention and live
readiness with its scoped role; retain those results separately from app rollout.

Run `release_deployment_test.py`, `release_host_install_test.py`,
`release_kubernetes_worker_test.py` and `release_coordinator_test.py` through
unittest discovery. Cover interruption after activation, serial canaries,
rollback, unchanged identity/configuration, concurrent operator changes, missing
image availability, disabled workloads and stale deployment observations.
A lower ordinal rollback must use its recorded pod image, freeze automatic rolling,
replace only the failed pod, preserve higher ordinals and resume after a lost reply.
Restricted SSH uploads must reject changed/partial/oversized bytes and cannot select
unlisted units, executable names or protected paths. Controller-only source changes
must not reuse an infrastructure image from an older source pair.
`release_canary_grant_test.py` checks lost replies, fixed bootstrap authority,
expiry without renewal, idempotent revocation and grant-store permissions.
Registry tests require layer repair even when a manifest survives. Image builds
must derive configuration digests from retained archive bytes even when
Docker reports an image index ID. A different or ambiguous archive tag must fail.
Native OCI exports must preserve the exact archived configuration digest; reject
partial or duplicate OCI layout members. Classic Docker archives must produce a
readable OCI manifest. Rollback must retain and restore actual Docker and OCI
manifest media types without changing their running digest. Earlier OCI receipts
keep their original identity. Require real-image round-trip evidence in addition
to component controls before controller activation.
Linux packaging must reject a missing or changed CLI; the native worker runs both packaged binaries
through isolated unlock, wrong-passphrase refusal, disconnect and reopen.
The push image must use its own qualified configuration/repository; a service-image
configuration cannot authenticate it. `release_inventory_test.py` requires all 17
targets, descending anchor partitions, matching init/runtime containers and the
controller last; missing or duplicated host policies must fail closed.
The live canary producer must use the hash-bound provider archive and exact native
CLI receipt. Missing ACKs, smaller files, late or non-finite measurements, changed
inputs and incomplete cleanup cannot pass. Interrupted cleanup must be limited to
its recorded temporary root, with original logs and failures retained.
`release_rollout_watchdog_test.py` must restore a failed controller independently,
preserve the prior rollout intent across a lost reply, respect backoff and refuse
unrelated workloads or changed source bindings. `release_rollback_image_test.py`
requires pinned previous images, retains their manifest/layers before mutation and
repairs missing remote layers before rollback; changed retained bytes must fail.
UI `idle-updates.test.ts` must reject new activity while native status is pending,
wait for saved drafts/actions, and back off after native deferral. Run the UI type
checks/build and all unit tests. Rust `fleet_host` must reject invalid bootstrap
registration before profile startup; managed updates retain owner-lease and
checkpoint/exit checks. Live completion requires exact running identities for all
managed targets and a subsequent unattended update; component passes alone do not
qualify the deployment process.

`release_infrastructure_bundle_test.py` rejects changed source identities,
provider payload hashes, retained binaries and escaping artifact names before
promotion. Infrastructure must come from the hash-bound provider ZIP, never
self-authenticating extracted cache files. Rollout tests must retain and finish
pending rollback even when a new inventory removes its target. Idle activation
tests must acquire the input guard before native shutdown and release it on defer.

## Completed 64-member protected-network gate (2026-09-30)

The `a460d74`/`624e8b2` source pair passes the full `--members 64` campaign.
Both ten-sender phases require 630 real covered signatures, alongside ordinary
recovery, visible long-backlog recovery, exact 16 MiB resume/export, removal and
replacement. Churn admits 65 distinct identities over time, with the old member
removed before replacement; channel membership stays at 64. All deadlines,
resource capture, cleanup and temporary grant revocation pass. Retain the raw
logs/profiles and [source-bound receipt](docs/evidence/irc-hosted-capacity-20260930/capacity-64-01-pass.json).
Do not require a larger campaign or relabel older 500-member evidence.

## IRC/main invitation integration (2026-09-30)

Merged main's reusable invitation sharing, QR rendering and saved enrollment
progress with hosted channels and contacts. The 64-member maximum is unchanged.
Generated Rust/TypeScript/RPC artifacts include both features; merged UI checks,
unit tests and the client build pass. The companion GComs uses IPC26 to preserve
released IPC23 invitation messages before hosted/file requests. Paired Rust and
protected-network qualification remain pending for this merged source.

## IRC parity: retain the 64-member limit (2026-09-30)

The user confirmed **64 members**, including the owner, as the channel limit.
Hosted creation defaults to 64; `/mode +l` accepts 2–64 and GComs independently
enforces signed policy. Capacity qualification now uses 64 independent members,
ten senders and 630 actual recipient signatures per messaging phase. No larger
campaign is required. The former 500-member run was stopped, its grant revoked,
and its original evidence retained without relabelling it as a pass.

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
## Owner-controlled membership recovery

`cargo test -p gchat-core --features gc2-carrier --lib membership_recovery` covers strict preview parsing and the actual encrypted-profile stale-member → recovery → single-use invitation → authenticated message ACK → normal kick → reopen flow. Node tests separately assert exact retained wire/ACK equality, rollback and no future access for removed leaves. Browser `recovery.spec.ts` exercises phone/desktop selection, explicit confirmation/cancel, destination binding and absence of owner controls for members. No personal profile is used by these gates.

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

## Live hosted GChat journey

Run `python3 scripts/hosted-live.py --root NEW_PRIVATE_DIRECTORY --gchat
SOURCE_BOUND_GCHAT --probe SOURCE_BOUND_FLEET_PROBE --invitation-file PRIVATE_INVITATION`. The operator must add only
the emitted `channel.json` ID to the service creation allowlist and then create
`enabled` in the run directory. The harness stops owned daemons on exit and keeps
encrypted profiles/logs. Require offline-owner admission and Topic pending,
authenticated topic recovery, exact recipient receipts, unvoiced denial/voice
grant, offline archive recovery, 16 MiB verified partial resume and unvoiced file
completion. Record feedback and delivery timings separately; this two-client
journey cannot substitute for the 500-member protected-network gate.

The live harness reports `passed` for its bounded correctness journey separately
from `latency_passed`. Require explicit 30s admission, 200ms feedback, 5s small-room
message/ACK, 180s resumed verification and 600s file-workflow observations. Keep
large-channel covered-ACK timing separate. A predicate returning success after
its fixed wait deadline must still fail; run `hosted_live_test.py` for this guard.

Live hosted journey observations poll the local IPC snapshot every 250ms. This
reduces sampling uncertainty around the five-second small-room target; all
elapsed times and deadline checks still use the monotonic wall clock. Earlier
one-second-probe reports retain their original measurements and failed status.

Hosted live07 passes the unchanged 200ms feedback, 5s small-room receipt, 30s
join, 180s resumed verification and 600s file-workflow checks. Bind this result
to runtime `907e54f` and the recorded binary hashes; it covers two real clients,
not the separate 500-member or native installed campaigns.
Recovery compatibility: persisted operation results use the existing Text contract so older views and rollback daemons can read the archive; the requesting updated client receives the typed preview. Focused tests check snapshot/journal compatibility and unchanged error results.

After current-trunk integration, repeat actual membership recovery mint/join/
redeem/ACK/kick/reopen alongside hosted/contact regressions. Regenerate the
combined Rust UI/RPC contract, run both workspace Svelte checks and UI tests/build,
and retain the owner-confirmation browser tests for the merged members panel.

## Protected-network hosted capacity

`scripts/hosted-capacity.py --members 12|64 --root NEW_PRIVATE_DIRECTORY --gchat
EXACT_BINARY --probe EXACT_PROBE --invitation-file PRIVATE_INVITATION` runs actual
independent GChat daemon profiles through the installed protected network. Provision
only the emitted channel ID, then create `enabled`. Run the 12-member smoke before
the 64-member campaign; neither component tests nor a smoke pass can set
`qualified_64`. Retain all profiles, logs, source/binary hashes and ten-second
process RSS/I/O samples. The owner remains offline throughout admission. Require
independent verified rosters, ten simultaneous senders and all authenticated
recipient receipts, offline delivery recovery, real mixed chat/file traffic,
16 MiB pause/reopen/resume/export, removal confidentiality and replacement admission.
Keep 200ms feedback, 30s join and 10s recovery targets; covered large-room receipt
completion is measured separately with a 600s observation bound. Existing 180s
file-resume and 600s full-workflow targets remain unchanged. Cleanup and every
required observation must pass. `hosted_capacity_test.py` rejects missing evidence,
duplicate identities, failed timing/cleanup and promotion of a smoke to 64 members.

Capacity defaults to sequential cold bootstrap. `--startup-concurrency 4` starts
at most four independent profiles together, then submits their membership joins
sequentially. The report records that scheduling; profile/identity checks and
all deadlines are unchanged. Preserve results from the original sequential smoke.

Capacity qualification also requires process resource samples covering every
original profile and the full concurrent profile count. Retain per-process CPU
ticks, RSS and I/O with PIDs and clock frequency. A missing/failed sampler cannot
qualify 64 members. Compare timing targets before rounding display values; the
regression rejects a 200.4ms result against the 200ms feedback limit.

### Large membership backlogs and ordinary recovery

The user selected separate treatment for long membership replay on 2026-09-30.
Keep the 10-second ordinary offline-message gate in every campaign. Measure
membership replay separately in both small and large rooms: whenever it exceeds
10 seconds, require visible, positive applied-record progress. A small room can
also accumulate a long membership backlog. Retain the existing bounded
observation windows: 300 seconds for the smoke and 1,800 seconds for 64 members.
Reports explicitly identify this recovery policy; earlier reports cannot inherit it.
Do not convert earlier failed 10-second results into passes. Confirm that locked
views hide progress, cancellation/errors clear it, and an empty recovery page
clears it after a complete roster. Progress is not a delivery acknowledgment.

The hosted capacity journey rechecks the removed client after the replacement
roster converges: it must remain inactive with no channel/archive replay error.
A transient inactive view between kick and rekey cannot qualify churn recovery.

### IRC-8 hosted worker scheduling

Durable hosted admissions must wake the consumer without an idle timer tick.
Multiple queued admissions coalesce; reads and refused mutations must not cause
extra polling. Keep one-second idle polling, durable consumer commit before ACK,
covered receipt transport and the unchanged five-second small-room live target.

The two-client harness records cleanup independently of correctness and timing.
An exceptional journey must attempt every owned process; a stop failure remains
an explicit cleanup failure and nonzero exit, never a successful final receipt.
