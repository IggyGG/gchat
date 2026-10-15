//! Owner-local startup association. This is a host recipe, never an unlock grant.
use super::{fleet, host::InstanceConfig, instance_metadata};
use crate::private_fs;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    io::Read,
    net::SocketAddr,
    path::{Path, PathBuf},
};

const LIMIT: u64 = 32 * 1024;
pub(super) const CAPABILITY: &str = "gchat.host.v1:";

/// UTF-8 paths stay readable. Native paths are retained losslessly on their OS.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged, deny_unknown_fields)]
enum LocalPath {
    Text(String),
    Unix { unix: Vec<u8> },
    Windows { windows: Vec<u16> },
}
impl LocalPath {
    fn new(path: &Path) -> Result<Self, String> {
        let path = std::path::absolute(path).map_err(|e| e.to_string())?;
        if path
            .components()
            .any(|p| matches!(p, std::path::Component::ParentDir))
        {
            return Err("Host paths must not contain parent traversal".into());
        }
        if let Some(text) = path.to_str() {
            return Ok(Self::Text(text.into()));
        }
        #[cfg(unix)]
        {
            use std::os::unix::ffi::OsStrExt;
            Ok(Self::Unix {
                unix: path.as_os_str().as_bytes().to_vec(),
            })
        }
        #[cfg(windows)]
        {
            use std::os::windows::ffi::OsStrExt;
            Ok(Self::Windows {
                windows: path.as_os_str().encode_wide().collect(),
            })
        }
        #[cfg(not(any(unix, windows)))]
        Err("Unsupported native host path".into())
    }
    fn path(&self) -> Result<PathBuf, String> {
        let path = match self {
            Self::Text(text) if !text.contains('\0') => PathBuf::from(text),
            #[cfg(unix)]
            Self::Unix { unix } if !unix.contains(&0) => {
                use std::os::unix::ffi::OsStringExt;
                std::ffi::OsString::from_vec(unix.clone()).into()
            }
            #[cfg(windows)]
            Self::Windows { windows } if !windows.contains(&0) => {
                use std::os::windows::ffi::OsStringExt;
                std::ffi::OsString::from_wide(windows).into()
            }
            _ => return Err("Host registration has an unsupported native path".into()),
        };
        if !path.is_absolute() || Self::new(&path)? != *self {
            return Err("Host registration paths must be absolute without parent traversal".into());
        }
        Ok(path)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
struct Fleet {
    config: LocalPath,
    safety_number: String,
    primary_component: [u8; 16],
    components: Vec<[u8; 16]>,
    bootstrap_listeners: Vec<[u8; 16]>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub(super) struct Registration {
    version: u16,
    instance: String,
    profile: LocalPath,
    archive: LocalPath,
    protocol_socket: LocalPath,
    listen: SocketAddr,
    advertise: Option<SocketAddr>,
    relay_file: Option<LocalPath>,
    relay_urls: Vec<String>,
    network_config: Option<LocalPath>,
    network_recovery: bool,
    local_fixture: bool,
    gc2_carrier: bool,
    catalog_urls: Vec<String>,
    fleet: Option<Fleet>,
    service: Option<String>,
}

fn optional_path(path: &Option<PathBuf>) -> Result<Option<LocalPath>, String> {
    path.as_deref().map(LocalPath::new).transpose()
}

impl Registration {
    fn from_config(config: &InstanceConfig, instance: &str) -> Result<Self, String> {
        let loaded = config.fleet_config.as_deref().map(|path| {
            fleet::load(path).map_err(|_| {
                "The fleet host configuration is missing or invalid. Restore its owner-private configuration to reconnect.".to_string()
            })
        }).transpose()?;
        Self::from_fleet(config, instance, loaded.as_ref().map(|(fleet, _)| fleet))
    }

    fn from_fleet(
        config: &InstanceConfig,
        instance: &str,
        loaded: Option<&gchat_api::fleet::FleetConfig>,
    ) -> Result<Self, String> {
        let fleet = loaded
            .map(|fleet| {
                let policy = fleet.policy();
                Ok::<_, String>(Fleet {
                    config: LocalPath::new(
                        config
                            .fleet_config
                            .as_deref()
                            .ok_or("Missing fleet configuration path")?,
                    )?,
                    safety_number: fleet.safety_number.clone(),
                    primary_component: fleet.primary_component,
                    components: policy.components,
                    bootstrap_listeners: policy.bootstrap_listeners,
                })
            })
            .transpose()?;
        Ok(Self {
            version: 1,
            instance: instance.into(),
            profile: LocalPath::new(&config.profile)?,
            archive: LocalPath::new(&config.archive)?,
            protocol_socket: LocalPath::new(&config.protocol_socket)?,
            listen: config.listen,
            advertise: config.advertise,
            relay_file: optional_path(&config.relay_file)?,
            relay_urls: if config.network_recovery
                && !config.local_fixture
                && config.relay_file.is_none()
            {
                config.relay_urls.clone()
            } else {
                Vec::new()
            },
            network_config: optional_path(&config.network_config)?,
            network_recovery: config.network_recovery,
            local_fixture: config.local_fixture,
            gc2_carrier: config.gc2_carrier,
            catalog_urls: config.catalog_urls.clone(),
            fleet,
            service: config.managed_service.clone(),
        })
    }

    fn validate(&self) -> Result<(), String> {
        if self.version != 1
            || !crate::build_info::valid_hex(&self.instance, 64)
            || self
                .service
                .as_deref()
                .is_some_and(|unit| !crate::managed_updates::valid_unit(unit))
            || self.relay_urls.len() > 16
            || self.catalog_urls.len() > 16
            || self
                .relay_urls
                .iter()
                .chain(&self.catalog_urls)
                .any(|s| s.len() > 2048)
        {
            return Err("Invalid saved host registration".into());
        }
        self.profile.path()?;
        self.archive.path()?;
        self.protocol_socket.path()?;
        for path in [&self.relay_file, &self.network_config]
            .into_iter()
            .flatten()
        {
            path.path()?;
        }
        if let Some(fleet) = &self.fleet {
            fleet.config.path()?;
            if fleet.components.len() > 64
                || fleet.bootstrap_listeners.len() > 64
                || fleet.safety_number.is_empty()
                || fleet.safety_number.len() > 160
            {
                return Err("Invalid saved fleet host partition".into());
            }
        }
        Ok(())
    }

    fn binds(&self, config: &InstanceConfig) -> Result<(), String> {
        private_fs::validate_private_file(
            &config.archive.with_extension("instance.json"),
            "registered instance metadata",
        )?;
        if self.profile != LocalPath::new(&config.profile)?
            || self.archive != LocalPath::new(&config.archive)?
            || self.instance != instance_metadata(&config.archive)?.id
        {
            return Err("The saved host registration belongs to another instance".into());
        }
        Ok(())
    }

    fn restore(&self, config: &mut InstanceConfig) -> Result<(), String> {
        self.binds(config)?;
        config.protocol_socket = self.protocol_socket.path()?;
        config.listen = self.listen;
        config.advertise = self.advertise;
        config.relay_file = self.relay_file.as_ref().map(LocalPath::path).transpose()?;
        config.relay_urls = self.relay_urls.clone();
        config.network_config = self
            .network_config
            .as_ref()
            .map(LocalPath::path)
            .transpose()?;
        config.network_recovery = self.network_recovery;
        config.local_fixture = self.local_fixture;
        config.gc2_carrier = self.gc2_carrier;
        config.catalog_urls = self.catalog_urls.clone();
        config.fleet_config = self.fleet.as_ref().map(|f| f.config.path()).transpose()?;
        config.managed_service = self.service.clone();
        self.check(config)
    }

    fn check(&self, config: &InstanceConfig) -> Result<(), String> {
        self.binds(config)?;
        let next = Self::from_config(config, &self.instance)?;
        if !self.permits_adoption(&next) {
            return Err("Startup configuration conflicts with this identity's registered host. Restore the registered configuration before reconnecting.".into());
        }
        Ok(())
    }

    /// Explicit installation configuration may add the first scoped host or
    /// managed service. It cannot replace an existing binding or any saved
    /// profile/carrier/network choice. Publication still waits for runtime
    /// identity authentication and exclusive profile ownership.
    fn permits_adoption(&self, next: &Self) -> bool {
        let mut expected = self.clone();
        if expected.fleet.is_none() {
            expected.fleet = next.fleet.clone();
        }
        if expected.service.is_none() {
            expected.service = next.service.clone();
        }
        expected == *next
    }

    fn capability(&self) -> Result<String, String> {
        let bytes = serde_json::to_vec(self).map_err(|e| e.to_string())?;
        Ok(format!("{CAPABILITY}{:x}", Sha256::digest(bytes)))
    }
}

fn path(config: &InstanceConfig) -> PathBuf {
    config.archive.with_extension("host.json")
}

fn read(config: &InstanceConfig) -> Result<Option<Registration>, String> {
    let path = path(config);
    match std::fs::symlink_metadata(&path) {
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(e) => return Err(e.to_string()),
        Ok(_) => {}
    }
    private_fs::validate_private_parent(&path, "host registration")?;
    private_fs::validate_private_file(&path, "host registration")?;
    let mut bytes = Vec::new();
    std::fs::File::open(&path)
        .map_err(|e| e.to_string())?
        .take(LIMIT + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    if bytes.len() as u64 > LIMIT {
        return Err("Saved host registration exceeds its size limit".into());
    }
    let registration: Registration = serde_json::from_slice(&bytes).map_err(|_| {
        "Saved host registration is invalid; restore its original configuration".to_string()
    })?;
    registration.validate()?;
    Ok(Some(registration))
}

pub(super) fn defaults(config: &mut InstanceConfig) -> Result<(), String> {
    if let Some(registration) = read(config)? {
        registration.restore(config)?;
    }
    Ok(())
}

pub(super) fn registered(config: &InstanceConfig) -> Result<bool, String> {
    Ok(read(config)?.is_some())
}

/// Missing fleet/service arguments may be restored; explicit conflicts refuse.
pub(super) fn resolve(config: &mut InstanceConfig) -> Result<(), String> {
    if let Some(registration) = read(config)? {
        if config.fleet_config.is_none() {
            config.fleet_config = registration
                .fleet
                .as_ref()
                .map(|f| f.config.path())
                .transpose()?;
        }
        if config.managed_service.is_none() {
            config.managed_service = registration.service.clone();
        }
        registration.check(config)?;
    }
    Ok(())
}

pub(super) fn capability(config: &InstanceConfig, instance: &str) -> Result<String, String> {
    Registration::from_config(config, instance)?.capability()
}

pub(super) fn capability_for_fleet(
    config: &InstanceConfig,
    instance: &str,
    fleet: Option<&gchat_api::fleet::FleetConfig>,
) -> Result<String, String> {
    Registration::from_fleet(config, instance, fleet)?.capability()
}

/// Publish only after the runtime has authenticated the identity and its partition.
pub(super) fn publish(
    config: &InstanceConfig,
    instance: &str,
    binding: &str,
) -> Result<(), String> {
    // Mobile owns its host in-process, with no desktop launcher/service recipe.
    // Its OS may relocate the application data container during an upgrade.
    if cfg!(any(target_os = "android", target_os = "ios"))
        && config.fleet_config.is_none()
        && config.managed_service.is_none()
    {
        return Ok(());
    }
    let registration = Registration::from_config(config, instance)?;
    registration.validate()?;
    if registration.capability()? != binding {
        return Err("The host configuration changed during startup. Restore its registered identity and component partition before reconnecting.".into());
    }
    let previous = read(config)?;
    if let Some(previous) = &previous {
        previous.check(config)?;
        if previous == &registration {
            return Ok(());
        }
    }
    let bytes = serde_json::to_vec_pretty(&registration).map_err(|e| e.to_string())?;
    if bytes.len() as u64 > LIMIT {
        return Err("Host registration exceeds its size limit".into());
    }
    match crate::store::atomic_write(&path(config), &bytes, previous.is_none()) {
        Ok(()) => Ok(()),
        Err(error) => match read(config)? {
            Some(current) if current == registration => Ok(()),
            _ => Err(error),
        },
    }
}

#[cfg(test)]
#[path = "host_registration_tests.rs"]
mod tests;
