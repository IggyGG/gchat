use super::*;
use std::path::{Path, PathBuf};

/// An attachment is pinned for its lifetime. No endpoint discovery or fallback.
#[derive(Clone, Debug)]
pub struct ChatClient {
    endpoint: PathBuf,
    instance: String,
    api_version: u16,
    capabilities: Vec<String>,
    handles: std::sync::Arc<gcoms::rpc::file_store::FileHandles>,
}

impl ChatClient {
    pub async fn connect(endpoint: &Path, expected: Option<&str>) -> Result<Self, String> {
        Self::connect_host(endpoint, expected, None).await
    }

    /// Check a registered local host before opening per-attachment operation state.
    /// Legacy callers retain the original instance/API handshake.
    pub async fn connect_host(
        endpoint: &Path,
        expected: Option<&str>,
        host_capability: Option<&str>,
    ) -> Result<Self, String> {
        Self::connect_bound(endpoint, expected, host_capability, None).await
    }

    /// A registered Unix host also binds the kernel owner and optional managed PID.
    #[cfg(unix)]
    pub async fn connect_owned_host(
        endpoint: &Path,
        expected: Option<&str>,
        host_capability: Option<&str>,
        owner_uid: u32,
        process_id: Option<u32>,
    ) -> Result<Self, String> {
        Self::connect_bound(
            endpoint,
            expected,
            host_capability,
            Some((owner_uid, process_id)),
        )
        .await
    }

    async fn connect_bound(
        endpoint: &Path,
        expected: Option<&str>,
        host_capability: Option<&str>,
        peer: Option<(u32, Option<u32>)>,
    ) -> Result<Self, String> {
        let (api_version, instance) =
            Self::inspect_bound(endpoint, expected, host_capability, peer).await?;
        let mut handle_path = endpoint.as_os_str().to_owned();
        handle_path.push(".handles");
        let handles = gcoms::rpc::file_store::FileHandles::open(Path::new(&handle_path))
            .map_err(|e| e.to_string())?;
        Ok(Self {
            endpoint: endpoint.into(),
            instance: instance.id,
            api_version,
            capabilities: instance.capabilities,
            handles: std::sync::Arc::new(handles),
        })
    }

    /// Validate the existing public handshake without allocating attachment files.
    pub async fn inspect_host(
        endpoint: &Path,
        expected: Option<&str>,
        host_capability: Option<&str>,
    ) -> Result<InstanceInfo, String> {
        Self::inspect_bound(endpoint, expected, host_capability, None)
            .await
            .map(|(_, instance)| instance)
    }

    /// Read-only inspection retains the same kernel owner/process binding as attachment.
    #[cfg(unix)]
    pub async fn inspect_owned_host(
        endpoint: &Path,
        expected: Option<&str>,
        host_capability: Option<&str>,
        owner_uid: u32,
        process_id: Option<u32>,
    ) -> Result<InstanceInfo, String> {
        Self::inspect_bound(
            endpoint,
            expected,
            host_capability,
            Some((owner_uid, process_id)),
        )
        .await
        .map(|(_, instance)| instance)
    }

    async fn inspect_bound(
        endpoint: &Path,
        expected: Option<&str>,
        host_capability: Option<&str>,
        peer: Option<(u32, Option<u32>)>,
    ) -> Result<(u16, InstanceInfo), String> {
        let mut envelope = exchange_bound(
            endpoint,
            &RequestEnvelope {
                version: VERSION,
                instance_id: None,
                request: Request::Identify,
            },
            peer,
        )
        .await?;
        let mut api_version = VERSION;
        if envelope.version == crate::compat::LEGACY_VERSION
            && matches!(&envelope.response, Response::Error { code, .. } if code == "version")
        {
            let original = envelope.instance_id.clone();
            api_version = crate::compat::LEGACY_VERSION;
            envelope = exchange_bound(
                endpoint,
                &RequestEnvelope {
                    version: api_version,
                    instance_id: None,
                    request: Request::Identify,
                },
                peer,
            )
            .await?;
            if envelope.instance_id != original {
                return Err("chat instance changed during version negotiation".into());
            }
        }
        if envelope.version != api_version || expected.is_some_and(|id| id != envelope.instance_id)
        {
            return Err("chat instance or API version does not match this attachment".into());
        }
        let instance = match envelope.response {
            Response::Instance { instance } if instance.id == envelope.instance_id => instance,
            _ => return Err("invalid chat instance handshake".into()),
        };
        if host_capability
            .is_some_and(|binding| !instance.capabilities.iter().any(|c| c == binding))
        {
            return Err("The running service does not match this identity's registered host. Close its views and restart the registered service with the matching GChat release.".into());
        }
        Ok((api_version, instance))
    }

    /// One bounded piece per owner-authenticated local exchange.
    pub async fn file_io(&self, frame: Vec<u8>) -> Result<Vec<u8>, String> {
        let (header, _) = files::decode_io(&frame)?;
        if header.instance != self.instance {
            return Err("File request belongs to another instance".into());
        }
        tokio::time::timeout(std::time::Duration::from_secs(150), async {
            let mut stream =
                gcoms_sdk::local::connect(&gcoms_sdk::LocalEndpoint::new(&self.endpoint))
                    .await
                    .map_err(|e| e.to_string())?;
            gcoms_sdk::local_rpc::write(&mut stream, &frame, files::IO_LIMIT)
                .await
                .map_err(|e| e.to_string())?;
            let response = gcoms_sdk::local_rpc::read(&mut stream, files::IO_LIMIT)
                .await
                .map_err(|e| e.to_string())?;
            match response.first() {
                Some(0) => Ok(response[1..].to_vec()),
                Some(1) => Err(String::from_utf8_lossy(&response[1..]).into_owned()),
                _ => Err("Invalid file response".into()),
            }
        })
        .await
        .map_err(|_| "File exchange timed out".to_string())?
    }

    pub fn instance_id(&self) -> &str {
        &self.instance
    }
    pub fn endpoint(&self) -> &Path {
        &self.endpoint
    }

    pub async fn request(&self, request: Request) -> Result<Response, String> {
        self.request_typed(request).await.map_err(|e| e.to_string())
    }

    pub async fn request_typed(&self, request: Request) -> Result<Response, ChatError> {
        super::rpc_compat::request(self.service_client(), request, &self.capabilities).await
    }

    pub fn service_client(&self) -> gcoms::rpc::Client<gcoms::rpc::local::LocalTransport> {
        gcoms::rpc::Client::new(
            gcoms::rpc::local::LocalTransport::new(rpc::endpoint_for(&self.endpoint)),
            &self.instance,
        )
        .with_handles(self.handles.clone())
    }

    pub fn pending_operations(&self) -> Result<Vec<gcoms::rpc::OperationHandle>, ChatError> {
        let client = self.service_client();
        client
            .handles()
            .list()
            .map(|handles| {
                handles
                    .into_iter()
                    .filter(|h| {
                        h.instance == self.instance
                            && h.destination == client.destination()
                            && h.service == rpc::SERVICE
                            && h.version == rpc::SERVICE_VERSION
                    })
                    .collect()
            })
            .map_err(|e| super::rpc_compat::error(gcoms::rpc::CallError::Rpc(e)))
    }

    pub async fn operation_status(&self, id: &str) -> Result<gcoms::rpc::ReplyBody, ChatError> {
        super::rpc_compat::status(&self.service_client(), id).await
    }

    pub async fn resume_submit(&self, id: &str) -> Result<Response, ChatError> {
        super::rpc_compat::resume(&self.service_client(), id).await
    }

    /// Explicit v2 compatibility exchange, retained for existing integrations.
    pub async fn request_v2(&self, request: Request) -> Result<Response, ChatError> {
        let envelope = exchange(
            &self.endpoint,
            &RequestEnvelope {
                version: self.api_version,
                instance_id: Some(self.instance.clone()),
                request,
            },
        )
        .await
        .map_err(|message| ChatError {
            code: "transport".into(),
            message,
        })?;
        if envelope.version != self.api_version || envelope.instance_id != self.instance {
            return Err(ChatError {
                code: if envelope.version != self.api_version {
                    "version"
                } else {
                    "instance"
                }
                .into(),
                message: "chat instance changed; this UI remains bound to its original instance"
                    .into(),
            });
        }
        match envelope.response {
            Response::Error { code, message } => Err(ChatError { code, message }),
            response => Ok(response),
        }
    }
}

async fn exchange(endpoint: &Path, request: &RequestEnvelope) -> Result<ResponseEnvelope, String> {
    exchange_bound(endpoint, request, None).await
}

async fn exchange_bound(
    endpoint: &Path,
    request: &RequestEnvelope,
    peer: Option<(u32, Option<u32>)>,
) -> Result<ResponseEnvelope, String> {
    tokio::time::timeout(std::time::Duration::from_secs(150), async {
        let mut stream = gcoms::sdk::local::connect(&gcoms::sdk::LocalEndpoint::new(endpoint))
            .await
            .map_err(|e| e.to_string())?;
        if let Some((uid, pid)) = peer {
            #[cfg(unix)]
            {
                let actual = stream.peer_cred().map_err(|e| e.to_string())?;
                if actual.uid() != uid
                    || pid.is_some_and(|pid| {
                        actual.pid().and_then(|p| u32::try_from(p).ok()) != Some(pid)
                    })
                {
                    return Err(
                        "The local endpoint is not owned by the registered host process".into(),
                    );
                }
            }
            #[cfg(not(unix))]
            {
                let _ = (uid, pid);
                return Err("Unix host credentials are unavailable on this platform".into());
            }
        }
        let encoded = serde_json::to_vec(request).map_err(|e| e.to_string())?;
        gcoms::sdk::local_rpc::write(&mut stream, &encoded, MAX_FRAME_BYTES)
            .await
            .map_err(|e| e.to_string())?;
        let bytes = gcoms::sdk::local_rpc::read(&mut stream, MAX_FRAME_BYTES)
            .await
            .map_err(|e| e.to_string())?;
        serde_json::from_slice(&bytes).map_err(|e| e.to_string())
    })
    .await
    .map_err(|_| "chat service request timed out".to_string())?
}
