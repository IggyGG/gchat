Linux releases compile each production binary once. GChat CI, GComs CI and the production relay/fixture build run concurrently. The relay campaign consumes those retained production relay bytes; packaging consumes the same relay bytes and the desktop/CLI already built by GChat CI. Signing verifies exact source, workflow, compiler, commands, dependencies and file hashes before bundling; DEB verification accounts for the pinned Tauri bundle marker and rejects all other binary changes. It does not rerun Cargo or the frontend build.

Compiler caches are written by the trusted `main` workflow and restored by release branches. They contain compiler/dependency bytes, never qualification or signing authority. Keys separate toolchains, runner images and build roles while allowing dependency reuse across application version changes. Every candidate still runs its required tests. This avoids the old cache isolation between successive release branches; see [GitHub's cache access rules](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching).

The isolated load gate still uses all 64 clients, a two-client preflight and one full 30-minute campaign. Independent profile preparation and client readiness run concurrently. Admission through the shared owner uses the original round-robin order across four channels, allowing each membership update to progress before the next request. Relay restart readiness has a bounded wait while delivery measurement continues. Thresholds remain <1% refusals and recipient p95 <5 seconds, with verified DS-sized file delivery and relay restart recovery. Native receipts authorize signing; the load receipt separately authorizes infrastructure activation. The mandatory campaign means a complete release cannot finish in a few minutes, even with warm caches. First-time compilation and runner queues add time.

The original 60-minute build deadline prevents new dispatches after expiry but permits collection and verification of the same provider request. Publication receives its own persistent 60-minute active budget once infrastructure is ready; infrastructure and external review waits pause that budget. Restarts do not reset either clock or create a second provider request.

An independently qualified controller repair can be bound to the currently selected release with `controller_qualification_release_id`. The next qualified release then installs its own bundled controller automatically; the temporary repair does not pin future controller versions.

Push source to Forgejo to start a release. The existing source mirror and Kubernetes coordinator handle qualification, rollout, publication and reconciliation. The local package timer installs signed desktop updates. Check the actual release with:

```sh
python3 scripts/release.py status
```

Release status, 2026-10-04: Linux 0.1.98 and all 17 infrastructure targets are active and healthy. Linux, Windows, both Mac architectures and SDK archives are published. Controller c66c230 runs the production-minutes-v1 publication path in Kubernetes. Original Android and iOS artifacts passed its publication gates. Android 1113 is uploaded, committed to Google Play and processing; iOS 1.1.13 awaits Apple encryption approval, including France. Full GUI qualification and SDK 1.0 remain separate and incomplete. Mobile publication and Apple encryption approval remain separate from full GUI qualification and SDK 1.0; original failed reports are retained.

Routine publication now verifies the native build, signatures, permissions, startup lifecycle and eight fresh matching relays. Full mobile GUI upgrade/rollback/history/file journeys run separately with `python3 scripts/release.py qualify --platform android` or `ios`; they do not gate routine upload and never become passes from a build or upload. Routine work has a persistent 60-minute active budget, one transient retry and one-minute source settlement; external review pauses its budget. Native dependencies and compiler outputs are cached, while signed artifacts and every source binding are verified.

## Routine release operation

The GitHub `release-signing` environment must permit `release/gchat-*` and
`release/qualification-*` branches. Qualification refs are immutable and bound to
the exact helper commit. Keep all other environment protection rules. A terminal
provider failure before report upload retains its run and empty artifact inventory,
cleans its authority, and permits one derived request from a different frozen
helper. A lost or still-running request is reconciled instead of resubmitted;
missing successful reports never become passes.

Use `python3 scripts/release.py status` for the selected release, actual deployment
versions and platform waiting/failure states. Native check details include each
job's current or failed step and original attempt. `resume --platform linux-x86_64`
authorizes one bounded retry of failed jobs in the existing source-bound workflow;
successful sibling jobs and their verified artifacts are retained. The worker
records intent before requesting the retry and reconciles an uncertain response
without submitting it again. A second failure stays blocked. Changed source
requires a new candidate. Original failures remain retained; neither the original
build budget nor the full load campaign is shortened or reset. `resume` also retries the selected
deployment. `rollback` queues restoration of recorded infrastructure versions.
These commands use the running coordinator and never create a second ledger writer.
Store publications cannot be rolled back by that command. Use `--json` for status
integration and `--state PATH` only when operating on a local controller state.

New source changes settle for one minute. Three artifact workers and up to six
installed-client acceptance workers can progress concurrently. While the active release is incomplete, older dispatched reconciliations use at
most one artifact worker and one acceptance worker, leaving capacity for active
work. They may finish their original requests; fresh acceptance authority and
corrected follow-ups wait for their own active flight. Infrastructure
activation stays serial in one owned worker, so a long canary does not delay the
coordinator's polling or status updates. Each step has a deadline and source-bound
receipt. Status exposes active stages, deadlines and controller observation age.
Rollback requests remain queued while a deployment owns its lock. Production defaults admit
one active release and expose one newest pending release. On production-minutes-v1, a terminal failed platform and SDK qualification do not hold admission of the next routine release; their failures and dispatched requests remain retained. Legacy policy retains its original flight admission. The active release is polled first; already dispatched provider requests retain their original
identity and keep being reconciled. Once all internal stages finish, mobile
processing/review may continue while the next release starts. A pending iOS encryption declaration may also release the global flight after the unchanged IPA and installed compatibility gates pass. It requires fresh IN_REVIEW evidence including France and matching native receipt hashes. The original iOS submit request continues reconciliation in its own lane; the wait never marks an upload, submission or availability as passed. This prerequisite handling is active in the qualified 2b2478e controller. The scheduler never
selects an older pending candidate after a newer one completes. Completed stages and
provider request IDs survive retries. A failed or unknown operation remains explicit.
The operator inventory can select `network_check_policy: boundaries-v1`: full
covered messaging/interrupted-file checks run at the first and final targets;
intermediate targets run covered bidirectional messaging within 300 seconds plus
their running-version/health checks. The original every-target policy remains the
default for existing inventories. A short check cannot qualify file recovery.

Store observation keeps one request ID until its source-bound result is
verified, including across controller restarts. Only then does the next poll
receive a new ID. Completed worker logs are closed even when a platform is
blocked; status lists live processes. This prevents descriptor exhaustion from
long-running store review and preserves unknown outcomes for reconciliation.

The controller target may retain a separately qualified operations image through
`controller_qualification` and its SHA-256 in the operator inventory. Its sealed
receipt must bind exact source, actual-image runtime tests, registry configuration
and Kubernetes validation with the previous image retained. This applies only to
the installed `ghost-com/gchat-release` controller; application services still use
the original paired-source bundle. Matching boundary images still receive their
full network check. Failure of such a check does not restart an unchanged target.
Each canary starts its two isolated clients concurrently under the same deadline
and waits for both owned startup workers before cleanup.

Canaries receive expiring bootstrap and invitation-publication scope, zero name
quota and no server authority. Legacy bootstrap-only grants remain revocable.
Catalog preparation with `canary_operator: true` installs the qualified companion
operator from the same infrastructure receipt and verifies an isolated grant and
revocation before updating its root-owned policy. Original operators and policy
backups remain retained.

The release publisher preserves original provider archives and source receipts.
Retained Mac packaging accepts an optional `gcoms_native_input` containing the
original successful provider run, artifact and SHA-256. It verifies every GComs
source byte and executable mode except individually reviewed status files, the
exact native workflow recipe, architecture and full compiler/Python/platform
environment. The original failed report remains unchanged and the original
positive GChat paired-source qualification is still required. The package uses
the frozen requested source pair and must pass actual signing, notarization and
installed DMG lifecycle checks. Retained packaging tooling changes require a new
controller qualification rather than another application release.
`release/automation/qualification/native-recoveries.json` registers an exact
candidate, target, original failed run/archive and separately frozen package
follow-up. A running or queued follow-up keeps the original build pending without
another dispatch. Successful results require independent validation of the whole
provider ZIP, original native evidence, source pair, helper archive and installed
smoke; signed updater and acceptance gates still follow. An operator may provide
the same registry through `GCHAT_NATIVE_RECOVERIES`. Missing registrations and
failed/cancelled follow-ups cannot become passes.
An `ios-retained` registration also binds the failed original IPA, its retained
simulator lifecycle run and the frozen verification helper. Collection waits for
the lifecycle provider's success, then records a durable request before dispatching
unchanged-IPA verification with upload disabled. Lost replies reconcile that same
request; duplicate providers or changed inputs fail. Signed-IPA verification still
requires the original failed verdict, immutable archive and native lifecycle
evidence. Native acceptance and store submission follow independently.

The production image registry is declared by `release/automation/registry.yaml`.
It uses a retained replicated volume and avoids node 5's recurring disk pressure.
For a storage move, provision the new claim and mount the old claim read-only in
an isolated copy worker. Stop the registry writer, run `copy-release-registry.py`
with `--writer-stopped`, and require its complete byte/mode receipt before a guarded
Deployment switch. Keep the original claim and Deployment specification for
rollback; restore that specification if activation fails. Apply the production
manifest for subsequent operations rather than the legacy development cache.
SDK qualification is cached per completed matrix. A hit requires identical Git
entries for every build, test, toolchain, feature, workflow and policy input; only
individually reviewed prose/status files are excluded. The controller rechecks the
original successful provider run and all expected archive hashes and sizes before
reuse. A desktop matrix can be reused while mobile qualification continues. The
public SDK index includes the requested source and original qualification source;
original archive names and embedded source labels are preserved. Partial or
cancelled provider runs remain failures and cannot become cached passes.
Every completed SDK publication also has an immutable index at
`/updates/sdk/<release-id>/index.json`. Resume verifies that index and its archive
bytes directly. Older retained candidates can complete while the newest version
stays advertised by `latest.json`; publishers serialize their updates and reject
same-version source collisions or changed immutable indexes. Reviewed inventory
and SDK orchestration edits require controller qualification without reserving
new application versions.
`release_compaction.py --state /state` verifies each completed build's original
archive before sharing identical extraction files. It preserves every path and
byte, checks ownership/mode compatibility and refuses changed files or links.
The same job verifies retained controller image receipts, immutable manifest
digests and every configuration/layer blob before sharing large identical layers.
It checks up to 32 images per run, supports directory and legacy OCI transports,
and retains every image path and rollback receipt. Other workloads keep their
own storage policy. Changed metadata, bytes, symlinks, nonregular files and
replacement races prevent a successful maintenance receipt. Existing hard links
remain safe to retry; no image is removed or relabelled as newly qualified.
Receipts under `maintenance/compaction/` retain the archive and build proof hashes.
An uncertain run can be retried; already shared files are unchanged. Compaction
never removes archives, profiles, unpublished work, signatures or evidence.
The independent hourly `release/automation/compaction.yaml` uses a qualified,
immutable controller image and the release PVC, without signing keys or network
access. Install that image only after its source and native compaction controls
pass. Its pod follows the live controller node so the shared ReadWriteOnce volume
can attach. Storage headroom still blocks new build stages when capacity is insufficient.
Already admitted workers can finish and record receipts below that threshold;
no new artifact is admitted by this exception.

Builds blocked solely by storage resume when the unchanged headroom threshold is
met. This also recognizes retained blocks from older controller versions. An
older candidate is superseded only if its build effect was never dispatched;
original request markers, receipts and provider identities are retained. Worker
logs include a random suffix, preserving separate reconciliations within one host
clock tick. Existing
builds and verifications keep their ownership. Recent candidates are polled first
so old diagnostics cannot delay starting otherwise eligible current work.

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
   macOS workers. Linux/Mac/Windows full Python gates install the pinned
   `numpy==2.3.5` and `cryptography==50.0.2` test dependencies; release tooling
   portability also pins cryptography. Mac/Windows build qualification runs the
   signed installed offline lifecycle without a shared production invitation.
   Their live network/file/rollback checks remain mandatory in acceptance after
   deployed infrastructure is ready and the worker receives fresh authority.
   iOS startup launches its owned simulator normally after explicit per-phase
   termination, retaining both 60-second launch bounds and liveness/cleanup checks.
   Physical mobile devices remain deferred. SDK qualification
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
   observations. Production rollout selects qualified Linux targets and advances
   the desired release only after its exact infrastructure receipt is ready. A newer
   mobile artifact cannot supersede that selection while Linux is queued. Active
   rollouts retain ownership; late older builds cannot downgrade the desired version.
   The controller never infers topology or discards retained state.
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
latest available normally retained provider with unchanged source-bound installed
acceptance evidence for that platform. A historical publication without that
receipt leaves the qualified seed in place. Changed or failed evidence remains an
error; an older publication is never relabelled as a successful native run.
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

Linux qualification, production/fixture compilation, load and packaging have
separate bounded native jobs. The two qualification jobs run the existing
repository CI entrypoints and retain logs, paired source/dependency evidence and
workflow/release bindings. The signing job requires both successful qualifications
and the production build, fetches their exact same-run artifacts by ID, checks
provider digests and every retained binding against its clean frozen pair, then
bundles the retained desktop/CLI and production service binaries. A failed-job
retry may reuse that run's earlier successful jobs. Qualification and failed
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

## Retained mobile launch checkpoints

Current release, 2026-10-04: all 17 infrastructure targets are healthy and match the release. Linux, Windows, both Mac architectures and SDK 0.1.98 are published. Linux 0.1.98 is installed and the running production-profile executable matches it. Android and iOS installed acceptance remain incomplete after retained failures. Apple encryption approval remains IN_REVIEW, including France. SDK 1.0 and the subsequent unattended release remain open.

Controller 7f423f8 is active, with temporary GitHub outage recovery and the original request IDs retained. Native helper d3a64e5 is qualified independently: 872 source controls, five existing skips, 68 focused mobile controls, and unchanged API 2/3 contracts. Native acceptance still has to pass against the original signed applications. Failed runs remain retained in the [launch evidence](evidence/stabilization-20261001/launch-simplification.json).

All eight node headroom timers are enabled. Every five minutes they check free space and prune unused Kubernetes images below 17%. If space is still insufficient and the local Docker daemon exists, they also prune dangling Docker images created more than one hour ago. Tagged Docker images, containers, volumes and builder caches remain retained. The service allows 270 seconds for the two bounded cleanup calls and records actual free space. Node 5 recovered from accumulated untagged build images; see the [live recovery](evidence/stabilization-20261001/node5-recovery-20261004.json). Original insufficient-prune results and reversible reserve adjustments remain in the [earlier maintenance evidence](evidence/stabilization-20261001/node-image-headroom.json). Docker image selection follows its [documented dangling-image and age filters](https://docs.docker.com/reference/cli/docker/image/prune/).

If a platform blocks, inspect its retained failure and queue its existing stage with `python3 scripts/release.py resume --platform <platform>`. The controller retains unknown external operations for reconciliation and never silently repeats them. `python3 scripts/release.py rollback` queues restoration of the recorded infrastructure versions.

OS invitation arrival on iOS remains a separate failed check. Its visible invitation form can qualify enrollment and recovery, but cannot qualify OS link arrival. The retained cold-start failure is consistent with the [upstream iOS scene URL issue](https://github.com/tauri-apps/tao/issues/1248); the warm failure remains independently unexplained.

Retained helper f30bac0 verifies iOS baseline installation under the existing setup budget, then fails because the system Paste menu is absent. Android passes the incoming rendered message and authenticated ACK and receives its exact outgoing message at the peer; its OCR recognizes a delivered line but cannot match the complete outgoing body. The worker now selects the existing Readable font through normal Android UI and uses normal iOS keyboard input in eight-character chunks, requiring every exact prefix before continuing. Normal password visibility controls permit exact confirmation; clipboard staging and the missing Paste menu are removed. All 62 focused controls pass. Native acceptance remains required, and the failed reports remain retained.

The latest iOS f696b22 run failed during initial installation before XCTest; its new identity observer was not exercised. The installer now issues one request and polls the actual container/executable hash inside the same deadline, avoiding overlapping installs when registration is delayed. Initial installation remains at most 240 seconds within setup 600; upgrade/rollback remain 120 seconds. Wrong binaries, ordinary command failures and exhausted deadlines still fail. All 65 focused mobile controls pass in 2.159 seconds; API contracts and application bytes are unchanged. Android is running its separately qualified ad8a119 helper (868 CI controls, five existing skips, 30.797 seconds). Installed mobile acceptance remains incomplete.

The retained Android cecddf7 run passes exact rendered messages, authenticated acknowledgments in both directions and exact export filename confirmation. It then fails because the system picker has no Show roots control. The helper now accepts the normal Downloads screen directly or opens it through Show roots, using only the two owned DocumentsUI packages and exact Save labels; export hashes remain mandatory. iOS d3a64e5 is independently qualified and running against the original signed apps. Remaining dynamic WebView row queries now bind accessibility elements rather than unstable indices. All 69 focused controls pass in 2.936 seconds; L0 checks 825 paths and API 2/3 contracts remain unchanged. Native results are still required.

Retained iOS d3a64e5 passes visible enrollment, exact identity, initial covered messages, system export, upgrade and baseline rollback with unchanged identity/history/encrypted cache and authenticated acknowledgments. Its final restoration cannot start within the original 600-second compatibility budget. Exact label ancestor queries now narrow file and message row candidates before the existing uniqueness/status checks, removing repeated whole-tree scans without extending any deadline. The failed report remains retained; complete installed qualification is still required.

Native follow-up, 2026-10-04: Android 80d68e5 passes exact rendering, authenticated messages and the normal OS export with the original hash. Its encrypted-cache check searched filesDir, but the pinned Tauri Android resolver uses activity.dataDir; the fixture now checks the owned app instance beneath dataDir and still requires one exact encrypted piece. iOS 96d51b6 passes setup but the first keyboard batch enters zero characters. Input now waits for the actual keyboard and permits one local retry only when the complete previous prefix remains unchanged; partial or different values fail. Original command and journey deadlines, failed reports and signed applications remain retained. All 70 focused controls pass in 3.052 seconds; complete native results remain required.

The active mobile helper da7073b passed 874 independent CI controls with five existing skips, plus 70 focused controls. It uses the corrected Android app-data cache path, normal system export and exact rendered acknowledgments; iOS narrows exact row queries and reconciles zero-character local input once within the original deadlines. Both actual native runs retain the original signed apps. Controller 7f423f8, all eight node headroom timers and both local release timers remain active. The running Linux executable still matches installed 0.1.98 byte for byte.

Native fixture simplification, 2026-10-04: retained Android da7073b passes initial enrollment/export and both upgrade and baseline rollback phases with unchanged identity/history/encrypted cache and authenticated acknowledgments, then exhausts the original compatibility deadline during final-restoration history observation. Fresh hierarchy removal, capture and read now share one ADB round trip. Each replacement checks authenticated messages before its OS export; an immediate next replacement performs only its required unlock, while subsequent messaging still reconnects normally. Android partial-transfer observation now requires an exact rendered filename, its adjacent transfer status, exact total and bounded verified counter. iOS empty-prefix handling accepts its actual accessibility placeholder without admitting existing input. All 71 focused controls pass in 2.956 seconds; native qualification is still required and all original deadlines and failed reports remain retained.


## Retaining an externally installed hotfix

If an operator has already repaired a failed managed rollout, keep that working
binary in place. `release.py handoff --release RELEASE --observed relay-1=SHA256
--reason "Retain the installed capacity repair"` queues a controller-only handoff;
repeat `--observed` for every affected target. The sole controller takes its normal
rollout lock, verifies the queued journal hash, observes the exact healthy running
artifacts and retains the original failed journal before releasing ownership.
Every pending rollback must be covered. It neither restarts services nor marks a
release qualified. The retired release cannot be resumed or rolled back; the next
qualified candidate must complete the normal deployment gates.

An operator-owned host policy may authorize that next release to retire explicitly
named, hash-bound temporary drop-ins. Preparation retains their bytes and modes
and the working previous artifact; activation removes only those overrides after
the new binary is verified. Rollback restores the retained overrides. Unrelated
operator changes remain a refusal. This one-time repair does not alter the usual
`push main` release process.

### Provider waits and controller maintenance

Local deployment supervision and provider polling have separate clocks: `poll_interval_seconds=10`, `github_poll_interval_seconds=120`, `store_poll_interval_seconds=900`. Quota cooldowns survive process restarts and apply across workers. `status` exposes the next provider check; `resume --platform android` reconciles the retained submission and does not create a new upload. Apple encryption review remains an external prerequisite.

Reviewed controller-only source changes produce a separately qualified controller image for the current application release. Native artifacts and their original source bindings remain immutable. An Intel-only successor may nominate `deployment_baseline` only when the controller validates its test-only/runtime-unchanged provenance; this creates a separate receipt and never rewrites the baseline deployment journal or failed native results.
