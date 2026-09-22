//! Attachment controls carry opaque handles. Bytes use the bounded native binary
//! exchange, never JSON RPC or a caller-supplied server filesystem path.
use crate::*;
pub const CAPABILITY: &str = "files.v1";
pub const PIECE_BYTES: usize = 256 * 1024;
pub const IO_MAGIC: &[u8; 6] = b"GCFIO1";
pub const IO_LIMIT: usize = PIECE_BYTES + 1024;
#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(tag = "action", rename_all = "snake_case", deny_unknown_fields)]
pub enum FileRequest {
    List {
        conversation: Option<String>,
    },
    Prepare {
        id: String,
        conversation: String,
        name: String,
        size_bytes: String,
    },
    Commit {
        id: String,
    },
    Accept {
        id: String,
    },
    Pause {
        id: String,
    },
    Resume {
        id: String,
    },
    Cancel {
        id: String,
    },
    Configure {
        quota_bytes: String,
        retention_days: u16,
    },
}
#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(rename_all = "snake_case")]
pub enum FileState {
    Offered,
    Importing,
    Downloading,
    WaitingForPeers,
    Paused,
    Complete,
    Failed,
    Cancelled,
}
#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(deny_unknown_fields)]
pub struct FileInfo {
    pub id: String,
    #[serde(default)]
    #[ts(optional)]
    pub aliases: Option<Vec<String>>,
    pub conversation: String,
    pub name: String,
    pub size_bytes: String,
    pub verified_bytes: String,
    pub state: FileState,
    pub sources: u16,
    /// Peers contributing verified pieces since this process opened the cache.
    #[serde(default)]
    pub verified_sources: u16,
    pub completed_by: u16,
    pub error: Option<String>,
}
#[derive(Clone, Debug, Serialize, Deserialize, JsonSchema, TS)]
#[serde(deny_unknown_fields)]
pub struct FileSnapshot {
    pub files: Vec<FileInfo>,
    pub quota_bytes: String,
    pub used_bytes: String,
    pub retention_days: u16,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FileIo {
    pub instance: String,
    pub id: String,
    pub piece: u32,
    pub upload: bool,
}
pub fn encode_io(header: &FileIo, bytes: &[u8]) -> Result<Vec<u8>, String> {
    let header = serde_json::to_vec(header).map_err(|e| e.to_string())?;
    if header.len() > 512 || bytes.len() > PIECE_BYTES {
        return Err("File frame exceeds bound".into());
    }
    let mut out = IO_MAGIC.to_vec();
    out.extend((header.len() as u16).to_be_bytes());
    out.extend(header);
    out.extend(bytes);
    Ok(out)
}
pub fn decode_io(bytes: &[u8]) -> Result<(FileIo, &[u8]), String> {
    if bytes.len() < 8 || bytes.len() > IO_LIMIT || &bytes[..6] != IO_MAGIC {
        return Err("Invalid file frame".into());
    }
    let n = u16::from_be_bytes([bytes[6], bytes[7]]) as usize;
    if n > 512 || bytes.len() < 8 + n || bytes.len() - (8 + n) > PIECE_BYTES {
        return Err("Invalid file frame length".into());
    }
    let header =
        serde_json::from_slice(&bytes[8..8 + n]).map_err(|_| "Invalid file frame header")?;
    Ok((header, &bytes[8 + n..]))
}
