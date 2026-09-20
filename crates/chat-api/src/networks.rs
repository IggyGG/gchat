//! Network selection is an explicit boundary for every conversation/file call.
use super::*;

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(rename_all = "camelCase")]
pub struct JoinedNetwork {
    pub id: String,
    pub name: String,
    pub fingerprint: String,
    pub primary: bool,
    pub status: NetworkStatus,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(rename_all = "camelCase")]
pub struct InvitationPreview {
    pub network: JoinedNetwork,
    pub channel: Option<String>,
    pub new_network: bool,
    #[ts(type = "number")]
    pub expires: u64,
}

#[derive(Clone, Serialize, Deserialize, JsonSchema, TS)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum NetworkRequest {
    List,
    Inspect {
        code: String,
    },
    Join {
        code: String,
        nickname: String,
        accepted_network: String,
        operation_id: String,
    },
    Call {
        network: String,
        request: Box<Request>,
    },
}
// A request can contain private invitation tokens or an unlock secret.
impl std::fmt::Debug for NetworkRequest {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("NetworkRequest([redacted])")
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum NetworkResponse {
    List {
        networks: Vec<JoinedNetwork>,
    },
    Preview {
        preview: InvitationPreview,
    },
    Result {
        network: String,
        response: Box<Response>,
    },
}
