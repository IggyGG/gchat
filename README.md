# GChat

**GChat** is the reference chat application for **GComs**, with a Tauri desktop
application, terminal client and local service built from one repository.
The Rust API contract drives both native clients and generated TypeScript bindings.

Development and release authority remains in the existing local Forgejo repository.
Public delivery uses [IggyGG/gchat](https://github.com/IggyGG/gchat) and
[IggyGG/gcoms](https://github.com/IggyGG/gcoms) as GitHub mirrors.
The first signed release is being prepared for Linux x86_64, Windows x86_64,
and macOS Apple Silicon/Intel. See [release preparation](docs/RELEASE.md).

For installation and first launch, see [gchat.boo](https://gchat.boo/#downloads)
and the [installation guide](docs/INSTALL.md). GChat includes signed Hetzner relay
settings; users import a network invitation and do not configure relay addresses.
The [website and delivery tooling](docs/PUBLIC_DELIVERY.md) live in this repository.

Current validation covers secure connections, authentication, transport security,
local IPC access controls, disconnect/reconnect behavior, and private file sharing.
Validation uses Linux and the existing Windows VM. macOS is unavailable;
installer and publication work is deferred.

[Private file sharing](docs/FILES.md) adds verified pieces, restart, multiple
authorized sources, explicit download acceptance and a bounded encrypted cache.

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
The signed preview requires Linux x86_64, Windows 11 x86_64, and macOS on
Apple Silicon and Intel. GitHub workers provide Mac qualification; mobile is deferred. See the
[release evidence procedure](docs/RELEASE_EVIDENCE.md).

The preview uses GComs' rustls/XML advisory fixes and disables unused postcard
heapless defaults. `deny.toml` records reviewed transitive-version exceptions and
two unmaintained build-time macros (OpenMLS/libcrux and ratatui). These require
follow-up upgrades; no runtime vulnerability is waived. The desktop dependency
graph has its own audit and native packaging requirements. See the exact
[dependency review and follow-up](docs/DEPENDENCIES.md).
