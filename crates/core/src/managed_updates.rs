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

/// Read-only, sanitized service-manager observations for local diagnostics.
#[derive(Debug, serde::Serialize)]
pub struct ServiceStatus {
    pub query_state: &'static str,
    pub load_state: Option<String>,
    pub active_state: Option<String>,
    pub sub_state: Option<String>,
    pub main_pid: Option<u32>,
    pub result: Option<String>,
    pub exit_status: Option<u32>,
}

impl ServiceStatus {
    fn unavailable(query_state: &'static str) -> Self {
        Self {
            query_state,
            load_state: None,
            active_state: None,
            sub_state: None,
            main_pid: None,
            result: None,
            exit_status: None,
        }
    }

    fn parse(bytes: &[u8]) -> Option<Self> {
        if bytes.len() > 4096 {
            return None;
        }
        let text = std::str::from_utf8(bytes).ok()?;
        let mut fields = std::collections::BTreeMap::new();
        for line in text.lines() {
            let (key, value) = line.split_once('=')?;
            if ![
                "LoadState",
                "ActiveState",
                "SubState",
                "MainPID",
                "Result",
                "ExecMainStatus",
            ]
            .contains(&key)
                || fields.insert(key, value).is_some()
            {
                return None;
            }
        }
        let state = |key| -> Option<String> {
            let value: &&str = fields.get(key)?;
            (!value.is_empty()
                && value.len() <= 40
                && value
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-'))
            .then(|| (*value).to_string())
        };
        let number = |key| {
            fields
                .get(key)
                .map(|value| value.parse::<u32>())
                .transpose()
                .ok()
        };
        Some(Self {
            query_state: "observed",
            load_state: Some(state("LoadState")?),
            active_state: Some(state("ActiveState")?),
            sub_state: Some(state("SubState")?),
            main_pid: number("MainPID")?,
            result: if fields.contains_key("Result") {
                Some(state("Result")?)
            } else {
                None
            },
            exit_status: number("ExecMainStatus")?,
        })
    }
}

/// Never activates or changes a unit. Output and process lifetime are bounded.
pub(crate) async fn service_status(unit: &str) -> ServiceStatus {
    use tokio::io::AsyncReadExt;
    if !cfg!(target_os = "linux") || !valid_unit(unit) {
        return ServiceStatus::unavailable("unsupported");
    }
    let observe = async {
        let mut child = tokio::process::Command::new("systemctl")
            .args([
                "--user",
                "--no-pager",
                "show",
                unit,
                "--property=LoadState,ActiveState,SubState,MainPID,Result,ExecMainStatus",
            ])
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::null())
            .kill_on_drop(true)
            .spawn()
            .ok()?;
        let stdout = child.stdout.take()?;
        let mut bytes = Vec::new();
        stdout.take(4097).read_to_end(&mut bytes).await.ok()?;
        if bytes.len() > 4096 {
            return None;
        }
        let success = child.wait().await.ok()?.success();
        let status = ServiceStatus::parse(&bytes)?;
        (success || status.load_state.as_deref() == Some("not-found")).then_some(status)
    };
    tokio::time::timeout(std::time::Duration::from_secs(2), observe)
        .await
        .ok()
        .flatten()
        .unwrap_or_else(|| ServiceStatus::unavailable("unavailable"))
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
    fn diagnostic_service_properties_are_bounded_and_not_raw_process_output() {
        let output = b"LoadState=loaded\nActiveState=failed\nSubState=failed\nMainPID=0\nResult=exit-code\nExecMainStatus=1\n";
        let status = ServiceStatus::parse(output).unwrap();
        assert_eq!(status.query_state, "observed");
        assert_eq!(status.active_state.as_deref(), Some("failed"));
        assert_eq!(status.exit_status, Some(1));
        assert_eq!(status.main_pid, Some(0));
        for invalid in [
            b"LoadState=loaded\nLoadState=not-found\nActiveState=active\nSubState=running\n"
                .as_slice(),
            b"LoadState=loaded\nActiveState=active\nSubState=running\nEnvironment=secret\n"
                .as_slice(),
            b"LoadState=loaded\nActiveState=active\nSubState=running\nMainPID=invalid\n".as_slice(),
            b"LoadState=loaded\nActiveState=active\nSubState=\x1b[31msecret\n".as_slice(),
            &[b'x'; 4097],
        ] {
            assert!(ServiceStatus::parse(invalid).is_none());
        }
    }

    #[tokio::test]
    async fn diagnostics_do_not_query_unregistered_service_names() {
        assert_eq!(
            service_status("ssh.service").await.query_state,
            "unsupported"
        );
        assert_eq!(
            service_status("gchat-x.service\nsecret").await.query_state,
            "unsupported"
        );
    }

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
