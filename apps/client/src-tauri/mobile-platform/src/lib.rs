//! Rust-only native unlock storage and process lifecycle notifications.
//! No plaintext credential is exposed as a webview command or event.

use tauri::{
    plugin::{Builder, TauriPlugin},
    Manager, Runtime,
};

#[cfg(not(any(target_os = "android", target_os = "ios")))]
mod desktop;
mod error;
mod lifecycle;
#[cfg(any(target_os = "android", target_os = "ios"))]
mod mobile;
mod models;
mod push;

#[cfg(not(any(target_os = "android", target_os = "ios")))]
pub use desktop::MobilePlatform;
pub use error::{Error, Result};
pub use lifecycle::{on_lifecycle, LifecycleEvent, LifecycleSubscription};
#[cfg(any(target_os = "android", target_os = "ios"))]
pub use mobile::MobilePlatform;
pub use models::{RememberSecret, UnlockSecret};
pub use push::PushDevice;

pub trait MobilePlatformExt<R: Runtime> {
    fn mobile_platform(&self) -> &MobilePlatform<R>;
}

impl<R: Runtime, T: Manager<R>> MobilePlatformExt<R> for T {
    fn mobile_platform(&self) -> &MobilePlatform<R> {
        self.state::<MobilePlatform<R>>().inner()
    }
}

pub fn init<R: Runtime>() -> TauriPlugin<R> {
    Builder::new("gchat-mobile-platform")
        // Returning true also prevents Tauri's native-plugin fallback dispatch.
        // Secrets remain inaccessible even if a capability is accidentally widened.
        .invoke_handler(|invoke| {
            invoke.resolver.reject("mobile platform APIs are Rust-only");
            true
        })
        .setup(|app, api| {
            #[cfg(any(target_os = "android", target_os = "ios"))]
            let platform = mobile::init(app, api)?;
            #[cfg(not(any(target_os = "android", target_os = "ios")))]
            let platform = desktop::init(app, api)?;
            app.manage(platform);
            Ok(())
        })
        .build()
}
