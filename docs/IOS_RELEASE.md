# iOS application release

The iOS worker builds the actual GChat application from a clean, frozen GChat /
GComs pair. Its identifier is `boo.gchat.app`, Apple team is `U93DVTJ3T5`, and the
App Store Connect record is **GChat.boo** (`6814308446`). Desktop identifiers are
unchanged. iOS 15+ ARM64 devices and an ARM64 simulator are the initial targets.

Dispatch `.github/workflows/ios-release.yml` from an approved `main`,
`release/gchat-*`, or version-tag ref. Supply both full commits, their protected
refs, a unique request ID, and an unused numeric `build_number` such as `1.0.1`.
The worker checks its own workflow/source identity before receiving signing
credentials. It archives the exact pair and records derived Rust locks, resolved
GComs packages, npm archive hashes, tool versions and resulting binaries.

The `release-signing` environment needs these protected inputs:

- `IOS_CERTIFICATE_BASE64`, `IOS_CERTIFICATE_PASSWORD` and
  `IOS_PROVISIONING_PROFILE_BASE64`: Apple Distribution identity and an App Store
  profile for this exact app, with production APNs enabled.
- `IOS_SIGNING_CERT_SHA256` repository variable: reviewed public distribution
  certificate SHA-256 pin, independent of the uploaded private material.
- Optional upload only: `APP_STORE_CONNECT_PRIVATE_KEY`,
  `APP_STORE_CONNECT_KEY_ID`, `APP_STORE_CONNECT_ISSUER_ID`.

Private signing material is imported into a newly created temporary keychain.
The prior keychain search list is restored, the temporary keychain is deleted,
and any newly installed profile for this exact UUID is removed. Existing profiles
are never overwritten. A before/after receipt requires all original profiles to
remain unchanged. Upload keys exist only in a private temporary directory, never
in the app, retained build artifacts or repository.

The validated UUID profile is installed in both recognized Xcode profile locations.
Tauri's additional randomly named copy is removed only after decoding the same
UUID and validating its certificate/entitlements. Newly created unrelated profiles
are preserved and fail the unchanged-profile check. A private build-directory
`xcodebuild` shim restores the pinned developer directory and manual-signing config
because pinned cargo-mobile2 clears these variables from child environments;
the shim invokes Apple's actual tool, with no signing check disabled. The worker
retains these public settings and hidden dependency-provenance files.

The build checks each mobile target's actual normal-dependency feature graph:
`network-client` must be enabled, and `embedded`, `launch` and node `relay-host`
must be absent. Compiled RPC IPC types are permitted; they do not start a host.
The simulator app is installed into a freshly created iPhone simulator, launched,
observed alive, terminated and relaunched. Screenshots and actual PIDs are
retained, then only that simulator is deleted. This gate establishes native
startup/relaunch, **not** an interactive profile, messaging, file, notification,
battery or physical-device journey. Those remain separate application checks.

Only after simulator success does the worker build a signed device IPA. It
verifies the ARM64/iOS platform, iOS 15 minimum, app/build identity, complete code
signature, pinned leaf certificate, unexpired App Store profile, disabled
debugger entitlement, production APNs entitlement and app-scoped Keychain groups.
Signing cleanup and unchanged original sources are required for success. Push
entitlement presence does not prove live push delivery.

`upload_testflight` defaults to false. When explicitly selected, the worker
rehashes the completed IPA and bound simulator/signing receipts before using
`altool` to upload it. This starts App Store Connect processing; it does not submit
a public App Store release, add testers, declare Apple processing complete or
resolve export compliance. GChat uses encryption: the derived iOS Info.plist
sets `ITSAppUsesNonExemptEncryption=true`, rather than asserting an unreviewed
exemption. Any required Apple export-compliance documentation must be completed
before tester distribution.

The Tauri CLI is supplied by the exact npm lock. The workflow uses Xcode 26.2 on
an Apple Silicon Mac, source-pinned Rust, Node 22.23.2 and npm 11.6.2. No source
patch, relaxed trust check, production relay action or private SDK substitution
is performed by the worker. Failed build/startup/signing/upload receipts remain
failures, even when a later retry passes.

References: [Tauri iOS signing](https://v2.tauri.app/distribute/sign/ios/),
[Tauri App Store build/upload](https://v2.tauri.app/distribute/app-store/),
[Tauri CLI options](https://v2.tauri.app/reference/cli/).
