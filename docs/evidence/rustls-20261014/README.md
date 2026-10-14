# Rustls dependency correction — 2026-10-14

The original Linux0.1.222 run38570960220 (attempt1) failed both GChat and GComs
native gates at `cargo deny check`. The recorded advisories are
RUSTSEC-2026-0346,0347,0348 and0349 against Rustls0.23.45; all require >=0.23.46.
The earlier failing nested unittest output is an intentional fixture and is not
the cause of these native failures. Original failures and clocks remain intact.

The source pair now requires Rustls0.23.46 and retains its registry checksum
`48e13bd8c0e9365c43cfa5c9e8f9ad49d3c8444926c9aac819e0e4dc503c8fdf` in all six
affected locks: GChat workspace, desktop and released consumer; GComs workspace,
Rust example and mobile native consumer. Cargo generated the GComs update. The
identical version/checksum-only stanza is applied to the GChat locks because its
unpublished GComs dependencies require the normal isolated paired-source resolver.
That resolver independently checked all three graphs. The SDK fuzz graph contains
no Rustls and its unchanged lock passes. No advisory exclusions were added.

Focused qualification on immutable source snapshots took312.159s:

- GComs and both GChat dependency audits passed with `--locked`.
- All three GComs independent consumer locks passed `cargo tree --locked`.
- All three GChat paired metadata graphs resolve Rustls0.23.46.
- GComs transport suite:72passed,4existing ignored long-running cases.
- GChat host-registration suite:8passed,0ignored.
- Both canonical source trees and locks remained unchanged during qualification.

Retained evidence root: `rustls-pair-1791990276` in the private durable-host evidence
directory. Input manifest SHA256:
`fe745d7f27fc0a176078b959c3ad6cb5932c594a7c7c133c82850217d0a28a20`.
Result SHA256:
`ef044421117b6df5a95c9f4b0ecf90926fa1bfaeaf4a6211b7c3a924ba7b385f`.
Source baselines are GChat`ead81db` and GComs`712d671`; the input manifest binds
every changed manifest/lock byte. This is dependency/source qualification, not
a new signed or installed release. Normal paired native CI, relay load,
signing, installed acceptance and publication must qualify the successor.

The original219 artifact was recovered with its exact SHA256, provider run and
budget preserved. It is retained as a historical successful native artifact;
its earlier dependency audit does not cover the newly issued advisories.
