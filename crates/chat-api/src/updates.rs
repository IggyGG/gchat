//! Local installation identity and owner-only maintenance controls.
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use ts_rs::TS;

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct BuildInfo {
    pub release_id: String,
    pub gchat_commit: String,
    pub gcoms_commit: String,
    pub version: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(tag = "action", rename_all = "snake_case", deny_unknown_fields)]
pub enum UpdateRequest {
    /// Views renew this lease every fifteen seconds. No private view data.
    Heartbeat {
        view: String,
    },
    Detach {
        view: String,
    },
    Prepare {
        view: String,
        release: String,
    },
    Abort {
        view: String,
        release: String,
    },
    Exit {
        view: String,
        release: String,
    },
}

#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS, PartialEq, Eq)]
#[serde(tag = "state", rename_all = "snake_case")]
pub enum PrepareUpdateResult {
    Attached,
    Ready { process_id: u32, boot_id: String },
    Busy { reason: String },
}
