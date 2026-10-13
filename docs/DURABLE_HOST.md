# Durable per-instance host startup

Status: source and isolated lifecycle qualification passed; signed release and
installed acceptance remain in progress (F5 / durable-host).

An instance with retained component ownership must reopen through its configured
host. A desktop launch previously depended entirely on `--fleet-config`; when its
managed daemon was stopped and the shortcut omitted that argument, a personal
worker started and the runtime refused the retained identity. The ownership
refusal was correct. Host selection was not retained.

## Startup association

After a successful scoped unlock, the host publishes an owner-private, versioned
`chat.host.json` beside the archive. It binds the existing instance ID, native
profile/archive/socket paths, carrier/network selection, fleet configuration
reference and public component partition. A managed daemon learns its exact Linux
user unit from its own process association. Passphrases and component tokens are
not copied into this registration.

First publication is atomic and no-clobber. Reopening restores omitted fleet and
service arguments; explicit conflicting options refuse. Credential rotation may
change tokens and permissions within the existing authenticated component IPC
contract without changing the retained identity or routing partition. A changed
identity, partition, instance or host recipe needs explicit configuration repair.

Desktop entries select the saved instance (for example with `--home`). The saved
instance owns its host association. Personal instances without a registration keep
the existing startup path.

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
