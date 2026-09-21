# GChat mobile applications

Android and iOS use the same channel, invitation, message and file UI as desktop.
Their application identity is `boo.gchat.app`. Existing desktop profiles retain
the `dev.ghost.gchat` identity.

The mobile process owns an outbound GComs client. It does not launch a local
daemon, advertise a relay or accept inbound relay connections. The profile and
archive are encrypted in app-private storage. Joined networks also use the
outbound backend.

On suspension, new requests stop, admitted work drains, and the profile is
checkpointed before network resources close. Foreground recovery reopens the
same instance. An interrupted operation is not reported as delivered; delivery
still depends on its authenticated acknowledgement.

“Remember on this device” is off by default. Opting in stores the unlock secret
through Android Keystore encryption or a device-only iOS Keychain item, accessible
only while the device is unlocked. The webview cannot read that stored secret.
`/lock` and `/disconnect` disable automatic reopening and remove the remembered
credential. If secure storage is unavailable, the application keeps manual
passphrase unlocking available and reports the storage error.

File export stages a complete, verified file through bounded reads before
opening the platform picker. Android supports content destinations; iOS exports
an app-owned temporary document. Incomplete files and partial copies are not
reported as successful exports.

## Release status

The Android and iOS pipelines retain exact source, dependency and artifact
identities. See [Android release](ANDROID_RELEASE.md) and the iOS release workflow
for their platform-specific checks. A pipeline implementation or a Linux test is
not evidence that the corresponding native app has passed.

Native device builds, simulator/emulator execution, actual messaging and file
delivery, and physical-device behavior must be reported separately. Current local
checks cover the outbound profile lifecycle, cancellation/draining, private
credential policy, export bounds, and the shared UI. They do not qualify battery
use or physical-device operation.

APNs and Firebase credentials have been configured for the app operator. Native
push registration, relay-to-gateway binding and live notification delivery remain
unfinished. Firebase client configuration in a build does not establish push
delivery. Provider private keys never belong in application packages or source.
While push is unfinished, background delivery must not be promised.

Statistical privacy and 24-hour campaigns are not release gates under the owner's
current production policy. This does not assert statistical privacy qualification;
the remaining privacy work is recorded in [Production release](PRODUCTION_RELEASE.md).
