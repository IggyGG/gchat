//! Explicit owner opt-in to updates through a Linux user service manager.
//! The private IPC owner still has to prepare, checkpoint and exit the daemon.

pub(crate) fn valid_unit(unit: &str) -> bool {
    unit.starts_with("gchat-")
        && unit.ends_with(".service")
        && unit.len() <= 128
        && unit
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_.@".contains(&b))
}

/// Identify the exact user service owning this process. Other applications,
/// scopes and system services are never restart targets.
pub async fn service_for_process(pid: u32) -> Result<Option<String>, String> {
    if !cfg!(target_os = "linux") {
        return Ok(None);
    }
    let output = tokio::time::timeout(
        std::time::Duration::from_secs(5),
        tokio::process::Command::new("systemctl")
            .args(["--user", "whoami", &pid.to_string()])
            .kill_on_drop(true)
            .output(),
    )
    .await
    .map_err(|_| "Service manager identification timed out")?;
    let output = match output {
        Ok(output) if output.status.success() => output,
        _ => return Ok(None),
    };
    let unit = String::from_utf8(output.stdout).map_err(|_| "Invalid service identity")?;
    let unit = unit.trim();
    if !valid_unit(unit) {
        return Ok(None);
    }
    let output = tokio::time::timeout(
        std::time::Duration::from_secs(5),
        tokio::process::Command::new("systemctl")
            .args(["--user", "show", unit, "-p", "MainPID", "--value"])
            .kill_on_drop(true)
            .output(),
    )
    .await
    .map_err(|_| "Service manager identification timed out")?
    .map_err(|_| "Service manager is unavailable")?;
    if !output.status.success() || String::from_utf8_lossy(&output.stdout).trim() != pid.to_string()
    {
        return Err("The service manager does not own this daemon process".into());
    }
    Ok(Some(unit.into()))
}

pub async fn start_service(unit: &str) -> Result<(), String> {
    if !cfg!(target_os = "linux") || !valid_unit(unit) {
        return Err("Unsupported managed update service".into());
    }
    let result = tokio::time::timeout(
        std::time::Duration::from_secs(30),
        tokio::process::Command::new("systemctl")
            .args(["--user", "start", unit])
            .kill_on_drop(true)
            .output(),
    )
    .await
    .map_err(|_| "Service activation timed out")?
    .map_err(|_| "Service manager is unavailable")?;
    if !result.status.success() {
        return Err("The registered service could not start; inspect its service status".into());
    }
    Ok(())
}

/// A successful socket connection alone does not prove the registered manager owns it.
pub(crate) async fn running_service_pid(unit: &str) -> Result<u32, String> {
    if !cfg!(target_os = "linux") || !valid_unit(unit) {
        return Err("The registered host requires its Linux user service".into());
    }
    let output = tokio::time::timeout(
        std::time::Duration::from_secs(5),
        tokio::process::Command::new("systemctl")
            .args(["--user", "show", unit, "-p", "MainPID", "--value"])
            .kill_on_drop(true)
            .output(),
    )
    .await
    .map_err(|_| "Service manager identification timed out")?
    .map_err(|_| "Service manager is unavailable")?;
    let pid = String::from_utf8_lossy(&output.stdout)
        .trim()
        .parse::<u32>()
        .ok()
        .filter(|pid| *pid > 0);
    if !output.status.success() || pid.is_none() {
        return Err("The running endpoint is not owned by the registered host service".into());
    }
    if service_for_process(pid.expect("checked service PID"))
        .await?
        .as_deref()
        != Some(unit)
    {
        return Err("The registered host process no longer belongs to its service".into());
    }
    Ok(pid.expect("checked service PID"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn service_activation_is_limited_to_gchat_user_units() {
        assert!(valid_unit("gchat-fleet-host.service"));
        for name in [
            "ssh.service",
            "gchat-view.scope",
            "../gchat-host.service",
            "gchat-x.service\nssh.service",
        ] {
            assert!(!valid_unit(name));
        }
    }
}
