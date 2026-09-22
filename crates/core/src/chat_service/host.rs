//! UI-independent startup, unlock and shutdown. Mobile hosts this in-process.
use super::{instance_metadata, random_id, ChatEndpoint, ChatService};
use crate::runtime::ProtocolRuntime;
use gchat_api::{
    ChatClient, InstanceInfo, Request, RequestEnvelope, Response, ResponseEnvelope, Snapshot,
    VERSION,
};
use gcoms::sdk::{ipc::Capability, LocalEndpoint};
use std::{
    net::SocketAddr,
    path::{Path, PathBuf},
    sync::Arc,
};
use tokio::sync::{watch, Mutex};
use zeroize::Zeroizing;

#[derive(Clone)]
pub struct InstanceConfig {
    pub protocol_backend: gcoms::Backend,
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
    pub fleet_config: Option<PathBuf>,
}

impl InstanceConfig {
    pub fn from_home(home: Option<&Path>) -> Result<Self, String> {
        let paths = crate::paths::resolve(home)?;
        Ok(Self {
            protocol_backend: crate::runtime::default_backend(),
            profile: paths.profile,
            archive: paths.archive,
            protocol_socket: paths.socket,
            listen: "0.0.0.0:0".parse().expect("static address"),
            advertise: None,
            relay_file: None,
            relay_urls: crate::bootstrap::default_provider_urls(),
            network_recovery: true,
            local_fixture: false,
            gc2_carrier: cfg!(any(target_os = "android", target_os = "ios")),
            catalog_urls: Vec::new(),
            fleet_config: None,
        })
    }
    pub fn chat_endpoint(&self) -> PathBuf {
        super::endpoint_for(&self.protocol_socket)
    }

    fn uses_protocol_ipc(&self) -> bool {
        !matches!(self.protocol_backend, gcoms::Backend::NetworkClient)
    }
}

struct ProtocolIpc {
    stop: watch::Sender<bool>,
    server: tokio::task::JoinHandle<Result<(), gcoms::sdk::SdkError>>,
}
impl ProtocolIpc {
    async fn stop(self) {
        let _ = self.stop.send(true);
        let _ = self.server.await;
    }
}
struct Running {
    service: Arc<ChatService>,
    runtime: ProtocolRuntime,
    ipc: Option<ProtocolIpc>,
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
        Capability::FileSharing,
        Capability::IdentityRead,
        Capability::DirectMessage,
        Capability::ChannelMember,
        Capability::ChannelAdmin,
        Capability::EventRead,
    ]
}

impl InstanceHost {
    /// Uses existing unlocked runtimes; notification work never opens a profile.
    #[cfg(feature = "mobile-push")]
    pub async fn push_networks(&self) -> Result<Vec<String>, String> {
        let running = self.running.lock().await;
        let current = running
            .as_ref()
            .ok_or("Unlock GChat to configure notifications")?;
        if !current
            .service
            .session
            .lock()
            .await
            .as_ref()
            .is_some_and(|session| !session.ui_locked)
        {
            return Err("Unlock GChat to configure notifications".into());
        }
        let mut result = vec!["primary".to_owned()];
        result.extend(current.service.networks.lock().await.keys().cloned());
        Ok(result)
    }

    #[cfg(feature = "mobile-push")]
    async fn push_runtime(&self, network: &str) -> Result<ProtocolRuntime, String> {
        let running = self.running.lock().await;
        let current = running
            .as_ref()
            .ok_or("Unlock GChat to configure notifications")?;
        if !current
            .service
            .session
            .lock()
            .await
            .as_ref()
            .is_some_and(|session| !session.ui_locked)
        {
            return Err("Unlock GChat to configure notifications".into());
        }
        if network == "primary" {
            return Ok(current.runtime.clone());
        }
        let result = current
            .service
            .networks
            .lock()
            .await
            .get(network)
            .map(|child| child.runtime.clone())
            .ok_or_else(|| "Notification network is unavailable".into());
        result
    }

    #[cfg(feature = "mobile-push")]
    pub async fn request_push_registration(
        &self,
        network: &str,
        request: gcoms::runtime::push_notifications::PushRegistrationRequest,
    ) -> Result<gcoms::runtime::push_notifications::PushRegistrationTicket, String> {
        let runtime = self.push_runtime(network).await?;
        runtime
            .embedded()
            .ok_or("Notifications require the in-process runtime")?
            .node()
            .request_push_registration(request)
            .await
    }

    #[cfg(feature = "mobile-push")]
    pub async fn request_push_revocation(
        &self,
        network: &str,
        request: gcoms::runtime::push_notifications::PushRegistrationRequest,
    ) -> Result<gcoms::runtime::push_notifications::PushRegistrationTicket, String> {
        let runtime = self.push_runtime(network).await?;
        runtime
            .embedded()
            .ok_or("Notifications require the in-process runtime")?
            .node()
            .request_push_revocation(request)
            .await
    }

    #[cfg(feature = "mobile-push")]
    pub async fn bind_push_notifications(
        &self,
        network: &str,
        reference: [u8; 32],
        revision: u64,
        expires: u64,
    ) -> Result<(), String> {
        let runtime = self.push_runtime(network).await?;
        runtime
            .embedded()
            .ok_or("Notifications require the in-process runtime")?
            .node()
            .bind_push_notifications(reference, revision, expires)
            .await
    }

    pub fn new(config: InstanceConfig) -> Result<Arc<Self>, String> {
        if config.fleet_config.is_some()
            && !matches!(config.protocol_backend, gcoms::Backend::Embedded)
        {
            return Err("fleet requires the desktop in-process GChat host".into());
        }
        #[cfg(any(target_os = "android", target_os = "ios"))]
        if config.uses_protocol_ipc() || !config.gc2_carrier {
            return Err("mobile instances require the outbound GC/2 network client".into());
        }
        if !config.uses_protocol_ipc() && (config.listen.port() != 0 || config.advertise.is_some())
        {
            return Err("outbound instances cannot configure listeners or advertisements".into());
        }
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
            operations: Some(Vec::new()),
            activity: Some(Vec::new()),
            presence_enabled: Some(false),
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
        if self.config.uses_protocol_ipc() {
            LocalEndpoint::new(&self.config.protocol_socket)
                .prepare_server()
                .map_err(|e| e.to_string())?;
        }
        let relay = if let Some(path) = self.config.relay_file.as_deref() {
            crate::daemon::resolve_inbox_relay(Some(path), &[], None).await?
        } else {
            None
        };
        let builder = gcoms::Application::builder("gchat")
            .network_config(crate::network::installed_json())
            .profile(&self.config.profile)
            .unlock_secret(passphrase.to_string())
            .create(create)
            .backend(self.config.protocol_backend.clone())
            .carrier_profile(if self.config.gc2_carrier {
                gcoms::sdk::CarrierProfile::Gc2
            } else {
                gcoms::sdk::CarrierProfile::Legacy
            })
            .listen(self.config.listen)
            .advertise(self.config.advertise)
            .relay(relay)
            .receive_messages(false)
            .network_providers(self.config.relay_urls.clone())
            .network_recovery(self.config.relay_file.is_none() && self.config.network_recovery);
        let builder = if self.config.local_fixture {
            builder.local_fixture().listen(self.config.listen)
        } else {
            builder
        };
        let fleet = self
            .config
            .fleet_config
            .as_deref()
            .map(super::fleet::load)
            .transpose()?;
        let builder = if let Some((config, _)) = &fleet {
            builder.central_components(
                config.policy(),
                vec![config.primary_component],
                config.safety_number.clone(),
            )
        } else {
            builder
        };
        let runtime = ProtocolRuntime(builder.open().await?);
        let service =
            match ChatService::new(self.config.archive.clone(), runtime.clone(), capabilities()) {
                Ok(service) => service,
                Err(error) => {
                    runtime.shutdown().await?;
                    return Err(error);
                }
            };
        service.configure_catalogs(self.config.catalog_urls.clone());
        if let Some((config, _)) = fleet {
            let transport = super::fleet::Transport::new(
                self.config
                    .fleet_config
                    .clone()
                    .expect("fleet configuration"),
                self.config.protocol_socket.with_extension("fleet"),
                config,
                runtime.clone(),
            );
            match transport {
                Ok(transport) => *service.fleet.lock().await = Some(transport),
                Err(error) => {
                    runtime.shutdown().await?;
                    return Err(error);
                }
            }
        }
        let ipc = if self.config.uses_protocol_ipc() {
            let (stop, receiver) = watch::channel(false);
            let socket = self.config.protocol_socket.clone();
            let sdk = runtime.sdk_client();
            let server = tokio::spawn(async move {
                gcoms::sdk::ipc::serve_local_until(&socket, sdk, capabilities(), async move {
                    let mut receiver = receiver;
                    let _ = receiver.changed().await;
                })
                .await
            });
            Some(ProtocolIpc { stop, server })
        } else {
            None
        };
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
                    let _ = service.disconnect().await;
                    if let Some(ipc) = ipc {
                        ipc.stop().await;
                    }
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
            ipc,
        })
    }

    async fn stop(&self, running: Running) -> Result<(), String> {
        let saved = running.service.disconnect().await;
        if let Some(ipc) = running.ipc {
            ipc.stop().await;
        }
        drop(running.service);
        let shutdown = running.runtime.shutdown().await;
        if self.config.uses_protocol_ipc() {
            let _ = LocalEndpoint::new(&self.config.protocol_socket).cleanup();
        }
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
    if !config.uses_protocol_ipc() {
        return Err(
            "outbound instances must attach in-process instead of launching a daemon".into(),
        );
    }
    let endpoint = config.chat_endpoint();
    let metadata = instance_metadata(&config.archive)?;
    if let Ok(client) = ChatClient::connect(&endpoint, Some(&metadata.id)).await {
        return Ok(client);
    }
    if gcoms::sdk::local::connect(&LocalEndpoint::new(&config.protocol_socket))
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
    if let Some(path) = &config.fleet_config {
        command.arg("--fleet-config").arg(path);
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
#[path = "host_mobile_tests.rs"]
mod mobile_tests;

#[cfg(test)]
mod retained_scope_tests {
    use super::*;
    use gcoms::runtime::ProtocolRuntime;
    use gcoms::sdk::{
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
            protocol_backend: gcoms::Backend::Embedded,
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
            fleet_config: None,
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
