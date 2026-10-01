// Frozen API 2 dialect; see release/contracts/api-2/provenance.json.
//! Local installation identity and owner-only maintenance controls.
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct BuildInfo {
    pub release_id: String,
    pub gchat_commit: String,
    pub gcoms_commit: String,
    pub version: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
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

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(tag = "state", rename_all = "snake_case")]
pub enum PrepareUpdateResult {
    Attached,
    Ready { process_id: u32, boot_id: String },
    Busy { reason: String },
}
