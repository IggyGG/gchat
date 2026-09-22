#![cfg(any(unix, windows))]

use gchat_api::{fleet::FleetConfig, Request, RequestEnvelope, Response, VERSION};
use gchat_core::chat_service::{
    host::{InstanceConfig, InstanceHost},
    ChatEndpoint,
};
use gcoms::sdk::{
    ipc::{Capability, IpcClient as SdkClient},
    machine::{ComponentCredentials, ComponentRegistration, MachineRegistry},
    GcClient,
};
use std::{path::Path, time::Duration};

fn save(path: &Path, config: &FleetConfig) {
    let mut file = tempfile::NamedTempFile::new_in(path.parent().unwrap()).unwrap();
    gcoms::sdk::private_fs::make_private(file.path(), false).unwrap();
    serde_json::to_writer(file.as_file_mut(), config).unwrap();
    file.as_file_mut().sync_all().unwrap();
    file.persist(path).unwrap();
}

async fn attach(endpoint: &Path, credentials: &ComponentCredentials) -> SdkClient {
    tokio::time::timeout(Duration::from_secs(15), async {
        loop {
            if let Ok(client) = SdkClient::connect_component(
                endpoint,
                "fleet-test",
                vec![Capability::IdentityRead],
                credentials.clone(),
            )
            .await
            {
                return client;
            }
            tokio::time::sleep(Duration::from_millis(50)).await;
        }
    })
    .await
    .expect("fleet endpoint becomes available")
}

async fn request(host: &InstanceHost, request: Request) -> Response {
    let response = host
        .dispatch(RequestEnvelope {
            version: VERSION,
            instance_id: Some(host.instance_id().into()),
            request,
        })
        .await
        .response;
    if let Response::Error { code, message } = &response {
        eprintln!("fleet fixture request: {code}: {message}");
    }
    response
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn fleet_attachment_preserves_identity_reloads_credentials_and_drains_on_lock() {
    let dir = tempfile::tempdir().unwrap();
    gcoms::sdk::private_fs::make_private(dir.path(), true).unwrap();
    let mut config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    config.local_fixture = true;
    config.gc2_carrier = false;
    config.listen = "127.0.0.1:0".parse().unwrap();
    config.relay_urls.clear();
    config.network_recovery = false;
    let original = InstanceHost::new(config.clone()).unwrap();
    let Response::Snapshot { snapshot } = request(
        &original,
        Request::Unlock {
            passphrase: "fleet-test-passphrase".into(),
            create: true,
        },
    )
    .await
    else {
        panic!("create personal GChat fixture");
    };
    let safety = snapshot.instance.safety_number;
    original.flush().await.unwrap();
    drop(original);
    let credentials = ComponentCredentials {
        component_id: [2; 16],
        token: [7; 32],
    };
    let mut fleet = FleetConfig {
        version: 1,
        safety_number: safety.clone(),
        primary_component: [1; 16],
        registry: MachineRegistry {
            version: 1,
            components: vec![ComponentRegistration {
                credentials: credentials.clone(),
                capabilities: vec![Capability::IdentityRead],
                peers: Vec::new(),
                files: None,
            }],
        },
    };
    let path = dir.path().join("fleet.json");
    save(&path, &fleet);
    config.fleet_config = Some(path.clone());
    let socket = config.protocol_socket.with_extension("fleet");
    let host = InstanceHost::new(config.clone()).unwrap();
    assert!(matches!(
        request(
            &host,
            Request::Unlock {
                passphrase: "fleet-test-passphrase".into(),
                create: false
            }
        )
        .await,
        Response::Snapshot { .. }
    ));
    let old = attach(&socket, &credentials).await;
    assert_eq!(old.identity().safety_number, safety);
    assert!(
        SdkClient::connect(&socket, "unregistered", vec![Capability::IdentityRead])
            .await
            .is_err()
    );
    assert!(old
        .shell_request(gcoms::sdk::shell::ShellRequest::Health)
        .await
        .is_err());

    fleet.registry.components[0].credentials.token = [8; 32];
    save(&path, &fleet);
    let current = attach(&socket, &fleet.registry.components[0].credentials).await;
    assert_eq!(current.identity().safety_number, safety);
    assert!(old.refresh_identity().await.is_err());
    assert!(
        matches!(request(&host, Request::Lock).await, Response::Instance { instance } if instance.locked)
    );
    assert!(current.refresh_identity().await.is_err());
    assert!(!socket.exists());
    assert!(matches!(
        request(
            &host,
            Request::Unlock {
                passphrase: "fleet-test-passphrase".into(),
                create: false
            }
        )
        .await,
        Response::Snapshot { .. }
    ));
    let unlocked = attach(&socket, &fleet.registry.components[0].credentials).await;
    assert_eq!(unlocked.identity().safety_number, safety);
    drop((old, current, unlocked));
    host.flush().await.unwrap();
    drop(host);
    let restarted = InstanceHost::new(config).unwrap();
    assert!(matches!(
        request(
            &restarted,
            Request::Unlock {
                passphrase: "fleet-test-passphrase".into(),
                create: false
            }
        )
        .await,
        Response::Snapshot { .. }
    ));
    let retained = attach(&socket, &fleet.registry.components[0].credentials).await;
    assert_eq!(retained.identity().safety_number, safety);
    drop(retained);
    restarted.flush().await.unwrap();
}
