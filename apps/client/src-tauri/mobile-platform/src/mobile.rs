use serde::{de::DeserializeOwned, Deserialize, Serialize};
use tauri::{
    plugin::{PluginApi, PluginHandle},
    AppHandle, Runtime,
};

use crate::{models::validate_slot, Error, RememberSecret, Result, UnlockSecret};

#[cfg(target_os = "ios")]
tauri::ios_plugin_binding!(init_plugin_gchat_mobile_platform);

pub(crate) fn init<R: Runtime, C: DeserializeOwned>(
    _app: &AppHandle<R>,
    api: PluginApi<R, C>,
) -> Result<MobilePlatform<R>> {
    #[cfg(target_os = "android")]
    let handle =
        api.register_android_plugin("boo.gchat.app.mobileplatform", "MobilePlatformPlugin");
    #[cfg(target_os = "ios")]
    let handle = api.register_ios_plugin(init_plugin_gchat_mobile_platform);
    Ok(MobilePlatform(
        handle.map_err(|_| Error::NativeUnavailable)?,
    ))
}

pub struct MobilePlatform<R: Runtime>(PluginHandle<R>);

#[derive(Serialize)]
struct SlotArgs<'a> {
    slot: &'a str,
}
#[derive(Serialize)]
struct StoreArgs<'a> {
    slot: &'a str,
    secret: &'a str,
    confirmed: bool,
}
#[derive(Deserialize)]
struct SecretReply {
    secret: Option<String>,
}

impl<R: Runtime> MobilePlatform<R> {
    pub async fn push_settings(&self) -> Result<()> {
        let handle = self.0.clone();
        tauri::async_runtime::spawn_blocking(move || {
            handle
                .run_mobile_plugin::<()>("pushSettings", ())
                .map_err(|_| Error::NativeUnavailable)
        })
        .await
        .map_err(|_| Error::NativeUnavailable)?
    }

    /// Only trusted Rust can request permission or obtain a provider token.
    pub async fn push_device(&self, enabled: Option<bool>) -> Result<crate::PushDevice> {
        #[derive(Serialize)]
        struct Args {
            enabled: Option<bool>,
        }
        let handle = self.0.clone();
        tauri::async_runtime::spawn_blocking(move || {
            handle
                .run_mobile_plugin("pushDevice", Args { enabled })
                .map_err(|_| Error::NativeUnavailable)
        })
        .await
        .map_err(|_| Error::NativeUnavailable)?
    }

    pub async fn store_secret(
        &self,
        slot: &str,
        secret: UnlockSecret,
        consent: RememberSecret,
    ) -> Result<()> {
        validate_slot(slot)?;
        let slot = slot.to_owned();
        let handle = self.0.clone();
        tauri::async_runtime::spawn_blocking(move || {
            let RememberSecret::Confirmed = consent;
            handle
                .run_mobile_plugin::<()>(
                    "storeSecret",
                    StoreArgs {
                        slot: &slot,
                        secret: secret.as_str(),
                        confirmed: true,
                    },
                )
                .map_err(|_| Error::NativeUnavailable)
        })
        .await
        .map_err(|_| Error::NativeUnavailable)?
    }

    pub async fn get_secret(&self, slot: &str) -> Result<Option<UnlockSecret>> {
        validate_slot(slot)?;
        let slot = slot.to_owned();
        let handle = self.0.clone();
        tauri::async_runtime::spawn_blocking(move || {
            let reply: SecretReply = handle
                .run_mobile_plugin("getSecret", SlotArgs { slot: &slot })
                .map_err(|_| Error::NativeUnavailable)?;
            reply.secret.map(UnlockSecret::new).transpose()
        })
        .await
        .map_err(|_| Error::NativeUnavailable)?
    }

    pub async fn delete_secret(&self, slot: &str) -> Result<()> {
        validate_slot(slot)?;
        let slot = slot.to_owned();
        let handle = self.0.clone();
        tauri::async_runtime::spawn_blocking(move || {
            handle
                .run_mobile_plugin::<()>("deleteSecret", SlotArgs { slot: &slot })
                .map_err(|_| Error::NativeUnavailable)
        })
        .await
        .map_err(|_| Error::NativeUnavailable)?
    }
}

// Deliberately use the blocking native response receiver on a blocking worker.
// Cancelling the Rust await does not drop the native response receiver while a
// platform callback still owns it. The worker consumes and drops the response.
