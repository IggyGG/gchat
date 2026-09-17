# Validation

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
