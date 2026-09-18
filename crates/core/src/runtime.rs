//! GChat's compatibility adapter over the public application API.
pub use gcoms::runtime::ErrorSink;
use gcoms::{
    sdk::{GcClient, RelayCard},
    Application,
};
use std::{net::SocketAddr, path::Path, sync::Arc};
#[derive(Clone)]
pub struct ProtocolRuntime(pub Application);
impl ProtocolRuntime {
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
            .profile(path)
            .unlock_secret(secret)
            .listen(listen)
            .advertise(advertise)
            .relay(relay)
            .create(true)
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
            .profile(path)
            .unlock_secret(secret)
            .listen(listen)
            .advertise(advertise)
            .relay(relay)
            .create(false)
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
            .profile(path)
            .unlock_secret(secret)
            .listen(listen)
            .advertise(advertise)
            .relay(relay)
            .create(true)
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
            .profile(path)
            .unlock_secret(secret)
            .listen(listen)
            .advertise(advertise)
            .relay(relay)
            .create(false)
            .receive_messages(false);
        let builder = builder.local_fixture().listen(listen);
        Ok(Self(builder.open().await?))
    }
}
