//! Append-only encrypted application transcripts for command-center clients.

use aes_gcm::aead::{Aead, Payload};
use aes_gcm::{Aes256Gcm, Key, KeyInit, Nonce};
use fs2::FileExt;
use rand::RngCore;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::io::{Read, Write};
use zeroize::Zeroizing;

const MAGIC: &[u8; 6] = b"GCCTX1";
const HEADER_LEN: usize = MAGIC.len() + 32;
const MAX_RECORD_BYTES: usize = 16 * 1024 * 1024;
const ARGON_M_COST: u32 = 64 * 1024;
const ARGON_T_COST: u32 = 3;
const ARGON_P_COST: u32 = 1;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TranscriptPolicy {
    Standard,
    Lab,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum DeliveryState {
    Pending,
    Received,
    Delivered,
    Failed,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum ValidationResult {
    NotChecked,
    Valid,
    Invalid { reason: String },
}

impl ValidationResult {
    /// Transcript validation is descriptive and never authorizes execution.
    pub fn authorizes_commands(&self) -> bool {
        false
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct TranscriptTimestamps {
    pub created_unix: u64,
    pub received_unix: Option<u64>,
    pub delivered_unix: Option<u64>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct TranscriptEntry {
    pub peer_identity_hash: [u8; 32],
    pub channel: Option<String>,
    pub pseudonym: Option<String>,
    pub shared_channel: bool,
    pub content_type: String,
    pub body: Vec<u8>,
    pub delivery_state: DeliveryState,
    pub timestamps: TranscriptTimestamps,
    pub validation: ValidationResult,
}

impl TranscriptEntry {
    pub fn authorizes_commands(&self) -> bool {
        false
    }

    fn validate(&self, policy: TranscriptPolicy) -> Result<(), String> {
        if self.content_type.is_empty()
            || !self.content_type.is_ascii()
            || self
                .content_type
                .bytes()
                .any(|byte| byte.is_ascii_control())
        {
            return Err("invalid transcript content type".into());
        }
        if self.channel.is_some() != self.pseudonym.is_some() {
            return Err("channel and pseudonym must be present together".into());
        }
        if self.shared_channel && self.channel.is_none() {
            return Err("shared transcript entry has no channel".into());
        }
        if self.shared_channel && policy != TranscriptPolicy::Lab {
            return Err("shared channels require lab application policy".into());
        }
        Ok(())
    }
}

#[derive(Serialize, Deserialize)]
struct EncryptedRecord {
    generation: u32,
    salt: [u8; 16],
    nonce: [u8; 12],
    ciphertext: Vec<u8>,
}

pub struct ApplicationTranscript {
    file: std::fs::File,
    passphrase: Zeroizing<String>,
    daemon_identity_hash: [u8; 32],
    generation: u32,
    generation_salt: [u8; 16],
    generation_key: Zeroizing<[u8; 32]>,
    policy: TranscriptPolicy,
}

impl ApplicationTranscript {
    pub fn create(
        path: &std::path::Path,
        passphrase: &str,
        daemon_identity_hash: [u8; 32],
        policy: TranscriptPolicy,
    ) -> Result<Self, String> {
        ensure_parent(path)?;
        let mut options = std::fs::OpenOptions::new();
        options.read(true).append(true).create_new(true);
        #[cfg(unix)]
        {
            use std::os::unix::fs::OpenOptionsExt;
            options.mode(0o600);
        }
        let mut file = options.open(path).map_err(|error| error.to_string())?;
        file.try_lock_exclusive()
            .map_err(|_| format!("transcript is already in use: {}", path.display()))?;
        file.write_all(MAGIC)
            .and_then(|_| file.write_all(&daemon_identity_hash))
            .and_then(|_| file.sync_all())
            .map_err(|error| error.to_string())?;
        let mut generation_salt = [0; 16];
        rand::thread_rng().fill_bytes(&mut generation_salt);
        let generation_key = derive_key(passphrase, &generation_salt)?;
        Ok(Self {
            file,
            passphrase: Zeroizing::new(passphrase.to_string()),
            daemon_identity_hash,
            generation: 0,
            generation_salt,
            generation_key,
            policy,
        })
    }

    pub fn open(
        path: &std::path::Path,
        passphrase: &str,
        expected_daemon_identity_hash: [u8; 32],
        policy: TranscriptPolicy,
    ) -> Result<(Self, Vec<TranscriptEntry>), String> {
        crate::private_fs::validate_private_file(path, "transcript")?;
        let mut options = std::fs::OpenOptions::new();
        options.read(true).append(true);
        let mut file = options.open(path).map_err(|error| error.to_string())?;
        file.try_lock_exclusive()
            .map_err(|_| format!("transcript is already in use: {}", path.display()))?;
        let mut raw = Vec::new();
        file.read_to_end(&mut raw)
            .map_err(|error| error.to_string())?;
        if raw.len() < HEADER_LEN || &raw[..MAGIC.len()] != MAGIC {
            return Err("not a command-center transcript".into());
        }
        let daemon_identity_hash: [u8; 32] = raw[MAGIC.len()..HEADER_LEN]
            .try_into()
            .map_err(|_| "invalid transcript identity binding")?;
        if daemon_identity_hash != expected_daemon_identity_hash {
            return Err("transcript belongs to a different daemon identity".into());
        }

        let mut entries = Vec::new();
        let mut generation = 0;
        let mut generation_keys = std::collections::HashMap::new();
        let mut generation_salts = std::collections::HashMap::new();
        let mut offset = HEADER_LEN;
        while offset < raw.len() {
            let length_bytes = raw
                .get(offset..offset + 4)
                .ok_or("truncated transcript record length")?;
            let length = u32::from_be_bytes(length_bytes.try_into().unwrap()) as usize;
            offset += 4;
            if length > MAX_RECORD_BYTES {
                return Err("transcript record exceeds limit".into());
            }
            let encoded = raw
                .get(offset..offset + length)
                .ok_or("truncated transcript record")?;
            offset += length;
            let (record, trailing): (EncryptedRecord, _) = postcard::take_from_bytes(encoded)
                .map_err(|error| format!("invalid transcript record: {error}"))?;
            if !trailing.is_empty() {
                return Err("trailing bytes in transcript record".into());
            }
            if generation_salts
                .insert(record.generation, record.salt)
                .is_some_and(|salt| salt != record.salt)
            {
                return Err("transcript generation changed encryption salt".into());
            }
            if let std::collections::hash_map::Entry::Vacant(key) =
                generation_keys.entry(record.generation)
            {
                key.insert(derive_key(passphrase, &record.salt)?);
            }
            let entry = decrypt_record(
                &record,
                generation_keys
                    .get(&record.generation)
                    .expect("generation key was inserted"),
                &daemon_identity_hash,
            )?;
            entry.validate(policy)?;
            generation = generation.max(record.generation);
            entries.push(entry);
        }
        let generation_salt = generation_salts
            .remove(&generation)
            .unwrap_or_else(random_salt);
        let generation_key = match generation_keys.remove(&generation) {
            Some(key) => key,
            None => derive_key(passphrase, &generation_salt)?,
        };
        Ok((
            Self {
                file,
                passphrase: Zeroizing::new(passphrase.to_string()),
                daemon_identity_hash,
                generation,
                generation_salt,
                generation_key,
                policy,
            },
            entries,
        ))
    }

    pub fn append(&mut self, entry: &TranscriptEntry) -> Result<(), String> {
        entry.validate(self.policy)?;
        let mut nonce = [0; 12];
        rand::thread_rng().fill_bytes(&mut nonce);
        let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(&*self.generation_key));
        let plain = postcard::to_allocvec(entry).map_err(|error| error.to_string())?;
        let aad = associated_data(&self.daemon_identity_hash, self.generation);
        let ciphertext = cipher
            .encrypt(
                Nonce::from_slice(&nonce),
                Payload {
                    msg: &plain,
                    aad: &aad,
                },
            )
            .map_err(|_| "transcript encryption failed".to_string())?;
        let encoded = postcard::to_allocvec(&EncryptedRecord {
            generation: self.generation,
            salt: self.generation_salt,
            nonce,
            ciphertext,
        })
        .map_err(|error| error.to_string())?;
        if encoded.len() > MAX_RECORD_BYTES {
            return Err("transcript record exceeds limit".into());
        }
        let length = u32::try_from(encoded.len()).map_err(|_| "transcript record too large")?;
        self.file
            .write_all(&length.to_be_bytes())
            .and_then(|_| self.file.write_all(&encoded))
            .and_then(|_| self.file.sync_data())
            .map_err(|error| error.to_string())
    }

    pub fn rotate(&mut self) -> Result<u32, String> {
        self.generation = self
            .generation
            .checked_add(1)
            .ok_or("transcript generation exhausted")?;
        self.generation_salt = random_salt();
        self.generation_key = derive_key(&self.passphrase, &self.generation_salt)?;
        Ok(self.generation)
    }

    pub fn generation(&self) -> u32 {
        self.generation
    }
}

pub fn identity_hash(identity: &[u8]) -> [u8; 32] {
    Sha256::digest(identity).into()
}

fn decrypt_record(
    record: &EncryptedRecord,
    key: &[u8; 32],
    daemon_identity_hash: &[u8; 32],
) -> Result<TranscriptEntry, String> {
    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(key));
    let aad = associated_data(daemon_identity_hash, record.generation);
    let plain = cipher
        .decrypt(
            Nonce::from_slice(&record.nonce),
            Payload {
                msg: &record.ciphertext,
                aad: &aad,
            },
        )
        .map_err(|_| "wrong passphrase or corrupted transcript".to_string())?;
    let (entry, trailing) = postcard::take_from_bytes(&plain)
        .map_err(|error| format!("invalid transcript entry: {error}"))?;
    if !trailing.is_empty() {
        return Err("trailing bytes in transcript entry".into());
    }
    Ok(entry)
}

fn random_salt() -> [u8; 16] {
    let mut salt = [0; 16];
    rand::thread_rng().fill_bytes(&mut salt);
    salt
}

fn derive_key(passphrase: &str, salt: &[u8; 16]) -> Result<Zeroizing<[u8; 32]>, String> {
    let params = argon2::Params::new(ARGON_M_COST, ARGON_T_COST, ARGON_P_COST, Some(32))
        .map_err(|error| format!("argon2 params: {error}"))?;
    let argon = argon2::Argon2::new(argon2::Algorithm::Argon2id, argon2::Version::V0x13, params);
    let mut key = Zeroizing::new([0; 32]);
    argon
        .hash_password_into(passphrase.as_bytes(), salt, &mut *key)
        .map_err(|error| format!("argon2: {error}"))?;
    Ok(key)
}

fn associated_data(daemon_identity_hash: &[u8; 32], generation: u32) -> Vec<u8> {
    let mut aad = Vec::with_capacity(HEADER_LEN + 4);
    aad.extend_from_slice(MAGIC);
    aad.extend_from_slice(daemon_identity_hash);
    aad.extend_from_slice(&generation.to_be_bytes());
    aad
}

fn ensure_parent(path: &std::path::Path) -> Result<(), String> {
    let Some(parent) = path
        .parent()
        .filter(|parent| !parent.as_os_str().is_empty())
    else {
        return Ok(());
    };
    if !parent.exists() {
        std::fs::create_dir_all(parent).map_err(|error| error.to_string())?;
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            std::fs::set_permissions(parent, std::fs::Permissions::from_mode(0o700))
                .map_err(|error| error.to_string())?;
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn entry(shared_channel: bool) -> TranscriptEntry {
        TranscriptEntry {
            peer_identity_hash: identity_hash(b"peer identity"),
            channel: shared_channel.then(|| "ops".into()),
            pseudonym: shared_channel.then(|| "ghost-7".into()),
            shared_channel,
            content_type: "application/vnd.ghost.command-center+json".into(),
            body: br#"{"status":"ok"}"#.to_vec(),
            delivery_state: DeliveryState::Delivered,
            timestamps: TranscriptTimestamps {
                created_unix: 10,
                received_unix: Some(11),
                delivered_unix: Some(12),
            },
            validation: ValidationResult::Valid,
        }
    }

    #[test]
    fn append_rotation_and_identity_binding_roundtrip() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("command-center.gcctx");
        let identity = identity_hash(b"daemon identity");
        let mut transcript =
            ApplicationTranscript::create(&path, "passphrase", identity, TranscriptPolicy::Lab)
                .unwrap();
        transcript.append(&entry(true)).unwrap();
        assert!(!entry(true).authorizes_commands());
        assert_eq!(transcript.rotate().unwrap(), 1);
        let mut second = entry(false);
        second.channel = None;
        second.pseudonym = None;
        second.body = b"direct".to_vec();
        transcript.append(&second).unwrap();
        drop(transcript);

        let (transcript, loaded) =
            ApplicationTranscript::open(&path, "passphrase", identity, TranscriptPolicy::Lab)
                .unwrap();
        assert_eq!(transcript.generation(), 1);
        assert_eq!(loaded, vec![entry(true), second]);
        drop(transcript);
        assert!(ApplicationTranscript::open(
            &path,
            "passphrase",
            identity_hash(b"other daemon"),
            TranscriptPolicy::Lab,
        )
        .is_err());
    }

    #[test]
    fn tamper_and_shared_channel_policy_are_rejected() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("command-center.gcctx");
        let identity = identity_hash(b"daemon identity");
        let mut transcript = ApplicationTranscript::create(
            &path,
            "passphrase",
            identity,
            TranscriptPolicy::Standard,
        )
        .unwrap();
        assert!(transcript.append(&entry(true)).is_err());
        let mut direct = entry(false);
        direct.channel = None;
        direct.pseudonym = None;
        transcript.append(&direct).unwrap();
        assert!(!direct.authorizes_commands());
        assert!(!direct.validation.authorizes_commands());
        drop(transcript);

        let mut raw = std::fs::read(&path).unwrap();
        let last = raw.len() - 1;
        raw[last] ^= 1;
        std::fs::write(&path, raw).unwrap();
        assert!(ApplicationTranscript::open(
            &path,
            "passphrase",
            identity,
            TranscriptPolicy::Standard,
        )
        .is_err());
    }
}
