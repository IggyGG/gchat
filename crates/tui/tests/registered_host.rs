#![cfg(target_os = "linux")]

use gchat_api::{fleet::FleetConfig, ChatClient, Request, RequestEnvelope, Response, VERSION};
use gchat_core::chat_service::{
    host::{ensure_running_checked, InstanceConfig, InstanceHost},
    ChatEndpoint,
};
use gcoms::sdk::{
    ipc::{Capability, IpcClient},
    machine::{ComponentCredentials, ComponentRegistration, MachineRegistry},
    GcClient,
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

fn retained_files(home: &Path) -> std::collections::BTreeMap<PathBuf, Vec<u8>> {
    let mut files = std::collections::BTreeMap::new();
    let mut pending = vec![home.to_path_buf()];
    while let Some(directory) = pending.pop() {
        for entry in std::fs::read_dir(directory).unwrap() {
            let entry = entry.unwrap();
            let kind = entry.file_type().unwrap();
            if kind.is_dir() {
                pending.push(entry.path());
            } else if kind.is_file() {
                files.insert(
                    entry.path().strip_prefix(home).unwrap().to_path_buf(),
                    std::fs::read(entry.path()).unwrap(),
                );
            }
        }
    }
    files
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn registered_host_diagnostics_are_read_only_before_unlock_or_service_start() {
    let dir = tempfile::tempdir().unwrap();
    let home = dir.path().join("retained fleet λ");
    std::fs::create_dir(&home).unwrap();
    let (mut config, _) = fixture(&home).await;
    config.managed_service = Some(format!("gchat-diagnostic-{}.service", std::process::id()));
    let host = InstanceHost::new(config.clone()).unwrap();
    let identity = unlock(&host, false).await.instance;
    host.flush().await.unwrap();
    drop(host);

    for missing_fleet in [false, true] {
        if missing_fleet {
            std::fs::remove_file(config.fleet_config.as_ref().unwrap()).unwrap();
        }
        let before = retained_files(&home);
        let output = tokio::time::timeout(
            Duration::from_secs(10),
            tokio::process::Command::new(env!("CARGO_BIN_EXE_gchat"))
                .args(["--home"])
                .arg(&home)
                .args(["paths", "--json"])
                .kill_on_drop(true)
                .output(),
        )
        .await
        .expect("read-only diagnostics must be bounded")
        .unwrap();
        assert!(
            output.status.success(),
            "saved-host diagnostic record unavailable: {}",
            String::from_utf8_lossy(&output.stderr)
        );
        let report: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
        assert_eq!(report["instance_id"], identity.id);
        assert_eq!(
            report["managed_service"].as_str(),
            config.managed_service.as_deref()
        );
        assert_eq!(report["mode"], "managed_fleet");
        assert_eq!(report["local_ready"], false);
        assert_eq!(
            report["error_code"],
            if missing_fleet {
                "host_configuration"
            } else {
                "host_unavailable"
            }
        );
        assert!(report.get("service_status").is_some());
        assert!(report.get("client_build").is_some());
        assert!(report.get("host_build").is_some());
        let text = String::from_utf8(output.stdout).unwrap();
        assert!(!text.contains(SECRET) && !text.contains("\"token\""));
        assert!(!text.contains("\"safetyNumber\""));
        assert_eq!(retained_files(&home), before);
        assert!(server_pid(&config.chat_endpoint()).is_none());
    }
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn standalone_personal_cold_launch_uses_saved_configuration_without_flags() {
    let dir = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(dir.path(), true).unwrap();
    let mut config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    config.local_fixture = true;
    config.gc2_carrier = false;
    config.listen = "127.0.0.1:0".parse().unwrap();
    config.network_recovery = false;
    config.relay_urls.clear();
    let personal = InstanceHost::new(config.clone()).unwrap();
    let original = unlock(&personal, true).await.instance;
    personal.flush().await.unwrap();
    drop(personal);

    // Older standalone versions did not save a recipe. Opening that same
    // retained profile once with its explicit installation settings migrates it.
    let registration_path = config.archive.with_extension("host.json");
    if registration_path.exists() {
        std::fs::remove_file(registration_path).unwrap();
    }
    let migrated = InstanceHost::new(config.clone()).unwrap();
    let retained = unlock(&migrated, false).await.instance;
    assert_eq!(retained.id, original.id);
    assert_eq!(retained.safety_number, original.safety_number);
    migrated.flush().await.unwrap();
    drop(migrated);

    let selected = InstanceConfig::from_home(Some(dir.path())).unwrap();
    assert!(
        selected.has_registered_host().unwrap(),
        "actual personal runtime must publish its saved host recipe"
    );
    assert!(selected.local_fixture && !selected.network_recovery && !selected.gc2_carrier);
    assert_eq!(selected.listen, config.listen);
    assert!(selected.fleet_config.is_none() && selected.managed_service.is_none());
    let registration = std::fs::read(config.archive.with_extension("host.json")).unwrap();
    let executable = Path::new(env!("CARGO_BIN_EXE_gchat"));
    let client = ensure_running_checked(&selected, executable, true)
        .await
        .unwrap();
    let worker = Worker {
        endpoint: selected.chat_endpoint(),
        pid: server_pid(&selected.chat_endpoint()).unwrap(),
    };
    let Response::Snapshot { snapshot } = client
        .request(Request::Unlock {
            passphrase: SECRET.into(),
            create: false,
        })
        .await
        .unwrap()
    else {
        panic!("personal retained daemon unlock");
    };
    assert_eq!(snapshot.instance.id, original.id);
    assert_eq!(snapshot.instance.safety_number, original.safety_number);
    client.request(Request::Disconnect).await.unwrap();
    drop(client);
    worker.stop().await;
    assert_eq!(
        std::fs::read(config.archive.with_extension("host.json")).unwrap(),
        registration
    );
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

async fn fleet_identity(endpoint: &Path) -> String {
    tokio::time::timeout(Duration::from_secs(15), async {
        loop {
            if let Ok(client) = IpcClient::connect_component(
                endpoint,
                "registered-fleet-fixture",
                vec![Capability::IdentityRead],
                ComponentCredentials {
                    component_id: [2; 16],
                    token: [7; 32],
                },
            )
            .await
            {
                return client.refresh_identity().await.unwrap().safety_number;
            }
            tokio::time::sleep(Duration::from_millis(50)).await;
        }
    })
    .await
    .expect("registered fleet authentication becomes ready")
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn crashed_scoped_daemon_reclaims_fleet_endpoint_and_authenticates() {
    let dir = tempfile::tempdir().unwrap();
    let (config, safety) = fixture(dir.path()).await;
    let endpoint = config.protocol_socket.with_extension("fleet");
    let selected = InstanceConfig::from_home(Some(dir.path())).unwrap();
    let executable = Path::new(env!("CARGO_BIN_EXE_gchat"));
    let client = ensure_running_checked(&selected, executable, true)
        .await
        .unwrap();
    let worker = Worker {
        endpoint: selected.chat_endpoint(),
        pid: server_pid(&selected.chat_endpoint()).unwrap(),
    };
    let instance = client.instance_id().to_owned();
    client
        .request(Request::Unlock {
            passphrase: SECRET.into(),
            create: false,
        })
        .await
        .unwrap();
    assert_eq!(fleet_identity(&endpoint).await, safety);
    // Only the actual process serving this disposable profile may be killed.
    assert_eq!(server_pid(client.endpoint()), Some(worker.pid));
    assert!(std::process::Command::new("kill")
        .args(["-KILL", &worker.pid.to_string()])
        .status()
        .unwrap()
        .success());
    tokio::time::timeout(Duration::from_secs(10), async {
        while server_pid(client.endpoint()).is_some() {
            tokio::time::sleep(Duration::from_millis(20)).await;
        }
    })
    .await
    .expect("owned crashed process releases its listeners");
    assert!(
        endpoint.exists(),
        "abrupt termination retains the socket name"
    );
    drop((client, worker));

    let reopened = InstanceConfig::from_home(Some(dir.path())).unwrap();
    let client = ensure_running_checked(&reopened, executable, true)
        .await
        .unwrap();
    let worker = Worker {
        endpoint: reopened.chat_endpoint(),
        pid: server_pid(&reopened.chat_endpoint()).unwrap(),
    };
    assert_eq!(client.instance_id(), instance);
    client
        .request(Request::Unlock {
            passphrase: SECRET.into(),
            create: false,
        })
        .await
        .unwrap();
    assert_eq!(fleet_identity(&endpoint).await, safety);
    client.request(Request::Disconnect).await.unwrap();
    drop(client);
    worker.stop().await;
}
