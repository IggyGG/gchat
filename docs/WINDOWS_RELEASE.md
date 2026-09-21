# Native Windows release worker

The Windows worker builds the existing desktop application and SDK consumer on
Windows Server 2022 x64 with the repository's pinned Rust MSVC toolchain, Python
3.12.10, Node 22.23.2 and npm 11.6.2. It runs both native CI entrypoints before
building a signed current-user NSIS installer. The native runner supplies Visual
Studio C++ tools, the Windows SDK and NSIS. A missing WebView2 runtime is installed
using Microsoft's HTTPS bootstrapper after verifying its trusted Microsoft
Authenticode signature. The installer test itself performs no runtime download.

Both Windows MSVC launchers reserve 8 MiB for the main thread, with pages
committed on demand. The default 1 MiB reserve caused a native stack overflow
during retained-profile daemon startup in unoptimized builds. The existing
standalone daemon readiness/reopen test runs before full CI and retains the
child's exit status and stderr; the installer still exercises the packaged
desktop service separately. Worker-thread stack sizes and protocol limits are
unchanged.

The protected GitHub environment `release-signing` needs these secrets:

| Secret | Contents |
| --- | --- |
| `WINDOWS_CERTIFICATE_BASE64` | Base64 PKCS#12 containing only the existing pinned Gh0st leaf and its private key |
| `WINDOWS_CERTIFICATE_PASSWORD` | Password for that PKCS#12 |

The certificate must match both Windows fingerprints in
`release/publication.json`. This workflow does not create or rotate a signing
identity. The PFX is inspected ephemerally, imported into `CurrentUser/My` on the
isolated worker, then deleted from disk. An unconditional cleanup step removes
the imported certificate and private key and verifies the original user store
and persistent Root/TrustedPublisher stores. No certificate is added to a trust
store. The environment must allow only the approved release branches or version
tags; the worker verifies its workflow SHA, checkout SHA and selected ref before
using protected secrets.

Before native compilation the worker exercises import/refusal/cleanup with a
disposable PFX, then imports and removes the actual pinned signer once. A wrong
password, wrong pin or unsupported PFX therefore stops before the expensive
build. `X509Certificate2Collection.Import` receives its required string password;
`Import-PfxCertificate` separately receives a `SecureString`. No private key
remains installed during compilation. The final signing import and cleanup
retain their separate receipts and remain required for release acceptance.

Dispatch from an approved frozen release pair after mirroring those exact
commits. The GChat ref must name the exact workflow commit. The GComs commit must
belong to its selected branch, or exactly match its selected version tag.

```sh
python scripts/windows-build.py \
  --gchat-ref release/gchat-0.1.4 --gchat-commit FULL_GCHAT_SHA \
  --gcoms-ref release/gchat-0.1.4 --gcoms-commit FULL_GCOMS_SHA \
  --output target/windows-release-0.1.4
```

Both native workspaces, their frozen source archives, paired dependency inputs,
native qualification, signing policy and final executable are bound in the
retained reports. The worker installs the actual signed NSIS into a new private
directory, verifies the installed executable and signed uninstaller, and runs
fresh-profile/unlock/shutdown/reopen checks through the application's authenticated
local service. It then uninstalls and verifies removal of the owned process,
installation, registration and metadata. Existing GChat profiles, processes or
registrations cause refusal; they are never taken over. All failure receipts and
signing cleanup reports remain in the job artifact.

The collector requires the exact native, artifact, service and cleanup evidence.
It also verifies the raw before/after persistent certificate-store snapshots.
Successful evidence is specifically **Windows Server 2022 native MSVC and NSIS
service lifecycle**. It does not qualify Windows 11 graphical interaction,
SmartScreen reputation, real network onboarding, messaging/file delivery or
mobile behavior. The pinned self-signed signature establishes the configured
publisher identity; it is not a claim of public CA trust. Native results require
an actual completed Windows worker; local Python fixture passes alone are not a
Windows release receipt.

## Packaging-only recovery

`windows-package.yml` keeps its packaging controller separate from the exact
application source pair in `release/windows-package-recovery.json`. It verifies
the original GitHub artifact digest, both unchanged successful native reports,
their logs, source archives and dependency identity before reusing them. It then
builds only NSIS, verifies the executable extracted from that signed installer,
and runs the existing install/reopen/uninstall and signer-cleanup checks. Tauri
restores the unsigned build-directory executable after bundling; that temporary
copy is not the shipped executable and must not supply its signature or hash.

Windows20's original upload omitted the generated hidden `.cargo/config.toml`.
Recovery reproduces only that file from the frozen manifests and original
hash-bound native-log checkout path, requires its exact recorded SHA256, and
labels the reconstruction separately. The original ZIP and native receipts stay
unchanged. Subsequent uploads explicitly include hidden provenance. Actual build
executables/installers are retained even if verification fails; their presence
does not qualify them. Controller provenance never replaces application-native
provenance or converts the original failed workflow into a passing release.
