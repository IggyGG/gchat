//! Channel-first application API over the typed GC SDK.

use crate::model::{
    sort_home, sort_members, CachedDescriptor, ChannelRecord, HomeItem, MemberId, MemberRecord,
    Message, ScopedPmId, ScopedPmRecord,
};
use crate::runtime::ProtocolRuntime;
use crate::store::{ArchiveData, ArchiveStore, Store, StoreData};
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use base64::Engine;
use gcoms::sdk::{
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

pub use gcoms::sdk::ClientEvent as NodeEvent;
pub use gcoms::sdk::RelayCard as NodeInfo;

const CATALOG_PAGE_SIZE: u16 = 100;
const CATALOG_MAX_PAGES: usize = 10;
const CATALOG_MAX_DESCRIPTORS: usize = 10_000;
const CATALOG_MAX_CURSOR_BYTES: usize = 1024;
const DESCRIPTOR_MAX_LIFETIME: u64 = 7 * 24 * 60 * 60;

pub fn b64_encode(bytes: &[u8]) -> String {
    URL_SAFE_NO_PAD.encode(bytes)
}
pub fn b64_decode(value: &str) -> Option<Vec<u8>> {
    URL_SAFE_NO_PAD.decode(value.trim()).ok()
}
pub fn decode_relay_card(card: &str) -> Result<NodeInfo, String> {
    gcoms::runtime::contacts::decode_relay_card(card)
}

/// Decode a peer-visible contact card. Contact cards deliberately use the
/// public NodeInfo encoding, which excludes every relay-private capability;
/// only local bootstrap material carries private provisioning.
pub fn decode_contact_card(card: &str) -> Result<gcoms::sdk::ContactCard, String> {
    gcoms::runtime::contacts::decode_contact_card(card)
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
    archive_blocked: AtomicBool,
    presence_enabled: AtomicBool,
    presence_control: tokio::sync::Mutex<()>,
    recent_members: Mutex<BTreeMap<(String, [u8; 32]), std::time::Instant>>,
    background: Mutex<Vec<tokio::task::JoinHandle<()>>>,
}

enum Persistence {
    /// Legacy combined store: the node lives in this process and the
    /// archive is saved inside the same encrypted file.
    Embedded {
        runtime: ProtocolRuntime,
        pending_archive: Arc<Mutex<Option<ClientEvent>>>,
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
        let embedded = runtime.embedded();
        Self::finish(
            sdk,
            embedded,
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

    /// File scheduling needs conversation metadata, never a copy of transcripts.
    pub(crate) fn file_context(&self) -> ArchiveData {
        let data = self.0.data.lock().unwrap();
        ArchiveData {
            channels: data
                .channels
                .iter()
                .map(|c| ChannelRecord {
                    id: c.id,
                    protocol_name: c.protocol_name.clone(),
                    title: c.title.clone(),
                    visibility: c.visibility,
                    role: c.role,
                    joined_at_unix: c.joined_at_unix,
                    active: c.active,
                    self_member_id: c.self_member_id,
                    members: c.members.clone(),
                    messages: Vec::new(),
                })
                .collect(),
            scoped_pms: data
                .scoped_pms
                .iter()
                .map(|p| ScopedPmRecord {
                    id: p.id,
                    remote_display_name: p.remote_display_name.clone(),
                    messages: Vec::new(),
                    active: p.active,
                })
                .collect(),
            ..ArchiveData::default()
        }
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
            false,
            passphrase,
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
            true,
            passphrase,
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
            false,
            passphrase,
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
            true,
            passphrase,
        )
        .await
    }

    async fn boot(
        store: Store,
        data: StoreData,
        listen: SocketAddr,
        advertise: Option<SocketAddr>,
        inbox_relay: Option<NodeInfo>,
        fixture: bool,
        secret: &str,
    ) -> Result<Self, String> {
        let path = store.path().to_owned();
        let archive = Arc::new(Mutex::new(data.archive));
        let pending_archive = Arc::new(Mutex::new(None));
        let storage = Arc::new(LegacyProtocolStorage {
            pending_archive: pending_archive.clone(),
            store,
            archive: archive.clone(),
        });
        let builder = gcoms::Application::builder("gchat")
            .network_config(crate::network::installed_json())
            .profile(path)
            .unlock_secret(secret)
            .create(false)
            .listen(listen)
            .advertise(advertise)
            .relay(inbox_relay)
            .durable_channel_inbox(true)
            .receive_messages(false)
            .legacy_storage(
                storage,
                gcoms::runtime::store::ProtocolData {
                    identity_seed: data.identity_seed,
                    node_state: data.node_state,
                },
            );
        let builder = if fixture {
            builder.local_fixture().listen(listen)
        } else {
            builder
        };
        let runtime = ProtocolRuntime(builder.open().await?);
        let sdk = runtime.sdk_client();
        let embedded = runtime.embedded();
        let identity = sdk.identity();
        let label = runtime.listen_label();
        Self::finish(
            sdk,
            embedded,
            identity,
            label,
            Persistence::Embedded {
                runtime,
                pending_archive,
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
        use gcoms::sdk::ipc::Capability;
        let sdk = gcoms::sdk::IpcClient::connect(
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
        let embedded = runtime.embedded();
        Self::finish(
            sdk,
            embedded,
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
            archive_blocked: AtomicBool::new(false),
            presence_enabled: AtomicBool::new(false),
            presence_control: tokio::sync::Mutex::new(()),
            recent_members: Mutex::new(BTreeMap::new()),
            background: Mutex::new(Vec::new()),
        });
        let handle = Self(inner);
        if let Some(embedded) = &handle.0.embedded_sdk {
            embedded
                .channel_inbox()
                .await
                .map_err(|e| format!("durable channel archive is not available: {e}"))?;
        }
        if reconcile {
            handle.reconcile_channels().await?;
        }
        spawn_archiver(&handle.0);
        spawn_channel_archive(&handle.0);
        spawn_periodic_save(&handle.0);
        spawn_presence(&handle.0);
        Ok(handle)
    }

    pub fn archive_waiting_for_storage(&self) -> bool {
        self.0.archive_blocked.load(Ordering::Relaxed)
    }

    pub async fn configure_presence(&self, enabled: bool) -> Result<(), String> {
        let _control = self.0.presence_control.lock().await;
        self.0.presence_enabled.store(enabled, Ordering::Relaxed);
        if !enabled {
            self.0.recent_members.lock().unwrap().clear();
        }
        let mut failure = None;
        for channel in self.archive_snapshot().channels.iter().filter(|c| c.active) {
            if let Err(error) = self
                .0
                .sdk
                .set_channel_presence_opt_in(&channel.protocol_name, enabled)
                .await
            {
                // The SDK emits this error only after committing the local
                // opt-out. An offline peer must not prevent profile reopening;
                // its last activity signal expires normally. Other errors,
                // including a failed local save, remain failures.
                if !enabled
                    && matches!(&error, gcoms::sdk::SdkError::Runtime(message)
                    if message.starts_with("presence disabled locally; withdrawal failed:"))
                {
                    eprintln!("Activity sharing disabled locally; peer withdrawal unavailable");
                } else if failure.is_none() {
                    failure = Some(error.to_string());
                }
            }
        }
        failure.map_or(Ok(()), Err)
    }
    pub fn recently_active(&self, channel: &str, member: [u8; 32]) -> bool {
        self.0.presence_enabled.load(Ordering::Relaxed)
            && self
                .0
                .recent_members
                .lock()
                .unwrap()
                .get(&(channel.to_string(), member))
                .is_some_and(|at| at.elapsed() < Duration::from_secs(90))
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
        self.0
            .sdk
            .recover_network(urls.to_vec())
            .await
            .map_err(|e| e.to_string())
    }

    async fn catalog_http(
        &self,
        method: &str,
        url: Url,
        body: Vec<u8>,
    ) -> Result<gcoms::sdk::CatalogHttpResponse, String> {
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
            return Ok(gcoms::sdk::CatalogHttpResponse { status, body });
        }
        gcoms::runtime::contacts::validate_catalog_request(method, url.as_str(), &body)
            .map_err(|e| e.to_string())?;
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
            .catalog_request(gcoms::sdk::CatalogHttpRequest {
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
    /// long the invite is valid. Available through either application backend.
    pub async fn create_invite(&self, id: ChannelId, ttl_secs: u64) -> Result<String, String> {
        let channel = self
            .channel_protocol_name(id)
            .ok_or("channel is not active")?;
        self.0
            .sdk
            .create_channel_invitation(&channel, ttl_secs)
            .await
            .map(|i| i.link)
            .map_err(|e| e.to_string())
    }

    /// Friend: redeem an invite link. Prepares a key package, contacts the
    /// owner over the relay (waiting up to `timeout_secs` if they are offline),
    /// and joins the channel on success. Available through either application backend.
    pub async fn join_with_invite(
        &self,
        link: &str,
        display: &str,
        timeout_secs: u64,
    ) -> Result<String, String> {
        let channel = self
            .0
            .sdk
            .join_channel_invitation(link, display, timeout_secs)
            .await
            .map_err(|e| e.to_string())?;
        self.reconcile_channels().await?;
        Ok(channel)
    }
    pub async fn send_channel(&self, id: ChannelId, text: &str) -> Result<(), String> {
        self.send_channel_operation(id, text, None).await
    }
    pub(crate) async fn send_channel_operation(
        &self,
        id: ChannelId,
        text: &str,
        operation: Option<&str>,
    ) -> Result<(), String> {
        let started = now_unix();
        let channel = self.channel(id).ok_or("channel is not active")?;
        // The tracked API requires a remote recipient. Preserve solo-channel
        // notes through the ordinary API, deciding before any send (never retry
        // an uncertain tracked send through another method).
        let message_id = if channel.members.iter().any(|member| !member.is_self) {
            self.0
                .sdk
                .send_channel_tracked(&channel.protocol_name, text.as_bytes())
                .await
                .map_err(|e| e.to_string())?
                .0
        } else {
            self.0
                .sdk
                .send_channel(&channel.protocol_name, text.as_bytes())
                .await
                .map_err(|e| e.to_string())?;
            rand::random::<[u8; 16]>() // Local archive identity; no recipient ACK claimed.
        };
        let mut data = self.0.data.lock().unwrap();
        let delivered = data.delivery_receipts.contains(&(id.0, message_id));
        if let Some(channel) = data
            .channels
            .iter_mut()
            .find(|candidate| candidate.active && candidate.id == id)
        {
            channel.messages.push(Message {
                id: message_id,
                operation_id: operation.map(str::to_owned),
                delivery: Some(if delivered {
                    gchat_api::Delivery::Delivered
                } else {
                    gchat_api::Delivery::LocalAccepted
                }),
                ts_unix: started,
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
        self.send_scoped_pm_operation(id, text, None).await
    }
    pub(crate) async fn send_scoped_pm_operation(
        &self,
        id: ScopedPmId,
        text: &str,
        operation: Option<&str>,
    ) -> Result<(), String> {
        let started = now_unix();
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
        let delivered = data
            .delivery_receipts
            .contains(&(id.channel_id.0, message_id.0));
        let pm = data
            .scoped_pms
            .iter_mut()
            .find(|pm| pm.id == id && pm.active)
            .ok_or("scoped PM is not active")?;
        pm.messages.push(Message {
            id: message_id.0,
            operation_id: operation.map(str::to_owned),
            delivery: Some(if delivered {
                gchat_api::Delivery::Delivered
            } else {
                gchat_api::Delivery::LocalAccepted
            }),
            ts_unix: started,
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

    pub async fn channel_topic(&self, id: ChannelId) -> Result<String, String> {
        let channel = self.channel(id).ok_or("channel is not active")?;
        self.0
            .sdk
            .channel_topic(&channel.protocol_name)
            .await
            .map_err(|e| e.to_string())
    }

    pub async fn change_channel(
        &self,
        id: ChannelId,
        change: gcoms::sdk::ChannelChange,
    ) -> Result<(), String> {
        let channel = self.channel(id).ok_or("channel is not active")?;
        self.0
            .sdk
            .change_channel(&channel.protocol_name, change)
            .await
            .map_err(|e| e.to_string())?;
        self.reconcile_channels().await?;
        self.save().await
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
            Persistence::Embedded { runtime, .. } => runtime.clone().shutdown().await?,
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

fn spawn_presence(inner: &Arc<Inner>) {
    let weak = Arc::downgrade(inner);
    let task = tokio::spawn(async move {
        let mut timer = tokio::time::interval(Duration::from_secs(60));
        timer.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
        loop {
            timer.tick().await;
            let Some(inner) = weak.upgrade() else { break };
            if !inner.presence_enabled.load(Ordering::Relaxed) {
                continue;
            }
            let channels: Vec<_> = inner
                .data
                .lock()
                .unwrap()
                .channels
                .iter()
                .filter(|c| c.active)
                .map(|c| c.protocol_name.clone())
                .collect();
            for channel in channels {
                let _control = inner.presence_control.lock().await;
                if !inner.presence_enabled.load(Ordering::Relaxed) {
                    break;
                }
                let sdk = inner.sdk.clone();
                let _ = tokio::time::timeout(Duration::from_secs(5), async {
                    sdk.set_channel_presence_opt_in(&channel, true).await?;
                    sdk.set_channel_presence(
                        &channel,
                        gcoms::sdk::PresenceMode::RecentlyReachable,
                        90,
                    )
                    .await
                })
                .await;
            }
        }
    });
    inner.background.lock().unwrap().push(task);
}

fn spawn_channel_archive(inner: &Arc<Inner>) {
    let Some(sdk) = inner.embedded_sdk.clone() else {
        return;
    };
    let weak = Arc::downgrade(inner);
    let task = tokio::spawn(async move {
        let mut last_error = None;
        loop {
            tokio::time::sleep(Duration::from_millis(200)).await;
            let Some(inner) = weak.upgrade() else { break };
            let result: Result<(), String> = async {
                let pending = sdk.channel_inbox().await.map_err(|e| e.to_string())?;
                for (sequence, digest, event) in pending {
                    // Reconcile first: startup or a new membership may precede its roster event.
                    let channel = match &event {
                        ClientEvent::ChannelMessage { channel, .. }
                        | ClientEvent::ChannelDirectMessage { channel, .. } => channel,
                        _ => unreachable!(),
                    };
                    let known = inner
                        .data
                        .lock()
                        .unwrap()
                        .channels
                        .iter()
                        .any(|c| c.protocol_name == *channel);
                    if !known {
                        ClientHandle(inner.clone()).reconcile_channels().await?;
                    }
                    archive_channel_delivery(&inner, &event).await?;
                    sdk.commit_channel_delivery(sequence, digest)
                        .await
                        .map_err(|e| e.to_string())?;
                    let _ = inner.events.send(event);
                }
                Ok(())
            }
            .await;
            match result {
                Ok(()) => {
                    inner.archive_blocked.store(false, Ordering::Relaxed);
                    last_error = None;
                }
                Err(error) => {
                    inner.archive_blocked.store(true, Ordering::Relaxed);
                    if last_error.as_ref() != Some(&error) {
                        eprintln!("chat archive delivery retained: {error}");
                    }
                    last_error = Some(error);
                    drop(inner);
                    tokio::time::sleep(Duration::from_secs(2)).await;
                }
            }
        }
    });
    inner.background.lock().unwrap().push(task);
}

fn archive_contains_delivery(data: &ArchiveData, event: &ClientEvent) -> bool {
    match event {
        ClientEvent::ChannelMessage {
            channel,
            message_id,
            ..
        } => data.channels.iter().any(|c| {
            c.protocol_name == *channel && c.messages.iter().any(|m| m.id == message_id.0)
        }),
        ClientEvent::ChannelDirectMessage {
            channel,
            message_id,
            sender_member_id,
            recipient_member_id,
            ..
        } => {
            let id = data
                .channels
                .iter()
                .find(|c| c.protocol_name == *channel)
                .map(|c| c.id);
            data.scoped_pms.iter().any(|p| {
                Some(p.id.channel_id) == id
                    && p.id.remote_member_id == MemberId(*sender_member_id)
                    && p.id.self_member_id == MemberId(*recipient_member_id)
                    && p.messages.iter().any(|m| m.id == message_id.0)
            })
        }
        _ => false,
    }
}

async fn archive_channel_delivery(inner: &Arc<Inner>, event: &ClientEvent) -> Result<(), String> {
    let channel = match event {
        ClientEvent::ChannelMessage { channel, .. }
        | ClientEvent::ChannelDirectMessage { channel, .. } => channel,
        _ => return Err("not a channel delivery".into()),
    };
    if !inner
        .data
        .lock()
        .unwrap()
        .channels
        .iter()
        .any(|c| c.protocol_name == *channel)
    {
        return Err("channel archive metadata not ready".into());
    }
    match &inner.persistence {
        Persistence::Archive(store) | Persistence::Hosted { store, .. } => {
            // Hold the projection lock through its durable commit. No failed candidate
            // becomes visible, and concurrent local writes cannot be rolled back.
            let mut data = inner.data.lock().unwrap();
            let mut candidate = data.clone();
            apply_archive_event(&mut candidate, event);
            if !archive_contains_delivery(&candidate, event) {
                return Err("channel delivery metadata incomplete".into());
            }
            store.save(&candidate)?;
            *data = candidate;
        }
        Persistence::Embedded {
            runtime,
            pending_archive,
        } => {
            *pending_archive.lock().unwrap() = Some(event.clone());
            // The legacy storage sink commits this candidate while holding its data
            // lock, then updates RAM. Never hold the data lock across a node call.
            runtime.save().await?;
        }
        Persistence::Memory => apply_archive_event(&mut inner.data.lock().unwrap(), event),
    }
    Ok(())
}

fn spawn_archiver(inner: &Arc<Inner>) {
    let mut source = inner.sdk.subscribe_events();
    let weak = Arc::downgrade(inner);
    let task = tokio::spawn(async move {
        while let Some(event) = source.recv().await {
            let Some(inner) = weak.upgrade() else { break };
            if let ClientEvent::ChannelPresenceChanged {
                channel,
                member_id,
                reachability,
            } = &event
            {
                let mut recent = inner.recent_members.lock().unwrap();
                recent.retain(|_, at| at.elapsed() < Duration::from_secs(90));
                let key = (channel.clone(), *member_id);
                if inner.presence_enabled.load(Ordering::Relaxed)
                    && *reachability == gcoms::sdk::Reachability::RecentlyReachable
                {
                    recent.insert(key, std::time::Instant::now());
                } else {
                    recent.remove(&key);
                }
                // Presence is deliberately RAM-only. Never persist or count it as a chat message.
                drop(recent);
                let _ = inner.events.send(event);
                continue;
            }
            if matches!(event, ClientEvent::ChannelRosterChanged { .. }) {
                let _ = ClientHandle(inner.clone()).reconcile_channels().await;
            }
            if matches!(&event, ClientEvent::ChannelMessage { body, .. } | ClientEvent::ChannelDirectMessage { body, .. }
                if gcoms_core::is_piece_application_payload(body))
            {
                continue;
            }
            if inner.embedded_sdk.is_some()
                && matches!(
                    event,
                    ClientEvent::ChannelMessage { .. } | ClientEvent::ChannelDirectMessage { .. }
                )
            {
                // The durable inbox owns text publication; this subscription is only a hint.
                continue;
            }
            archive_event(&inner, &event).await;
            // Attempt the archive checkpoint before notifying views. A failed save
            // still leaves RAM state visible; it is not a durability acknowledgement.
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
    apply_archive_event(&mut inner.data.lock().unwrap(), event);
    inner.dirty.store(true, Ordering::Relaxed);
}

fn apply_archive_event(data: &mut ArchiveData, event: &ClientEvent) {
    match event {
        ClientEvent::ChannelDelivered {
            channel,
            message_id,
        }
        | ClientEvent::ChannelDirectDelivered {
            channel,
            message_id,
            ..
        } => {
            if let Some(id) = data
                .channels
                .iter()
                .find(|c| c.protocol_name == *channel && c.active)
                .map(|c| c.id)
            {
                let receipt = (id.0, message_id.0);
                if !data.delivery_receipts.contains(&receipt) {
                    data.delivery_receipts.push(receipt);
                }
                if data.delivery_receipts.len() > 1024 {
                    data.delivery_receipts.remove(0);
                }
                for record in data.channels.iter_mut().filter(|c| c.id == id) {
                    for message in record
                        .messages
                        .iter_mut()
                        .filter(|m| m.mine && m.id == message_id.0)
                    {
                        message.delivery = Some(gchat_api::Delivery::Delivered);
                    }
                }
                for pm in data.scoped_pms.iter_mut().filter(|p| p.id.channel_id == id) {
                    for message in pm
                        .messages
                        .iter_mut()
                        .filter(|m| m.mine && m.id == message_id.0)
                    {
                        message.delivery = Some(gchat_api::Delivery::Delivered);
                    }
                }
            }
        }
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
                .find(|candidate| candidate.protocol_name == *channel)
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
                    operation_id: None,
                    delivery: None,
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
                .find(|candidate| candidate.protocol_name == *channel)
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
                    operation_id: None,
                    delivery: None,
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
        _ => (),
    }
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
        Persistence::Embedded { runtime, .. } => runtime.save().await?,
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
fn now_unix() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map_or(0, |duration| duration.as_secs())
}

// Keeps the legacy combined encrypted file format while GComs owns protocol lifecycle.
struct LegacyProtocolStorage {
    pending_archive: Arc<Mutex<Option<ClientEvent>>>,
    store: Store,
    archive: Arc<Mutex<ArchiveData>>,
}
impl gcoms::runtime::store::ProfileStorage for LegacyProtocolStorage {
    fn save(&self, data: &gcoms::runtime::store::ProtocolData) -> Result<(), String> {
        let mut archive = self.archive.lock().map_err(|_| "archive lock poisoned")?;
        let mut pending = self
            .pending_archive
            .lock()
            .map_err(|_| "pending archive lock poisoned")?;
        let mut candidate = archive.clone();
        if let Some(event) = pending.as_ref() {
            apply_archive_event(&mut candidate, event);
            if !archive_contains_delivery(&candidate, event) {
                return Err("channel delivery metadata incomplete".into());
            }
        }
        self.store.save(&StoreData {
            identity_seed: data.identity_seed,
            node_state: data.node_state.clone(),
            archive: candidate.clone(),
        })?;
        *archive = candidate;
        *pending = None;
        Ok(())
    }

    fn network_directory(&self) -> std::path::PathBuf {
        self.store.network_directory()
    }
    fn verify_secret(&self, secret: &str) -> Result<(), String> {
        self.store.verify_secret(secret)
    }
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
        crate::private_fs::make_private(dir.path(), true).unwrap();
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
        crate::private_fs::make_private(dir.path(), true).unwrap();
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

#[cfg(test)]
mod presence_view_tests {
    use super::*;

    #[tokio::test]
    async fn activity_is_opt_in_expires_and_is_cleared_on_disable() {
        let dir = tempfile::tempdir().unwrap();
        crate::private_fs::make_private(dir.path(), true).unwrap();
        let client = ClientHandle::create_profile_fixture(
            &dir.path().join("profile"),
            "test",
            "127.0.0.1:0".parse().unwrap(),
            None,
            None,
        )
        .await
        .unwrap();
        let key = ("room".to_string(), [9; 32]);
        client
            .0
            .recent_members
            .lock()
            .unwrap()
            .insert(key.clone(), std::time::Instant::now());
        assert!(!client.recently_active("room", [9; 32]));
        client.configure_presence(true).await.unwrap();
        assert!(client.recently_active("room", [9; 32]));
        client
            .0
            .recent_members
            .lock()
            .unwrap()
            .insert(key, std::time::Instant::now() - Duration::from_secs(91));
        assert!(!client.recently_active("room", [9; 32]));
        client.configure_presence(false).await.unwrap();
        assert!(client.0.recent_members.lock().unwrap().is_empty());
        client.configure_presence(true).await.unwrap();
        assert!(!client.recently_active("room", [9; 32]));
        client.shutdown().await.unwrap();
    }
}
