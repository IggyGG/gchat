//! Owns the optional fleet socket without opening another copy of the profile.
use crate::{private_fs, runtime::ProtocolRuntime};
use gchat_api::fleet::{FleetConfig, CONFIG_LIMIT};
use gcoms::sdk::{local::LocalListener, LocalEndpoint};
use std::{
    io::Read,
    path::{Path, PathBuf},
    time::Duration,
};
use tokio::sync::watch;
use zeroize::Zeroizing;

pub(super) fn load(path: &Path) -> Result<(FleetConfig, Zeroizing<Vec<u8>>), String> {
    if !path.is_absolute()
        || path
            .components()
            .any(|p| matches!(p, std::path::Component::ParentDir))
    {
        return Err("fleet configuration must have an absolute path".into());
    }
    private_fs::validate_private_parent(path, "fleet configuration")?;
    private_fs::validate_private_file(path, "fleet configuration")?;
    let mut bytes = Zeroizing::new(Vec::new());
    std::fs::File::open(path)
        .map_err(|e| e.to_string())?
        .take(CONFIG_LIMIT + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    if bytes.len() as u64 > CONFIG_LIMIT {
        return Err("fleet configuration exceeds bound".into());
    }
    let config: FleetConfig = serde_json::from_slice(&bytes).map_err(|e| e.to_string())?;
    config.validate()?;
    Ok((config, bytes))
}

pub(super) struct Transport {
    path: PathBuf,
    endpoint: PathBuf,
    initial: FleetConfig,
    runtime: ProtocolRuntime,
    running: Option<(watch::Sender<bool>, tokio::task::JoinHandle<()>)>,
}

impl Transport {
    pub(super) fn new(
        path: PathBuf,
        endpoint: PathBuf,
        initial: FleetConfig,
        runtime: ProtocolRuntime,
    ) -> Result<Self, String> {
        if runtime.0.embedded_runtime().is_none() {
            return Err("fleet requires an in-process GChat runtime".into());
        }
        private_fs::validate_private_parent(&endpoint, "fleet socket")?;
        Ok(Self {
            path,
            endpoint,
            initial,
            runtime,
            running: None,
        })
    }

    pub(super) fn resume(&mut self) {
        if self.running.is_some() {
            return;
        }
        let (stop, receiver) = watch::channel(false);
        let path = self.path.clone();
        let endpoint = self.endpoint.clone();
        let initial = self.initial.clone();
        let runtime = self.runtime.clone();
        self.running = Some((
            stop,
            tokio::spawn(run(path, endpoint, initial, runtime, receiver)),
        ));
    }

    pub(super) async fn pause(&mut self) {
        if let Some((stop, task)) = self.running.take() {
            stop.send_replace(true);
            let _ = task.await;
        }
    }
}

async fn run(
    path: PathBuf,
    endpoint: PathBuf,
    initial: FleetConfig,
    runtime: ProtocolRuntime,
    mut stop: watch::Receiver<bool>,
) {
    let mut last_error = None;
    while !*stop.borrow() {
        let result = serve_generation(&path, &endpoint, &initial, &runtime, &mut stop).await;
        if let Err(error) = result {
            if last_error.as_ref() != Some(&error) {
                eprintln!("gchat fleet unavailable: {error}");
            }
            last_error = Some(error);
        } else {
            last_error = None;
        }
        if *stop.borrow() {
            break;
        }
        tokio::select! { _ = stop.changed() => break, _ = tokio::time::sleep(Duration::from_secs(1)) => {} }
    }
}

async fn serve_generation(
    path: &Path,
    endpoint: &Path,
    initial: &FleetConfig,
    runtime: &ProtocolRuntime,
    stop: &mut watch::Receiver<bool>,
) -> Result<(), String> {
    let (config, bytes) = load(path)?;
    if !initial.same_partition(&config) {
        return Err(
            "fleet configuration changed the retained identity or component partition".into(),
        );
    }
    let endpoint = LocalEndpoint::new(endpoint);
    let listener = LocalListener::bind(&endpoint).map_err(|e| e.to_string())?;
    let sdk = runtime
        .0
        .embedded_runtime()
        .ok_or("fleet runtime is unavailable")?
        .sdk_client();
    let (shutdown, mut stopped) = watch::channel(false);
    let server = gcoms::sdk::ipc::serve_machine_on_listener_until(
        listener,
        sdk,
        config.registry,
        async move {
            let _ = stopped.changed().await;
        },
    );
    tokio::pin!(server);
    let mut check = tokio::time::interval(Duration::from_secs(1));
    let result = loop {
        tokio::select! {
            result = &mut server => break result.map_err(|e| e.to_string()),
            _ = stop.changed() => {
                shutdown.send_replace(true);
                break server.await.map_err(|e| e.to_string());
            },
            _ = check.tick() => {
                // Drain old credentials before installing changed permissions.
                if !load(path).is_ok_and(|(next, current)| initial.same_partition(&next) && *current == *bytes) {
                    shutdown.send_replace(true);
                    break server.await.map_err(|e| e.to_string());
                }
            }
        }
    };
    let cleanup = endpoint.cleanup().map_err(|e| e.to_string());
    result.and(cleanup)
}
