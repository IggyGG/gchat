//! Read-only saved-instance inspection. This path cannot create, unlock or start a host.
use super::{host::InstanceConfig, host_registration, read_instance_metadata};
use crate::managed_updates::{self, ServiceStatus};
use gchat_api::{BuildInfo, ChatClient, InstanceInfo};
use gcoms::sdk::LocalEndpoint;
use serde::Serialize;
use serde_json::Value;
use std::{path::Path, time::Duration};

#[derive(Debug, Serialize)]
pub struct HostDiagnostics {
    pub schema: u16,
    pub profile: Value,
    pub archive: Value,
    pub protocol_socket: Value,
    pub registration: Value,
    pub instance_id: Option<String>,
    pub registered_instance: Option<String>,
    pub mode: &'static str,
    pub managed_service: Option<String>,
    pub service_status: Option<ServiceStatus>,
    pub client_build: Option<BuildInfo>,
    pub host_build: Option<BuildInfo>,
    pub client_api_version: u16,
    pub local_ready: bool,
    pub archive_locked: Option<bool>,
    pub protocol_locked: Option<bool>,
    pub error_code: Option<&'static str>,
    pub recovery: &'static str,
}

async fn existing_host(
    config: &InstanceConfig,
    instance: &str,
    registered: bool,
) -> Result<Option<InstanceInfo>, &'static str> {
    let endpoint = config.chat_endpoint();
    let stream = match gcoms::sdk::local::connect(&LocalEndpoint::new(&endpoint)).await {
        Ok(stream) => stream,
        Err(_) => return Ok(None),
    };
    drop(stream);
    let binding =
        host_registration::capability(config, instance).map_err(|_| "host_configuration")?;
    let pid = match &config.managed_service {
        Some(unit) => Some(
            managed_updates::running_service_pid(unit)
                .await
                .map_err(|_| "host_mismatch")?,
        ),
        None => None,
    };
    #[cfg(unix)]
    let result = ChatClient::inspect_owned_host(
        &endpoint,
        Some(instance),
        registered.then_some(binding.as_str()),
        rustix::process::getuid().as_raw(),
        pid,
    )
    .await;
    #[cfg(not(unix))]
    let result = {
        let _ = pid;
        ChatClient::inspect_host(
            &endpoint,
            Some(instance),
            registered.then_some(binding.as_str()),
        )
        .await
    };
    result.map(Some).map_err(|_| "host_mismatch")
}

/// Inspect existing public state, including an invalid/missing referenced fleet file.
/// Unknown host builds remain null; a stopped host is never started just to identify it.
pub async fn inspect(home: Option<&Path>) -> Result<HostDiagnostics, String> {
    let mut config = InstanceConfig::selected(home)?;
    let metadata = read_instance_metadata(&config.archive);
    let registration = host_registration::inspect(&mut config);
    let mut valid = metadata.is_ok() && registration.is_ok();
    let instance_id = metadata.ok().flatten().map(|metadata| metadata.id);
    let registration = registration.ok().flatten();
    let registered = registration.is_some();
    if let Some(registration) = &registration {
        valid &= registration.configuration_valid;
    }
    if config.network_config.is_some()
        && crate::network::selected_json(config.network_config.as_deref()).is_err()
    {
        valid = false;
    }
    let mut report = HostDiagnostics {
        schema: 1,
        profile: host_registration::path_reference(&config.profile)?,
        archive: host_registration::path_reference(&config.archive)?,
        protocol_socket: host_registration::path_reference(&config.protocol_socket)?,
        registration: host_registration::path_reference(
            &config.archive.with_extension("host.json"),
        )?,
        instance_id,
        registered_instance: registration
            .as_ref()
            .map(|registration| registration.instance.clone()),
        mode: registration
            .as_ref()
            .map_or("unregistered", |registration| registration.mode),
        managed_service: registration.and_then(|registration| registration.service),
        service_status: None,
        client_build: crate::build_info::current(),
        host_build: None,
        client_api_version: gchat_api::VERSION,
        local_ready: false,
        archive_locked: None,
        protocol_locked: None,
        error_code: None,
        recovery: "Open the selected instance using its saved host configuration.",
    };
    if let Some(service) = &report.managed_service {
        report.service_status = Some(managed_updates::service_status(service).await);
    }
    if !valid {
        report.error_code = Some("host_configuration");
        report.recovery =
            "Restore this saved instance's registered host configuration before reconnecting.";
        return Ok(report);
    }
    let Some(instance) = &report.instance_id else {
        report.recovery = "No saved instance metadata was found; review the selected profile location before opening GChat.";
        return Ok(report);
    };
    match tokio::time::timeout(
        Duration::from_secs(3),
        existing_host(&config, instance, registered),
    )
    .await
    {
        Ok(Ok(Some(identity))) => {
            report.local_ready = true;
            report.archive_locked = Some(identity.locked);
            report.protocol_locked = Some(identity.protocol_locked);
            report.host_build = identity.build;
            report.recovery =
                "The matching local host is ready; lock and network recovery are separate states.";
        }
        Ok(Err(code)) => {
            report.error_code = Some(code);
            report.recovery = "Inspect the selected instance and host build; restart only its registered host after correcting the mismatch.";
        }
        _ => {
            report.error_code = Some("host_unavailable");
            report.recovery = if report.managed_service.is_some() {
                "Inspect the registered service state; ordinary launch starts that exact service when stopped."
            } else if registered {
                "Open the selected instance through its configured standalone host."
            } else {
                "This instance has no saved host recipe. Restore or explicitly configure its intended host before reconnecting."
            };
        }
    }
    Ok(report)
}
