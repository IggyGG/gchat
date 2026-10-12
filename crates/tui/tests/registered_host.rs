#![cfg(target_os = "linux")]

use gchat_api::{fleet::FleetConfig, ChatClient, Request, RequestEnvelope, Response, VERSION};
use gchat_core::chat_service::{
    host::{ensure_running_checked, InstanceConfig, InstanceHost},
    ChatEndpoint,
};
use gcoms::sdk::{
    ipc::Capability,
    machine::{ComponentCredentials, ComponentRegistration, MachineRegistry},
};
use std::{
    path::{Path, PathBuf},
    time::Duration,
};

const SECRET: &str = "registered-host-fixture";

async fn unlock(host: &InstanceHost, create: bool) -> gchat_api::Snapshot {
    let response = host
        .dispatch(RequestEnvelope {
            version: VERSION,
            instance_id: Some(host.instance_id().into()),
            request: Request::Unlock {
                passphrase: SECRET.into(),
                create,
            },
        })
        .await
        .response;
    match response {
        Response::Snapshot { snapshot } => snapshot,
        other => panic!("fixture unlock: {other:?}"),
    }
}

async fn fixture(home: &Path) -> (InstanceConfig, String) {
    gchat_core::private_fs::make_private(home, true).unwrap();
    let mut config = InstanceConfig::from_home(Some(home)).unwrap();
    config.local_fixture = true;
    config.gc2_carrier = false;
    config.listen = "127.0.0.1:0".parse().unwrap();
    config.network_recovery = false;
    config.relay_urls.clear();
    let personal = InstanceHost::new(config.clone()).unwrap();
    let safety = unlock(&personal, true).await.instance.safety_number;
    personal.flush().await.unwrap();
    drop(personal);
    let fleet = FleetConfig {
        version: 1,
        safety_number: safety.clone(),
        primary_component: [1; 16],
        registry: MachineRegistry {
            version: 1,
            components: vec![ComponentRegistration {
                credentials: ComponentCredentials {
                    component_id: [2; 16],
                    token: [7; 32],
                },
                capabilities: vec![Capability::IdentityRead],
                peers: vec![],
                files: None,
            }],
        },
    };
    let path = home.join("fleet.json");
    std::fs::write(&path, serde_json::to_vec(&fleet).unwrap()).unwrap();
    gchat_core::private_fs::make_private(&path, false).unwrap();
    config.fleet_config = Some(path);
    let scoped = InstanceHost::new(config.clone()).unwrap();
    assert_eq!(unlock(&scoped, false).await.instance.safety_number, safety);
    scoped.flush().await.unwrap();
    drop(scoped);
    (config, safety)
}

fn server_pid(endpoint: &Path) -> Option<i32> {
    let stream = std::os::unix::net::UnixStream::connect(endpoint).ok()?;
    stream.set_nonblocking(true).ok()?;
    tokio::net::UnixStream::from_std(stream)
        .ok()?
        .peer_cred()
        .ok()?
        .pid()
}

struct Worker {
    endpoint: PathBuf,
    pid: i32,
}
impl Worker {
    async fn stop(self) {
        let endpoint = self.endpoint.clone();
        drop(self);
        tokio::time::timeout(Duration::from_secs(10), async {
            while server_pid(&endpoint).is_some() {
                tokio::time::sleep(Duration::from_millis(20)).await;
            }
        })
        .await
        .expect("owned daemon shuts down orderly");
    }
}
impl Drop for Worker {
    fn drop(&mut self) {
        // Only the process still serving this owned disposable socket is signalled.
        if server_pid(&self.endpoint) == Some(self.pid) {
            let _ = std::process::Command::new("kill")
                .args(["-TERM", &self.pid.to_string()])
                .status();
        }
    }
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn concurrent_cold_launches_recover_the_same_scoped_daemon_without_fleet_flags() {
    let dir = tempfile::tempdir().unwrap();
    let (config, safety) = fixture(dir.path()).await;
    let selected = InstanceConfig::from_home(Some(dir.path())).unwrap();
    let executable = Path::new(env!("CARGO_BIN_EXE_gchat"));
    let (one, two) = tokio::join!(
        ensure_running_checked(&selected, executable, true),
        ensure_running_checked(&selected, executable, true),
    );
    let one = one.unwrap_or_else(|error| panic!("first launch: {error}"));
    let worker = Worker {
        endpoint: selected.chat_endpoint(),
        pid: server_pid(&selected.chat_endpoint()).unwrap(),
    };
    let two = two.unwrap_or_else(|error| panic!("second launch: {error}"));
    assert_eq!(one.instance_id(), two.instance_id());
    let Response::Snapshot { snapshot } = one
        .request(Request::Unlock {
            passphrase: SECRET.into(),
            create: false,
        })
        .await
        .unwrap()
    else {
        panic!("retained daemon unlock");
    };
    assert_eq!(snapshot.instance.safety_number, safety);
    assert_eq!(server_pid(two.endpoint()), Some(worker.pid));
    let registration = std::fs::read(config.archive.with_extension("host.json")).unwrap();
    one.request(Request::Disconnect).await.unwrap();
    drop((one, two));
    worker.stop().await;
    assert_eq!(
        std::fs::read(config.archive.with_extension("host.json")).unwrap(),
        registration
    );

    let reopened = InstanceConfig::from_home(Some(dir.path())).unwrap();
    let client = ensure_running_checked(&reopened, executable, true)
        .await
        .unwrap();
    let worker = Worker {
        endpoint: reopened.chat_endpoint(),
        pid: server_pid(&reopened.chat_endpoint()).unwrap(),
    };
    let Response::Snapshot { snapshot } = client
        .request(Request::Unlock {
            passphrase: SECRET.into(),
            create: false,
        })
        .await
        .unwrap()
    else {
        panic!("second retained daemon unlock");
    };
    assert_eq!(snapshot.instance.safety_number, safety);
    assert_eq!(snapshot.instance.id, client.instance_id());
    client.request(Request::Disconnect).await.unwrap();
    drop(client);
    worker.stop().await;
}

#[tokio::test]
async fn configured_host_pid_and_legacy_clients_keep_their_attachment_boundaries() {
    // Existing non-scoped clients can still read the new host handshake.
    let dir = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(dir.path(), true).unwrap();
    let mut config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    config.local_fixture = true;
    config.network_recovery = false;
    let client = ensure_running_checked(&config, Path::new(env!("CARGO_BIN_EXE_gchat")), true)
        .await
        .unwrap();
    let worker = Worker {
        endpoint: config.chat_endpoint(),
        pid: server_pid(&config.chat_endpoint()).unwrap(),
    };
    let legacy = ChatClient::connect(client.endpoint(), Some(client.instance_id()))
        .await
        .unwrap();
    assert_eq!(legacy.instance_id(), client.instance_id());
    assert!(!config.profile.exists());
    assert!(!config.archive.exists());
    drop((legacy, client));
    worker.stop().await;
}
