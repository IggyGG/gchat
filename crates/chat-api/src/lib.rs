//! Shared application API. It contains no archive, command parser or GC runtime.
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use ts_rs::TS;

pub mod files;
#[cfg(feature = "native")]
pub mod fleet;
pub mod networks;
pub mod updates;
pub use files::{FileInfo, FileRequest, FileSnapshot, FileState};
pub use networks::{InvitationPreview, JoinedNetwork, NetworkRequest, NetworkResponse};
pub use updates::{BuildInfo, PrepareUpdateResult, UpdateRequest};

pub const VERSION: u16 = 2;
pub const MAX_FRAME_BYTES: usize = 16 * 1024 * 1024;
/// Complete submitted text, including slash-command arguments, measured in UTF-8 bytes.
pub const MAX_INPUT_BYTES: usize = 12_000;
/// Bound of the base64url network-invitation envelope accepted by GComs.
pub const MAX_NETWORK_INVITATION_BYTES: usize = 128 * 1024 * 4 / 3 + 16;

/// Public connection progress; never contains invitations or private routing cards.
#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum NetworkState {
    Locked,
    LocalOnly,
    InvitationRequired,
    Connecting,
    Connected,
    Reconnecting,
    InvitationExpired,
    Unavailable,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct NetworkStatus {
    pub state: NetworkState,
    pub message: String,
}
impl NetworkStatus {
    pub fn new(state: NetworkState) -> Self {
        let message = match state {
            NetworkState::Locked => "Unlock your identity to connect.",
            NetworkState::LocalOnly => "This instance uses an explicitly configured local network.",
            NetworkState::InvitationRequired => {
                "Import a network invitation from the person inviting you."
            }
            NetworkState::Connecting => "Connecting through the GChat relays…",
            NetworkState::Connected => "Connected to the GChat network.",
            NetworkState::Reconnecting => {
                "Relays are unavailable. Reconnecting; your identity and history are preserved."
            }
            NetworkState::InvitationExpired => {
                "Your network invitation has expired. Request a replacement invitation."
            }
            NetworkState::Unavailable => {
                "Network configuration is unavailable. Your identity and history are preserved."
            }
        };
        Self {
            state,
            message: message.into(),
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct InstanceInfo {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    #[ts(optional)]
    pub build: Option<BuildInfo>,
    pub id: String,
    pub label: String,
    pub boot_id: String,
    pub locked: bool,
    pub protocol_locked: bool,
    pub profile_exists: bool,
    pub archive_exists: bool,
    pub safety_number: String,
    pub capabilities: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct Member {
    pub id: String,
    pub nickname: String,
    pub is_self: bool,
    #[serde(default)]
    #[ts(optional)]
    pub recently_active: Option<bool>,
    #[serde(default)]
    pub capabilities: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct Conversation {
    #[serde(default)]
    pub provider: Option<String>,
    pub id: String,
    pub channel_id: String,
    pub kind: ConversationKind,
    pub name: String,
    pub topic: String,
    pub active: bool,
    pub owner: bool,
    #[serde(default)]
    #[ts(optional)]
    pub visibility: Option<String>,
    #[serde(default)]
    #[ts(optional)]
    pub directory: Option<String>,
    pub members: Vec<Member>,
    pub unread: u32,
    pub last_message_id: Option<String>,
    #[serde(default = "default_input_limit")]
    pub input_limit_bytes: usize,
    #[serde(default)]
    pub commands: Vec<CommandSpec>,
}

fn default_input_limit() -> usize {
    MAX_INPUT_BYTES
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ConversationKind {
    Channel,
    Query,
    Archive,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct Message {
    pub id: String,
    pub conversation_id: String,
    pub member_id: Option<String>,
    pub nickname: String,
    pub body: String,
    #[ts(type = "number")]
    pub timestamp: u64,
    pub mine: bool,
    #[serde(default)]
    #[ts(optional)]
    pub operation_id: Option<String>,
    /// Delivered is an authenticated recipient acknowledgement, never a read receipt.
    pub delivery: Option<Delivery>,
    #[serde(default)]
    pub result: Option<ActionResult>,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct ActionResult {
    pub id: String,
    #[serde(default)]
    pub message_id: Option<String>,
    pub state: String,
    /// Exact signed bytes, base64 encoded; views decode only for display.
    pub output_base64: Option<String>,
    pub stderr: bool,
    pub details: Vec<String>,
    pub artifacts: Vec<Artifact>,
}
#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
pub struct Artifact {
    pub name: String,
    pub url: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Delivery {
    LocalAccepted,
    Delivered,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct CommandSpec {
    pub name: String,
    pub usage: String,
    pub description: String,
    pub scope: String,
    pub capability: Option<String>,
    pub available: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(rename_all = "camelCase")]
pub struct DirectoryEntry {
    pub name: String,
    pub joined: bool,
    pub conversation: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum CommandOutput {
    Help {
        commands: Vec<CommandSpec>,
    },
    Directory {
        channels: Vec<DirectoryEntry>,
    },
    Invitation {
        channel: String,
        link: String,
        #[ts(type = "number")]
        expires: u64,
        #[serde(default, rename = "localOnly")]
        local_only: bool,
    },
    Text {
        title: String,
        text: String,
    },
    Status {
        text: String,
    },
    Close {
        conversation: String,
    },
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(rename_all = "camelCase")]
pub struct InputHistoryEntry {
    pub conversation: Option<String>,
    pub text: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(rename_all = "camelCase")]
pub struct ProviderStatus {
    pub id: String,
    pub code: String,
    pub message: String,
    pub retryable: bool,
}

/// Authenticated state changes observed by this profile, retained before publication.
#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct Activity {
    pub id: String,
    pub conversation: String,
    pub kind: String,
    pub text: String,
    #[ts(type = "number")]
    pub timestamp: u64,
}

/// Safe metadata plus the protected result retained in the encrypted operation journal.
#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(rename_all = "camelCase")]
pub struct OperationDetail {
    #[serde(default)]
    #[ts(optional)]
    pub network: Option<String>,
    pub id: String,
    pub instance: String,
    pub conversation: Option<String>,
    pub action: String,
    #[ts(type = "number")]
    pub started: u64,
    pub state: String,
    pub output: Option<CommandOutput>,
    pub message: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(rename_all = "camelCase")]
pub struct Snapshot {
    pub instance: InstanceInfo,
    pub revision: String,
    pub conversations: Vec<Conversation>,
    pub command_history: Vec<String>,
    pub input_history: Vec<InputHistoryEntry>,
    #[serde(default)]
    pub provider_errors: Vec<ProviderStatus>,
    #[serde(default)]
    #[ts(optional)]
    pub operations: Option<Vec<OperationDetail>>,
    #[serde(default)]
    #[ts(optional)]
    pub activity: Option<Vec<Activity>>,
    #[serde(default)]
    #[ts(optional)]
    pub presence_enabled: Option<bool>,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(rename_all = "camelCase")]
pub struct HistoryPage {
    pub messages: Vec<Message>,
    pub before: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
pub struct Completion {
    pub text: String,
    pub description: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Request {
    Update {
        request: UpdateRequest,
    },
    Networks {
        request: NetworkRequest,
    },
    Files {
        request: FileRequest,
    },
    Identify,
    Unlock {
        passphrase: String,
        create: bool,
    },
    Lock,
    Disconnect,
    Snapshot,
    NetworkStatus,
    ImportNetworkInvitation {
        code: String,
    },
    Catalogue {
        conversation: Option<String>,
    },
    History {
        conversation: String,
        before: Option<String>,
        limit: u16,
    },
    Search {
        conversation: String,
        text: String,
        before: Option<String>,
        limit: u16,
    },
    Submit {
        operation_id: String,
        conversation: Option<String>,
        text: String,
    },
    Complete {
        conversation: Option<String>,
        text: String,
    },
    MarkRead {
        conversation: String,
        message_id: String,
    },
    Events {
        after: String,
        wait_ms: u16,
    },
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Response {
    Update {
        result: PrepareUpdateResult,
    },
    Networks {
        response: NetworkResponse,
    },
    Files {
        snapshot: FileSnapshot,
    },
    NetworkStatus {
        status: NetworkStatus,
    },
    Instance {
        instance: InstanceInfo,
    },
    Snapshot {
        snapshot: Snapshot,
    },
    History {
        page: HistoryPage,
    },
    Completed {
        items: Vec<Completion>,
    },
    Catalogue {
        commands: Vec<CommandSpec>,
    },
    Projection {
        conversations: Vec<Conversation>,
        revision: String,
    },
    Output {
        conversation: Option<String>,
        output: CommandOutput,
    },
    Applied {
        conversation: Option<String>,
        notice: Option<String>,
    },
    Changed {
        revision: String,
    },
    Error {
        code: String,
        message: String,
    },
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(deny_unknown_fields)]
pub struct RequestEnvelope {
    pub version: u16,
    pub instance_id: Option<String>,
    pub request: Request,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
pub struct ResponseEnvelope {
    pub version: u16,
    pub instance_id: String,
    pub response: Response,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(deny_unknown_fields)]
pub struct ChatError {
    pub code: String,
    pub message: String,
}
impl ChatError {
    pub fn retryable(&self) -> bool {
        matches!(self.code.as_str(), "transport" | "timeout" | "unavailable")
    }
}
impl std::fmt::Display for ChatError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: {}", self.code, self.message)
    }
}
impl std::error::Error for ChatError {}

#[cfg(feature = "native")]
mod legacy;
#[cfg(feature = "native")]
mod native_files;
#[cfg(feature = "native")]
mod rpc_compat;
#[cfg(feature = "native")]
pub use legacy::ChatClient;
pub mod rpc;

pub fn typescript() -> String {
    let declarations = [
        JoinedNetwork::decl(),
        InvitationPreview::decl(),
        NetworkRequest::decl(),
        NetworkResponse::decl(),
        files::FilePublication::decl(),
        FileInfo::decl(),
        FileRequest::decl(),
        FileSnapshot::decl(),
        FileState::decl(),
        NetworkState::decl(),
        NetworkStatus::decl(),
        BuildInfo::decl(),
        UpdateRequest::decl(),
        PrepareUpdateResult::decl(),
        InstanceInfo::decl(),
        Member::decl(),
        Conversation::decl(),
        ConversationKind::decl(),
        Message::decl(),
        ActionResult::decl(),
        Artifact::decl(),
        Delivery::decl(),
        CommandSpec::decl(),
        DirectoryEntry::decl(),
        CommandOutput::decl(),
        InputHistoryEntry::decl(),
        ProviderStatus::decl(),
        Activity::decl(),
        OperationDetail::decl(),
        Snapshot::decl(),
        HistoryPage::decl(),
        Completion::decl(),
        Request::decl(),
        Response::decl(),
        RequestEnvelope::decl(),
        ResponseEnvelope::decl(),
    ];
    format!("// Generated by cargo run -p gchat-api --bin gchat-types. Do not edit.\nexport const API_VERSION = {VERSION};\nexport const MAX_INPUT_BYTES = {MAX_INPUT_BYTES};\nexport const MAX_NETWORK_INVITATION_BYTES = {MAX_NETWORK_INVITATION_BYTES};\n{}\n",
        declarations.into_iter().map(|s| format!("export {s}").lines().map(str::trim_end).collect::<Vec<_>>().join("\n")).collect::<Vec<_>>().join("\n"))
}
