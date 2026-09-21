# Android process lifecycle

GChat registers its own single observer with AndroidX `ProcessLifecycleOwner`
from `MobilePlatformPlugin.load`, on the Android main thread. Tauri 2.11.5's
generated `TauriActivity` defines a `TauriLifecycleObserver` but does not attach
it, so overriding plugin `onResume`/`onStop` alone did not deliver events.

The observer forwards process resume/stop to the existing Rust lifecycle hub.
It retains only a weak recipient, replays current state to a replacement plugin
and never registers another observer during Activity recreation. AndroidX owns
the configuration-change debounce. Pause alone does not count as background.
The initial stopped state is explicit; it never assumes a hidden process is live.
`GChatLifecycle` Logcat entries contain fixed phase names only, without profile,
credential, invitation, message or file details.

The Rust checkpoint/shutdown and default locked return remain unchanged. External
file-picker stop/resume remains subject to the same policy and needs its own
installed-app test. There is no keep-unlocked exception or automatic credential
storage in this change.

`ProcessLifecycleRegistrationTest` uses a real AndroidX `LifecycleRegistry` to
exercise initial replay, duplicate load, replacement recipients, pause, stop and
resume. These JVM checks do not substitute for the signed-APK Home/reopen and
picker journeys in `scripts/android-build.py`.

Sources:
- [Exact Tauri 2.11.5 generated activity](https://raw.githubusercontent.com/tauri-apps/tauri/tauri-v2.11.5/crates/tauri/mobile/android-codegen/TauriActivity.kt)
- [AndroidX process lifecycle behavior](https://developer.android.com/reference/androidx/lifecycle/ProcessLifecycleOwner)
