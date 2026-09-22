//! One archive owner and one command implementation for every UI attachment.
mod extensions;
mod files;
pub mod host;
mod networks;
#[cfg(test)]
mod responsiveness_tests;
pub mod rpc;

use crate::client::ClientHandle;
use crate::model::{ChannelRecord, MemberId, ScopedPmId};
use crate::runtime::ProtocolRuntime;
use crate::store::{ArchiveData, ChatServiceStore};
use gchat_api::{
    Completion, Conversation, ConversationKind, HistoryPage, InstanceInfo, Member, Message,
    Request, RequestEnvelope, Response, ResponseEnvelope, Snapshot, MAX_FRAME_BYTES, VERSION,
};
use gcoms::sdk::{ipc::Capability, ChannelRole, ChannelVisibility, GcClient, LocalEndpoint};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    path::{Path, PathBuf},
    sync::Arc,
    time::{Duration, Instant},
};
use tokio::sync::{watch, Mutex, Notify, RwLock};
use zeroize::Zeroizing;

const HISTORY_LIMIT: usize = 200;
const OPERATION_LIMIT: usize = 4096;

#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct InstanceMetadata {
    version: u16,
    id: String,
    label: String,
}

#[derive(Clone, Default, Serialize, Deserialize)]
#[serde(default)]
struct UiState {
    networks: BTreeMap<String, networks::RetainedNetwork>,
    topics: BTreeMap<String, String>,
    observed_channels: BTreeMap<String, ObservedChannel>,
    activity: Vec<gchat_api::Activity>,
    shared_files: std::collections::BTreeSet<String>,
    files_observed: bool,
    publications: BTreeMap<String, String>,
    presence_enabled: bool,
    instance_id: String,
    safety_number: String,
    read: BTreeMap<String, String>,
    command_history: Vec<String>,
    input_history: Vec<gchat_api::InputHistoryEntry>,
    operations: BTreeMap<String, OperationRecord>,
    message_metadata: BTreeMap<String, MessageMetadata>,
    file_key: Option<[u8; 32]>,
    file_config: gcoms::sdk::sharing::CacheConfig,
}
// Additive metadata lives in the versioned JSON sidecar, never the positional
// postcard archive. Existing encrypted archives keep their exact binary layout.
#[derive(Clone, Default, Serialize, Deserialize, PartialEq, Eq)]
struct MessageMetadata {
    operation_id: Option<String>,
    delivery: Option<gchat_api::Delivery>,
}
fn observe_messages(state: &mut UiState, archive: &ArchiveData) {
    let messages = archive
        .channels
        .iter()
        .flat_map(|c| &c.messages)
        .chain(archive.scoped_pms.iter().flat_map(|p| &p.messages))
        .filter(|m| m.mine);
    let mut retained = std::collections::BTreeSet::new();
    for m in messages {
        let id = hex(&m.id);
        retained.insert(id.clone());
        if m.operation_id.is_none() && m.delivery.is_none() {
            continue;
        }
        let metadata = state.message_metadata.entry(id).or_default();
        if let Some(operation) = &m.operation_id {
            metadata.operation_id = Some(operation.clone());
        }
        if metadata.delivery != Some(gchat_api::Delivery::Delivered) && m.delivery.is_some() {
            metadata.delivery = m.delivery.clone();
        }
    }
    state.message_metadata.retain(|id, _| retained.contains(id));
}

#[derive(Clone, Default, Serialize, Deserialize, PartialEq, Eq)]
struct ObservedChannel {
    members: BTreeMap<String, String>,
    topic: String,
    active: bool,
}

fn record_activity(state: &mut UiState, conversation: String, kind: &str, text: String) {
    state.activity.push(gchat_api::Activity {
        id: random_id(),
        conversation,
        kind: kind.into(),
        text,
        timestamp: now(),
    });
    if state.activity.len() > 2000 {
        state.activity.drain(..state.activity.len() - 2000);
    }
}

#[derive(Clone, Serialize, Deserialize)]
struct OperationRecord {
    #[serde(default)]
    action: String,
    #[serde(default)]
    conversation: Option<String>,
    digest: String,
    at: u64,
    response: Option<Response>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    rpc: Option<rpc::RecordBinding>,
}
struct Unlocked {
    files: Option<Arc<files::FileRuntime>>,
    file_error: Option<String>,
    ui_locked: bool,
    client: ClientHandle,
    store: ChatServiceStore,
    state: UiState,
}

struct InFlight<'a> {
    id: &'a str,
    operations: &'a std::sync::Mutex<std::collections::BTreeSet<String>>,
}
impl Drop for InFlight<'_> {
    fn drop(&mut self) {
        self.operations
            .lock()
            .expect("active operations")
            .remove(self.id);
    }
}
fn latency(stage: &str, started: Instant) {
    if std::env::var_os("GCHAT_LATENCY_DIAGNOSTICS").is_some() {
        eprintln!(
            "gchat_latency stage={stage} elapsed_ms={}",
            started.elapsed().as_millis()
        );
    }
}

/// Hosting the same module in gcd or an Android service does not duplicate logic.
pub struct ChatService {
    networks: Mutex<BTreeMap<String, Arc<ChatService>>>,
    network_operations: Mutex<()>,
    id: String,
    label: String,
    boot: String,
    archive: PathBuf,
    runtime: ProtocolRuntime,
    capabilities: Vec<Capability>,
    command_extension: Option<extensions::CommandExtension>,
    session: Mutex<Option<Unlocked>>,
    /// Serializes admission/mutations without blocking snapshot, history or lock requests.
    operations: RwLock<()>,
    active_operations: std::sync::Mutex<std::collections::BTreeSet<String>>,
    startup: Arc<Notify>,
    startup_worker: std::sync::Mutex<Option<tokio::task::JoinHandle<()>>>,
    projection: std::sync::RwLock<(Vec<Conversation>, String)>,
    projection_refresh: Mutex<()>,
    provider_error: std::sync::RwLock<Option<gchat_api::ProviderStatus>>,
    stopped: watch::Sender<bool>,
    file_worker: std::sync::Mutex<Option<tokio::task::JoinHandle<()>>>,
    catalog_urls: std::sync::RwLock<Vec<String>>,
}

pub fn endpoint_for(protocol_endpoint: &Path) -> PathBuf {
    protocol_endpoint.with_extension("chat")
}

fn random_id() -> String {
    hex(&rand::random::<[u8; 32]>())
}
fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}
fn now() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}
fn channel_key(id: gcoms::sdk::ChannelId) -> String {
    format!("channel/{}", hex(&id.0))
}
fn record_key(channel: &ChannelRecord) -> String {
    if channel.active {
        channel_key(channel.id)
    } else {
        format!(
            "archive/{}/{}/{}",
            hex(&channel.id.0),
            channel
                .self_member_id
                .map(|id| hex(&id.0))
                .unwrap_or_default(),
            channel.joined_at_unix
        )
    }
}
fn query_key(id: ScopedPmId) -> String {
    format!(
        "query/{}/{}/{}",
        hex(&id.channel_id.0),
        hex(&id.self_member_id.0),
        hex(&id.remote_member_id.0)
    )
}

fn instance_metadata(archive: &Path) -> Result<InstanceMetadata, String> {
    let parent = archive
        .parent()
        .ok_or("chat archive needs a parent directory")?;
    crate::paths::ensure_private_dir(parent, "chat instance")?;
    let metadata_path = archive.with_extension("instance.json");
    let metadata: InstanceMetadata = if metadata_path.exists() {
        crate::private_fs::validate_private_file(&metadata_path, "chat instance metadata")?;
        if std::fs::metadata(&metadata_path)
            .map_err(|e| e.to_string())?
            .len()
            > 4096
        {
            return Err("chat instance metadata exceeds bound".into());
        }
        serde_json::from_slice(&std::fs::read(&metadata_path).map_err(|e| e.to_string())?)
            .map_err(|e| format!("invalid chat instance metadata: {e}"))?
    } else {
        let metadata = InstanceMetadata {
            version: 1,
            id: random_id(),
            label: parent
                .file_name()
                .and_then(|s| s.to_str())
                .unwrap_or("gchat")
                .into(),
        };
        let bytes = serde_json::to_vec(&metadata).map_err(|e| e.to_string())?;
        if let Err(error) = crate::store::atomic_write(&metadata_path, &bytes, true) {
            // A competing first attachment may have published the complete metadata.
            if metadata_path.exists() {
                return instance_metadata(archive);
            }
            return Err(error);
        }
        metadata
    };
    if metadata.version != 1
        || metadata.id.len() != 64
        || !metadata.id.bytes().all(|c| c.is_ascii_hexdigit())
    {
        return Err("invalid chat instance identifier".into());
    }
    Ok(metadata)
}

impl ChatService {
    pub fn new(
        archive: PathBuf,
        runtime: ProtocolRuntime,
        capabilities: Vec<Capability>,
    ) -> Result<Arc<Self>, String> {
        let metadata = instance_metadata(&archive)?;
        let service = Arc::new(Self {
            networks: Mutex::new(BTreeMap::new()),
            network_operations: Mutex::new(()),
            id: metadata.id,
            label: metadata.label,
            boot: random_id(),
            command_extension: extensions::CommandExtension::load(&archive)?,
            archive,
            runtime,
            capabilities,
            session: Mutex::new(None),
            operations: RwLock::new(()),
            active_operations: std::sync::Mutex::new(std::collections::BTreeSet::new()),
            startup: Arc::new(Notify::new()),
            startup_worker: std::sync::Mutex::new(None),
            projection: std::sync::RwLock::new((Vec::new(), String::new())),
            projection_refresh: Mutex::new(()),
            provider_error: std::sync::RwLock::new(None),
            stopped: watch::channel(false).0,
            file_worker: std::sync::Mutex::new(None),
            catalog_urls: std::sync::RwLock::new(Vec::new()),
        });
        if service.command_extension.is_some() {
            let weak = Arc::downgrade(&service);
            tokio::spawn(async move {
                loop {
                    let Some(service) = weak.upgrade() else { break };
                    if *service.stopped.borrow() {
                        break;
                    }
                    let unlocked = service
                        .session
                        .try_lock()
                        .is_ok_and(|session| session.as_ref().is_some_and(|s| !s.ui_locked));
                    if unlocked
                        && service
                            .provider_error
                            .read()
                            .expect("provider state lock")
                            .as_ref()
                            .is_none_or(|e| e.retryable)
                    {
                        service.refresh_projection().await;
                    }
                    drop(service);
                    tokio::time::sleep(Duration::from_secs(2)).await;
                }
            });
        }
        *service.file_worker.lock().expect("file worker handle") =
            Some(Self::spawn_file_worker(&service));
        *service
            .startup_worker
            .lock()
            .expect("startup worker handle") = Some(Self::spawn_startup_worker(&service));
        Ok(service)
    }

    async fn extension_request(
        &self,
        operation_id: &str,
        action: &str,
        room: &str,
        text: &str,
        before: Option<&str>,
        limit: u16,
    ) -> Result<Response, String> {
        self.command_extension
            .as_ref()
            .ok_or("No conversation provider is configured")?
            .call(extensions::CommandRequest {
                version: VERSION,
                instance_id: &self.id,
                operation_id,
                action,
                room,
                text,
                before,
                limit,
            })
            .await
    }

    async fn refresh_projection(&self) {
        let _guard = self.projection_refresh.lock().await;
        let mut stopped = self.stopped.subscribe();
        let result = tokio::select! {
            _ = stopped.changed() => return,
            result = self.extension_request("projection-refresh", "list", "", "", None, 200) => result,
        };
        match result {
            Ok(Response::Projection {
                conversations,
                revision,
            }) if conversations.iter().all(|c| {
                c.id.starts_with("extension/cmd/") && c.provider.as_deref() == Some("cmd")
            }) =>
            {
                *self.projection.write().expect("projection lock") = (conversations, revision);
                *self.provider_error.write().expect("provider state lock") = None;
            }
            result => {
                let (code, message) = match result { Ok(Response::Error { code, message }) => (code, message), Err(message) => ("unavailable".into(), message), _ => ("version".into(), "Conversation provider returned an incompatible response. Update its service binding.".into()) };
                let retryable = matches!(code.as_str(), "transport" | "timeout" | "unavailable");
                if !retryable {
                    *self.projection.write().expect("projection lock") =
                        (Vec::new(), String::new());
                }
                *self.provider_error.write().expect("provider state lock") =
                    Some(gchat_api::ProviderStatus {
                        id: "cmd".into(),
                        code,
                        message,
                        retryable,
                    });
            }
        }
    }

    fn require(&self, capability: Capability) -> Result<(), String> {
        if self.capabilities.contains(&capability) {
            Ok(())
        } else {
            Err("this instance does not grant the requested operation".into())
        }
    }

    fn info(&self, locked: bool) -> InstanceInfo {
        InstanceInfo {
            id: self.id.clone(),
            label: self.label.clone(),
            boot_id: self.boot.clone(),
            locked,
            protocol_locked: false,
            profile_exists: true,
            archive_exists: self.archive.exists(),
            safety_number: self.runtime.sdk_client().identity().safety_number,
            capabilities: self
                .capabilities
                .iter()
                .map(|c| format!("{c:?}"))
                .chain(self.command_extension.as_ref().map(|_| "cmd".into()))
                .chain(std::iter::once(gchat_api::files::CAPABILITY.into()))
                .chain(self.runtime.network_client().map(|_| "networks.v1".into()))
                .collect(),
        }
    }

    pub async fn dispatch(&self, envelope: RequestEnvelope) -> ResponseEnvelope {
        let response = if envelope.version != VERSION {
            Response::Error {
                code: "version".into(),
                message: "unsupported chat API version".into(),
            }
        } else if !matches!(envelope.request, Request::Identify)
            && envelope.instance_id.as_deref() != Some(&self.id)
        {
            Response::Error {
                code: "instance".into(),
                message: "request belongs to a different instance".into(),
            }
        } else {
            let mut stopped = self.stopped.subscribe();
            let result = if *stopped.borrow() {
                Err("instance disconnected".into())
            } else {
                tokio::select! {
                    biased;
                    _ = stopped.changed() => Err("instance disconnected; admitted operations are not replayed automatically".into()),
                    result = self.handle(envelope.request) => result,
                }
            };
            result.unwrap_or_else(|message| Response::Error {
                code: if *self.stopped.borrow() {
                    "disconnected"
                } else {
                    "rejected"
                }
                .into(),
                message,
            })
        };
        ResponseEnvelope {
            version: VERSION,
            instance_id: self.id.clone(),
            response,
        }
    }

    async fn handle(&self, request: Request) -> Result<Response, String> {
        self.handle_mode(request, false).await
    }

    async fn handle_mode(&self, request: Request, admitted: bool) -> Result<Response, String> {
        let request = lifecycle_request(request);
        if let Request::Networks { request } = request {
            return Box::pin(self.networks_request(request))
                .await
                .map(|response| Response::Networks { response });
        }
        if let Request::Files { request } = request {
            return self
                .files_request(request)
                .await
                .map(|snapshot| Response::Files { snapshot });
        }
        let (request, search) = match request {
            Request::Search {
                conversation,
                text,
                before,
                limit,
            } => {
                if text.is_empty() || text.len() > 256 {
                    return Err("Search requires 1–256 UTF-8 bytes".into());
                }
                (
                    Request::History {
                        conversation,
                        before,
                        limit,
                    },
                    Some(text.to_lowercase()),
                )
            }
            request => (request, None),
        };
        if let Request::Events { after, wait_ms } = request {
            let deadline = Instant::now() + Duration::from_millis(u64::from(wait_ms.min(20_000)));
            loop {
                let revision = self.snapshot().await?.revision;
                if revision != after || Instant::now() >= deadline {
                    return Ok(Response::Changed { revision });
                }
                tokio::time::sleep(Duration::from_millis(200)).await;
            }
        }
        // Acquire mutation ordering before the short-lived archive-state lock.
        let _network_lifecycle = if matches!(request, Request::Lock) {
            Some(self.network_operations.lock().await)
        } else {
            None
        };
        // Ordinary sends may wait independently; the SDK orders MLS admission.
        // Commands which change membership still exclude concurrent sends.
        let ordinary_send = matches!(&request, Request::Submit { text, .. } if !text.starts_with('/') || matches!(text.split_whitespace().next(), Some("/say" | "/me" | "/join" | "/create")));
        let _send = if ordinary_send {
            Some(self.operations.read().await)
        } else {
            None
        };
        let _mutation = if matches!(request, Request::Submit { .. }) && !ordinary_send {
            Some(self.operations.write().await)
        } else {
            None
        };
        let mut session = self.session.lock().await;
        if let Request::Identify = request {
            return Ok(Response::Instance {
                instance: self.info(session.as_ref().is_none_or(|s| s.ui_locked)),
            });
        }
        if let Request::Unlock { passphrase, create } = request {
            let started = Instant::now();
            self.require(Capability::ChannelMember)?;
            let passphrase = Zeroizing::new(passphrase);
            if passphrase.len() > 4096 {
                return Err("passphrase exceeds bound".into());
            }
            if session.is_none() {
                if create && passphrase.chars().count() < 8 {
                    return Err("choose a passphrase of at least eight characters".into());
                }
                let client =
                    ClientHandle::open_service(&self.archive, &passphrase, &self.runtime, create)
                        .await?;
                let urls = self
                    .catalog_urls
                    .read()
                    .map_err(|_| "catalog configuration lock")?
                    .clone();
                client.configure_catalogs(&urls).await?;
                let (store, mut state): (_, UiState) = ChatServiceStore::open_or_create(
                    &self.archive.with_extension("service"),
                    &passphrase,
                )?;
                client.configure_presence(state.presence_enabled).await?;
                let safety = client.safety_number().to_string();
                if (!state.instance_id.is_empty() && state.instance_id != self.id)
                    || (!state.safety_number.is_empty() && state.safety_number != safety)
                {
                    return Err("chat service state belongs to a different instance".into());
                }
                for text in &mut state.command_history {
                    *text = recall_text(text);
                }
                for entry in &mut state.input_history {
                    entry.text = recall_text(&entry.text);
                }
                state.instance_id = self.id.clone();
                state.safety_number = safety;
                state.file_key.get_or_insert_with(rand::random);
                store.save(&state)?;
                *session = Some(Unlocked {
                    files: None,
                    file_error: Some("Preparing encrypted file cache…".into()),
                    ui_locked: false,
                    client,
                    store,
                    state,
                });
            }
            if let Some(current) = session.as_mut() {
                if current.ui_locked {
                    current.store.verify_passphrase(&passphrase)?;
                    current.ui_locked = false;
                }
            }
            let snapshot = self.project(session.as_ref());
            drop(session);
            latency("local_unlock", started);
            self.startup.notify_one();
            return Ok(Response::Snapshot { snapshot });
        }
        if let Request::Lock = request {
            if let Some(current) = session.as_mut() {
                current.client.save().await?;
                Self::save_message_metadata(current)?;
                if let Some(files) = &current.files {
                    files.enabled(false).await?;
                }
                current.ui_locked = true;
            }
            drop(session);
            self.lock_networks().await?;
            return Ok(Response::Instance {
                instance: self.info(true),
            });
        }
        if let Request::Snapshot = request {
            if let Some(current) = session.as_mut().filter(|s| !s.ui_locked) {
                Self::refresh_channel_topics(current).await?;
            }
            return Ok(Response::Snapshot {
                snapshot: self.project(session.as_ref()),
            });
        }
        if let Request::NetworkStatus = request {
            return Ok(Response::NetworkStatus {
                status: if session.as_ref().is_none_or(|s| s.ui_locked) {
                    gchat_api::NetworkStatus::new(gchat_api::NetworkState::Locked)
                } else {
                    self.runtime.network_status().await?
                },
            });
        }
        if let Request::Catalogue { conversation } = request {
            return Ok(Response::Catalogue {
                commands: self.context_commands(if session.as_ref().is_none_or(|s| s.ui_locked) {
                    None
                } else {
                    conversation.as_deref()
                }),
            });
        }
        let Some(unlocked) = session.as_mut().filter(|s| !s.ui_locked) else {
            return Ok(Response::Error { code: "locked".into(), message: "Unlock this instance's chat archive. Receiving continues while the archive is locked.".into() });
        };
        match request {
            Request::ImportNetworkInvitation { code } => {
                let code = Zeroizing::new(code);
                if code.len() > gchat_api::MAX_NETWORK_INVITATION_BYTES {
                    return Err("Network invitation exceeds size limit".into());
                }
                self.runtime.import_network_invitation(code.trim()).await?;
                Ok(Response::NetworkStatus {
                    status: self.runtime.network_status().await?,
                })
            }
            Request::History {
                conversation,
                before,
                limit,
            } => {
                if conversation.starts_with("extension/cmd/") {
                    drop(session);
                    let response = self
                        .extension_request(
                            "history-read-only",
                            if search.is_some() {
                                "search"
                            } else {
                                "history"
                            },
                            &conversation,
                            search.as_deref().unwrap_or(""),
                            before.as_deref(),
                            limit.clamp(1, 200),
                        )
                        .await?;
                    if matches!(&response, Response::Error { code, .. } if matches!(code.as_str(), "authentication" | "forbidden" | "instance" | "version"))
                    {
                        self.refresh_projection().await;
                    }
                    let session = self.session.lock().await;
                    if session.as_ref().is_none_or(|s| s.ui_locked) {
                        return Ok(Response::Error {
                            code: "locked".into(),
                            message: "Archive locked".into(),
                        });
                    }
                    return Ok(response);
                }
                let archive = unlocked.client.archive_snapshot();
                let mut candidate = unlocked.state.clone();
                observe_messages(&mut candidate, &archive);
                if candidate.message_metadata != unlocked.state.message_metadata {
                    unlocked.store.save(&candidate)?;
                    unlocked.state = candidate;
                }
                let all_messages = conversation_messages(&archive, &conversation)?;
                let messages: Vec<_> = all_messages
                    .iter()
                    .filter(|m| {
                        search.as_ref().is_none_or(|query| {
                            m.text.to_lowercase().contains(query)
                                || m.sender_name.to_lowercase().contains(query)
                        })
                    })
                    .collect();
                let end = match before {
                    Some(id) => messages
                        .iter()
                        .position(|m| hex(&m.id) == id)
                        .ok_or("history cursor is not in this conversation")?,
                    None => messages.len(),
                };
                let start = end.saturating_sub(usize::from(limit.clamp(1, 200)));
                let messages = messages[start..end]
                    .iter()
                    .map(|m| message(&conversation, m, &unlocked.state))
                    .collect::<Vec<_>>();
                let before = if start > 0 {
                    messages.first().map(|m| m.id.clone())
                } else {
                    None
                };
                Ok(Response::History {
                    page: HistoryPage { messages, before },
                })
            }
            Request::MarkRead {
                conversation,
                message_id,
            } => {
                if conversation.starts_with("extension/cmd/") {
                    drop(session);
                    return self
                        .extension_request(
                            "mark-read-position",
                            "read",
                            &conversation,
                            &message_id,
                            None,
                            200,
                        )
                        .await;
                }
                let archive = unlocked.client.archive_snapshot();
                let messages = conversation_messages(&archive, &conversation)?;
                let requested = messages
                    .iter()
                    .position(|m| hex(&m.id) == message_id)
                    .ok_or("unknown read marker")?;
                let current = unlocked
                    .state
                    .read
                    .get(&conversation)
                    .and_then(|id| messages.iter().position(|m| hex(&m.id) == *id));
                if current.is_none_or(|index| requested > index) {
                    unlocked.state.read.insert(conversation, message_id);
                    unlocked.store.save(&unlocked.state)?;
                }
                Ok(Response::Applied {
                    conversation: None,
                    notice: None,
                })
            }
            Request::Complete { conversation, text } => {
                let commands: Vec<Completion> = self
                    .context_commands(conversation.as_deref())
                    .into_iter()
                    .filter(|c| c.available)
                    .map(|c| Completion {
                        text: c.name,
                        description: c.description,
                    })
                    .collect();
                let projection = self.projection.read().expect("projection lock");
                let items = if let Some(room) = projection
                    .0
                    .iter()
                    .find(|c| Some(c.id.as_str()) == conversation.as_deref())
                {
                    if text.starts_with('@') {
                        commands
                            .into_iter()
                            .filter(|c| {
                                c.text.to_lowercase().starts_with(&text.to_lowercase())
                                    && c.text != text
                            })
                            .take(20)
                            .collect()
                    } else {
                        member_completions(&room.members, &text).unwrap_or_else(|| {
                            commands
                                .into_iter()
                                .filter(|c: &Completion| {
                                    c.text.starts_with(&text) && c.text != text
                                })
                                .collect()
                        })
                    }
                } else {
                    completions(
                        &unlocked.client.archive_snapshot(),
                        conversation.as_deref(),
                        &text,
                        commands,
                    )
                };
                Ok(Response::Completed { items })
            }
            Request::Submit {
                operation_id,
                conversation,
                text,
            } => {
                if operation_id.len() < 16
                    || operation_id.len() > 128
                    || !operation_id
                        .bytes()
                        .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'-' | b'_'))
                {
                    return Err("invalid operation identifier".into());
                }
                if text.is_empty() || text.len() > gchat_api::MAX_INPUT_BYTES {
                    return Err(format!(
                        "message must contain 1–{} UTF-8 bytes",
                        gchat_api::MAX_INPUT_BYTES
                    ));
                }
                let digest = hex(&Sha256::digest(
                    serde_json::to_vec(&(conversation.as_ref(), &text))
                        .map_err(|e| e.to_string())?,
                ));
                if let Some(previous) = unlocked.state.operations.get(&operation_id) {
                    if previous.digest != digest {
                        return Err(
                            "operation identifier was already used for different contents".into(),
                        );
                    }
                    if !admitted || previous.response.is_some() {
                        return Ok(previous.response.clone().unwrap_or_else(|| Response::Error { code: "outcome_unknown".into(), message: "Operation was interrupted after admission; delivery is unknown. It will not be sent again automatically.".into() }));
                    }
                } else if admitted {
                    return Err("RPC operation admission is missing".into());
                }
                if !admitted {
                    unlocked
                        .state
                        .operations
                        .retain(|_, op| op.at.saturating_add(7 * 24 * 3600) > now());
                    if unlocked.state.operations.len() >= OPERATION_LIMIT {
                        return Err(
                            "chat operation journal is full; retry after retained entries expire"
                                .into(),
                        );
                    }
                    unlocked.state.operations.insert(
                        operation_id.clone(),
                        OperationRecord {
                            action: String::new(),
                            conversation: None,
                            digest,
                            at: now(),
                            response: None,
                            rpc: None,
                        },
                    );
                    unlocked.store.save(&unlocked.state)?;
                }
                // Keep only the command name, never arguments, credentials or message bodies.
                if let Some(record) = unlocked.state.operations.get_mut(&operation_id) {
                    record.action = if text.starts_with('/') {
                        text.split_whitespace()
                            .next()
                            .unwrap_or("Command")
                            .to_string()
                    } else {
                        "Send message".into()
                    };
                    record.conversation = conversation.clone();
                }
                unlocked.store.save(&unlocked.state)?;
                // Persist admission before any protocol mutation. A crash cannot silently replay it.
                let client = unlocked.client.clone();
                self.active_operations
                    .lock()
                    .expect("active operations")
                    .insert(operation_id.clone());
                let _active = InFlight {
                    id: &operation_id,
                    operations: &self.active_operations,
                };
                let started = Instant::now();
                drop(session);
                let response =
                    match self.validate_submission(&client, conversation.as_deref(), &text) {
                        Err(message) => Response::Error {
                            code: "rejected".into(),
                            message,
                        },
                        Ok(()) => match self
                            .submit(&client, conversation.as_deref(), &text, &operation_id)
                            .await
                        {
                            Ok(response) => response,
                            // Once a protocol call started, failure does not prove non-delivery.
                            Err(message) => Response::Error {
                                code: "outcome_unknown".into(),
                                message,
                            },
                        },
                    };
                latency("command_completion", started);
                client.save().await?;
                let mut session = self.session.lock().await;
                let unlocked = session
                    .as_mut()
                    .ok_or("instance disconnected; operation outcome unknown")?;
                // Keep destination context, and never put bearer invitations into recall.
                let history_text = recall_text(&text);
                let mut candidate = unlocked.state.clone();
                observe_messages(&mut candidate, &client.archive_snapshot());
                candidate.command_history.push(history_text.clone());
                candidate.input_history.push(gchat_api::InputHistoryEntry {
                    conversation,
                    text: history_text,
                });
                if candidate.input_history.len() > HISTORY_LIMIT {
                    candidate.input_history.remove(0);
                }
                if candidate.command_history.len() > HISTORY_LIMIT {
                    candidate.command_history.remove(0);
                }
                candidate
                    .operations
                    .get_mut(&operation_id)
                    .unwrap()
                    .response = Some(response.clone());
                // Readers must never observe a terminal outcome whose save failed.
                unlocked.store.save(&candidate)?;
                unlocked.state = candidate;
                Ok(response)
            }
            _ => Err("invalid request".into()),
        }
    }

    pub async fn snapshot(&self) -> Result<Snapshot, String> {
        let mut session = self.session.lock().await;
        if let Some(current) = session.as_mut().filter(|s| !s.ui_locked) {
            Self::refresh_channel_topics(current).await?;
        }
        Ok(self.project(session.as_ref()))
    }

    fn save_message_metadata(current: &mut Unlocked) -> Result<(), String> {
        let mut candidate = current.state.clone();
        observe_messages(&mut candidate, &current.client.archive_snapshot());
        current.store.save(&candidate)?;
        current.state = candidate;
        Ok(())
    }

    async fn refresh_channel_topics(current: &mut Unlocked) -> Result<(), String> {
        let mut candidate = current.state.clone();
        let archive = current.client.archive_snapshot();
        observe_messages(&mut candidate, &archive);
        for channel in &archive.channels {
            let key = record_key(channel);
            let topic = if channel.active {
                current.client.channel_topic(channel.id).await.ok()
            } else {
                None
            };
            if let Some(topic) = &topic {
                candidate
                    .topics
                    .insert(channel_key(channel.id), topic.clone());
            }
            let observed = ObservedChannel {
                members: channel
                    .members
                    .iter()
                    .map(|m| (hex(&m.id.0), m.display_name.clone()))
                    .collect(),
                topic: topic.unwrap_or_else(|| {
                    candidate
                        .topics
                        .get(&channel_key(channel.id))
                        .cloned()
                        .unwrap_or_default()
                }),
                active: channel.active,
            };
            // First observation is a baseline, not a synthetic burst of joins.
            let previous = candidate.observed_channels.get(&key).cloned().or_else(|| {
                (!channel.active)
                    .then(|| {
                        candidate
                            .observed_channels
                            .get(&channel_key(channel.id))
                            .cloned()
                    })
                    .flatten()
            });
            if let Some(old) = previous {
                if old.active && !observed.active {
                    record_activity(
                        &mut candidate,
                        key.clone(),
                        "left",
                        "This channel is no longer active for this profile.".into(),
                    );
                } else if observed.active {
                    for (id, name) in &observed.members {
                        if !old.members.contains_key(id) {
                            record_activity(
                                &mut candidate,
                                key.clone(),
                                "joined",
                                format!("{name} joined."),
                            );
                        }
                    }
                    for (id, name) in &old.members {
                        if !observed.members.contains_key(id) {
                            record_activity(
                                &mut candidate,
                                key.clone(),
                                "left",
                                format!("{name} left or was removed."),
                            );
                        }
                    }
                    if old.topic != observed.topic {
                        record_activity(
                            &mut candidate,
                            key.clone(),
                            "topic",
                            if observed.topic.is_empty() {
                                "Topic cleared.".into()
                            } else {
                                format!("Topic: {}", observed.topic)
                            },
                        );
                    }
                }
            }
            if !channel.active {
                candidate.observed_channels.remove(&channel_key(channel.id));
            }
            candidate.observed_channels.insert(key, observed);
        }
        if candidate.message_metadata != current.state.message_metadata
            || candidate.topics != current.state.topics
            || candidate.observed_channels != current.state.observed_channels
        {
            current.store.save(&candidate)?;
            current.state = candidate;
        }
        Ok(())
    }

    fn project(&self, session: Option<&Unlocked>) -> Snapshot {
        let instance = self.info(session.as_ref().is_none_or(|s| s.ui_locked));
        let mut conversations = Vec::new();
        let mut command_history = Vec::new();
        let mut input_history = Vec::new();
        if let Some(session) = session.filter(|s| !s.ui_locked) {
            let archive = session.client.archive_snapshot();
            for channel in &archive.channels {
                let id = record_key(channel);
                conversations.push(Conversation {
                    provider: None,
                    input_limit_bytes: gchat_api::MAX_INPUT_BYTES,
                    commands: Vec::new(),
                    id: id.clone(),
                    channel_id: hex(&channel.id.0),
                    kind: if channel.active {
                        ConversationKind::Channel
                    } else {
                        ConversationKind::Archive
                    },
                    name: format!("#{}", channel.title),
                    topic: session
                        .state
                        .topics
                        .get(&channel_key(channel.id))
                        .cloned()
                        .unwrap_or_default(),
                    active: channel.active,
                    owner: channel.role == ChannelRole::Owner,
                    visibility: Some(
                        if channel.visibility == ChannelVisibility::Public {
                            "public"
                        } else {
                            "private"
                        }
                        .into(),
                    ),
                    directory: session
                        .state
                        .publications
                        .get(&channel_key(channel.id))
                        .cloned(),
                    members: channel
                        .members
                        .iter()
                        .map(|m| Member {
                            id: hex(&m.id.0),
                            nickname: m.display_name.clone(),
                            is_self: m.is_self,
                            recently_active: Some(
                                session
                                    .client
                                    .recently_active(&channel.protocol_name, m.id.0),
                            ),
                            capabilities: Vec::new(),
                        })
                        .collect(),
                    unread: unread(&session.state, &id, &channel.messages),
                    last_message_id: channel.messages.last().map(|m| hex(&m.id)),
                });
            }
            for pm in &archive.scoped_pms {
                let id = query_key(pm.id);
                conversations.push(Conversation {
                    provider: None,
                    input_limit_bytes: gchat_api::MAX_INPUT_BYTES,
                    commands: Vec::new(),
                    id: id.clone(),
                    channel_id: hex(&pm.id.channel_id.0),
                    kind: if pm.active {
                        ConversationKind::Query
                    } else {
                        ConversationKind::Archive
                    },
                    name: pm.remote_display_name.clone(),
                    topic: archive
                        .channels
                        .iter()
                        .find(|c| c.id == pm.id.channel_id)
                        .map(|c| format!("Private in #{}", c.title))
                        .unwrap_or_default(),
                    active: pm.active,
                    owner: false,
                    visibility: None,
                    directory: None,
                    members: archive
                        .channels
                        .iter()
                        .find(|c| c.id == pm.id.channel_id)
                        .map(|channel| {
                            channel
                                .members
                                .iter()
                                .map(|m| Member {
                                    id: hex(&m.id.0),
                                    nickname: m.display_name.clone(),
                                    is_self: m.is_self,
                                    recently_active: Some(
                                        session
                                            .client
                                            .recently_active(&channel.protocol_name, m.id.0),
                                    ),
                                    capabilities: Vec::new(),
                                })
                                .collect()
                        })
                        .unwrap_or_default(),
                    unread: unread(&session.state, &id, &pm.messages),
                    last_message_id: pm.messages.last().map(|m| hex(&m.id)),
                });
            }
            for (index, legacy) in archive.legacy.conversations.list.iter().enumerate() {
                conversations.push(Conversation {
                    provider: None,
                    input_limit_bytes: gchat_api::MAX_INPUT_BYTES,
                    commands: Vec::new(),
                    id: format!("legacy/{index}"),
                    channel_id: String::new(),
                    kind: ConversationKind::Archive,
                    name: legacy.key().to_string(),
                    topic: "Legacy archive · read only · channel identity unavailable".into(),
                    active: false,
                    owner: false,
                    visibility: None,
                    directory: None,
                    members: Vec::new(),
                    unread: 0,
                    last_message_id: legacy.messages().last().map(|m| hex(&m.id)),
                });
            }
            command_history = session.state.command_history.clone();
            input_history = session.state.input_history.clone();
            conversations.extend(self.projection.read().expect("projection lock").0.clone());
        }
        let provider_errors: Vec<_> = if instance.locked {
            Vec::new()
        } else {
            self.provider_error
                .read()
                .expect("provider state lock")
                .clone()
                .into_iter()
                .collect()
        };
        let activity = session
            .filter(|s| !s.ui_locked)
            .map(|s| s.state.activity.clone())
            .unwrap_or_default();
        let mut operations: Vec<_> = session.filter(|s| !s.ui_locked).into_iter()
            .flat_map(|s| s.state.operations.iter())
            .filter(|(_, r)| !r.action.is_empty() && r.at.saturating_add(7 * 24 * 3600) > now())
            .map(|(id, r)| {
                let (state, output, message) = match &r.response {
                    Some(Response::Output { output, .. }) => ("complete", Some(output.clone()), None),
                    Some(Response::Applied { notice, .. }) => ("complete", None, notice.clone()),
                    Some(Response::Error { code, message }) => (if code == "rejected" { "rejected" } else { "unknown" }, None, Some(message.clone())),
                    Some(_) => ("complete", None, None),
                    None if self.active_operations.lock().expect("active operations").contains(id) => ("pending", None, Some("Working on this request.".into())),
                    None => ("unknown", None, Some("No confirmed result retained. This operation will not run again automatically.".into())),
                };
                gchat_api::OperationDetail { network: None, id: id.clone(), instance: self.id.clone(), conversation: r.conversation.clone(), action: r.action.clone(), started: r.at, state: state.into(), output, message }
            }).collect();
        operations.sort_by_key(|r| r.started);
        if operations.len() > 30 {
            operations.drain(..operations.len() - 30);
        }
        let delivery_revision = session
            .filter(|s| !s.ui_locked)
            .map(|s| &s.state.message_metadata);
        let revision = hex(&Sha256::digest(
            serde_json::to_vec(&(
                &instance,
                &conversations,
                &command_history,
                &input_history,
                &provider_errors,
                &operations,
                &activity,
                &delivery_revision,
                &self.projection.read().expect("projection lock").1,
            ))
            .expect("serializable projection"),
        ));
        Snapshot {
            instance,
            revision,
            conversations,
            command_history,
            input_history,
            provider_errors,
            operations: Some(operations),
            activity: Some(activity),
            presence_enabled: Some(
                session.is_some_and(|s| !s.ui_locked && s.state.presence_enabled),
            ),
        }
    }

    fn validate_submission(
        &self,
        client: &ClientHandle,
        conversation: Option<&str>,
        text: &str,
    ) -> Result<(), String> {
        let archive = client.archive_snapshot();
        if let Some(args) = network_arguments(text) {
            if args.starts_with("join GCNI1-")
                || matches!(args, "dns on" | "dns off" | "dns status")
            {
                return Ok(());
            }
            return Err("Usage: /network join invitation-code | dns on|off|status".into());
        }
        if let Some(args) = text.strip_prefix("/join ") {
            if self.projected_join(&archive, split_head(args).0)?.is_some() {
                return Ok(());
            }
        }
        if let Some(id) = conversation.filter(|id| id.starts_with("extension/cmd/")) {
            let projection = self.projection.read().expect("projection lock");
            let room = projection
                .0
                .iter()
                .find(|c| c.id == id)
                .ok_or("Conversation is unavailable; refresh its provider")?;
            if !text.starts_with('/') && text.len() > room.input_limit_bytes {
                return Err(format!(
                    "This conversation accepts at most {} UTF-8 bytes. Nothing was submitted.",
                    room.input_limit_bytes
                ));
            }
            return Ok(()); // The configured provider validates its own capabilities and syntax.
        }
        let Some(command) = text.strip_prefix('/') else {
            self.require(Capability::ChannelMember)?;
            conversation_messages(
                &archive,
                conversation.ok_or("Open a conversation before sending")?,
            )?;
            return Ok(());
        };
        let (name, args) = split_head(command);
        let name = format!("/{}", name.to_ascii_lowercase());
        let spec = self
            .command_specs()
            .into_iter()
            .find(|c| c.name == name)
            .ok_or_else(|| {
                format!("Unknown command {name}. Use /help or /say for literal text.")
            })?;
        if !spec.available {
            return Err(format!("{}: {}", spec.name, spec.description));
        }
        if let Some(capability) = &spec.capability {
            if !self
                .capabilities
                .iter()
                .any(|c| format!("{c:?}") == *capability)
            {
                return Err(format!("This instance does not grant {capability}"));
            }
        }
        if spec.scope == "conversation" {
            context_channel(&archive, conversation)?;
        }
        match name.as_str() {
            "/owner" => {
                self.require(Capability::ChannelAdmin)?;
                let channel = context_channel(&archive, conversation)?;
                if channel.role != ChannelRole::Owner {
                    return Err("Only the channel owner can transfer ownership".into());
                }
                let member = resolve_member(channel, args)?;
                if channel.self_member_id == Some(member) {
                    return Err("Choose another channel member".into());
                }
            }
            "/part" => {
                let channel = context_channel(&archive, conversation)?;
                if channel.role == ChannelRole::Owner {
                    self.require(Capability::ChannelAdmin)?;
                    if args != "--close" {
                        let target = args.strip_prefix("--transfer ").ok_or(
                            "Choose /part --transfer nickname-or-member-id or /part --close",
                        )?;
                        if channel.self_member_id == Some(resolve_member(channel, target)?) {
                            return Err("Choose another channel member".into());
                        }
                    }
                } else if !args.is_empty() {
                    return Err("Usage: /part".into());
                }
            }
            "/nick" => {
                gcoms::runtime::contacts::validate_channel_change(
                    &gcoms::sdk::ChannelChange::Nickname(args.into()),
                )?;
            }
            "/topic" if !args.is_empty() => {
                self.require(Capability::ChannelAdmin)?;
                if context_channel(&archive, conversation)?.role != ChannelRole::Owner {
                    return Err("Only the channel owner can change the topic".into());
                }
                gcoms::runtime::contacts::validate_channel_change(
                    &gcoms::sdk::ChannelChange::Topic(if args == "--clear" {
                        String::new()
                    } else {
                        args.into()
                    }),
                )?;
            }
            "/query" | "/msg" | "/kick" => {
                resolve_member(context_channel(&archive, conversation)?, split_head(args).0)?;
            }
            "/join" | "/create" => {
                let (target, nickname) = split_head(args);
                let already_joined = name == "/join"
                    && archive.channels.iter().any(|c| {
                        c.active && c.title.eq_ignore_ascii_case(target.trim_start_matches('#'))
                    });
                if !already_joined {
                    if target.is_empty() || nickname.trim().is_empty() {
                        return Err(format!("Usage: {}", spec.usage));
                    }
                    if name == "/join" && !target.starts_with('#') {
                        let invite = gcoms::runtime::contacts::inspect_channel_invitation(target)
                            .map_err(|_| "Invalid invitation. Paste the complete link.")?;
                        if invite.expires_at <= now() {
                            return Err(
                                "This invitation has expired. Ask for a new invitation.".into()
                            );
                        }
                    }
                }
            }
            "/say" | "/me" if args.is_empty() => return Err(format!("Usage: {}", spec.usage)),
            _ => {}
        }
        Ok(())
    }

    async fn submit(
        &self,
        client: &ClientHandle,
        conversation: Option<&str>,
        text: &str,
        operation_id: &str,
    ) -> Result<Response, String> {
        let archive = client.archive_snapshot();
        let applied = |conversation, notice| {
            Ok(Response::Applied {
                conversation,
                notice,
            })
        };
        if let Some(args @ ("dns on" | "dns off" | "dns status")) = network_arguments(text) {
            if args != "dns status" {
                self.runtime.configure_network_dns(args == "dns on").await?;
            }
            let status = self.runtime.network_dns_status().await?;
            let notice = if !status.opted_in {
                if status.pending {
                    "Public DNS is off; removal is queued.".into()
                } else {
                    "Public DNS is off.".into()
                }
            } else if let Some(name) = status
                .name
                .filter(|_| !status.removed && status.lease_expires_at.unwrap_or(0) > now())
            {
                if status.published {
                    format!(
                        "Public DNS: {} (lease expires at {}).",
                        name,
                        status.lease_expires_at.unwrap_or(0)
                    )
                } else {
                    format!(
                        "DNS name reserved: {}; publication confirmation is pending.",
                        name
                    )
                }
            } else {
                "Public DNS is on; waiting for a verified reachable listener and publication."
                    .into()
            };
            return Ok(Response::Applied {
                conversation: conversation.map(str::to_owned),
                notice: Some(notice),
            });
        }
        if let Some(code) = network_arguments(text).and_then(|args| args.strip_prefix("join ")) {
            self.runtime.import_network_invitation(code.trim()).await?;
            return Ok(Response::Applied {
                conversation: conversation.map(str::to_string),
                notice: Some("Network invitation saved. Connecting in the background.".into()),
            });
        }
        if let Some(room) = conversation.filter(|id| id.starts_with("extension/cmd/")) {
            let (name, args) = text
                .strip_prefix('/')
                .map(split_head)
                .unwrap_or(("say", text));
            match name.to_ascii_lowercase().as_str() {
                "query" | "msg" => {
                    let (member, body) = split_head(args);
                    let response = self.extension_request(operation_id, "query", room, member, None, 200).await?;
                    self.refresh_projection().await;
                    if name.eq_ignore_ascii_case("msg") && !body.is_empty() {
                        if let Response::Applied { conversation: Some(target), .. } = &response {
                            return self.extension_request(operation_id, "send", target, body, None, 200).await;
                        }
                    }
                    return Ok(response);
                }
                "say" | "me" => {
                    let body = if name == "me" { format!("\u{1}ACTION {args}\u{1}") } else { args.into() };
                    let response = self.extension_request(operation_id, "send", room, &body, None, 200).await?;
                    self.refresh_projection().await;
                    return Ok(response);
                }
                "names" => {
                    let projection = self.projection.read().expect("projection lock");
                    let channel = projection.0.iter().find(|c| c.id == room).ok_or("Conversation unavailable")?;
                    return Ok(Response::Output { conversation: Some(room.into()), output: gchat_api::CommandOutput::Text { title: format!("Nicks in {}", channel.name), text: channel.members.iter().map(|m| m.nickname.clone()).collect::<Vec<_>>().join("  ") } });
                }
                "help" | "status" | "list" | "close" | "hide" | "refresh" | "join" => {}
                _ => return Ok(Response::Error { code: "rejected".into(), message: format!("/{name} is unavailable in this conversation. Use /help; addressed capability commands can be entered directly.") }),
            }
        }
        let Some(command) = text.strip_prefix('/') else {
            self.require(Capability::ChannelMember)?;
            send(
                client,
                &archive,
                conversation.ok_or("open a channel or query before sending")?,
                text,
                operation_id,
            )
            .await?;
            return applied(conversation.map(str::to_string), None);
        };
        let (name, args) = split_head(command);
        match name.to_ascii_lowercase().as_str() {
            "cmd" | "cmd-list" | "cmd-history" => {
                let (room, body) = split_head(args);
                self.refresh_projection().await;
                if name == "cmd-list" {
                    let channels = self.projection.read().expect("projection lock").0.iter().map(|c| gchat_api::DirectoryEntry { name: c.name.clone(), joined: c.active, conversation: Some(c.id.clone()) }).collect();
                    return Ok(Response::Output { conversation: conversation.map(str::to_string), output: gchat_api::CommandOutput::Directory { channels } });
                }
                if name == "cmd-history" {
                    let projection = self.projection.read().expect("projection lock");
                    let matches = projection.0.iter().filter(|c| c.name.eq_ignore_ascii_case(room) || c.id == room).collect::<Vec<_>>();
                    let [target] = matches.as_slice() else { return Err("Unknown or ambiguous conversation".into()); };
                    return applied(Some(target.id.clone()), None);
                }
                let response = self.extension_request(operation_id, "send", room, body, None, 200).await?;
                self.refresh_projection().await;
                Ok(response)
            }
            "help" => Ok(Response::Output { conversation: conversation.map(str::to_string), output: gchat_api::CommandOutput::Help { commands: self.context_commands(conversation) } }),
            "status" => Ok(Response::Output { conversation: None, output: gchat_api::CommandOutput::Status { text: format!("{} joined channels. Closing a view keeps receiving; /lock hides the archive in every view; /quit stops this instance.", archive.channels.iter().filter(|c| c.active).count()) } }),
            "list" => Ok(Response::Output { conversation: conversation.map(str::to_string), output: gchat_api::CommandOutput::Directory { channels: archive.channels.iter().filter(|c| c.active).map(|c| gchat_api::DirectoryEntry { name: format!("#{}", c.title), joined: true, conversation: Some(channel_key(c.id)) }).chain(archive.public_descriptors.iter().map(|d| gchat_api::DirectoryEntry { name: format!("#{}", d.descriptor.title), joined: false, conversation: None })).chain(self.projection.read().expect("projection lock").0.iter().map(|c| gchat_api::DirectoryEntry { name: c.name.clone(), joined: c.active, conversation: Some(c.id.clone()) })).collect() } }),
            "close" | "hide" => Ok(Response::Output { conversation: conversation.map(str::to_string), output: gchat_api::CommandOutput::Close { conversation: conversation.ok_or("Select a conversation to close")?.into() } }),
            "nick" => {
                let channel = context_channel(&archive, conversation)?;
                client.change_channel(channel.id, gcoms::sdk::ChannelChange::Nickname(args.into())).await?;
                applied(conversation.map(str::to_owned), Some("Channel nickname updated. Your identity and history are unchanged.".into()))
            }
            "topic" => {
                let channel = context_channel(&archive, conversation)?;
                if args.is_empty() {
                    return Ok(Response::Output { conversation: conversation.map(str::to_owned), output: gchat_api::CommandOutput::Text { title: format!("Topic for #{}", channel.title), text: client.channel_topic(channel.id).await? } });
                }
                client.change_channel(channel.id, gcoms::sdk::ChannelChange::Topic(if args == "--clear" { String::new() } else { args.into() })).await?;
                applied(conversation.map(str::to_owned), None)
            }
            "owner" => {
                let channel = context_channel(&archive, conversation)?;
                let member = resolve_member(channel, args)?;
                client.change_channel(channel.id, gcoms::sdk::ChannelChange::Transfer(member.0)).await?;
                applied(conversation.map(str::to_owned), Some("Ownership transferred; the channel and history are unchanged.".into()))
            }
            "part" => {
                let channel = context_channel(&archive, conversation)?;
                if args == "--close" {
                    client.change_channel(channel.id, gcoms::sdk::ChannelChange::Close).await?;
                    let history = client.archive_snapshot().channels.iter().find(|c| c.id == channel.id).map(record_key);
                    return applied(history, Some("Channel closed. Offline members receive the closure when they reconnect. History is retained; unconfirmed sends are not marked delivered.".into()));
                }
                if channel.role == ChannelRole::Owner {
                    let member = resolve_member(channel, args.strip_prefix("--transfer ").ok_or("Choose the next owner")?)?;
                    client.change_channel(channel.id, gcoms::sdk::ChannelChange::Transfer(member.0)).await?;
                }
                client.change_channel(channel.id, gcoms::sdk::ChannelChange::Leave).await?;
                applied(conversation.map(str::to_owned), Some("Leave request saved. Membership ends when the owner processes it; your history is retained.".into()))
            }
            "me" => {
                self.require(Capability::ChannelMember)?;
                if args.is_empty() { return Err("Usage: /me action".into()); }
                send(client, &archive, conversation.ok_or("open a conversation first")?, &format!("\u{1}ACTION {args}\u{1}"), operation_id).await?;
                applied(conversation.map(str::to_string), None)
            }
            "names" => {
                let channel = context_channel(&archive, conversation)?;
                Ok(Response::Output { conversation: conversation.map(str::to_string), output: gchat_api::CommandOutput::Text { title: format!("Nicks in #{}", channel.title), text: channel.members.iter().map(|m| m.display_name.clone()).collect::<Vec<_>>().join("  ") } })
            }
            "presence" => {
                let enabled = match args { "on" => true, "off" => false, _ => return Err("Usage: /presence on|off".into()) };
                client.configure_presence(enabled).await?;
                let mut session = self.session.lock().await;
                let unlocked = session.as_mut().ok_or("Unlock the profile first")?;
                let mut candidate = unlocked.state.clone(); candidate.presence_enabled = enabled;
                unlocked.store.save(&candidate)?; unlocked.state = candidate;
                applied(None, Some(if enabled { "Recently-active sharing enabled. Signals expire; they do not confirm delivery." } else { "Recently-active sharing disabled." }.into()))
            }
            "publish" => {
                self.require(Capability::ChannelAdmin)?;
                let channel = context_channel(&archive, conversation)?;
                client.publish_channel(channel.id, "", args).await?;
                let mut session = self.session.lock().await;
                let unlocked = session.as_mut().ok_or("Unlock the profile first")?;
                let mut candidate = unlocked.state.clone(); candidate.publications.insert(channel_key(channel.id), args.into());
                unlocked.store.save(&candidate)?; unlocked.state = candidate;
                applied(conversation.map(str::to_string), Some("Channel published. You can retry publication without creating another channel.".into()))
            }
            "create" => {
                self.require(Capability::ChannelAdmin)?;
                let (choice, remaining) = split_head(args);
                let (visibility, args) = match choice {
                    "--public" => (ChannelVisibility::Public, remaining),
                    "--private" => (ChannelVisibility::Private, remaining),
                    _ => (ChannelVisibility::Private, args),
                };
                let (channel, nick) = split_head(args);
                if channel.is_empty() || nick.is_empty() {
                    return Err("Usage: /create [--private|--public] #channel nickname".into());
                }
                let id = client
                    .create_channel(
                        channel.trim_start_matches('#'),
                        nick,
                        64,
                        visibility,
                    )
                    .await?;
                applied(
                    Some(channel_key(id)),
                    None,
                )
            }
            "join" => {
                self.require(Capability::ChannelMember)?;
                let (destination, nick) = split_head(args);
                if destination.starts_with("extension/cmd/") {
                    let response = self.extension_request(operation_id, "join", destination, "", None, 200).await?;
                    self.refresh_projection().await;
                    return Ok(response);
                }
                if let Some(channel) = archive.channels.iter().find(|c| {
                    c.active
                        && c.title
                            .eq_ignore_ascii_case(destination.trim_start_matches('#'))
                }) {
                    return applied(Some(channel_key(channel.id)), None);
                }
                if nick.is_empty() {
                    return Err(
                        "Usage: /join invite-link nickname; /join #channel opens a joined channel"
                            .into(),
                    );
                }
                if destination.starts_with('#') {
                    let choices = archive
                        .public_descriptors
                        .iter()
                        .filter(|d| {
                            d.descriptor
                                .title
                                .eq_ignore_ascii_case(destination.trim_start_matches('#'))
                        })
                        .collect::<Vec<_>>();
                    match choices.as_slice() {
                        [descriptor] => client.join_public(&descriptor.descriptor, nick).await?,
                        [] => return Err("no public channel with that name; /refresh then /list, or use an invitation".into()),
                        _ => return Err("public channel name is ambiguous; use an invitation".into()),
                    }
                } else {
                    client
                        .join_with_invite(destination, nick, 120)
                        .await?;
                }
                let joined = client.archive_snapshot();
                let channel = joined
                    .channels
                    .iter()
                    .rev()
                    .find(|c| {
                        c.active
                            && !archive
                                .channels
                                .iter()
                                .any(|old| old.active && old.id == c.id)
                    })
                    .ok_or("join completed; refresh the channel list")?;
                applied(
                    Some(channel_key(channel.id)),
                    None,
                )
            }
            "query" | "msg" => {
                self.require(Capability::ChannelMember)?;
                let channel = context_channel(&archive, conversation)?;
                let (nick, body) = split_head(args);
                let member = resolve_member(channel, nick)?;
                let id = client.open_scoped_pm(channel.id, member)?;
                if name.eq_ignore_ascii_case("msg") && !body.is_empty() {
                    client.send_scoped_pm(id, body).await?;
                }
                applied(Some(query_key(id)), None)
            }
            "invite" => {
                self.require(Capability::ChannelAdmin)?;
                let channel = context_channel(&archive, conversation)?;
                let link = client.create_invite(channel.id, 3600).await?;
                let invitation = gcoms::runtime::contacts::inspect_channel_invitation(&link)?;
                let local_only = invitation.local_only;
                let link = if let Some(network) = self.runtime.network_client() {
                    gcoms_network::JoinInvitation {
                        version: 1,
                        network: network.shareable_identity()?,
                        network_invitation: None,
                        channel_invitation: Some(link),
                    }.encode_at(now())?
                } else { link };
                Ok(Response::Output { conversation: conversation.map(str::to_string), output: gchat_api::CommandOutput::Invitation { channel: channel.title.clone(), link, expires: invitation.expires_at, local_only } })
            }
            "kick" => {
                self.require(Capability::ChannelAdmin)?;
                let channel = context_channel(&archive, conversation)?;
                let member = resolve_member(channel, args.trim())?;
                client.remove_member(channel.id, member).await?;
                client.reconcile_channels().await?;
                applied(None, Some("Member removal accepted.".into()))
            }
            "say" => {
                self.require(Capability::ChannelMember)?;
                send(
                    client,
                    &archive,
                    conversation.ok_or("open a conversation first")?,
                    args,
                    operation_id,
                )
                .await?;
                applied(conversation.map(str::to_string), None)
            }
            "refresh" => {
                if self.command_extension.is_some() { self.refresh_projection().await; }
                client.reconcile_channels().await?;
                client.refresh_catalogs().await?;
                applied(
                    None,
                    Some("Channels and public catalogue refreshed.".into()),
                )
            }
            _ => Err(format!(
                "Unknown client command /{name}. Use /help or /say to send literal text."
            )),
        }
    }

    fn commands(&self) -> Vec<Completion> {
        let mut commands = command_catalogue(&self.capabilities);
        commands.push(Completion {
            text: "/presence".into(),
            description: "Optional recently-active signals: /presence on|off (default off)".into(),
        });
        commands.push(Completion {
            text: "/publish".into(),
            description: "Publish this public channel: /publish https://directory.example/".into(),
        });
        if self.command_extension.is_some() {
            commands.extend(
                [
                    ("/cmd-list", "List channels in the configured CMD extension"),
                    (
                        "/cmd",
                        "CMD extension: /cmd #channel exact addressed command",
                    ),
                    (
                        "/cmd-history",
                        "Read command results: /cmd-history #channel",
                    ),
                ]
                .into_iter()
                .map(|(text, description)| Completion {
                    text: text.into(),
                    description: description.into(),
                }),
            );
        }
        commands
    }

    fn command_specs(&self) -> Vec<gchat_api::CommandSpec> {
        let commands = self
            .commands()
            .into_iter()
            .map(|c| {
                let capability = match c.text.as_str() {
                    "/create" | "/invite" | "/kick" | "/owner" | "/publish" => {
                        Some("ChannelAdmin".into())
                    }
                    "/join" | "/query" | "/msg" | "/say" | "/me" | "/nick" => {
                        Some("ChannelMember".into())
                    }
                    _ => None,
                };
                gchat_api::CommandSpec {
                    usage: command_usage(&c.text).into(),
                    scope: if matches!(
                        c.text.as_str(),
                        "/query"
                            | "/msg"
                            | "/names"
                            | "/invite"
                            | "/kick"
                            | "/say"
                            | "/me"
                            | "/close"
                            | "/hide"
                            | "/nick"
                            | "/topic"
                            | "/owner"
                            | "/publish"
                            | "/part"
                    ) {
                        "conversation"
                    } else {
                        "instance"
                    }
                    .into(),
                    name: c.text,
                    description: c.description,
                    capability,
                    available: true,
                }
            })
            .collect::<Vec<_>>();
        commands
    }

    fn projected_join(
        &self,
        archive: &ArchiveData,
        target: &str,
    ) -> Result<Option<String>, String> {
        let projection = self.projection.read().expect("projection lock");
        let choices: Vec<_> = projection
            .0
            .iter()
            .filter(|c| c.id == target || c.name.eq_ignore_ascii_case(target))
            .collect();
        if choices.is_empty() {
            return if target.starts_with("extension/cmd/") {
                Err("Conversation provider has no such channel. Use /list to choose a current channel.".into())
            } else {
                Ok(None)
            };
        }
        let native = archive
            .channels
            .iter()
            .any(|c| c.active && c.title.eq_ignore_ascii_case(target.trim_start_matches('#')))
            || archive.public_descriptors.iter().any(|d| {
                d.descriptor
                    .title
                    .eq_ignore_ascii_case(target.trim_start_matches('#'))
            });
        if choices.len() != 1 || native {
            return Err(
                "Channel name is ambiguous. Use /list and select its exact conversation.".into(),
            );
        }
        Ok(Some(choices[0].id.clone()))
    }

    fn context_commands(&self, conversation: Option<&str>) -> Vec<gchat_api::CommandSpec> {
        let extension = conversation.is_some_and(|id| id.starts_with("extension/cmd/"));
        let mut commands: Vec<_> = self
            .command_specs()
            .into_iter()
            .map(|mut command| {
                if command.scope == "conversation" && conversation.is_none() {
                    command.available = false;
                    command
                        .description
                        .push_str(" Select a conversation first.");
                }
                if extension && matches!(command.name.as_str(), "/invite" | "/kick" | "/publish") {
                    command.available = false;
                    command.description = "Unavailable in this conversation provider.".into();
                }
                command
            })
            .collect();
        if let Some(room) = self
            .projection
            .read()
            .expect("projection lock")
            .0
            .iter()
            .find(|c| Some(c.id.as_str()) == conversation)
        {
            commands.extend(room.commands.clone());
        }
        commands
    }

    pub fn configure_catalogs(&self, urls: Vec<String>) {
        *self
            .catalog_urls
            .write()
            .expect("catalog configuration lock") = urls;
    }

    /// Owned by the service, never by an attachment or a discarded unlock request.
    fn spawn_startup_worker(service: &Arc<Self>) -> tokio::task::JoinHandle<()> {
        let weak = Arc::downgrade(service);
        let mut stopped = service.stopped.subscribe();
        let notify = service.startup.clone();
        tokio::spawn(async move {
            loop {
                tokio::select! {
                    _ = stopped.changed() => break,
                    _ = notify.notified() => {}
                }
                let Some(service) = weak.upgrade() else { break };
                if *stopped.borrow() {
                    break;
                }
                let started = Instant::now();
                // Lock/disconnect coordinate with restoration, so a finished open
                // cannot publish a child after the lifecycle barrier completes.
                {
                    let _lifecycle = service.network_operations.lock().await;
                    let inputs = {
                        let session = service.session.lock().await;
                        session.as_ref().filter(|s| !s.ui_locked).map(|s| {
                            (
                                s.files.clone(),
                                s.state.file_key,
                                s.state.file_config.clone(),
                            )
                        })
                    };
                    if let Some((existing, key, config)) = inputs {
                        let result = if let Some(files) = existing {
                            files.enabled(true).await.map(|_| files)
                        } else if let Some(key) = key {
                            files::FileRuntime::open(
                                &service.runtime,
                                &service.archive.with_extension("pieces"),
                                key,
                                config,
                            )
                            .await
                        } else {
                            Err("File cache key unavailable".into())
                        };
                        let mut session = service.session.lock().await;
                        if let Some(current) = session.as_mut().filter(|s| !s.ui_locked) {
                            match result {
                                Ok(files) => { current.files = Some(files); current.file_error = None; }
                                Err(error) => current.file_error = Some(format!("File cache unavailable: {error}. Chat history remains available.")),
                            }
                        }
                    }
                }
                if *stopped.borrow() {
                    break;
                }
                latency("file_cache_ready", started);
                let _ = Box::pin(service.restore_networks()).await;
                latency("retained_network_restoration", started);
            }
        })
    }

    pub async fn disconnect(&self) -> Result<(), String> {
        self.stopped.send_replace(true);
        let startup = self
            .startup_worker
            .lock()
            .map_err(|_| "Startup worker unavailable")?
            .take();
        if let Some(worker) = startup {
            worker
                .await
                .map_err(|_| "Startup worker stopped unexpectedly")?;
        }
        let _network_lifecycle = self.network_operations.lock().await;
        let network_result = self.stop_networks().await;
        if let Some(current) = self.session.lock().await.as_ref() {
            if let Some(files) = &current.files {
                files.enabled(false).await?;
            }
        }
        let worker = self
            .file_worker
            .lock()
            .map_err(|_| "File worker handle unavailable")?
            .take();
        if let Some(worker) = worker {
            worker
                .await
                .map_err(|_| "File worker stopped unexpectedly")?;
        }
        let mut session = self.session.lock().await;
        let result = if let Some(current) = session.as_mut() {
            if let Some(files) = &current.files {
                files.enabled(false).await?;
            }
            current.client.stop_background().await;
            current
                .client
                .save()
                .await
                .and_then(|_| Self::save_message_metadata(current))
        } else {
            Ok(())
        };
        *session = None;
        result.and(network_result)
    }

    pub async fn flush(&self) -> Result<(), String> {
        let mut session = self.session.lock().await;
        if let Some(session) = session.as_mut() {
            session.client.save().await?;
            Self::save_message_metadata(session)?;
        }
        drop(session);
        self.flush_networks().await?;
        Ok(())
    }
}

fn split_head(text: &str) -> (&str, &str) {
    let text = text.trim_start();
    text.split_once(char::is_whitespace).unwrap_or((text, ""))
}
fn context_channel<'a>(
    archive: &'a ArchiveData,
    conversation: Option<&str>,
) -> Result<&'a ChannelRecord, String> {
    let key = conversation.ok_or("open a channel or a channel-scoped query first")?;
    let id = if let Some(pm) = archive.scoped_pms.iter().find(|p| query_key(p.id) == key) {
        pm.id.channel_id
    } else {
        return archive
            .channels
            .iter()
            .find(|c| c.active && channel_key(c.id) == key)
            .ok_or_else(|| "channel is not active".into());
    };
    archive
        .channels
        .iter()
        .find(|c| c.active && c.id == id)
        .ok_or_else(|| "channel is not active".into())
}
fn resolve_member(channel: &ChannelRecord, name: &str) -> Result<MemberId, String> {
    let name = name.trim_start_matches('@');
    let matches = channel
        .members
        .iter()
        .filter(|m| {
            !m.is_self && (hex(&m.id.0) == name || m.display_name.eq_ignore_ascii_case(name))
        })
        .collect::<Vec<_>>();
    match matches.as_slice() {
        [member] => Ok(member.id),
        [] => Err("no such member in this channel".into()),
        _ => {
            Err("nickname is ambiguous in this channel; select a member from the nick list".into())
        }
    }
}
fn conversation_messages(
    archive: &ArchiveData,
    key: &str,
) -> Result<Vec<crate::model::Message>, String> {
    if let Some(index) = key
        .strip_prefix("legacy/")
        .and_then(|s| s.parse::<usize>().ok())
    {
        let legacy = archive
            .legacy
            .conversations
            .list
            .get(index)
            .ok_or("unknown archive")?;
        return Ok(legacy
            .messages()
            .iter()
            .map(|m| crate::model::Message {
                id: m.id,
                operation_id: None,
                delivery: None,
                ts_unix: m.ts_unix,
                sender_member_id: None,
                sender_name: m.sender.clone(),
                mine: m.mine,
                text: m.text.clone(),
            })
            .collect());
    }
    if let Some(c) = archive.channels.iter().find(|c| record_key(c) == key) {
        return Ok(c.messages.clone());
    }
    if let Some(p) = archive.scoped_pms.iter().find(|p| query_key(p.id) == key) {
        return Ok(p.messages.clone());
    }
    Err("conversation is not in this instance".into())
}
async fn send(
    client: &ClientHandle,
    archive: &ArchiveData,
    key: &str,
    text: &str,
    operation: &str,
) -> Result<(), String> {
    if let Some(c) = archive
        .channels
        .iter()
        .find(|c| c.active && channel_key(c.id) == key)
    {
        return client
            .send_channel_operation(c.id, text, Some(operation))
            .await;
    }
    if let Some(p) = archive
        .scoped_pms
        .iter()
        .find(|p| p.active && query_key(p.id) == key)
    {
        return client
            .send_scoped_pm_operation(p.id, text, Some(operation))
            .await;
    }
    Err("conversation is not active in this instance".into())
}
fn message(key: &str, m: &crate::model::Message, state: &UiState) -> Message {
    let metadata = m
        .mine
        .then(|| state.message_metadata.get(&hex(&m.id)))
        .flatten();
    Message {
        id: hex(&m.id),
        conversation_id: key.into(),
        member_id: m.sender_member_id.map(|id| hex(&id.0)),
        nickname: m.sender_name.clone(),
        body: m.text.clone(),
        timestamp: m.ts_unix,
        mine: m.mine,
        operation_id: metadata.and_then(|v| v.operation_id.clone()),
        delivery: metadata.and_then(|v| v.delivery.clone()),
        result: None,
    }
}
fn unread(state: &UiState, key: &str, messages: &[crate::model::Message]) -> u32 {
    let start = state
        .read
        .get(key)
        .and_then(|id| messages.iter().position(|m| hex(&m.id) == *id))
        .map_or(0, |i| i + 1);
    messages[start..]
        .iter()
        .filter(|m| !m.mine)
        .count()
        .min(u32::MAX as usize) as u32
}
/// Lifecycle commands are parsed here for every frontend and native host.
pub(super) fn lifecycle_request(request: Request) -> Request {
    match &request {
        Request::Submit { text, .. } if text.trim() == "/lock" => Request::Lock,
        Request::Submit { text, .. } if matches!(text.trim(), "/disconnect" | "/quit") => {
            Request::Disconnect
        }
        _ => request,
    }
}
fn command_catalogue(caps: &[Capability]) -> Vec<Completion> {
    let mut commands = vec![
        ("/help", "Show available commands"),
        ("/status", "Show this instance"),
        (
            "/network",
            "Connect: /network join invitation-code; public naming: /network dns on|off|status",
        ),
        ("/lock", "Lock all attached views; keep receiving messages"),
        (
            "/disconnect",
            "Disconnect this instance (standalone service)",
        ),
        ("/list", "List channels"),
        ("/names", "List this channel's members"),
        (
            "/part",
            "Leave this channel through its owner; keep your history",
        ),
        (
            "/nick",
            "Change your nickname in this channel; keep your identity and history",
        ),
        ("/topic", "Show the topic; owners can set it or use --clear"),
        (
            "/join",
            "Open a channel or redeem an invitation: /join link nickname",
        ),
        ("/query", "Open a private conversation in this channel"),
        ("/msg", "Send a private message: /msg nickname text"),
        ("/say", "Send literal text"),
        ("/me", "Send an action in this conversation"),
        (
            "/close",
            "Close a private chat window or hide this channel; membership stays active",
        ),
        ("/hide", "Hide this conversation window; keep receiving"),
        (
            "/quit",
            "Disconnect this instance and stop receiving in every view",
        ),
        ("/refresh", "Refresh channels and catalogue"),
    ];
    if caps.contains(&Capability::ChannelAdmin) {
        commands.extend([
            (
                "/create",
                "Create an encrypted channel: /create [--private|--public] #channel nickname",
            ),
            ("/invite", "Create a single-use invitation"),
            ("/kick", "Remove a channel member"),
            (
                "/owner",
                "Transfer ownership to another member without changing the channel",
            ),
        ]);
    }
    commands
        .into_iter()
        .map(|(text, description)| Completion {
            text: text.into(),
            description: description.into(),
        })
        .collect()
}
fn command_usage(name: &str) -> &str {
    match name {
        "/presence" => "/presence on|off",
        "/publish" => "/publish https://directory.example/",
        "/network" => "/network join invitation-code | dns on|off|status",
        "/create" => "/create [--private|--public] #channel nickname",
        "/join" => "/join invitation-or-#channel nickname",
        "/query" => "/query nickname-or-member-id",
        "/msg" => "/msg nickname-or-member-id text",
        "/say" => "/say text",
        "/me" => "/me action",
        "/kick" => "/kick nickname-or-member-id",
        "/owner" => "/owner nickname-or-member-id",
        "/part" => "/part [--transfer nickname-or-member-id | --close]",
        "/nick" => "/nick nickname",
        "/topic" => "/topic [text | --clear]",
        "/cmd" => "/cmd #channel addressed-command",
        _ => name,
    }
}
fn network_arguments(text: &str) -> Option<&str> {
    let (name, args) = split_head(text);
    name.eq_ignore_ascii_case("/network").then_some(args)
}
fn recall_text(text: &str) -> String {
    let (name, args) = split_head(text);
    if name.eq_ignore_ascii_case("/network") {
        return if matches!(args, "dns on" | "dns off" | "dns status") {
            format!("/network {args}")
        } else {
            "/network join ".into()
        };
    }
    if name.eq_ignore_ascii_case("/join")
        && !args.starts_with('#')
        && !args.starts_with("extension/cmd/")
    {
        "/join ".into()
    } else {
        text.into()
    }
}

fn member_completions(members: &[gchat_api::Member], text: &str) -> Option<Vec<Completion>> {
    for prefix in ["/query ", "/msg ", "/kick "] {
        if text.to_lowercase().starts_with(prefix) {
            let partial = text[prefix.len()..].to_lowercase();
            return Some(
                members
                    .iter()
                    .filter(|m| !m.is_self && m.nickname.to_lowercase().starts_with(&partial))
                    .take(20)
                    .map(|m| Completion {
                        text: format!("{prefix}{}", m.id),
                        description: format!("{} · conversation member", m.nickname),
                    })
                    .collect(),
            );
        }
    }
    if !text.starts_with('/') && !text.trim().is_empty() {
        let start = text
            .rfind(char::is_whitespace)
            .map_or(0, |i| i + text[i..].chars().next().unwrap().len_utf8());
        let (head, partial) = text.split_at(start);
        if !partial.is_empty() {
            return Some(
                members
                    .iter()
                    .filter(|m| {
                        !m.is_self
                            && m.nickname
                                .to_lowercase()
                                .starts_with(&partial.to_lowercase())
                    })
                    .take(20)
                    .map(|m| Completion {
                        text: format!(
                            "{head}{}{}",
                            m.nickname,
                            if head.is_empty() { ":" } else { "" }
                        ),
                        description: if m.capabilities.is_empty() {
                            "Nickname in this conversation".into()
                        } else {
                            format!("Capabilities: {}", m.capabilities.join(", "))
                        },
                    })
                    .collect(),
            );
        }
    }
    None
}

fn completions(
    archive: &ArchiveData,
    conversation: Option<&str>,
    text: &str,
    mut choices: Vec<Completion>,
) -> Vec<Completion> {
    if let Ok(channel) = context_channel(archive, conversation) {
        let members = channel
            .members
            .iter()
            .map(|m| gchat_api::Member {
                id: hex(&m.id.0),
                nickname: m.display_name.clone(),
                is_self: m.is_self,
                recently_active: None,
                capabilities: Vec::new(),
            })
            .collect::<Vec<_>>();
        if let Some(items) = member_completions(&members, text) {
            return items;
        }
    }
    for channel in archive.channels.iter().filter(|c| c.active) {
        choices.push(Completion {
            text: format!("/join #{}", channel.title),
            description: "Joined channel".into(),
        });
    }
    choices
        .into_iter()
        .filter(|c| c.text.starts_with(text) && c.text != text)
        .take(20)
        .collect()
}

/// Existing owner-only IPC framing, separate from Recorder's protocol endpoint.
pub async fn serve<S: ChatEndpoint>(
    service: Arc<S>,
    endpoint: &Path,
    mut stop: watch::Receiver<bool>,
) -> Result<(), String> {
    let parent = endpoint.parent().ok_or("chat endpoint needs a parent")?;
    crate::paths::ensure_private_dir(parent, "chat endpoint")?;
    let router = rpc::router(service.clone()).map_err(|e| e.to_string())?;
    let rpc_endpoint = gchat_api::rpc::endpoint_for(endpoint);
    let (shutdown, receiver) = watch::channel(false);
    let mut rpc_stop = receiver.clone();
    let mut forward_stop = receiver.clone();
    let legacy = async {
        let result = serve_legacy(service, endpoint, receiver).await;
        let _ = shutdown.send(true);
        result
    };
    let typed = async {
        let result = gcoms::rpc::local::serve(&rpc_endpoint, router, async move {
            if !*rpc_stop.borrow() {
                let _ = rpc_stop.changed().await;
            }
        })
        .await
        .map_err(|e| e.to_string());
        let _ = shutdown.send(true);
        result
    };
    let forward = async {
        if !*stop.borrow() {
            tokio::select! { _ = stop.changed() => {}, _ = forward_stop.changed() => {} }
        }
        let _ = shutdown.send(true);
    };
    let (legacy, typed, ()) = tokio::join!(legacy, typed, forward);
    legacy.and(typed)
}

async fn serve_legacy<S: ChatEndpoint>(
    service: Arc<S>,
    endpoint: &Path,
    mut stop: watch::Receiver<bool>,
) -> Result<(), String> {
    #[cfg(unix)]
    let _instance_server_lock = {
        let parent = endpoint.parent().ok_or("chat endpoint needs a parent")?;
        crate::paths::ensure_private_dir(parent, "chat endpoint")?;
        crate::store::acquire_lock(endpoint)?
    };
    let endpoint = LocalEndpoint::new(endpoint);
    endpoint.prepare_server().map_err(|e| e.to_string())?;
    let mut listener =
        gcoms::sdk::local::LocalListener::bind(&endpoint).map_err(|e| e.to_string())?;
    let mut tasks = tokio::task::JoinSet::new();
    let slots = Arc::new(tokio::sync::Semaphore::new(32));
    let result = loop {
        tokio::select! {
            _ = stop.changed() => break Ok(()),
            accepted = listener.accept() => {
                let mut stream = match accepted { Ok(stream) => stream, Err(error) => break Err(error.to_string()) };
                let Ok(permit) = slots.clone().try_acquire_owned() else { continue };
                let service = service.clone();
                tasks.spawn(async move {
                    let _permit = permit;
                    let operation = async {
                        let bytes = gcoms::sdk::local_rpc::read(&mut stream, MAX_FRAME_BYTES).await?;
                        if bytes.starts_with(gchat_api::files::IO_MAGIC) {
                            let mut response = match service.clone().file_io(bytes).await {
                                Ok(data) => { let mut out = vec![0]; out.extend(data); out },
                                Err(error) => { let mut out = vec![1]; out.extend(error.bytes().take(512)); out },
                            };
                            let result = gcoms::sdk::local_rpc::write(&mut stream, &response, gchat_api::files::IO_LIMIT).await;
                            use zeroize::Zeroize; response.zeroize();
                            return result;
                        }
                        let request = serde_json::from_slice::<RequestEnvelope>(&bytes)
                            .map_err(|e| gcoms::sdk::SdkError::Protocol(e.to_string()))?;
                        let response = service.dispatch(request).await;
                        let encoded = serde_json::to_vec(&response).map_err(|e| gcoms::sdk::SdkError::Protocol(e.to_string()))?;
                        gcoms::sdk::local_rpc::write(&mut stream, &encoded, MAX_FRAME_BYTES).await
                    };
                    let _ = tokio::time::timeout(Duration::from_secs(145), operation).await;
                });
            }
            _ = tasks.join_next(), if !tasks.is_empty() => {}
        }
    };
    tasks.shutdown().await;
    let saved = service.flush().await;
    drop(listener);
    let _ = endpoint.cleanup();
    result.and(saved)
}

#[async_trait::async_trait]
pub trait ChatEndpoint: Send + Sync + 'static {
    fn instance_id(&self) -> &str;
    async fn rpc_service(self: Arc<Self>) -> Option<Arc<ChatService>>;
    async fn dispatch(&self, request: RequestEnvelope) -> ResponseEnvelope;
    async fn flush(&self) -> Result<(), String>;
    async fn file_io(self: Arc<Self>, bytes: Vec<u8>) -> Result<Vec<u8>, String> {
        let service = self
            .rpc_service()
            .await
            .ok_or("Unlock the selected service to use files")?;
        service.file_piece_io(bytes).await
    }
}

#[async_trait::async_trait]
impl ChatEndpoint for ChatService {
    fn instance_id(&self) -> &str {
        &self.id
    }
    async fn rpc_service(self: Arc<Self>) -> Option<Arc<ChatService>> {
        Some(self)
    }
    async fn dispatch(&self, request: RequestEnvelope) -> ResponseEnvelope {
        ChatService::dispatch(self, request).await
    }
    async fn flush(&self) -> Result<(), String> {
        ChatService::flush(self).await
    }
}
