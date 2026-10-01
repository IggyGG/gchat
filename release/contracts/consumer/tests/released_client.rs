#![cfg(any(unix, windows))]

use gchat_core::chat_service::{
    self,
    host::{InstanceConfig, InstanceHost},
    ChatEndpoint,
};
use released_chat::{ChatClient, Request, Response};
use std::time::Duration;

// Compile the unchanged API 2 client and generated RPC 1 client from the
// released source fixture, then attach them to the current real local server.
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn released_client_attaches_mutates_once_and_reopens_without_identity_change() {
    let dir = tempfile::tempdir().unwrap();
    gcoms::sdk::private_fs::make_private(dir.path(), true).unwrap();
    let mut config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    config.local_fixture = true;
    config.gc2_carrier = false;
    config.listen = "127.0.0.1:0".parse().unwrap();
    config.relay_urls.clear();
    config.network_recovery = false;
    let endpoint = dir.path().join("chat.sock");
    let host = InstanceHost::new(config.clone()).unwrap();
    let identity = host.instance_id().to_string();
    let (stop, receiver) = tokio::sync::watch::channel(false);
    let serving = tokio::spawn({
        let host = host.clone();
        let endpoint = endpoint.clone();
        async move { chat_service::serve(host, &endpoint, receiver).await }
    });
    let old = tokio::time::timeout(Duration::from_secs(15), async {
        loop {
            if let Ok(client) = ChatClient::connect(&endpoint, Some(&identity)).await {
                break client;
            }
            tokio::time::sleep(Duration::from_millis(25)).await;
        }
    })
    .await
    .expect("released client connects to current server");
    assert_eq!(old.instance_id(), identity);
    let Response::Snapshot { snapshot } = old
        .request(Request::Unlock {
            passphrase: "released-client-fixture".into(),
            create: true,
        })
        .await
        .unwrap()
    else {
        panic!("released unlock decoder");
    };
    let safety = snapshot.instance.safety_number;
    let Response::Applied {
        conversation: Some(channel),
        ..
    } = old
        .request(Request::Submit {
            operation_id: "released-create-01".into(),
            conversation: None,
            text: "/create #compat owner".into(),
        })
        .await
        .unwrap()
    else {
        panic!("released create");
    };
    let message = Request::Submit {
        operation_id: "released-message01".into(),
        conversation: Some(channel.clone()),
        text: "retained client message".into(),
    };
    old.request(message.clone()).await.unwrap();
    old.request(message).await.unwrap();
    let Response::History { page } = old
        .request(Request::History {
            conversation: channel.clone(),
            before: None,
            limit: 100,
        })
        .await
        .unwrap()
    else {
        panic!("released RPC history decoder");
    };
    assert_eq!(
        page.messages
            .iter()
            .filter(|row| row.body == "retained client message")
            .count(),
        1
    );
    assert!(ChatClient::connect(&endpoint, Some("different-instance"))
        .await
        .is_err());
    let new = gchat_api::ChatClient::connect(&endpoint, Some(&identity))
        .await
        .unwrap();
    assert_eq!(new.instance_id(), old.instance_id());
    drop(new);
    host.flush().await.unwrap();
    old.request(Request::Disconnect).await.unwrap();
    drop(old);
    stop.send(true).unwrap();
    serving.await.unwrap().unwrap();
    drop(host);
    let host = InstanceHost::new(config).unwrap();
    assert_eq!(host.instance_id(), identity);
    let (stop, receiver) = tokio::sync::watch::channel(false);
    let serving = tokio::spawn({
        let host = host.clone();
        let endpoint = endpoint.clone();
        async move { chat_service::serve(host, &endpoint, receiver).await }
    });
    let old = tokio::time::timeout(Duration::from_secs(15), async {
        loop {
            if let Ok(client) = ChatClient::connect(&endpoint, Some(&identity)).await {
                break client;
            }
            tokio::time::sleep(Duration::from_millis(25)).await;
        }
    })
    .await
    .unwrap();
    let Response::Snapshot { snapshot } = old
        .request(Request::Unlock {
            passphrase: "released-client-fixture".into(),
            create: false,
        })
        .await
        .unwrap()
    else {
        panic!("released reopen");
    };
    assert_eq!(snapshot.instance.safety_number, safety);
    let Response::History { page } = old
        .request(Request::History {
            conversation: channel,
            before: None,
            limit: 100,
        })
        .await
        .unwrap()
    else {
        panic!("released retained history");
    };
    assert_eq!(
        page.messages
            .iter()
            .filter(|row| row.body == "retained client message")
            .count(),
        1
    );
    old.request(Request::Disconnect).await.unwrap();
    stop.send(true).unwrap();
    serving.await.unwrap().unwrap();
}
