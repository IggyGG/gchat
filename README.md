## Hosted and contact files (qualification in progress)

The shared file controls now select the explicit hosted/contact transfer profile
for those conversations and preserve the legacy channel/PM cache. Piece data uses
bulk transport; verified download-completion acknowledgments stay covered. Contact
blocks replace the file worker's authorization set before the command completes.
The new profile has a separate encrypted `.pieces.v2` cache. Both caches share
one GChat admission budget. File permissions follow the conversation: direct
message permission for contacts and hosted-channel permission for hosted rooms. End-to-end, capacity
and native release qualification is still in progress on the IRC parity branch.

## Independent contacts and local IRC workflows

Use `/contact card` to share your signed card deliberately, then `/contact add
alias card` to save a peer. Both sides must add each other. `/contact open alias`
opens a persistent conversation independent of all channels. `/contact update`
accepts only the same identity; `/contact verify alias fingerprint` records a
manual comparison. No global directory or automatic scoped-identity linking is
introduced. `/block` persists across reopen, stops new sends and suppresses new
inbound replies; it cannot recall packets already admitted to the transport.

Text, `/me` and `/notice` use durable application messages and exact-content,
peer-authenticated receipts. A notice never triggers an automatic notice reply.
`/away reason`, `/back` and `/presence on|off` share presence only with the current
contact, with ten-minute leases and seven-minute renewal. Sharing defaults off;
unknown or expired presence is not proof that someone is offline.

`/mute on|off` suppresses a conversation's unread indicators while retaining
history. `/ignore member` and `/unignore member` affect only the current scoped
identity. `/highlight add text|remove text|list` marks matching incoming messages.
`/alias name /command arguments` creates a bounded single-command alias; arguments
are appended literally and aliases cannot replace built-ins or run shell commands.
`/unalias name` removes it. Contacts and preferences use separate encrypted
`.contacts` and `.preferences` sidecars that older GChat clients leave untouched.
Signed-card import commands have a 192 KiB limit; ordinary message limits remain.

## Hosted channel work in progress

The opt-in `/hosted create #name nickname [private|public|code]` and
`/hosted join invitation #alias nickname` commands use the installed network's
hosted MLS service. Private creation is the default. `/help` in a hosted channel
lists moderation, invitations, roles, presence and channel commands. `/whowas
nickname-or-scoped-id` searches this channel's retained name observations, including
departed members. It keeps at most 2,048 observations and returns at most 64 matches;
it does not query other rooms or discover global identities. Operators
can explicitly publish a directory name with `/publish name`, and withdraw it
with `/publish --remove`. Use `/hosted list [cursor]` anywhere, or `/list` in a
hosted room, to browse the installed network. Public admission alone does not
publish a room. Private/secret rooms and encrypted topics stay out of listings. Topic,
nickname, action, notice and signed activity share the same desktop/TUI API.
Message status distinguishes queued, service accepted, recipient delivered and
failed. A durably queued local message appears immediately, even while a service
request is stalled. Service acceptance never proves recipient delivery.

Hosted history uses a separate encrypted `.hosted-history` sidecar; older GChat
versions cannot rewrite it. Existing channel archives and scoped private messages
retain their identities. Unlock alone does not create hosted history. IRC control
formatting is rendered with bounded styles, never HTML or terminal escape output.
This task branch requires its paired GComs IRC-parity branch. No dependency or
installed-release update is implied. Newcomers see `Topic pending` until an authorized member returns to hand off the
encrypted topic; invitations contain no extra metadata secret. Independent-file
transfers and full network/native capacity qualification remain in progress.

Release tooling has a separate Linux/Windows portability workflow; it does not
compile applications or qualify installed releases. Mac artifact paths retain
POSIX ZIP syntax on all hosts. The coordinator daemon remains POSIX-only.

Windows candidate 36 can be diagnosed with the retained-installer workflow,
without compiling again. Its interrupted-transfer deadline failure is preserved;
a later run must meet the same budgets and cleanup checks. iOS retained-verification
archives also retain the original failed startup report referenced by recovery.

Retained iOS releases can recover from a simulator launch timeout using the
original signed IPA and unchanged simulator app. The original failure remains
retained; fresh native tests, profile/reopen lifecycle and complete cleanup must
pass before verification can authorize upload. No application rebuild or re-signing
is performed by that recovery path.

Generated release configurations keep installed acceptance receipts in separate
platform directories. A passing Linux application check cannot authorize a
mobile release; SDK qualification remains separate. See
[automatic releases](docs/AUTOMATIC_RELEASES.md).

Mac release CI now includes the same bounded 16 MiB interrupted-file and
authenticated-message journey as Windows, using disposable profiles and a
protected fixture invitation. Existing releases retain their original evidence;
this automation change alone does not qualify or publish a new installer.

Current paired GComs source selects responsive profile 46: messages are eligible
immediately, with independent randomized interactive cover. Timing/activity privacy
is unqualified. See [production policy](docs/PRODUCTION_RELEASE.md); this source
change is not a claim that installed/store artifacts have been updated.

# GChat

The [Apple App Store creative pack](marketing/app-store/retro-v1/README.md)
adds four iPhone and four iPad screenshots plus English listing metadata to the
iOS draft. App Store publication still requires the qualified build and Apple's
encryption approval; the pack records its upload receipt and current status.

The [Play Store creative pack](marketing/play-store/retro-v1/README.md) contains
an old-school chat visual direction, exported graphics, a local preview and
listing copy submitted to Google Play. Its sample-data browser captures match
the shared UI source of published Android build 1055; submission details are
recorded in the pack's `publication.json`.

Current work follows the [reliability test plan](docs/RELIABILITY_TEST_PLAN.md):
cluster recovery/concurrency checks, then exact-artifact platform validation.
Historical release/device observations below are not current qualification.

GChat uses the public `gcoms` Rust application API for its protocol runtime. It
owns the chat archive and UI; GComs owns identity, encrypted protocol state,
network enrollment, recovery, invitations and the file-transfer worker. GChat
retains its archive, signed network settings, file-cache path/key and UI contract. The embedded backend is the
default. To use a bundled shared service, run `gchat daemon --gcomsd
/absolute/bundle/gcomsd --gcoms-endpoint /private/runtime/gcoms.sock` with the usual
instance options. Each GChat profile remains independent inside that service.
Locking/disconnecting stops that profile without stopping other applications.

In-process hosts retain incoming channel and private messages in a bounded,
encrypted protocol inbox until the chat archive is saved. Failed archive writes
leave those messages available for retry and show an actionable storage notice;
uncommitted history is not published. The external shared-service archive path
keeps its existing contract and is outside this new transaction boundary. See
the [archive transaction and rollback requirements](docs/RELIABILITY_TEST_PLAN.md#incoming-archive-transaction-candidate).

Attached views share a cached projection and wait for actual archive/UI changes.
Idle file observation does not copy the retained operation journal. Receiving,
persistence, delivery acknowledgments and the cover schedule are unchanged.
The [controlled idle benchmark](docs/evidence/idle-cpu-20260925/summary.json)
measured 92.45% less CPU with four views and a large retained operation history;
this is not an installed-client or relay-load measurement.
Signed Linux 0.1.13 now carries this fix through the update/APT feeds.
The website’s Linux download link follows the qualified publisher automatically,
with immutable package links, signatures, hashes and exact source details.
Existing unlocked instances retain their running executable until their next start;
see the [deployment receipt](docs/evidence/idle-cpu-20260925/deployment-20260927.json).

For paired-source development, validate against the matching GComs checkout with
its `scripts/check-gchat.py --gchat /absolute/gchat --offline` command. Keep public
registry manifests and canonical release lockfiles intact; each published download
retains its exact source and dependency bindings in its signed release manifest.

**GChat** is the reference chat application for **GComs**, with a Tauri desktop
application, terminal client and local service built from one repository.
The Rust API contract drives both native clients and generated TypeScript bindings.

Development and release authority remains in the existing local Forgejo repository.
Public delivery uses [IggyGG/gchat](https://github.com/IggyGG/gchat) and
[IggyGG/gcoms](https://github.com/IggyGG/gcoms) as GitHub mirrors.
Current downloads are signed Linux x86_64 and Android through Google Play.
Mac and Windows updates for the current network are still being qualified; their
earlier signed installers remain archived.
Physical Android and iPhone checks are currently deferred. Four disposable Android
emulators and the Mac iOS simulator passed their scoped lifecycle checks;
[exact source/artifact bindings](docs/evidence/emulator-lifecycle-20260924/summary.json)
remain separate from current runtime and mobile network/file qualification.
Historical physical-device and release observations remain in [PLAN.md](PLAN.md).
Live APNs/FCM and new store publication are not qualified by those lifecycle runs.
Windows x86_64 and iOS
releases are being qualified independently;
availability and exact versions are listed on the download page. See
[platform release delivery](docs/PLATFORM_RELEASES.md).
Retained Windows network diagnosis can reuse a pinned signed installer via
`windows-verify.yml` (`network_candidate: windows29`), without rebuilding it;
aggregate fixture diagnostics preserve the original recovery deadlines.

For installation and first launch, see [gchat.boo](https://gchat.boo/#downloads)
and the [installation guide](docs/INSTALL.md). GChat includes signed Hetzner relay
settings; users import a network invitation and do not configure relay addresses.
The [website and delivery tooling](docs/PUBLIC_DELIVERY.md) live in this repository.

Current validation covers secure connections, authentication, transport security,
local IPC access controls, disconnect/reconnect behavior, and private file sharing.
The shared Rust integration has a native Linux/macOS test and size matrix; see
the [GComs integration report](https://github.com/IggyGG/gcoms/blob/main/docs/RUST_INTEGRATIONS.md).
GChat's desktop release checks are recorded separately in the
[release evidence procedure](docs/RELEASE_EVIDENCE.md).

[Private file sharing](docs/FILES.md) adds verified pieces, restart, multiple
authorized sources, explicit download acceptance and a bounded encrypted cache.
Optional local [persistence diagnostics](docs/PERSISTENCE.md) measure protocol
profile write counts, bytes and time during file-transfer investigation.

## Build and run

Install Rust 1.98, Node 22, npm 11 and the platform's Tauri v2 prerequisites.
After GComs 0.1.0 packages are available from crates.io/npm:

```sh
cargo build --locked -p gchat-tui
cargo run -p gchat-tui --bin gchat -- --help
npm ci --ignore-scripts
npm run check
npm test
npm run build
python3 scripts/collect-notices.py
npm run tauri -w @gchat/client -- dev
```

For development before package publication, use GComs' package-consumer staging
script. Public manifests use versioned registry dependencies; no private Ghost
checkout or sibling layout is required by the released project.

Run `gchat paths` to inspect the existing platform profile/archive locations.
The desktop app launches its own local service worker. `gchat daemon --interactive`
starts a locked standalone service; attach a UI to unlock the selected instance.
Headless deployments may use an owner-only passphrase file or private stdin pipe.
Never put passphrases on a command line. An existing archive with a separate
passphrase remains locked until explicitly unlocked.

## Network and identity

GChat bundles the existing application's signed network defaults and installed
trust root. Joining the operated network requires an invitation. Enter it through
the application's onboarding flow. The invitation must agree with independently
trusted network configuration. Custom providers can be configured explicitly.

An unavailable provider does not mean a profile is corrupt. Preserve the profile,
archive, invitation and retained network state while diagnosing recovery. Do not
create a replacement identity to repair an unavailable connection. The app preserves
existing profile paths and formats during the GComs branding transition.

GChat cannot open a retained Ghost machine/central profile as personal chat. Use
its original scoped host. Public GChat excludes managed commands, machine agents,
recorders and private installer/identity services.

## Project map

| Location | Purpose |
| --- | --- |
| `crates/chat-api` (`gchat-api`) | Typed chat service and shared UI schema |
| `crates/core` (`gchat-core`) | Profile, archive, chat model and standalone service |
| `crates/tui` (`gchat-tui`) | `gchat` terminal application and daemon entry point |
| `ui` | Shared Svelte UI and bound RPC bridge |
| `apps/client` | Tauri desktop client |
| `website` | gchat.boo source; built with `scripts/website.py` |

See [TESTING.md](TESTING.md), [integration](docs/INTEGRATION.md),
[network operation](docs/NETWORK.md) and [SECURITY.md](SECURITY.md).
GComs provides transport and typed services; GChat owns chat behavior and UI.

MIT OR Apache-2.0, with [separate third-party notices](NOTICE.md).
Current downloads cover Linux x86_64 and Android through Google Play.
Mac and Windows current-network updates are being qualified; iOS publication
awaits Apple’s France-inclusive encryption review.
Android lifecycle checks include emulator coverage and a limited physical-phone
follow-up; battery and attributable live push qualification remain open. Each
download retains its own source and validation scope. See the [release evidence procedure](docs/RELEASE_EVIDENCE.md).

The preview uses GComs' rustls/XML advisory fixes and disables unused postcard
heapless defaults. `deny.toml` records reviewed transitive-version exceptions and
two unmaintained build-time macros (OpenMLS/libcrux and ratatui). These require
follow-up upgrades; no runtime vulnerability is waived. The desktop dependency
graph has its own audit and native packaging requirements. See the exact
[dependency review and follow-up](docs/DEPENDENCIES.md).

## Optional local fleet controller

Desktop/headless workers accept `--fleet-config <private-file>` (`GCHAT_FLEET_CONFIG`). The file pins this existing GChat safety number and fixed component partition. The worker opens `<protocol-socket>.fleet` for registered local credentials without opening a second profile. Locking or disconnecting drains fleet connections; registry changes revoke existing connections before replacement. The private component configuration must accompany every subsequent startup of that profile. Fleet publication metadata is an opt-in file API backed by the encrypted chat archive; ordinary file replies stay compatible.

## Welcome and invitation cards

The shared welcome screen detects an existing identity before offering setup,
confirms new passphrases, and offers the existing recovery guidance. Invitations
can be saved as evergreen PNG cards and opened or dropped into GChat. Send the
original PNG as a file: screenshots and edited images lose invitation data.
Opening a card stages or previews it; joining still requires explicit acceptance
of the service-validated network and channel. Text invitations remain supported.
See [UX behavior and qualification](docs/UX-CARDS.md). No new dependencies.

Locked passphrase errors appear once, beside the field, and can be retried.
The signed local Linux package passed native first-run, retained-profile upgrade,
invitation picker and narrow-layout checks. See the
[installation receipt](docs/evidence/ux-cards/signed-local-summary.json); public
installer qualification remains separate.

The desktop dependency policy records exact native API version duplicates required
by the updater's existing dependencies; see [the graph review](docs/DEPENDENCIES.md).

Release file checks use a bounded 16 MiB interrupted transfer; the 1 GiB campaign runs separately. See [automatic releases](docs/AUTOMATIC_RELEASES.md).

SDK release archives are closed and hash-checked before atomic publication,
including on Windows. Interrupted copies leave the previous index intact.

The macOS release worker allows 120 seconds per browser-download socket;
this setup budget does not change application test deadlines.

Release publication accepts repeated references to the same verified artifact,
while checking every evidence hash and rejecting ambiguous installer candidates.
Both updater and package inputs are selected before public pointers change.
# Release operation

Production uses immutable artifacts and separately bound qualification evidence.
See [automatic releases](docs/AUTOMATIC_RELEASES.md) for conservative source-change
classification, paused admission during stabilization, and the owner-approved
Windows 4 MiB recovery check. A tooling update or policy decision is not a native
application pass.

The `scripts/hosted-live.py` qualification driver exercises real hosted GChat
daemons on the installed protected network, with creator-offline admission,
covered receipts, moderation, restart and a 16 MiB resumed file. It retains
private profiles/evidence and waits for explicit network-operator provisioning
of its generated channel ID. Running it is not an installed-release claim.

Hosted live qualification reports correctness and latency independently. The
first completed protected-network two-client journey verified messages, policies,
offline recovery and a resumed 16 MiB file, but missed small-room receipt and
file-resume timing targets. See docs/evidence/irc-hosted-live-20260930/summary.json;
it does not qualify the 500-member or native installed release gates.
