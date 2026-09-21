# Independently qualified application downloads

Use `scripts/publish-platform-release.py` for a completed Mac, Windows or Android
application build. The existing paired SDK/application publisher is unchanged.
Each bundle has its own immutable signed tag, such as
`v0.1.4-macos-aarch64.1`. It names the app's version and its actual paired sources;
it does not reclassify another platform's receipt or republish SDK packages.
Linux downloads remain attached to their existing release and original bytes.

The local candidate is schema `1`, kind `platform-release`. It contains:

- `version`, `tag`, one `target`, `channel: "production"`,
  `release_policy: "production-minutes-v1"`, `privacy_qualified: false`, and a
  nonempty `unqualified_scopes` list describing the actual remaining work.
- `sources.gchat` and `sources.gcoms`: exact `commit`, `tree` and hash-bound local
  source `archive` references. References use relative `path` and `sha256` fields.
- `signer`: `name` and `certificate_sha256` matching the GChat source commit's
  frozen publication policy. This is separate from the detached release key.
- `release_key`: a local public-key reference, full primary `fingerprint`, and a
  `signature` reference. It must match the frozen Gh0st release key.
- `artifacts`: one installer filename mapped to its local reference, `size`,
  `target`, `format` (`dmg`, `nsis` or `apk`), and detached `signature` reference.
- `checks.build`, `checks.smoke`, `checks.signing`: hash-bound qualification
  attestations. Preserve the original runner reports/logs; do not edit them.

Each check is schema `1`, `scope: "platform.<role>"`, `passed: true`,
`source_unchanged: true`, exact `sources` commit/tree bindings, `target`, and
`artifacts` filename-to-SHA256 mapping. Include `qualified_scopes` naming only
what actually ran and nonempty `evidence` references to the original checked
reports/logs. The smoke attestation requires `cleanup_complete: true`; signing
requires the same exact `signer`. These are reviewable runner attestations,
not independent proof that arbitrary supplied logs were executed. The release
owner must first use the platform-specific download/verification tooling on the
actual native run. Never turn a compile or startup smoke into messaging, device,
push, installed recovery, or full native CI qualification.

1. Verify the original platform run and assemble these bindings. Make detached
   signatures with the protected Gh0st release key; never put private keys or
   passphrases in arguments, source, candidate JSON or public evidence.
2. Run `publish-platform-release.py manifest --candidate CANDIDATE --gchat GCHAT
   --gcoms GCOMS --output CANDIDATE_DIR/platform-release.json`. It generates a
   public manifest containing hashes and scopes, without private worker paths.
   Sign it as `platform-release.json.asc` with the same pinned key.
3. Create and push the exact signed platform tag to Forgejo and GitHub. Both
   source commits must be present in their public mirrors. Run the `check`
   action with the same arguments and an output receipt path.
4. Only when publication is authorized, run `publish` with `--notes RELEASE.md`.
   It stages on draft releases, verifies every uploaded byte, and then publishes.
   An existing published release is a closed asset set; different bytes or any
   added asset are refused. A retry may verify an identical completed bundle.

The website accepts its existing schema 1 unchanged. Schema 2 uses `version:
null`, `channel: "production"`, `publisher_fingerprint`, a `releases` object
keyed by immutable tag, and `artifacts` with an added `release` tag reference.
Each release has its own `version`, exact source commit pair, `release_key`, and
signed `manifest` URL/checksums, with `manifest_format: "platform-v1"`.
Use `legacy-v1` only for the existing signed Linux `release-manifest.json`.
Every artifact and signature must use its own release's GitHub asset origin.
`website.py --check-remote` verifies the manifests, source/artifact bindings,
checksums and detached signatures before generating links. Display versions per
platform rather than implying all downloads came from one source pair.

iOS delivery remains App Store Connect/TestFlight. A signed IPA or upload receipt
does not by itself establish Apple processing, tester availability or an App
Store release; this tool does not publish an IPA as a general download.
