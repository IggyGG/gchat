# Forgejo authority and public delivery

Local Forgejo remains authoritative for both repositories. GitHub hosts
`IggyGG/gchat` and `IggyGG/gcoms` as public mirrors. GChat contains the static
website and all deployment scripts. GitHub Actions runs the two macOS release
workers; Forgejo owns publication and deployment. Public contributions are
reviewed and integrated in Forgejo before mirroring back to GitHub.

## Runner setup

The existing Linux runner and a Windows 11 VM with native MSVC use the labels
`gcoms-linux-x64` and `gcoms-windows-x64`. Install the pinned Rust toolchain,
Node 22, npm 11, Python, native Tauri prerequisites, `gh`, and Gitleaks on release
runners. The website deployment runner additionally needs `kubectl`, an authenticated
cluster connection, and `gpg` to verify published downloads.
Register runners only against the relevant GChat/GComs repositories.

Before using GitHub, create the two public mirrors with the audited source:

```sh
python3 scripts/github-mirror.py --create
```

Run this from each repository after committing and validating its changes.
The command scans reachable main history with Gitleaks, checks the source
inventory, and pushes explicit refs without force. Existing divergent GitHub
history is an error. Future source mirroring uses `ENABLE_PUBLIC_MIRROR=true`
and a protected `GITHUB_MIRROR_TOKEN` with contents/workflows access limited to
these two repositories. Mirroring a version tag also verifies its signature.
Install Gitleaks 8.30.1 or a reviewed newer version. `.gitleaksignore` records only
three reviewed historical false positives across the pair: the `libcrux-secrets`
dependency name followed by `libcrux-sha3` in Cargo lockfiles. New findings still
block publication; do not exclude entire lockfiles.
GitHub private vulnerability reporting is enabled by the mirror setup command.

## Signing enrollment

Account enrollment and identity validation are owner steps; a GitHub account or
an Apple Development certificate is not a distribution certificate.

- Apple: enroll in the Apple Developer Program, create a **Developer ID
  Application** certificate, export its certificate/private key as an encrypted
  P12, and create an App Store Connect API key for notarization. Configure the
  GChat GitHub environment `release-signing` with `APPLE_CERTIFICATE_BASE64`,
  `APPLE_CERTIFICATE_PASSWORD`, `APPLE_SIGNING_IDENTITY`, `APPLE_API_KEY_BASE64`,
  `APPLE_API_KEY` (key ID), and `APPLE_API_ISSUER`; set the public `APPLE_TEAM_ID`
  variable to the expected ten-character team ID. Restrict it to protected main.
  A temporary keychain is created and removed for each build. The local Mac is
  not used.
- Windows: obtain a publicly trusted Authenticode certificate from a CA that
  supports the publisher's legal identity. Provision its hardware-backed key or
  provider into the Windows VM's certificate store. Set
  `WINDOWS_CERTIFICATE_THUMBPRINT` and an HTTPS RFC3161 `WINDOWS_TIMESTAMP_URL`.
  Tauri uses SignTool with SHA-256; qualification verifies the expected signer
  and timestamp. Do not substitute a self-signed certificate.
- Linux: create a dedicated OpenPGP release key with an offline backup, then put
  only the signing subkey in the protected Linux runner's `GNUPGHOME`. Set
  `GCHAT_RELEASE_KEY` to its full fingerprint and `GCHAT_RELEASE_PASSPHRASE` as a
  secret. Publish the public key and fingerprint with releases. This key is
  separate from the network-defaults signing root.

Record actual signer names and certificate/key fingerprints in
`release/publication.json`. Private security and conduct reports use
`iggy@gchat.boo`; GitHub private vulnerability reporting is also enabled for both
public repositories. Retain the required rights/operator reviews. Unconfigured
fields remain explicit release blockers; scripts never invent identities or passing evidence.

## Build and qualify

Publish the inspected GComs Rust and npm packages in dependency order, then
verify registry consumers and review the resulting lockfiles. Package names and
versions are immutable: a changed archive requires a new version or a new
unpublished candidate, never replacing published bytes.

Freeze clean GChat/GComs source commits with `release-candidate.py init`. The
`signed-builds.yml` Forgejo workflow builds Linux and Windows and dispatches the
GitHub Mac workflow. Both public mirror main refs must contain the frozen source;
the GChat workflow must execute from the exact frozen GChat commit. GitHub workers
use `macos-15` and `macos-15-intel`, configure disposable test-only loopback aliases,
run both native CI suites, and sign/notarize each DMG. Forgejo retrieves the exact
run and checks both source commits and artifact hashes.

Build output is a fresh directory containing installers and `build.json`. Native
evidence is retained for every platform. Record these artifacts, native reports, installer
scenarios, and signature-verification evidence in the candidate using the existing
release-evidence tools. A build report alone is not installer qualification.
Complete every required check in `RELEASE_EVIDENCE.md`, including clean install,
retained-profile upgrades, real invitation onboarding, and recovery.

Use `scripts/sign-release.py --candidate PATH --gchat PATH --gcoms PATH` on the
protected Linux runner after recording the final artifacts. It adds a public key,
a source-bound artifact manifest for each project, and detached signatures for all
assets using the recorded primary key fingerprint. It verifies signatures and
retains matching existing signatures on retries. Native signatures remain required.
Record manifest signing evidence and verify `check-release.py --stage preflight`
before publication. Signed Git tags must use this same primary release key.

## Publish identical releases

Push signed version tags to Forgejo and mirror them with
`github-mirror.py --tag vVERSION`. Prepare release notes as a file. On the
protected Forgejo runner, configure `FORGEJO_TOKEN`, `FORGEJO_API_URL` (default:
workstation loopback API), and `GH_TOKEN` with release access to the two mirrors.

```sh
python3 scripts/publish-release.py --candidate /evidence/rc/candidate.json \
  --gchat /checkouts/gchat --gcoms /checkouts/gcoms --notes /evidence/notes.md \
  --output /evidence/downloads.json --dry-run
```

Run without `--dry-run` after all checks pass. The command publishes the retained
artifacts to Forgejo first, copies them into GitHub releases, refuses to replace
existing different bytes, and verifies public downloads before producing website
metadata. Retrying a partial upload preserves completed matching assets. Keep all
failed attempts and update the existing published-stage evidence afterwards.

Review and commit the produced `release/downloads.json` to GChat so future website
deployments retain the released version. Code changes after freezing need a new
candidate; a website-only metadata update does not rebuild the already released
artifacts or rewrite their source bindings.

## Website deployment

`website/IMPORT.json` records the live site's import. The build copies the existing
licensed application font. It uses static HTML and makes no background GitHub API
requests in visitors' browsers.

```sh
python3 scripts/website.py
python3 -m http.server 8080 --directory dist/website
```

The existing site is in Kubernetes: namespace `ghost-com`, Deployment/Service/
Ingress `gchat-site`. Nginx serves `/usr/share/nginx/html` from the `content`
ConfigMap volume. The ingress handles `gchat.boo` and `www.gchat.boo`; the latter
redirects to the canonical domain. TLS remains in the existing `gchat-site-tls`
Secret. The deployer does not read or change that Secret, the ingress, service,
Nginx configuration, container image, or relay settings.

Deployment defaults to that namespace and workload. Override with
`GCHAT_WEB_NAMESPACE`, `GCHAT_WEB_DEPLOYMENT`, and `GCHAT_KUBE_CONTEXT` when needed.
Configure `GCHAT_WEB_KUBECONFIG` in Forgejo as the **path** to a protected kubeconfig
already mounted on the deployment runner, not its contents. With no path/context
override, kubectl uses its normal configuration. Never commit kubeconfig files or
copy the workstation's cluster-admin credentials into CI. A dedicated deployment
identity needs `get` and `patch` on the named Deployment and `get`/`create` on
ConfigMaps in this namespace; it needs no Secret access. Kubernetes RBAC cannot
restrict `create` by resource name, so namespace-level ConfigMap creation is the
remaining permission boundary.

```sh
python3 scripts/website.py --check-remote
python3 scripts/deploy-website.py --dry-run
# After committing the validated changes:
python3 scripts/deploy-website.py
```

The dry run validates creation and the guarded Deployment patch with the API
server without changing cluster state. Each six-file bundle (including the
existing `robots.txt` and font license) gets an immutable ConfigMap named with
the source commit and content hash. Only the content volume is changed, allowing
the existing two-replica rolling update to serve traffic throughout. Once every
replica is ready, the deployer verifies all six public file hashes over HTTPS.
It retains the prior Deployment/content snapshot and the successful verification
report in ignored `test-evidence/website-deploy/`.

Failed rollout or public verification restores the previous content volume,
unless another operator has since changed the pod template. Generation/UID tests
prevent overwriting concurrent work. Prior ConfigMaps are retained; subsequent
versions can be restored and verified with
`python3 scripts/deploy-website.py --rollback PREVIOUS_CONFIGMAP`. The original
unversioned `gchat-site` ConfigMap remains available alongside the first migration's
backup. Set `ENABLE_WEBSITE_DEPLOY=true` in Forgejo once its runner has this
restricted cluster access and a successful dry run. The existing mirror gate
must also be enabled for the dependent website job to run.

See Kubernetes' [ConfigMap documentation](https://kubernetes.io/docs/concepts/configuration/configmap/)
and [RBAC reference](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
for immutable objects and the limits on restricting creation permissions.
