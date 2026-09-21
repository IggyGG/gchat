# Android application build and qualification

The Android app uses the shared GChat UI and the outbound GComs `NetworkClient`
backend. Its package is `boo.gchat.app`, minimum Android API 26. ARM64 device and
x86_64 emulator APKs are built from the same frozen GChat/GComs sources. Mobile
relay hosting is not enabled. Compiled IPC contract helpers are permitted because
GChat's shared API uses them; the app does not start a desktop IPC host.

`scripts/android-build.py` and `.github/workflows/android-release.yml` provide the
build path. A committed workflow is not a completed platform qualification. No
Android pass is claimed until the real build, pinned signing and emulator steps
produce their receipts. ARM64 compilation does not establish physical-device
behavior. Live push, battery, lock-screen and physical-device results remain open.

## Published 0.1.4 APKs

The [ARM64](https://github.com/IggyGG/gchat/releases/tag/v0.1.4-android-arm64.1)
and [x86_64](https://github.com/IggyGG/gchat/releases/tag/v0.1.4-android-x86_64.1)
APKs are published with pinned Gh0st signatures and independent signed manifests.
Run `35616288196` built GChat `ab3697a8bb98962f7a765254a6c5d2b6c8b6259e`
with GComs `398c751474dda2a361eca0cf0e28308c192c68fa`; both native packages,
16 KiB alignment and signatures passed. The actual x86_64 API35 app passed
profile creation, background locking, explicit reopening, retained process restart,
and Android DocumentsUI cancellation/selected-invitation continuation. Cleanup
passed. ARM64 execution on a physical phone remains deferred; these receipts do
not establish remote messaging/files, FCM, live onboarding or full mobile CI.
The manifests and release notes retain those distinctions.

## Exact inputs and tools

- The same pinned Rust version in both repositories' `rust-toolchain.toml`.
- Node 22.23.2, npm 11.6.2 and Python 3.12.10.
- Java 17, Android platform/build-tools 36 / 36.0.0.
- NDK `28.2.13676358`, Rust `aarch64-linux-android` and `x86_64-linux-android`.
- For the automated smoke: a fresh, disposable, root-capable x86_64 API 35 Google
  APIs emulator, Linux KVM and the Android SDK emulator/platform-tools packages.

The worker first checks the protected workflow ref and both full commit IDs. It
uses existing paired-source preparation: immutable Git archives, local GComs Rust
patches, built npm archives, derived locks and source provenance. Originals must
stay clean and unchanged. Tauri generates its Android project only in those
retained build inputs. Invoke the installed local Tauri CLI through the package
script (`npm run tauri -- ...`) so Gradle's generated Rust callback retains a
working launcher when its cwd is `src-tauri`. A direct Node/script launch can
become an invalid `node tauri` callback. The CLI's `android init --ci
--skip-targets-install` and `android build --ci --apk --split-per-abi --target
aarch64 x86_64` commands are used without invented build flags.

For each target, the normal dependency graph must select `network-client`, include
the actual GComs runtime and omit `embedded`, `launch` and node `relay-host`.
Dev-dependency feature unification is not used as the shipping graph. Dependency
notices are generated from both resolved Android metadata graphs after npm setup
and before Tauri packages its resource directory. APK inspection
requires the exact package/minimum SDK, one expected ABI per APK and actual
`libgchat_native.so`. Every native library must have 16 KiB-compatible ELF load
segments; Android `zipalign -c -P 16` additionally checks ZIP alignment.

## Signing inputs

The protected `release-signing` environment supplies:

- `ANDROID_KEYSTORE_BASE64`
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_PASSWORD`
- `ANDROID_KEY_ALIAS`

Repository variable `ANDROID_SIGNING_CERT_SHA256` must equal the Android publisher
certificate hash in the frozen `release/publication.json`. Signing uses Android
`apksigner`, requires the single pinned certificate and a valid v2 signature, and
rechecks unchanged native-library contents. A private temporary keystore is removed
on success and failure. No password is put on the command line or retained in a
report. Signed APKs are kept with their unsigned build and signature provenance.
The script signs existing exact APKs; it never creates a replacement publisher.

Optional `GOOGLE_SERVICES_JSON_BASE64` contains only Firebase **client** app
configuration matching `boo.gchat.app`. The runner rejects service-account keys.
It retains the config hash and places the client JSON in generated Android inputs;
It also generates the four documented Firebase Android resource values for the
mobile messaging plugin. No analytics SDK is added; packaging these resources
does not prove FCM delivery. No server credential belongs
in an APK, a Git commit, or this workflow.

## Commands

On a correctly prepared build worker, with clean exact source trees:

```sh
python3 gchat/scripts/android-build.py build --gchat gchat --gcoms gcoms --output android-output
python3 gchat/scripts/android-build.py sign --output android-output
python3 gchat/scripts/android-build.py emulator --output android-output
```

Output must be fresh. Build and signing write `build.json` and `signing.json`;
the emulator writes `emulator-smoke/report.json`, including cleanup on failure.
The workflow uploads those reports, APKs, normal feature graphs and paired-source
provenance. It does not publish or dispatch another workflow.

The smoke refuses a physical device or an emulator with a pre-existing GChat app.
Before launch it blocks only the installed app UID's non-loopback IPv4/IPv6 egress
inside that disposable emulator, leaving adb/host networking untouched. It drives
the actual WebView UI: create an encrypted profile, reach invitation setup without
provisioning, background, return locked, reopen with the original passphrase and
restart the process with the retained profile still locked. It checks app-UID TCP
listening sockets at each observed stage and uninstalls its app, removes its own
firewall rules and UI dump even after failure. This is bounded sampled no-listener
and profile lifecycle evidence, not continuous traffic coverage or proof of remote
chat/files, invitation acceptance, profile identity equality or optional push.
The existing source-level real-node mobile journey remains a separate receipt.

`python3 scripts/android-build.py self-test` and
`python3 -m unittest discover -s scripts/tests -p android_release_test.py` exercise
pure provenance, signer, feature, alignment and cleanup guards without credentials
or device access. Platform execution is still required; mocks are not reported as
an app or OS vault pass.

References: [Tauri Android build CLI](https://v2.tauri.app/reference/cli/#android-build),
[Tauri Android signing](https://v2.tauri.app/distribute/sign/android/),
[Android 16 KiB page sizes](https://developer.android.com/guide/practices/page-sizes).

## Retry installed smoke without rebuilding

`.github/workflows/android-smoke.yml` consumes an existing completed Android
release run and its exact artifact ID, ZIP digest and original GChat/GComs commits.
It needs no signing environment, keystore, Firebase config, Rust or npm build. Its
read-only GitHub token downloads that run's artifact; the controller checks the
protected original workflow/ref and source identities, GitHub and downloaded ZIP
digests, source/build/signing receipt agreement, both APK hashes, the current
publisher certificate pin, signatures and native-library/alignment metadata.
A failed overall build workflow is acceptable only when its retained build and
signing gates passed; the old emulator failure remains failed.

The original extracted artifact stays under `original/`; original JSON bytes and
paths are preserved. `reuse.json` binds the original app sources separately from
the new controller's commit/tree and helper hash. The new lifecycle receipt never
qualifies newer application code. The job creates one fresh AVD using the same
explicit `ANDROID_USER_HOME`, `ANDROID_EMULATOR_HOME` and `ANDROID_AVD_HOME` for
both avdmanager and emulator, checks its registration before starting, and stops
its emulator on every terminal path. This avoids the inherited home-directory
mismatch that prevented the earlier emulator from booting. The bounded driver
retains setup, emulator, app-UID logcat and UI diagnostics alongside cleanup.
ADB's root restart may close the initial connection. The driver reconnects within
45 seconds and at most three attempts, and requires an actual `id -u` result of
zero before installing the app or firewall rules. It retains every root attempt;
this does not retry an application assertion or weaken lifecycle checks.
The UI observer removes each prior XML dump before sampling. A missing or partial
dump remains a pending observation within the original UI deadline, with the
observer error retained; it cannot satisfy an assertion using a stale screen.

[Android's documented AVD directory lookup](https://developer.android.com/tools/variables)
defines these shared paths. The earlier native/signing artifact remains immutable;
no new remote delivery or physical-device pass is implied. Both build and reuse
workers also check the invitation picker. Leaving GChat for Android Documents
locks the default profile, just like Home. Cancellation must return to the manual
unlock screen and reopen without a pending selection. A second picker selects a
harmless local text fixture: the app must retain its opaque file handle across
lock, require explicit same-profile unlock and Continue, then populate the
invitation field. The worker never submits that invalid invitation. It removes
the owned fixture on every terminal path and preserves earlier failed receipts.

The mobile UI holds at most one opaque file handle in RAM for five minutes. It
does not persist selection or plaintext. Expiry, profile replacement or explicit
discard invalidates that handle; outgoing selections retain their original
network/channel and cannot be redirected by navigation. Browser tests also cover
outgoing continuation/cancellation and unavailable destinations. Native smoke
does not qualify remote file transfer or invitations to an operated network.

## Google Play bundles

The release workflow also runs `build --bundle` to produce one AAB containing both
ARM64 and x86_64, in addition to the existing separate APKs. Bundletool 1.18.2 is
pinned by SHA-256. Every bundled native library must match the corresponding APK
and retain 16 KiB ELF alignment. The AAB uses JAR signing with the existing Android
publisher; every payload entry is read and checked against the pinned certificate,
including refusal of unsigned additions and modified entries.

The signing stage derives an x86_64 API35 split-APK set from that exact signed AAB.
The emulator stage uses `--from-bundle` and `adb install-multiple`, verifies each
split signature and source-bound native payload, and exercises the existing
profile/reopen/document-picker checks. A passing tool test is not an executed
emulator receipt or a successful Play upload. Play app creation, permissions and
Play App Signing continuity remain separate account prerequisites. Use the existing
publisher key for Play App Signing so direct APK installations remain compatible.

Bundletool keystore passwords use private temporary files, removed on failure and
success. The retained `.apks` archive, split hashes and device specification bind
the installed emulator app to the submitted AAB; no server push keys are packaged.
