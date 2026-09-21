# Gh0st self-signed desktop distribution

The owner selected **Gh0st** and self-signed distribution on 2026-09-20. The
current production policy records `signing_policy: self-signed`; older preview
receipts retain their original `self-signed-preview` policy. The desktop bundle
publisher is Gh0st. This policy verifies signed bytes against pinned keys; it
does not assert public certificate-authority trust, Windows reputation, or Apple
notarization. Native installer acceptance must include the resulting OS prompts.

Public certificates and the OpenPGP verification key are in `release/signers/`.
Their fingerprints are pinned in `release/publication.json`. Release artifacts
must carry the signing policy and verification results in `build.json`.

`scripts/create-preview-signers.py --private-directory PATH` creates independent
encrypted Windows/macOS signing keys, PKCS#12 imports, a protected OpenPGP keyring,
and random passwords. PATH must be a new private directory outside Git. The
`--resume` option finishes interrupted setup while preserving existing keys.
Keep an encrypted offline backup before relying on these identities for upgrades;
do not rotate keys on every build. Only copy the `public/` contents into Git.

Protected workers need these inputs:

| Worker | Inputs |
| --- | --- |
| Linux | Dedicated `GNUPGHOME`, `GCHAT_RELEASE_KEY` fingerprint, protected `GCHAT_RELEASE_PASSPHRASE` |
| Windows | PKCS#12 imported into the worker's CurrentUser/My store, `WINDOWS_CERTIFICATE_THUMBPRINT`, `GCHAT_ISOLATED_SIGNING_WORKER=1` |
| macOS | Protected `APPLE_CERTIFICATE_BASE64`, `APPLE_CERTIFICATE_PASSWORD`, and `APPLE_SIGNING_IDENTITY` set to the pinned SHA-1 certificate fingerprint |

No Apple Developer account, team identifier, notarization API key, or public
Windows code-signing enrollment is used for this policy. A future trusted release
must explicitly select `publicly-trusted` and satisfy its enrollment, publisher,
timestamp, notarization and trust checks.

The Windows verification script runs only on an isolated signing worker. It
uses Windows' Authenticode digest/signature verification and an exclusive,
memory-only chain engine containing the pinned certificate. It checks the
signer's code-signing usage, current validity and exact identity. It never
changes a current-user or machine trust store. This also works on headless
workers where adding a root certificate would require an unavailable UI.
The native API contracts are
[WinVerifyTrust](https://learn.microsoft.com/en-us/windows/win32/api/wintrust/nf-wintrust-winverifytrust)
and [exclusive certificate chain trust](https://learn.microsoft.com/en-us/windows/win32/api/wincrypt/ns-wincrypt-cert_chain_engine_config).

Self-signed preview artifacts use untimestamped signatures. The preview verifier
rejects timestamped signatures instead of applying an unqualified timestamp
policy. Verification accounts for certificate expiry; the release certificates
are valid for two years.
macOS verification checks the code signature and certificate pin and records
notarization as absent. It must not report a passing Gatekeeper assessment.

Key creation and Linux detached-signature verification have been exercised
locally. Native Windows 10 verification of a test PE signed with the pinned Gh0st
certificate passed, including modified bytes, wrong pin, unsigned input and
unchanged trust stores. `scripts/test-windows-signature.ps1` additionally passed
with disposable test keys, including rejection after actual certificate expiry,
rejection of a preview as publicly trusted, and private-key cleanup. Native
Windows CI runs this regression automatically; it never needs release keys.
The first root-store-based implementation and the expired-before-signing test
fixture failed; their logs remain in `target/gc2-requalification`.

These are verifier checks, not installer acceptance. Windows 11/MSVC builds,
macOS signing, actual installer prompts, and installation/upgrade tests remain
release requirements. Creating signers does not qualify or publish a release.

## Installer dependency inputs

The installer builder exports the exact clean GChat and GComs commits into its
new output directory. It resolves Rust against that GComs snapshot and JavaScript
against npm archives built from the same snapshot. It checks dependency sources,
archive integrity, and the derived lockfiles before producing a successful build
report. The provenance/inputs.json report travels with the installer artifacts.
Original checkout manifests and lockfiles stay unchanged. Retain the local inputs
directory when diagnosing a failed build.

Before publication, run native GChat CI with
`python3 scripts/ci.py --gcoms ../gcoms`. This prepares the same source pair in
an isolated checkout and executes the complete CI entrypoint there. The derived
locks and source identities are retained under target/paired-ci. This qualifies
source integration; the separate published-registry consumer gate still applies.

Installer builds require `--native-ci-report PATH` naming the successful paired
`native-ci.json` for the same target. Preparing a second build may relocate its
checkout, but its source archives, dependency locks, resolved protocol graph and
npm archives must match those exercised by native CI. A changed dependency
resolution fails before signing. Both native workflows pass this receipt
explicitly; the macOS collector checks it against the retained CI evidence.
Provenance includes the derived locks, Cargo configuration and npm archives,
so ephemeral-worker artifacts retain the actual dependency inputs as well as
hashes. Native verifier fixtures do not satisfy this native-CI requirement.
