//! Bounded, per-instance startup. A registered managed host owns its lifecycle.
use super::{
    host::{self, InstanceConfig},
    host_registration, instance_metadata,
};
use crate::private_fs;
use fs2::FileExt;
use gchat_api::{ChatClient, ChatError};
use gcoms::sdk::LocalEndpoint;
use std::{path::Path, time::Duration};

fn error(code: &str, message: impl Into<String>) -> ChatError {
    ChatError {
        code: code.into(),
        message: message.into(),
    }
}

async fn probe(config: &InstanceConfig, instance: &str) -> Result<Option<ChatClient>, ChatError> {
    let endpoint = config.chat_endpoint();
    let available = tokio::time::timeout(
        Duration::from_secs(1),
        gcoms::sdk::local::connect(&LocalEndpoint::new(&endpoint)),
    )
    .await;
    match available {
        Ok(Ok(stream)) => drop(stream),
        Ok(Err(_)) => return Ok(None),
        Err(_) => return Err(error("host_unavailable", "The selected local host is not responding. Inspect its service status before restarting.")),
    }
    let strict = config.fleet_config.is_some()
        || config.managed_service.is_some()
        || config
            .has_registered_host()
            .map_err(|e| error("host_configuration", e))?;
    let binding = host_registration::capability(config, instance)
        .map_err(|e| error("host_configuration", e))?;
    let process_id = match &config.managed_service {
        Some(unit) => Some(
            crate::managed_updates::running_service_pid(unit)
                .await
                .map_err(|e| error("host_mismatch", e))?,
        ),
        None => None,
    };
    let connect = async {
        #[cfg(unix)]
        {
            ChatClient::connect_owned_host(
                &endpoint,
                Some(instance),
                strict.then_some(binding.as_str()),
                rustix::process::getuid().as_raw(),
                process_id,
            )
            .await
        }
        #[cfg(not(unix))]
        {
            let _ = process_id;
            ChatClient::connect_host(
                &endpoint,
                Some(instance),
                strict.then_some(binding.as_str()),
            )
            .await
        }
    };
    let client = tokio::time::timeout(Duration::from_secs(2), connect)
        .await
        .map_err(|_| {
            error(
                "host_unavailable",
                "The selected local host handshake timed out.",
            )
        })?
        .map_err(|e| error("host_mismatch", e))?;
    Ok(Some(client))
}

fn lock_file(config: &InstanceConfig) -> Result<std::fs::File, ChatError> {
    let path = config.archive.with_extension("launch.lock");
    private_fs::validate_private_parent(&path, "host launch lock")
        .map_err(|e| error("host_configuration", e))?;
    let mut options = std::fs::OpenOptions::new();
    options.read(true).write(true).create_new(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.mode(0o600);
    }
    match options.open(&path) {
        Ok(file) => {
            private_fs::make_private(&path, false).map_err(|e| error("host_configuration", e))?;
            Ok(file)
        }
        Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => {
            private_fs::validate_private_file(&path, "host launch lock")
                .map_err(|e| error("host_configuration", e))?;
            std::fs::OpenOptions::new()
                .read(true)
                .write(true)
                .open(path)
                .map_err(|e| error("host_configuration", e.to_string()))
        }
        Err(e) => Err(error("host_configuration", e.to_string())),
    }
}

pub(super) async fn ensure(
    config: &InstanceConfig,
    executable: &Path,
    gchat_binary: bool,
) -> Result<ChatClient, ChatError> {
    if !config.uses_protocol_ipc() {
        return Err(error(
            "host_configuration",
            "outbound instances must attach in-process instead of launching a daemon",
        ));
    }
    let mut config = config.clone();
    host_registration::resolve(&mut config).map_err(|e| error("host_configuration", e))?;
    let metadata =
        instance_metadata(&config.archive).map_err(|e| error("host_configuration", e))?;
    // Covers contention, manager activation, handshake and child readiness together.
    tokio::time::timeout(Duration::from_secs(30), async {
        if let Some(client) = probe(&config, &metadata.id).await? { return Ok(client); }
        let lock = lock_file(&config)?;
        loop {
            match lock.try_lock_exclusive() {
                Ok(()) => break,
                Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                    tokio::time::sleep(Duration::from_millis(50)).await;
                    if let Some(client) = probe(&config, &metadata.id).await? { return Ok(client); }
                }
                Err(e) => return Err(error("host_unavailable", e.to_string())),
            }
        }
        if let Some(client) = probe(&config, &metadata.id).await? { return Ok(client); }
        if let Some(unit) = &config.managed_service {
            crate::managed_updates::start_service(unit).await.map_err(|e| error("host_unavailable", e))?;
            loop {
                if let Some(client) = probe(&config, &metadata.id).await? { return Ok(client); }
                tokio::time::sleep(Duration::from_millis(50)).await;
            }
        }
        if gcoms::sdk::local::connect(&LocalEndpoint::new(&config.protocol_socket)).await.is_ok() {
            return Err(error("host_mismatch", "The selected daemon has no matching shared chat API. Restart that instance with the matching GChat release."));
        }
        host::launch_standalone(&config, executable, gchat_binary).await.map_err(|e| error("host_unavailable", e))
    }).await.map_err(|_| error("host_unavailable", "The selected host did not become ready within 30 seconds. Inspect its service status and retry."))?
}

#[cfg(test)]
#[path = "host_startup_tests.rs"]
mod tests;
