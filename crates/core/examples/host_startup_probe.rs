//! Native installed-host qualification: exercise the same startup path as the UI.
//! Arguments select an owner-controlled instance and its GChat executable; no secret.
use gchat_api::{Request, Response};
use gchat_core::chat_service::host::{ensure_running_checked, InstanceConfig};
use std::path::Path;

async fn run() -> Result<(), String> {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    if args.len() != 2 {
        return Err("usage: host_startup_probe INSTANCE_DIRECTORY GCHAT_EXECUTABLE".into());
    }
    let config = InstanceConfig::from_home(Some(Path::new(&args[0])))?;
    let client = ensure_running_checked(&config, Path::new(&args[1]), true)
        .await
        .map_err(|e| e.to_string())?;
    match client.request(Request::Identify).await? {
        Response::Instance { instance } => {
            println!(
                "{}",
                serde_json::to_string(&instance).map_err(|e| e.to_string())?
            );
            Ok(())
        }
        _ => Err("host identification returned an unexpected response".into()),
    }
}

#[tokio::main(flavor = "multi_thread", worker_threads = 2)]
async fn main() {
    if let Err(error) = run().await {
        eprintln!("{error}");
        std::process::exit(1);
    }
}
