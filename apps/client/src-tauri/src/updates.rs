//! Desktop update downloads never restart a working view. Installation is a
//! separate owner action, also attempted for a previously staged update at launch.
use base64::Engine;
use gchat_api::{PrepareUpdateResult, Request, Response, UpdateRequest};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{path::PathBuf, sync::Mutex, time::Duration};
use tauri::Manager;
use tauri_plugin_updater::{Update, UpdaterExt};

const MAX_UPDATE: u64 = 512 * 1024 * 1024;

#[derive(Clone, Serialize, Default)]
#[serde(rename_all = "camelCase")]
pub(super) struct Status {
    state: String,
    version: Option<String>,
    downloaded: u64,
    total: Option<u64>,
    message: String,
    running: Option<gchat_api::BuildInfo>,
}

#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Binding {
    schema: u32,
    release_id: String,
    version: String,
    target: String,
    sha256: String,
    size: u64,
}

struct Staged {
    update: Update,
    binding: Binding,
    path: PathBuf,
}

struct Updates {
    view: String,
    directory: PathBuf,
    status: Mutex<Status>,
    staged: tokio::sync::Mutex<Option<Staged>>,
    action: tokio::sync::Mutex<()>,
    interacted: std::sync::atomic::AtomicBool,
    _view_lock: std::fs::File,
}

fn error(value: impl std::fmt::Display) -> String {
    value.to_string()
}

fn verify_signed(bytes: &[u8], signature: &str) -> Result<(), String> {
    let config: serde_json::Value =
        serde_json::from_str(include_str!("../tauri.conf.json")).map_err(error)?;
    let key = config["plugins"]["updater"]["pubkey"]
        .as_str()
        .ok_or("Updater trust is not configured")?;
    let decode = |value: &str| -> Result<String, String> {
        String::from_utf8(
            base64::engine::general_purpose::STANDARD
                .decode(value)
                .map_err(error)?,
        )
        .map_err(error)
    };
    let key = minisign_verify::PublicKey::decode(&decode(key)?).map_err(error)?;
    let signature = minisign_verify::Signature::decode(&decode(signature)?).map_err(error)?;
    key.verify(bytes, &signature, true).map_err(error)
}

fn binding(update: &Update) -> Result<Binding, String> {
    // Sign metadata separately: a valid old payload signature must not be usable
    // with a forged newer version or a different release/architecture.
    let encoded = update.raw_json["binding"]
        .as_str()
        .ok_or("Missing signed update binding")?;
    if encoded.len() > 8192 {
        return Err("Update binding is too large".into());
    }
    let signature = update.raw_json["binding_signature"]
        .as_str()
        .ok_or("Missing update binding signature")?;
    verify_signed(encoded.as_bytes(), signature)?;
    let value: Binding = serde_json::from_str(encoded).map_err(error)?;
    let os = if cfg!(target_os = "macos") {
        "darwin"
    } else {
        std::env::consts::OS
    };
    let target = format!("{os}-{}", std::env::consts::ARCH);
    if value.schema != 1
        || value.version != update.version
        || value.target != target
        || value.size == 0
        || value.size > MAX_UPDATE
        || !hex_id(&value.release_id, 64)
        || !hex_id(&value.sha256, 64)
    {
        return Err("Update identity, size or platform does not match".into());
    }
    Ok(value)
}

fn hex_id(value: &str, size: usize) -> bool {
    value.len() == size
        && value
            .bytes()
            .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
}

fn verify_payload(bytes: &[u8], binding: &Binding, signature: &str) -> Result<(), String> {
    if bytes.len() as u64 != binding.size
        || format!("{:x}", Sha256::digest(bytes)) != binding.sha256
    {
        return Err("Downloaded update does not match its signed binding".into());
    }
    verify_signed(bytes, signature)
}

fn status(app: &tauri::AppHandle, state: &str, message: impl Into<String>) {
    let updates = app.state::<Updates>();
    let mut value = updates.status.lock().expect("update status");
    value.state = state.into();
    value.message = message.into();
}

#[tauri::command]
pub(super) fn chat_update_activity(app: tauri::AppHandle) {
    app.state::<Updates>()
        .interacted
        .store(true, std::sync::atomic::Ordering::SeqCst);
}

#[tauri::command]
pub(super) fn chat_update_status(app: tauri::AppHandle) -> Status {
    app.state::<Updates>()
        .status
        .lock()
        .expect("update status")
        .clone()
}

async fn maintenance(
    app: &tauri::AppHandle,
    request: UpdateRequest,
) -> Result<PrepareUpdateResult, String> {
    let attachment = app.state::<crate::desktop::Attachment>();
    let client = crate::desktop::attached(&attachment).await?;
    match client
        .request_v2(Request::Update { request })
        .await
        .map_err(error)?
    {
        Response::Update { result } => Ok(result),
        _ => Err("The running service does not support coordinated updates yet".into()),
    }
}

#[tauri::command]
pub(super) async fn chat_update_check(app: tauri::AppHandle) -> Result<Status, String> {
    let result = check(&app).await;
    if let Err(message) = &result {
        status(&app, "failed", message.clone());
    }
    result?;
    Ok(chat_update_status(app))
}

async fn check(app: &tauri::AppHandle) -> Result<(), String> {
    let state = app.state::<Updates>();
    let Ok(_action) = state.action.try_lock() else {
        return Ok(());
    };
    if cfg!(target_os = "linux") && std::env::var_os("APPIMAGE").is_none() {
        // Debian owns /usr/bin. Never let an AppImage updater replace it.
        return check_debian(app).await;
    }
    status(app, "checking", "Checking for updates…");
    let Some(mut update) = app
        .updater_builder()
        .timeout(Duration::from_secs(15))
        .build()
        .map_err(error)?
        .check()
        .await
        .map_err(error)?
    else {
        *state.staged.lock().await = None;
        status(app, "current", "GChat is up to date.");
        return Ok(());
    };
    let binding = binding(&update)?;
    let path = state.directory.join(format!("{}.update", binding.sha256));
    if !path.exists() {
        status(app, "downloading", "Downloading update…");
        {
            let mut value = state.status.lock().expect("update status");
            value.version = Some(update.version.clone());
            value.total = Some(binding.size);
            value.downloaded = 0;
        }
        update.timeout = Some(Duration::from_secs(180));
        let overflow = tokio::sync::Notify::new();
        let download = update.download(
            |chunk, _| {
                let mut value = state.status.lock().expect("update status");
                value.downloaded = value.downloaded.saturating_add(chunk as u64);
                if value.downloaded > binding.size {
                    overflow.notify_one();
                }
            },
            || {},
        );
        let bytes = tokio::select! {
            result = download => result.map_err(error)?,
            _ = overflow.notified() => return Err("Update exceeded its signed size limit".into()),
        };
        verify_payload(&bytes, &binding, &update.signature)?;
        use std::io::Write;
        let mut file = tempfile::NamedTempFile::new_in(&state.directory).map_err(error)?;
        file.write_all(&bytes).map_err(error)?;
        file.as_file().sync_all().map_err(error)?;
        file.persist(&path).map_err(error)?;
    } else {
        if std::fs::metadata(&path).map_err(error)?.len() != binding.size {
            return Err("Staged update size changed".into());
        }
        verify_payload(
            &tokio::fs::read(&path).await.map_err(error)?,
            &binding,
            &update.signature,
        )?;
    }
    *state.staged.lock().await = Some(Staged {
        update,
        binding,
        path,
    });
    status(
        app,
        "ready",
        "Update ready. It will activate at your next launch, or choose Restart now.",
    );
    Ok(())
}

async fn check_debian(app: &tauri::AppHandle) -> Result<(), String> {
    let output = tokio::process::Command::new("dpkg-query")
        .args(["-W", "-f=${Version}", "g-chat"])
        .output()
        .await
        .map_err(error)?;
    if !output.status.success() {
        status(
            app,
            "manual",
            "This build is not managed by the GChat APT repository.",
        );
        return Ok(());
    }
    let installed = String::from_utf8(output.stdout).map_err(error)?;
    let attachment = app.state::<crate::desktop::Attachment>();
    let client = crate::desktop::attached(&attachment).await?;
    let stale_service = match client.request_v2(Request::Identify).await.map_err(error)? {
        Response::Instance { instance } => {
            match (instance.build, gchat_core::build_info::current()) {
                (Some(service), Some(window)) => service.release_id != window.release_id,
                _ => false, // Historical services require the controlled initial bootstrap.
            }
        }
        _ => return Err("Cannot identify the running service".into()),
    };
    let running = app.package_info().version.to_string();
    let newer = tokio::process::Command::new("dpkg")
        .args(["--compare-versions", installed.trim(), "gt", &running])
        .status()
        .await
        .map_err(error)?;
    if newer.success() || stale_service {
        status(
            app,
            "ready",
            "A newer GChat package is installed. Restart to activate it.",
        );
    } else if std::path::Path::new("/etc/apt/sources.list.d/gchat.sources").exists() {
        status(app, "current", "GChat package updates are managed by APT.");
    } else {
        status(
            app,
            "manual",
            "Automatic package updates have not been configured on this computer.",
        );
    }
    app.state::<Updates>()
        .status
        .lock()
        .expect("update status")
        .version = Some(installed);
    Ok(())
}

async fn stop_instance(app: &tauri::AppHandle, release: &str) -> Result<(), String> {
    let view = app.state::<Updates>().view.clone();
    maintenance(app, UpdateRequest::Heartbeat { view: view.clone() }).await?;
    let pid = match maintenance(
        app,
        UpdateRequest::Prepare {
            view: view.clone(),
            release: release.into(),
        },
    )
    .await?
    {
        PrepareUpdateResult::Ready { process_id, .. } if process_id != std::process::id() => {
            process_id
        }
        PrepareUpdateResult::Busy { reason } => return Err(reason),
        _ => return Err("Update preparation was not acknowledged".into()),
    };
    let attachment = app.state::<crate::desktop::Attachment>();
    let client = crate::desktop::attached(&attachment).await?;
    let result: Result<(), String> = async {
        let response = client
            .request_v2(Request::Disconnect)
            .await
            .map_err(error)?;
        if !matches!(response, Response::Snapshot { snapshot } if snapshot.instance.protocol_locked)
        {
            return Err("Service did not confirm its checkpointed shutdown".into());
        }
        maintenance(
            app,
            UpdateRequest::Exit {
                view: view.clone(),
                release: release.into(),
            },
        )
        .await?;
        for _ in 0..50 {
            // Socket failure alone does not prove the process has terminated.
            if process_exited(pid)? {
                attachment
                    .updating
                    .store(true, std::sync::atomic::Ordering::SeqCst);
                *attachment.client.lock().await = None;
                return Ok(());
            }
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
        Err("Service is still running; update has been deferred".into())
    }
    .await;
    if result.is_err() {
        let _ = maintenance(
            app,
            UpdateRequest::Abort {
                view,
                release: release.into(),
            },
        )
        .await;
    }
    result
}

#[tauri::command]
pub(super) async fn chat_update_install(app: tauri::AppHandle) -> Result<(), String> {
    let updates = app.state::<Updates>();
    let _action = updates
        .action
        .try_lock()
        .map_err(|_| "An update action is already running")?;
    // Across separate --home windows there can be more than one GUI process.
    let lock = std::fs::OpenOptions::new()
        .create(true)
        .truncate(false)
        .write(true)
        .open(updates.directory.join("install.lock"))
        .map_err(error)?;
    fs2::FileExt::try_lock_exclusive(&lock).map_err(|_| "Another GChat update is running")?;
    for entry in std::fs::read_dir(updates.directory.join("views")).map_err(error)? {
        let entry = entry.map_err(error)?;
        if entry.file_name() == std::ffi::OsStr::new(&updates.view) {
            continue;
        }
        let file = std::fs::OpenOptions::new()
            .write(true)
            .open(entry.path())
            .map_err(error)?;
        fs2::FileExt::try_lock_exclusive(&file)
            .map_err(|_| "Another GChat profile window is open. Close it before restarting.")?;
        // No live process owns this leftover view. The installation lock prevents
        // a new process from registering while the old executable is replaced.
        std::fs::remove_file(entry.path()).map_err(error)?;
    }
    let result: Result<(), String> = async {
        if cfg!(target_os = "linux") && std::env::var_os("APPIMAGE").is_none() {
            // Root owns this marker; APT publishes it only after package verification.
            #[cfg(unix)]
            {
                use std::os::unix::fs::MetadataExt;
                let metadata =
                    std::fs::symlink_metadata("/var/lib/gchat-update/release-id").map_err(error)?;
                if !metadata.is_file() || metadata.uid() != 0 || metadata.mode() & 0o022 != 0 {
                    return Err(
                        "The package release identity is not root-owned and protected".into(),
                    );
                }
            }
            let marker = std::fs::read_to_string("/var/lib/gchat-update/release-id")
                .map_err(|_| "The installed package has no verified update identity")?;
            let release = marker.trim();
            if !hex_id(release, 64) {
                return Err("Invalid installed release identity".into());
            }
            stop_instance(&app, release).await?;
            app.restart();
        }
        let staged = updates.staged.lock().await;
        let staged = staged
            .as_ref()
            .ok_or("Download and verify an update first")?;
        if std::fs::metadata(&staged.path).map_err(error)?.len() != staged.binding.size {
            return Err("Staged update changed".into());
        }
        let bytes = tokio::fs::read(&staged.path).await.map_err(error)?;
        verify_payload(&bytes, &staged.binding, &staged.update.signature)?;
        stop_instance(&app, &staged.binding.release_id).await?;
        staged.update.install(bytes).map_err(error)?;
        app.restart();
    }
    .await;
    if let Err(message) = &result {
        app.state::<crate::desktop::Attachment>()
            .updating
            .store(false, std::sync::atomic::Ordering::SeqCst);
        status(&app, "deferred", message.clone());
    }
    result
}

pub(super) fn setup(app: &mut tauri::App) -> tauri::Result<()> {
    let directory = app.path().app_cache_dir()?.join("updates");
    gchat_core::paths::ensure_private_dir(&directory, "update cache")
        .map_err(std::io::Error::other)?;
    let previously_staged = std::fs::read_dir(&directory)?
        .filter_map(Result::ok)
        .any(|entry| entry.path().extension().is_some_and(|ext| ext == "update"));
    let view = format!("{:032x}", rand::random::<u128>());
    let registration = std::fs::OpenOptions::new()
        .create(true)
        .truncate(false)
        .write(true)
        .open(directory.join("install.lock"))?;
    fs2::FileExt::try_lock_shared(&registration).map_err(|_| {
        std::io::Error::other("GChat is activating an update. Open it again shortly.")
    })?;
    let views = directory.join("views");
    gchat_core::paths::ensure_private_dir(&views, "update views").map_err(std::io::Error::other)?;
    let view_lock = std::fs::OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(views.join(&view))?;
    fs2::FileExt::try_lock_exclusive(&view_lock)?;
    app.manage(Updates {
        view,
        directory,
        _view_lock: view_lock,
        status: Mutex::new(Status {
            state: "idle".into(),
            running: gchat_core::build_info::current(),
            ..Status::default()
        }),
        staged: tokio::sync::Mutex::new(None),
        action: tokio::sync::Mutex::new(()),
        interacted: std::sync::atomic::AtomicBool::new(false),
    });
    drop(registration);
    let heartbeat = app.handle().clone();
    tauri::async_runtime::spawn(async move {
        loop {
            let view = heartbeat.state::<Updates>().view.clone();
            let _ = maintenance(&heartbeat, UpdateRequest::Heartbeat { view }).await;
            tokio::time::sleep(Duration::from_secs(15)).await;
        }
    });
    let activation_pending =
        previously_staged || (cfg!(target_os = "linux") && std::env::var_os("APPIMAGE").is_none());
    if !activation_pending {
        if let Some(window) = app.get_webview_window("main") {
            window.show()?;
        }
    }
    let handle = app.handle().clone();
    tauri::async_runtime::spawn(async move {
        let mut first = true;
        loop {
            if first {
                if tokio::time::timeout(Duration::from_secs(20), chat_update_check(handle.clone()))
                    .await
                    .is_err()
                {
                    status(
                        &handle,
                        "deferred",
                        "Startup update check timed out. GChat will check again in the background.",
                    );
                }
            } else {
                let _ = chat_update_check(handle.clone()).await;
            }
            if first
                && (previously_staged
                    || (cfg!(target_os = "linux") && std::env::var_os("APPIMAGE").is_none()))
                && !handle
                    .state::<Updates>()
                    .interacted
                    .load(std::sync::atomic::Ordering::SeqCst)
                && chat_update_status(handle.clone()).state == "ready"
            {
                let _ = chat_update_install(handle.clone()).await;
            }
            if first {
                if let Some(window) = handle.get_webview_window("main") {
                    let _ = window.show();
                }
            }
            first = false;
            tokio::time::sleep(Duration::from_secs(900 + rand::random::<u8>() as u64 % 60)).await;
        }
    });
    Ok(())
}

// A reused PID conservatively defers the update. Never terminate a process to
// make progress, and never confuse access denial with proof of process exit.
#[cfg(unix)]
fn process_exited(pid: u32) -> Result<bool, String> {
    let pid = i32::try_from(pid).map_err(error)?;
    if pid <= 0 {
        return Err("Invalid service process identifier".into());
    }
    // SAFETY: signal zero performs existence/permission checking only.
    if unsafe { libc::kill(pid, 0) } == 0 {
        return Ok(false);
    }
    let error = std::io::Error::last_os_error();
    if error.raw_os_error() == Some(libc::ESRCH) {
        Ok(true)
    } else {
        Err(error.to_string())
    }
}
#[cfg(windows)]
fn process_exited(pid: u32) -> Result<bool, String> {
    use windows_sys::Win32::{
        Foundation::{CloseHandle, ERROR_INVALID_PARAMETER, WAIT_OBJECT_0, WAIT_TIMEOUT},
        System::Threading::{OpenProcess, WaitForSingleObject, PROCESS_SYNCHRONIZE},
    };
    if pid == 0 {
        return Err("Invalid service process identifier".into());
    }
    // SAFETY: a synchronization-only process handle, closed on every branch.
    unsafe {
        let handle = OpenProcess(PROCESS_SYNCHRONIZE, 0, pid);
        if handle.is_null() {
            let error = std::io::Error::last_os_error();
            return if error.raw_os_error() == Some(ERROR_INVALID_PARAMETER as i32) {
                Ok(true)
            } else {
                Err(error.to_string())
            };
        }
        let state = WaitForSingleObject(handle, 0);
        CloseHandle(handle);
        match state {
            WAIT_OBJECT_0 => Ok(true),
            WAIT_TIMEOUT => Ok(false),
            _ => Err("Cannot confirm service exit".into()),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn service_liveness_is_not_inferred_from_a_missing_socket() {
        assert!(!process_exited(std::process::id()).unwrap());
        assert!(process_exited(0).is_err());
    }
    #[test]
    fn changed_download_is_refused_before_installation() {
        let bytes = b"original";
        let binding = Binding {
            schema: 1,
            release_id: "a".repeat(64),
            version: "1.0.1".into(),
            target: "linux-x86_64".into(),
            sha256: format!("{:x}", Sha256::digest(bytes)),
            size: bytes.len() as u64,
        };
        assert!(verify_payload(b"modified", &binding, "invalid-signature")
            .unwrap_err()
            .contains("binding"));
        assert!(verify_payload(bytes, &binding, "invalid-signature").is_err());
    }
}
