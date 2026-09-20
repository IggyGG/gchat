# Shared GComs Rust integration

GChat now consumes the paired GComs application facade and runtime. The file UI
maps conversations to GComs channel/member scopes; existing archive and encrypted
cache formats, cache paths and keys are preserved. Network trust remains owned by
GChat, and GC/2 selection remains explicit.

Linux validation completed on 2026-09-20: 137 Rust tests, strict Clippy, generated
contracts, 22 frontend tests and the packaged desktop consumer passed against the
paired GComs sources. Cache reconnect/corruption behavior is covered through both
GComs backends. Native macOS qualification of the Rust integrations is pending.

See the [GComs integration report](https://github.com/IggyGG/gcoms/blob/main/docs/RUST_INTEGRATIONS.md)
for exact inputs, sizes and native platform results.
