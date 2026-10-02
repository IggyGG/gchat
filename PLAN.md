## Live controller and native acceptance (2026-10-02, in progress)

The numeric iOS allocator is active in controller generation 49 (`e0e7fb9`),
with 81 independent checks, both containers ready and the previous image retained.
Live discovery exposed an older `1.0.103` reservation for the same source pair;
replaying it prevented a valid replacement. Discovery now checks the original
manifest digest and other fields, preserves that invalid row and ref, and reserves
a new valid version on a distinct immutable ref. Lost publication retries reuse
that new reservation. The real Git/ledger regressions and 637 Python checks pass
with five existing skips. The retry fix is active in generation 50 (`defc0e1`), with 82 independent
checks, both containers ready, retained/repaired rollback and a successful minute
watchdog. It automatically reserved build `1.1.0`; that native run passed numeric
validation and later failed its unchanged 60-second simulator launch limit. Its
verified archive and successful owned-device cleanup are retained. The next
automatic reservation, `1.1.2`, includes the latest SDK fixes and is building. The original `1.0.100` worker failure and later invalid rows are
retained in the [allocation checkpoint](docs/evidence/stabilization-20261001/ios-build-allocation.json).

Retained acceptance now binds the signed application and its qualification worker
independently. The worker uses a full commit and a checked immutable reference;
its report must match that commit's actual tree and the application's original
source manifest. A corrected worker may follow only a completed failed attempt
with its archive, run and revoked grant retained. An unknown dispatch keeps its
original request and worker across controller updates. Acceptance workflow edits
require fresh infrastructure qualification. Image validation exposed three legacy
fixtures that implicitly depended on an unset controller revision. Those cases now
select legacy behavior explicitly; a new control checks the production default
and rejects moving refs. The original failed image Job is retained, the previous
controller remains active, and fresh activation and installed execution are required.

Retained iOS lifecycle rerun `37017329318` passes using the exact native visibility
Switch. The entire provider archive is verified; app `1.0.87` keeps the same binary
hash, is neither rebuilt nor re-signed, and uses no Keychain signing fixture. Normal
Show/Hide, exact input, background/manual unlock, remembered reopen, original timing
and cleanup checks pass. Original run `36862393296` remains failed. This verifies
retained profile lifecycle; network messaging, upgrades, push and physical devices
still need their own acceptance. See the
[control checkpoint](docs/evidence/stabilization-20261001/ios-passphrase-control.json).

Status updates to reviewed iOS/SDK receipts no longer reserve application versions
or infrastructure images. Exact file names are classified; unknown evidence, Rust,
locks and packaging changes still invalidate artifacts. The real Git classification
controls and 637 Python tests pass with five existing skips. The refinement is
active in controller generation 51 (`421be37`): 82 independent checks pass, both
containers are ready with no restarts, the previous image is retained and repaired,
and the independent minute watchdog succeeds. Client and fleet activation remain
subject to the native and installed acceptance gates.

Android and iOS now have retained-app acceptance producers and a separate native
workflow. They install distinct signed releases on a fresh owned AVD/Simulator,
create state with the baseline, then upgrade, roll back and restore through normal
UI. Every phase checks rendered history, the same identity, unchanged encrypted
cache, a real system-picker export and fresh covered bidirectional acknowledgments.
The current app then performs the unchanged 16 MiB interrupted-transfer check
within 360 seconds and a 600-second network journey. Android uses accessibility;
iOS compiles only its XCTest runner, never the retained application. No personal
profiles or physical devices are used. Dispatch waits for an exact-pair qualified
native desktop peer before issuing its private expiring bootstrap grant. Mobile
workers use the existing lost-reply, revocation and eight-relay observation gates.
The iOS UI runner now verifies the exact entered passphrase through the existing
Show/Hide control within the original ten-second value assertion. This avoids
relying on the masked secure-field value, which failed the retained lifecycle
run; original assertions and failed verdicts remain, and retained native rerun
`37017329318` passes.
Full Python validation passes 632 checks with five existing skips in a short SSD
temporary directory. Earlier long-path harness failures are retained separately.
Generated controller configurations require the acceptance stage for every
installed platform, including both mobile stores; the SDK keeps its separate gate.
Component tests pass nine controls, including a real loopback XCTest bridge and
unrelated-delivery-marker rejection. Full Python validation and actual native UI
execution remain separately recorded in the
[mobile checkpoint](docs/evidence/stabilization-20261001/mobile-acceptance.json).
Controller `5b89c81` is now active with two ready containers and no restarts. Its
76 deployment/acceptance checks pass in an independent Kubernetes Job, the prior
image is retained and registry repair passes, and the independent minute watchdog
continues succeeding. The first validation attempt's registry-policy failure is
retained separately from the scoped correction. Signed Android/iOS baselines were
verified from retained provider archives and bound with both mobile acceptance
recipes. This activates the producers; actual native UI, fleet/client rollout and
the subsequent unattended release remain required. SDK source `7c4af27` passes
native Linux and Windows recovery; fresh native qualification remains open. The
owner approved 20% size growth for this feature release and automatic restoration
of the 5% regression cap at SDK 1.0; original failed workflows remain failures.
The source mirror retained a secret-audit false positive in a plain test instruction.
The wording is corrected and only that exact historical finding is allowlisted;
the full reachable-history audit remains mandatory.
The exact reviewed acceptance drivers and GComs status/reopen-validation documents
now change qualification identity without reserving another application version.
The same reviewed GComs status documents now preserve infrastructure identity as
well as application artifact identity; the former infrastructure hash caused
status-only updates to reserve needless builds. Acceptance now selects the most
recent available predecessor automatically and uses initial seeds only as fallback.
It excludes the current/newer candidates and identical source pairs; missing
historical provider archives are skipped, while corrupt receipts still fail.
The real-ledger rotation and fingerprint controls pass, with 633 full Python
checks and five existing skips. These controller fixes are active in generation 48; its previous image was retained and repaired before activation.
Unknown files, Android/iOS build scripts and application workflows still invalidate
artifacts; the original qualified source pair is never rewritten.

The actual pinned watchdog failed a registry connection under its original network
policy. The scoped correction now permits only registry pods on TCP 5000 in the
same namespace. The same pinned recovery image then repaired the exact retained
previous controller digest in a separate successful Kubernetes Job. Both results
are retained; routine no-op watchdog success alone cannot prove registry recovery.

Linux runs `36813732641` and `36823321752` passed qualification, then reached
the 120-minute job limit during signed bundle building. Qualification and
packaging now use separate native jobs with the original job limits. Packaging
requires both successful repository CI gates from the same workflow run, the
qualifying job's exact artifact ID/digest, clean matching source objects and
unchanged retained dependency inputs before signing access. Attempt-specific
qualification/failure artifacts preserve earlier failures. Native run `36844555101`
now passes both qualification and signed packaging; its original immutable pair
remains separate from the newer release candidates. Android release artifacts now retain the existing
shell-error log so a keyboard/ADB failure can be diagnosed from its original
stderr; the smoke assertions and retry policy are unchanged. Validation passes
623 Python tests with the five existing skips, including eight handoff controls;
the source inventory and whitespace gate pass.

The next upgrade's real-image check exposed two archive interoperability issues.
Containerd Docker exports preserve their configuration bytes through the native
OCI archive reader; the Docker compatibility reader reserializes those bytes.
Classic Docker archives explicitly convert their manifest for an OCI layout while
still requiring the qualified configuration hash. Rollback retention now uses
directory transport, which retains Docker and OCI manifests verbatim; earlier
valid OCI receipts keep their transport. The running controller's exact Docker
manifest and layers have been retained and registry repair passes without changing
its digest. The first configuration/retention failures remain recorded.

The source-bound `dfd65d4` controller is now active on Kubernetes with both
containers ready, scoped workload permissions and an independent successful
minute watchdog. The complete inventory has 17 serial targets; all eight native
relays pass restricted observations. The previous controller image and layers
are retained and registry repair passes. This is controller activation, not a
claim that the new clients or relay binaries have completed rollout.

Desktop acceptance automation now dispatches matching Linux, Windows and both
Mac workers with an expiring bootstrap-only grant. It downloads retained signed
current/baseline artifacts without rebuilding, checks actual identity/history/
encrypted-cache recovery through current → baseline → current, runs the original
16 MiB interrupted journey, and observes all eight relays before writing a
platform-specific compatibility receipt. The initial native baselines and all four
desktop acceptance recipes are active in the controller. New acceptance starts
with the older release, then upgrades, rolls back and restores the current release;
each phase must preserve identity, history, cache and authenticated delivery.
Identical releases or installed binaries cannot qualify an upgrade. Lost dispatch replies are reconciled;
only completed receipts expire into new work and earlier evidence is retained.
Oversized invitations revoke their grant before any worker is dispatched.
Validation passes 615 Python tests with five retained skips. Paired GChat Rust
tests and strict Clippy pass against GComs `500b305`; no wire version changes.

The old 18 owned 500-member test rooms were archived as 46 unchanged signed
files. Their private hash manifest is retained; the active 64-member room and
unrelated rooms remain intact, and the hosted service is healthy. Local launch
and service configuration now prefer the managed package while retaining the
qualified fallback; initial activation of the new binary remains separately
recorded. See [operational checkpoint](docs/evidence/stabilization-20261001/live-controller-and-acceptance.json).

Native SDK run `36814943114` failed the unchanged contact file reopen check on
all four platforms. The first scheduling fix passes Linux's native runtime check,
but corrected run `36820878112` still fails Windows recovery; its original logs
are retained and further investigation is required. Native Windows GChat run
`36820159187` also exposed fixture cleanup before SQLite/file handles closed and
Linux-only controller tests running on Windows. Cleanup now closes handles first;
portable authority guards still run everywhere, while POSIX ownership/locking tests
run on their actual controller platform. Actual desktop and mobile acceptance,
qualified fleet/client rollout, a subsequent unattended release and SDK 1.0
declaration remain required. Component checks do not satisfy those gates.

The corrected Windows run `36824009006` passes GChat's native checks, including
the portable fixtures; its paired GComs stage still fails. Android's ordinary
profile/picker/no-listener run `36824016393` passes and does not qualify network
acceptance. SDK run `36827922107` against the four-record legacy window fails
contact recovery on all four native platforms. The independent controller
validation Job succeeds, its prior digest remains retained, and the live minute
watchdog continues to succeed. Client/fleet activation remains gated.

## Stable contracts and released clients (2026-10-01, in progress)

Keep API 3 and typed service 1 stable while compatible features continue. API 2
remains supported for the full stable major through a server adapter. Legacy
history maps service acceptance to local acceptance and failed status to unknown;
neither becomes a recipient delivery receipt. Detailed history/search/network
methods are optional and advertised in instance capabilities. Version negotiation
only repeats the read-only identify request and retains the instance binding.

Retained source fixtures and the service contract reject removal, changed method
lifecycle, changed requests and incompatible output variants. Native CI compiles
the unchanged released client against the current local server and checks reopen
and message deduplication. Pair preparation also freezes that consumer's graph
and lock. The fast retained-contract workflow runs on pushes and pull requests.
UI checks pass with 70 tests; Python passes 583 tests with five retained skips.
The compiled released client passes its actual-server identity/deduplication/reopen
journey. Full GChat Rust checks pass 201 tests with three retained ignores and
strict workspace Clippy; generated artifacts agree. Live deployment, complete
platform qualification and the SDK 1.0 declaration remain open.

The deployment follow-up retains the controller image with the service binaries,
binds both to the complete source pair, and keys the infrastructure bundle by
release ID. The controller includes a checksum-pinned Kubernetes client. Native
workers use a restricted SSH command with root-owned unit/path policy. Stateful
rollback records each ordinal's actual image and replaces only the failed pod;
registry repair re-publishes retained OCI images before fresh bounded pull jobs.
These changes pass their component regressions; production wiring remains open.
The next operational checkpoint adds scoped Kubernetes roles, coordinator-only
credentials, a separate cold-pull namespace and missing-layer registry repair.
The Linux package includes a source-bound CLI and requires its lifecycle receipt.
Root-owned canary grants are bootstrap-only, expire within one hour, reconcile a
lost reply and retain revocation. Native package execution and activation of this
controller still require their own evidence; configuration files alone are not a
deployment pass.
The installed-network canary producer now uses the qualified Linux provider
archive and retains real covered delivery/file/reopen evidence. Interrupted grants
and disposable processes are reconciled before a retry. The operator inventory
and production bootstrap activation remain the next step; platform-specific
upgrade/rollback acceptance remains separate.
Component validation now passes 599 Python tests with five retained skips. All
eight native hosts accept restricted observations; a live bootstrap-only grant
reconciles a repeated request and is revoked. Independent controller recovery and
retained prior-image layer repair pass their failure/interruption controls.
Activation of the production controller and inventory remains open.
The live bridge caught two secret-audit false positives: a public Cargo checksum
and the existing public GPG fingerprint. Only those exact historical findings are
allowlisted. Archive-derived image configuration hashes fix Docker's index-ID
behavior without weakening the source/configuration verification gate.
The production inventory renderer now covers 17 serial targets with the controller
last. The push gateway has its own source-bound retained archive/configuration and
its init/runtime containers advance together. The catalog image keeps the installed
executable name. A live copy retained and restored the previous controller digest
through the registry's digest-addressed destination. Recovery jobs share the
controller node/PVC and avoid recursive volume ownership changes. Full activation
and native package acceptance remain open.

## Automatic deployment and idle activation (2026-09-30, in progress)

The local qualified IRC-parity pair is now installed in the launcher, CLI and
production background service. Its original profile was backed up and retained.
An invalid pre-existing bootstrap `ChannelAdmin` registration was removed without
changing credentials; startup validation now catches this before an unlock prompt.
The three Kubernetes anchors are healthy after restoring their exact retained
image digest. This is recovery of the old deployment, not activation of new relays.
See [local recovery receipt](docs/evidence/deployment-automation-20260930/local-and-anchor-recovery.json).

Implementation in this task adds source-bound serial deployment reconciliation,
native systemd and Kubernetes workers, identity preservation, rollback, actual
image observation, an image-pull gate, and publication gated on a fresh deployment
observation. Desktop activation waits for idle UI and daemon state; managed Linux
user services require explicit owner opt-in. Infrastructure artifact production,
operator inventory/credentials, acceptance producers, controller activation and
a complete automatically observed release remain required before this task is done.
The 64-member/covered-receipt/topic-pending/recovery policies are unchanged.

The next checkpoint adds retained infrastructure artifacts to the Linux workflow,
verification against provider archive bytes, OCI publication, bounded transient
worker reconciliation, and an input guard during idle activation. An inventory
revision cannot discard a pending rollback. Component validation passes: 196 Rust
tests (three retained ignores), strict workspace Clippy, native desktop compilation
and 25 desktop tests; 66 UI tests, Svelte checks and client build. Full Python
and evidence fingerprints are retained in
`docs/evidence/deployment-automation-20260930/automation-checkpoint.json`.
This checkpoint is not a live infrastructure rollout or completed automation.

## IRC parity: full 64-member network qualification (2026-09-30)

The user retained the 64-member limit. The final `a460d74`/`624e8b2` pair passes
64 independent members, ten senders and 1,260 covered recipient signatures across
baseline and mixed file traffic, ordinary recovery, visible membership catch-up,
16 MiB pause/reopen/resume/export, removal confidentiality and replacement.
All timing targets, resource capture, cleanup and grant revocation pass. Churn
replaces one removed member; membership never exceeds 64. No larger campaign is
required. See [decisive receipt](docs/evidence/irc-hosted-capacity-20260930/capacity-64-01-pass.json).
Paired Rust passes 194 tests with three retained exclusions and strict Clippy;
generated contracts match. All 20 Rust and two npm archive consumers, 63 UI tests,
Svelte checks/build and Linux desktop compilation pass. Source implementation and
64-member qualification are complete; native installer publication remains
separately gated. See [package receipt](docs/evidence/irc-trunk-integration-20260930/limit-64-merged-packages.json).

## IRC/main invitation integration (2026-09-30)

Merged main's reusable invitation sharing, QR rendering and saved enrollment
progress with hosted channels and contacts. The 64-member maximum is unchanged.
Generated Rust/TypeScript/RPC artifacts include both features; merged UI checks,
unit tests and the client build pass. The companion GComs uses IPC26 to preserve
released IPC23 invitation messages before hosted/file requests. Paired Rust and
protected-network qualification pass for this merged source; archive consumers, frontend and Linux desktop checks also pass.

## IRC parity: retain the 64-member limit (2026-09-30)

The user confirmed **64 members**, including the owner, as the channel limit.
Hosted creation defaults to 64; `/mode +l` accepts 2–64 and GComs independently
enforces signed policy. Capacity qualification now uses 64 independent members,
ten senders and 630 actual recipient signatures per messaging phase. No larger
campaign is required. The former 500-member run was stopped, its grant revoked,
and its original evidence retained without relabelling it as a pass.

## IRC 500-profile network failure — 2026-09-30

The `40b440d` / `c5bbfe8` campaign stopped at the original 180-second cold
bootstrap deadline for member-83, before that profile joined the hosted channel.
Eighty additional members were admitted with the owner offline (81 including the
creator); maximum admission was 16.354s, within 30s. The run never reached its
ten-sender, offline-recovery, file or churn phases. Cleanup passed and the
bootstrap grant was revoked. Original private profiles and complete logs are
retained; the underlying bootstrap failure is under investigation. This is not
500-member qualification. See
`docs/evidence/irc-hosted-capacity-20260930/capacity-500-01-failure.json`.

## Current IRC small-room gate — 2026-09-30

The same `40b440d` / `c5bbfe8` release binary also passes live09: 113ms local
feedback, 3.933s display plus covered recipient receipt, 7.857s offline-owner
admission, 164.709s resumed 16MiB verification and 329.148s full file workflow.
Topic pending followed by authenticated handoff, moderation/voice/notices,
offline recovery, retained partial pieces and the exact exported hash pass.
Owned daemons stopped and the bootstrap grant was revoked. Evidence:
`docs/evidence/irc-hosted-live-20260930/replay-09.json`. The separate 500-profile
protected-network campaign failed during cold bootstrap, as recorded below.

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

### IRC-8 visible membership catch-up — 2026-09-30

The user selected 10-second ordinary offline-message recovery with visible
progress for large membership backlogs. The shared service now tracks confirmed
applied records across pages, displays slow synchronization after two seconds,
and clears the indicator on an empty page, failure or cancellation. Shared
mobile/desktop UI and terminal UI consume the same optional snapshot field;
profiles and GComs IPC remain unchanged. Validation and the actual retained
81-member replay are pending. Earlier timing misses retain their original scope.

### IRC-8 final catch-up validation — 2026-09-30

Shared UI checks pass at desktop and phone widths. The first Rust release run
passed 63 core unit tests (three existing ignores), then found an ordering
assumption in the real private-file/chat test. Commit `39848b8` waits up to
10 seconds for chat independently of file completion, keeping all byte/hash
and transcript-isolation assertions. The original failure is retained in
`docs/evidence/irc-trunk-integration-20260930/catchup-rust-01-failure.json`.
Full final-source Rust, live backlog and package qualification remain in progress.

### IRC-8 protected-network backlog progress — 2026-09-30

Current GComs `250ece7` / GChat `39848b8` binaries recover the retained
81-member owner roster in 102.236 seconds, showing confirmed progress at
0, 32, 64, 83 and 84 applied records and clearing the indicator on completion.
The original profile is unchanged; the daemon stopped and its temporary grant
was revoked. This passes the selected large-backlog behavior, with ordinary
message recovery still separately limited to 10 seconds. Evidence:
`docs/evidence/irc-trunk-integration-20260930/catchup-live-81.json`.
The earlier 96.815-second result remains a failure against its original 10-second
backlog requirement. Full 500-member and installed-native qualification remain open.

Final paired catch-up Rust validation now passes 190 tests with
3 unchanged ignores and strict all-target/all-feature Clippy.
Source: GComs `250ece7` / GChat `39848b8`; evidence:
`docs/evidence/irc-trunk-integration-20260930/catchup-rust-02-pass.json`.

Current catch-up pair `250ece7` / `39848b8` passes all 20 Rust and two npm
archive consumers, generated API contracts, 63 UI tests and Linux desktop
compilation (`catchup-packages-02.json`). The 12-member live smoke03 nevertheless
fails a transient route outage while preparing member-11 admission; ten peers
had joined. Cleanup, full resource sampling and grant revocation pass. See
`docs/evidence/irc-hosted-capacity-20260930/smoke-12-03-failure.json`. GComs
`a715a70` adjusts only bounded snapshot read backoff; its full paired and live
qualification is in progress. Existing failure receipts remain unchanged.

### IRC-8 recovery-policy alignment — 2026-09-30

Smoke04 on `a715a70` / `39848b8` passes all correctness checks: twelve independent
members, 220 recipient signatures, ordinary offline-message recovery in 5 ms,
16 MiB resume in 169.315 seconds, full file workflow in 336.055 seconds,
removal confidentiality, replacement, resource sampling and cleanup. Its old
small-room membership timing rule still fails at 16.590 seconds; that result
remains a failure and its temporary grant is revoked.

The selected user policy distinguishes ordinary offline messages from membership
backlogs, rather than assigning different recovery semantics by room size. The
harness now measures membership replay separately for every room and requires
confirmed visible progress whenever replay exceeds ten seconds. Existing
300/1,800-second observation windows, complete unique rosters and indicator
completion remain mandatory. Ordinary offline messages still have the unchanged
ten-second target. New reports name this policy; old failures are not relabeled.
A fresh smoke is required before the protected-network 500-member campaign.

Fresh smoke05 passes messaging, 220 covered recipient signatures, ordinary
recovery (6 ms), visible membership replay (14.811 s) and verified 16 MiB
resume (104.546 s). It fails removal recovery: the owner completes the kick,
but the victim rejects the accepted update and retains an active view.
Cleanup, resource sampling and grant revocation pass. The exact source remains
unqualified pending a removal replay regression and fix. Evidence:
`docs/evidence/irc-hosted-capacity-20260930/smoke-12-05-removal-failure.json`.

Paired `a715a70` / `39848b8` compilation qualifies 190 Rust tests (three
unchanged ignores), strict Clippy, all 22 package archives, generated contracts,
UI checks and Linux desktop compilation. This predates the removal replay fix;
it does not override smoke05. Evidence: `snapshot-maintenance-paired.json`
in the trunk-integration evidence directory.

Removal fix `2c4535d` / GChat `39848b8` recovers a private clone of the exact
failed smoke05 victim in 262 ms after network readiness. It stays inactive
without replay errors for ten seconds and reopens inactive. The original
profile is unchanged; cleanup and grant revocation pass. Evidence:
`docs/evidence/irc-hosted-capacity-20260930/removal-replay-live-01.json`.
Fresh smoke06 now exercises the full journey with the stricter final churn check.

Fresh smoke06 (`2c4535d` / `39848b8`, harness `c449de7`) passes twelve
independent clients, 220 covered recipient signatures, ordinary recovery,
visible membership replay, mixed file traffic, removal confidentiality and
replacement. The victim remains inactive with no replay error after replacement.
Timing, resource capture, cleanup and grant revocation pass. Evidence:
`docs/evidence/irc-hosted-capacity-20260930/smoke-12-06-pass.json`.
The separate two-client journey and full 500-member campaign remain open.

The two-client run10 observes a 5.206-second delivery/receipt result against the
unchanged five-second target. Newly durable sends and committed receipts can
wait for the next one-second application tick. A coalesced application wake-up
now schedules that work promptly; idle reads and refused mutations do not wake
the worker. This changes no transport profile or acknowledgment requirement.
Cluster regression and new live timing qualification are pending.

Completed run10 retains correctness but fails timing: 5.206-second online
message/receipt and 182.527-second file resume against unchanged 5/180-second
targets. Full file workflow is 341.821 seconds with the correct 16 MiB hash.
Independent OS checks confirm no owned clients remain; the temporary grant is
revoked. See `live-10-original-timing.json` in hosted-capacity evidence. The
original report is unchanged; the updated harness explicitly records cleanup.

GChat `556c8f8` / GComs `2c4535d` passes 191 Rust tests (three unchanged
ignores) and strict all-target/all-feature Clippy. The real local admission
regression verifies coalesced durable wake-up and idle reads/refusals. Eight
Python harness tests pass, including exceptional cleanup and strict deadlines.
Evidence: `worker-wake-qualified.json` in trunk-integration evidence.
Fresh exact-source two-client run11 is active; package qualification follows.

The same `2c4535d` / `556c8f8` pair passes all 20 Rust and two npm archive
consumers, generated contracts, 63 UI tests, frontend checks/build and Linux
desktop compilation. Original source checkouts are unchanged; nothing was
published. Evidence: `worker-wake-packages.json` in trunk-integration evidence.

Fresh exact-source run11 passes the two-client protected-network journey: 111 ms
local feedback, 4.439 s message plus covered receipt, 6.739 s offline-owner
admission, Topic pending and authenticated handoff, moderation, voice, notice
and ordinary offline-message recovery. Verified 16 MiB resume takes 156.586 s;
the whole file workflow takes 231.017 s. Existing timing targets, cleanup and
grant revocation all pass. Evidence: `live-11-pass.json` in hosted-capacity
evidence. Fresh exact-source smoke07 is running before the 500-member campaign.

Fresh exact-source smoke07 passes all twelve independent members and both
ten-sender phases (220 covered recipient signatures), ordinary offline recovery
(5 ms), confirmed membership progress (17.102 s), 16 MiB resume (97.373 s),
full file workflow (254.144 s), removal exclusion and replacement. Timing,
resource capture, cleanup and grant revocation pass. Evidence:
`docs/evidence/irc-hosted-capacity-20260930/smoke-12-07-pass.json`.
The protected-network 500-member campaign now runs on this same verified pair
under the original six-hour, 64 GiB and 12-CPU limits; it has no result yet.

During the fresh 500-member run, 104 running profiles show 80 daemons with
17 threads, 22 with 16 and two still starting with five. Five hundred established
17-thread daemons alone require 8,500 tasks, exceeding the launcher's arbitrary
8,192-task ceiling. Before reaching it, the qualification-host ceiling was
corrected to 16,384. The 12-CPU, 64 GiB and six-hour limits, original timing
targets, application/harness hashes and protocol checks are unchanged. This is
an explicitly retained environment correction, not a 500-member acceptance:
`docs/evidence/irc-hosted-capacity-20260930/capacity-500-02-task-ceiling.json`.
