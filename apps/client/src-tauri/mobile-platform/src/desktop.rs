use serde::de::DeserializeOwned;
use tauri::{plugin::PluginApi, AppHandle, Runtime};

use crate::{models::validate_slot, Error, RememberSecret, Result, UnlockSecret};

pub(crate) fn init<R: Runtime, C: DeserializeOwned>(
    _app: &AppHandle<R>,
    _api: PluginApi<R, C>,
) -> Result<MobilePlatform<R>> {
    Ok(MobilePlatform(std::marker::PhantomData))
}

/// Desktop has no mobile vault; unsupported operations never fall back to files.
pub struct MobilePlatform<R: Runtime>(std::marker::PhantomData<fn() -> R>);

impl<R: Runtime> MobilePlatform<R> {
    pub async fn push_settings(&self) -> Result<()> {
        Err(Error::Unsupported)
    }

    pub async fn push_device(&self, _enabled: Option<bool>) -> Result<crate::PushDevice> {
        Err(Error::Unsupported)
    }

    pub async fn store_secret(
        &self,
        slot: &str,
        _secret: UnlockSecret,
        _consent: RememberSecret,
    ) -> Result<()> {
        validate_slot(slot)?;
        Err(Error::Unsupported)
    }

    pub async fn get_secret(&self, slot: &str) -> Result<Option<UnlockSecret>> {
        validate_slot(slot)?;
        Err(Error::Unsupported)
    }

    pub async fn delete_secret(&self, slot: &str) -> Result<()> {
        validate_slot(slot)?;
        Err(Error::Unsupported)
    }
}
