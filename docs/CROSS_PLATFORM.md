# GChat platform delivery

GChat shares its Svelte/Tauri interface across desktop and mobile. The current
production Linux release is 0.1.3. Mac 0.1.4 downloads for Apple Silicon and
Intel are now Developer ID signed, Apple-notarized and stapled; both passed
quarantined Gatekeeper and installed startup/service checks. Android 0.1.4 APKs
are available with their documented emulator-only scope. Windows and the mobile
push builds remain in progress; this is not a claim of completed store delivery.

## Delivery order

1. Apple Silicon and Intel macOS: native paired CI, pinned Gh0st signing,
   installed application journeys, then DMG publication.
2. Windows 11 x64: native MSVC, matching authenticated local host, WebView and
   installer lifecycle, then signed installer publication.
3. Android API 26+: shared touch UI, outbound SDK, app-private encrypted storage,
   bounded document streams and verified FCM notifications, then signed APK.
4. iOS 15+: in-process outbound SDK, Keychain and document access, suspension and
   verified APNs notifications, then TestFlight using the owner's Apple account.

Android and iOS must not use desktop daemon spawning or relay hosting. One SDK
runtime owns networking; native Kotlin/Swift adapters own platform lifecycle,
permissions, files and notification integration. Push is required for the first
mobile release, with normal reconnect preserved when permission or delivery fails.
Provider payloads carry generic activity only, never message text, sender names
or file names. The SDK and gateway implementation belong to the mobile SDK work;
GChat consumes completed source-bound handoffs.

## Integration contract

The expanded SDK branch and released 0.1.3 sources diverged. Migration must keep
combined invitations, separately authenticated networks, topics/nicknames,
leave/ownership transfer/closure, durable pending sends and streamed files.
Matching hosts must be bundled; incompatible IPC versions must be refused.
Existing encrypted profiles, archives and file caches must reopen unchanged or
through a tested recoverable migration. Do not replace the released application
with an older SDK consumer that lacks these behaviors.

Each platform must demonstrate invitation onboarding, chat and hash-verified
files with Linux, network isolation, offline recovery, retained-profile reopen,
and upgrade without data loss. Mobile adds suspension, termination, token changes
and real provider notification checks. Emulator/simulator results are distinguished
from physical-device results; use BrowserStack/TestFlight or invited testers for
the latter. Hosted Mac workers provide Xcode when no local Mac is available.

## Release policy

Keep pinned Gh0st release signatures. Current Mac `.2` releases additionally use
Movsai AB Developer ID signing and Apple notarization; original self-signed `.1`
releases retain their original limitations and are superseded on the website.
Apple TestFlight uses its own Apple-authorized provisioning. Secrets stay in
protected CI, never in Git or application bundles. Every binary and installer
retains exact source/dependency/native-check identities. Platforms ship separately
after their checks pass; Linux remains available throughout.

The owner's production-minutes-v1 policy remains: no 24-hour campaign or
statistical-privacy release gate. Report the actual remaining privacy limitations
in PRODUCTION_RELEASE.md without relabeling historical failures.
