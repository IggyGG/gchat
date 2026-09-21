#![cfg(any(unix, windows))]
use gchat_api::ChatClient;
use gchat_core::{chat_service::endpoint_for, runtime::ProtocolRuntime};
use gcoms::sdk::GcClient;
use std::{io::Read, process::Stdio, time::Duration};

#[tokio::test]
async fn headless_daemon_creates_separate_archive_for_a_retained_profile() {
    let dir = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(dir.path(), true).unwrap();
    let profile = dir.path().join("profile");
    let archive = dir.path().join("chat.gcarchive");
    let socket = dir.path().join("service.sock");
    let protocol_pass = dir.path().join("protocol-pass");
    let archive_pass = dir.path().join("archive-pass");
    for (path, secret) in [
        (&protocol_pass, "fixture-profile-password"),
        (&archive_pass, "fixture-archive-password"),
    ] {
        std::fs::write(path, secret).unwrap();
        gchat_core::private_fs::make_private(path, false).unwrap();
    }
    let runtime = ProtocolRuntime::create_fixture(
        &profile,
        "fixture-profile-password",
        "127.0.0.1:0".parse().unwrap(),
        None,
        None,
        &[],
    )
    .await
    .unwrap();
    let client = runtime.sdk_client();
    let identity = client
        .contact_identity(&client.identity().contact_card)
        .unwrap();
    drop(client);
    runtime.shutdown().await.unwrap();
    assert!(!archive.exists());
    let stderr_path = dir.path().join("daemon.stderr");
    let stderr = std::fs::File::create(&stderr_path).unwrap();
    let diagnostic = || {
        let mut bytes = Vec::new();
        if let Ok(file) = std::fs::File::open(&stderr_path) {
            let _ = file.take(16 * 1024).read_to_end(&mut bytes);
        }
        String::from_utf8_lossy(&bytes).into_owned()
    };
    let mut child = tokio::process::Command::new(env!("CARGO_BIN_EXE_gchat"))
        .args([
            "daemon",
            "--local-fixture",
            "--no-network-bootstrap",
            "--listen",
            "127.0.0.1:0",
        ])
        .arg("--store")
        .arg(&profile)
        .arg("--chat-archive")
        .arg(&archive)
        .arg("--socket")
        .arg(&socket)
        .arg("--passphrase-file")
        .arg(&protocol_pass)
        .arg("--chat-passphrase-file")
        .arg(&archive_pass)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::from(stderr))
        .kill_on_drop(true)
        .spawn()
        .unwrap();
    let endpoint = endpoint_for(&socket);
    let connected = tokio::time::timeout(Duration::from_secs(30), async {
        loop {
            if let Ok(client) = ChatClient::connect(&endpoint, None).await {
                break client;
            }
            if let Some(status) = child.try_wait().unwrap() {
                panic!(
                    "standalone daemon stopped before readiness: {status}; {}",
                    diagnostic()
                );
            }
            tokio::time::sleep(Duration::from_millis(20)).await;
        }
    })
    .await
    .unwrap_or_else(|error| {
        panic!(
            "standalone daemon readiness timed out: {error}; {}",
            diagnostic()
        )
    });
    let response = connected
        .request(gchat_api::Request::Snapshot)
        .await
        .unwrap();
    assert!(
        matches!(response,gchat_api::Response::Snapshot { snapshot } if !snapshot.instance.locked && !snapshot.instance.protocol_locked)
    );
    assert!(archive.exists());
    connected
        .request(gchat_api::Request::Disconnect)
        .await
        .unwrap();
    drop(connected);
    child.start_kill().unwrap();
    let _ = child.wait().await;
    let reopened = ProtocolRuntime::unlock_fixture(
        &profile,
        "fixture-profile-password",
        "127.0.0.1:0".parse().unwrap(),
        None,
        None,
        &[],
    )
    .await
    .unwrap();
    let client = reopened.sdk_client();
    assert_eq!(
        client
            .contact_identity(&client.identity().contact_card)
            .unwrap(),
        identity
    );
    drop(client);
    reopened.shutdown().await.unwrap();
}
