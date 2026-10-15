# Durable per-instance host startup

Status: source and isolated lifecycle qualification passed; signed release and
installed acceptance remain in progress (F5 / durable-host).

Latest follow-up, 2026-10-15: signed0.1.228 has independently verified source-bound
Linux qualification receipts, package signature and matching running CLI/desktop.
Its fresh stopped backup and isolated restoration preserve the same identity,
memberships,205message digests and23operations. The encrypted cache metadata uses
fresh nonces; logical snapshot comparison verifies its unchanged empty-cache/config
state. Four completed operations missing from an earlier snapshot reached their
exact seven-day retention deadlines; retained encrypted evidence confirms this.

The original228delivery deadline remains failed. Normal authenticated reconnect
imports later deliver that exact queued message and its recipient ACK without
resubmission. Source diagnosis also found obsolete deferred owner announcements,
POSTs discarded during a known dial cooldown, and a dispatch race after deferred
frames were already materialized. The combined SDK fixes pass474node,79transport
and40native TLS checks, plus the exact GChat fleet/ownership/daemon integration.
The intended fleet component's existing IdentityRead runtime-status operation now
passes its causal scoped test, while shell/profile administration remain denied.
These source results require the normal signed successor and fresh installed
functional/lifecycle acceptance before closeout. [Source evidence](evidence/durable-host/source.json).

Installed follow-up, 2026-10-15: signed0.1.223's public package and both running
executables match independently verified receipts. After an approved normal
desktop close, the owner maintenance contract deferred until its existing view
lease expired, then allowed a stopped backup of39files/106,662,221bytes. The
service and both update timers were restored, and the production desktop entry
reopened the matching release. All204 message digests,23 operation records,
memberships and identity/partition remained exact. A network-isolated clone of
that fresh backup restored the same complete logical state in15.544seconds.

The designated-peer223 delivery trial still failed its original300-second stage
and remains failed. A real TLS/H2 regression then exposed long-lived subscriptions
consuming all of a pooled connection's stream capacity, blocking finite recovery
controls. GComs `acbe008` reserves that credit and uses bounded same-route/class
subscription shards;76transport controls, four TLS/restart journeys and strict
checks pass. Normal immutable successor226 includes this repair and the fleet
endpoint repair below. Its Linux native gate subsequently failed a browser-fixture
history race; the original failure remains retained. The corrected fixture passes
the full Chromium/WebKit matrix. Signed successor qualification and the installed
journey remain required. [Installed and recovery evidence](evidence/durable-host/installed.json).

Installed follow-up, 2026-10-14: the currently observed signed0.1.217 host retains
the same identity, eleven conversations,203 fully paginated message digests and22
operation records. Its fresh stopped backup contains39 regular files and
102,540,193bytes; actual restoration in an isolated network namespace verifies
every message digest and operation state. The original managed registration stays
in the backup; only the isolated clone is explicitly relocated for restoration.
Both update timers and the production service were restored after backup.

The live fleet check found a further restart defect: an abandoned fleet socket
still existed, so the fleet listener refused to bind although chat was ready.
The startup journal and a causal retained-profile test show the same error.
Fleet startup now uses the SDK's existing guarded socket preparation under one
generation's owner lock, held through serving and cleanup. An active listener,
ordinary file or symlink is refused; the runtime identity/partition checks remain
before endpoint preparation. Actual disposable-daemon crash/relaunch recovers
authenticated fleet attachment. Signed deployment and final installed fleet,
message/file, rollback and login/reboot acceptance remain required.

The earlier cache-count change is separately accounted for by authenticated
seven-day expiry. Independent backup recovery restored the original41,988,496byte
file with its original hash. This recovery is not a claim that expired live cache
bytes survived. See the [current installed observation](evidence/durable-host/installed.json).

Installed follow-up, 2026-10-13: the signed 0.1.214 successor is now installed.
Its production host was activated after a consistent stopped backup and verified
hotfix ancestry; only the superseded temporary override was retired. The host
publishes its service-bound registration, runs the exact packaged executable and
is connected with the retained identity, conversations and file. The actual desktop
entry launches and relaunches the matching GUI. Both update timers are active and
the installed activation helper matches the qualified source. The
[alignment delivery receipt](evidence/irc-ux-alignment-20261013/installed.json)
records this cutover; the broader lifecycle requirements below retain their own
acceptance scope.

Installed follow-up, 2026-10-14: the normal package/activation timers advanced the
workstation to signed0.1.216, containing GComs9e889b7's channel-recovery fairness
repair. The public DEB, existing-key signature and both executable hashes were
independently verified. The actual packaged host preserves the same identity,
partition, eleven memberships, all202 recorded messages and165 cache files.
A fresh current-state backup after this automatic migration contains201 files
and135,111,879bytes, copied with the host stopped and profile/launch locks held.
Both timers and the service were restored afterward. This is a post-migration
backup, separate from the stopped pre-migration backup taken for0.1.214.

The automatic0.1.216 activation receipt recorded `PermissionError` after its
restart request, although the new matching process subsequently ran normally.
The original receipt remains failed. The process observer now treats an
unreadable `/proc` observation like a disappearing process: it breaks the stable
observation pair and waits within the original30-second deadline. It still needs
two consecutive matching PID/path/hash observations; persistent unreadability
fails and preserves the one-attempt restart guard. Three causal controls fail
on the previous helper, and all35 activation/input controls pass after the fix.
This qualifies the observer correction in source; it does not relabel the old
activation receipt or complete the outstanding live delivery/lifecycle gates.

Retained observer checks: `activation-proc-permission-before-1` and
`activation-proc-permission-after-1` under the durable-host private evidence root.
Before/after code comparison found generic process polling in
`GarageGames/Qt:qt-5/qtwebkit/Tools/Scripts/webkitpy/common/system/executive.py`
(cosine0.6502/rerank0.0230 before;0.6500/0.0255 after). It checks process presence;
this helper additionally binds the exact executable and requires a stable pair.
No implementation was copied, and the index did not identify a close match.

An instance with retained component ownership must reopen through its configured
host. A desktop launch previously depended entirely on `--fleet-config`; when its
managed daemon was stopped and the shortcut omitted that argument, a personal
worker started and the runtime refused the retained identity. The ownership
refusal was correct. Host selection was not retained.

## Startup association

After a successful desktop runtime unlock, the host publishes an owner-private, versioned
`chat.host.json` beside the archive. It binds the existing instance ID, native
profile/archive/socket paths, carrier/network selection, fleet configuration
reference and public component partition. A managed daemon learns its exact Linux
user unit from its own process association. Passphrases and component tokens are
not copied into this registration.

First publication is atomic and no-clobber. This also preserves standalone
personal carrier and network choices before a later argument-free launch or
update. An older personal profile migrates after opening once with its explicit
existing installation configuration. Reopening restores omitted fleet and
service arguments; explicit conflicting options refuse. Credential rotation may
change tokens and permissions within the existing authenticated component IPC
contract without changing the retained identity or routing partition. A changed
identity, partition, instance or host recipe needs explicit configuration repair.
Intentional first fleet/service adoption can fill an absent binding only while
all other recipe fields remain equal. Validation is read-only; atomic replacement
waits for the runtime to authenticate and exclusively own the profile. An existing
fleet partition or service cannot be replaced or downgraded through this path.

Desktop entries select the saved instance (for example with `--home`). The saved
instance owns its host association. A personal desktop recipe explicitly records
no fleet and no managed service for the standalone path. Mobile hosts remain
in-process with app-owned configuration; desktop absolute-path recipes are not
introduced into OS-relocatable mobile data containers.

## Attachment and lifecycle

The application advertises a `gchat.host.v1:` capability containing a SHA-256 of
the canonical public host recipe. A registered attachment validates this alongside
the existing instance/API handshake before opening local operation-handle state.
The GComs identity pin and retained-ownership checks still govern runtime unlock.
The capability is a local configuration consistency check, not a network credential
or a substitute for owner-only IPC authentication.

Startup serializes launch decisions using a private per-instance file lock and a
30-second overall deadline. Managed instances start their exact registered user
service; standalone instances use the existing detached-worker path. Local
readiness and network recovery have separate status. An incompatible responding
endpoint is a configuration error, not permission to start another profile owner.

Native startup errors preserve `host_configuration`, `host_mismatch` and
`host_unavailable` codes into the interface. A failed request can invalidate a
desktop attachment for a subsequent reconnect; an uncertain mutation is not
replayed by the native adapter. Existing operation handles own its reconciliation.

Unix attachments verify the kernel peer UID; managed attachments additionally
require the user service's actual MainPID. Headless activation uses the same
registration and the existing owner maintenance lease, deferring while a window
or admitted operation remains active. Unknown activation outcomes retain their
one-attempt receipt. Only that receipt's abandoned lease may be released later;
an uncertain restart is never repeated automatically.

## Validation and deployment requirements

Full WebKit qualification also exposed an existing scroll-anchor failure. The
reader now chooses the nearest representable scroll position when an engine
quantizes `scrollTop`, and viewport resize clears an earlier gesture's intent
window so layout-generated scrolling cannot replace the saved anchor. The
original font/resize/activity/incoming-message regression and its half-pixel
assertion are retained. Baseline failed three repetitions; the combined repair
passes all three. Full browser qualification remains separately recorded.

The causal regression creates a real disposable identity, registers fleet scope,
checkpoints, removes the original fleet launch argument and reopens the same
identity with the original component credentials. Negative controls cover copied
registrations, wrong partitions/identities, explicit conflicts, credential
rotation, native paths, private-file validation, bounded loading, and wrong-host
refusal before attachment state is opened. Real daemon, managed-service, UI,
upgrade/rollback and installed lifecycle acceptance remain required.

Use the current production release policy: paired source qualification, exact
signed artifact receipts, authenticated messages, interrupted-file recovery,
compatible relay observations and state-preserving upgrade/rollback. The retained
host hotfix must remain until a signed successor contains its required fixes and
passes installed acceptance. Inventory and retire only the exact qualified
temporary overrides; retain rollback copies and a consistent stopped backup.

The [source receipt](evidence/durable-host/source.json) records the complete Linux
CI, browser matrices, real user-service controls, isolated network checks and
current-state rollback. It preserves each original failed attempt. The task is
not complete until the normal icon, cold service start, invitation
arrival, lock/unlock, restart, login/reboot, messaging, files, fleet attachment,
and canonical installed update cycle have real receipts. Qualification progress
and failure dispositions will be recorded in `docs/evidence/durable-host/`.

## Operator procedures for the registered workstation

The production home is `$HOME/.local/share/gchat-production`; its private
`chat.host.json` selects `gchat-fleet-host.service` and references the protected
fleet configuration under `$HOME/.local/state/gchat-fleet/`. Keep credential and
unattended-unlock files private. The following status commands were exercised
against the signed223 installation:

```sh
gchat --home "$HOME/.local/share/gchat-production" paths
systemctl --user status gchat-fleet-host.service
systemctl --user show gchat-fleet-host.service -p MainPID -p ActiveState -p NRestarts
systemctl --user status gchat-headless-activate.timer gchat-hub-backup.timer
systemctl status gchat-package-update.timer
sha256sum /usr/bin/gchat /usr/bin/gchat-desktop
```

Start the exact registered unit with `systemctl --user start
gchat-fleet-host.service`, or open the saved production icon. Close a view to
leave receiving active. `/lock` hides the archive in every view while receiving
continues; `/quit` intentionally disconnects the instance. Before a planned stop,
obtain the existing authenticated maintenance readiness and use `systemctl --user
stop gchat-fleet-host.service` for orderly checkpoint/shutdown.

Use these diagnostic distinctions:

- `host_unavailable`: inspect unit state and the bounded user-service journal.
- `host_configuration`: restore the protected registered recipe/configuration.
- `host_mismatch`: compare selected home, instance/partition, registered unit,
  actual MainPID and build. Repair the conflicting owner through orderly lifecycle.
- Locked protocol/archive: use normal unlock after verifying host association.
- Local workspace ready/network recovering: inspect routing separately. A connected
  indicator does not establish recipient delivery or authenticated acknowledgment.
- API incompatibility: use the same qualified package/dependency pair for both
  components and verify their actual running executable hashes.

The package timer installs signed packages; headless activation defers while a
view or admitted operation is active. A closed view's retained lease expires after
45seconds. Uncertain activations retain their one-attempt receipt under
`$HOME/.local/state/gchat-headless-activation/`; reconcile that receipt before any
manual recovery rather than issuing an unrecorded second restart.

The installed `gchat-hub-backup.service` retains a legacy daily **live file-copy**
set under `$HOME/.local/state/gchat-fleet/backups/`. Its script explicitly does not
claim a transactionally consistent multi-file checkpoint. Deployment preparation
uses a separate complete stopped recovery set, including registration, every
profile/archive/cache file, fleet configuration, effective unit/drop-ins and both
compatible executables. Preserve the original daily copy and the complete set.

The tested complete-backup sequence closes the desktop normally, excludes running
package/activation jobs, holds package/launch locks, obtains the existing owner
maintenance lease, requires `ready`, orderly-stops the registered service, locks
the remaining profile files, then copies/hash-readbacks/fsyncs the private set.
It finally starts the same service, verifies stable matching executable observations,
restores previous timer states, verifies fresh attachment and reopens the icon.
Full history pagination, memberships, identity/partition and operation states are
compared separately from encrypted-file hashes. Exercise recovery in a network
namespace with only loopback, explicitly relocate only the clone's registration,
and keep it disconnected from the live network. The dated installed receipt binds
the current 0.1.228 stopped backup and isolated restoration (all 205 message digests,
memberships, 23 operation records and logical cache), alongside earlier recovery
points. Take another fresh complete set before the final candidate installation.

For a state-preserving rollback, retain failure evidence, checkpoint/stop the
candidate and open its **current state** with the tested compatible predecessor
and exact retained service configuration. Restoring an older backup is a distinct
recovery operation that can discard newer state. Keep the prior signed package,
detached signature, build/dependency receipt and exact unit/drop-ins available.
The final repaired release still requires its own current-state rollback receipt.
Logout/login and reboot acceptance require an agreed maintenance window covering
other active workstation work. The final manifest must identify each performed
acceptance row, actual running hashes and the verified rollback set.

## Implementation comparison

After-write peer-binding comparison:
`vercel/turborepo:crates/turborepo-daemon/src/endpoint.rs` (cosine0.6484,
rerank0.8081) checks `peer_cred().uid()` against the current UID. GChat also binds
managed connections to the observed MainPID and validates the instance/host recipe
before opening operation-handle state. The owned IPC and actual-service tests
exercise refusals as well as successful attachment.

The JSON comparison `bitnom/schwab-py-remote:schwab/contrib/util.py`
(0.7334,0.9241) retries after modifying escaped input. GChat instead rejects
invalid/duplicate fields and explicitly limits nesting to32 levels. The registry
TOCTOU comparison returned generic check/use shapes in
`ZoneMinder/zoneminder:src/zm_fifo.cpp` (0.5878,0.4688) and
`ruby/ruby:lib/fileutils.rb` (0.4957,0.4688). Host metadata remains owner-private;
first publication and launch-lock creation are exclusive, and connection authority
comes from kernel credentials and the bound handshake rather than path presence.

Scroll anchoring discovery found
`openwrt/luci:themes/luci-theme-footstrap/htdocs/luci-static/resources/fs-fit.js`
(0.6836,0.9196), which measures residual engine anchoring and distinguishes scrolling
from layout correction. GChat retains its existing keyed anchor and adds the
small quantization/viewport-intent correction proven by its unchanged regression.
These comparisons guide implementation review; they do not establish live findings
in indexed projects.

Code-index startup results were generic single-instance implementations:
`khulnasoft/EditSync:crates/editsync/src/editsync/mac_only_instance.rs`
(cosine 0.7031, rerank 0.5467) and
`henrikpersson/potatis:nes-cloud/src/server/runners/process.rs`
(0.6670, 0.5467). The fetched EditSync implementation uses bounded connect/read
timeouts but falls back to accepting another instance after a failed handshake;
registered GChat hosts must refuse that case.

`Capybara003/sniper-bot:src/config/loader.rs` (0.7791, 0.8741) is an unbounded
`read_to_string` JSON loader. This implementation retains GChat's bounded
owner-private file validation and atomic publication instead. The index results
are implementation comparisons, not current vulnerability findings.
