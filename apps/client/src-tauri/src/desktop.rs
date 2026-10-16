use gchat_api::{ChatClient, ChatError, RequestEnvelope, ResponseEnvelope, VERSION};
use gchat_core::chat_service::host::ensure_running_checked;
use gchat_core::chat_service::host::InstanceConfig;
use tauri::Manager;
use tauri_plugin_deep_link::DeepLinkExt;
use tauri_plugin_dialog::DialogExt;
use tokio::sync::Mutex;

pub(super) struct Attachment {
    pub(super) client: Mutex<Option<ChatClient>>,
    config: Result<InstanceConfig, ChatError>,
    instance: std::sync::OnceLock<String>,
    pub(super) updating: std::sync::atomic::AtomicBool,
}

#[tauri::command]
async fn chat_request(
    state: tauri::State<'_, Attachment>,
    envelope: RequestEnvelope,
) -> Result<ResponseEnvelope, ChatError> {
    let client = attached_checked(&state).await?;
    if envelope.version != VERSION
        || (!matches!(envelope.request, gchat_api::Request::Identify)
            && envelope.instance_id.as_deref() != Some(client.instance_id()))
    {
        return Err(ChatError {
            code: "instance".into(),
            message: "selected instance or version mismatch".into(),
        });
    }
    let response = match client.request_typed(envelope.request).await {
        Ok(response) => response,
        Err(error) => {
            if matches!(error.code.as_str(), "transport" | "timeout" | "unavailable") {
                *state.client.lock().await = None;
            }
            return Err(error);
        }
    };
    Ok(ResponseEnvelope {
        version: VERSION,
        instance_id: client.instance_id().into(),
        response,
    })
}

pub(super) async fn attached(state: &tauri::State<'_, Attachment>) -> Result<ChatClient, String> {
    attached_checked(state).await.map_err(|e| e.to_string())
}

async fn attached_checked(state: &Attachment) -> Result<ChatClient, ChatError> {
    if state.updating.load(std::sync::atomic::Ordering::SeqCst) {
        return Err(ChatError {
            code: "unavailable".into(),
            message: "GChat is restarting to activate an update".into(),
        });
    }
    let mut client = state.client.lock().await;
    if client.is_none() {
        {
            let retry_config;
            let config = match &state.config {
                Ok(config) => config,
                Err(_) => {
                    retry_config =
                        crate::startup::configuration(std::env::args_os()).map_err(|message| {
                            ChatError {
                                code: "host_configuration".into(),
                                message,
                            }
                        })?;
                    &retry_config
                }
            };
            let connected = ensure_running_checked(
                config,
                &std::env::current_exe().map_err(|e| ChatError {
                    code: "host_unavailable".into(),
                    message: e.to_string(),
                })?,
                false,
            )
            .await?;
            if state
                .instance
                .get()
                .is_some_and(|id| id != connected.instance_id())
            {
                return Err(ChatError {
                    code: "instance".into(),
                    message: "The selected instance changed. Reopen this view explicitly.".into(),
                });
            }
            let _ = state.instance.set(connected.instance_id().into());
            *client = Some(connected);
        }
    }
    Ok(client.as_ref().expect("initialized attachment").clone())
}

#[tauri::command]
async fn chat_rpc(
    state: tauri::State<'_, Attachment>,
    request: gcoms::rpc::Request,
) -> Result<gcoms::rpc::Reply, ChatError> {
    use gcoms::rpc::Transport;
    let client = attached_checked(&state).await?;
    if request.rpc != gcoms::rpc::WIRE_VERSION
        || request.instance != client.instance_id()
        || request.service != gchat_api::rpc::SERVICE
        || request.version != gchat_api::rpc::SERVICE_VERSION
    {
        return Err(ChatError {
            code: "instance".into(),
            message: "selected instance or service version mismatch".into(),
        });
    }
    let transport =
        gcoms::rpc::local::LocalTransport::new(gchat_api::rpc::endpoint_for(client.endpoint()));
    let reply = match transport.exchange(&request).await {
        Ok(reply) => reply,
        Err(error) => {
            // The next request may reattach. An uncertain mutation is never
            // replayed here; its existing operation handle owns recovery.
            *state.client.lock().await = None;
            return Err(ChatError {
                code: "transport".into(),
                message: error.to_string(),
            });
        }
    };
    request.check_reply(&reply).map_err(|e| ChatError {
        code: "instance".into(),
        message: e.to_string(),
    })?;
    Ok(reply)
}

#[tauri::command]
async fn chat_file_io(
    state: tauri::State<'_, Attachment>,
    request: tauri::ipc::Request<'_>,
) -> Result<tauri::ipc::Response, String> {
    let tauri::ipc::InvokeBody::Raw(frame) = request.body() else {
        return Err("Expected a binary file frame".into());
    };
    let bytes = attached(&state).await?.file_io(frame.clone()).await?;
    Ok(tauri::ipc::Response::new(bytes))
}

#[tauri::command]
async fn chat_file_save(
    app: tauri::AppHandle,
    state: tauri::State<'_, Attachment>,
    id: String,
) -> Result<String, String> {
    let client = attached(&state).await?;
    let snapshot = client.files_for(&id).await?;
    let file = snapshot
        .files
        .iter()
        .find(|f| f.id == id && matches!(f.state, gchat_api::FileState::Complete))
        .ok_or("File is not complete")?;
    // The service validates names, but the native filesystem boundary also
    // requires exactly one normal component, including on Windows.
    let mut parts = std::path::Path::new(&file.name).components();
    if !matches!(parts.next(), Some(std::path::Component::Normal(_)))
        || parts.next().is_some()
        || file.name.contains(':')
        || file.name.ends_with('.')
        || file.name.ends_with(' ')
    {
        return Err("Invalid export name".into());
    }
    let (send, receive) = tokio::sync::oneshot::channel();
    app.dialog()
        .file()
        .set_file_name(&file.name)
        .save_file(move |path| {
            let _ = send.send(path);
        });
    let Some(destination) = receive.await.map_err(|_| "Save dialog closed")? else {
        return Ok(String::new());
    };
    let destination = destination.into_path().map_err(|e| e.to_string())?;
    client.save_file(&id, &destination).await?;
    Ok(destination.display().to_string())
}

#[tauri::command]
async fn chat_invitation_save(
    app: tauri::AppHandle,
    invitation: String,
) -> Result<Option<String>, String> {
    if invitation.is_empty() || invitation.len() > gchat_api::MAX_NETWORK_INVITATION_BYTES {
        return Err("Invalid invitation length".into());
    }
    save_invitation_bytes(app, "gchat-invitation.txt", invitation.into_bytes()).await
}

#[tauri::command]
async fn chat_invitation_card_save(
    app: tauri::AppHandle,
    bytes: Vec<u8>,
) -> Result<Option<String>, String> {
    if bytes.len() > 8 * 1024 * 1024 || !bytes.starts_with(b"\x89PNG\r\n\x1a\n") {
        return Err("Invalid invitation picture".into());
    }
    save_invitation_bytes(app, "gchat-invitation.png", bytes).await
}

async fn save_invitation_bytes(
    app: tauri::AppHandle,
    filename: &str,
    bytes: Vec<u8>,
) -> Result<Option<String>, String> {
    use std::io::Write;
    let (send, receive) = tokio::sync::oneshot::channel();
    app.dialog()
        .file()
        .set_file_name(filename)
        .save_file(move |path| {
            let _ = send.send(path);
        });
    let Some(path) = receive.await.map_err(|_| "Save dialog closed")? else {
        return Ok(None);
    };
    let path = path.into_path().map_err(|e| e.to_string())?;
    tokio::task::spawn_blocking(move || {
        let mut file = tempfile::NamedTempFile::new_in(path.parent().ok_or("Invalid destination")?)
            .map_err(|e| e.to_string())?;
        file.write_all(&bytes).map_err(|e| e.to_string())?;
        file.as_file().sync_all().map_err(|e| e.to_string())?;
        file.persist_noclobber(&path).map_err(|e| e.to_string())?;
        Ok(Some(path.display().to_string()))
    })
    .await
    .map_err(|e| e.to_string())?
}

fn forward_invitation(app: &tauri::AppHandle, args: Vec<String>) {
    if let Some(link) = args
        .into_iter()
        .skip(1)
        .find(|arg| arg.starts_with("gcoms://join#"))
    {
        // The UI/backend validate before any network work; never log link contents.
        if link.len() <= 174800 {
            app.deep_link()
                .handle_cli_arguments(["gchat-desktop".to_owned(), link].into_iter());
        }
    }
}

#[tauri::command]
fn chat_desktop_platform() -> &'static str {
    std::env::consts::OS
}

pub fn run() {
    // Never expose an interactive window until the one startup activation has
    // finished or been deferred. Updates found later only stage for next launch.
    let mut context = tauri::generate_context!();
    for window in &mut context.config_mut().app.windows {
        window.visible = false;
    }
    let mut builder = tauri::Builder::default();
    // Explicit separate profiles keep independent GUI processes; the receiving
    // service dispatches --interactive before reaching this builder.
    if !std::env::args_os()
        .any(|arg| arg == "--home" || arg.to_string_lossy().starts_with("--home="))
    {
        builder = builder.plugin(tauri_plugin_single_instance::init(|app, args, _| {
            forward_invitation(app, args);
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.unminimize();
                let _ = window.set_focus();
            }
        }));
    }
    builder
        .plugin(tauri_plugin_deep_link::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(|app| {
            #[cfg(not(target_os = "macos"))]
            if let Some(window) = app.get_webview_window("main") {
                window.set_decorations(false)?;
            }
            forward_invitation(
                app.handle(),
                std::env::args_os()
                    .filter_map(|arg| arg.into_string().ok())
                    .collect(),
            );
            let config =
                crate::startup::configuration(std::env::args_os()).map_err(|message| ChatError {
                    code: "host_configuration".into(),
                    message,
                });
            app.manage(Attachment {
                client: Mutex::new(None),
                instance: std::sync::OnceLock::new(),
                updating: std::sync::atomic::AtomicBool::new(false),
                config,
            });
            crate::updates::setup(app)?;
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            chat_desktop_platform,
            crate::updates::chat_update_activity,
            crate::updates::chat_update_status,
            crate::updates::chat_update_check,
            crate::updates::chat_update_install,
            chat_request,
            chat_rpc,
            chat_file_io,
            chat_file_save,
            chat_invitation_save,
            chat_invitation_card_save
        ])
        .run(context)
        .expect("gchat native application");
}

#[cfg(test)]
mod attachment_tests {
    use super::*;
    use std::sync::{atomic::AtomicBool, OnceLock};
    use std::time::Duration;

    fn state(updating: bool) -> Attachment {
        Attachment {
            client: Mutex::new(None),
            config: Err(ChatError {
                code: "host_configuration".into(),
                message: "This test must not select or start a host".into(),
            }),
            instance: OnceLock::new(),
            updating: AtomicBool::new(updating),
        }
    }

    #[tokio::test(start_paused = true)]
    async fn attachment_deadline_includes_an_existing_background_waiter() {
        let state = state(false);
        let held = state.client.lock().await;
        let started = tokio::time::Instant::now();
        let outcome = tokio::time::timeout(Duration::from_secs(31), attached_checked(&state))
            .await
            .expect("waiting for a prior attachment must share the 30-second startup deadline");
        let error = match outcome {
            Err(error) => error,
            Ok(_) => panic!("a blocked attachment cannot return a client"),
        };
        assert_eq!(error.code, "host_unavailable");
        assert!(started.elapsed() <= Duration::from_secs(30));
        assert!(held.is_none() && state.instance.get().is_none());
        drop(held);
        assert!(
            state.client.try_lock().is_ok(),
            "timed-out waiter must release its queue slot"
        );
    }

    #[tokio::test(start_paused = true)]
    async fn update_activation_refusal_does_not_wait_for_attachment() {
        let state = state(true);
        let _held = state.client.lock().await;
        let started = tokio::time::Instant::now();
        let outcome = tokio::time::timeout(Duration::from_secs(1), attached_checked(&state))
            .await
            .expect("update activation must reject immediately");
        let error = match outcome {
            Err(error) => error,
            Ok(_) => panic!("activation cannot expose a new client"),
        };
        assert_eq!(error.code, "unavailable");
        assert_eq!(started.elapsed(), Duration::ZERO);
    }
}
