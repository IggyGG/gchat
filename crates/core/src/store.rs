//! Encrypted-at-rest client store.
//!
//! One file per profile, whole-file AEAD:
//!
//! ```text
//! magic "GCCST2" | argon2id m/t/p (3×u32 BE) | salt 16 | nonce 12 | ciphertext
//! ```
//!
//! key = argon2id(passphrase, salt, m=64 MiB, t=3, p=1), AES-256-GCM over
//! postcard-serialized [`StoreData`], fresh random nonce per save.
//! Writes are atomic (tmp file + rename).

use crate::contact::ContactBook;
use crate::conversation::Conversations;
use crate::model::{CachedDescriptor, ChannelRecord, LegacyArchive, ScopedPmRecord};
use fs2::FileExt;
use rand::RngCore;
use serde::de::DeserializeOwned;
use serde::{Deserialize, Serialize};
use std::io::Write;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;
use zeroize::Zeroizing;

mod diagnostics;
pub use diagnostics::StoreSaveDiagnostics;
use diagnostics::{elapsed_us, SaveCounters};

const MAGIC: &[u8; 6] = b"GCCST2";
const ARCHIVE_MAGIC: &[u8; 6] = b"GCCAR2";
const LEGACY_MAGIC: &[u8; 6] = b"GCCST1";
const LEGACY_ARCHIVE_MAGIC: &[u8; 6] = b"GCCAR1";
const PROTOCOL_MAGIC: &[u8; 6] = b"GCPRT1";
const ARGON_M_COST: u32 = 64 * 1024; // KiB
const ARGON_T_COST: u32 = 3;
const ARGON_P_COST: u32 = 1;
const HEADER_LEN: usize = 6 + 12 + 16 + 12;

#[derive(Serialize, Deserialize)]
pub struct StoreData {
    pub identity_seed: [u8; 32],
    pub archive: ArchiveData,
    /// gc-node state export blob (key material; encrypted here at rest).
    pub node_state: Option<Vec<u8>>,
}

#[derive(Clone, Default, Serialize, Deserialize)]
pub struct ArchiveData {
    /// Bounded ACK race buffer: an ACK may arrive before the send call returns.
    #[serde(skip)]
    pub delivery_receipts: Vec<([u8; 32], [u8; 16])>,
    pub daemon_safety_number: String,
    pub channels: Vec<ChannelRecord>,
    pub scoped_pms: Vec<ScopedPmRecord>,
    pub public_descriptors: Vec<CachedDescriptor>,
    pub legacy: LegacyArchive,
}

#[derive(Serialize, Deserialize)]
struct LegacyStoreData {
    identity_seed: [u8; 32],
    contacts: ContactBook,
    conversations: Conversations,
    node_state: Option<Vec<u8>>,
}

#[derive(Serialize, Deserialize)]
struct LegacyArchiveData {
    daemon_safety_number: String,
    contacts: ContactBook,
    conversations: Conversations,
}

#[derive(Serialize, Deserialize)]
pub struct ProtocolData {
    pub identity_seed: [u8; 32],
    pub node_state: Option<Vec<u8>>,
}

impl StoreData {
    pub fn new(identity_seed: [u8; 32]) -> Self {
        StoreData {
            identity_seed,
            archive: ArchiveData::default(),
            node_state: None,
        }
    }
}

fn derive_key(passphrase: &str, salt: &[u8; 16]) -> Result<Zeroizing<[u8; 32]>, String> {
    let params = argon2::Params::new(ARGON_M_COST, ARGON_T_COST, ARGON_P_COST, Some(32))
        .map_err(|e| format!("argon2 params: {e}"))?;
    let argon = argon2::Argon2::new(argon2::Algorithm::Argon2id, argon2::Version::V0x13, params);
    let mut out = Zeroizing::new([0u8; 32]);
    argon
        .hash_password_into(passphrase.as_bytes(), salt, &mut *out)
        .map_err(|e| format!("argon2: {e}"))?;
    Ok(out)
}

fn parse_header(raw: &[u8], magic: &[u8; 6]) -> Result<([u8; 16], [u8; 12]), String> {
    if raw.len() < HEADER_LEN + 16 || &raw[..6] != magic {
        return Err("not a gc client store".into());
    }
    let m = u32::from_be_bytes(raw[6..10].try_into().unwrap());
    let t = u32::from_be_bytes(raw[10..14].try_into().unwrap());
    let p = u32::from_be_bytes(raw[14..18].try_into().unwrap());
    // Refuse KDF params that differ from client policy: a tampered header
    // must not weaken (or DoS) the unlock.
    if m != ARGON_M_COST || t != ARGON_T_COST || p != ARGON_P_COST {
        return Err("store KDF params differ from client policy".into());
    }
    let mut salt = [0u8; 16];
    salt.copy_from_slice(&raw[18..34]);
    let mut nonce = [0u8; 12];
    nonce.copy_from_slice(&raw[34..46]);
    Ok((salt, nonce))
}

struct EncryptedStore {
    path: std::path::PathBuf,
    magic: &'static [u8; 6],
    salt: [u8; 16],
    key: Zeroizing<[u8; 32]>,
    initialized: AtomicBool,
    save_lock: Mutex<()>,
    save_counters: SaveCounters,
    _profile_lock: std::fs::File,
}

impl EncryptedStore {
    fn create(
        path: &std::path::Path,
        passphrase: &str,
        magic: &'static [u8; 6],
        label: &str,
    ) -> Result<Self, String> {
        ensure_parent(path)?;
        let profile_lock = acquire_lock(path)?;
        if std::fs::symlink_metadata(path).is_ok() {
            return Err(format!("{label} exists: {}", path.display()));
        }
        let mut salt = [0u8; 16];
        rand::thread_rng().fill_bytes(&mut salt);
        Ok(Self {
            path: path.to_path_buf(),
            magic,
            salt,
            key: derive_key(passphrase, &salt)?,
            initialized: AtomicBool::new(false),
            save_lock: Mutex::new(()),
            save_counters: SaveCounters::default(),
            _profile_lock: profile_lock,
        })
    }

    fn open<T: DeserializeOwned>(
        path: &std::path::Path,
        passphrase: &str,
        magic: &'static [u8; 6],
        corruption: &str,
    ) -> Result<(Self, T), String> {
        use aes_gcm::aead::Aead;
        use aes_gcm::{Aes256Gcm, Key, KeyInit, Nonce};

        ensure_parent(path)?;
        crate::private_fs::validate_private_file(path, "encrypted store")?;
        let profile_lock = acquire_lock(path)?;
        let raw = std::fs::read(path).map_err(|error| error.to_string())?;
        let (salt, nonce) = parse_header(&raw, magic)?;
        let key = derive_key(passphrase, &salt)?;
        let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(&*key));
        let plain = cipher
            .decrypt(Nonce::from_slice(&nonce), &raw[HEADER_LEN..])
            .map_err(|_| corruption.to_string())?;
        let (data, trailing) =
            postcard::take_from_bytes(&plain).map_err(|error| format!("deserialize: {error}"))?;
        if !trailing.is_empty() {
            return Err("trailing bytes in encrypted store".into());
        }
        Ok((
            Self {
                path: path.to_path_buf(),
                magic,
                salt,
                key,
                initialized: AtomicBool::new(true),
                save_lock: Mutex::new(()),
                save_counters: SaveCounters::default(),
                _profile_lock: profile_lock,
            },
            data,
        ))
    }

    fn open_legacy<T: DeserializeOwned>(
        path: &std::path::Path,
        passphrase: &str,
        legacy_magic: &'static [u8; 6],
        new_magic: &'static [u8; 6],
        corruption: &str,
    ) -> Result<(Self, T), String> {
        let (legacy, data) = Self::open(path, passphrase, legacy_magic, corruption)?;
        Ok((
            Self {
                magic: new_magic,
                ..legacy
            },
            data,
        ))
    }

    fn save<T: Serialize>(&self, data: &T) -> Result<(), String> {
        use aes_gcm::aead::Aead;
        use aes_gcm::{Aes256Gcm, Key, KeyInit, Nonce};

        let started = std::time::Instant::now();
        self.save_counters.begin();
        let mut sample = StoreSaveDiagnostics::default();
        let result = (|| {
            let _save = self.save_lock.lock().map_err(|_| "store lock poisoned")?;
            sample.lock_wait_us = elapsed_us(started);
            let serialize_started = std::time::Instant::now();
            let plain = postcard::to_allocvec(data);
            sample.serialize_us = elapsed_us(serialize_started);
            let plain = plain.map_err(|error| format!("serialize: {error}"))?;
            sample.serialized_bytes = plain.len() as u64;
            let encrypt_started = std::time::Instant::now();
            let mut nonce = [0u8; 12];
            rand::thread_rng().fill_bytes(&mut nonce);
            let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(&*self.key));
            let ciphertext = cipher.encrypt(Nonce::from_slice(&nonce), plain.as_slice());
            sample.encrypt_us = elapsed_us(encrypt_started);
            let ciphertext = ciphertext.map_err(|_| "encrypt failed".to_string())?;
            let mut output = Vec::with_capacity(HEADER_LEN + ciphertext.len());
            output.extend_from_slice(self.magic);
            output.extend_from_slice(&ARGON_M_COST.to_be_bytes());
            output.extend_from_slice(&ARGON_T_COST.to_be_bytes());
            output.extend_from_slice(&ARGON_P_COST.to_be_bytes());
            output.extend_from_slice(&self.salt);
            output.extend_from_slice(&nonce);
            output.extend_from_slice(&ciphertext);
            sample.write_attempted_bytes = output.len() as u64;
            let write_started = std::time::Instant::now();
            let written = atomic_write(
                &self.path,
                &output,
                !self.initialized.load(Ordering::Acquire),
            );
            sample.atomic_write_us = elapsed_us(write_started);
            written?;
            self.initialized.store(true, Ordering::Release);
            Ok(())
        })();
        self.save_counters.finish(&sample, started, result.is_ok());
        result
    }
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

pub(crate) fn acquire_lock(path: &std::path::Path) -> Result<std::fs::File, String> {
    let mut lock_name = path.as_os_str().to_os_string();
    lock_name.push(".lock");
    let mut options = std::fs::OpenOptions::new();
    options.read(true).write(true).create(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.mode(0o600);
    }
    let lock = options
        .open(std::path::PathBuf::from(lock_name))
        .map_err(|error| error.to_string())?;
    lock.try_lock_exclusive()
        .map_err(|_| format!("profile is already in use: {}", path.display()))?;
    Ok(lock)
}

pub(crate) fn atomic_write(
    path: &std::path::Path,
    bytes: &[u8],
    no_clobber: bool,
) -> Result<(), String> {
    let parent = path
        .parent()
        .filter(|parent| !parent.as_os_str().is_empty())
        .unwrap_or_else(|| std::path::Path::new("."));
    let prefix = format!(
        ".{}.",
        path.file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("gcstore")
    );
    let mut temporary = tempfile::Builder::new()
        .prefix(&prefix)
        .tempfile_in(parent)
        .map_err(|error| error.to_string())?;
    // Fix ownership and ACLs before publication, including elevated Windows
    // accounts whose default file owner is the Administrators group.
    crate::private_fs::make_private(temporary.path(), false)?;
    temporary
        .write_all(bytes)
        .and_then(|_| temporary.as_file().sync_all())
        .map_err(|error| error.to_string())?;
    if no_clobber {
        temporary
            .persist_noclobber(path)
            .map_err(|error| error.error.to_string())?;
    } else {
        temporary
            .persist(path)
            .map_err(|error| error.error.to_string())?;
    }
    #[cfg(unix)]
    std::fs::File::open(parent)
        .and_then(|directory| directory.sync_all())
        .map_err(|error| error.to_string())?;
    Ok(())
}

pub struct Store(EncryptedStore);

impl Store {
    pub(crate) fn path(&self) -> &std::path::Path {
        &self.0.path
    }
    pub(crate) fn verify_secret(&self, secret: &str) -> Result<(), String> {
        use hmac::{Hmac, Mac};
        let key = derive_key(secret, &self.0.salt)?;
        let mut expected =
            Hmac::<sha2::Sha256>::new_from_slice(&*self.0.key).map_err(|e| e.to_string())?;
        expected.update(b"gchat.profile.unlock");
        let mut supplied =
            Hmac::<sha2::Sha256>::new_from_slice(&*key).map_err(|e| e.to_string())?;
        supplied.update(b"gchat.profile.unlock");
        supplied
            .verify_slice(&expected.finalize().into_bytes())
            .map_err(|_| "wrong passphrase".into())
    }

    pub(crate) fn network_directory(&self) -> std::path::PathBuf {
        self.0.path.with_extension("network")
    }

    pub fn create(path: &std::path::Path, passphrase: &str) -> Result<(Self, StoreData), String> {
        let store = Self(EncryptedStore::create(path, passphrase, MAGIC, "store")?);
        let mut seed = [0u8; 32];
        rand::thread_rng().fill_bytes(&mut seed);
        let data = StoreData::new(seed);
        store.save(&data)?;
        Ok((store, data))
    }

    pub fn open(path: &std::path::Path, passphrase: &str) -> Result<(Self, StoreData), String> {
        let magic = read_magic(path)?;
        if magic == *LEGACY_MAGIC {
            let (store, legacy): (_, LegacyStoreData) = EncryptedStore::open_legacy(
                path,
                passphrase,
                LEGACY_MAGIC,
                MAGIC,
                "wrong passphrase or corrupted store",
            )?;
            let data = StoreData {
                identity_seed: legacy.identity_seed,
                archive: ArchiveData {
                    legacy: LegacyArchive {
                        contacts: legacy.contacts,
                        conversations: legacy.conversations,
                    },
                    ..ArchiveData::default()
                },
                node_state: legacy.node_state,
            };
            store.save(&data)?;
            return Ok((Self(store), data));
        }
        let (store, data) = EncryptedStore::open(
            path,
            passphrase,
            MAGIC,
            "wrong passphrase or corrupted store",
        )?;
        Ok((Self(store), data))
    }

    pub fn save(&self, data: &StoreData) -> Result<(), String> {
        self.0.save(data)
    }
}

pub struct ArchiveStore(EncryptedStore);

/// Versioned application state beside the unchanged protocol/chat archives.
/// JSON inside the existing AEAD container permits additive state fields.
pub struct ChatServiceStore(EncryptedStore);

impl ChatServiceStore {
    pub fn verify_passphrase(&self, passphrase: &str) -> Result<(), String> {
        use hmac::Mac;
        type Check = hmac::Hmac<sha2::Sha256>;
        let candidate = derive_key(passphrase, &self.0.salt)?;
        let mut expected = Check::new_from_slice(&*self.0.key).map_err(|_| "archive key")?;
        expected.update(b"gchat-service-unlock-v1");
        let mut actual = Check::new_from_slice(&*candidate).map_err(|_| "archive key")?;
        actual.update(b"gchat-service-unlock-v1");
        actual
            .verify_slice(&expected.finalize().into_bytes())
            .map_err(|_| "wrong archive passphrase".into())
    }

    pub fn open_or_create<T: Serialize + DeserializeOwned + Default>(
        path: &std::path::Path,
        passphrase: &str,
    ) -> Result<(Self, T), String> {
        const MAGIC: &[u8; 6] = b"GCCUI1";
        if path.exists() {
            let (store, bytes): (_, Vec<u8>) = EncryptedStore::open(
                path,
                passphrase,
                MAGIC,
                "wrong passphrase or corrupted chat service state",
            )?;
            let state = serde_json::from_slice(&bytes).map_err(|e| e.to_string())?;
            Ok((Self(store), state))
        } else {
            let store = Self(EncryptedStore::create(
                path,
                passphrase,
                MAGIC,
                "chat service state",
            )?);
            let state = T::default();
            store.save(&state)?;
            Ok((store, state))
        }
    }

    pub fn save<T: Serialize>(&self, state: &T) -> Result<(), String> {
        let bytes = serde_json::to_vec(state).map_err(|e| e.to_string())?;
        if bytes.len() > 16 * 1024 * 1024 {
            return Err("chat service state exceeds its bound".into());
        }
        self.0.save(&bytes)
    }
}

impl ArchiveStore {
    pub fn create(
        path: &std::path::Path,
        passphrase: &str,
        daemon_safety_number: String,
    ) -> Result<(Self, ArchiveData), String> {
        let store = Self(EncryptedStore::create(
            path,
            passphrase,
            ARCHIVE_MAGIC,
            "archive",
        )?);
        let data = ArchiveData {
            daemon_safety_number,
            ..ArchiveData::default()
        };
        store.save(&data)?;
        Ok((store, data))
    }

    pub fn open(path: &std::path::Path, passphrase: &str) -> Result<(Self, ArchiveData), String> {
        let magic = read_magic(path)?;
        if magic == *LEGACY_ARCHIVE_MAGIC {
            let (store, legacy): (_, LegacyArchiveData) = EncryptedStore::open_legacy(
                path,
                passphrase,
                LEGACY_ARCHIVE_MAGIC,
                ARCHIVE_MAGIC,
                "wrong passphrase or corrupted archive",
            )?;
            let data = ArchiveData {
                daemon_safety_number: legacy.daemon_safety_number,
                legacy: LegacyArchive {
                    contacts: legacy.contacts,
                    conversations: legacy.conversations,
                },
                ..ArchiveData::default()
            };
            store.save(&data)?;
            return Ok((Self(store), data));
        }
        let (store, data) = EncryptedStore::open(
            path,
            passphrase,
            ARCHIVE_MAGIC,
            "wrong passphrase or corrupted archive",
        )?;
        Ok((Self(store), data))
    }

    pub fn save(&self, data: &ArchiveData) -> Result<(), String> {
        self.0.save(data)
    }
}

/// Which of the three encrypted file types a path holds.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum StoreKind {
    /// Legacy combined identity + archive (`gchat --store`).
    Combined,
    /// Chat archive pinned to a daemon or hosted-runtime identity.
    Archive,
    /// Protocol profile (identity + node state) used by runtimes.
    Protocol,
}

/// Sniff the magic without unlocking. Errors for missing or foreign files.
pub fn store_kind(path: &std::path::Path) -> Result<StoreKind, String> {
    let magic = read_magic(path)?;
    if magic == *MAGIC || magic == *LEGACY_MAGIC {
        Ok(StoreKind::Combined)
    } else if magic == *ARCHIVE_MAGIC || magic == *LEGACY_ARCHIVE_MAGIC {
        Ok(StoreKind::Archive)
    } else if magic == *PROTOCOL_MAGIC {
        Ok(StoreKind::Protocol)
    } else {
        Err("not a gc client store".into())
    }
}

fn read_magic(path: &std::path::Path) -> Result<[u8; 6], String> {
    use std::io::Read;
    let mut file = std::fs::File::open(path).map_err(|error| error.to_string())?;
    let mut magic = [0; 6];
    file.read_exact(&mut magic)
        .map_err(|_| "not a gc client store".to_string())?;
    Ok(magic)
}

pub struct ProtocolStore(EncryptedStore);

/// Split a stopped legacy profile into a new instance directory. The original
/// encrypted file is held locked and retained byte-for-byte for recovery.
pub fn migrate_combined(
    source: &std::path::Path,
    destination: &std::path::Path,
    passphrase: &str,
) -> Result<(), String> {
    if std::fs::symlink_metadata(destination).is_ok() {
        return Err("migration destination already exists".into());
    }
    crate::private_fs::validate_private_file(source, "migration source")?;
    crate::private_fs::validate_private_parent(source, "migration source")?;
    let _source_lock = acquire_lock(source)?;
    if store_kind(source)? != StoreKind::Combined {
        return Err("migration requires a combined profile".into());
    }
    let parent = destination
        .parent()
        .ok_or("migration destination needs a parent")?;
    let stage = tempfile::Builder::new()
        .prefix(".gchat-migration-")
        .tempdir_in(parent)
        .map_err(|e| e.to_string())?;
    crate::private_fs::make_private(stage.path(), true)?;
    let copy = stage.path().join("legacy.gcstore");
    std::fs::copy(source, &copy).map_err(|e| e.to_string())?;
    crate::private_fs::make_private(&copy, false)?;
    let (old, mut data) = Store::open(&copy, passphrase)?;
    let protocol_path = stage.path().join("profile.gcprotocol");
    let protocol = ProtocolStore(EncryptedStore::create(
        &protocol_path,
        passphrase,
        PROTOCOL_MAGIC,
        "migrated protocol profile",
    )?);
    protocol.save(&ProtocolData {
        identity_seed: data.identity_seed,
        node_state: data.node_state.take(),
    })?;
    let safety = gcoms_crypto::safety_number_of(
        &gcoms_crypto::IdentityKeypair::from_seed(data.identity_seed).public_bytes(),
    );
    if !data.archive.daemon_safety_number.is_empty() && data.archive.daemon_safety_number != safety
    {
        return Err("legacy archive identity does not match its profile".into());
    }
    data.archive.daemon_safety_number = safety.clone();
    let (archive, _) =
        ArchiveStore::create(&stage.path().join("chat.gcarchive"), passphrase, safety)?;
    archive.save(&data.archive)?;
    data.identity_seed.fill(0);
    drop(archive);
    drop(protocol);
    drop(old);
    // Retain the exact original encrypted bytes, even if opening the temporary
    // working copy upgraded an old archive representation.
    std::fs::copy(source, &copy).map_err(|e| e.to_string())?;
    // Windows requires a writable handle for FlushFileBuffers. The restored
    // bytes must reach disk before publishing the new profile directory.
    std::fs::OpenOptions::new()
        .write(true)
        .open(&copy)
        .and_then(|f| f.sync_all())
        .map_err(|e| e.to_string())?;
    if std::fs::symlink_metadata(destination).is_ok() {
        return Err("migration destination appeared during conversion".into());
    }
    std::fs::rename(stage.path(), destination).map_err(|e| e.to_string())?;
    #[cfg(unix)]
    std::fs::File::open(parent)
        .and_then(|f| f.sync_all())
        .map_err(|e| e.to_string())?;
    Ok(())
}

impl ProtocolStore {
    pub fn create(
        path: &std::path::Path,
        passphrase: &str,
    ) -> Result<(Self, ProtocolData), String> {
        let store = Self(EncryptedStore::create(
            path,
            passphrase,
            PROTOCOL_MAGIC,
            "protocol profile",
        )?);
        let mut identity_seed = [0; 32];
        rand::thread_rng().fill_bytes(&mut identity_seed);
        let data = ProtocolData {
            identity_seed,
            node_state: None,
        };
        store.save(&data)?;
        Ok((store, data))
    }

    pub fn open(path: &std::path::Path, passphrase: &str) -> Result<(Self, ProtocolData), String> {
        let (store, data) = EncryptedStore::open(
            path,
            passphrase,
            PROTOCOL_MAGIC,
            "wrong passphrase or corrupted protocol profile",
        )?;
        Ok((Self(store), data))
    }

    /// Read a consistent encrypted snapshot without creating a profile/lock or
    /// changing the live writer. Saves use atomic replacement; identity is stable.
    /// Return only the public key, never the seed or protocol state.
    pub fn inspect_identity_public_key(
        path: &std::path::Path,
        passphrase: &str,
    ) -> Result<Vec<u8>, String> {
        use aes_gcm::aead::Aead;
        use aes_gcm::{Aes256Gcm, Key, KeyInit, Nonce};
        crate::private_fs::validate_private_file(path, "encrypted profile")?;
        crate::private_fs::validate_private_parent(path, "encrypted profile")?;
        let raw = std::fs::read(path).map_err(|_| "read encrypted profile")?;
        let (salt, nonce) = parse_header(&raw, PROTOCOL_MAGIC)?;
        let key = derive_key(passphrase, &salt)?;
        let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(&*key));
        let plain = Zeroizing::new(
            cipher
                .decrypt(Nonce::from_slice(&nonce), &raw[HEADER_LEN..])
                .map_err(|_| "profile decryption refused")?,
        );
        let (mut data, trailing): (ProtocolData, _) =
            postcard::take_from_bytes(&plain).map_err(|_| "invalid encrypted profile")?;
        if !trailing.is_empty() {
            return Err("trailing encrypted profile data".into());
        }
        let public = gcoms_crypto::IdentityKeypair::from_seed(data.identity_seed).public_bytes();
        zeroize::Zeroize::zeroize(&mut data.identity_seed);
        Ok(public)
    }

    pub fn save(&self, data: &ProtocolData) -> Result<(), String> {
        self.0.save(data)
    }

    /// Aggregate costs since this process opened the profile; no profile contents.
    pub fn save_diagnostics(&self) -> StoreSaveDiagnostics {
        self.0.save_counters.snapshot()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn profile_save_counts_only_successful_replacements_as_committed() {
        let dir = tempfile::tempdir().unwrap();
        crate::private_fs::make_private(dir.path(), true).unwrap();
        let path = dir.path().join("protocol");
        let (store, mut data) = ProtocolStore::create(&path, "test-passphrase").unwrap();
        let initial = store.save_diagnostics();
        assert_eq!(initial.completed, 1);
        assert_eq!(
            initial.committed_bytes,
            std::fs::metadata(&path).unwrap().len()
        );
        let retained = dir.path().join("retained");
        std::fs::rename(&path, &retained).unwrap();
        std::fs::create_dir(&path).unwrap();
        data.node_state = Some(vec![7; 1024 * 1024]);
        assert!(store.save(&data).is_err());
        let failed = store.save_diagnostics();
        assert_eq!(failed.attempts, 2);
        assert_eq!(failed.failed, 1);
        assert_eq!(failed.completed, 1);
        assert_eq!(failed.committed_bytes, initial.committed_bytes);
        assert!(failed.write_attempted_bytes > initial.committed_bytes + 1024 * 1024);
        std::fs::remove_dir(&path).unwrap();
        std::fs::rename(retained, &path).unwrap();
        store.save(&data).unwrap();
        let succeeded = store.save_diagnostics();
        assert_eq!(succeeded.attempts, 3);
        assert_eq!(succeeded.completed, 2);
        assert_eq!(succeeded.failed, 1);
        assert_eq!(
            succeeded.committed_bytes - initial.committed_bytes,
            std::fs::metadata(&path).unwrap().len()
        );
        assert!(succeeded.total_us >= succeeded.atomic_write_us);
        drop(store);
        let (_, reopened) = ProtocolStore::open(&path, "test-passphrase").unwrap();
        assert_eq!(reopened.node_state, data.node_state);
    }

    fn tmpdir(tag: &str) -> std::path::PathBuf {
        let dir = std::env::temp_dir().join(format!("gcstore-{tag}-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        dir
    }

    #[test]
    fn create_open_roundtrip() {
        let dir = tmpdir("rt");
        let path = dir.join("profile.gcstore");
        let (initial_store, mut data) = Store::create(&path, "pass phrase").unwrap();
        let seed = data.identity_seed;
        data.node_state = Some(vec![1, 2, 3]);
        drop(initial_store);
        let (store, _) = Store::open(&path, "pass phrase").unwrap();
        store.save(&data).unwrap();
        drop(store);
        let (_s2, loaded) = Store::open(&path, "pass phrase").unwrap();
        assert_eq!(loaded.identity_seed, seed);
        assert_eq!(loaded.node_state, Some(vec![1, 2, 3]));
        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn store_kind_detects_all_magics() {
        let dir = tmpdir("kind");
        let combined = dir.join("combined.gcstore");
        let archive = dir.join("chat.gcarchive");
        let protocol = dir.join("profile.gcprotocol");
        let junk = dir.join("junk");
        let _combined = Store::create(&combined, "pw").unwrap();
        let _archive = ArchiveStore::create(&archive, "pw", "safety".into()).unwrap();
        let _protocol = ProtocolStore::create(&protocol, "pw").unwrap();
        std::fs::write(&junk, b"hello world").unwrap();
        assert_eq!(store_kind(&combined).unwrap(), StoreKind::Combined);
        assert_eq!(store_kind(&archive).unwrap(), StoreKind::Archive);
        assert_eq!(store_kind(&protocol).unwrap(), StoreKind::Protocol);
        assert!(store_kind(&junk).is_err());
        assert!(store_kind(&dir.join("missing")).is_err());
        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn create_makes_missing_parent_directories() {
        let dir = tmpdir("parents");
        let path = dir.join("nested/profile.gcstore");
        Store::create(&path, "pass phrase").unwrap();
        assert!(path.is_file());
        std::fs::remove_dir_all(dir).ok();
    }

    #[test]
    fn wrong_passphrase_rejected() {
        let dir = tmpdir("wp");
        let path = dir.join("profile.gcstore");
        let _ = Store::create(&path, "right").unwrap();
        assert!(Store::open(&path, "wrong").is_err());
        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn corrupted_store_rejected() {
        let dir = tmpdir("cor");
        let path = dir.join("profile.gcstore");
        let _ = Store::create(&path, "pw").unwrap();
        let mut raw = std::fs::read(&path).unwrap();
        let last = raw.len() - 1;
        raw[last] ^= 1;
        std::fs::write(&path, raw).unwrap();
        assert!(Store::open(&path, "pw").is_err());
        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn create_refuses_clobber() {
        let dir = tmpdir("clob");
        let path = dir.join("profile.gcstore");
        let _ = Store::create(&path, "pw").unwrap();
        assert!(Store::create(&path, "pw").is_err());
        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn archive_is_distinct_and_roundtrips() {
        let dir = tmpdir("archive");
        let path = dir.join("chat.gcarchive");
        let identity = "safety-number".to_string();
        let (store, mut data) = ArchiveStore::create(&path, "pw", identity.clone()).unwrap();
        data.legacy.contacts.contacts.push(crate::contact::Contact {
            name: "peer".into(),
            card: "card".into(),
            safety_number: "safety".into(),
            verified: false,
        });
        store.save(&data).unwrap();
        drop(store);
        let (_, loaded) = ArchiveStore::open(&path, "pw").unwrap();
        assert_eq!(loaded.daemon_safety_number, identity);
        assert_eq!(loaded.legacy.contacts.contacts[0].name, "peer");
        assert!(Store::open(&path, "pw").is_err());
        std::fs::remove_dir_all(dir).ok();
    }

    #[test]
    fn legacy_store_and_archive_migrate_into_nested_legacy_data() {
        let dir = tmpdir("legacy-migration");
        let store_path = dir.join("profile.gcstore");
        let archive_path = dir.join("chat.gcarchive");
        let contact = crate::contact::Contact {
            name: "peer".into(),
            card: "card".into(),
            safety_number: "safety".into(),
            verified: true,
        };
        let contacts = ContactBook {
            contacts: vec![contact],
        };
        let mut conversations = Conversations::default();
        conversations.direct("peer");

        let old_store = EncryptedStore::create(&store_path, "pw", LEGACY_MAGIC, "store").unwrap();
        old_store
            .save(&LegacyStoreData {
                identity_seed: [7; 32],
                contacts: contacts.clone(),
                conversations: conversations.clone(),
                node_state: Some(vec![1, 2, 3]),
            })
            .unwrap();
        drop(old_store);

        let (store, migrated) = Store::open(&store_path, "pw").unwrap();
        assert_eq!(migrated.identity_seed, [7; 32]);
        assert_eq!(migrated.archive.legacy.contacts.contacts[0].name, "peer");
        assert_eq!(migrated.archive.legacy.conversations.list.len(), 1);
        assert!(migrated.archive.channels.is_empty());
        assert_eq!(read_magic(&store_path).unwrap(), *MAGIC);
        drop(store);

        let old_archive =
            EncryptedStore::create(&archive_path, "pw", LEGACY_ARCHIVE_MAGIC, "archive").unwrap();
        old_archive
            .save(&LegacyArchiveData {
                daemon_safety_number: "daemon".into(),
                contacts,
                conversations,
            })
            .unwrap();
        drop(old_archive);

        let (archive, migrated) = ArchiveStore::open(&archive_path, "pw").unwrap();
        assert_eq!(migrated.daemon_safety_number, "daemon");
        assert_eq!(migrated.legacy.contacts.contacts[0].name, "peer");
        assert_eq!(migrated.legacy.conversations.list.len(), 1);
        assert!(migrated.scoped_pms.is_empty());
        assert_eq!(read_magic(&archive_path).unwrap(), *ARCHIVE_MAGIC);
        drop(archive);

        std::fs::remove_dir_all(dir).ok();
    }

    #[test]
    fn protocol_profile_contains_no_chat_archive() {
        let dir = tmpdir("protocol");
        let path = dir.join("profile.gcprotocol");
        let (store, mut data) = ProtocolStore::create(&path, "pw").unwrap();
        data.node_state = Some(vec![4, 5, 6]);
        store.save(&data).unwrap();
        drop(store);
        let (_, loaded) = ProtocolStore::open(&path, "pw").unwrap();
        assert_eq!(loaded.node_state, Some(vec![4, 5, 6]));
        assert!(ArchiveStore::open(&path, "pw").is_err());
        assert!(Store::open(&path, "pw").is_err());
        std::fs::remove_dir_all(dir).ok();
    }

    #[test]
    fn profile_lock_rejects_a_second_writer() {
        let dir = tmpdir("lock");
        let path = dir.join("profile.gcstore");
        let (_store, _) = Store::create(&path, "pw").unwrap();
        assert!(Store::open(&path, "pw").is_err());
        std::fs::remove_dir_all(dir).ok();
    }

    #[cfg(unix)]
    #[test]
    fn new_store_and_parent_are_private() {
        use std::os::unix::fs::PermissionsExt;

        let dir = tmpdir("permissions");
        let parent = dir.join("private");
        let path = parent.join("profile.gcstore");
        Store::create(&path, "pw").unwrap();
        assert_eq!(
            std::fs::metadata(&parent).unwrap().permissions().mode() & 0o777,
            0o700
        );
        assert_eq!(
            std::fs::metadata(&path).unwrap().permissions().mode() & 0o777,
            0o600
        );
        std::fs::remove_dir_all(dir).ok();
    }
}
