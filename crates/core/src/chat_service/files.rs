use super::*;
use gchat_api::{FileInfo, FileRequest, FileSnapshot, FileState};
use gcoms_file_transfer::swarm::{
    Action, Cache, CacheConfig, Engine, Manifest, Peer, Scope, ShareId, Status, CONTENT_TYPE,
};
use std::{
    collections::{BTreeMap, VecDeque},
    sync::atomic::{AtomicBool, AtomicU64, Ordering},
};

pub(super) struct FileRuntime {
    enabled: AtomicBool,
    diagnostics: bool,
    send_failures: AtomicU64,
    send_timeouts: AtomicU64,
    inner: std::sync::Mutex<Backend>,
}
struct Work {
    actions: Vec<(String, Action)>,
    pms: Vec<(gcoms_sdk::ChannelId, MemberId)>,
}
struct Backend {
    engine: Engine,
    routes: BTreeMap<[u8; 32], String>,
    pending: VecDeque<Action>,
    next_diagnostic: u64,
}
#[cfg(test)]
pub(super) struct TestReceiptGate {
    entered: std::sync::atomic::AtomicUsize,
    release: tokio::sync::Semaphore,
}
impl FileRuntime {
    pub fn open(path: &Path, key: [u8; 32], config: CacheConfig) -> Result<Arc<Self>, String> {
        let cache = Cache::open(path, key, config).map_err(|e| e.to_string())?;
        Ok(Arc::new(Self {
            enabled: AtomicBool::new(true),
            diagnostics: std::env::var("GCHAT_FILE_DIAGNOSTICS").is_ok_and(|v| v == "1"),
            send_failures: AtomicU64::new(0),
            send_timeouts: AtomicU64::new(0),
            inner: std::sync::Mutex::new(Backend {
                engine: Engine::new(cache),
                routes: BTreeMap::new(),
                pending: VecDeque::new(),
                next_diagnostic: 0,
            }),
        }))
    }
    pub fn enabled(&self, enabled: bool) {
        self.enabled.store(enabled, Ordering::Release);
    }
}
fn id(value: &str) -> Result<ShareId, String> {
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
fn scope(archive: &ArchiveData, conversation: &str) -> Result<Scope, String> {
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
    Ok(Scope {
        channel: channel.id.0,
        participants,
    })
}
fn conversation(archive: &ArchiveData, scope: &Scope) -> Option<String> {
    let channel = archive.channels.iter().rev().find(|c| {
        c.id.0 == scope.channel && c.self_member_id.is_some_and(|own| scope.permits(&own.0))
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
fn snapshot(backend: &Backend, archive: &ArchiveData, filter: Option<&str>) -> FileSnapshot {
    let files = backend
        .engine
        .views()
        .into_iter()
        .filter_map(|view| {
            let conversation = conversation(archive, &view.state.manifest.scope)?;
            if filter.is_some_and(|f| f != conversation) {
                return None;
            }
            let state = match view.state.status {
                Status::Offered => FileState::Offered,
                Status::Importing => FileState::Importing,
                Status::Downloading if view.waiting_for_peers => FileState::WaitingForPeers,
                Status::Downloading => FileState::Downloading,
                Status::Paused => FileState::Paused,
                Status::Complete => FileState::Complete,
                Status::Failed => FileState::Failed,
                Status::Cancelled => FileState::Cancelled,
            };
            Some(FileInfo {
                id: hex(&view.state.manifest.id),
                conversation,
                name: view.state.manifest.name.clone(),
                size_bytes: view.state.manifest.size.to_string(),
                verified_bytes: view.state.verified_bytes().to_string(),
                state,
                sources: view.sources as u16,
                completed_by: view.delivered as u16,
                error: view.state.error.clone(),
            })
        })
        .collect();
    FileSnapshot {
        files,
        quota_bytes: backend.engine.cache.config.quota_bytes.to_string(),
        used_bytes: backend.engine.cache.used().to_string(),
        retention_days: (backend.engine.cache.config.retention_secs / 86400).min(u16::MAX as u64)
            as u16,
    }
}
fn authorize(backend: &Backend, share: ShareId) -> Result<(), String> {
    let state = backend.engine.cache.get(share).map_err(|e| e.to_string())?;
    if backend.engine.own_scope(&state.manifest.scope) {
        Ok(())
    } else {
        Err("File conversation is no longer authorized".into())
    }
}
fn announce(backend: &mut Backend, manifest: Manifest, archive: &ArchiveData) {
    if let Some(channel) = archive
        .channels
        .iter()
        .find(|c| c.active && c.id.0 == manifest.scope.channel)
    {
        for member in channel.members.iter().filter(|m| !m.is_self).take(64) {
            let peer = Peer {
                channel: channel.id.0,
                member: member.id.0,
            };
            if backend.engine.permits(peer, &manifest.scope) && backend.pending.len() < 128 {
                backend.pending.push_back(Action {
                    peer,
                    message: gcoms_file_transfer::swarm::Message::Offers {
                        manifests: vec![manifest.clone()],
                        next: None,
                    },
                });
            }
        }
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
        let runtime = unlocked.files.clone().ok_or_else(|| {
            unlocked
                .file_error
                .clone()
                .unwrap_or_else(|| "File cache unavailable".into())
        })?;
        let archive = unlocked.client.file_context();
        if let FileRequest::Configure {
            quota_bytes,
            retention_days,
        } = &request
        {
            let quota = number(quota_bytes)?;
            if !(1024 * 1024..=1024 * 1024 * 1024 * 1024).contains(&quota)
                || !(1..=365).contains(retention_days)
            {
                return Err("Choose 1 MiB–1 TiB of cache and 1–365 retention days".into());
            }
            let mut candidate = unlocked.state.clone();
            candidate.file_config = CacheConfig {
                quota_bytes: quota,
                retention_secs: u64::from(*retention_days) * 86400,
            };
            unlocked.store.save(&candidate)?;
            unlocked.state = candidate;
        }
        let config = unlocked.state.file_config.clone();
        drop(session);
        self.refresh_file_members(&runtime, &archive).await?;
        tokio::task::spawn_blocking(move || {
            if !runtime.enabled.load(Ordering::Acquire) {
                return Err("File sharing is locked".into());
            }
            let mut backend = runtime
                .inner
                .lock()
                .map_err(|_| "File worker unavailable")?;
            backend.engine.cache.config = config;
            let mut filter = None;
            match request {
                FileRequest::List { conversation } => filter = conversation,
                FileRequest::Prepare {
                    id: handle,
                    conversation,
                    name,
                    size_bytes,
                } => {
                    let scope = scope(&archive, &conversation)?;
                    if !backend.engine.own_scope(&scope) {
                        return Err("Conversation membership is not ready".into());
                    }
                    backend
                        .engine
                        .cache
                        .begin_import(id(&handle)?, scope, name, number(&size_bytes)?, now())
                        .map_err(|e| e.to_string())?;
                }
                FileRequest::Commit { id: handle } => {
                    let share = id(&handle)?;
                    authorize(&backend, share)?;
                    let manifest = backend
                        .engine
                        .cache
                        .finish_import(share, now())
                        .map_err(|e| e.to_string())?;
                    announce(&mut backend, manifest, &archive);
                }
                FileRequest::Accept { id: handle } | FileRequest::Resume { id: handle } => {
                    let share = id(&handle)?;
                    authorize(&backend, share)?;
                    backend
                        .engine
                        .accept(share, now())
                        .map_err(|e| e.to_string())?;
                }
                FileRequest::Pause { id: handle } => {
                    let share = id(&handle)?;
                    authorize(&backend, share)?;
                    backend.engine.pause(share).map_err(|e| e.to_string())?;
                }
                FileRequest::Cancel { id: handle } => {
                    // The unlocked local owner can always discard their cache,
                    // including a conversation they can no longer fetch from.
                    let share = id(&handle)?;
                    backend.engine.cancel(share).map_err(|e| e.to_string())?;
                }
                FileRequest::Configure { .. } => {}
            }
            Ok(snapshot(&backend, &archive, filter.as_deref()))
        })
        .await
        .map_err(|_| "File worker stopped".to_string())?
    }
    pub(super) async fn file_piece_io(&self, frame: Vec<u8>) -> Result<Vec<u8>, String> {
        self.require(Capability::ChannelMember)?;
        let (header, bytes) = gchat_api::files::decode_io(&frame)?;
        if header.instance != self.id {
            return Err("File request belongs to another instance".into());
        }
        if !header.upload && !bytes.is_empty() {
            return Err("Download request contains unexpected bytes".into());
        }
        let session = self.session.lock().await;
        let unlocked = session
            .as_ref()
            .filter(|s| !s.ui_locked)
            .ok_or("Unlock this instance to use files")?;
        let runtime = unlocked.files.clone().ok_or_else(|| {
            unlocked
                .file_error
                .clone()
                .unwrap_or_else(|| "File cache unavailable".into())
        })?;
        let archive = unlocked.client.file_context();
        drop(session);
        self.refresh_file_members(&runtime, &archive).await?;
        let bytes = Zeroizing::new(bytes.to_vec());
        tokio::task::spawn_blocking(move || {
            if !runtime.enabled.load(Ordering::Acquire) {
                return Err("File sharing is locked".into());
            }
            let mut backend = runtime
                .inner
                .lock()
                .map_err(|_| "File worker unavailable")?;
            let share = id(&header.id)?;
            if header.upload {
                authorize(&backend, share)?;
                backend
                    .engine
                    .cache
                    .import_piece(share, header.piece, &bytes)
                    .map_err(|e| e.to_string())?;
                Ok(Vec::new())
            } else {
                backend
                    .engine
                    .cache
                    .export_piece(share, header.piece)
                    .map_err(|e| e.to_string())
            }
        })
        .await
        .map_err(|_| "File worker stopped".to_string())?
    }
    async fn refresh_file_members(
        &self,
        runtime: &Arc<FileRuntime>,
        archive: &ArchiveData,
    ) -> Result<(), String> {
        let sdk = self.runtime.sdk_client();
        let joined = sdk.list_channels().await.map_err(|e| e.to_string())?;
        let mut rosters = Vec::new();
        for channel in archive.channels.iter().filter(|c| {
            c.active
                && joined.iter().any(|j| {
                    j.id.0 == c.id.0
                        && j.channel == c.protocol_name
                        && j.status == gcoms_sdk::ChannelStatus::Active
                })
        }) {
            // Query the protocol's authenticated roster, not names supplied by a UI.
            if let Ok(roster) = sdk.channel_roster(&channel.protocol_name).await {
                if let Some(own) = roster.iter().find(|m| m.is_self) {
                    rosters.push((
                        channel.id.0,
                        channel.protocol_name.clone(),
                        own.member_id,
                        roster.into_iter().map(|m| m.member_id).collect::<Vec<_>>(),
                    ));
                }
            }
        }
        let runtime = runtime.clone();
        tokio::task::spawn_blocking(move || {
            let mut backend = runtime
                .inner
                .lock()
                .map_err(|_| "File worker unavailable")?;
            let removed: Vec<_> = backend
                .routes
                .keys()
                .filter(|id| !rosters.iter().any(|r| r.0 == **id))
                .copied()
                .collect();
            for channel in removed {
                backend.routes.remove(&channel);
                backend.engine.set_members(channel, [0; 32], []);
            }
            for (channel, name, own, roster) in rosters {
                backend.routes.insert(channel, name);
                backend.engine.set_members(channel, own, roster);
            }
            Ok(())
        })
        .await
        .map_err(|_| "File worker stopped".to_string())?
    }
    pub(super) fn spawn_file_worker(service: &Arc<Self>) -> tokio::task::JoinHandle<()> {
        let weak = Arc::downgrade(service);
        let sdk = service.runtime.sdk_client();
        // Observe the node's authenticated stream directly. The chat owner's
        // protocol subscription already persists events; a second persistence
        // forwarder can outlive this worker and retain the profile at reopen.
        let mut events = sdk.embedded().subscribe_events();
        let mut stop = service.stopped.subscribe();
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_millis(250));
            interval.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
            let mut sends = tokio::task::JoinSet::new();
            loop {
                let event = tokio::select! {
                    _=stop.changed()=>break,
                    _=interval.tick()=>None,
                    _=sends.join_next(), if !sends.is_empty()=>None,
                    event=events.recv()=>match event{Some(event)=>Some(event),None=>break},
                };
                let Some(service) = weak.upgrade() else { break };
                // Ordinary IPC contention must not discard an already-received
                // authenticated block. Shutdown can still cancel this wait.
                let session = tokio::select! {
                    _=stop.changed()=>break,
                    session=service.session.lock()=>session,
                };
                let Some((runtime, archive, client)) =
                    session.as_ref().filter(|s| !s.ui_locked).and_then(|s| {
                        s.files
                            .clone()
                            .map(|files| (files, s.client.file_context(), s.client.clone()))
                    })
                else {
                    continue;
                };
                drop(session);
                if service
                    .refresh_file_members(&runtime, &archive)
                    .await
                    .is_err()
                {
                    continue;
                }
                let worker = runtime.clone();
                // Keep bounded sends alive across receive/tick iterations. A slow
                // receipt must not block the peer's next piece response.
                let send_capacity = 4usize.saturating_sub(sends.len());
                // Copy aggregate counters only; do not retain a node handle in
                // blocking file work or extend its profile lock lifetime.
                let protocol_diagnostics = worker
                    .diagnostics
                    .then(|| {
                        client.sdk_client().ok().map(|sdk| {
                            sdk.node().enable_diagnostics();
                            sdk.node().diagnostics()
                        })
                    })
                    .flatten();
                let result = tokio::task::spawn_blocking(move || -> Result<Work, String> {
                    if !worker.enabled.load(Ordering::Acquire) {
                        return Ok(Work {
                            actions: Vec::new(),
                            pms: Vec::new(),
                        });
                    }
                    let mut backend = worker.inner.lock().map_err(|_| "File worker unavailable")?;
                    let mut new = Vec::new();
                    if let Some(gcoms_sdk::ClientEvent::ChannelDirectMessage {
                        channel,
                        sender_member_id,
                        body,
                        ..
                    }) = event
                    {
                        if gcoms_core::is_piece_application_payload(&body) {
                            if let (Some(channel_id), Ok(application)) = (
                                backend
                                    .routes
                                    .iter()
                                    .find(|(_, name)| **name == channel)
                                    .map(|(id, _)| *id),
                                gcoms_sdk::ApplicationMessage::decode(&body),
                            ) {
                                if let Ok(message) =
                                    gcoms_file_transfer::swarm::Message::decode(&application.body)
                                {
                                    // A rejected remote record cannot stop other transfers.
                                    if let Ok(actions) = backend.engine.receive(
                                        Peer {
                                            channel: channel_id,
                                            member: sender_member_id,
                                        },
                                        message,
                                        now(),
                                    ) {
                                        new.extend(actions);
                                    }
                                }
                            }
                        }
                    }
                    new.extend(backend.engine.tick(now()).map_err(|e| e.to_string())?);
                    if worker.diagnostics && now() >= backend.next_diagnostic {
                        use std::io::Write;
                        backend.next_diagnostic = now().saturating_add(5);
                        let d = backend.engine.diagnostics();
                        let observation = serde_json::json!({
                            "event": "file_diagnostics", "unix_seconds": now(),
                            "pid": std::process::id(), "verified_pieces": d.verified_pieces,
                            "received_blocks": d.received_blocks, "received_bytes": d.received_bytes,
                            "send_failures": worker.send_failures.load(Ordering::Relaxed),
                            "send_timeouts": worker.send_timeouts.load(Ordering::Relaxed),
                            "rejected_pieces": d.rejected_pieces, "retries": d.retries,
                            "buffered_bytes": d.buffered_bytes, "pending_pulls": d.pending_pulls,
                            "pending_actions": backend.pending.len(), "cache_bytes": backend.engine.cache.used(),
                            "protocol": protocol_diagnostics,
                        });
                        // Optional local aggregates only. A full diagnostic disk
                        // must not turn an observation into a transfer failure.
                        let _ = writeln!(std::io::stderr().lock(), "{observation}");
                    }
                    for action in new {
                        if backend.pending.len() < 128 {
                            backend.pending.push_back(action);
                        }
                    }
                    let mut ready = Vec::new();
                    for _ in 0..send_capacity {
                        if let Some(action) = backend.pending.pop_front() {
                            if let Some(name) = backend.routes.get(&action.peer.channel) {
                                if backend.engine.action_allowed(&action) {
                                    ready.push((name.clone(), action));
                                }
                            }
                        }
                    }
                    let pms = backend
                        .engine
                        .cache
                        .entries()
                        .values()
                        .filter_map(|entry| {
                            let scope = &entry.manifest.scope;
                            if scope.participants.len() != 2
                                || !backend.engine.own_scope(scope)
                                || matches!(
                                    entry.status,
                                    Status::Cancelled | Status::Importing | Status::Failed
                                )
                            {
                                return None;
                            }
                            let channel =
                                archive.channels.iter().find(|c| c.id.0 == scope.channel)?;
                            let own = channel.self_member_id?;
                            let remote =
                                MemberId(*scope.participants.iter().find(|p| **p != own.0)?);
                            let id = ScopedPmId {
                                channel_id: channel.id,
                                self_member_id: own,
                                remote_member_id: remote,
                            };
                            if archive.scoped_pms.iter().any(|p| p.id == id) {
                                return None;
                            }
                            Some((channel.id, remote))
                        })
                        .collect();
                    Ok(Work {
                        actions: ready,
                        pms,
                    })
                })
                .await;
                if let Ok(Ok(work)) = result {
                    let mut changed = false;
                    for (channel, member) in work.pms {
                        if runtime.enabled.load(Ordering::Acquire)
                            && client.open_scoped_pm(channel, member).is_ok()
                        {
                            changed = true;
                        }
                    }
                    if changed {
                        let _ = client.save().await;
                    }
                    for (channel, action) in work.actions {
                        if !runtime.enabled.load(Ordering::Acquire) {
                            break;
                        }
                        let sdk = sdk.clone();
                        let counters = runtime.clone();
                        #[cfg(test)]
                        let receipt_gate = service.file_receipt_gate.lock().unwrap().clone();
                        sends.spawn(async move {
                            if let Ok(bytes) = action.message.encode() {
                                let outcome =
                                    tokio::time::timeout(Duration::from_secs(20), async {
                                        let result = sdk
                                            .send_channel_application(
                                                &channel,
                                                action.peer.member,
                                                CONTENT_TYPE,
                                                &bytes,
                                            )
                                            .await;
                                        // Simulate a delayed receipt after the peer
                                        // has received a request and can answer it.
                                        #[cfg(test)]
                                        if let Some(gate) = receipt_gate {
                                            gate.entered.fetch_add(1, Ordering::SeqCst);
                                            let _permit = gate.release.acquire().await;
                                        }
                                        result
                                    })
                                    .await;
                                let counter = match outcome {
                                    Ok(Ok(_)) => None,
                                    Ok(Err(_)) => Some(&counters.send_failures),
                                    Err(_) => Some(&counters.send_timeouts),
                                };
                                if let Some(counter) = counter {
                                    let _ = counter.fetch_update(
                                        Ordering::Relaxed,
                                        Ordering::Relaxed,
                                        |value| Some(value.saturating_add(1)),
                                    );
                                }
                            }
                        });
                    }
                }
            }
            sends.shutdown().await;
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime::ProtocolRuntime;
    use gchat_api::files::{encode_io, FileIo};
    use gcoms_sdk::{ChannelVisibility, GcClient};

    async fn request(service: &ChatService, request: Request) -> Response {
        service
            .dispatch(RequestEnvelope {
                version: gchat_api::VERSION,
                instance_id: Some(service.id.clone()),
                request,
            })
            .await
            .response
    }

    async fn peer(home: &Path) -> (ProtocolRuntime, Arc<ChatService>) {
        crate::private_fs::make_private(home, true).unwrap();
        let runtime = ProtocolRuntime::create_fixture(
            &home.join("profile"),
            "file-receipt-test",
            "127.0.0.1:0".parse().unwrap(),
            None,
            None,
            &[],
        )
        .await
        .unwrap();
        let service = ChatService::new(
            home.join("archive"),
            runtime.clone(),
            vec![
                Capability::IdentityRead,
                Capability::ChannelMember,
                Capability::ChannelAdmin,
                Capability::EventRead,
            ],
        )
        .unwrap();
        (runtime, service)
    }

    #[tokio::test(flavor = "multi_thread", worker_threads = 2)]
    async fn incoming_file_completes_while_outbound_receipts_are_stalled() {
        let a = tempfile::tempdir().unwrap();
        let b = tempfile::tempdir().unwrap();
        let (ar, sender) = peer(a.path()).await;
        let (br, receiver) = peer(b.path()).await;
        let owner = ar.sdk_client();
        let joiner = br.sdk_client();
        owner
            .create_channel("receipts", "owner", 8, ChannelVisibility::Private)
            .await
            .unwrap();
        let join = joiner.prepare_channel_join("peer").await.unwrap();
        let package = joiner.channel_key_package(join).await.unwrap();
        let welcome = owner
            .admit_channel("receipts", &package, "peer")
            .await
            .unwrap();
        joiner
            .join_channel(join, "receipts", ChannelVisibility::Private, &welcome)
            .await
            .unwrap();
        let gate = Arc::new(TestReceiptGate {
            entered: std::sync::atomic::AtomicUsize::new(0),
            release: tokio::sync::Semaphore::new(0),
        });
        *receiver.file_receipt_gate.lock().unwrap() = Some(gate.clone());
        for service in [&sender, &receiver] {
            assert!(matches!(
                request(
                    service,
                    Request::Unlock {
                        passphrase: "file-receipt-test".into(),
                        create: true,
                    }
                )
                .await,
                Response::Snapshot { .. }
            ));
        }
        tokio::time::timeout(Duration::from_secs(8), async {
            while gate.entered.load(Ordering::SeqCst) == 0 {
                tokio::time::sleep(Duration::from_millis(10)).await;
            }
        })
        .await
        .expect("an outgoing discovery reached the peer, but its receipt is held");

        // Publish only after the receiver has a pending receipt. Its file worker
        // must continue processing authenticated incoming offers and piece data.
        let conversation = sender.snapshot().await.unwrap().conversations[0].id.clone();
        let handle = "81818181818181818181818181818181";
        let bytes = vec![0x7b; 1024];
        assert!(matches!(
            request(
                &sender,
                Request::Files {
                    request: FileRequest::Prepare {
                        id: handle.into(),
                        conversation,
                        name: "receipt.bin".into(),
                        size_bytes: bytes.len().to_string(),
                    },
                }
            )
            .await,
            Response::Files { .. }
        ));
        sender
            .clone()
            .file_io(
                encode_io(
                    &FileIo {
                        instance: sender.id.clone(),
                        id: handle.into(),
                        piece: 0,
                        upload: true,
                    },
                    &bytes,
                )
                .unwrap(),
            )
            .await
            .unwrap();
        assert!(matches!(
            request(
                &sender,
                Request::Files {
                    request: FileRequest::Commit { id: handle.into() },
                }
            )
            .await,
            Response::Files { .. }
        ));

        tokio::time::timeout(Duration::from_secs(8), async {
            let mut accepted = false;
            loop {
                let Response::Files { snapshot } = request(
                    &receiver,
                    Request::Files {
                        request: FileRequest::List { conversation: None },
                    },
                )
                .await
                else {
                    panic!("file list failed")
                };
                if let Some(file) = snapshot.files.iter().find(|f| f.id == handle) {
                    if matches!(file.state, FileState::Complete) {
                        break;
                    }
                    if !accepted {
                        assert!(matches!(file.state, FileState::Offered));
                        assert_eq!(file.verified_bytes, "0");
                        assert!(matches!(
                            request(
                                &receiver,
                                Request::Files {
                                    request: FileRequest::Accept { id: handle.into() },
                                }
                            )
                            .await,
                            Response::Files { .. }
                        ));
                        accepted = true;
                    }
                }
                tokio::time::sleep(Duration::from_millis(20)).await;
            }
        })
        .await
        .expect("incoming file progresses without releasing outbound receipts");
        assert_eq!(
            receiver
                .clone()
                .file_io(
                    encode_io(
                        &FileIo {
                            instance: receiver.id.clone(),
                            id: handle.into(),
                            piece: 0,
                            upload: false,
                        },
                        &[]
                    )
                    .unwrap()
                )
                .await
                .unwrap(),
            bytes
        );
        assert!((1..=4).contains(&gate.entered.load(Ordering::SeqCst)));
        assert_eq!(gate.release.available_permits(), 0);
        tokio::time::timeout(Duration::from_secs(5), receiver.disconnect())
            .await
            .expect("shutdown cancels held sends")
            .unwrap();
        sender.disconnect().await.unwrap();
        drop(sender);
        drop(receiver);
        drop(owner);
        drop(joiner);
        ar.shutdown().await.unwrap();
        br.shutdown().await.unwrap();
    }
}
