use gchat_api::{ChatClient, RequestEnvelope, ResponseEnvelope, VERSION};
use gchat_core::chat_service::host::ensure_running;
use gchat_core::chat_service::host::InstanceConfig;
use tauri::Manager;
use tauri_plugin_deep_link::DeepLinkExt;
use tauri_plugin_dialog::DialogExt;
use tokio::sync::Mutex;

struct Attachment {
    client: Mutex<Option<ChatClient>>,
    config: InstanceConfig,
}

#[tauri::command]
async fn chat_request(
    state: tauri::State<'_, Attachment>,
    envelope: RequestEnvelope,
) -> Result<ResponseEnvelope, String> {
    let client = attached(&state).await?;
    if envelope.version != VERSION
        || (!matches!(envelope.request, gchat_api::Request::Identify)
            && envelope.instance_id.as_deref() != Some(client.instance_id()))
    {
        return Err("selected instance or version mismatch".into());
    }
    let response = client.request(envelope.request).await?;
    Ok(ResponseEnvelope {
        version: VERSION,
        instance_id: client.instance_id().into(),
        response,
    })
}

async fn attached(state: &tauri::State<'_, Attachment>) -> Result<ChatClient, String> {
    let mut client = state.client.lock().await;
    if client.is_none() {
        {
            *client = Some(
                ensure_running(
                    &state.config,
                    &std::env::current_exe().map_err(|e| e.to_string())?,
                    false,
                )
                .await?,
            );
        }
    }
    Ok(client.as_ref().expect("initialized attachment").clone())
}

#[tauri::command]
async fn chat_rpc(
    state: tauri::State<'_, Attachment>,
    request: gcoms::rpc::Request,
) -> Result<gcoms::rpc::Reply, String> {
    use gcoms::rpc::Transport;
    let client = attached(&state).await?;
    if request.rpc != gcoms::rpc::WIRE_VERSION
        || request.instance != client.instance_id()
        || request.service != gchat_api::rpc::SERVICE
        || request.version != gchat_api::rpc::SERVICE_VERSION
    {
        return Err("selected instance or service version mismatch".into());
    }
    let transport =
        gcoms::rpc::local::LocalTransport::new(gchat_api::rpc::endpoint_for(client.endpoint()));
    let reply = transport
        .exchange(&request)
        .await
        .map_err(|e| e.to_string())?;
    request.check_reply(&reply).map_err(|e| e.to_string())?;
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
            let config = crate::startup::configuration(std::env::args_os())
                .map_err(std::io::Error::other)?;
            app.manage(Attachment {
                client: Mutex::new(None),
                config,
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            chat_desktop_platform,
            chat_request,
            chat_rpc,
            chat_file_io,
            chat_file_save,
            chat_invitation_save,
            chat_invitation_card_save
        ])
        .run(tauri::generate_context!())
        .expect("gchat native application");
}
