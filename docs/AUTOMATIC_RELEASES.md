# Automatic releases

A release is one immutable GChat/GComs source pair. A successful build, a submitted
store review and an available download are recorded as different states. No
platform can inherit a pass from a different pair. Apple review does not block
Linux, Windows, macOS, Android or the SDK lane.

## Production sequence

1. Land reviewed source in Forgejo `main` and retain the public GitHub mirror.
   The cluster controller watches their GitHub mirrors after the existing Forgejo
   source-mirroring workflow publishes them. The authoritative Forgejo is local
   to the workstation; it is not exposed to the cluster. It waits for source changes
   to settle, reserves monotonically increasing versions in SQLite, and creates
   immutable `release/gchat-*` refs. It never resets a working checkout.
2. Exact-source native workers run existing qualification, signing and installed
   lifecycle checks. Android uses emulators; Apple uses simulators and native
   macOS workers. Physical mobile devices remain deferred. SDK qualification
   runs the four desktop integrations and all client/relay/base/push mobile
   combinations. SDK archives are pinned releases, not hot updates to consumers.
3. Verify provider archive hashes, paired native provenance, publisher pins and
   the separately signed updater payload. Authentication, durable delivery,
   file integrity, recovery and state-compatible upgrades remain prerequisites.
4. `release_compatibility.py` consumes the fleet controller's recent, exact-pair
   application/rollback receipt and eight compatible relay observations from
   `/state/acceptance/<release_id>.json`. It **does not manufacture that receipt**
   from CI. Missing acceptance keeps publication waiting. Relay deployment uses
   its existing canary/serial process; the release controller does not guess
   topology, migrate profiles, or restart relays itself.
5. Desktop feeds and the GChat-only APT repository advance after verification.
   Public bytes are read back. Android commits one retained Play edit and polls
   the actual lifecycle API. iOS waits for the France-inclusive encryption
   declaration, uploads the already-built IPA on macOS, then attaches the exact
   processed build to a version and submits review. Store rejection or missing
   listing information remains an explicit blocked state.

There is no 24-hour campaign, physical-device requirement or statistical privacy
release gate. This does not claim traffic-analysis privacy qualification. The
remaining privacy work remains described in `PRODUCTION_RELEASE.md`.

## Desktop behavior

`/update` shows the running build, download progress and restart state. Downloaded
payload and metadata signatures bind version, source pair, platform, size and
hash. A signed older payload cannot be relabeled as a new version. Downloads are
bounded to 512 MiB. An unavailable update server leaves the installed app usable.

An update already staged at launch may activate before the window becomes
interactive. The startup check has a bounded wait. Updates discovered while a
window is open stage for the next launch. Restart now is disabled while there
are drafts or foreground actions; drafts in other conversations count too.
Other profile windows, active RPC admissions, checkpoint failures and an
unconfirmed service exit defer activation. Preparation uses the existing
owner-authenticated local IPC. It checkpoints before stopping, then verifies OS
process termination; a missing socket is insufficient. No passphrase enters the
updater. The saved profile remains and may need unlocking after a restart.

Debian installations are upgraded by a GChat-only systemd APT timer, without
restarting running clients. `scripts/install-local-updates.py` first verifies the
public signed repository, then installs the source, pinned key and timer when
run as root with `--apply`. AppImage/macOS/Windows use signed Tauri updates.
Mobile stores own mobile installation and their automatic-update preferences.

## Controller deployment and secrets

`release/automation/Dockerfile`, `kubernetes.yaml`, `nginx.conf` and
`scripts/release_config.py` describe the controller and public download service.
The controller has one replica, a persistent SQLite WAL and immutable job inputs.
Only `/state/public` is served. Provider responses and credentials remain private.
Mount the existing publisher keys at `/keys`; never commit them. GitHub credentials are supplied through the protected environment. The
controller does not need workstation access or a Forgejo credential. Updater keys
are shared only with signing workers and the metadata signer. Signing workers
must use the configured release environment and protected candidate refs.

The image needs Python dependencies, GitHub CLI, GnuPG, minisign, Java/apksigner
and the pinned Tauri CLI. The cluster has a minimum-free-space admission check;
export retained artifacts before removing old data. Do not remove active job
state, provider journals or the release database. Back up SQLite using its backup
API (or a consistent stopped-volume snapshot), including source manifests and
provider journals. The daily maintenance task verifies and refreshes the signed APT index when
fewer than seven of its fourteen valid days remain, even without a new release.
It retains seven consistent daily SQLite backups; cluster volume backups must
also retain the immutable job evidence and provider journals.

After an interrupted external action, the request ID is reconciled with the
provider. Unknown uploads/commits are never blindly repeated. A blocked target
resumes its previous stage with `release_coordinator.py --resume RELEASE TARGET`;
it cannot skip verification. New source changes supersede only unstarted work.
The public status document distinguishes building, verification, publication,
processing, review, blocked and available.

Initial deployment is not complete merely because these files or tests exist.
Retain a concrete deployment receipt, a first qualified release, a real installed
upgrade/reopen result and provider observations before claiming it operational.

Provider references: [Google release lifecycle API](https://developers.google.com/android-publisher/api-ref/rest/v3/applications.tracks.releases),
[Apple version metadata](https://developer.apple.com/help/app-store-connect/update-your-app/create-a-new-version),
[Apple encryption states](https://developer.apple.com/documentation/appstoreconnectapi/appencryptiondeclarationstate).
