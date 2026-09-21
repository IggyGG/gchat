# GChat mobile platform

A native Tauri 2 plugin for GChat (`boo.gchat.app`), Android API 26+ and iOS 15+.
This plugin never hosts relays or starts a profile automatically. Optional FCM/APNs
registration uses the platform notification services after explicit opt-in. The application owns opt-in UI, profile IDs,
locking, checkpointing and serialized suspend/resume operations.

## Rust integration

Register `tauri_plugin_gchat_mobile_platform::init()` on the Tauri builder.
Import `MobilePlatformExt`, then use `app.mobile_platform()`:

- `store_secret(slot, UnlockSecret::new(secret)?, RememberSecret::Confirmed).await`
- `get_secret(slot).await -> Result<Option<UnlockSecret>>`
- `delete_secret(slot).await -> Result<()>`
- `push_device(Option<bool>).await -> Result<PushDevice>` (Rust-only permission/token state)
- `on_lifecycle(callback) -> LifecycleSubscription` (module-level function)

Keep the `LifecycleSubscription` in the application attachment. Its callback
receives `LifecycleEvent::{Foreground, Background}`, immediately replays the
latest known state, and runs on the native lifecycle thread. Only enqueue work
there. Dropping the handle unregisters it; an already running callback may finish.
Deduplication and generation ordering prevent a registration replay from delivering
an older state after a newer event.

Use opaque per-profile slots (1–128 ASCII letters, digits, `_` or `-`), not paths.
Secrets are nonempty UTF-8 strings, at most 4096 bytes, with no NUL. Remembering
requires explicit `RememberSecret::Confirmed` on every write; initialization
never remembers anything. The application must invoke delete on opt-out/profile
removal and handle failure visibly before claiming the credential was forgotten.
A missing entry is `Ok(None)`; corrupt, locked or unavailable storage is an error.
Desktop calls return `Unsupported`, without a plaintext or in-memory fallback.

There are no webview commands or events carrying secrets. Empty default
permissions and an explicit Rust invoke rejection also block native command
fallback. The API is for trusted Rust application code only. Blocking native
response receivers run on blocking workers so cancellation of the Rust await
cannot drop a response receiver still owned by native code. Cancellation does
not undo a native store/delete already submitted; callers must serialize these
operations and await opt-out cleanup.

## Storage and lifecycle

Android stores AES-256-GCM ciphertext in `Context.noBackupFilesDir`, with a
non-exportable key generated in AndroidKeyStore for each slot. Random nonces
and slot/service authenticated data prevent record substitution; atomic writes
preserve the previous record on ordinary write failure. Plaintext byte arrays
are cleared after encryption/decryption. The application process checks device
unlock state before read/write. This is not biometric authentication or a promise
of hardware-backed key storage on every API 26 device. Keystore keys are not
made exportable or backed up. Deletion removes the key before deleting ciphertext.

Android sends background on `onStop` (excluding configuration recreation), not
`onPause`; foreground is `onResume`. iOS uses `didEnterBackground` and
`didBecomeActive`, not `willResignActive`. Native JNI/C callbacks do not depend
on JavaScript continuing to execute while the app is backgrounded.

The iOS vault uses generic-password Keychain entries, a private service name,
`kSecAttrAccessibleWhenUnlockedThisDeviceOnly` and `kSecAttrSynchronizable=false`.
No shared access group is selected. Updating does not delete the previous item
before a replacement is accepted. Rust secret wrappers zeroize on drop and redact
Debug. Native bridge serialization creates transient JVM/Swift strings; this
implementation does not promise whole-heap zeroization.

## Validation

Rust unit tests cover invalid slots/secrets, redacted diagnostics, initial state
replay, duplicate suppression, unsubscribe, out-of-order replay and callback panic
containment. Android unit/instrumentation tests cover validation, consent refusal,
Keystore round-trip/update, ciphertext tampering and deletion. Swift tests cover
validation, consent and private Keychain round-trip/update/delete in an app-hosted
iOS test target. Native platform tests must run on their platform; a Linux Rust
pass is not Android/iOS qualification. Physical lock behavior, process death and
app-integrated background persistence must be exercised separately.

The plugin follows the [Tauri mobile plugin API](https://v2.tauri.app/develop/plugins/develop-mobile/),
[Android Keystore](https://developer.android.com/privacy-and-security/keystore)
and [Apple Keychain accessibility](https://developer.apple.com/documentation/security/ksecattraccessiblewhenunlockedthisdeviceonly).

## Notification callbacks

Android uses a non-exported FirebaseMessagingService with auto-init disabled by
default. A generation gate rejects stale permission/token fetch completions after
opt-out. Data-only activity hints create one fixed generic notification while the
native policy and OS permission allow it. No hint starts a Rust runtime.

iOS adds only absent optional APNs methods to Tao's delegate; it does not replace
existing framework methods. A conflicting delegate causes notification setup to
fail without changing ordinary chat. Native completion handlers return promptly,
including while keys are unavailable. A tap only records a non-secret activity flag.
Provider tokens and gateway management receipts never enter webview commands or
events. The application adds its own bounded, serialized registration coordinator.
