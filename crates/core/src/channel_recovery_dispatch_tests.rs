use super::*;
use gcoms::sdk::ChannelStatus;
use std::time::Duration;

async fn exchange(a: &ProtocolClient, b: &ProtocolClient, text: &[u8]) {
    let mut sent = a.subscribe_events();
    let mut received = b.subscribe_events();
    let id = a
        .send_channel_tracked("retained-recovery", text)
        .await
        .unwrap();
    tokio::time::timeout(Duration::from_secs(25), async {
        loop {
            if matches!(received.recv().await.unwrap(), ClientEvent::ChannelMessage { channel, message_id, body, .. } if channel == "retained-recovery" && message_id == id && body == text) {
                break;
            }
        }
        loop {
            if matches!(sent.recv().await.unwrap(), ClientEvent::ChannelDelivered { channel, message_id } if channel == "retained-recovery" && message_id == id) {
                break;
            }
        }
    }).await.expect("actual plaintext and exact authenticated ACK");
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn protocol_runtime_recovery_forwards_exact_admission_after_cold_reopen() {
    let dir = tempfile::tempdir().unwrap();
    crate::private_fs::make_private(dir.path(), true).unwrap();
    let allow = vec!["127.0.0.1/32".to_owned()];
    let mut a = ProtocolRuntime::create_fixture(
        &dir.path().join("owner"),
        "test-only-passphrase",
        "127.0.0.1:0".parse().unwrap(),
        None,
        None,
        &allow,
    )
    .await
    .unwrap();
    let mut b = ProtocolRuntime::create_fixture(
        &dir.path().join("member"),
        "test-only-passphrase",
        "127.0.0.1:0".parse().unwrap(),
        None,
        None,
        &allow,
    )
    .await
    .unwrap();
    let (mut owner, mut member) = (a.sdk_client(), b.sdk_client());
    let old_identity = owner.identity();
    let id = owner
        .create_channel("retained-recovery", "owner", 8, ChannelVisibility::Private)
        .await
        .unwrap();
    let join = member.prepare_channel_join("member").await.unwrap();
    let package = member.channel_key_package(join).await.unwrap();
    let welcome = owner
        .admit_channel("retained-recovery", &package, "member")
        .await
        .unwrap();
    member
        .join_channel(
            join,
            "retained-recovery",
            ChannelVisibility::Private,
            &welcome,
        )
        .await
        .unwrap();
    exchange(&owner, &member, b"retained before both reopen").await;
    let before = owner.list_channels().await.unwrap().remove(0);
    assert_eq!(before.status, ChannelStatus::Active);
    let (a_listen, b_listen) = (
        a.listen_label().parse().unwrap(),
        b.listen_label().parse().unwrap(),
    );
    drop(owner);
    drop(member);
    a.shutdown().await.unwrap();
    b.shutdown().await.unwrap();
    a = ProtocolRuntime::unlock_fixture(
        &dir.path().join("owner"),
        "test-only-passphrase",
        a_listen,
        None,
        None,
        &allow,
    )
    .await
    .unwrap();
    b = ProtocolRuntime::unlock_fixture(
        &dir.path().join("member"),
        "test-only-passphrase",
        b_listen,
        None,
        None,
        &allow,
    )
    .await
    .unwrap();
    owner = a.sdk_client();
    member = b.sdk_client();
    assert_eq!(
        owner
            .contact_identity(&owner.identity().contact_card)
            .unwrap(),
        owner.contact_identity(&old_identity.contact_card).unwrap()
    );
    assert_eq!(owner.list_channels().await.unwrap()[0].id, id);
    let peer = member.refresh_identity().await.unwrap().contact_card;
    // This production wrapper previously inherited the deny-by-default trait
    // method, while the embedded implementation and IPC codec tests passed.
    let socket = dir.path().join("owner.sock");
    let host = owner.clone();
    let server_socket = socket.clone();
    let server = tokio::spawn(gcoms::sdk::serve_unix(
        server_socket,
        host,
        crate::daemon::scope_capabilities(crate::daemon::Scope::Chat),
    ));
    tokio::time::timeout(Duration::from_secs(3), async {
        while !socket.exists() {
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
    })
    .await
    .unwrap();
    let ipc = gcoms::sdk::IpcClient::connect(
        &socket,
        "actual-recovery-wrapper",
        vec![
            gcoms::sdk::ipc::Capability::IdentityRead,
            gcoms::sdk::ipc::Capability::ChannelAdmin,
        ],
    )
    .await
    .unwrap();
    let recovered = ipc
        .recover_channel_route("retained-recovery", id, before.epoch, &welcome, &peer)
        .await;
    drop(ipc);
    server.abort();
    let _ = server.await;
    recovered.unwrap();
    exchange(&owner, &member, b"owner after retained runtime reopen").await;
    exchange(&member, &owner, b"member after retained runtime reopen").await;
    assert_eq!(owner.list_channels().await.unwrap()[0].epoch, before.epoch);
    let denied = owner
        .recover_channel_route(
            "retained-recovery",
            id,
            before.epoch,
            &Blob(vec![0; 8]),
            &peer,
        )
        .await;
    assert!(
        matches!(denied, Err(SdkError::Runtime(reason)) if reason.contains("exact retained admission missing"))
    );
    drop(owner);
    drop(member);
    a.shutdown().await.unwrap();
    b.shutdown().await.unwrap();
}
