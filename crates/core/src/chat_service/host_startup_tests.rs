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
