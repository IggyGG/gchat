# Gh0st preview signing

The owner selected **Gh0st** and self-signed distribution on 2026-09-20. Both
repositories record `signing_policy: self-signed-preview`. The desktop bundle
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
temporarily adds the pinned public certificate to that worker's current-user
root store, asks Windows to verify the Authenticode digest, and removes only its
own insertion in `finally`. It never installs a trust root on an end user's
machine. Native validation must verify rejection of a modified installer and
confirm that temporary trust is removed after successful and failed checks.

Self-signed preview timestamps are not required. Verification must therefore
also account for certificate expiry; these certificates are valid for two years.
macOS verification checks the code signature and certificate pin and records
notarization as absent. It must not report a passing Gatekeeper assessment.

Key creation and Linux detached-signature verification have been exercised
locally. Windows Authenticode, macOS signing, actual installer prompts, and
installation/upgrade tests require their native workers and remain release
requirements. Creating signers does not qualify or publish a desktop release.
