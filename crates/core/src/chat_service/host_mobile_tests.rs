//! The outbound host path is exercised on desktop too; no provider or relay is
//! provisioned. Profiles start with no invitation, directory or ready routes.
use super::*;

fn outbound(home: &Path) -> InstanceConfig {
    let mut config = InstanceConfig::from_home(Some(home)).unwrap();
    config.protocol_backend = gcoms::Backend::NetworkClient;
    config.gc2_carrier = true;
    config.network_recovery = false;
    config.relay_urls.clear();
    // Any IPC preparation would create this directory; mobile must not touch it.
    config.protocol_socket = home.join("no-ipc").join("protocol.sock");
    config
}

#[cfg(feature = "gc2-carrier")]
async fn request(host: &InstanceHost, request: Request) -> Response {
    host.dispatch(RequestEnvelope {
        version: VERSION,
        instance_id: Some(host.instance_id().into()),
        request,
    })
    .await
    .response
}

#[test]
fn outbound_host_refuses_listener_configuration_before_creating_profile() {
    let dir = tempfile::tempdir().unwrap();
    let home = dir.path().join("untouched");
    for advertise in [false, true] {
        let mut config = outbound(&home);
        if advertise {
            config.advertise = Some("127.0.0.1:24433".parse().unwrap());
        } else {
            config.listen = "127.0.0.1:24433".parse().unwrap();
        }
        let error = match InstanceHost::new(config) {
            Ok(_) => panic!("outbound host accepted a listener configuration"),
            Err(error) => error,
        };
        assert!(error.contains("cannot configure listeners"), "{error}");
        assert!(!home.exists());
    }
}

#[tokio::test]
async fn outbound_host_cannot_launch_an_external_daemon() {
    let dir = tempfile::tempdir().unwrap();
    let home = dir.path().join("untouched");
    let config = outbound(&home);
    let error = match ensure_running(&config, &home.join("no-executable"), false).await {
        Ok(_) => panic!("outbound host launched a daemon"),
        Err(error) => error,
    };
    assert!(error.contains("attach in-process"), "{error}");
    assert!(!home.exists());
}

#[cfg(feature = "gc2-carrier")]
#[tokio::test]
async fn outbound_host_reopens_encrypted_profile_and_files_without_local_endpoints() {
    use gchat_api::{files::FileIo, FileRequest};
    use gcoms::sdk::ConnectionState;

    let dir = tempfile::tempdir().unwrap();
    let config = outbound(&dir.path().join("instance"));
    let host = InstanceHost::new(config.clone()).unwrap();
    let id = host.instance_id().to_string();
    let boot = host.boot.clone();
    let secret = "outbound-host-fixture-secret";
    let initial = request(
        &host,
        Request::Unlock {
            passphrase: secret.into(),
            create: true,
        },
    )
    .await;
    let Response::Snapshot { snapshot } = initial else {
        panic!("outbound profile did not unlock: {initial:?}");
    };
    assert!(!snapshot.instance.locked && !snapshot.instance.protocol_locked);
    assert!(!snapshot.instance.safety_number.is_empty());
    let safety = snapshot.instance.safety_number;
    let lifecycle = {
        let running = host.running.lock().await;
        let running = running.as_ref().unwrap();
        assert!(running.ipc.is_none());
        let embedded = running.runtime.embedded().unwrap();
        assert_eq!(embedded.node().listener_addr().port(), 0);
        assert!(embedded
            .node()
            .local_relay_introduction()
            .unwrap()
            .is_none());
        let diagnostics = embedded.node().diagnostics();
        assert_eq!(diagnostics.relay_resources.jobs, 0);
        assert_eq!(diagnostics.relay_resources.bytes, 0);
        running.runtime.clone()
    };
    assert!(!config.protocol_socket.parent().unwrap().exists());
    let configured = request(
        &host,
        Request::Files {
            request: FileRequest::Configure {
                quota_bytes: (64_u64 * 1024 * 1024).to_string(),
                retention_days: 1,
            },
        },
    )
    .await;
    assert!(
        matches!(configured, Response::Files { .. }),
        "{configured:?}"
    );
    let foreign_frame = gchat_api::files::encode_io(
        &FileIo {
            instance: "another-instance".into(),
            id: "00".repeat(16),
            piece: 0,
            upload: false,
        },
        &[],
    )
    .unwrap();
    assert!(host
        .clone()
        .file_io(foreign_frame.clone())
        .await
        .unwrap_err()
        .contains("another instance"));

    // The configured socket path is irrelevant in-process: even an unrelated
    // existing file must survive stop, failed unlock and a later successful open.
    std::fs::create_dir(config.protocol_socket.parent().unwrap()).unwrap();
    let sentinel = b"not an IPC endpoint; preserve this file";
    std::fs::write(&config.protocol_socket, sentinel).unwrap();
    host.flush().await.unwrap();
    assert!(host.running.lock().await.is_none());
    assert_eq!(
        lifecycle.0.status().await.unwrap().connection,
        ConnectionState::Stopped
    );
    // The observer clone also owns the stopped routing directory. Release it
    // before opening a separate instance, as the mobile attachment does.
    drop(lifecycle);
    assert!(host
        .clone()
        .file_io(foreign_frame)
        .await
        .unwrap_err()
        .contains("Unlock"));
    assert_eq!(std::fs::read(&config.protocol_socket).unwrap(), sentinel);
    let profile = std::fs::read(&config.profile).unwrap();
    let archive = std::fs::read(&config.archive).unwrap();
    assert!(!profile
        .windows(secret.len())
        .any(|window| window == secret.as_bytes()));
    assert!(!archive
        .windows(secret.len())
        .any(|window| window == secret.as_bytes()));

    // A fresh host can reacquire both profile locks after orderly suspension.
    let reopened = InstanceHost::new(config.clone()).unwrap();
    assert_eq!(reopened.instance_id(), id);
    assert_ne!(reopened.boot, boot);
    let wrong = request(
        &reopened,
        Request::Unlock {
            passphrase: "incorrect-passphrase".into(),
            create: false,
        },
    )
    .await;
    assert!(matches!(wrong, Response::Error { .. }), "{wrong:?}");
    assert!(reopened.running.lock().await.is_none());
    assert_eq!(std::fs::read(&config.profile).unwrap(), profile);
    assert_eq!(std::fs::read(&config.archive).unwrap(), archive);
    let restored = request(
        &reopened,
        Request::Unlock {
            passphrase: secret.into(),
            create: false,
        },
    )
    .await;
    let Response::Snapshot { snapshot } = restored else {
        panic!("outbound profile did not reopen: {restored:?}");
    };
    assert_eq!(snapshot.instance.safety_number, safety);
    let files = request(
        &reopened,
        Request::Files {
            request: FileRequest::List { conversation: None },
        },
    )
    .await;
    let Response::Files { snapshot } = files else {
        panic!("outbound file cache did not reopen: {files:?}");
    };
    assert_eq!(snapshot.quota_bytes, (64_u64 * 1024 * 1024).to_string());
    assert_eq!(snapshot.retention_days, 1);
    assert!(snapshot.files.is_empty());
    reopened.flush().await.unwrap();
    reopened.flush().await.unwrap();
    assert!(reopened.running.lock().await.is_none());
    assert_eq!(std::fs::read(&config.protocol_socket).unwrap(), sentinel);
}

#[cfg(not(any(target_os = "android", target_os = "ios")))]
#[test]
fn desktop_default_still_uses_the_existing_embedded_attachment() {
    let dir = tempfile::tempdir().unwrap();
    let config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    assert!(matches!(config.protocol_backend, gcoms::Backend::Embedded));
    assert!(config.uses_protocol_ipc());
    assert!(!config.gc2_carrier);
}

#[cfg(feature = "mobile-push")]
#[tokio::test]
async fn notification_failure_and_tap_do_not_unlock_or_replace_the_mobile_runtime() {
    use gcoms::runtime::push_notifications::{PushPlatform, PushRegistrationRequest};
    let dir = tempfile::tempdir().unwrap();
    let config = outbound(&dir.path().join("instance"));
    let host = InstanceHost::new(config.clone()).unwrap();
    assert!(host.push_networks().await.unwrap_err().contains("Unlock"));
    assert!(host.running.lock().await.is_none());
    assert!(!config.profile.exists());
    let Response::Snapshot { snapshot } = request(
        &host,
        Request::Unlock {
            passphrase: "notification profile fixture".into(),
            create: true,
        },
    )
    .await
    else {
        panic!("fixture failed to unlock");
    };
    let safety = snapshot.instance.safety_number;
    assert_eq!(host.push_networks().await.unwrap(), ["primary"]);
    let ticket = host
        .request_push_registration(
            "primary",
            PushRegistrationRequest {
                app_id: "boo.gchat.app".into(),
                installation_nonce: [9; 32],
                platform: PushPlatform::Fcm,
                token: "fixture-provider-token".into(),
                revision: 1,
                visible: true,
            },
        )
        .await;
    assert!(ticket.err().unwrap().contains("inbox relay is not ready"));
    let Response::Snapshot { snapshot } = request(&host, Request::Snapshot).await else {
        panic!("lost normal chat after push failure");
    };
    assert_eq!(snapshot.instance.safety_number, safety);
    assert!(!snapshot.instance.locked);
    let _ = request(&host, Request::Lock).await;
    assert!(host.push_networks().await.unwrap_err().contains("Unlock"));
    // A hint only requests normal status; it never supplies a passphrase or
    // creates a second runtime. The native app leaves this archive locked.
    let Response::Snapshot { snapshot } = request(&host, Request::Snapshot).await else {
        panic!("lost locked profile");
    };
    assert!(snapshot.instance.locked);
    assert_eq!(snapshot.instance.safety_number, safety);
    assert!(!config.protocol_socket.parent().unwrap().exists());
    host.flush().await.unwrap();
}
