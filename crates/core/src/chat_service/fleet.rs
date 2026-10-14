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
    let (listener, _server_lock) = bind_endpoint(&endpoint)?;
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

fn bind_endpoint(
    endpoint: &LocalEndpoint,
) -> Result<(LocalListener, Option<std::fs::File>), String> {
    // Match the chat endpoint's lifecycle: hold one owner through preparation,
    // serving and cleanup. Only the existing guarded SDK preparation may reclaim
    // a refused stale socket; live listeners and non-socket paths stay intact.
    #[cfg(unix)]
    let owner = Some(crate::store::acquire_lock(endpoint.path())?);
    #[cfg(not(unix))]
    let owner = None;
    endpoint.prepare_server().map_err(|e| e.to_string())?;
    let listener = LocalListener::bind(endpoint).map_err(|e| e.to_string())?;
    Ok((listener, owner))
}

#[cfg(all(test, unix))]
mod tests {
    use super::*;
    use std::os::unix::{fs::MetadataExt, net::UnixListener};

    #[tokio::test]
    async fn stale_socket_recovery_keeps_one_generation_owner() {
        let directory = tempfile::tempdir().unwrap();
        private_fs::make_private(directory.path(), true).unwrap();
        let endpoint = LocalEndpoint::new(directory.path().join("fleet.sock"));
        drop(UnixListener::bind(endpoint.path()).unwrap());
        assert!(endpoint.path().exists());
        let (listener, owner) = bind_endpoint(&endpoint).unwrap();
        assert!(owner.is_some());
        assert!(bind_endpoint(&endpoint).is_err());
        assert!(gcoms::sdk::local::connect(&endpoint).await.is_ok());
        drop(listener);
        // Dropping the listener alone does not release generation ownership.
        assert!(bind_endpoint(&endpoint).is_err());
        drop(owner);
        let (replacement, _owner) = bind_endpoint(&endpoint).unwrap();
        assert!(gcoms::sdk::local::connect(&endpoint).await.is_ok());
        drop(replacement);
        endpoint.cleanup().unwrap();
    }

    #[tokio::test]
    async fn active_listener_without_a_generation_lock_is_not_replaced() {
        let directory = tempfile::tempdir().unwrap();
        private_fs::make_private(directory.path(), true).unwrap();
        let endpoint = LocalEndpoint::new(directory.path().join("fleet.sock"));
        let listener = UnixListener::bind(endpoint.path()).unwrap();
        let original = std::fs::symlink_metadata(endpoint.path()).unwrap();
        assert!(bind_endpoint(&endpoint).is_err());
        let retained = std::fs::symlink_metadata(endpoint.path()).unwrap();
        assert_eq!(
            (retained.dev(), retained.ino()),
            (original.dev(), original.ino())
        );
        assert!(gcoms::sdk::local::connect(&endpoint).await.is_ok());
        drop(listener);
        endpoint.cleanup().unwrap();
    }

    #[tokio::test]
    async fn regular_files_and_symlinks_are_preserved() {
        let directory = tempfile::tempdir().unwrap();
        private_fs::make_private(directory.path(), true).unwrap();
        let endpoint = LocalEndpoint::new(directory.path().join("fleet.sock"));
        std::fs::write(endpoint.path(), b"retained input").unwrap();
        assert!(bind_endpoint(&endpoint).is_err());
        assert_eq!(std::fs::read(endpoint.path()).unwrap(), b"retained input");
        let target = directory.path().join("retained");
        std::fs::rename(endpoint.path(), &target).unwrap();
        std::os::unix::fs::symlink(&target, endpoint.path()).unwrap();
        assert!(bind_endpoint(&endpoint).is_err());
        assert!(std::fs::symlink_metadata(endpoint.path())
            .unwrap()
            .file_type()
            .is_symlink());
        assert_eq!(std::fs::read(target).unwrap(), b"retained input");
    }
}
