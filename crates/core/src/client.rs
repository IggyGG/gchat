//! Channel-first application API over the typed GC SDK.

use crate::model::{
    sort_home, sort_members, CachedDescriptor, ChannelRecord, HomeItem, MemberId, MemberRecord,
    Message, ScopedPmId, ScopedPmRecord,
};
use crate::runtime::ProtocolRuntime;
use crate::store::{ArchiveData, ArchiveStore, Store, StoreData};
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use base64::Engine;
use gcoms_node::node::{NodeConfig, NodeHandle};
use gcoms_node::proto::{info_from_b64, private_info_from_b64};
use gcoms_sdk::{
    ActivityBucket, AutomaticJoinEndpoint, Blob, CatalogResponse, ChannelId, ChannelRole,
    ChannelVisibility, ClientEvent, EmbeddedClient, GcClient, Identity, JoinRequest,
    PublicChannelDescriptor,
};
use reqwest::Url;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashSet};
use std::net::SocketAddr;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tokio::sync::{broadcast, mpsc};

pub use gcoms_node::proto::NodeInfo;
pub use gcoms_sdk::ClientEvent as NodeEvent;

const CATALOG_PAGE_SIZE: u16 = 100;
const CATALOG_MAX_PAGES: usize = 10;
const CATALOG_MAX_DESCRIPTORS: usize = 10_000;
const CATALOG_MAX_CURSOR_BYTES: usize = 1024;
const DESCRIPTOR_MAX_LIFETIME: u64 = 7 * 24 * 60 * 60;

pub fn b64_encode(bytes: &[u8]) -> String {
    gcoms_transport::encode_b64url(bytes)
}
pub fn b64_decode(value: &str) -> Option<Vec<u8>> {
    gcoms_transport::decode_b64url(value.trim())
}
pub fn decode_relay_card(card: &str) -> Result<NodeInfo, String> {
    private_info_from_b64(card.trim()).ok_or_else(|| "invalid relay card".to_string())
}

/// Decode a peer-visible contact card. Contact cards deliberately use the
/// public NodeInfo encoding, which excludes every relay-private capability;
/// only local bootstrap material carries private provisioning.
pub fn decode_contact_card(card: &str) -> Result<NodeInfo, String> {
    info_from_b64(card.trim()).ok_or_else(|| "invalid contact card".to_string())
}

struct Inner {
    sdk: Arc<dyn GcClient>,
    embedded_sdk: Option<EmbeddedClient>,
    identity: Identity,
    runtime_label: String,
    persistence: Persistence,
    data: Arc<Mutex<ArchiveData>>,
    catalog_urls: Mutex<Vec<Url>>,
    #[cfg(test)]
    http: Mutex<reqwest::Client>,
    catalog_https_only: AtomicBool,
    events: broadcast::Sender<ClientEvent>,
    dirty: AtomicBool,
    background: Mutex<Vec<tokio::task::JoinHandle<()>>>,
}

enum Persistence {
    /// Legacy combined store: the node lives in this process and the
    /// archive is saved inside the same encrypted file.
    Embedded {
        node: Box<NodeHandle>,
        _store: Arc<Store>,
        network: Option<gcoms_network_client::NetworkClient>,
    },
    /// Attached to an external daemon; only the chat archive is ours.
    Archive(ArchiveStore),
    /// Protocol runtime hosted in this process plus a separate archive:
    /// the same files a daemon would use, without the socket.
    Hosted {
        runtime: ProtocolRuntime,
        store: ArchiveStore,
    },
    /// Nothing persisted (UI snapshot tests).
    Memory,
}

#[derive(Clone)]
pub struct ClientHandle(Arc<Inner>);

#[derive(Serialize)]
struct CatalogJoinBody<'a> {
    display_pseudonym: &'a str,
    key_package_b64: String,
}

#[derive(Deserialize, Serialize)]
struct CatalogJoinResponse {
    channel: String,
    visibility: ChannelVisibility,
    welcome_b64: String,
}

impl ClientHandle {
    /// Service-owned archive over the already running protocol instance.
    /// The service is the only archive writer; attached UIs never open it.
    pub async fn open_service(
        path: &std::path::Path,
        passphrase: &str,
        runtime: &crate::runtime::ProtocolRuntime,
        create: bool,
    ) -> Result<Self, String> {
        let sdk = runtime.sdk_client();
        let identity = sdk.identity();
        let (store, data) = if create {
            ArchiveStore::create(path, passphrase, identity.safety_number.clone())?
        } else {
            ArchiveStore::open(path, passphrase)?
        };
        if data.daemon_safety_number != identity.safety_number {
            return Err("chat archive belongs to a different instance identity".into());
        }
        let embedded = sdk.embedded();
        Self::finish(
            Arc::new(sdk),
            Some(embedded),
            identity,
            "gcd".into(),
            Persistence::Archive(store),
            Arc::new(Mutex::new(data)),
            true,
        )
        .await
    }

    /// Consistent copy for the service projection, including read-only archives.
    pub fn archive_snapshot(&self) -> ArchiveData {
        self.0.data.lock().unwrap().clone()
    }

    pub fn sdk_client(&self) -> Result<EmbeddedClient, String> {
        self.0
            .embedded_sdk
            .clone()
            .ok_or_else(|| "client uses an IPC runtime".into())
    }

    pub async fn create_profile(
        path: &std::path::Path,
        passphrase: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        inbox_relay: Option<NodeInfo>,
    ) -> Result<Self, String> {
        let (store, data) = Store::create(path, passphrase)?;
        Self::boot(
            store,
            data,
            listen,
            advertise,
            inbox_relay,
            gcoms_node::node::NodeProfile::Production,
        )
        .await
    }

    /// Explicit direct transport for disposable local integration fixtures.
    #[doc(hidden)]
    pub async fn create_profile_fixture(
        path: &std::path::Path,
        passphrase: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        inbox_relay: Option<NodeInfo>,
    ) -> Result<Self, String> {
        let (store, data) = Store::create(path, passphrase)?;
        Self::boot(
            store,
            data,
            listen,
            advertise,
            inbox_relay,
            gcoms_node::node::NodeProfile::fixture(),
        )
        .await
    }

    pub async fn unlock(
        path: &std::path::Path,
        passphrase: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        inbox_relay: Option<NodeInfo>,
    ) -> Result<Self, String> {
        let (store, data) = Store::open(path, passphrase)?;
        Self::boot(
            store,
            data,
            listen,
            advertise,
            inbox_relay,
            gcoms_node::node::NodeProfile::Production,
        )
        .await
    }

    /// Explicit direct transport for disposable local integration fixtures.
    #[doc(hidden)]
    pub async fn unlock_fixture(
        path: &std::path::Path,
        passphrase: &str,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        inbox_relay: Option<NodeInfo>,
    ) -> Result<Self, String> {
        let (store, data) = Store::open(path, passphrase)?;
        Self::boot(
            store,
            data,
            listen,
            advertise,
            inbox_relay,
            gcoms_node::node::NodeProfile::fixture(),
        )
        .await
    }

    async fn boot(
        store: Store,
        data: StoreData,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        inbox_relay: Option<NodeInfo>,
        profile: gcoms_node::node::NodeProfile,
    ) -> Result<Self, String> {
        let StoreData {
            identity_seed,
            archive,
            node_state,
        } = data;
        let network = if matches!(profile, gcoms_node::node::NodeProfile::Production) {
            Some(gcoms_network_client::NetworkClient::open(
                &store.network_directory(),
                crate::network::installed()?,
            )?)
        } else {
            None
        };
        let mut routing = gcoms_node::node::RoutingConfig::from_environment()?;
        if network.is_some() && listen.port() == 0 {
            routing.connectivity = Some(gcoms_node::connectivity::ConnectivityConfig {
                state: Some(Arc::new(gcoms_node::connectivity::PortState::open(
                    &store.network_directory(),
                    &identity_seed,
                )?)),
                ..Default::default()
            });
        }
        let store = Arc::new(store);
        let archive = Arc::new(Mutex::new(archive));
        let sink_store = store.clone();
        let sink_archive = archive.clone();
        let sink = Arc::new(move |state| {
            sink_store.save(&StoreData {
                identity_seed,
                archive: sink_archive
                    .lock()
                    .map_err(|_| "client archive lock poisoned")?
                    .clone(),
                node_state: Some(state),
            })
        });
        let config = NodeConfig {
            seed: identity_seed,
            listen,
            control: None,
            advertise,
            inbox_relay,
            profile,
            alias_lifecycle: Default::default(),
        };
        let node = if network.is_some() {
            gcoms_node::node::start_persistent_restored_with_policy_and_routing(
                config,
                None,
                routing,
                sink,
                node_state.as_deref(),
            )
            .await?
        } else {
            gcoms_node::node::start_persistent_restored(config, None, sink, node_state.as_deref())
                .await?
        };
        let sdk = EmbeddedClient::new(node.clone());
        let runtime_label = node.info.primary().map_or_else(
            || "unavailable".into(),
            |alias| alias.target.address.to_string(),
        );
        Self::finish(
            Arc::new(sdk.clone()),
            Some(sdk.clone()),
            sdk.identity(),
            runtime_label,
            Persistence::Embedded {
                node: Box::new(node),
                _store: store,
                network,
            },
            archive,
            true,
        )
        .await
    }

    #[cfg(any(unix, windows))]
    pub async fn connect_daemon(
        path: &std::path::Path,
        passphrase: &str,
        socket: &std::path::Path,
        create: bool,
    ) -> Result<Self, String> {
        use gcoms_sdk::ipc::Capability;
        let sdk = gcoms_sdk::IpcClient::connect(
            socket,
            "gchat",
            vec![
                Capability::IdentityRead,
                Capability::DirectMessage,
                Capability::ChannelMember,
                Capability::ChannelAdmin,
                Capability::EventRead,
                Capability::CatalogAccess,
            ],
        )
        .await
        .map_err(|error| error.to_string())?;
        let identity = sdk.identity();
        let (store, data) = if create {
            ArchiveStore::create(path, passphrase, identity.safety_number.clone())?
        } else {
            ArchiveStore::open(path, passphrase)?
        };
        if data.daemon_safety_number != identity.safety_number {
            return Err("chat archive belongs to a different daemon identity".into());
        }
        Self::finish(
            Arc::new(sdk),
            None,
            identity,
            "gcd".into(),
            Persistence::Archive(store),
            Arc::new(Mutex::new(data)),
            true,
        )
        .await
    }

    /// Use a protocol runtime hosted in this process, with the chat archive
    /// at `path`. Mirrors `connect_daemon` without a socket: the on-disk
    /// layout is identical to a daemon plus an attached client.
    pub async fn open_hosted(
        path: &std::path::Path,
        passphrase: &str,
        runtime: ProtocolRuntime,
        create: bool,
    ) -> Result<Self, String> {
        let sdk = runtime.sdk_client();
        let identity = sdk.identity();
        let (store, data) = if create {
            ArchiveStore::create(path, passphrase, identity.safety_number.clone())?
        } else {
            ArchiveStore::open(path, passphrase)?
        };
        if data.daemon_safety_number != identity.safety_number {
            return Err("chat archive belongs to a different identity".into());
        }
        let runtime_label = runtime.listen_label();
        let embedded = sdk.embedded();
        Self::finish(
            Arc::new(sdk),
            Some(embedded),
            identity,
            runtime_label,
            Persistence::Hosted { runtime, store },
            Arc::new(Mutex::new(data)),
            true,
        )
        .await
    }

    /// A client over any SDK with a prepared archive and no persistence.
    /// The archive is taken as-is (no reconcile), so UI tests can stage
    /// channels and messages without a node.
    pub async fn in_memory(sdk: Arc<dyn GcClient>, data: ArchiveData) -> Result<Self, String> {
        let identity = sdk.identity();
        Self::finish(
            sdk,
            None,
            identity,
            "memory".into(),
            Persistence::Memory,
            Arc::new(Mutex::new(data)),
            false,
        )
        .await
    }

    async fn finish(
        sdk: Arc<dyn GcClient>,
        embedded_sdk: Option<EmbeddedClient>,
        identity: Identity,
        runtime_label: String,
        persistence: Persistence,
        data: Arc<Mutex<ArchiveData>>,
        reconcile: bool,
    ) -> Result<Self, String> {
        let (events, _) = broadcast::channel(256);
        let inner = Arc::new(Inner {
            sdk,
            embedded_sdk,
            identity,
            runtime_label,
            persistence,
            data,
            catalog_urls: Mutex::new(Vec::new()),
            #[cfg(test)]
            http: Mutex::new(
                crate::bootstrap::http_builder(true, Duration::from_secs(5))
                    .build()
                    .map_err(|e| e.to_string())?,
            ),
            catalog_https_only: AtomicBool::new(true),
            events,
            dirty: AtomicBool::new(false),
            background: Mutex::new(Vec::new()),
        });
        let handle = Self(inner);
        if reconcile {
            handle.reconcile_channels().await?;
        }
        spawn_archiver(&handle.0);
        spawn_periodic_save(&handle.0);
        Ok(handle)
    }

    pub fn safety_number(&self) -> &str {
        &self.0.identity.safety_number
    }
    /// The public contact card (base64 text) peers use to reach this identity.
    pub fn contact_card(&self) -> String {
        String::from_utf8_lossy(&self.0.identity.contact_card.0).into_owned()
    }
    pub async fn current_identity(&self) -> Result<Identity, String> {
        self.0
            .sdk
            .refresh_identity()
            .await
            .map_err(|error| error.to_string())
    }
    pub fn listen_addr(&self) -> String {
        self.0.runtime_label.clone()
    }
    /// Configured public catalog base URLs (normalized, trailing slash).
    pub fn catalog_urls(&self) -> Vec<String> {
        self.0
            .catalog_urls
            .lock()
            .unwrap()
            .iter()
            .map(Url::to_string)
            .collect()
    }
    pub fn subscribe(&self) -> mpsc::Receiver<ClientEvent> {
        let mut source = self.0.events.subscribe();
        let (send, receive) = mpsc::channel(256);
        tokio::spawn(async move {
            loop {
                match source.recv().await {
                    Ok(event) => {
                        if send.send(event).await.is_err() {
                            break;
                        }
                    }
                    Err(broadcast::error::RecvError::Lagged(skipped)) => {
                        if send
                            .send(ClientEvent::EventsLagged { skipped })
                            .await
                            .is_err()
                        {
                            break;
                        }
                    }
                    Err(broadcast::error::RecvError::Closed) => break,
                }
            }
        });
        receive
    }

    /// Backend bootstrap used by hosted frontends; private introductions never enter UI state.
    pub async fn bootstrap_routing(&self, urls: &[String]) -> Result<String, String> {
        let node = self.sdk_client()?.node().clone();
        let network = match &self.0.persistence {
            Persistence::Embedded { network, .. } => network.clone(),
            Persistence::Hosted { runtime, .. } => runtime.network_client(),
            _ => None,
        };
        crate::bootstrap::recover_network(
            &node,
            network.as_ref(),
            urls,
            tokio::time::Instant::now() + Duration::from_secs(120),
        )
        .await?;
        let info = node.current_info().await?;
        Ok(info
            .primary()
            .ok_or("inbox routing is recovering")?
            .target
            .address
            .to_string())
    }

    async fn catalog_http(
        &self,
        method: &str,
        url: Url,
        body: Vec<u8>,
    ) -> Result<gcoms_sdk::CatalogHttpResponse, String> {
        #[cfg(test)]
        if !self.0.catalog_https_only.load(Ordering::Relaxed) {
            let http = self.0.http.lock().unwrap().clone();
            let mut response = http
                .request(method.parse().map_err(|_| "invalid HTTP method")?, url)
                .header("content-type", "application/json")
                .body(body)
                .send()
                .await
                .map_err(|e| e.to_string())?;
            let status = response.status().as_u16();
            let mut body = Vec::new();
            while let Some(chunk) = response.chunk().await.map_err(|e| e.to_string())? {
                if chunk.len() > (4 * 1024 * 1024usize).saturating_sub(body.len()) {
                    return Err("catalog response exceeds limit".into());
                }
                body.extend_from_slice(&chunk);
            }
            return Ok(gcoms_sdk::CatalogHttpResponse { status, body });
        }
        gcoms_routing::catalog::validate(method, url.as_str(), &body).map_err(|e| e.to_string())?;
        let mut origins: Vec<String> = self
            .0
            .catalog_urls
            .lock()
            .unwrap()
            .iter()
            .filter_map(|u| u.host_str().map(str::to_owned))
            .collect();
        origins.push(url.host_str().ok_or("catalog host is absent")?.to_owned());
        origins.sort();
        origins.dedup();
        self.0
            .sdk
            .configure_catalog_origins(origins)
            .await
            .map_err(|e| e.to_string())?;
        self.0
            .sdk
            .catalog_request(gcoms_sdk::CatalogHttpRequest {
                method: method.into(),
                url: url.into(),
                body,
            })
            .await
            .map_err(|e| e.to_string())
    }

    pub async fn configure_catalogs(&self, values: &[String]) -> Result<(), String> {
        let mut urls = Vec::new();
        for value in values {
            let mut url = Url::parse(value).map_err(|e| format!("invalid catalog URL: {e}"))?;
            let https_only = self.0.catalog_https_only.load(Ordering::Relaxed);
            if (https_only && url.scheme() != "https")
                || (!https_only && url.scheme() != "https" && url.scheme() != "http")
                || url.host_str().is_none()
                || url.cannot_be_a_base()
                || url.query().is_some()
                || url.fragment().is_some()
                || !url.username().is_empty()
                || url.password().is_some()
            {
                return Err("catalog URLs must be credential-free HTTPS base URLs".into());
            }
            url.set_path(&format!("{}/", url.path().trim_end_matches('/')));
            urls.push(url);
        }
        *self.0.catalog_urls.lock().unwrap() = urls;
        self.refresh_catalogs().await
    }

    #[cfg(test)]
    fn allow_test_http(&self) {
        self.0.catalog_https_only.store(false, Ordering::Relaxed);
        *self.0.http.lock().unwrap() = reqwest::Client::builder()
            .timeout(Duration::from_secs(5))
            .redirect(reqwest::redirect::Policy::none())
            .build()
            .unwrap();
    }

    pub async fn reconcile_channels(&self) -> Result<(), String> {
        let joined = self
            .0
            .sdk
            .list_channels()
            .await
            .map_err(|e| e.to_string())?;
        let active_ids = joined
            .iter()
            .map(|channel| channel.id)
            .collect::<HashSet<_>>();
        {
            let mut data = self.0.data.lock().unwrap();
            let lost = data
                .channels
                .iter_mut()
                .filter_map(|channel| {
                    if channel.active && !active_ids.contains(&channel.id) {
                        channel.active = false;
                        Some(channel.id)
                    } else {
                        None
                    }
                })
                .collect::<HashSet<_>>();
            for pm in &mut data.scoped_pms {
                if lost.contains(&pm.id.channel_id) {
                    pm.active = false;
                }
            }
        }
        for joined in joined {
            let roster = self
                .0
                .sdk
                .channel_roster(&joined.channel)
                .await
                .map_err(|e| e.to_string())?;
            let self_id = roster
                .iter()
                .find(|member| member.is_self)
                .map(|member| MemberId(member.member_id));
            let members = roster
                .into_iter()
                .map(|member| MemberRecord {
                    id: MemberId(member.member_id),
                    display_name: member.display_name,
                    join_order: member.join_order,
                    joined_at_unix: member.joined_at_unix,
                    is_self: member.is_self,
                })
                .collect::<Vec<_>>();
            let mut data = self.0.data.lock().unwrap();
            let current = data.channels.iter_mut().find(|channel| {
                channel.active && channel.id == joined.id && channel.self_member_id == self_id
            });
            if let Some(channel) = current {
                channel.protocol_name = joined.channel;
                channel.visibility = joined.visibility;
                channel.role = joined.role;
                channel.members = members;
            } else {
                data.channels.push(ChannelRecord {
                    id: joined.id,
                    protocol_name: joined.channel.clone(),
                    title: joined.channel,
                    visibility: joined.visibility,
                    role: joined.role,
                    joined_at_unix: now_unix(),
                    active: true,
                    self_member_id: self_id,
                    members,
                    messages: Vec::new(),
                });
            }
        }
        self.0.dirty.store(true, Ordering::Relaxed);
        Ok(())
    }

    pub async fn refresh_catalogs(&self) -> Result<(), String> {
        let urls = self.0.catalog_urls.lock().unwrap().clone();
        if urls.is_empty() {
            return Ok(());
        }
        let now = now_unix();
        let mut valid = BTreeMap::<[u8; 32], CachedDescriptor>::new();
        let mut successful = false;
        let mut last_error: Option<String> = None;
        for base in urls {
            let mut cursor: Option<String> = None;
            let mut cursors = HashSet::new();
            for page_index in 0..CATALOG_MAX_PAGES {
                let mut url = base.join("v1/catalog").map_err(|e| e.to_string())?;
                url.query_pairs_mut()
                    .append_pair("limit", &CATALOG_PAGE_SIZE.to_string());
                if let Some(cursor) = &cursor {
                    url.query_pairs_mut().append_pair("cursor", cursor);
                }
                let response = match self.catalog_http("GET", url, Vec::new()).await {
                    Ok(response) => response,
                    Err(error) => {
                        last_error = Some(format!("{base}: {error}"));
                        break;
                    }
                };
                if !(200..300).contains(&response.status) {
                    last_error = Some(format!("{base}: HTTP {}", response.status));
                    break;
                }
                let page: CatalogResponse = serde_json::from_slice(&response.body)
                    .map_err(|e| format!("invalid catalog response: {e}"))?;
                if page.descriptors.len() > usize::from(CATALOG_PAGE_SIZE) {
                    return Err("catalog page exceeds limit".into());
                }
                successful = true;
                for descriptor in page.descriptors {
                    if validate_descriptor(
                        &descriptor,
                        now,
                        self.0.catalog_https_only.load(Ordering::Relaxed),
                    )
                    .is_ok()
                    {
                        let cached = CachedDescriptor {
                            published_at_unix: descriptor
                                .expires_at_unix
                                .saturating_sub(DESCRIPTOR_MAX_LIFETIME),
                            descriptor,
                        };
                        match valid.get(&cached.descriptor.channel_id.0) {
                            Some(old)
                                if old.descriptor.expires_at_unix
                                    >= cached.descriptor.expires_at_unix => {}
                            _ => {
                                valid.insert(cached.descriptor.channel_id.0, cached);
                            }
                        }
                    }
                    if valid.len() >= CATALOG_MAX_DESCRIPTORS {
                        break;
                    }
                }
                let Some(next) = page.next_cursor else { break };
                if next.is_empty() || next.len() > CATALOG_MAX_CURSOR_BYTES {
                    return Err("catalog pagination cursor is out of bounds".into());
                }
                if !cursors.insert(next.clone()) {
                    return Err("catalog repeated pagination cursor".into());
                }
                if page_index + 1 == CATALOG_MAX_PAGES {
                    return Err("catalog pagination exceeds page limit".into());
                }
                cursor = Some(next);
            }
        }
        let mut data = self.0.data.lock().unwrap();
        if successful {
            data.public_descriptors = valid.into_values().collect();
        }
        data.public_descriptors.retain(|cached| {
            validate_descriptor(
                &cached.descriptor,
                now,
                self.0.catalog_https_only.load(Ordering::Relaxed),
            )
            .is_ok()
        });
        self.0.dirty.store(true, Ordering::Relaxed);
        if successful {
            Ok(())
        } else {
            // Cached descriptors stay usable; the caller decides how loudly
            // to say the catalogs were unreachable.
            Err(last_error.unwrap_or_else(|| "no catalog responded".into()))
        }
    }

    pub fn home_items(&self) -> Vec<HomeItem> {
        let now = now_unix();
        let data = self.0.data.lock().unwrap();
        let joined = data
            .channels
            .iter()
            .filter(|channel| channel.active)
            .map(|channel| channel.id)
            .collect::<HashSet<_>>();
        let mut items = data
            .channels
            .iter()
            .filter(|channel| channel.active)
            .cloned()
            .map(HomeItem::Joined)
            .chain(
                data.public_descriptors
                    .iter()
                    .filter(|cached| {
                        !joined.contains(&cached.descriptor.channel_id)
                            && validate_descriptor(
                                &cached.descriptor,
                                now,
                                self.0.catalog_https_only.load(Ordering::Relaxed),
                            )
                            .is_ok()
                    })
                    .cloned()
                    .map(HomeItem::Public),
            )
            .chain(
                data.scoped_pms
                    .iter()
                    .filter(|pm| pm.active)
                    .cloned()
                    .map(HomeItem::ScopedPm),
            )
            .collect::<Vec<_>>();
        sort_home(&mut items, now);
        items
    }

    pub fn channel(&self, id: ChannelId) -> Option<ChannelRecord> {
        self.0
            .data
            .lock()
            .unwrap()
            .channels
            .iter()
            .find(|channel| channel.active && channel.id == id)
            .cloned()
    }

    pub fn channel_protocol_name(&self, id: ChannelId) -> Option<String> {
        self.0
            .data
            .lock()
            .unwrap()
            .channels
            .iter()
            .find(|channel| channel.id == id)
            .map(|channel| channel.protocol_name.clone())
    }

    pub fn members(&self, id: ChannelId) -> Vec<MemberRecord> {
        let data = self.0.data.lock().unwrap();
        let Some(channel) = data
            .channels
            .iter()
            .find(|channel| channel.active && channel.id == id)
        else {
            return Vec::new();
        };
        let mut members = channel
            .members
            .iter()
            .filter(|member| !member.is_self)
            .cloned()
            .collect::<Vec<_>>();
        let pms = data
            .scoped_pms
            .iter()
            .filter(|pm| pm.id.channel_id == id)
            .cloned()
            .collect::<Vec<_>>();
        sort_members(&mut members, &pms, &channel.messages);
        members
    }

    pub fn scoped_pm(&self, id: ScopedPmId) -> Option<ScopedPmRecord> {
        self.0
            .data
            .lock()
            .unwrap()
            .scoped_pms
            .iter()
            .find(|pm| pm.id == id)
            .cloned()
    }

    pub fn open_scoped_pm(
        &self,
        channel_id: ChannelId,
        remote: MemberId,
    ) -> Result<ScopedPmId, String> {
        let mut data = self.0.data.lock().unwrap();
        let channel = data
            .channels
            .iter()
            .find(|channel| channel.active && channel.id == channel_id)
            .ok_or("channel is not active")?;
        let self_member_id = channel
            .self_member_id
            .ok_or("channel roster has no self member")?;
        let name = channel
            .members
            .iter()
            .find(|member| member.id == remote && !member.is_self)
            .ok_or("member is no longer in channel")?
            .display_name
            .clone();
        let id = ScopedPmId {
            channel_id,
            self_member_id,
            remote_member_id: remote,
        };
        if !data.scoped_pms.iter().any(|pm| pm.id == id) {
            data.scoped_pms.push(ScopedPmRecord {
                id,
                remote_display_name: name,
                messages: Vec::new(),
                active: true,
            });
            self.0.dirty.store(true, Ordering::Relaxed);
        }
        Ok(id)
    }

    pub async fn create_channel(
        &self,
        channel: &str,
        display: &str,
        capacity: usize,
        visibility: ChannelVisibility,
    ) -> Result<ChannelId, String> {
        let id = self
            .0
            .sdk
            .create_channel(channel, display, capacity, visibility)
            .await
            .map_err(|e| e.to_string())?;
        self.reconcile_channels().await?;
        Ok(id)
    }

    pub async fn publish_channel(
        &self,
        channel_id: ChannelId,
        description: &str,
        catalog: &str,
    ) -> Result<(), String> {
        let channel = self.channel(channel_id).ok_or("channel is not active")?;
        if channel.role != ChannelRole::Owner || channel.visibility != ChannelVisibility::Public {
            return Err("only a public channel owner can publish".into());
        }
        let mut base = Url::parse(catalog).map_err(|e| e.to_string())?;
        let https_only = self.0.catalog_https_only.load(Ordering::Relaxed);
        if (https_only && base.scheme() != "https")
            || (!https_only && base.scheme() != "https" && base.scheme() != "http")
            || base.host_str().is_none()
            || base.cannot_be_a_base()
            || base.query().is_some()
            || base.fragment().is_some()
            || !base.username().is_empty()
            || base.password().is_some()
        {
            return Err("catalog must be credential-free HTTPS".into());
        }
        base.set_path(&format!("{}/", base.path().trim_end_matches('/')));
        let endpoint = base
            .join(&format!(
                "v1/channels/{}/join",
                URL_SAFE_NO_PAD.encode(channel_id.0)
            ))
            .map_err(|e| e.to_string())?;
        let descriptor = self
            .0
            .sdk
            .public_channel_descriptor(
                &channel.protocol_name,
                description,
                ActivityBucket::None,
                AutomaticJoinEndpoint {
                    catalog: base.to_string(),
                    endpoint: endpoint.to_string(),
                },
                now_unix() + DESCRIPTOR_MAX_LIFETIME,
            )
            .await
            .map_err(|e| e.to_string())?;
        validate_descriptor(&descriptor, now_unix(), https_only)?;
        let response = self
            .catalog_http(
                "PUT",
                base.join("v1/descriptors").map_err(|e| e.to_string())?,
                serde_json::to_vec(&descriptor).map_err(|e| e.to_string())?,
            )
            .await?;
        if !(200..300).contains(&response.status) {
            return Err(format!("catalog publish failed: {}", response.status));
        }
        Ok(())
    }

    pub async fn join_public(
        &self,
        descriptor: &PublicChannelDescriptor,
        display: &str,
    ) -> Result<(), String> {
        validate_descriptor(
            descriptor,
            now_unix(),
            self.0.catalog_https_only.load(Ordering::Relaxed),
        )?;
        let request = self
            .0
            .sdk
            .prepare_channel_join(display)
            .await
            .map_err(|e| e.to_string())?;
        let package = self
            .0
            .sdk
            .channel_key_package(request)
            .await
            .map_err(|e| e.to_string())?;
        let response = self
            .catalog_http(
                "POST",
                Url::parse(&descriptor.automatic_join.endpoint).map_err(|e| e.to_string())?,
                serde_json::to_vec(&CatalogJoinBody {
                    display_pseudonym: display,
                    key_package_b64: URL_SAFE_NO_PAD.encode(&package.0),
                })
                .map_err(|e| e.to_string())?,
            )
            .await?;
        if !(200..300).contains(&response.status) {
            return Err(format!("catalog join failed: {}", response.status));
        }
        let joined: CatalogJoinResponse = serde_json::from_slice(&response.body)
            .map_err(|e| format!("invalid catalog join response: {e}"))?;
        if joined.visibility != ChannelVisibility::Public {
            return Err("catalog returned non-public channel".into());
        }
        let welcome = URL_SAFE_NO_PAD
            .decode(joined.welcome_b64)
            .map_err(|_| "catalog returned invalid welcome")?;
        self.0
            .sdk
            .join_channel(
                request,
                &joined.channel,
                ChannelVisibility::Public,
                &Blob(welcome),
            )
            .await
            .map_err(|e| e.to_string())?;
        self.reconcile_channels().await
    }

    pub async fn prepare_join(&self, display: &str) -> Result<(u64, Vec<u8>), String> {
        let request = self
            .0
            .sdk
            .prepare_channel_join(display)
            .await
            .map_err(|e| e.to_string())?;
        let package = self
            .0
            .sdk
            .channel_key_package(request)
            .await
            .map_err(|e| e.to_string())?;
        Ok((request.0, package.0))
    }
    pub async fn admit(
        &self,
        channel: &str,
        package: &[u8],
        member: &str,
    ) -> Result<Vec<u8>, String> {
        self.0
            .sdk
            .admit_channel(channel, &Blob(package.to_vec()), member)
            .await
            .map(|welcome| welcome.0)
            .map_err(|e| e.to_string())
    }
    pub async fn join_channel(
        &self,
        request: u64,
        channel: &str,
        _display: &str,
        welcome: &[u8],
    ) -> Result<(), String> {
        self.0
            .sdk
            .join_channel(
                JoinRequest(request),
                channel,
                ChannelVisibility::Private,
                &Blob(welcome.to_vec()),
            )
            .await
            .map_err(|e| e.to_string())?;
        self.reconcile_channels().await
    }

    /// Owner: mint a single-use invite link for a channel this node owns. The
    /// link carries the owner's public contact card so a friend can redeem it
    /// over the relay with no hand-carried key package. `ttl_secs` bounds how
    /// long the invite is valid. Hosted runtime only (an IPC/daemon-attached
    /// client has no in-process node and returns "client uses an IPC runtime").
    pub async fn create_invite(&self, id: ChannelId, ttl_secs: u64) -> Result<String, String> {
        let channel = self
            .channel_protocol_name(id)
            .ok_or("channel is not active")?;
        let embedded = self.sdk_client()?;
        let node = embedded.node();
        let (invite_id, secret, expiry) = node
            .create_channel_invite(&channel, ttl_secs)
            .await
            .map_err(|e| e.to_string())?;
        let owner = node.current_info().await.map_err(|e| e.to_string())?;
        let invite = gcoms_node::channel_invite::ChannelInvite {
            owner,
            channel,
            id: invite_id,
            secret,
            expiry,
        };
        let link = if node.uses_onion_routing() {
            invite.to_link_with_bootstrap(node.routing_bootstrap()?)
        } else {
            invite.to_link()
        };
        link.ok_or_else(|| "invite is too large to encode".into())
    }

    /// Friend: redeem an invite link. Prepares a key package, contacts the
    /// owner over the relay (waiting up to `timeout_secs` if they are offline),
    /// and joins the channel on success. Hosted runtime only (see
    /// `create_invite`).
    pub async fn join_with_invite(
        &self,
        link: &str,
        display: &str,
        timeout_secs: u64,
    ) -> Result<String, String> {
        let envelope = gcoms_node::channel_invite::InviteEnvelope::from_link(link.trim())
            .ok_or("that does not look like a valid invite link")?;
        let invite = envelope.invite;
        let remaining = invite.expiry.saturating_sub(now_unix()).min(timeout_secs);
        if remaining == 0 {
            return Err("invite expired or join deadline elapsed".into());
        }
        let deadline = tokio::time::Instant::now() + Duration::from_secs(remaining);
        let embedded = self.sdk_client()?;
        let node = embedded.node();
        if let Some(bootstrap) = envelope.bootstrap {
            node.install_routing_bootstrap(bootstrap).await?;
        }
        node.wait_for_inbox(deadline).await?;
        tokio::time::timeout_at(deadline, async {
            // Prepare our own key package for this channel.
            let request = node
                .prepare_channel_join(display)
                .await
                .map_err(|e| e.to_string())?;
            let package = node
                .channel_key_package(request)
                .await
                .map_err(|e| e.to_string())?;
            let welcome = node
                .redeem_invite_remote(
                    invite.owner.clone(),
                    &invite.channel,
                    display,
                    &package,
                    invite.id,
                    invite.secret,
                    deadline
                        .saturating_duration_since(tokio::time::Instant::now())
                        .as_secs(),
                )
                .await?;
            node.join_channel(
                request,
                &invite.channel,
                gcoms_node::channel::ChannelVisibility::Private,
                &welcome,
            )
            .await
            .map_err(|e| e.to_string())?;
            self.reconcile_channels().await?;
            Ok(invite.channel)
        })
        .await
        .map_err(|_| "invite join deadline elapsed".to_owned())?
    }
    pub async fn send_channel(&self, id: ChannelId, text: &str) -> Result<(), String> {
        let channel = self.channel(id).ok_or("channel is not active")?;
        self.0
            .sdk
            .send_channel(&channel.protocol_name, text.as_bytes())
            .await
            .map_err(|e| e.to_string())?;
        let mut data = self.0.data.lock().unwrap();
        if let Some(channel) = data
            .channels
            .iter_mut()
            .find(|candidate| candidate.active && candidate.id == id)
        {
            channel.messages.push(Message {
                id: fresh_id(),
                ts_unix: now_unix(),
                sender_member_id: channel.self_member_id,
                sender_name: channel
                    .members
                    .iter()
                    .find(|m| m.is_self)
                    .map(|m| m.display_name.clone())
                    .unwrap_or_else(|| "you".into()),
                mine: true,
                text: text.into(),
            });
        }
        self.0.dirty.store(true, Ordering::Relaxed);
        Ok(())
    }
    pub async fn send_scoped_pm(&self, id: ScopedPmId, text: &str) -> Result<(), String> {
        let channel = self.channel(id.channel_id).ok_or("channel is not active")?;
        let message_id = self
            .0
            .sdk
            .send_channel_direct(
                &channel.protocol_name,
                id.remote_member_id.0,
                text.as_bytes(),
            )
            .await
            .map_err(|e| e.to_string())?;
        let mut data = self.0.data.lock().unwrap();
        let pm = data
            .scoped_pms
            .iter_mut()
            .find(|pm| pm.id == id && pm.active)
            .ok_or("scoped PM is not active")?;
        pm.messages.push(Message {
            id: message_id.0,
            ts_unix: now_unix(),
            sender_member_id: Some(id.self_member_id),
            sender_name: channel
                .members
                .iter()
                .find(|m| m.is_self)
                .map(|m| m.display_name.clone())
                .unwrap_or_else(|| "you".into()),
            mine: true,
            text: text.into(),
        });
        self.0.dirty.store(true, Ordering::Relaxed);
        Ok(())
    }
    pub async fn remove_member(&self, id: ChannelId, member: MemberId) -> Result<(), String> {
        let channel = self.channel(id).ok_or("channel is not active")?;
        self.0
            .sdk
            .remove_channel_member(&channel.protocol_name, member.0)
            .await
            .map_err(|e| e.to_string())
    }
    pub fn legacy_archive(&self) -> crate::model::LegacyArchive {
        self.0.data.lock().unwrap().legacy.clone()
    }
    pub fn archived_channels(&self) -> Vec<ChannelRecord> {
        self.0
            .data
            .lock()
            .unwrap()
            .channels
            .iter()
            .filter(|channel| !channel.active)
            .cloned()
            .collect()
    }
    pub async fn save(&self) -> Result<(), String> {
        save_inner(&self.0).await
    }
    pub async fn stop_background(&self) {
        let tasks = self
            .0
            .background
            .lock()
            .unwrap()
            .drain(..)
            .collect::<Vec<_>>();
        for task in &tasks {
            task.abort();
        }
        for task in tasks {
            let _ = task.await;
        }
    }

    pub async fn shutdown(self) -> Result<(), String> {
        self.stop_background().await;
        let save = self.save().await;
        match &self.0.persistence {
            Persistence::Embedded { node, .. } => node.shutdown().await,
            Persistence::Hosted { runtime, .. } => {
                // Persists node state, then stops the node.
                runtime.clone().shutdown().await?;
            }
            Persistence::Archive(_) | Persistence::Memory => {}
        }
        save
    }
}

fn validate_descriptor(
    descriptor: &PublicChannelDescriptor,
    now: u64,
    https_only: bool,
) -> Result<(), String> {
    if !descriptor.verify_at(now) {
        return Err("invalid or expired public descriptor".into());
    }
    if descriptor.expires_at_unix > now.saturating_add(DESCRIPTOR_MAX_LIFETIME)
        || descriptor.capacity > 1_000_000
        || descriptor.title.len() > 128
        || descriptor.description.len() > 1024
        || descriptor.owner_public_key.len() > 4096
        || descriptor.signature.len() > 4096
    {
        return Err("public descriptor bounds exceeded".into());
    }
    let catalog = Url::parse(&descriptor.automatic_join.catalog)
        .map_err(|_| "invalid descriptor catalog URL")?;
    let endpoint = Url::parse(&descriptor.automatic_join.endpoint)
        .map_err(|_| "invalid descriptor join endpoint")?;
    if (https_only && catalog.scheme() != "https")
        || (!https_only && catalog.scheme() != "https" && catalog.scheme() != "http")
        || catalog.host_str().is_none()
        || catalog.cannot_be_a_base()
        || catalog.query().is_some()
        || catalog.fragment().is_some()
        || !catalog.username().is_empty()
        || catalog.password().is_some()
    {
        return Err("unsafe descriptor endpoint".into());
    }
    let mut normalized = catalog;
    normalized.set_path(&format!("{}/", normalized.path().trim_end_matches('/')));
    let expected = normalized
        .join(&format!(
            "v1/channels/{}/join",
            URL_SAFE_NO_PAD.encode(descriptor.channel_id.0)
        ))
        .map_err(|e| e.to_string())?;
    if endpoint != expected {
        return Err("descriptor join endpoint does not match channel".into());
    }
    Ok(())
}

fn spawn_archiver(inner: &Arc<Inner>) {
    let mut source = inner.sdk.subscribe_events();
    let weak = Arc::downgrade(inner);
    let task = tokio::spawn(async move {
        while let Some(event) = source.recv().await {
            let Some(inner) = weak.upgrade() else { break };
            if matches!(event, ClientEvent::ChannelRosterChanged { .. }) {
                let _ = ClientHandle(inner.clone()).reconcile_channels().await;
            }
            archive_event(&inner, &event).await;
            // Incoming state is durable before any UI observes the event.
            if let Err(error) = save_inner(&inner).await {
                eprintln!("chat archive save failed: {error}");
            }
            let _ = inner.events.send(event);
        }
    });
    inner.background.lock().unwrap().push(task);
}

async fn archive_event(inner: &Arc<Inner>, event: &ClientEvent) {
    if let ClientEvent::ChannelRosterChanged { channel, .. } = event {
        if let Ok(roster) = inner.sdk.channel_roster(channel).await {
            let mut data = inner.data.lock().unwrap();
            let changed = if let Some(record) = data
                .channels
                .iter_mut()
                .find(|candidate| candidate.active && candidate.protocol_name == *channel)
            {
                record.members = roster
                    .into_iter()
                    .map(|member| MemberRecord {
                        id: MemberId(member.member_id),
                        display_name: member.display_name,
                        join_order: member.join_order,
                        joined_at_unix: member.joined_at_unix,
                        is_self: member.is_self,
                    })
                    .collect();
                let present = record
                    .members
                    .iter()
                    .map(|member| member.id)
                    .collect::<HashSet<_>>();
                Some((record.id, present))
            } else {
                None
            };
            if let Some((channel_id, present)) = changed {
                for pm in &mut data.scoped_pms {
                    if pm.id.channel_id == channel_id && !present.contains(&pm.id.remote_member_id)
                    {
                        pm.active = false;
                    }
                }
            }
            inner.dirty.store(true, Ordering::Relaxed);
        }
        return;
    }
    let mut data = inner.data.lock().unwrap();
    match event {
        ClientEvent::ChannelMessage {
            channel,
            message_id,
            timestamp_unix,
            sender,
            sender_index,
            body,
            ..
        } => {
            if let Some(record) = data
                .channels
                .iter_mut()
                .find(|candidate| candidate.active && candidate.protocol_name == *channel)
            {
                if record
                    .messages
                    .iter()
                    .any(|message| message.id == message_id.0)
                {
                    return;
                }
                let member = record
                    .members
                    .iter()
                    .find(|member| member.join_order == *sender_index)
                    .map(|member| member.id);
                record.messages.push(Message {
                    id: message_id.0,
                    ts_unix: *timestamp_unix,
                    sender_member_id: member,
                    sender_name: sender.clone(),
                    mine: false,
                    text: String::from_utf8_lossy(body).into_owned(),
                });
            }
        }
        ClientEvent::ChannelDirectMessage {
            channel,
            sender_member_id,
            recipient_member_id,
            message_id,
            timestamp_unix,
            body,
        } => {
            let Some(record) = data
                .channels
                .iter()
                .find(|candidate| candidate.active && candidate.protocol_name == *channel)
                .cloned()
            else {
                return;
            };
            let Some(self_id) = record.self_member_id else {
                return;
            };
            if MemberId(*recipient_member_id) != self_id {
                return;
            }
            let remote = MemberId(*sender_member_id);
            let name = record
                .members
                .iter()
                .find(|member| member.id == remote)
                .map_or_else(
                    || short_member(&remote),
                    |member| member.display_name.clone(),
                );
            let id = ScopedPmId {
                channel_id: record.id,
                self_member_id: self_id,
                remote_member_id: remote,
            };
            let pm = match data.scoped_pms.iter_mut().find(|pm| pm.id == id) {
                Some(pm) => pm,
                None => {
                    data.scoped_pms.push(ScopedPmRecord {
                        id,
                        remote_display_name: name,
                        messages: Vec::new(),
                        active: true,
                    });
                    data.scoped_pms.last_mut().unwrap()
                }
            };
            if !pm.messages.iter().any(|message| message.id == message_id.0) {
                pm.messages.push(Message {
                    id: message_id.0,
                    ts_unix: *timestamp_unix,
                    sender_member_id: Some(remote),
                    sender_name: pm.remote_display_name.clone(),
                    mine: false,
                    text: String::from_utf8_lossy(body).into_owned(),
                });
            }
        }
        ClientEvent::ChannelRemoved { channel } => {
            let removed = data
                .channels
                .iter_mut()
                .find(|candidate| candidate.active && candidate.protocol_name == *channel)
                .map(|record| {
                    record.active = false;
                    record.id
                });
            if let Some(channel_id) = removed {
                for pm in &mut data.scoped_pms {
                    if pm.id.channel_id == channel_id {
                        pm.active = false;
                    }
                }
            }
        }
        _ => return,
    }
    inner.dirty.store(true, Ordering::Relaxed);
}

fn spawn_periodic_save(inner: &Arc<Inner>) {
    let weak = Arc::downgrade(inner);
    let task = tokio::spawn(async move {
        loop {
            tokio::time::sleep(Duration::from_secs(30)).await;
            let Some(inner) = weak.upgrade() else { break };
            if inner.dirty.load(Ordering::Relaxed) {
                let _ = save_inner(&inner).await;
            }
        }
    });
    inner.background.lock().unwrap().push(task);
}

async fn save_inner(inner: &Arc<Inner>) -> Result<(), String> {
    match &inner.persistence {
        Persistence::Embedded { node, .. } => node.persist_state().await?,
        // The hosted runtime saves its own node state on every event and
        // every 30 s; only the archive is ours here.
        Persistence::Archive(store) | Persistence::Hosted { store, .. } => {
            store.save(&inner.data.lock().unwrap())?
        }
        Persistence::Memory => {}
    }
    inner.dirty.store(false, Ordering::Relaxed);
    Ok(())
}

fn short_member(member: &MemberId) -> String {
    member.0[..4]
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}
fn fresh_id() -> [u8; 16] {
    use rand::RngCore;
    let mut id = [0; 16];
    rand::thread_rng().fill_bytes(&mut id);
    id
}
fn now_unix() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map_or(0, |duration| duration.as_secs())
}

#[cfg(test)]
mod catalog_tests {
    use super::*;
    use axum::extract::{Path, Query, State};
    use axum::http::StatusCode;
    use axum::routing::{get, post, put};
    use axum::{Json, Router};
    use serde::Deserialize;
    use std::collections::HashMap;
    use tokio::net::TcpListener;

    #[derive(Clone)]
    struct FakeCatalog {
        owner: ClientHandle,
        descriptors: Arc<tokio::sync::Mutex<Vec<PublicChannelDescriptor>>>,
        cursor: CursorBehavior,
    }

    #[derive(Clone, Copy)]
    enum CursorBehavior {
        Pages,
        Repeat,
        Oversized,
    }

    #[derive(Deserialize)]
    struct JoinBody {
        display_pseudonym: String,
        key_package_b64: String,
    }

    async fn query(
        State(state): State<FakeCatalog>,
        Query(query): Query<HashMap<String, String>>,
    ) -> Json<CatalogResponse> {
        let descriptors = state.descriptors.lock().await.clone();
        let current = query.get("cursor").map(String::as_str);
        let (descriptors, next_cursor) = match state.cursor {
            CursorBehavior::Pages if current.is_none() && descriptors.len() > 1 => {
                (descriptors[..1].to_vec(), Some("second".into()))
            }
            CursorBehavior::Pages if current == Some("second") => (descriptors[1..].to_vec(), None),
            CursorBehavior::Pages => (descriptors, None),
            CursorBehavior::Repeat => (Vec::new(), Some("repeat".into())),
            CursorBehavior::Oversized => {
                (Vec::new(), Some("x".repeat(CATALOG_MAX_CURSOR_BYTES + 1)))
            }
        };
        Json(CatalogResponse {
            descriptors,
            next_cursor,
        })
    }

    async fn publish(
        State(state): State<FakeCatalog>,
        Json(descriptor): Json<PublicChannelDescriptor>,
    ) -> StatusCode {
        state.descriptors.lock().await.push(descriptor);
        StatusCode::NO_CONTENT
    }

    async fn join(
        State(state): State<FakeCatalog>,
        Path(_channel): Path<String>,
        Json(body): Json<JoinBody>,
    ) -> Result<Json<CatalogJoinResponse>, StatusCode> {
        let package = URL_SAFE_NO_PAD
            .decode(body.key_package_b64)
            .map_err(|_| StatusCode::BAD_REQUEST)?;
        let welcome = state
            .owner
            .admit("public-room", &package, &body.display_pseudonym)
            .await
            .map_err(|_| StatusCode::BAD_GATEWAY)?;
        Ok(Json(CatalogJoinResponse {
            channel: "public-room".into(),
            visibility: ChannelVisibility::Public,
            welcome_b64: URL_SAFE_NO_PAD.encode(welcome),
        }))
    }

    async fn serve_fake(
        owner: ClientHandle,
        cursor: CursorBehavior,
    ) -> (
        String,
        Arc<tokio::sync::Mutex<Vec<PublicChannelDescriptor>>>,
        tokio::task::JoinHandle<()>,
    ) {
        let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let descriptors = Arc::new(tokio::sync::Mutex::new(Vec::new()));
        let state = FakeCatalog {
            owner,
            descriptors: descriptors.clone(),
            cursor,
        };
        let router = Router::new()
            .route("/v1/catalog", get(query))
            .route("/v1/descriptors", put(publish))
            .route("/v1/channels/{channel}/join", post(join))
            .with_state(state);
        let task = tokio::spawn(async move {
            axum::serve(listener, router).await.unwrap();
        });
        (format!("http://{address}/"), descriptors, task)
    }

    fn addr() -> SocketAddr {
        "127.0.0.1:0".parse().unwrap()
    }

    #[tokio::test(flavor = "multi_thread")]
    async fn fake_catalogs_cover_pages_signatures_cache_publication_and_join() {
        let dir = tempfile::tempdir().unwrap();
        let owner = ClientHandle::create_profile_fixture(
            &dir.path().join("owner.gcstore"),
            "owner",
            addr(),
            None,
            None,
        )
        .await
        .unwrap();
        owner.allow_test_http();
        let channel_id = owner
            .create_channel("public-room", "owner", 8, ChannelVisibility::Public)
            .await
            .unwrap();
        let (catalog, descriptors, server) = serve_fake(owner.clone(), CursorBehavior::Pages).await;
        owner
            .publish_channel(channel_id, "locally signed", &catalog)
            .await
            .unwrap();
        let valid = descriptors.lock().await[0].clone();
        assert!(valid.verify_at(now_unix()));

        let mut tampered = valid.clone();
        tampered.title = "forged".into();
        let expired = owner
            .0
            .sdk
            .public_channel_descriptor(
                "public-room",
                "expired",
                ActivityBucket::None,
                valid.automatic_join.clone(),
                now_unix().saturating_sub(1),
            )
            .await
            .unwrap();
        descriptors.lock().await.extend([tampered, expired]);

        let (second_catalog, second_descriptors, second_server) =
            serve_fake(owner.clone(), CursorBehavior::Pages).await;
        second_descriptors.lock().await.push(valid.clone());

        let cache_path = dir.path().join("cache.gcstore");
        let cache = ClientHandle::create_profile_fixture(&cache_path, "cache", addr(), None, None)
            .await
            .unwrap();
        cache.allow_test_http();
        cache
            .configure_catalogs(&[catalog.clone(), second_catalog])
            .await
            .unwrap();
        let public = cache
            .home_items()
            .into_iter()
            .filter_map(|item| match item {
                HomeItem::Public(descriptor) => Some(descriptor),
                _ => None,
            })
            .collect::<Vec<_>>();
        assert_eq!(public.len(), 1, "ChannelId must deduplicate catalogs");
        assert_eq!(public[0].descriptor, valid);
        cache.save().await.unwrap();
        cache.shutdown().await.unwrap();
        assert!(!std::fs::read(&cache_path)
            .unwrap()
            .windows(b"locally signed".len())
            .any(|bytes| bytes == b"locally signed"));

        let joiner = ClientHandle::create_profile_fixture(
            &dir.path().join("joiner.gcstore"),
            "joiner",
            addr(),
            None,
            None,
        )
        .await
        .unwrap();
        joiner.allow_test_http();
        joiner.join_public(&valid, "guest").await.unwrap();
        assert_eq!(
            joiner.channel(channel_id).unwrap().protocol_name,
            "public-room"
        );

        server.abort();
        second_server.abort();
        let reopened = ClientHandle::unlock_fixture(&cache_path, "cache", addr(), None, None)
            .await
            .unwrap();
        reopened.allow_test_http();
        let unreachable = reopened
            .configure_catalogs(std::slice::from_ref(&catalog))
            .await
            .unwrap_err();
        assert!(unreachable.starts_with(&catalog), "{unreachable}");
        assert_eq!(reopened.catalog_urls(), vec![catalog]);
        assert!(reopened.home_items().iter().any(
            |item| matches!(item, HomeItem::Public(cached) if cached.descriptor.channel_id == channel_id)
        ));
        reopened.shutdown().await.unwrap();
        joiner.shutdown().await.unwrap();
        owner.shutdown().await.unwrap();
    }

    #[tokio::test(flavor = "multi_thread")]
    async fn catalog_rejects_repeated_and_oversized_cursors_and_http_in_production() {
        let dir = tempfile::tempdir().unwrap();
        let owner = ClientHandle::create_profile_fixture(
            &dir.path().join("owner.gcstore"),
            "owner",
            addr(),
            None,
            None,
        )
        .await
        .unwrap();
        owner.allow_test_http();
        let production = ClientHandle::create_profile_fixture(
            &dir.path().join("production.gcstore"),
            "production",
            addr(),
            None,
            None,
        )
        .await
        .unwrap();
        let (repeat, _, repeat_server) = serve_fake(owner.clone(), CursorBehavior::Repeat).await;
        let (oversized, _, oversized_server) =
            serve_fake(owner.clone(), CursorBehavior::Oversized).await;
        assert!(production
            .configure_catalogs(std::slice::from_ref(&repeat))
            .await
            .is_err());
        assert!(owner
            .configure_catalogs(&[repeat])
            .await
            .unwrap_err()
            .contains("repeated"));
        assert!(owner
            .configure_catalogs(&[oversized])
            .await
            .unwrap_err()
            .contains("out of bounds"));
        repeat_server.abort();
        oversized_server.abort();
        production.shutdown().await.unwrap();
        owner.shutdown().await.unwrap();
    }
}
