use crate::store::{ProtocolData, ProtocolStore};
use async_trait::async_trait;
use gchat_api::{NetworkState, NetworkStatus};
use gcoms_node::node::{NodeConfig, NodeHandle};
use gcoms_node::proto::NodeInfo;
use gcoms_sdk::{
    ActivityBucket, AutomaticJoinEndpoint, Blob, ChannelId, ChannelMemberSummary,
    ChannelVisibility, ClientEvent, ContactCard, EmbeddedClient, GcClient, Identity, JoinRequest,
    JoinedChannel, MessageId, PresenceMode, PublicChannelDescriptor, SdkError,
};
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::sync::{broadcast, mpsc, watch};

mod persistence;
pub use persistence::PersistenceDiagnostics;
use persistence::{PersistenceCounters, SaveCause};

/// Receives non-fatal runtime problems (failed background saves) so a host
/// with a full-screen UI can show them instead of writing to stderr.
pub type ErrorSink = Arc<dyn Fn(String) + Send + Sync>;

struct Inner {
    node: NodeHandle,
    _store: Arc<ProtocolStore>,
    persistence: PersistenceCounters,
    events: broadcast::Sender<ClientEvent>,
    event_failures: watch::Sender<u64>,
    save_lock: tokio::sync::Mutex<()>,
    error_sink: std::sync::Mutex<Option<ErrorSink>>,
    network: Option<gcoms_network_client::NetworkClient>,
    network_status: std::sync::Mutex<NetworkStatus>,
    uses_installed_network: std::sync::atomic::AtomicBool,
    background: std::sync::Mutex<Option<BackgroundTasks>>,
    recover_now: tokio::sync::Notify,
    names_now: tokio::sync::Notify,
}

#[derive(Default)]
struct BackgroundTasks {
    tasks: tokio::task::JoinSet<()>,
    recovery_started: bool,
    naming_started: bool,
}

#[derive(Clone)]
pub struct ProtocolRuntime(Arc<Inner>);

/// GChat file carrier profile with fixed chat cover and observable bulk. The durable
/// directory lives beside the other private network state.
#[cfg(feature = "gc2-carrier")]
fn protected_profile(store: &ProtocolStore) -> gcoms_node::node::NodeProfile {
    gcoms_node::node::NodeProfile::gchat_file_transfer_production(
        Some(store.network_directory()),
        2,
    )
}

type CentralPartition = (Vec<[u8; 16]>, Vec<[u8; 16]>);

#[derive(Clone)]
pub struct ProtocolClient {
    embedded: EmbeddedClient,
    runtime: ProtocolRuntime,
    central_primary: Option<CentralPartition>,
}

impl ProtocolRuntime {
    pub async fn create(
        store_path: &std::path::Path,
        passphrase: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        inbox_relay: Option<NodeInfo>,
        allow_frwd_private_cidrs: &[String],
    ) -> Result<Self, String> {
        let (store, data) = ProtocolStore::create(store_path, passphrase)?;
        Self::boot(
            store,
            data,
            listen,
            advertise,
            inbox_relay,
            allow_frwd_private_cidrs,
            gcoms_node::node::NodeProfile::Production,
        )
        .await
    }

    /// Explicit direct transport for disposable local integration fixtures.
    #[doc(hidden)]
    pub async fn create_fixture(
        store_path: &std::path::Path,
        passphrase: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        inbox_relay: Option<NodeInfo>,
        allow_frwd_private_cidrs: &[String],
    ) -> Result<Self, String> {
        let (store, data) = ProtocolStore::create(store_path, passphrase)?;
        Self::boot(
            store,
            data,
            listen,
            advertise,
            inbox_relay,
            allow_frwd_private_cidrs,
            gcoms_node::node::NodeProfile::fixture(),
        )
        .await
    }

    /// Create an instance that selects the explicit GC/2 carrier profile:
    /// production transport behaviour with the durable directory under this
    /// instance's network directory. Requires the `gc2-carrier` feature.
    #[cfg(feature = "gc2-carrier")]
    pub async fn create_protected(
        store_path: &std::path::Path,
        passphrase: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        inbox_relay: Option<NodeInfo>,
        allow_frwd_private_cidrs: &[String],
    ) -> Result<Self, String> {
        let (store, data) = ProtocolStore::create(store_path, passphrase)?;
        let profile = protected_profile(&store);
        Self::boot(
            store,
            data,
            listen,
            advertise,
            inbox_relay,
            allow_frwd_private_cidrs,
            profile,
        )
        .await
    }

    /// Without the `gc2-carrier` feature this build cannot select the profile.
    #[cfg(not(feature = "gc2-carrier"))]
    pub async fn create_protected(
        _store_path: &std::path::Path,
        _passphrase: &str,
        _listen: SocketAddr,
        _advertise: Option<SocketAddr>,
        _inbox_relay: Option<NodeInfo>,
        _allow_frwd_private_cidrs: &[String],
    ) -> Result<Self, String> {
        Err("this build does not include the GC/2 carrier profile".into())
    }

    pub async fn unlock(
        store_path: &std::path::Path,
        passphrase: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        inbox_relay: Option<NodeInfo>,
        allow_frwd_private_cidrs: &[String],
    ) -> Result<Self, String> {
        let (store, data) = ProtocolStore::open(store_path, passphrase)?;
        Self::boot(
            store,
            data,
            listen,
            advertise,
            inbox_relay,
            allow_frwd_private_cidrs,
            gcoms_node::node::NodeProfile::Production,
        )
        .await
    }

    /// Explicit direct transport for disposable local integration fixtures.
    #[doc(hidden)]
    pub async fn unlock_fixture(
        store_path: &std::path::Path,
        passphrase: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        inbox_relay: Option<NodeInfo>,
        allow_frwd_private_cidrs: &[String],
    ) -> Result<Self, String> {
        let (store, data) = ProtocolStore::open(store_path, passphrase)?;
        Self::boot(
            store,
            data,
            listen,
            advertise,
            inbox_relay,
            allow_frwd_private_cidrs,
            gcoms_node::node::NodeProfile::fixture(),
        )
        .await
    }

    /// Reopen an instance created with the explicit GC/2 carrier profile.
    #[cfg(feature = "gc2-carrier")]
    pub async fn unlock_protected(
        store_path: &std::path::Path,
        passphrase: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        inbox_relay: Option<NodeInfo>,
        allow_frwd_private_cidrs: &[String],
    ) -> Result<Self, String> {
        let (store, data) = ProtocolStore::open(store_path, passphrase)?;
        let profile = protected_profile(&store);
        Self::boot(
            store,
            data,
            listen,
            advertise,
            inbox_relay,
            allow_frwd_private_cidrs,
            profile,
        )
        .await
    }

    #[cfg(not(feature = "gc2-carrier"))]
    pub async fn unlock_protected(
        _store_path: &std::path::Path,
        _passphrase: &str,
        _listen: SocketAddr,
        _advertise: Option<SocketAddr>,
        _inbox_relay: Option<NodeInfo>,
        _allow_frwd_private_cidrs: &[String],
    ) -> Result<Self, String> {
        Err("this build does not include the GC/2 carrier profile".into())
    }

    #[allow(clippy::too_many_arguments)]
    async fn boot(
        store: ProtocolStore,
        data: ProtocolData,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        inbox_relay: Option<NodeInfo>,
        allow_frwd_private_cidrs: &[String],
        profile: gcoms_node::node::NodeProfile,
    ) -> Result<Self, String> {
        let identity_seed = data.identity_seed;
        let node_state = data.node_state;
        let network = if profile.is_production() {
            Some(gcoms_network_client::NetworkClient::open(
                &store.network_directory(),
                crate::network::installed()?,
            )?)
        } else {
            None
        };
        let connectivity = if network.is_some() && listen.port() == 0 {
            Some(gcoms_node::connectivity::ConnectivityConfig {
                state: Some(Arc::new(gcoms_node::connectivity::PortState::open(
                    &store.network_directory(),
                    &identity_seed,
                )?)),
                ..Default::default()
            })
        } else {
            None
        };
        let store = Arc::new(store);
        let sink_store = store.clone();
        let durable_state_sink: gcoms_node::node::DurableStateSink = Arc::new(move |node_state| {
            sink_store.save(&ProtocolData {
                identity_seed,
                node_state: Some(node_state),
            })
        });
        let node_config = NodeConfig {
            seed: identity_seed,
            listen,
            control: None,
            advertise,
            inbox_relay,
            profile,
            alias_lifecycle: Default::default(),
        };
        let policy = build_frwd_policy(allow_frwd_private_cidrs, listen.port())?;
        let node = if let Some(connectivity) = connectivity {
            let mut routing = gcoms_node::node::RoutingConfig::from_environment()?;
            routing.connectivity = Some(connectivity);
            gcoms_node::node::start_persistent_restored_with_policy_and_routing(
                node_config,
                policy,
                routing,
                durable_state_sink,
                node_state.as_deref(),
            )
            .await?
        } else {
            gcoms_node::node::start_persistent_restored(
                node_config,
                policy,
                durable_state_sink,
                node_state.as_deref(),
            )
            .await?
        };
        let runtime = Self(Arc::new(Inner {
            node,
            _store: store,
            persistence: PersistenceCounters::default(),
            events: broadcast::channel(256).0,
            event_failures: watch::channel(0).0,
            save_lock: tokio::sync::Mutex::new(()),
            error_sink: std::sync::Mutex::new(None),
            network_status: std::sync::Mutex::new(NetworkStatus::new(if network.is_some() {
                NetworkState::Connecting
            } else {
                NetworkState::LocalOnly
            })),
            network,
            uses_installed_network: std::sync::atomic::AtomicBool::new(true),
            background: std::sync::Mutex::new(Some(BackgroundTasks::default())),
            recover_now: tokio::sync::Notify::new(),
            names_now: tokio::sync::Notify::new(),
        }));
        runtime.spawn_event_persistence();
        runtime.spawn_periodic_save();
        Ok(runtime)
    }

    /// Opt in only for a dedicated recorder/control profile, never a chat profile.
    pub async fn enable_durable_applications(&self) -> Result<(), String> {
        self.0.node.enable_durable_applications().await
    }

    pub fn sdk_client(&self) -> ProtocolClient {
        ProtocolClient {
            embedded: EmbeddedClient::new(self.0.node.clone()),
            runtime: self.clone(),
            central_primary: None,
        }
    }

    /// Route background-save failures somewhere other than stderr.
    pub fn set_error_sink(&self, sink: ErrorSink) {
        *self
            .0
            .error_sink
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner()) = Some(sink);
    }

    /// The node's primary advertised address, or `unavailable`.
    pub fn listen_label(&self) -> String {
        self.0.node.info.primary().map_or_else(
            || "unavailable".into(),
            |alias| alias.target.address.to_string(),
        )
    }

    fn report(&self, message: String) {
        let sink = self
            .0
            .error_sink
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner())
            .clone();
        match sink {
            Some(sink) => sink(message),
            None => eprintln!("gcd: {message}"),
        }
    }

    pub async fn save(&self) -> Result<(), String> {
        self.save_for(SaveCause::Explicit).await
    }

    async fn save_for(&self, cause: SaveCause) -> Result<(), String> {
        let started = std::time::Instant::now();
        self.0.persistence.begin(cause);
        let _save = self.0.save_lock.lock().await;
        let result = self.0.node.persist_state().await;
        self.0.persistence.finish(cause, started, result.is_ok());
        result
    }

    /// Aggregate caller and actual encrypted-write costs since this runtime opened.
    /// A canceled/in-flight request may not yet have a completion; snapshots are
    /// observational counters, not a durability receipt.
    pub fn persistence_diagnostics(&self) -> PersistenceDiagnostics {
        self.0
            .persistence
            .snapshot(self.0._store.save_diagnostics())
    }

    pub async fn shutdown(self) -> Result<(), String> {
        // A weak reference can still be upgraded by an in-flight save or event
        // forwarder. Join every worker before releasing the encrypted profile;
        // taking the registry also prevents new subscriptions from starting one.
        let background = self.0.background.lock().expect("runtime task lock").take();
        if let Some(mut background) = background {
            background.tasks.abort_all();
            while background.tasks.join_next().await.is_some() {}
        }

        let save = self.save_for(SaveCause::Shutdown).await;
        self.0.node.shutdown().await;
        save
    }

    pub(crate) fn network_client(&self) -> Option<gcoms_network_client::NetworkClient> {
        self.0.network.clone()
    }

    pub fn network_status(&self) -> NetworkStatus {
        if let Some(network) = self.0.network.as_ref().filter(|_| {
            self.0
                .uses_installed_network
                .load(std::sync::atomic::Ordering::Relaxed)
        }) {
            match network.has_invitation() {
                Ok(false) if !self.0.node.has_routing_bootstrap() => {
                    return NetworkStatus::new(NetworkState::InvitationRequired)
                }
                Err(_) => return NetworkStatus::new(NetworkState::Unavailable),
                _ => {}
            }
        }
        self.0
            .network_status
            .lock()
            .expect("network status lock")
            .clone()
    }

    pub fn import_network_invitation(&self, code: &str) -> Result<(), String> {
        self.0
            .network
            .as_ref()
            .ok_or("Network invitations are unavailable in a local fixture")?
            .import_invitation(code)?;
        *self.0.network_status.lock().expect("network status lock") =
            NetworkStatus::new(NetworkState::Connecting);
        self.0.recover_now.notify_one();
        Ok(())
    }

    pub fn configure_network_dns(&self, enabled: bool) -> Result<(), String> {
        self.0
            .network
            .as_ref()
            .ok_or("Network naming is unavailable in a local fixture")?
            .configure_opt_in(enabled)?;
        self.start_network_maintenance(Vec::new(), false)?;
        self.0.names_now.notify_one();
        Ok(())
    }

    pub fn network_dns_status(&self) -> Result<gcoms_network_client::names::NameStatus, String> {
        self.0
            .network
            .as_ref()
            .ok_or("Network naming is unavailable in a local fixture")?
            .name_status()
    }

    /// Local startup never waits for network I/O. Naming/removal is independent
    /// of bootstrap suppression and each lane retains its own original budget.
    pub fn start_network_recovery(&self, urls: Vec<String>) -> Result<(), String> {
        self.start_network_maintenance(urls, true)
    }

    pub fn start_network_maintenance(
        &self,
        urls: Vec<String>,
        bootstrap: bool,
    ) -> Result<(), String> {
        if self.0.network.is_none() {
            return Ok(());
        }
        if bootstrap && !urls.is_empty() {
            crate::bootstrap::parse_bootstrap_urls(&urls, false)?;
        }
        let mut background = self.0.background.lock().expect("runtime task lock");
        let background = background.as_mut().ok_or("protocol runtime is shut down")?;
        if bootstrap && !background.recovery_started {
            self.0.uses_installed_network.store(
                crate::bootstrap::uses_installed_network(&urls),
                std::sync::atomic::Ordering::Relaxed,
            );
            background.recovery_started = true;
            background
                .tasks
                .spawn(network_bootstrap_loop(Arc::downgrade(&self.0), urls));
        }
        if !background.naming_started {
            background.naming_started = true;
            background
                .tasks
                .spawn(network_names_loop(Arc::downgrade(&self.0)));
        }
        Ok(())
    }

    fn spawn_background(&self, task: impl std::future::Future<Output = ()> + Send + 'static) {
        let mut background = self.0.background.lock().expect("runtime task lock");
        if let Some(background) = background.as_mut() {
            // Closed subscriptions must not accumulate completed task records.
            while background.tasks.try_join_next().is_some() {}
            background.tasks.spawn(task);
        }
    }

    fn spawn_periodic_save(&self) {
        let inner = Arc::downgrade(&self.0);
        self.spawn_background(async move {
            loop {
                tokio::time::sleep(std::time::Duration::from_secs(30)).await;
                let Some(inner) = inner.upgrade() else { break };
                let runtime = ProtocolRuntime(inner);
                if let Err(error) = runtime.save_for(SaveCause::Periodic).await {
                    runtime.report(format!("periodic protocol profile save failed: {error}"));
                }
            }
        });
    }

    fn spawn_event_persistence(&self) {
        self.spawn_event_persistence_from(self.sdk_client().embedded.subscribe_events());
    }

    fn spawn_event_persistence_from(&self, mut events: mpsc::Receiver<ClientEvent>) {
        let inner = Arc::downgrade(&self.0);
        self.spawn_background(async move {
            while let Some(event) = events.recv().await {
                let Some(inner) = inner.upgrade() else { break };
                let runtime = ProtocolRuntime(inner);
                runtime.0.persistence.event(&event);
                match runtime.save_for(SaveCause::Event).await {
                    Ok(()) => {
                        // One completed barrier covers this event for every
                        // hosted subscriber present at publication.
                        let _ = runtime.0.events.send(event);
                        runtime.0.persistence.published();
                    }
                    Err(error) => {
                        // A separate watch cannot be lost when a slow consumer
                        // overruns the bounded event bus. Existing subscribers
                        // close; a new subscription may observe later saves.
                        runtime.0.event_failures.send_modify(|generation| {
                            *generation = generation.wrapping_add(1);
                        });
                        runtime.report(format!("protocol event save failed: {error}"));
                    }
                }
            }
        });
    }

    fn forward_events(&self, ownership: Option<CentralPartition>) -> mpsc::Receiver<ClientEvent> {
        let (sender, receiver) = mpsc::channel(256);
        self.spawn_background(forward_protocol_events(
            self.0.events.subscribe(),
            sender,
            self.0.event_failures.subscribe(),
            ownership,
        ));
        receiver
    }
}

fn recovery_delay(failures: u32) -> std::time::Duration {
    let seconds = if failures == 0 {
        300
    } else {
        (5u64 << failures.min(5)).min(120)
    };
    std::time::Duration::from_millis(seconds * 1000 + u64::from(rand::random::<u16>()) % 5000)
}
fn naming_delay(
    status: &gcoms_network_client::names::NameStatus,
    now: u64,
    base: std::time::Duration,
) -> std::time::Duration {
    let mut seconds = base.as_secs().clamp(1, 300);
    if status.pending {
        seconds = seconds.min(5);
    }
    if status.opted_in && !status.removed {
        if let Some(record) = &status.registration {
            seconds = seconds.min((record.lease_expires_at.saturating_sub(now) / 2).max(1));
        }
    }
    std::time::Duration::from_secs(seconds)
}
async fn network_bootstrap_loop(weak: std::sync::Weak<Inner>, urls: Vec<String>) {
    let mut failures = 0u32;
    loop {
        let Some(inner) = weak.upgrade() else { break };
        let deadline = tokio::time::Instant::now() + std::time::Duration::from_secs(120);
        let result = tokio::time::timeout_at(
            deadline,
            crate::bootstrap::recover_network(&inner.node, inner.network.as_ref(), &urls, deadline),
        )
        .await;
        let success = matches!(result, Ok(Ok(())));
        let state = match &result {
            Ok(Ok(())) => NetworkState::Connected,
            Ok(Err(error)) if error.contains("invitation expired") => {
                NetworkState::InvitationExpired
            }
            Ok(Err(error)) if error.contains("Enter a network invitation") => {
                NetworkState::InvitationRequired
            }
            _ => NetworkState::Reconnecting,
        };
        *inner.network_status.lock().expect("network status lock") = NetworkStatus::new(state);
        failures = if success {
            0
        } else {
            failures.saturating_add(1)
        };
        tokio::select! {
            _ = tokio::time::sleep(recovery_delay(failures)) => {},
            _ = inner.recover_now.notified() => {},
        }
    }
}
async fn network_names_loop(weak: std::sync::Weak<Inner>) {
    let mut failures = 0u32;
    loop {
        let Some(inner) = weak.upgrade() else { break };
        let Some(network) = inner.network.as_ref() else {
            break;
        };
        let deadline = tokio::time::Instant::now() + std::time::Duration::from_secs(15);
        let result = tokio::time::timeout_at(deadline, async {
            network.flush_name(deadline).await?;
            if network.name_status()?.opted_in {
                if let Some(listener) = inner.node.local_relay_introduction()? {
                    network.update_listener(&listener, deadline).await?;
                }
            }
            Ok::<(), String>(())
        })
        .await;
        failures = if matches!(result, Ok(Ok(()))) {
            0
        } else {
            failures.saturating_add(1)
        };
        let base = recovery_delay(failures);
        let delay = network
            .name_status()
            .map(|status| naming_delay(&status, gcoms_network_client::now_unix(), base))
            .unwrap_or(base);
        tokio::select! {
            _ = tokio::time::sleep(delay) => {},
            _ = inner.names_now.notified() => {},
        }
    }
}

impl ProtocolClient {
    fn check_primary_source(&self, wire: &[u8]) -> Result<(), SdkError> {
        if let Some((_, scoped)) = &self.central_primary {
            if gcoms_sdk::component::RoutedApplication::decode(wire)
                .is_ok_and(|route| scoped.contains(&route.source))
            {
                return Err(SdkError::PermissionDenied);
            }
        }
        Ok(())
    }

    async fn persist(&self) -> Result<(), SdkError> {
        self.runtime.save().await.map_err(SdkError::Runtime)
    }

    /// The in-process embedded client backing this hosted runtime, for
    /// operations (e.g. invite links) that reach the node directly.
    pub fn embedded(&self) -> EmbeddedClient {
        self.embedded.clone()
    }
}

#[async_trait]
impl GcClient for ProtocolClient {
    async fn configure_catalog_origins(&self, origins: Vec<String>) -> Result<(), SdkError> {
        self.embedded.configure_catalog_origins(origins).await
    }
    async fn catalog_request(
        &self,
        request: gcoms_sdk::CatalogHttpRequest,
    ) -> Result<gcoms_sdk::CatalogHttpResponse, SdkError> {
        self.embedded.catalog_request(request).await
    }

    async fn file_route(&self) -> Result<Vec<u8>, SdkError> {
        self.embedded.file_route().await
    }

    fn contact_identity(&self, card: &ContactCard) -> Result<Vec<u8>, SdkError> {
        self.embedded.contact_identity(card)
    }
    fn identity(&self) -> Identity {
        self.embedded.identity()
    }

    async fn refresh_identity(&self) -> Result<Identity, SdkError> {
        self.embedded.refresh_identity().await
    }

    async fn sign_identity_digest(&self, digest: [u8; 32]) -> Result<Vec<u8>, SdkError> {
        self.embedded.sign_identity_digest(digest).await
    }

    async fn sign_principal_binding_hash(
        &self,
        claims_hash: [u8; 32],
    ) -> Result<Vec<u8>, SdkError> {
        self.embedded.sign_principal_binding_hash(claims_hash).await
    }

    fn subscribe_events(&self) -> mpsc::Receiver<ClientEvent> {
        // Forward only events published after the runtime's shared barrier.
        // Subscriber workers hold no runtime/profile handle.
        self.runtime.forward_events(self.central_primary.clone())
    }

    async fn list_channels(&self) -> Result<Vec<JoinedChannel>, SdkError> {
        self.embedded.list_channels().await
    }

    async fn channel_roster(&self, channel: &str) -> Result<Vec<ChannelMemberSummary>, SdkError> {
        self.embedded.channel_roster(channel).await
    }

    async fn public_channel_descriptor(
        &self,
        channel: &str,
        description: &str,
        activity: ActivityBucket,
        automatic_join: AutomaticJoinEndpoint,
        expires_at_unix: u64,
    ) -> Result<PublicChannelDescriptor, SdkError> {
        self.embedded
            .public_channel_descriptor(
                channel,
                description,
                activity,
                automatic_join,
                expires_at_unix,
            )
            .await
    }

    async fn send_direct(
        &self,
        peer: &ContactCard,
        body: &[u8],
        via: Option<&ContactCard>,
    ) -> Result<(), SdkError> {
        self.check_primary_source(body)?;
        self.embedded.send_direct(peer, body, via).await?;
        self.persist().await
    }

    async fn send_direct_tracked(
        &self,
        peer: &ContactCard,
        body: &[u8],
        via: Option<&ContactCard>,
    ) -> Result<MessageId, SdkError> {
        self.check_primary_source(body)?;
        // Native tracked acceptance commits the ratchet and outbox atomically.
        // Do not introduce a second ambiguous save after returning its wire ID.
        self.embedded.send_direct_tracked(peer, body, via).await
    }

    async fn submit_volatile_opaque(
        &self,
        recipient: &ContactCard,
        content_type: &str,
        body: &[u8],
    ) -> Result<(), SdkError> {
        if self.central_primary.is_some() {
            self.check_primary_source(
                &gcoms_sdk::ApplicationMessage {
                    content_type: content_type.into(),
                    body: body.to_vec(),
                }
                .encode()?,
            )?;
        }
        // Node commits only ratchet/receipt metadata; pending contact frames remain RAM-only.
        self.embedded
            .submit_volatile_opaque(recipient, content_type, body)
            .await
    }

    async fn submit_durable_opaque(
        &self,
        recipient: &ContactCard,
        content_type: &str,
        body: &[u8],
    ) -> Result<(), SdkError> {
        if let Some((primary, _)) = &self.central_primary {
            let app = gcoms_sdk::ApplicationMessage {
                content_type: content_type.into(),
                body: body.to_vec(),
            };
            let wire = app.encode()?;
            if let Ok(route) = gcoms_sdk::component::RoutedApplication::decode(&wire) {
                self.check_primary_source(&wire)?;
                let own = self
                    .embedded
                    .contact_identity(&self.embedded.identity().contact_card)?;
                if self.embedded.contact_identity(recipient)? == own {
                    if !primary.contains(&route.source) {
                        return Err(SdkError::PermissionDenied);
                    }
                    return self.embedded.submit_local_component(&wire).await;
                }
            }
        }
        // The node commits the outgoing ratchet/outbox atomically before send.
        self.embedded
            .submit_durable_opaque(recipient, content_type, body)
            .await
    }

    async fn submit_local_component(&self, wire: &[u8]) -> Result<(), SdkError> {
        self.check_primary_source(wire)?;
        self.embedded.submit_local_component(wire).await
    }

    async fn application_inbox(
        &self,
        after: u64,
        limit: u16,
    ) -> Result<Vec<gcoms_sdk::ApplicationDelivery>, SdkError> {
        if self.central_primary.is_none() {
            return self.embedded.application_inbox(after, limit).await;
        }
        let mut cursor = after;
        let mut selected = Vec::new();
        loop {
            let page = self.embedded.application_inbox(cursor, limit).await?;
            if page.is_empty() {
                return Ok(selected);
            }
            for entry in page {
                if entry.sequence <= cursor {
                    return Err(SdkError::Protocol("non-monotonic primary inbox".into()));
                }
                cursor = entry.sequence;
                if !central_reserved(&self.central_primary, &entry.body) {
                    selected.push(entry);
                }
                if selected.len() == usize::from(limit) {
                    return Ok(selected);
                }
            }
        }
    }

    async fn commit_application(&self, sequence: u64, digest: [u8; 32]) -> Result<(), SdkError> {
        if self.central_primary.is_some() {
            let after = sequence.checked_sub(1).ok_or(SdkError::PermissionDenied)?;
            let page = self.embedded.application_inbox(after, 1).await?;
            if page.iter().any(|entry| {
                entry.sequence == sequence && central_reserved(&self.central_primary, &entry.body)
            }) {
                return Err(SdkError::PermissionDenied);
            }
        }
        self.embedded.commit_application(sequence, digest).await
    }

    async fn set_direct_presence(
        &self,
        peer: &ContactCard,
        mode: PresenceMode,
        lease_secs: u32,
        via: Option<&ContactCard>,
    ) -> Result<(), SdkError> {
        self.embedded
            .set_direct_presence(peer, mode, lease_secs, via)
            .await?;
        self.persist().await
    }

    async fn set_direct_presence_opt_in(
        &self,
        peer: &ContactCard,
        enabled: bool,
        via: Option<&ContactCard>,
    ) -> Result<(), SdkError> {
        self.embedded
            .set_direct_presence_opt_in(peer, enabled, via)
            .await?;
        self.persist().await
    }

    async fn create_channel(
        &self,
        channel: &str,
        display_name: &str,
        capacity: usize,
        visibility: ChannelVisibility,
    ) -> Result<ChannelId, SdkError> {
        let channel_id = self
            .embedded
            .create_channel(channel, display_name, capacity, visibility)
            .await?;
        self.persist().await?;
        Ok(channel_id)
    }

    async fn prepare_channel_join(&self, display_name: &str) -> Result<JoinRequest, SdkError> {
        let request = self.embedded.prepare_channel_join(display_name).await?;
        self.persist().await?;
        Ok(request)
    }

    async fn channel_key_package(&self, request: JoinRequest) -> Result<Blob, SdkError> {
        let package = self.embedded.channel_key_package(request).await?;
        self.persist().await?;
        Ok(package)
    }

    async fn admit_channel(
        &self,
        channel: &str,
        key_package: &Blob,
        member_name: &str,
    ) -> Result<Blob, SdkError> {
        let welcome = self
            .embedded
            .admit_channel(channel, key_package, member_name)
            .await?;
        self.persist().await?;
        Ok(welcome)
    }

    async fn recover_channel_route(
        &self,
        channel: &str,
        expected_channel_id: ChannelId,
        expected_epoch: u64,
        retained_welcome: &Blob,
        peer: &ContactCard,
    ) -> Result<MessageId, SdkError> {
        // The native owner checks the exact retained admission and commits the
        // original route-recovery wire before returning its bounded hop receipt.
        // Avoid a second ambiguous save or a new admission at this wrapper.
        self.embedded
            .recover_channel_route(
                channel,
                expected_channel_id,
                expected_epoch,
                retained_welcome,
                peer,
            )
            .await
    }

    async fn join_channel(
        &self,
        request: JoinRequest,
        channel: &str,
        visibility: ChannelVisibility,
        welcome: &Blob,
    ) -> Result<(), SdkError> {
        self.embedded
            .join_channel(request, channel, visibility, welcome)
            .await?;
        self.persist().await
    }

    async fn send_channel(&self, channel: &str, body: &[u8]) -> Result<(), SdkError> {
        // This remains the untracked native API. Its durable-outbox rule may
        // preserve local acceptance after a failed hop; the additional wrapper
        // barrier is still fallible. Propagate that error even when the exact
        // admitted send survives on disk. Neither result means delivery.
        self.embedded.send_channel(channel, body).await?;
        self.persist().await
    }

    async fn send_channel_tracked(
        &self,
        channel: &str,
        body: &[u8],
    ) -> Result<MessageId, SdkError> {
        self.embedded.send_channel_tracked(channel, body).await
    }

    async fn set_channel_presence(
        &self,
        channel: &str,
        mode: PresenceMode,
        lease_secs: u32,
    ) -> Result<(), SdkError> {
        self.embedded
            .set_channel_presence(channel, mode, lease_secs)
            .await?;
        self.persist().await
    }

    async fn set_channel_presence_opt_in(
        &self,
        channel: &str,
        enabled: bool,
    ) -> Result<(), SdkError> {
        self.embedded
            .set_channel_presence_opt_in(channel, enabled)
            .await?;
        self.persist().await
    }

    async fn send_channel_direct(
        &self,
        channel: &str,
        recipient_member_id: [u8; 32],
        body: &[u8],
    ) -> Result<MessageId, SdkError> {
        let message_id = self
            .embedded
            .send_channel_direct(channel, recipient_member_id, body)
            .await?;
        self.persist().await?;
        Ok(message_id)
    }

    async fn remove_channel_member(
        &self,
        channel: &str,
        member_id: [u8; 32],
    ) -> Result<(), SdkError> {
        self.embedded
            .remove_channel_member(channel, member_id)
            .await?;
        self.persist().await
    }
}

/// Build the operator-supplied FRWD target policy for
/// `--allow-frwd-private-cidr`. Each entry is `CIDR` (every target port in
/// the range) or `CIDR:PORT` (pinned to exactly that port). `None` keeps the
/// profile default (public targets only).
pub fn build_frwd_policy(
    cidrs: &[String],
    port: u16,
) -> Result<Option<gcoms_node::relay::FrwdTargetPolicy>, String> {
    let _ = port;
    if cidrs.is_empty() {
        return Ok(None);
    }
    let mut policy = gcoms_node::relay::FrwdTargetPolicy::new(false);
    for entry in cidrs {
        policy = match entry.rsplit_once(':') {
            Some((cidr, pin)) => policy
                .allow_private_cidr(
                    cidr,
                    pin.parse()
                        .map_err(|_| format!("invalid --allow-frwd-private-cidr port {entry}"))?,
                )
                .map_err(|error| format!("invalid --allow-frwd-private-cidr {entry}: {error}"))?,
            None => policy
                .allow_private_cidr_any_port(entry)
                .map_err(|error| format!("invalid --allow-frwd-private-cidr {entry}: {error}"))?,
        };
    }
    Ok(Some(policy))
}

async fn forward_protocol_events(
    mut source: broadcast::Receiver<ClientEvent>,
    sender: mpsc::Sender<ClientEvent>,
    mut failures: watch::Receiver<u64>,
    ownership: Option<CentralPartition>,
) {
    loop {
        let event = tokio::select! {
            biased;
            _ = sender.closed() => break,
            _ = failures.changed() => break,
            event = source.recv() => match event {
                Ok(event) => event,
                Err(broadcast::error::RecvError::Lagged(skipped)) => ClientEvent::EventsLagged { skipped },
                Err(broadcast::error::RecvError::Closed) => break,
            },
        };
        if matches!(&event, ClientEvent::DirectMessage { body, .. } if central_reserved(&ownership, body))
        {
            continue;
        }
        // Failure also interrupts a backpressured subscriber. Never leave it
        // waiting for the UI to drain before observing the failed barrier.
        tokio::select! {
            biased;
            _ = failures.changed() => break,
            result = sender.send(event) => if result.is_err() { break; },
        }
    }
}

fn central_reserved(ownership: &Option<CentralPartition>, body: &[u8]) -> bool {
    ownership.as_ref().is_some_and(|(_, scoped)| {
        gcoms_sdk::component::RoutedApplication::decode(body)
            .is_ok_and(|route| scoped.contains(&route.destination))
    })
}

#[cfg(test)]
mod persistence_tests;
#[cfg(test)]
mod shutdown_tests;

#[cfg(all(test, feature = "gc2-carrier"))]
mod protected_profile_tests {
    use super::*;

    #[tokio::test]
    async fn protected_profile_creates_and_reopens_the_carrier_instance() {
        let dir = tempfile::tempdir().unwrap();
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            std::fs::set_permissions(dir.path(), std::fs::Permissions::from_mode(0o700)).unwrap();
        }
        let profile = dir.path().join("carrier.gcprotocol");
        let listen: SocketAddr = "127.0.0.1:0".parse().unwrap();
        let first = ProtocolRuntime::create_protected(
            &profile,
            "carrier-passphrase",
            listen,
            None,
            None,
            &[],
        )
        .await
        .unwrap();
        let first_info = first
            .sdk_client()
            .embedded()
            .node()
            .current_info()
            .await
            .unwrap();
        first.shutdown().await.unwrap();
        let second = ProtocolRuntime::unlock_protected(
            &profile,
            "carrier-passphrase",
            listen,
            None,
            None,
            &[],
        )
        .await
        .unwrap();
        let second_info = second
            .sdk_client()
            .embedded()
            .node()
            .current_info()
            .await
            .unwrap();
        assert_eq!(first_info.identity_pk, second_info.identity_pk);
        second.shutdown().await.unwrap();
    }
}

#[cfg(test)]
mod frwd_policy_tests {
    use super::build_frwd_policy;

    #[test]
    fn empty_cidrs_keep_the_profile_default() {
        assert!(build_frwd_policy(&[], 8443).unwrap().is_none());
    }

    #[test]
    fn valid_cidrs_build_a_policy() {
        let policy = build_frwd_policy(&["192.168.0.0/16".to_string()], 8443)
            .unwrap()
            .expect("policy");
        let _ = policy;
    }

    #[test]
    fn pinned_cidr_port_entries_parse() {
        let policy = build_frwd_policy(&["192.168.1.139/32:24407".to_string()], 8443)
            .unwrap()
            .expect("policy");
        let _ = policy;
    }

    #[test]
    fn invalid_pinned_port_fails_closed() {
        let error = build_frwd_policy(&["192.168.1.0/24:notaport".to_string()], 8443).unwrap_err();
        assert!(error.contains("notaport"));
    }

    #[test]
    fn invalid_cidr_fails_closed() {
        let error = build_frwd_policy(&["not-a-cidr".to_string()], 8443).unwrap_err();
        assert!(error.contains("not-a-cidr"));
    }
}
