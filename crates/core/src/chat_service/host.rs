//! UI-independent startup, unlock and shutdown. Desktop and Android host this same code.
use super::{instance_metadata, random_id, ChatEndpoint, ChatService};
use crate::runtime::ProtocolRuntime;
use gchat_api::{
    ChatClient, InstanceInfo, Request, RequestEnvelope, Response, ResponseEnvelope, Snapshot,
    VERSION,
};
use gcoms_sdk::{ipc::Capability, LocalEndpoint};
use std::{
    net::SocketAddr,
    path::{Path, PathBuf},
    sync::Arc,
};
use tokio::sync::{watch, Mutex};
use zeroize::Zeroizing;

#[derive(Clone)]
pub struct InstanceConfig {
    pub profile: PathBuf,
    pub archive: PathBuf,
    pub protocol_socket: PathBuf,
    pub listen: SocketAddr,
    pub advertise: Option<SocketAddr>,
    pub relay_file: Option<PathBuf>,
    pub relay_urls: Vec<String>,
    pub network_recovery: bool,
    /// Explicit disposable loopback fixtures only; never inferred from an address.
    pub local_fixture: bool,
    /// Explicit opt-in for the GC/2 carrier profile. Never inferred.
    pub gc2_carrier: bool,
    pub catalog_urls: Vec<String>,
}

impl InstanceConfig {
    pub fn from_home(home: Option<&Path>) -> Result<Self, String> {
        let paths = crate::paths::resolve(home)?;
        Ok(Self {
            profile: paths.profile,
            archive: paths.archive,
            protocol_socket: paths.socket,
            listen: "0.0.0.0:0".parse().expect("static address"),
            advertise: None,
            relay_file: None,
            relay_urls: crate::bootstrap::default_provider_urls(),
            network_recovery: true,
            local_fixture: false,
            gc2_carrier: false,
            catalog_urls: Vec::new(),
        })
    }
    pub fn chat_endpoint(&self) -> PathBuf {
        super::endpoint_for(&self.protocol_socket)
    }
}

struct Running {
    service: Arc<ChatService>,
    runtime: ProtocolRuntime,
    stop: watch::Sender<bool>,
    server: tokio::task::JoinHandle<Result<(), gcoms_sdk::SdkError>>,
}
pub struct InstanceHost {
    config: InstanceConfig,
    id: String,
    label: String,
    boot: String,
    running: Mutex<Option<Running>>,
}
pub fn capabilities() -> Vec<Capability> {
    vec![
        Capability::IdentityRead,
        Capability::DirectMessage,
        Capability::ChannelMember,
        Capability::ChannelAdmin,
        Capability::EventRead,
    ]
}

impl InstanceHost {
    pub fn new(config: InstanceConfig) -> Result<Arc<Self>, String> {
        if !config.profile.exists() && config.archive.exists() {
            return Err(
                "the archive exists but its protocol profile is missing; restore this instance"
                    .into(),
            );
        }
        let metadata = instance_metadata(&config.archive)?;
        Ok(Arc::new(Self {
            config,
            id: metadata.id,
            label: metadata.label,
            boot: random_id(),
            running: Mutex::new(None),
        }))
    }
    fn info(&self) -> InstanceInfo {
        InstanceInfo {
            id: self.id.clone(),
            label: self.label.clone(),
            boot_id: self.boot.clone(),
            locked: true,
            protocol_locked: true,
            profile_exists: self.config.profile.exists(),
            archive_exists: self.config.archive.exists(),
            safety_number: String::new(),
            capabilities: capabilities().iter().map(|c| format!("{c:?}")).collect(),
        }
    }
    fn locked_snapshot(&self) -> Snapshot {
        Snapshot {
            instance: self.info(),
            revision: format!("{}:locked", self.boot),
            conversations: Vec::new(),
            command_history: Vec::new(),
            input_history: Vec::new(),
            provider_errors: Vec::new(),
        }
    }
    async fn unlock(&self, passphrase: String, create: bool) -> Result<Running, String> {
        let passphrase = Zeroizing::new(passphrase);
        if passphrase.len() > 4096 || (create && passphrase.chars().count() < 8) {
            return Err("choose a passphrase of 8–4096 characters".into());
        }
        if create == self.config.profile.exists() {
            return Err("instance creation state changed; refresh before unlocking".into());
        }
        let endpoint = LocalEndpoint::new(&self.config.protocol_socket);
        endpoint.prepare_server().map_err(|e| e.to_string())?;
        let relay = if let Some(path) = self.config.relay_file.as_deref() {
            crate::daemon::resolve_inbox_relay(Some(path), &[], None).await?
        } else {
            None
        };
        let runtime = if create && self.config.local_fixture {
            ProtocolRuntime::create_fixture(
                &self.config.profile,
                &passphrase,
                self.config.listen,
                self.config.advertise,
                relay,
                &[],
            )
            .await?
        } else if self.config.local_fixture {
            ProtocolRuntime::unlock_fixture(
                &self.config.profile,
                &passphrase,
                self.config.listen,
                self.config.advertise,
                relay,
                &[],
            )
            .await?
        } else if create && self.config.gc2_carrier {
            ProtocolRuntime::create_protected(
                &self.config.profile,
                &passphrase,
                self.config.listen,
                self.config.advertise,
                relay,
                &[],
            )
            .await?
        } else if self.config.gc2_carrier {
            ProtocolRuntime::unlock_protected(
                &self.config.profile,
                &passphrase,
                self.config.listen,
                self.config.advertise,
                relay,
                &[],
            )
            .await?
        } else if create {
            ProtocolRuntime::create(
                &self.config.profile,
                &passphrase,
                self.config.listen,
                self.config.advertise,
                relay,
                &[],
            )
            .await?
        } else {
            ProtocolRuntime::unlock(
                &self.config.profile,
                &passphrase,
                self.config.listen,
                self.config.advertise,
                relay,
                &[],
            )
            .await?
        };
        // Interactive chat cannot turn a retained machine/central profile into
        // an unscoped personal endpoint. Preserve the native admission boundary
        // before creating an archive, worker or IPC server.
        let ownership = async {
            let sdk = runtime.sdk_client();
            let embedded = sdk.embedded();
            let node = embedded.node();
            if node.central_ownership_required().await?
                || node.machine_ownership_required().await?
            {
                return Err("retained component ownership requires its explicit scoped daemon configuration".to_string());
            }
            Ok(())
        }.await;
        if let Err(error) = ownership {
            runtime.shutdown().await?;
            return Err(error);
        }
        let service =
            ChatService::new(self.config.archive.clone(), runtime.clone(), capabilities())?;
        runtime.start_network_maintenance(
            self.config.relay_urls.clone(),
            self.config.relay_file.is_none() && self.config.network_recovery,
        )?;
        service.configure_catalogs(self.config.catalog_urls.clone());
        let (stop, receiver) = watch::channel(false);
        let socket = self.config.protocol_socket.clone();
        let sdk = runtime.sdk_client();
        let server = tokio::spawn(async move {
            gcoms_sdk::ipc::serve_local_until(&socket, sdk, capabilities(), async move {
                let mut receiver = receiver;
                let _ = receiver.changed().await;
            })
            .await
        });
        if create || self.config.archive.exists() {
            let response = service
                .dispatch(RequestEnvelope {
                    version: VERSION,
                    instance_id: Some(self.id.clone()),
                    request: Request::Unlock {
                        passphrase: passphrase.to_string(),
                        create,
                    },
                })
                .await;
            if let Response::Error { message, .. } = response.response {
                if create {
                    let _ = stop.send(true);
                    let _ = server.await;
                    runtime.shutdown().await?;
                    return Err(message);
                }
                // Existing installations may use a different archive passphrase.
                // Keep that archive locked for an explicit second unlock.
            }
        }
        Ok(Running {
            service,
            runtime,
            stop,
            server,
        })
    }

    async fn stop(&self, running: Running) -> Result<(), String> {
        let saved = running.service.disconnect().await;
        let _ = running.stop.send(true);
        let _ = running.server.await;
        drop(running.service);
        let shutdown = running.runtime.shutdown().await;
        let _ = LocalEndpoint::new(&self.config.protocol_socket).cleanup();
        saved.and(shutdown)
    }
}

#[async_trait::async_trait]
impl ChatEndpoint for InstanceHost {
    fn instance_id(&self) -> &str {
        &self.id
    }
    async fn rpc_service(self: Arc<Self>) -> Option<Arc<ChatService>> {
        self.running
            .lock()
            .await
            .as_ref()
            .map(|r| r.service.clone())
    }
    async fn dispatch(&self, mut envelope: RequestEnvelope) -> ResponseEnvelope {
        let error = |code: &str, message| ResponseEnvelope {
            version: VERSION,
            instance_id: self.id.clone(),
            response: Response::Error {
                code: code.into(),
                message,
            },
        };
        if envelope.version != VERSION {
            return error(
                "version",
                "Update this client to match the selected instance API version".into(),
            );
        }
        if !matches!(envelope.request, Request::Identify)
            && envelope.instance_id.as_deref() != Some(&self.id)
        {
            return error(
                "instance",
                "This attachment is bound to a different instance".into(),
            );
        }
        envelope.request = super::lifecycle_request(envelope.request);
        // Do not hold the lifecycle lock during event long-polls.
        if !matches!(
            envelope.request,
            Request::Unlock { .. } | Request::Disconnect
        ) {
            let service = self
                .running
                .lock()
                .await
                .as_ref()
                .map(|r| r.service.clone());
            if let Some(service) = service {
                return service.dispatch(envelope).await;
            }
        }
        let mut running = self.running.lock().await;
        if matches!(envelope.request, Request::Disconnect) {
            if let Some(previous) = running.take() {
                if let Err(message) = self.stop(previous).await {
                    return error("rejected", message);
                }
            }
            return ResponseEnvelope {
                version: VERSION,
                instance_id: self.id.clone(),
                response: Response::Snapshot {
                    snapshot: self.locked_snapshot(),
                },
            };
        }
        if let Some(current) = running.as_ref() {
            return current.service.dispatch(envelope).await;
        }
        let response = match envelope.request {
            Request::Identify => Response::Instance {
                instance: self.info(),
            },
            Request::NetworkStatus => Response::NetworkStatus {
                status: gchat_api::NetworkStatus::new(gchat_api::NetworkState::Locked),
            },
            Request::Snapshot => Response::Snapshot {
                snapshot: self.locked_snapshot(),
            },
            Request::Events { after, wait_ms } => {
                drop(running);
                let deadline = tokio::time::Instant::now()
                    + std::time::Duration::from_millis(u64::from(wait_ms.min(20_000)));
                loop {
                    let service = self
                        .running
                        .lock()
                        .await
                        .as_ref()
                        .map(|r| r.service.clone());
                    let revision = if let Some(service) = service {
                        service.snapshot().await.expect("snapshot").revision
                    } else {
                        self.locked_snapshot().revision
                    };
                    if revision != after || tokio::time::Instant::now() >= deadline {
                        return ResponseEnvelope {
                            version: VERSION,
                            instance_id: self.id.clone(),
                            response: Response::Changed { revision },
                        };
                    }
                    tokio::time::sleep(std::time::Duration::from_millis(200)).await;
                }
            }
            Request::Unlock { passphrase, create } => match self.unlock(passphrase, create).await {
                Ok(current) => {
                    let snapshot = current
                        .service
                        .snapshot()
                        .await
                        .expect("snapshot is infallible");
                    *running = Some(current);
                    Response::Snapshot { snapshot }
                }
                Err(message) => return error("rejected", message),
            },
            _ => return error(
                "disconnected",
                "Reconnect this instance to receive messages. Unlock its protocol profile first."
                    .into(),
            ),
        };
        ResponseEnvelope {
            version: VERSION,
            instance_id: self.id.clone(),
            response,
        }
    }
    async fn flush(&self) -> Result<(), String> {
        if let Some(running) = self.running.lock().await.take() {
            self.stop(running).await
        } else {
            Ok(())
        }
    }
}

/// Start an explicitly selected local instance if it is not running.
/// Arguments contain only public configuration; unlock happens through private IPC.
pub async fn ensure_running(
    config: &InstanceConfig,
    executable: &Path,
    gchat_binary: bool,
) -> Result<ChatClient, String> {
    let endpoint = config.chat_endpoint();
    let metadata = instance_metadata(&config.archive)?;
    if let Ok(client) = ChatClient::connect(&endpoint, Some(&metadata.id)).await {
        return Ok(client);
    }
    if gcoms_sdk::local::connect(&LocalEndpoint::new(&config.protocol_socket))
        .await
        .is_ok()
    {
        return Err("the selected daemon has no shared chat API; restart that instance with the updated gcd".into());
    }
    let log_path = config.archive.with_extension("service.log");
    let mut options = std::fs::OpenOptions::new();
    options.create(true).append(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.mode(0o600);
    }
    if log_path.exists() {
        crate::private_fs::validate_private_file(&log_path, "service log")?;
    }
    let log = options.open(&log_path).map_err(|e| e.to_string())?;
    crate::private_fs::make_private(&log_path, false)?;
    let mut command = std::process::Command::new(executable);
    if gchat_binary {
        command.arg("daemon");
    }
    command
        .arg("--interactive")
        .arg("--store")
        .arg(&config.profile)
        .arg("--socket")
        .arg(&config.protocol_socket)
        .arg("--chat-archive")
        .arg(&config.archive)
        .arg("--listen")
        .arg(config.listen.to_string())
        .stdin(std::process::Stdio::null())
        .stdout(std::process::Stdio::null())
        .stderr(log);
    if let Some(address) = config.advertise {
        command.arg("--advertise").arg(address.to_string());
    }
    if let Some(path) = &config.relay_file {
        command.arg("--inbox-relay-file").arg(path);
    }
    for url in &config.relay_urls {
        command.arg("--relay-bootstrap-url").arg(url);
    }
    if config.local_fixture {
        command.arg("--local-fixture");
    }
    if config.gc2_carrier {
        command.arg("--gc2-carrier");
    }
    if !config.network_recovery {
        command.arg("--no-network-bootstrap");
    }
    for url in &config.catalog_urls {
        command.arg("--chat-catalog-url").arg(url);
    }
    // A selected instance outlives the terminal/window that first attached.
    // Redirecting stdio alone still leaves Unix children in the terminal's
    // session, and Windows children attached to its console.
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        // SAFETY: setsid is an async-signal-safe syscall; no allocation or locks
        // occur between fork and exec in this callback.
        unsafe {
            command.pre_exec(|| rustix::process::setsid().map(|_| ()).map_err(Into::into));
        }
    }
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        use windows_sys::Win32::System::Threading::{CREATE_NEW_PROCESS_GROUP, DETACHED_PROCESS};
        command.creation_flags(CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS);
    }
    let mut child = command.spawn().map_err(|e| e.to_string())?;
    for _ in 0..200 {
        if let Ok(client) = ChatClient::connect(&endpoint, Some(&metadata.id)).await {
            return Ok(client);
        }
        if let Some(status) = child.try_wait().map_err(|e| e.to_string())? {
            return Err(format!(
                "selected instance stopped ({status}); see {}",
                log_path.display()
            ));
        }
        tokio::time::sleep(std::time::Duration::from_millis(50)).await;
    }
    Err(format!(
        "selected instance did not become ready; see {}",
        log_path.display()
    ))
}

#[cfg(test)]
mod retained_scope_tests {
    use super::*;
    use gcoms_sdk::{
        machine::{ComponentCredentials, ComponentRegistration, MachineRegistry},
        GcClient,
    };

    #[tokio::test]
    async fn personal_host_refuses_retained_machine_before_archive_or_ipc() {
        let dir = tempfile::tempdir().unwrap();
        crate::private_fs::make_private(dir.path(), true).unwrap();
        let profile = dir.path().join("machine.gcprotocol");
        let passphrase = "fixture-only-passphrase";
        let registry = MachineRegistry {
            version: 1,
            components: vec![ComponentRegistration {
                credentials: ComponentCredentials {
                    component_id: [1; 16],
                    token: [2; 32],
                },
                capabilities: vec![Capability::IdentityRead],
                peers: Vec::new(),
                files: None,
            }],
        };
        let runtime = ProtocolRuntime::create_fixture(
            &profile,
            passphrase,
            "127.0.0.1:0".parse().unwrap(),
            None,
            None,
            &[],
        )
        .await
        .unwrap();
        runtime
            .sdk_client()
            .embedded()
            .node()
            .configure_component_routes(registry.routing_policy())
            .await
            .unwrap();
        let original = {
            let client = runtime.sdk_client();
            client
                .contact_identity(&client.identity().contact_card)
                .unwrap()
        };
        runtime.shutdown().await.unwrap();
        let config = InstanceConfig {
            profile: profile.clone(),
            archive: dir.path().join("personal.gcarchive"),
            protocol_socket: dir.path().join("personal.sock"),
            listen: "127.0.0.1:0".parse().unwrap(),
            advertise: None,
            relay_file: None,
            relay_urls: Vec::new(),
            network_recovery: false,
            local_fixture: true,
            gc2_carrier: false,
            catalog_urls: Vec::new(),
        };
        let host = InstanceHost::new(config.clone()).unwrap();
        let refusal = match host.unlock(passphrase.into(), false).await {
            Ok(running) => {
                host.stop(running).await.unwrap();
                panic!("owned profile opened as personal chat")
            }
            Err(error) => error,
        };
        assert!(
            refusal.contains("retained component ownership"),
            "{refusal}"
        );
        assert!(!config.archive.exists());
        assert!(!config.protocol_socket.exists());
        let reopened = ProtocolRuntime::unlock_fixture(
            &profile,
            passphrase,
            "127.0.0.1:0".parse().unwrap(),
            None,
            None,
            &[],
        )
        .await
        .unwrap();
        reopened
            .sdk_client()
            .embedded()
            .node()
            .configure_component_routes(registry.routing_policy())
            .await
            .unwrap();
        let reopened_identity = {
            let client = reopened.sdk_client();
            client
                .contact_identity(&client.identity().contact_card)
                .unwrap()
        };
        assert_eq!(reopened_identity, original);
        reopened.shutdown().await.unwrap();
    }
}
