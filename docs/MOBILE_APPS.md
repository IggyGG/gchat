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

## Optional activity notifications

Network settings expose an explicit notification opt-in on mobile. Android requests
notification permission and uses a Firebase service; iOS requests APNs alert permission.
Alerts say only “New activity in GChat.” Names, channels, message contents and file
names are excluded. Apple/Google can still observe notification timing and device
metadata; this is an optional convenience, not an anonymity guarantee.

The existing unlocked runtime requests a short-lived owner-authenticated registration
ticket from an inbox relay. Only the installed `https://push.gchat.boo` origin can
receive the provider token. Each profile/network retains a random installation nonce,
monotonic revision and management receipt in device-only OS-protected storage.
References are rebound to current aliases after reconnect, token rotation and before
suspension, with bounded work. Notification hints never count as message delivery.

Opt-out persists before native registration stops. Relay bindings are cleared and a
purpose-bound owner ticket revokes the gateway installation, including after a lost
registration reply. Incomplete cleanup is retained and retried after ordinary unlock
and reconnect. A generic hint already submitted to a provider may still arrive.
Default profile locking is unchanged: an alert tap opens the normal unlock screen;
callbacks never start another runtime or silently use a passphrase. Notification or
provider failure leaves foreground messaging and ordinary recovery available.

APNs/Firebase credentials remain operator-side. Source implementation and focused
local tests do not establish live provider delivery. Native permission/token/tap
callbacks, actual provider delivery and physical-device/battery behavior require
separate retained results. Push is best effort, not continuous background networking. Relay bindings never
outlive the existing inbox lease; suspension does not extend authenticated authority.
After lease expiry or relay state loss, a normal foreground reconnect restores it.

Statistical privacy and 24-hour campaigns are not release gates under the owner's
current production policy. This does not assert statistical privacy qualification;
the remaining privacy work is recorded in [Production release](PRODUCTION_RELEASE.md).
