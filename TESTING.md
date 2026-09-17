# Validation

Current work stays in the existing private local Forgejo repositories. Public
publication is deferred by the owner. Run the build/test and local package-consumer
checks below; `check-release.py` applies only when a public release is reconsidered.
Native development uses the tunneled Mac's `iggy` account and a Windows x86_64 VM.
Their availability does not imply completed native or installer qualification.

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
Linux x86_64, macOS x86_64/aarch64 and Windows x86_64 runners. On every target, qualify
fresh install, invite/unlock, two-peer messaging, disconnect/reconnect, restart,
upgrade with retained identity/archive and uninstall without deleting user data.
Sign Windows installers with the approved publisher identity and sign/notarize
macOS artifacts. Never remove quarantine to make an unsigned build appear released.

The release manifest must record hashes, signatures, toolchain and exact source
commits. Mobile builds and production security/privacy claims are deferred.
See docs/RELEASE.md for launch blockers and docs/NETWORK.md for operator acceptance.

## Forgejo runners

`.forgejo/workflows/check.yml` uses a pinned checkout action and the four named
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
resumes. Public publication remains deferred.

The [2026-09-17 runtime record](release/native-validation-2026-09-17.json) contains
584 passing GComs Windows cases (five ignored) and 121 passing GChat Windows cases.
GComs' offline-member backlog harness exceeded the 15-minute VM budget; a separate
90-second diagnostic reached offline sending after successful admission and member
shutdown. It remains an open Windows qualification issue. Unix-only harnesses with
zero Windows cases and the native compiler/installer gaps above are excluded from
these counts. Linux has 598 GComs and 142 GChat passing cases, with the final
transcript fix additionally retested across all core-library cases on both OSes.
