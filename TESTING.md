# Validation

Current release work covers GComs/GChat source, signed installers, and GChat's
website/onboarding. Validate secure connections on Linux, the native MSVC Windows
VM, and GitHub-hosted macOS Apple Silicon/Intel runners. The local Mac remains
unavailable. Historical results below do not qualify these new release inputs.

Use Rust 1.98, Node 22, npm 11 and the platform's Tauri v2 prerequisites.
After GComs packages have been published:

```sh
cargo fmt --all -- --check
cargo test --workspace --all-features --locked -- --test-threads=1
cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
npm ci --ignore-scripts
npm run types
npm run generate:rpc -w @gchat/ui
npm run check
npm test
npm run build
cargo check --manifest-path apps/client/src-tauri/Cargo.toml --locked
python3 scripts/check-source.py
```

Before publication, qualify against GComs' extracted package staging using its
`check-consumers.py --gchat /path/to/gchat`. An external Cargo patch file can select
those extracted packages without adding sibling paths to public manifests.

For current-source development, run GComs' `scripts/check-gchat.py --gchat
/path/to/gchat --offline` from the separated GComs repository. Its default action
runs this Rust workspace's all-feature tests; `--action check` and `--action
clippy` provide build/lint variants. It snapshots both repositories, leaving both checked-in
Cargo.lock files and registry dependency manifests intact. Read its retained
summary before treating the two-source integration as qualified.

The Rust suite covers chat history, encrypted archive continuity, instance-bound
RPC, durable submission/recovery, runtime shutdown and refusal of retained component
ownership before personal archive or IPC startup. UI tests exercise service errors,
attachment binding and pending-operation recovery. Run both after changing a shared
contract. A generated schema must agree with Rust and its checked-in TypeScript.

The desktop is a separate Cargo workspace. Build installers with Tauri on native
Linux x86_64, Windows 11 x86_64 and both macOS architecture runners. On every target, qualify
fresh install, invite/unlock, two-peer messaging, disconnect/reconnect, restart,
upgrade with retained identity/archive and uninstall without deleting user data.
Public installers require the configured distribution signatures. The two
GitHub-hosted Mac architectures must pass the same native and installer gates;
the unavailable local Mac is not used.

The release manifest must record hashes, signatures, toolchain and exact source
commits. Mobile builds and production security/privacy claims are deferred.
See docs/RELEASE.md for launch blockers and docs/NETWORK.md for operator acceptance.

## Forgejo runners

`.forgejo/workflows/check.yml` uses a pinned checkout action and the two named
native runner labels. Provision disposable runners with Rust 1.98, Node 22, npm 11,
Python 3.11+, the native build dependencies and cargo-deny. Untrusted pull requests
receive no signing/registry secrets and must not execute on a developer workstation.
Public GChat CI starts after its GComs registry dependencies are available; local
pre-publication checks use the documented extracted-package staging.

Run `cargo deny check` for the application workspace and separately with
`cargo deny --manifest-path apps/client/src-tauri/Cargo.toml --config deny-desktop.toml check`
for the desktop graph. Review each advisory against the pinned versions; keep
unmaintained macro exceptions distinct from runtime vulnerability fixes.

For pre-publication lockfile verification, GComs' `check-registry-consumer.py`
serves inspected package archives through a loopback registry and checks `--locked`
with canonical crates.io checksums. Run it for both this workspace and the separate
Tauri manifest. Path-patched development commands can rewrite these lock entries;
repeat registry verification before committing release lockfiles.

## Private Windows VM checks

The current manual test host is the isolated `gcoms-gchat-validation` x86_64 VM
(Windows 10 build 19045). Its restricted network exposes SSH only on the Linux
host's loopback interface. Windows GNU test executables are cross-built with Rust
1.98 on Linux, then executed inside Windows with their source fixtures and runtime
DLLs. Each harness retains its exit code and logs; timeouts and harnesses with no
Windows cases must be reported separately.

This checks Windows runtime behavior, including named pipes and file permissions.
It does not establish MSVC compilation, native compiler UI tests, desktop installer
behavior, signing or a configured Forgejo runner. Those require the corresponding
Windows build dependencies and separate acceptance evidence when release work
resumes. Public release preparation is active; required evidence must still be completed.

The [2026-09-17 runtime record](release/native-validation-2026-09-17.json) contains
584 passing GComs Windows cases (five ignored) and 121 passing GChat Windows cases.
GComs' offline-member backlog harness exceeded the 15-minute VM budget; a separate
90-second diagnostic reached offline sending after successful admission and member
shutdown. That historical failure is superseded by the bounded-dial fix below. Unix-only harnesses with
zero Windows cases and the native compiler/installer gaps above are excluded from
these counts. Linux has 598 GComs and 142 GChat passing cases, with the final
transcript fix additionally retested across all core-library cases on both OSes.

## Current qualification follow-up

The offline-member backlog test now passes unchanged on Linux and in the Windows
GNU VM (16.24 seconds). GComs bounds repeated pre-TLS refused/unreachable dials with
a five-second, 64-route cooldown and cancels scheduler waits during shutdown.
TLS, HTTP and ambiguous application outcomes are not automatically retried by this
cache. GC/1, IPC v16 and retained-state formats stay unchanged.

The 2026-09-18 Linux workspace runs have 606 passing GComs cases (five explicit
ignored cases) and 143 passing GChat cases. Strict Clippy passes for both workspaces.
The Windows GNU VM passes 16 focused cases covering the chat service, immediate
profile reopening, daemon/archive continuity, in-flight-save cancellation and the
standalone daemon. The empty Windows `gchat-api` harness is excluded from that count.
Broader Windows routing and native MSVC qualification remain unfinished; earlier
full-run failures are retained, including concurrent-admission responsiveness.

GChat now joins its persistence and event-forwarding tasks during shutdown. GComs
joins subscription, invitation and command workers; parallel maintenance futures
are owned by their caller so cancellation releases their state before returning.
The reconnect test opens the encrypted profile immediately, without a delay or
weakening its exclusive lock. A regression holds a save in flight and verifies
shutdown cancels it before releasing the profile. Windows profile migration now
uses a writable handle when flushing the preserved encrypted bytes to disk.

GChat's portable service, archive-reopen and standalone-daemon suites now run on
Windows too. Their readiness probes use IPC connections, since named pipes have
no socket-file entry. Unix PTY tests remain platform-specific.

## Protocol persistence

See [the persistence audit](docs/PERSISTENCE.md) for event ownership and local
write counters. The runtime regression verifies one completed encrypted profile
replacement per event for 0, 1 and 4 SDK subscribers. It also tests publication
ordering, an actual failed replacement, subscriber closure under backpressure,
lag notification and reopening after recovery. Existing shutdown and archive/file
continuity tests remain required. Run the paired all-feature Rust tests and strict
Clippy using GComs `scripts/check-gchat.py`; retain both source hashes.
