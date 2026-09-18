use gchat_api::{ChatClient, RequestEnvelope, ResponseEnvelope, VERSION};
#[cfg(not(target_os = "android"))]
use gchat_core::chat_service::host::ensure_running;
use gchat_core::chat_service::host::InstanceConfig;
use tauri::Manager;
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
        #[cfg(not(target_os = "android"))]
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
        #[cfg(target_os = "android")]
        {
            *client = Some(ChatClient::connect(&state.config.chat_endpoint(), None).await?);
        }
    }
    Ok(client.as_ref().expect("initialized attachment").clone())
}

#[tauri::command]
async fn chat_rpc(
    state: tauri::State<'_, Attachment>,
    request: gcoms_rpc::Request,
) -> Result<gcoms_rpc::Reply, String> {
    use gcoms_rpc::Transport;
    let client = attached(&state).await?;
    if request.rpc != gcoms_rpc::WIRE_VERSION
        || request.instance != client.instance_id()
        || request.service != gchat_api::rpc::SERVICE
        || request.version != gchat_api::rpc::SERVICE_VERSION
    {
        return Err("selected instance or service version mismatch".into());
    }
    let transport =
        gcoms_rpc::local::LocalTransport::new(gchat_api::rpc::endpoint_for(client.endpoint()));
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
    let snapshot = client
        .files(gchat_api::FileRequest::List { conversation: None })
        .await?;
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
    let destination = app
        .path()
        .download_dir()
        .map_err(|e| e.to_string())?
        .join(&file.name);
    client.save_file(&id, &destination).await?;
    Ok(destination.display().to_string())
}

#[cfg(target_os = "android")]
mod android;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            #[cfg(target_os = "android")]
            let home = Some(app.path().app_data_dir()?.join("files").join("instance"));
            #[cfg(not(target_os = "android"))]
            let home = {
                let mut args = std::env::args().skip(1);
                let mut home = None;
                while let Some(arg) = args.next() {
                    if arg == "--home" {
                        home = Some(std::path::PathBuf::from(
                            args.next().ok_or("--home requires a directory")?,
                        ));
                    } else {
                        return Err(format!("unknown client argument: {arg}").into());
                    }
                }
                home
            };
            let config =
                InstanceConfig::from_home(home.as_deref()).map_err(std::io::Error::other)?;
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
            chat_file_save
        ])
        .run(tauri::generate_context!())
        .expect("gchat native application");
}
