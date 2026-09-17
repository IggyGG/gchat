#![cfg(unix)]

use gchat_core::client::ClientHandle;
use gcoms_node::node::{start, NodeConfig};
use gcoms_sdk::ipc::Capability;
use gcoms_sdk::{serve_unix, ChannelVisibility, EmbeddedClient};

#[tokio::test(flavor = "multi_thread")]
async fn daemon_channel_archive_survives_restart() {
    let dir = tempfile::tempdir().unwrap();
    let socket = dir.path().join("gcd.sock");
    let archive = dir.path().join("chat.gcarchive");
    let embedded = EmbeddedClient::new(
        start(NodeConfig {
            seed: [0x41; 32],
            listen: "127.0.0.1:0".parse().unwrap(),
            control: None,
            advertise: None,
            inbox_relay: None,
            profile: gcoms_node::node::NodeProfile::fixture(),
            alias_lifecycle: Default::default(),
        })
        .await
        .unwrap(),
    );
    let server_client = embedded.clone();
    let server_socket = socket.clone();
    let server = tokio::spawn(async move {
        serve_unix(
            server_socket,
            server_client,
            vec![
                Capability::IdentityRead,
                Capability::ChannelMember,
                Capability::ChannelAdmin,
                Capability::EventRead,
            ],
        )
        .await
    });
    for _ in 0..100 {
        if socket.exists() {
            break;
        }
        tokio::time::sleep(std::time::Duration::from_millis(10)).await;
    }

    let remote = ClientHandle::connect_daemon(&archive, "archive", &socket, true)
        .await
        .unwrap();
    let id = remote
        .create_channel("ops", "owner", 8, ChannelVisibility::Private)
        .await
        .unwrap();
    remote
        .send_channel(id, "daemon channel history")
        .await
        .unwrap();
    remote.shutdown().await.unwrap();
    let reopened = ClientHandle::connect_daemon(&archive, "archive", &socket, false)
        .await
        .unwrap();
    assert!(reopened
        .channel(id)
        .unwrap()
        .messages
        .iter()
        .any(|message| message.text == "daemon channel history"));
    reopened.shutdown().await.unwrap();
    server.abort();
    embedded.node().shutdown().await;
}
