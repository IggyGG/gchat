use super::*;
use gchat_api::{FileInfo, FileRequest, FileSnapshot, FileState};
use gcoms::sdk::sharing as api;
use gcoms::sdk::sharing::CacheConfig;

pub(super) struct FileRuntime {
    sdk: Arc<dyn gcoms::sdk::GcClient>,
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
        });
        files.enabled(true).await?;
        files.request(api::Request::Configure(config)).await?;
        Ok(files)
    }
    pub async fn enabled(&self, enabled: bool) -> Result<(), String> {
        self.request(api::Request::SetEnabled(enabled))
            .await
            .map(|_| ())
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
impl ChatService {
    pub(super) async fn files_request(&self, request: FileRequest) -> Result<FileSnapshot, String> {
        self.require(Capability::ChannelMember)?;
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
        let archive = unlocked.client.file_context();
        let mut filter = None;
        let operation = match request {
            FileRequest::List { conversation } => {
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
                api::Request::Configure(config)
            }
        };
        // Serialize against archive locking so a finished lock cannot admit another write.
        match files.request(operation).await? {
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
                    if candidate.shared_files.insert(file.id.clone()) {
                        record_activity(
                            &mut candidate,
                            file.conversation.clone(),
                            "file",
                            format!("File shared: {} ({} bytes)", file.name, file.size_bytes),
                        );
                        unlocked.store.save(&candidate)?;
                        unlocked.state = candidate;
                    }
                }
                Ok(value)
            }
            _ => Err("Invalid file service reply".into()),
        }
    }
    pub(super) async fn file_piece_io(&self, frame: Vec<u8>) -> Result<Vec<u8>, String> {
        self.require(Capability::ChannelMember)?;
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
                let Ok(api::Reply::Snapshot(snapshot)) = files.request(api::Request::List).await
                else {
                    continue;
                };
                let archive = unlocked.client.file_context();
                let mut changed = false;
                let mut candidate = unlocked.state.clone();
                // Track only retained cache entries, not every file ever encountered.
                let retained: std::collections::BTreeSet<_> =
                    snapshot.files.iter().map(|f| hex(&f.id)).collect();
                candidate.shared_files.retain(|id| retained.contains(id));
                for file in &snapshot.files {
                    if !matches!(
                        file.status,
                        api::Status::Importing | api::Status::Failed | api::Status::Cancelled
                    ) {
                        if let Some(context) = conversation(&archive, &file.scope) {
                            if candidate.shared_files.insert(hex(&file.id))
                                && unlocked.state.files_observed
                            {
                                record_activity(
                                    &mut candidate,
                                    context,
                                    "file",
                                    format!(
                                        "File shared: {} ({} bytes)",
                                        file.name, file.size_bytes
                                    ),
                                );
                            }
                        }
                    }
                }
                candidate.files_observed = true;
                if (candidate.shared_files != unlocked.state.shared_files
                    || !unlocked.state.files_observed)
                    && unlocked.store.save(&candidate).is_ok()
                {
                    unlocked.state = candidate;
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
                }
            }
        })
    }
}
