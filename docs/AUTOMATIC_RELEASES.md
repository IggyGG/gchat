# Automatic releases

A release is one immutable GChat/GComs source pair. A successful build, a submitted
store review and an available download are recorded as different states. No
platform can inherit a pass from a different pair. Apple review does not block
Linux, Windows, macOS, Android or the SDK lane.

Discovery now fingerprints artifact inputs separately from qualification inputs.
An immutable candidate may explicitly select platforms. Only those targets queue
work; other platforms retain their earlier qualified artifacts. Coalescing also
works per selected platform, so a Mac-only candidate cannot discard queued work
for Android or interrupt an active Windows check. Version reservations remain
monotonic and original receipts retain their original source bindings.
An explicit reviewed list of controller and verification files may change without
reserving another application version; unknown files, package/signing scripts,
locks and build workflows remain artifact inputs. Such changes write
`qualification-needed.json` with `qualification_passed=false`, preserving the
original source pair. That observation does not qualify or publish an artifact.
The reviewed `marketing/play-store/retro-v1` and `marketing/app-store/retro-v1`
files are also classified individually as store-only inputs. Editing their copy,
artwork or publication receipts does not reserve another application version.
New unclassified files, packaged icons, version metadata and signing inputs still
invalidate artifacts. Existing running candidates and their receipts are retained.
After an input-classification update, the coordinator also checks previously
queued work against earlier active or qualified candidates for that platform.
Equivalent upstream application inputs and identical policy allow only an
undispatched duplicate to be superseded. Reserved external effects, active
workers, failed-only baselines and manually frozen sources are not discarded.
No version, source manifest or qualification receipt is reassigned.
Setting discovery to null pauses new source admission while existing workers,
receipts and publications continue. The closeout resumes discovery only after
the deployed classifier recognizes the reviewed controller-only changes; no
frozen worker is cancelled or restarted.

The registered iOS 1.0.59 recovery preserves its original failed workflow and
admits only the separately verified, unchanged IPA and original simulator binary.
Source, workflow, archive and publisher bindings must match the retained proof.
It does not rebuild or re-sign the app. Upload remains gated on France-inclusive
Apple encryption approval. An uncertain upload dispatch is reconciled rather
than automatically sent again. App Store availability still requires Apple's
actual published state; successful simulator tests or upload are insufficient.

The owner approved a Windows-only 4 MiB interrupted-transfer release check on
2026-09-28, retaining the 180/600-second deadlines and every integrity, admission,
reopen and cleanup assertion. The retained Windows 36 check accepts it only with
`release/automation/qualification/windows36-4mib.json`, bound to the original
source pair and executable hash. Its original 16 MiB failures and build manifest
remain unchanged. A new passing check still needs publication verification;
this policy record is not an acceptance receipt. Larger Windows transfers remain
separate and their speed limitation must be disclosed.

The owner accepted the measured transfer-speed limitation on 2026-09-29.
New 16 MiB qualification allows 360 seconds from the original accept through
interruption and completion, within the unchanged 600-second total journey.
Exact export hashes, retained pieces, authentication, ACKs, reopen, signatures
and rollback remain mandatory. Original failed receipts remain failures; this
change does not qualify an existing installer. The artifact-specific Windows 36
4 MiB authorization above retains its original 180-second limit.

## Production sequence

1. Land reviewed source in Forgejo `main` and retain the public GitHub mirror.
   The cluster controller watches their GitHub mirrors after the existing Forgejo
   source-mirroring bridge publishes them. `release_mirror.py` and its user timer
   run the existing source inventory and full-history secret audit before each
   non-force push. They perform no builds. The authoritative Forgejo is local
   to the workstation; it is not exposed to the cluster. It waits for source changes
   to settle, reserves monotonically increasing versions in SQLite, and creates
   immutable `release/gchat-*` refs. It never resets a working checkout.
2. Exact-source native workers run existing qualification, signing and installed
   lifecycle checks. Android uses emulators; Apple uses simulators and native
   macOS workers. Physical mobile devices remain deferred. SDK qualification
   runs the four desktop integrations and all client/relay/base/push mobile
   combinations. SDK archives are pinned releases, not hot updates to consumers.
3. Verify provider archive hashes, paired native provenance, publisher pins and
   the separately signed updater payload. Authentication, durable delivery,
   file integrity, recovery and state-compatible upgrades remain prerequisites.
   The file release check is a 16 MiB interrupted transfer: abrupt receiver stop,
   retained pieces and identity, authenticated chat ACK during resume, verified
   final SHA-256, then orderly reopen and re-export. Its file-completion budget
   is 360 seconds and the entire isolated journey is capped at 600 seconds.
   Use `gchat-turnover.py --mode file-recovery --release-check` with the frozen
   build and qualification host. A timeout remains a failure, never a pass.
4. `release_compatibility.py` consumes the fleet controller's recent, exact-pair
   application/rollback receipt and eight compatible relay observations from
   `/state/acceptance/<platform>/<release_id>.json`. Each installed platform has
   its own directory for both execution and reconciliation; a Linux receipt
   cannot unlock Android or iOS publication. SDK consumers retain their separate
   SDK checks. It **does not manufacture that receipt**
   from CI. Missing acceptance keeps publication waiting. Manifests requiring deployment also wait for the explicit operator inventory
   to pass serial native/Kubernetes rollout, canaries and fresh running-image
   observations. The controller never infers topology or discards retained state.
5. Desktop feeds and the GChat-only APT repository advance after verification.
   Public bytes are read back. Android commits one retained Play edit and polls
   the actual lifecycle API. iOS waits for the France-inclusive encryption
   declaration, uploads the already-built IPA on macOS, then attaches the exact
   processed build to a version and submits review. Store rejection or missing
   listing information remains an explicit blocked state.

The coordinator checks pending work every 30 seconds, after the previous tick
finishes. `poll_interval_seconds` may be set to an integer from 10 to 300 in its
configuration. This removes the former five-minute delay between completed
stages without overlapping workers or resubmitting an unknown external result.

Desktop acceptance uses `native-acceptance.yml` on the matching native runner.
The controller binds current and baseline provider runs, immutable archive hashes,
source pairs and the protected worker ref before dispatch. The worker downloads
and checks signed retained applications, performs current → baseline → current
profile/history/cache recovery, and runs the original bounded network journey.
New acceptance creates the profile and cached file with the baseline before
current → baseline → current replacement. All three replacements require retained
history, the same identity and cache hash, and fresh covered bidirectional ACKs.
An identical provider, source pair, archive or installed binary cannot stand in
for an upgrade or rollback. The initial native baseline bindings are installed
alongside the four desktop recipes in the live controller.
The controller refreshes eight native relay observations before publishing the
platform-specific receipt. No application is compiled in acceptance. This does
not qualify rendered GUI interaction or personal installations.

`acceptance.json` references the restricted grant and deployment policies and
optionally pins initial native `baselines` by platform. Later runs can select the
latest available normally retained provider for that platform. A failed historical
provider or missing baseline cannot be relabelled as a successful native run.
Only a short-lived repository secret carries bootstrap canary authority; deployment
and signing credentials stay in the coordinator. Grant revocation and owned secret
removal precede collection of completed evidence. Lost dispatch replies reconcile
the same request. Completed receipts refresh after their freshness window without
removing earlier evidence; unresolved attempts never expire into duplicate work.
Mobile acceptance uses `mobile-acceptance.yml` with its own retained provider
bindings and an exact-pair qualified Linux/Apple Silicon peer. It creates a fresh
owned AVD/Simulator, installs the unchanged signed apps and drives their ordinary
UI, deep links and system file picker. Baseline-created identity, rendered history
and encrypted cache must survive current → baseline → current replacement with
fresh covered ACKs at every phase. The independent network journey retains the
same 16 MiB interrupted-transfer, 360-second file and 600-second overall bounds.
iOS compiles only its XCTest runner. No signing keys reach acceptance; no app is
rebuilt or re-signed. Component validation, actual native execution and live
producer activation are separate states, tracked in PLAN.md. A normal mobile
profile/picker smoke pass cannot satisfy this installed-network gate.

There is no 24-hour campaign, physical-device requirement or statistical privacy
release gate. This does not claim traffic-analysis privacy qualification. The
remaining privacy work remains described in `PRODUCTION_RELEASE.md`.

The owner removed the 1 GiB interrupted-transfer release gate on 2026-09-25.
That test and the historical ~123 MB device transfer run separately; their
results cannot substitute for the mandatory bounded check. Retain their exact
source bindings and disclose timeouts or missing qualification. The two retained
1 GiB runs exceeded the original 1200-second completion deadline, including the
node-local-storage retry; neither is a pass. Do not alter an active run's budget.

For candidates with `policy.file_qualification`, the exact-pair acceptance JSON
also contains `file_check`: `mode`, integer `bytes`, measured
`completion_elapsed_seconds` and `total_elapsed_seconds`, matching
`source_sha256`/`export_sha256`, and true `abrupt_stop`, `verified_pieces_retained`,
`same_identity`, `authenticated_chat_ack`, `hash_verified_after_reopen` and
`cleanup_complete`. Bind the underlying logs/reports through `evidence`. This
supplements all existing required checks and relay/rollback observations; it
cannot turn the isolated fixture into installed-network acceptance. Previously
frozen manifests and their receipts keep their original policy.

## Desktop behavior

`/update` shows the running build, download progress and restart state. Downloaded
payload and metadata signatures bind version, source pair, platform, size and
hash. A signed older payload cannot be relabeled as a new version. Downloads are
bounded to 512 MiB. An unavailable update server leaves the installed app usable.

An update already staged at launch may activate before the window becomes
interactive. The startup check has a bounded wait. Updates discovered while a
window is open activate after 30 seconds without input, once drafts and
foreground actions have cleared. Drafts in other conversations count too. A
modal input guard prevents new drafts during the awaited native shutdown;
failed preparation releases the guard and retries after a bounded delay.
Other profile windows, active RPC admissions, checkpoint failures and an
unconfirmed service exit defer activation. Preparation uses the existing
owner-authenticated local IPC. It checkpoints before stopping, then verifies OS
process termination; a missing socket is insufficient. No passphrase enters the
updater. The saved profile remains and may need unlocking after a restart.

Debian installations are upgraded by a GChat-only systemd APT timer, without
restarting running clients. `scripts/install-local-updates.py` first verifies the
public signed repository, then installs the source, pinned key and timer when
run as root with `--apply`. A first deployment may initialize a signed empty
repository with `release/automation/initialize-apt`; this enables polling without
advertising an unqualified app. AppImage/macOS/Windows use signed Tauri updates.
Mobile stores own mobile installation and their automatic-update preferences.

## Controller deployment and secrets

`release/automation/Dockerfile`, `kubernetes.yaml`, `nginx.conf` and
`scripts/release_config.py` describe the controller and public download service.
The controller has one replica, a persistent SQLite WAL and immutable job inputs.
Only `/state/public` is served. Provider responses and credentials remain private.
Mount the existing publisher keys at `/keys`; never commit them. GitHub credentials are supplied through the protected environment. The
controller does not need workstation access or a Forgejo credential. Updater keys
are shared only with signing workers and the metadata signer. Signing workers
must use the configured release environment and protected candidate refs.

The image needs Python dependencies, GitHub CLI, GnuPG, minisign, Java/apksigner
and the pinned Tauri CLI. The cluster has a minimum-free-space admission check;
export retained artifacts before removing old data. Do not remove active job
state, provider journals or the release database. Back up SQLite using its backup
API (or a consistent stopped-volume snapshot), including source manifests and
provider journals. The daily maintenance task verifies and refreshes the signed APT index when
fewer than seven of its fourteen valid days remain, even without a new release.
It retains seven consistent daily SQLite backups; cluster volume backups must
also retain the immutable job evidence and provider journals.

After an interrupted external action, the request ID is reconciled with the
provider. Unknown uploads/commits are never blindly repeated. Transient timeouts use bounded backoff when automatic recovery is enabled.
The original effect always reconciles before another action. Deterministic
failures resume only after a corrected worker/controller revision, or explicit
`release_coordinator.py --resume RELEASE TARGET`; neither path skips verification. New source changes supersede only unstarted work.
Only one candidate per platform is newly dispatched while an earlier candidate
is building or verifying. New commits remain queued and coalesce to the latest
candidate; already-dispatched workers keep running on their frozen inputs.
Other platforms continue independently. Waiting for compatibility or store
review does not prevent preparing the next candidate.

The public status document distinguishes building, verification, publication,
processing, review, blocked and available.

Linux qualification and packaging have separate 120-minute native jobs. The
first runs both unchanged repository CI entrypoints and retains their logs,
paired source/dependency evidence and workflow/release bindings. The signing job
requires that successful job, fetches its exact same-run artifact by ID, checks
the provider digest and every retained binding against its clean frozen pair,
then prepares and rechecks the installer's dependency inputs. A packaging retry
may reuse that run's earlier successful qualification. Qualification and failed
build archives include their attempt number; successful packages keep the
`linux-x86_64` provider name. Neither failed CI nor another run's artifact can
authorize signing. Application recovery deadlines and acceptance gates remain
unchanged. The original timed-out jobs remain failed/cancelled evidence.

Initial deployment is not complete merely because these files or tests exist.
Retain a concrete deployment receipt, a first qualified release, a real installed
upgrade/reopen result and provider observations before claiming it operational.

Provider references: [Google release lifecycle API](https://developers.google.com/android-publisher/api-ref/rest/v3/applications.tracks.releases),
[Apple version metadata](https://developer.apple.com/help/app-store-connect/update-your-app/create-a-new-version),
[Apple encryption states](https://developer.apple.com/documentation/appstoreconnectapi/appencryptiondeclarationstate).

Retained worker recovery is explicit, not a generic success override. The reviewed
Windows 36 registry in `scripts/release_recovery.py` binds the failed original
run/archive to the exact successful 4 MiB follow-up run/archive and qualification
source commit. Collection preserves both; verification rechecks every extracted
member, original native/signing evidence, the installed executable, trust-store
cleanup and new network journey. It does not edit the original failed report or
invent its missing final worker attestation. Compatibility and upgrade/rollback
remain separate mandatory gates before publication. An unrelated candidate,
platform, changed artifact or failed follow-up has no recovery entry.

## Deployment worker contract (implementation in progress)

`deployment_file` selects an operator-owned inventory; each target provides argv
recipes for observe, prepare, activate, rollback and check. Receipts bind the
release, exact sources, target, stage, observation time and hashed evidence.
Only one rollout owns shared infrastructure. A lost activation reply is observed
before retrying. The first pending target is checked before another is changed;
an already unhealthy target is repaired first, and two unavailable targets defer
mutation. A failed canary restores the retained artifact and blocks the candidate.
Kubernetes targets retain PVC definitions and verify relay key hashes; image pull
checks happen before replacing a replica. StatefulSet ordinals roll from highest
to lowest through partitions. Deliberately disabled test workloads stay outside
the inventory. `public/deployment.json` reports actual observations separately
from package publication.

The Linux native worker retains `infrastructure/` in its verified provider
archive. `release_infrastructure_bundle.py` validates the original build and
verification receipts, retains native binaries and OCI blobs, and pushes images
by immutable digest. The OCI archive provides recovery if registry storage is
lost. The Docker archive, source-build report and qualification links are retained
alongside every deployed and rollback version. Production wiring and a complete
automatic release are still pending; these interfaces alone are not operational
deployment evidence.
