use super::*;
use gchat_api::{FileInfo, FileRequest, FileSnapshot, FileState};
use gcoms::sdk::sharing::CacheConfig;
use gcoms::sdk::{sharing as api, sharing_v2 as modern};

fn observed_files_candidate(
    state: &UiState,
    snapshot: &api::Snapshot,
    modern: Option<&modern::Snapshot>,
    archive: &ArchiveData,
) -> Option<UiState> {
    let mut shared = state.shared_files.clone();
    let mut activity = Vec::new();
    // Track only retained cache entries, not every file ever encountered.
    let retained: std::collections::BTreeSet<_> = snapshot
        .files
        .iter()
        .map(|f| hex(&f.id))
        .chain(
            modern
                .into_iter()
                .flat_map(|s| s.files.iter().map(|f| hex(&f.id))),
        )
        .collect();
    shared.retain(|id| retained.contains(id));
    for file in &snapshot.files {
        if !matches!(
            file.status,
            api::Status::Importing | api::Status::Failed | api::Status::Cancelled
        ) {
            if let Some(context) = conversation(archive, &file.scope) {
                if shared.insert(hex(&file.id)) && state.files_observed {
                    activity.push((
                        context,
                        format!("File shared: {} ({} bytes)", file.name, file.size_bytes),
                    ));
                }
            }
        }
    }
    if let Some(snapshot) = modern {
        for file in &snapshot.files {
            if !matches!(
                file.status,
                api::Status::Importing | api::Status::Failed | api::Status::Cancelled
            ) && shared.insert(hex(&file.id))
                && state.files_observed
            {
                activity.push((
                    modern_conversation(&file.scope),
                    format!("File shared: {} ({} bytes)", file.name, file.size_bytes),
                ));
            }
        }
    }
    if shared == state.shared_files && state.files_observed {
        return None;
    }
    {
        // Most ticks are unchanged. Do not copy the operation journal or
        // message metadata until there is an actual durable UI update.
        let mut candidate = state.clone();
        candidate.shared_files = shared;
        candidate.files_observed = true;
        for (context, text) in activity {
            record_activity(&mut candidate, context, "file", text);
        }
        Some(candidate)
    }
}

pub(super) struct FileRuntime {
    sdk: Arc<dyn gcoms::sdk::GcClient>,
    contacts: tokio::sync::Mutex<Vec<gcoms::sdk::ContactCard>>,
}
impl FileRuntime {
    pub async fn open(
        runtime: &ProtocolRuntime,
        path: &Path,
        key: [u8; 32],
        config: CacheConfig,
    ) -> Result<Arc<Self>, String> {
        let config = api::CacheConfig {
            quota_bytes: config.quota_bytes,
            retention_secs: config.retention_secs,
        };
        runtime
            .0
            .configure_file_cache(path, key, config.clone())
            .await?;
        if std::env::var("GCHAT_FILE_DIAGNOSTICS").is_ok_and(|v| v == "1") {
            if let Some(host) = runtime.0.embedded_runtime() {
                host.enable_file_diagnostics()
                    .await
                    .map_err(|e| e.to_string())?;
            }
        }
        let files = Arc::new(Self {
            sdk: runtime.sdk_client(),
            contacts: tokio::sync::Mutex::new(Vec::new()),
        });
        files.enabled(true).await?;
        files
            .modern(modern::Request::Configure(config.clone()))
            .await?;
        files.request(api::Request::Configure(config)).await?;
        Ok(files)
    }
    pub async fn enabled(&self, enabled: bool) -> Result<(), String> {
        let modern = self.modern(modern::Request::SetEnabled(enabled)).await;
        let legacy = self.request(api::Request::SetEnabled(enabled)).await;
        modern?;
        legacy.map(|_| ())
    }
    pub(super) async fn contacts(&self, book: &contacts::Book) -> Result<(), String> {
        let cards = book.file_cards();
        let mut retained = self.contacts.lock().await;
        if *retained == cards {
            return Ok(());
        }
        match self.modern(modern::Request::Contacts(cards.clone())).await {
            Ok(_) => {
                *retained = cards;
                Ok(())
            }
            Err(error) => {
                // A saved block must never leave old transfer authority running.
                let _ = self.modern(modern::Request::SetEnabled(false)).await;
                Err(error)
            }
        }
    }
    async fn modern(&self, request: modern::Request) -> Result<modern::Reply, String> {
        self.sdk
            .sharing_v2(request)
            .await
            .map_err(|e| e.to_string())
    }
    async fn modern_snapshot(&self) -> Result<modern::Snapshot, String> {
        match self.modern(modern::Request::List).await? {
            modern::Reply::Snapshot(s) => Ok(s),
            _ => Err("Invalid file service reply".into()),
        }
    }
    async fn request(&self, request: api::Request) -> Result<api::Reply, String> {
        self.sdk.sharing(request).await.map_err(|e| e.to_string())
    }
}
fn id(value: &str) -> Result<api::ShareId, String> {
    if value.len() != 32
        || !value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    {
        return Err("Invalid file handle".into());
    }
    let mut out = [0; 16];
    for (i, pair) in value.as_bytes().as_chunks::<2>().0.iter().enumerate() {
        out[i] = u8::from_str_radix(
            std::str::from_utf8(pair).map_err(|_| "Invalid file handle")?,
            16,
        )
        .map_err(|_| "Invalid file handle")?;
    }
    Ok(out)
}
fn number(value: &str) -> Result<u64, String> {
    if value.is_empty()
        || (value.len() > 1 && value.starts_with('0'))
        || !value.bytes().all(|c| c.is_ascii_digit())
    {
        return Err("Invalid byte count".into());
    }
    value.parse().map_err(|_| "Invalid byte count".into())
}
fn scope(archive: &ArchiveData, conversation: &str) -> Result<api::Scope, String> {
    let channel = context_channel(archive, Some(conversation))?;
    let participants = if let Some(pm) = archive
        .scoped_pms
        .iter()
        .find(|p| p.active && query_key(p.id) == conversation)
    {
        let mut ids = vec![pm.id.self_member_id.0, pm.id.remote_member_id.0];
        ids.sort();
        ids
    } else if conversation == channel_key(channel.id) {
        vec![]
    } else {
        return Err("Conversation is not active".into());
    };
    Ok(api::Scope {
        channel: channel.id.0,
        participants,
    })
}
fn conversation(archive: &ArchiveData, scope: &api::Scope) -> Option<String> {
    let channel = archive.channels.iter().rev().find(|c| {
        c.id.0 == scope.channel
            && c.self_member_id.is_some_and(|own| {
                scope.participants.is_empty() || scope.participants.contains(&own.0)
            })
    })?;
    if scope.participants.is_empty() {
        return Some(channel_key(channel.id));
    }
    let own = channel.self_member_id?;
    let remote = scope.participants.iter().find(|m| **m != own.0)?;
    Some(query_key(ScopedPmId {
        channel_id: channel.id,
        self_member_id: own,
        remote_member_id: MemberId(*remote),
    }))
}

fn snapshot(snapshot: api::Snapshot, archive: &ArchiveData, filter: Option<&str>) -> FileSnapshot {
    FileSnapshot {
        files: snapshot
            .files
            .into_iter()
            .filter_map(|view| {
                let conversation = conversation(archive, &view.scope)?;
                if filter.is_some_and(|f| f != conversation) {
                    return None;
                }
                Some(FileInfo {
                    id: hex(&view.id),
                    aliases: None,
                    publication: None,
                    conversation,
                    name: view.name,
                    size_bytes: view.size_bytes.to_string(),
                    verified_bytes: view.verified_bytes.to_string(),
                    state: match view.status {
                        api::Status::Offered => FileState::Offered,
                        api::Status::Importing => FileState::Importing,
                        api::Status::Downloading => FileState::Downloading,
                        api::Status::WaitingForPeers => FileState::WaitingForPeers,
                        api::Status::Paused => FileState::Paused,
                        api::Status::Complete => FileState::Complete,
                        api::Status::Failed => FileState::Failed,
                        api::Status::Cancelled => FileState::Cancelled,
                    },
                    sources: view.sources,
                    verified_sources: view.verified_sources,
                    completed_by: view.completed_by,
                    error: view.error,
                })
            })
            .collect(),
        quota_bytes: snapshot.config.quota_bytes.to_string(),
        used_bytes: snapshot.used_bytes.to_string(),
        retention_days: (snapshot.config.retention_secs / 86400).min(u16::MAX as u64) as u16,
    }
}
fn modern_scope(state: &UiState, conversation: &str) -> Result<Option<modern::Scope>, String> {
    if contacts::is_conversation(conversation) {
        return Ok(Some(modern::Scope::Contact {
            peer: state.contacts.file_peer(conversation)?,
        }));
    }
    if hosted::is_conversation(conversation) {
        let room = state
            .hosted
            .get(conversation)
            .filter(|r| r.active())
            .ok_or("Channel is not active")?;
        return Ok(Some(modern::Scope::Hosted {
            channel: room.file_channel(),
        }));
    }
    Ok(None)
}
fn combined_admission(
    request: &FileRequest,
    legacy: &api::Snapshot,
    modern: &modern::Snapshot,
    quota: u64,
) -> Result<(), String> {
    let piece = api::PIECE_BYTES as u64;
    let extra = match request {
        FileRequest::Prepare {
            id: handle,
            size_bytes,
            ..
        } => {
            if legacy.files.iter().any(|f| hex(&f.id) == *handle)
                || modern.files.iter().any(|f| hex(&f.id) == *handle)
            {
                0
            } else {
                let bytes = number(size_bytes)?;
                bytes
                    .saturating_add(bytes.div_ceil(piece).saturating_mul(1024))
                    .saturating_add(4096)
            }
        }
        FileRequest::Accept { id: handle } | FileRequest::Resume { id: handle } => {
            let offered = legacy
                .files
                .iter()
                .find(|f| hex(&f.id) == *handle && f.status == api::Status::Offered)
                .map(|f| f.size_bytes)
                .or_else(|| {
                    modern
                        .files
                        .iter()
                        .find(|f| hex(&f.id) == *handle && f.status == api::Status::Offered)
                        .map(|f| f.size_bytes)
                });
            offered.map_or(0, |bytes| {
                bytes.saturating_add(bytes.div_ceil(piece).saturating_mul(1016))
            })
        }
        _ => 0,
    };
    if extra > 0
        && legacy
            .used_bytes
            .saturating_add(modern.used_bytes)
            .saturating_add(extra)
            > quota
    {
        Err("Combined file cache quota exceeded".into())
    } else {
        Ok(())
    }
}
fn modern_conversation(scope: &modern::Scope) -> String {
    match scope {
        modern::Scope::Hosted { channel } => format!("hosted/{}", hex(channel)),
        modern::Scope::Contact { peer } => format!("contact/{}", hex(peer)),
    }
}
fn append_modern(result: &mut FileSnapshot, snapshot: modern::Snapshot, filter: Option<&str>) {
    let used = result
        .used_bytes
        .parse::<u64>()
        .unwrap_or(0)
        .saturating_add(snapshot.used_bytes);
    result.used_bytes = used.to_string();
    result
        .files
        .extend(snapshot.files.into_iter().filter_map(|view| {
            let conversation = modern_conversation(&view.scope);
            if filter.is_some_and(|f| f != conversation) {
                return None;
            }
            Some(FileInfo {
                id: hex(&view.id),
                aliases: None,
                publication: None,
                conversation,
                name: view.name,
                size_bytes: view.size_bytes.to_string(),
                verified_bytes: view.verified_bytes.to_string(),
                state: match view.status {
                    api::Status::Offered => FileState::Offered,
                    api::Status::Importing => FileState::Importing,
                    api::Status::Downloading => FileState::Downloading,
                    api::Status::WaitingForPeers => FileState::WaitingForPeers,
                    api::Status::Paused => FileState::Paused,
                    api::Status::Complete => FileState::Complete,
                    api::Status::Failed => FileState::Failed,
                    api::Status::Cancelled => FileState::Cancelled,
                },
                sources: view.sources,
                verified_sources: view.verified_sources,
                completed_by: view.completed_by,
                error: view.error,
            })
        }));
}
fn file_capability(conversation: &str) -> Capability {
    if contacts::is_conversation(conversation) {
        Capability::DirectMessage
    } else if hosted::is_conversation(conversation) {
        Capability::HostedChannels
    } else {
        Capability::ChannelMember
    }
}
impl ChatService {
    fn require_files(&self) -> Result<(), String> {
        if [
            Capability::DirectMessage,
            Capability::HostedChannels,
            Capability::ChannelMember,
        ]
        .iter()
        .any(|c| self.capabilities.contains(c))
        {
            Ok(())
        } else {
            Err("File conversations are not permitted".into())
        }
    }
    fn restrict_files(&self, mut snapshot: FileSnapshot) -> FileSnapshot {
        snapshot.files.retain(|f| {
            self.capabilities
                .contains(&file_capability(&f.conversation))
        });
        snapshot
    }
    // Both control calls and binary reads/writes can race a successful unlock.
    // Wait without the session lock so startup, history and lock can all progress.
    async fn wait_for_file_cache(&self) -> Result<(), String> {
        tokio::time::timeout(Duration::from_secs(30), async {
            loop {
                let session = self.session.lock().await;
                let preparing = session.as_ref().is_some_and(|s| {
                    !s.ui_locked
                        && s.files.is_none()
                        && s.file_error.as_deref() == Some("Preparing encrypted file cache…")
                });
                drop(session);
                if !preparing || *self.stopped.borrow() {
                    break;
                }
                tokio::time::sleep(Duration::from_millis(25)).await;
            }
        })
        .await
        .map_err(|_| "File cache is still preparing. Try again shortly.".to_string())
    }

    pub(super) async fn files_request(&self, request: FileRequest) -> Result<FileSnapshot, String> {
        self.require_files()?;
        self.wait_for_file_cache().await?;
        let publications = matches!(request, FileRequest::Publications { .. });
        let mut session = self.session.lock().await;
        let unlocked = session
            .as_mut()
            .filter(|s| !s.ui_locked)
            .ok_or("Unlock this instance to use files")?;
        let files = unlocked.files.clone().ok_or_else(|| {
            unlocked
                .file_error
                .clone()
                .unwrap_or_else(|| "File cache unavailable".into())
        })?;
        files.contacts(&unlocked.state.contacts).await?;
        let archive = unlocked.client.file_context();
        let modern_snapshot = files.modern_snapshot().await?;
        match &request {
            FileRequest::Prepare { conversation, .. }
            | FileRequest::List {
                conversation: Some(conversation),
            } => self.require(file_capability(conversation))?,
            FileRequest::Publications { .. } => self.require(Capability::ChannelMember)?,
            FileRequest::Commit { id }
            | FileRequest::Accept { id }
            | FileRequest::Pause { id }
            | FileRequest::Resume { id }
            | FileRequest::Cancel { id } => {
                let capability = modern_snapshot
                    .files
                    .iter()
                    .find(|f| hex(&f.id) == *id)
                    .map(|f| file_capability(&modern_conversation(&f.scope)))
                    .unwrap_or(Capability::ChannelMember);
                self.require(capability)?;
            }
            _ => {}
        }
        if matches!(
            request,
            FileRequest::Prepare { .. } | FileRequest::Accept { .. } | FileRequest::Resume { .. }
        ) {
            let api::Reply::Snapshot(legacy) = files.request(api::Request::List).await? else {
                return Err("Invalid file service reply".into());
            };
            combined_admission(
                &request,
                &legacy,
                &modern_snapshot,
                unlocked.state.file_config.quota_bytes,
            )?;
        }
        let modern_operation = match &request {
            FileRequest::Prepare {
                id: handle,
                conversation,
                name,
                size_bytes,
            } => modern_scope(&unlocked.state, conversation)?
                .map(|scope| {
                    Ok::<_, String>(modern::Request::Prepare {
                        id: id(handle)?,
                        scope,
                        name: name.clone(),
                        size_bytes: number(size_bytes)?,
                    })
                })
                .transpose()?,
            FileRequest::Commit { id: handle }
            | FileRequest::Accept { id: handle }
            | FileRequest::Pause { id: handle }
            | FileRequest::Resume { id: handle }
            | FileRequest::Cancel { id: handle }
                if modern_snapshot.files.iter().any(|f| hex(&f.id) == *handle) =>
            {
                let id = id(handle)?;
                Some(match &request {
                    FileRequest::Commit { .. } => modern::Request::Commit { id },
                    FileRequest::Accept { .. } => modern::Request::Accept { id },
                    FileRequest::Pause { .. } => modern::Request::Pause { id },
                    FileRequest::Resume { .. } => modern::Request::Resume { id },
                    _ => modern::Request::Cancel { id },
                })
            }
            _ => None,
        };
        if let Some(operation) = modern_operation {
            let api::Reply::Snapshot(legacy) = files.request(api::Request::List).await? else {
                return Err("Invalid file service reply".into());
            };
            let handle = match &operation {
                modern::Request::Prepare { id, .. }
                | modern::Request::Commit { id }
                | modern::Request::Accept { id }
                | modern::Request::Pause { id }
                | modern::Request::Resume { id }
                | modern::Request::Cancel { id } => *id,
                _ => unreachable!(),
            };
            if legacy.files.iter().any(|f| f.id == handle) {
                return Err("File identity conflicts across profiles".into());
            }
            let modern::Reply::Snapshot(value) = files.modern(operation).await? else {
                return Err("Invalid file service reply".into());
            };
            let mut result = snapshot(legacy, &archive, None);
            append_modern(&mut result, value, None);
            self.invalidate();
            return Ok(self.restrict_files(result));
        }
        if let FileRequest::Prepare { id: handle, .. } = &request {
            if modern_snapshot.files.iter().any(|f| hex(&f.id) == *handle) {
                return Err("File identity conflicts across profiles".into());
            }
        }
        let mut filter = None;
        let operation = match request {
            FileRequest::List { conversation } | FileRequest::Publications { conversation } => {
                filter = conversation;
                api::Request::List
            }
            FileRequest::Prepare {
                id: handle,
                conversation,
                name,
                size_bytes,
            } => api::Request::Prepare {
                id: id(&handle)?,
                scope: scope(&archive, &conversation)?,
                name,
                size_bytes: number(&size_bytes)?,
            },
            FileRequest::Commit { id: handle } => api::Request::CommitReusing { id: id(&handle)? },
            FileRequest::Accept { id: handle } => api::Request::Accept { id: id(&handle)? },
            FileRequest::Pause { id: handle } => api::Request::Pause { id: id(&handle)? },
            FileRequest::Resume { id: handle } => api::Request::Resume { id: id(&handle)? },
            FileRequest::Cancel { id: handle } => api::Request::Cancel { id: id(&handle)? },
            FileRequest::Configure {
                quota_bytes,
                retention_days,
            } => {
                let config = api::CacheConfig {
                    quota_bytes: number(&quota_bytes)?,
                    retention_secs: u64::from(retention_days) * 86400,
                };
                api::Request::Configure(config.clone())
                    .validate()
                    .map_err(|e| e.to_string())?;
                let mut candidate = unlocked.state.clone();
                candidate.file_config = CacheConfig {
                    quota_bytes: config.quota_bytes,
                    retention_secs: config.retention_secs,
                };
                unlocked.store.save(&candidate)?;
                unlocked.state = candidate;
                self.invalidate();
                files
                    .modern(modern::Request::Configure(config.clone()))
                    .await?;
                api::Request::Configure(config)
            }
        };
        // Serialize against archive locking so a finished lock cannot admit another write.
        let result: Result<FileSnapshot, String> = match files.request(operation).await? {
            api::Reply::Snapshot(value) => Ok(snapshot(value, &archive, filter.as_deref())),
            api::Reply::Committed {
                original,
                canonical,
                snapshot: value,
            } => {
                let mut value = snapshot(value, &archive, filter.as_deref());
                if let Some(file) = value.files.iter_mut().find(|f| f.id == hex(&canonical)) {
                    file.aliases = Some(vec![hex(&original)]);
                    let mut candidate = unlocked.state.clone();
                    let mut changed = false;
                    if !candidate.file_publications.contains_key(&hex(&original)) {
                        // An older shared host can still complete ordinary uploads;
                        // without a verified commitment it cannot publish a fleet release.
                        if let Ok(api::Reply::Metadata(metadata)) =
                            files.request(api::Request::Inspect { id: original }).await
                        {
                            if metadata.id != original
                                || metadata.size_bytes.to_string() != file.size_bytes
                            {
                                return Err("Committed file does not match its manifest".into());
                            }
                            candidate.file_publication_sequence = candidate
                                .file_publication_sequence
                                .checked_add(1)
                                .ok_or("File publication sequence exhausted")?;
                            candidate.file_publications.insert(
                                hex(&original),
                                gchat_api::files::FilePublication {
                                    name: metadata.name,
                                    canonical_id: hex(&canonical),
                                    sha256: hex(&metadata.sha256),
                                    publisher_safety_number: unlocked.client.safety_number().into(),
                                    sequence: candidate.file_publication_sequence.to_string(),
                                    committed_unix: now().to_string(),
                                },
                            );
                            changed = true;
                        }
                    }
                    if candidate.shared_files.insert(file.id.clone()) {
                        record_activity(
                            &mut candidate,
                            file.conversation.clone(),
                            "file",
                            format!("File shared: {} ({} bytes)", file.name, file.size_bytes),
                        );
                        changed = true;
                    }
                    if changed {
                        let retained: std::collections::BTreeSet<_> =
                            value.files.iter().map(|f| f.id.clone()).collect();
                        candidate
                            .file_publications
                            .retain(|_, p| retained.contains(&p.canonical_id));
                        unlocked.store.save(&candidate)?;
                        unlocked.state = candidate;
                        self.invalidate();
                    }
                }
                Ok(value)
            }
            _ => Err("Invalid file service reply".into()),
        };
        let mut result = result?;
        if !publications {
            append_modern(
                &mut result,
                files.modern_snapshot().await?,
                filter.as_deref(),
            );
        }
        if publications {
            result.files = unlocked
                .state
                .file_publications
                .iter()
                .filter_map(|(original, publication)| {
                    let mut file = result
                        .files
                        .iter()
                        .find(|f| f.id == publication.canonical_id)?
                        .clone();
                    file.id = original.clone();
                    file.name = publication.name.clone();
                    file.publication = Some(publication.clone());
                    Some(file)
                })
                .collect();
        }
        Ok(self.restrict_files(result))
    }
    pub(super) async fn file_piece_io(&self, frame: Vec<u8>) -> Result<Vec<u8>, String> {
        let _update_request = self.update_gate.enter()?;
        self.require_files()?;
        let (mut header, bytes) = gchat_api::files::decode_io(&frame)?;
        if header.instance != self.id {
            return Err("File request belongs to another instance".into());
        }
        if let Some((network, handle)) = header.id.split_once(':') {
            let child = {
                let session = self.session.lock().await;
                if session.as_ref().is_none_or(|s| s.ui_locked) {
                    return Err("Unlock this instance to use files".into());
                }
                self.networks
                    .lock()
                    .await
                    .get(network)
                    .cloned()
                    .ok_or("Network unavailable")?
            };
            header.id = handle.to_string();
            header.instance = child.id.clone();
            let routed = gchat_api::files::encode_io(&header, bytes)?;
            return Box::pin(child.file_piece_io(routed)).await;
        }
        if !header.upload && !bytes.is_empty() {
            return Err("Download request contains unexpected bytes".into());
        }
        self.wait_for_file_cache().await?;
        let session = self.session.lock().await;
        let unlocked = session
            .as_ref()
            .filter(|s| !s.ui_locked)
            .ok_or("Unlock this instance to use files")?;
        let files = unlocked.files.clone().ok_or_else(|| {
            unlocked
                .file_error
                .clone()
                .unwrap_or_else(|| "File cache unavailable".into())
        })?;
        files.contacts(&unlocked.state.contacts).await?;
        if let Some(file) = files
            .modern_snapshot()
            .await?
            .files
            .iter()
            .find(|f| hex(&f.id) == header.id)
        {
            self.require(file_capability(&modern_conversation(&file.scope)))?;
            if let api::Reply::Snapshot(legacy) = files.request(api::Request::List).await? {
                if legacy.files.iter().any(|f| hex(&f.id) == header.id) {
                    return Err("File identity conflicts across profiles".into());
                }
            }
            let operation = if header.upload {
                modern::Request::WritePiece {
                    id: id(&header.id)?,
                    piece: header.piece,
                    bytes: bytes.to_vec(),
                }
            } else {
                modern::Request::ReadPiece {
                    id: id(&header.id)?,
                    piece: header.piece,
                }
            };
            return match files.modern(operation).await? {
                modern::Reply::Piece(bytes) => Ok(bytes),
                modern::Reply::Snapshot(_) if header.upload => Ok(Vec::new()),
                _ => Err("Invalid file service reply".into()),
            };
        }
        self.require(Capability::ChannelMember)?;
        let operation = if header.upload {
            api::Request::WritePiece {
                id: id(&header.id)?,
                piece: header.piece,
                bytes: bytes.to_vec(),
            }
        } else {
            api::Request::ReadPiece {
                id: id(&header.id)?,
                piece: header.piece,
            }
        };
        match files.request(operation).await? {
            api::Reply::Piece(bytes) => Ok(bytes),
            api::Reply::Snapshot(_) if header.upload => Ok(Vec::new()),
            _ => Err("Invalid file service reply".into()),
        }
    }
    /// Only the presentation layer belongs here: expose incoming private file conversations.
    pub(super) fn spawn_file_worker(service: &Arc<Self>) -> tokio::task::JoinHandle<()> {
        let weak = Arc::downgrade(service);
        let mut stopped = service.stopped.subscribe();
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_millis(250));
            interval.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
            loop {
                tokio::select! { _ = stopped.changed() => break, _ = interval.tick() => {} }
                let Some(service) = weak.upgrade() else { break };
                let mut session = tokio::select! { _ = stopped.changed() => break, session = service.session.lock() => session };
                let Some(unlocked) = session.as_mut().filter(|s| !s.ui_locked) else {
                    continue;
                };
                let Some(files) = &unlocked.files else {
                    continue;
                };
                if files.contacts(&unlocked.state.contacts).await.is_err() {
                    continue;
                }
                let Ok(modern_snapshot) = files.modern_snapshot().await else {
                    continue;
                };
                {
                    let previous_error = unlocked.file_error.clone();
                    if let Some(error) = &modern_snapshot.error {
                        unlocked.file_error = Some(format!("File transfer: {error}"));
                    } else if unlocked
                        .file_error
                        .as_deref()
                        .is_some_and(|e| e.starts_with("File transfer:"))
                    {
                        unlocked.file_error = None;
                    }
                    if previous_error != unlocked.file_error {
                        service.invalidate();
                    }
                }
                let Ok(api::Reply::Snapshot(snapshot)) = files.request(api::Request::List).await
                else {
                    continue;
                };
                let archive = unlocked.client.file_context();
                let mut changed = false;
                if let Some(candidate) = observed_files_candidate(
                    &unlocked.state,
                    &snapshot,
                    Some(&modern_snapshot),
                    &archive,
                ) {
                    if unlocked.store.save(&candidate).is_ok() {
                        unlocked.state = candidate;
                        service.invalidate();
                    }
                }
                for file in snapshot.files {
                    if file.scope.participants.len() != 2
                        || matches!(
                            file.status,
                            api::Status::Cancelled | api::Status::Importing | api::Status::Failed
                        )
                    {
                        continue;
                    }
                    let Some(channel) = archive
                        .channels
                        .iter()
                        .find(|c| c.active && c.id.0 == file.scope.channel)
                    else {
                        continue;
                    };
                    let Some(own) = channel
                        .self_member_id
                        .filter(|m| file.scope.participants.contains(&m.0))
                    else {
                        continue;
                    };
                    let Some(remote) = file.scope.participants.iter().find(|m| **m != own.0) else {
                        continue;
                    };
                    let id = ScopedPmId {
                        channel_id: channel.id,
                        self_member_id: own,
                        remote_member_id: MemberId(*remote),
                    };
                    if !archive.scoped_pms.iter().any(|p| p.id == id)
                        && unlocked
                            .client
                            .open_scoped_pm(channel.id, MemberId(*remote))
                            .is_ok()
                    {
                        changed = true;
                    }
                }
                if changed {
                    let _ = unlocked.client.save().await;
                    service.invalidate();
                }
            }
        })
    }
}

#[cfg(test)]
mod observation_tests {
    use super::*;
    #[test]
    fn modern_file_activity_keeps_its_conversation_and_is_emitted_once() {
        let legacy = api::Snapshot {
            files: vec![],
            config: api::CacheConfig::default(),
            used_bytes: 0,
        };
        let modern = modern::Snapshot {
            files: vec![modern::FileInfo {
                id: [7; 16],
                scope: modern::Scope::Contact { peer: [9; 32] },
                name: "private.txt".into(),
                size_bytes: 12,
                verified_bytes: 0,
                status: api::Status::Offered,
                sources: 1,
                verified_sources: 0,
                completed_by: 0,
                error: None,
            }],
            config: api::CacheConfig::default(),
            used_bytes: 4096,
            error: None,
        };
        let archive = ArchiveData::default();
        let state = UiState {
            files_observed: true,
            ..UiState::default()
        };
        let changed = observed_files_candidate(&state, &legacy, Some(&modern), &archive).unwrap();
        assert_eq!(changed.activity.len(), 1);
        assert_eq!(
            changed.activity[0].conversation,
            format!("contact/{}", hex(&[9; 32]))
        );
        assert!(observed_files_candidate(&changed, &legacy, Some(&modern), &archive).is_none());
    }
    #[test]
    fn admission_reserves_one_budget_across_both_file_profiles() {
        let legacy = api::Snapshot {
            files: vec![],
            config: api::CacheConfig::default(),
            used_bytes: 60_000,
        };
        let modern = modern::Snapshot {
            files: vec![],
            config: api::CacheConfig::default(),
            used_bytes: 30_000,
            error: None,
        };
        let request = FileRequest::Prepare {
            id: "12121212121212121212121212121212".into(),
            conversation: "contact/test".into(),
            name: "bounded.bin".into(),
            size_bytes: "8192".into(),
        };
        // Each cache would separately admit this file under a 100,000-byte cap.
        assert!(combined_admission(&request, &legacy, &modern, 100_000).is_err());
        assert!(combined_admission(&request, &legacy, &modern, 110_000).is_ok());
        assert!(combined_admission(
            &FileRequest::Cancel {
                id: "12121212121212121212121212121212".into()
            },
            &legacy,
            &modern,
            1
        )
        .is_ok());
    }
    #[test]
    fn unchanged_files_need_no_candidate_and_failed_save_can_retry() {
        let snapshot = api::Snapshot {
            files: Vec::new(),
            config: api::CacheConfig::default(),
            used_bytes: 0,
        };
        let archive = ArchiveData::default();
        let state = UiState::default();
        let baseline = observed_files_candidate(&state, &snapshot, None, &archive).unwrap();
        assert!(baseline.files_observed);
        assert!(baseline.activity.is_empty());
        // Discarding a candidate (e.g. a failed save) must leave the delta retryable.
        assert!(observed_files_candidate(&state, &snapshot, None, &archive).is_some());
        assert!(observed_files_candidate(&baseline, &snapshot, None, &archive).is_none());
        let mut stale = baseline;
        stale.shared_files.insert("retired-file".into());
        let removed = observed_files_candidate(&stale, &snapshot, None, &archive).unwrap();
        assert!(removed.shared_files.is_empty());
        assert!(observed_files_candidate(&removed, &snapshot, None, &archive).is_none());
    }
}
