#![cfg(any(unix, windows))]

use gchat_core::client::ClientHandle;
use gcoms::sdk::ipc::Capability;
use gcoms::sdk::{serve_local, ChannelVisibility, EmbeddedClient};
use gcoms_node::node::{start, NodeConfig};

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
        serve_local(
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
    // A Windows named pipe has no filesystem entry. Probe the transport on
    // both platforms and stop promptly if the listener failed to start.
    tokio::time::timeout(std::time::Duration::from_secs(30), async {
        loop {
            if gcoms::sdk::local::connect(&gcoms::sdk::local::LocalEndpoint::new(&socket))
                .await
                .is_ok()
            {
                break;
            }
            assert!(
                !server.is_finished(),
                "protocol daemon stopped before readiness"
            );
            tokio::time::sleep(std::time::Duration::from_millis(10)).await;
        }
    })
    .await
    .expect("protocol daemon became ready");

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
