use super::*;
use std::path::{Path, PathBuf};

/// An attachment is pinned for its lifetime. No endpoint discovery or fallback.
#[derive(Clone, Debug)]
pub struct ChatClient {
    endpoint: PathBuf,
    instance: String,
    handles: std::sync::Arc<gcoms::rpc::file_store::FileHandles>,
}

impl ChatClient {
    pub async fn connect(endpoint: &Path, expected: Option<&str>) -> Result<Self, String> {
        let envelope = exchange(
            endpoint,
            &RequestEnvelope {
                version: VERSION,
                instance_id: None,
                request: Request::Identify,
            },
        )
        .await?;
        if envelope.version != VERSION || expected.is_some_and(|id| id != envelope.instance_id) {
            return Err("chat instance or API version does not match this attachment".into());
        }
        match &envelope.response {
            Response::Instance { instance } if instance.id == envelope.instance_id => {}
            _ => return Err("invalid chat instance handshake".into()),
        }
        let mut handle_path = endpoint.as_os_str().to_owned();
        handle_path.push(".handles");
        let handles = gcoms::rpc::file_store::FileHandles::open(Path::new(&handle_path))
            .map_err(|e| e.to_string())?;
        Ok(Self {
            endpoint: endpoint.into(),
            instance: envelope.instance_id,
            handles: std::sync::Arc::new(handles),
        })
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
        super::rpc_compat::request(self.service_client(), request).await
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
                version: VERSION,
                instance_id: Some(self.instance.clone()),
                request,
            },
        )
        .await
        .map_err(|message| ChatError {
            code: "transport".into(),
            message,
        })?;
        if envelope.version != VERSION || envelope.instance_id != self.instance {
            return Err(ChatError {
                code: if envelope.version != VERSION {
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
    tokio::time::timeout(std::time::Duration::from_secs(150), async {
        let mut stream = gcoms::sdk::local::connect(&gcoms::sdk::LocalEndpoint::new(endpoint))
            .await
            .map_err(|e| e.to_string())?;
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
