# Dependency review for 0.1.0 preview

Reviewed 2026-09-17 against the checked-in Rust lockfiles and a current RustSec
database. The core workspace uses `deny.toml`; the desktop workspace uses
`deny-desktop.toml`. Both deny known vulnerabilities, yanked dependencies, unknown
sources and unreviewed duplicate versions. These checks are a dependency review,
not an independent cryptographic or application security audit.

GComs upgraded rustls to at least 0.23.45 and quick-xml to at least 0.41.0. PEM
parsing now uses rustls-pki-types; unused postcard heapless defaults are disabled.
The exact lockfiles include those fixes.

Accepted unmaintained dependencies for this preview:

| Graph | Dependency | Scope and follow-up |
| --- | --- | --- |
| Both | proc-macro-error2 2.0.1 | Build macro through hax/OpenMLS/libcrux; upgrade with compatible upstream release |
| Terminal | paste 1.0.15 | ratatui 0.29 build macro; migrate with terminal UI qualification |
| Desktop | proc-macro-error 1.0.4 | Stable GTK3 build macros used by Tauri 2; revisit with the next stable platform upgrade |
| Desktop | Five unic-* 0.9.0 crates | Older Unicode tables via urlpattern 0.3 / tauri-utils 2.9.3; GChat grants no remote origin capabilities |

Each exception names the advisory in its policy and must be revisited before the
next preview. The source inventory gate rejects remote-origin capability grants
until the URLPattern dependency review is repeated. This is a scope constraint,
not a claim that an unmaintained dependency cannot cause problems. No runtime
vulnerability advisory is ignored. Upgrading to a development Tauri major solely
to remove advisory warnings would require separate native and bridge qualification.

Duplicate-version exceptions name exact versions and the upstream edges that
require separate APIs. Do not turn them into wildcard or whole-tree exceptions.
A newly resolved version needs review. The desktop graph and terminal graph are
checked separately because their native dependency trees differ.

Third-party license expressions pass policy checks. Before distributing native
installers, run `python3 scripts/collect-notices.py` after `npm ci`. It preserves
upstream notice files and writes a hashed inventory under `third-party/generated`,
which the bundle includes alongside project, font and trust-data notices. Review
`REVIEW.txt` for dependencies whose archives lack discoverable notice files. The
collector includes build tools conservatively; it does not certify compliance. Source/font/logo distribution rights
remain an owner release prerequisite.
