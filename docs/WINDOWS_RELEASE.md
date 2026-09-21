# Native Windows release worker

The Windows worker builds the existing desktop application and SDK consumer on
Windows Server 2022 x64 with the repository's pinned Rust MSVC toolchain, Python
3.12.10, Node 22.23.2 and npm 11.6.2. It runs both native CI entrypoints before
building a signed current-user NSIS installer. The native runner supplies Visual
Studio C++ tools, the Windows SDK and NSIS. A missing WebView2 runtime is installed
using Microsoft's HTTPS bootstrapper after verifying its trusted Microsoft
Authenticode signature. The installer test itself performs no runtime download.

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
