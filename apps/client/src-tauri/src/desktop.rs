use gchat_api::{ChatClient, RequestEnvelope, ResponseEnvelope, VERSION};
use gchat_core::chat_service::host::ensure_running;
use gchat_core::chat_service::host::InstanceConfig;
use tauri::Manager;
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
    use std::io::Write;
    if invitation.is_empty() || invitation.len() > gchat_api::MAX_NETWORK_INVITATION_BYTES {
        return Err("Invalid invitation length".into());
    }
    let (send, receive) = tokio::sync::oneshot::channel();
    app.dialog()
        .file()
        .set_file_name("gchat-invitation.txt")
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
        file.write_all(invitation.as_bytes())
            .map_err(|e| e.to_string())?;
        file.as_file().sync_all().map_err(|e| e.to_string())?;
        file.persist_noclobber(&path).map_err(|e| e.to_string())?;
        Ok(Some(path.display().to_string()))
    })
    .await
    .map_err(|e| e.to_string())?
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let config = crate::startup::configuration(std::env::args_os())
                .map_err(std::io::Error::other)?;
            app.manage(Attachment {
                client: Mutex::new(None),
                config,
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            chat_request,
            chat_rpc,
            chat_file_io,
            chat_file_save,
            chat_invitation_save
        ])
        .run(tauri::generate_context!())
        .expect("gchat native application");
}
