//! GChat's compatibility adapter over the public application API.
pub use gcoms::runtime::ErrorSink;
use gcoms::{
    sdk::{GcClient, RelayCard},
    Application,
};
use std::{net::SocketAddr, path::Path, sync::Arc};
#[derive(Clone)]
pub struct ProtocolRuntime(pub Application);

#[cfg(not(any(target_os = "android", target_os = "ios")))]
static DESKTOP_RELAY_CONFIG: std::sync::Mutex<Option<gcoms::runtime::RelaySharingConfig>> =
    std::sync::Mutex::new(None);

#[cfg(not(any(target_os = "android", target_os = "ios")))]
pub(crate) fn set_desktop_relay_config(config: gcoms::runtime::RelaySharingConfig) {
    *DESKTOP_RELAY_CONFIG
        .lock()
        .expect("desktop relay configuration") = Some(config);
}

#[cfg(not(any(target_os = "android", target_os = "ios")))]
pub(crate) fn desktop_relay_config() -> Result<gcoms::runtime::RelaySharingConfig, String> {
    if let Some(config) = DESKTOP_RELAY_CONFIG
        .lock()
        .expect("desktop relay configuration")
        .clone()
    {
        return Ok(config);
    }
    let mut config = gcoms::runtime::RelaySharingConfig {
        enabled: std::env::var("GCHAT_RELAY_SHARING").as_deref() != Ok("off"),
        router_mapping: std::env::var("GCHAT_ROUTER_MAPPING").as_deref() != Ok("off"),
        ..Default::default()
    };
    if let Ok(value) = std::env::var("GCHAT_RELAY_CIRCUITS") {
        config.circuits = value
            .parse()
            .map_err(|_| "Invalid desktop relay circuit budget")?;
    }
    config.connections = config.circuits.saturating_mul(2);
    if let Ok(value) = std::env::var("GCHAT_RELAY_CONNECTIONS") {
        config.connections = value
            .parse()
            .map_err(|_| "Invalid desktop relay connection budget")?;
    }
    config.bandwidth_bytes_per_second = config.bandwidth_bytes_per_second.max(
        config
            .circuits
            .saturating_mul(8192)
            .saturating_add(256 * 1024),
    );
    if let Ok(value) = std::env::var("GCHAT_RELAY_BANDWIDTH") {
        config.bandwidth_bytes_per_second = value
            .parse()
            .map_err(|_| "Invalid desktop relay bandwidth budget")?;
    }
    config.validate()?;
    Ok(config)
}

#[cfg(not(any(target_os = "android", target_os = "ios")))]
fn desktop_sharing(
    builder: gcoms::ApplicationBuilder,
) -> Result<gcoms::ApplicationBuilder, String> {
    Ok(builder.relay_sharing(desktop_relay_config()?))
}

#[cfg(any(target_os = "android", target_os = "ios"))]
fn desktop_sharing(
    builder: gcoms::ApplicationBuilder,
) -> Result<gcoms::ApplicationBuilder, String> {
    Ok(builder)
}

/// Mobile profiles, including explicitly joined networks, never host a relay.
pub(crate) fn default_backend() -> gcoms::Backend {
    #[cfg(any(target_os = "android", target_os = "ios"))]
    {
        gcoms::Backend::NetworkClient
    }
    #[cfg(not(any(target_os = "android", target_os = "ios")))]
    {
        gcoms::Backend::Embedded
    }
}

impl ProtocolRuntime {
    pub(crate) fn network_client(&self) -> Option<gcoms_network_client::NetworkClient> {
        self.0
            .embedded_runtime()
            .and_then(|runtime| runtime.network_client())
    }

    /// One independently pinned profile per explicitly accepted network.
    #[cfg(feature = "gc2-carrier")]
    pub(crate) async fn open_network(
        path: &Path,
        secret: &str,
        create: bool,
        network: gcoms_network::NetworkIdentity,
    ) -> Result<Self, String> {
        network.verify_at(
            if create {
                gcoms_network_client::now_unix()
            } else {
                network.signed_defaults.defaults.issued_at
            },
            0,
        )?;
        let installed = gcoms_network_client::InstalledNetwork {
            trusted_key_b64: network.trusted_key_b64,
            signed_defaults: network.signed_defaults,
        };
        let builder = Application::builder("gchat")
            .backend(default_backend())
            .network_config(serde_json::to_vec(&installed).map_err(|error| error.to_string())?)
            .profile(path)
            .unlock_secret(secret)
            .carrier_profile(gcoms::sdk::CarrierProfile::Gc2)
            .create(create)
            .durable_channel_inbox(true)
            .receive_messages(false);
        Ok(Self(desktop_sharing(builder)?.open().await?))
    }

    #[cfg(not(feature = "gc2-carrier"))]
    pub(crate) async fn open_network(
        _path: &Path,
        _secret: &str,
        _create: bool,
        _network: gcoms_network::NetworkIdentity,
    ) -> Result<Self, String> {
        Err("this build does not include the GC/2 carrier profile".into())
    }

    pub fn sdk_client(&self) -> Arc<dyn GcClient> {
        self.0.messaging()
    }
    pub fn embedded(&self) -> Option<gcoms::sdk::EmbeddedClient> {
        self.0.embedded_runtime().map(|r| r.sdk_client().embedded())
    }
    pub fn listen_label(&self) -> String {
        self.0
            .embedded_runtime()
            .map_or_else(|| "shared service".into(), |r| r.listen_label())
    }
    pub fn set_error_sink(&self, sink: ErrorSink) {
        if let Some(runtime) = self.0.embedded_runtime() {
            runtime.set_error_sink(sink);
        }
    }
    pub async fn save(&self) -> Result<(), String> {
        self.sdk_client()
            .persist_profile()
            .await
            .map_err(|e| e.to_string())
    }
    pub async fn shutdown(self) -> Result<(), String> {
        self.0.stop_profile().await
    }
    pub async fn configure_network_dns(&self, enabled: bool) -> Result<(), String> {
        self.sdk_client()
            .configure_network_dns(enabled)
            .await
            .map_err(|e| e.to_string())
    }

    pub fn configure_relay_sharing(
        &self,
        enabled: bool,
    ) -> Result<gcoms::runtime::RelaySharingStatus, String> {
        self.0
            .embedded_runtime()
            .ok_or("Relay sharing requires this desktop's local runtime")?
            .configure_relay_sharing(enabled)
    }

    pub fn relay_sharing_status(&self) -> gcoms::runtime::RelaySharingStatus {
        self.0.embedded_runtime().map_or_else(
            || gcoms::runtime::RelaySharingStatus {
                state: "Relay sharing is unavailable for this backend".into(),
                ..Default::default()
            },
            |runtime| runtime.relay_sharing_status(),
        )
    }
    pub async fn network_dns_status(&self) -> Result<gcoms::sdk::NetworkNameStatus, String> {
        self.sdk_client()
            .network_dns_status()
            .await
            .map_err(|e| e.to_string())
    }
    pub async fn import_network_invitation(&self, code: &str) -> Result<(), String> {
        self.sdk_client()
            .import_network_invitation(code)
            .await
            .map_err(|e| e.to_string())
    }

    pub async fn network_status(&self) -> Result<gchat_api::NetworkStatus, String> {
        let status = self
            .sdk_client()
            .network_status()
            .await
            .map_err(|e| e.to_string())?;
        use gchat_api::NetworkState as T;
        use gcoms::sdk::NetworkState as S;
        Ok(gchat_api::NetworkStatus::new(match status.state {
            S::Locked => T::Locked,
            S::LocalOnly => T::LocalOnly,
            S::InvitationRequired => T::InvitationRequired,
            S::Connecting => T::Connecting,
            S::Connected => T::Connected,
            S::Reconnecting => T::Reconnecting,
            S::InvitationExpired => T::InvitationExpired,
            S::Unavailable => T::Unavailable,
        }))
    }
    pub async fn create_protected(
        path: &Path,
        secret: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        relay: Option<RelayCard>,
        private_cidrs: &[String],
    ) -> Result<Self, String> {
        Self::protected(path, secret, listen, advertise, relay, private_cidrs, true).await
    }
    pub async fn unlock_protected(
        path: &Path,
        secret: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        relay: Option<RelayCard>,
        private_cidrs: &[String],
    ) -> Result<Self, String> {
        Self::protected(path, secret, listen, advertise, relay, private_cidrs, false).await
    }
    async fn protected(
        path: &Path,
        secret: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        relay: Option<RelayCard>,
        private_cidrs: &[String],
        create: bool,
    ) -> Result<Self, String> {
        if !private_cidrs.is_empty() {
            return Err("private forwarding requires a scoped infrastructure runtime".into());
        }
        let builder = Application::builder("gchat")
            .network_config(crate::network::installed_json())
            .profile(path)
            .unlock_secret(secret)
            .listen(listen)
            .advertise(advertise)
            .relay(relay)
            .carrier_profile(gcoms::sdk::CarrierProfile::Gc2)
            .create(create)
            .durable_channel_inbox(true)
            .receive_messages(false);
        Ok(Self(desktop_sharing(builder)?.open().await?))
    }
    pub async fn create(
        path: &Path,
        secret: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        relay: Option<RelayCard>,
        private_cidrs: &[String],
    ) -> Result<Self, String> {
        if !private_cidrs.is_empty() {
            return Err("private forwarding requires a scoped infrastructure runtime".into());
        }
        let builder = Application::builder("gchat")
            .network_config(crate::network::installed_json())
            .profile(path)
            .unlock_secret(secret)
            .listen(listen)
            .advertise(advertise)
            .relay(relay)
            .create(true)
            .durable_channel_inbox(true)
            .receive_messages(false);

        Ok(Self(builder.open().await?))
    }

    pub async fn unlock(
        path: &Path,
        secret: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        relay: Option<RelayCard>,
        private_cidrs: &[String],
    ) -> Result<Self, String> {
        if !private_cidrs.is_empty() {
            return Err("private forwarding requires a scoped infrastructure runtime".into());
        }
        let builder = Application::builder("gchat")
            .network_config(crate::network::installed_json())
            .profile(path)
            .unlock_secret(secret)
            .listen(listen)
            .advertise(advertise)
            .relay(relay)
            .create(false)
            .durable_channel_inbox(true)
            .receive_messages(false);

        Ok(Self(builder.open().await?))
    }

    pub async fn create_fixture(
        path: &Path,
        secret: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        relay: Option<RelayCard>,
        private_cidrs: &[String],
    ) -> Result<Self, String> {
        if !private_cidrs.is_empty() {
            return Err("private forwarding requires a scoped infrastructure runtime".into());
        }
        let builder = Application::builder("gchat")
            .network_config(crate::network::installed_json())
            .profile(path)
            .unlock_secret(secret)
            .listen(listen)
            .advertise(advertise)
            .relay(relay)
            .create(true)
            .durable_channel_inbox(true)
            .receive_messages(false);
        let builder = builder.local_fixture().listen(listen);
        Ok(Self(builder.open().await?))
    }

    pub async fn unlock_fixture(
        path: &Path,
        secret: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        relay: Option<RelayCard>,
        private_cidrs: &[String],
    ) -> Result<Self, String> {
        if !private_cidrs.is_empty() {
            return Err("private forwarding requires a scoped infrastructure runtime".into());
        }
        let builder = Application::builder("gchat")
            .network_config(crate::network::installed_json())
            .profile(path)
            .unlock_secret(secret)
            .listen(listen)
            .advertise(advertise)
            .relay(relay)
            .create(false)
            .durable_channel_inbox(true)
            .receive_messages(false);
        let builder = builder.local_fixture().listen(listen);
        Ok(Self(builder.open().await?))
    }
}
