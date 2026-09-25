Current paired GComs source selects responsive profile 46: messages are eligible
immediately, with independent randomized interactive cover. Timing/activity privacy
is unqualified. See [production policy](docs/PRODUCTION_RELEASE.md); this source
change is not a claim that installed/store artifacts have been updated.

# GChat

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
Signed Linux x86_64, Apple Silicon/Intel Mac and Android APK downloads are available.
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
Published downloads currently cover Linux x86_64, macOS Apple Silicon/Intel and Android
ARM64/x86_64. Windows and iOS releases are being qualified separately.
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
