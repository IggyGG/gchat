use super::*;
use crate::chat_service::{self, host::InstanceHost, ChatEndpoint};
use gchat_api::fleet::FleetConfig;
use gcoms::sdk::machine::{ComponentCredentials, ComponentRegistration, MachineRegistry};
use tokio::sync::watch;

fn scoped(config: &mut InstanceConfig) {
    let fleet = FleetConfig {
        version: 1,
        safety_number: "locked fixture identity".into(),
        primary_component: [1; 16],
        registry: MachineRegistry {
            version: 1,
            components: vec![ComponentRegistration {
                credentials: ComponentCredentials {
                    component_id: [2; 16],
                    token: [7; 32],
                },
                capabilities: vec![gcoms::sdk::ipc::Capability::IdentityRead],
                peers: vec![],
                files: None,
            }],
        },
    };
    let path = config.archive.with_extension("fleet.json");
    crate::store::atomic_write(&path, &serde_json::to_vec(&fleet).unwrap(), true).unwrap();
    config.fleet_config = Some(path);
}

async fn serve(
    host: std::sync::Arc<InstanceHost>,
    endpoint: std::path::PathBuf,
) -> (
    watch::Sender<bool>,
    tokio::task::JoinHandle<Result<(), String>>,
) {
    let (stop, receiver) = watch::channel(false);
    let selected = endpoint.clone();
    let server = tokio::spawn(async move { chat_service::serve(host, &selected, receiver).await });
    tokio::time::timeout(Duration::from_secs(10), async {
        loop {
            if gcoms::sdk::local::connect(&LocalEndpoint::new(&endpoint))
                .await
                .is_ok()
            {
                break;
            }
            assert!(
                !server.is_finished(),
                "fixture host exited before readiness"
            );
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
    })
    .await
    .expect("locked IPC fixture readiness");
    (stop, server)
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn read_only_diagnostics_inspect_the_locked_host_without_attachment_handles() {
    let dir = tempfile::tempdir().unwrap();
    private_fs::make_private(dir.path(), true).unwrap();
    let mut config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    scoped(&mut config);
    let host = InstanceHost::new(config.clone()).unwrap();
    let instance = host.instance_id().to_owned();
    let binding = host_registration::capability(&config, &instance).unwrap();
    host_registration::publish(&config, &instance, &binding).unwrap();
    let registration = std::fs::read(config.archive.with_extension("host.json")).unwrap();
    let (stop, server) = serve(host.clone(), config.chat_endpoint()).await;
    let report = chat_service::host_diagnostics::inspect(Some(dir.path()))
        .await
        .unwrap();
    assert_eq!(report.instance_id.as_deref(), Some(instance.as_str()));
    assert_eq!(report.mode, "fleet");
    assert!(report.local_ready);
    assert_eq!(report.archive_locked, Some(true));
    assert_eq!(report.protocol_locked, Some(true));
    assert!(report.error_code.is_none());
    assert!(host.running.lock().await.is_none());
    assert!(!config
        .protocol_socket
        .with_extension("chat.handles")
        .exists());
    assert!(!config.profile.exists() && !config.archive.exists());
    assert_eq!(
        std::fs::read(config.archive.with_extension("host.json")).unwrap(),
        registration
    );
    let json = serde_json::to_string(&report).unwrap();
    assert!(!json.contains("locked fixture identity") && !json.contains("\"token\""));
    stop.send_replace(true);
    server.await.unwrap().unwrap();
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn read_only_diagnostics_refuse_a_wrong_host_without_allocating_handles() {
    let dir = tempfile::tempdir().unwrap();
    private_fs::make_private(dir.path(), true).unwrap();
    let mut config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    let host = InstanceHost::new(config.clone()).unwrap();
    let instance = host.instance_id().to_owned();
    let (stop, server) = serve(host, config.chat_endpoint()).await;
    scoped(&mut config);
    let binding = host_registration::capability(&config, &instance).unwrap();
    host_registration::publish(&config, &instance, &binding).unwrap();
    let report = chat_service::host_diagnostics::inspect(Some(dir.path()))
        .await
        .unwrap();
    assert_eq!(report.error_code, Some("host_mismatch"));
    assert!(!report.local_ready);
    assert!(report.host_build.is_none());
    assert!(!config
        .protocol_socket
        .with_extension("chat.handles")
        .exists());
    assert!(!config.profile.exists() && !config.archive.exists());
    stop.send_replace(true);
    server.await.unwrap().unwrap();
}

#[tokio::test]
async fn read_only_diagnostics_never_initialize_or_repair_missing_or_bad_metadata() {
    let dir = tempfile::tempdir().unwrap();
    let home = dir.path().join("new identity λ");
    let report = chat_service::host_diagnostics::inspect(Some(&home))
        .await
        .unwrap();
    assert!(report.instance_id.is_none() && !report.local_ready);
    assert!(!home.exists());
    std::fs::create_dir(&home).unwrap();
    private_fs::make_private(&home, true).unwrap();
    let metadata = home.join("chat.instance.json");
    for bytes in [b"private-diagnostic-sentinel".to_vec(), vec![b'x'; 4097]] {
        std::fs::write(&metadata, &bytes).unwrap();
        private_fs::make_private(&metadata, false).unwrap();
        let report = chat_service::host_diagnostics::inspect(Some(&home))
            .await
            .unwrap();
        assert_eq!(report.error_code, Some("host_configuration"));
        assert!(report.instance_id.is_none());
        assert!(!serde_json::to_string(&report)
            .unwrap()
            .contains("private-diagnostic-sentinel"));
        assert_eq!(std::fs::read(&metadata).unwrap(), bytes);
        assert_eq!(std::fs::read_dir(&home).unwrap().count(), 1);
    }
}

#[cfg(unix)]
#[tokio::test]
async fn read_only_diagnostics_bound_stalled_handshakes_and_keep_native_paths() {
    use std::os::unix::{ffi::OsStringExt, fs::PermissionsExt};
    let dir = tempfile::tempdir().unwrap();
    let home = dir
        .path()
        .join(std::ffi::OsString::from_vec(b"native-\xff".to_vec()));
    std::fs::create_dir(&home).unwrap();
    private_fs::make_private(&home, true).unwrap();
    let config = InstanceConfig::from_home(Some(&home)).unwrap();
    let host = InstanceHost::new(config.clone()).unwrap();
    let _listener = std::os::unix::net::UnixListener::bind(config.chat_endpoint()).unwrap();
    std::fs::set_permissions(
        config.chat_endpoint(),
        std::fs::Permissions::from_mode(0o600),
    )
    .unwrap();
    let started = std::time::Instant::now();
    let report = chat_service::host_diagnostics::inspect(Some(&home))
        .await
        .unwrap();
    assert!(started.elapsed() < Duration::from_secs(5));
    assert_eq!(report.error_code, Some("host_unavailable"));
    assert_eq!(report.instance_id.as_deref(), Some(host.instance_id()));
    assert!(report
        .profile
        .get("unix")
        .and_then(|value| value.as_array())
        .is_some());
    assert!(!config
        .protocol_socket
        .with_extension("chat.handles")
        .exists());
    assert!(!config.profile.exists() && !config.archive.exists());
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn wrong_running_host_is_refused_before_attachment_state_or_profile_open() {
    let dir = tempfile::tempdir().unwrap();
    private_fs::make_private(dir.path(), true).unwrap();
    let mut config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    let host = InstanceHost::new(config.clone()).unwrap();
    let instance = host.instance_id().to_owned();
    let (stop, server) = serve(host, config.chat_endpoint()).await;
    scoped(&mut config);
    let binding = host_registration::capability(&config, &instance).unwrap();
    host_registration::publish(&config, &instance, &binding).unwrap();
    let failure = ensure(&config, Path::new("missing-executable"), false)
        .await
        .unwrap_err();
    assert_eq!(failure.code, "host_mismatch");
    assert!(!config.profile.exists());
    assert!(!config.archive.exists());
    assert!(!config
        .protocol_socket
        .with_extension("chat.handles")
        .exists());
    stop.send_replace(true);
    server.await.unwrap().unwrap();
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn concurrent_views_attach_to_the_same_registered_locked_host() {
    let dir = tempfile::tempdir().unwrap();
    private_fs::make_private(dir.path(), true).unwrap();
    let mut config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    scoped(&mut config);
    let host = InstanceHost::new(config.clone()).unwrap();
    let instance = host.instance_id().to_owned();
    let binding = host_registration::capability(&config, &instance).unwrap();
    host_registration::publish(&config, &instance, &binding).unwrap();
    let (stop, server) = serve(host, config.chat_endpoint()).await;
    let restored = InstanceConfig::from_home(Some(dir.path())).unwrap();
    let (one, two) = tokio::join!(
        ensure(&restored, Path::new("missing-executable"), false),
        ensure(&restored, Path::new("missing-executable"), false),
    );
    assert_eq!(one.unwrap().instance_id(), instance);
    assert_eq!(two.unwrap().instance_id(), instance);
    assert!(!config.profile.exists());
    assert!(!config.archive.exists());
    stop.send_replace(true);
    server.await.unwrap().unwrap();
}

#[cfg(unix)]
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn managed_handshake_refuses_another_process_before_creating_handles() {
    let dir = tempfile::tempdir().unwrap();
    private_fs::make_private(dir.path(), true).unwrap();
    let config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    let host = InstanceHost::new(config.clone()).unwrap();
    let instance = host.instance_id().to_owned();
    let (stop, server) = serve(host, config.chat_endpoint()).await;
    let result = ChatClient::connect_owned_host(
        &config.chat_endpoint(),
        Some(&instance),
        None,
        rustix::process::getuid().as_raw(),
        Some(std::process::id() + 1),
    )
    .await;
    assert!(result.unwrap_err().contains("registered host process"));
    assert!(!config
        .protocol_socket
        .with_extension("chat.handles")
        .exists());
    stop.send_replace(true);
    server.await.unwrap().unwrap();
}

#[cfg(unix)]
#[test]
fn launch_lock_does_not_follow_a_symlink() {
    let dir = tempfile::tempdir().unwrap();
    private_fs::make_private(dir.path(), true).unwrap();
    let config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    let target = dir.path().join("untouched");
    std::os::unix::fs::symlink(&target, config.archive.with_extension("launch.lock")).unwrap();
    assert_eq!(lock_file(&config).unwrap_err().code, "host_configuration");
    assert!(!target.exists());
}
