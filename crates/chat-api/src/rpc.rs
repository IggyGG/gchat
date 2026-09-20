//! Portable service definition shared by Rust, WebAssembly and generated TS.
use crate::*;
use gcoms::rpc::CallContext;

pub const SERVICE: &str = "ghost.chat";
pub const SERVICE_VERSION: u16 = 1;

#[cfg(feature = "native")]
pub fn endpoint_for(chat_endpoint: &std::path::Path) -> std::path::PathBuf {
    let mut path = chat_endpoint.as_os_str().to_owned();
    path.push(".rpc");
    path.into()
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(deny_unknown_fields)]
pub struct Applied {
    pub conversation: Option<String>,
    pub notice: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum SubmitOutcome {
    Applied {
        conversation: Option<String>,
        notice: Option<String>,
    },
    Output {
        conversation: Option<String>,
        output: CommandOutput,
    },
}
impl TryFrom<Response> for SubmitOutcome {
    type Error = ChatError;
    fn try_from(response: Response) -> Result<Self, Self::Error> {
        match response {
            Response::Applied {
                conversation,
                notice,
            } => Ok(Self::Applied {
                conversation,
                notice,
            }),
            Response::Output {
                conversation,
                output,
            } => Ok(Self::Output {
                conversation,
                output,
            }),
            Response::Error { code, message } => Err(ChatError { code, message }),
            _ => Err(ChatError {
                code: "protocol".into(),
                message: "unexpected submit result".into(),
            }),
        }
    }
}
impl From<SubmitOutcome> for Response {
    fn from(value: SubmitOutcome) -> Self {
        match value {
            SubmitOutcome::Applied {
                conversation,
                notice,
            } => Self::Applied {
                conversation,
                notice,
            },
            SubmitOutcome::Output {
                conversation,
                output,
            } => Self::Output {
                conversation,
                output,
            },
        }
    }
}

#[gcoms::rpc::service(name = "ghost.chat", version = 1)]
pub trait Chat {
    /// Idempotent controls over a separately journaled file handle.
    #[rpc(id = "files", kind = "session")]
    async fn files(&self, request: FileRequest) -> Result<FileSnapshot, ChatError>;
    #[rpc(id = "identify", kind = "query")]
    async fn identify(&self) -> Result<InstanceInfo, ChatError>;
    #[rpc(id = "unlock", kind = "session")]
    async fn unlock(&self, passphrase: String, create: bool) -> Result<Snapshot, ChatError>;
    #[rpc(id = "lock", kind = "session")]
    async fn lock(&self) -> Result<InstanceInfo, ChatError>;
    #[rpc(id = "disconnect", kind = "session")]
    async fn disconnect(&self) -> Result<Snapshot, ChatError>;
    #[rpc(id = "snapshot", kind = "query")]
    async fn snapshot(&self) -> Result<Snapshot, ChatError>;
    #[rpc(id = "network_status", kind = "query")]
    async fn network_status(&self) -> Result<NetworkStatus, ChatError>;
    #[rpc(id = "import_network_invitation", kind = "session")]
    async fn import_network_invitation(&self, code: String) -> Result<NetworkStatus, ChatError>;
    #[rpc(id = "catalogue", kind = "query")]
    async fn catalogue(&self, conversation: Option<String>) -> Result<Vec<CommandSpec>, ChatError>;
    #[rpc(id = "history", kind = "query")]
    async fn history(
        &self,
        conversation: String,
        before: Option<String>,
        limit: u16,
    ) -> Result<HistoryPage, ChatError>;
    #[rpc(id = "search", kind = "query")]
    async fn search(
        &self,
        conversation: String,
        text: String,
        before: Option<String>,
        limit: u16,
    ) -> Result<HistoryPage, ChatError>;
    #[rpc(id = "submit", kind = "operation")]
    async fn submit(
        &self,
        context: CallContext,
        conversation: Option<String>,
        text: String,
    ) -> Result<SubmitOutcome, ChatError>;
    #[rpc(id = "complete", kind = "query")]
    async fn complete(
        &self,
        conversation: Option<String>,
        text: String,
    ) -> Result<Vec<Completion>, ChatError>;
    #[rpc(id = "mark_read", kind = "operation")]
    async fn mark_read(
        &self,
        conversation: String,
        message_id: String,
    ) -> Result<Applied, ChatError>;
    #[rpc(id = "events", kind = "query")]
    async fn events(&self, after: String, wait_ms: u16) -> Result<String, ChatError>;
}

pub fn export() -> serde_json::Value {
    serde_json::json!({
        "service": ChatContract::descriptor(),
        "typescript": format!("{}\nexport {}\nexport {}\nexport {}\n", crate::typescript(), ChatError::decl(), Applied::decl(), SubmitOutcome::decl()),
    })
}
