//! The combined link is redeemed through the same service API as the UI.
use super::*;
use crate::chat_service::ChatEndpoint;
use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine};
use gchat_api::files::{encode_io, FileIo};
use gchat_api::{FileRequest, FileState};
use gcoms_node::node::{start_with_routing, NodeConfig, NodeProfile, RoutingConfig};

async fn request(service: &Arc<ChatService>, request: Request) -> Response {
    let response = service.handle(request).await.unwrap();
    assert!(!matches!(response, Response::Error { .. }), "{response:?}");
    response
}

fn service(home: &Path, runtime: ProtocolRuntime) -> Arc<ChatService> {
    ChatService::new(
        home.join("chat.enc"),
        runtime,
        vec![
            Capability::IdentityRead,
            Capability::ChannelMember,
            Capability::ChannelAdmin,
            Capability::EventRead,
        ],
    )
    .unwrap()
}

#[tokio::test(flavor = "multi_thread", worker_threads = 4)]
#[ignore = "requires scripts/test-bootstrap-namespace.py; no external network"]
async fn combined_invitation_joins_another_network_and_retains_chat_and_file() {
    assert_eq!(
        std::env::var("GCHAT_BOOTSTRAP_NAMESPACE").as_deref(),
        Ok("isolated")
    );
    assert_ne!(
        std::fs::read_link("/proc/self/ns/net")
            .unwrap()
            .to_string_lossy(),
        std::env::var("GCHAT_BOOTSTRAP_HOST_NAMESPACE").unwrap()
    );
    tokio::time::timeout(Duration::from_secs(480), journey())
        .await
        .unwrap();
}

async fn journey() {
    let home = tempfile::tempdir().unwrap();
    crate::private_fs::make_private(home.path(), true).unwrap();
    let sender_home = home.path().join("sender");
    let receiver_home = home.path().join("receiver");
    crate::paths::ensure_private_dir(&sender_home, "sender").unwrap();
    crate::paths::ensure_private_dir(&receiver_home, "receiver").unwrap();
    let mut relays = Vec::new();
    // GC/2 application routes require five distinct relay identities.
    for n in 71..76u8 {
        relays.push(
            start_with_routing(
                NodeConfig {
                    seed: [n; 32],
                    listen: format!("93.184.216.{n}:0").parse().unwrap(),
                    control: None,
                    advertise: None,
                    inbox_relay: None,
                    alias_lifecycle: Default::default(),
                    profile: NodeProfile::gchat_file_transfer_production(None, 2),
                },
                RoutingConfig::default(),
            )
            .await
            .unwrap(),
        );
    }
    let bundle = gcoms_routing::gc2::directory::BootstrapBundle {
        relays: relays
            .iter()
            .map(|r| r.gc2_relay_introduction().unwrap())
            .collect(),
    };
    for relay in &relays {
        relay.install_gc2_routing_bootstrap(&bundle).unwrap();
    }
    let signer = gcoms_crypto::IdentityKeypair::from_seed([94; 32]);
    let mut defaults = crate::network::installed()
        .unwrap()
        .signed_defaults
        .defaults;
    defaults.network_id = "invited.example".into();
    defaults.dns_domain = defaults.network_id.clone();
    defaults.provider_urls = vec!["https://bootstrap.invited.example/".into()];
    defaults.issued_at = now();
    defaults.expires_at = now() + 3600;
    defaults.founders.truncate(relays.len());
    for (i, (founder, relay)) in defaults.founders.iter_mut().zip(&relays).enumerate() {
        founder.name = format!("r{}.relays.invited.example", i + 1);
        let introduction = relay.gc2_relay_introduction().unwrap();
        founder.service_id = introduction.service_id;
        founder.address_hints = vec![relay.listener_addr()];
    }
    let identity = NetworkIdentity {
        trusted_key_b64: URL_SAFE_NO_PAD.encode(signer.public_bytes()),
        signed_defaults: gcoms_network::SignedNetworkDefaults::sign(defaults, &signer, vec![])
            .unwrap(),
    };
    let sender_runtime = ProtocolRuntime::open_network(
        &sender_home.join("protocol.enc"),
        "sender-test",
        true,
        identity.clone(),
    )
    .await
    .unwrap();
    let sender_node = sender_runtime
        .embedded()
        .expect("embedded fixture")
        .node()
        .clone();
    sender_node.install_gc2_routing_bootstrap(&bundle).unwrap();
    sender_node
        .wait_for_inbox(tokio::time::Instant::now() + Duration::from_secs(120))
        .await
        .unwrap();
    let sender = service(&sender_home, sender_runtime.clone());
    request(
        &sender,
        Request::Unlock {
            passphrase: "sender-test".into(),
            create: true,
        },
    )
    .await;
    request(
        &sender,
        Request::Submit {
            operation_id: random_id(),
            conversation: None,
            text: "/create welcome Alice".into(),
        },
    )
    .await;
    let channel = sender.snapshot().await.unwrap().conversations[0].id.clone();
    let Response::Output {
        output: gchat_api::CommandOutput::Invitation { link, .. },
        ..
    } = request(
        &sender,
        Request::Submit {
            operation_id: random_id(),
            conversation: Some(channel.clone()),
            text: "/invite".into(),
        },
    )
    .await
    else {
        panic!("combined invitation expected")
    };
    assert!(link.starts_with(JOIN_INVITATION_PREFIX));
    assert!(JoinInvitation::decode_at(&link, now())
        .unwrap()
        .network
        .same_network(&identity));

    let profile = receiver_home.join("protocol.enc");
    let primary = ProtocolRuntime::create_protected(
        &profile,
        "receiver-test",
        "127.0.0.1:24491".parse().unwrap(),
        None,
        None,
        &[],
    )
    .await
    .unwrap();
    let receiver = service(&receiver_home, primary.clone());
    request(
        &receiver,
        Request::Unlock {
            passphrase: "receiver-test".into(),
            create: true,
        },
    )
    .await;
    let NetworkResponse::Preview { preview } = receiver
        .networks_request(NetworkRequest::Inspect { code: link.clone() })
        .await
        .unwrap()
    else {
        panic!()
    };
    assert!(preview.new_network);
    assert_eq!(preview.channel.as_deref(), Some("welcome"));
    let network = preview.network.id;
    receiver
        .networks_request(NetworkRequest::Join {
            code: link,
            nickname: "Bob".into(),
            accepted_network: network.clone(),
            operation_id: random_id(),
        })
        .await
        .unwrap();
    let child = receiver.networks.lock().await[&network].clone();
    let snapshot = child.snapshot().await.unwrap();
    let child_identity = snapshot.instance.safety_number;
    let child_channel = snapshot.conversations[0].id.clone();
    assert!(
        receiver.snapshot().await.unwrap().conversations.is_empty(),
        "primary network stays separate"
    );
    assert_ne!(
        receiver.snapshot().await.unwrap().instance.safety_number,
        child_identity
    );
    eprintln!("combined invitation: protected network + channel joined; primary remains separate");

    let file = "03030303030303030303030303030303";
    let bytes = vec![0x7b; 16 * 1024 + 11];
    request(
        &sender,
        Request::Files {
            request: FileRequest::Prepare {
                id: file.into(),
                conversation: channel.clone(),
                name: "invitation.bin".into(),
                size_bytes: bytes.len().to_string(),
            },
        },
    )
    .await;
    sender
        .clone()
        .file_io(
            encode_io(
                &FileIo {
                    instance: sender.snapshot().await.unwrap().instance.id,
                    id: file.into(),
                    piece: 0,
                    upload: true,
                },
                &bytes,
            )
            .unwrap(),
        )
        .await
        .unwrap();
    request(
        &sender,
        Request::Files {
            request: FileRequest::Commit { id: file.into() },
        },
    )
    .await;
    tokio::time::timeout(Duration::from_secs(90), async {
        loop {
            if let Response::Files { snapshot } = request(
                &child,
                Request::Files {
                    request: FileRequest::List { conversation: None },
                },
            )
            .await
            {
                if snapshot
                    .files
                    .iter()
                    .any(|f| f.id == file && matches!(f.state, FileState::Offered))
                {
                    break;
                }
            }
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
    })
    .await
    .expect("actual protected offer");
    request(
        &child,
        Request::Files {
            request: FileRequest::Accept { id: file.into() },
        },
    )
    .await;
    request(
        &sender,
        Request::Submit {
            operation_id: random_id(),
            conversation: Some(channel),
            text: "hello on the invited network".into(),
        },
    )
    .await;
    tokio::time::timeout(Duration::from_secs(120), async {
        loop {
            if let Response::Files { snapshot } = request(
                &child,
                Request::Files {
                    request: FileRequest::List { conversation: None },
                },
            )
            .await
            {
                if snapshot
                    .files
                    .iter()
                    .any(|f| f.id == file && matches!(f.state, FileState::Complete))
                {
                    break;
                }
            }
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
    })
    .await
    .expect("actual protected verified file");
    child.flush().await.unwrap();
    receiver.disconnect().await.unwrap();
    drop(child);
    drop(receiver);
    primary.shutdown().await.unwrap();
    let reopened = ProtocolRuntime::unlock_protected(
        &profile,
        "receiver-test",
        "127.0.0.1:24491".parse().unwrap(),
        None,
        None,
        &[],
    )
    .await
    .unwrap();
    let receiver = service(&receiver_home, reopened.clone());
    request(
        &receiver,
        Request::Unlock {
            passphrase: "receiver-test".into(),
            create: false,
        },
    )
    .await;
    let child = receiver.networks.lock().await[&network].clone();
    assert_eq!(
        child.snapshot().await.unwrap().instance.safety_number,
        child_identity
    );
    assert!(receiver.snapshot().await.unwrap().conversations.is_empty());
    assert_eq!(
        child
            .clone()
            .file_io(
                encode_io(
                    &FileIo {
                        instance: child.snapshot().await.unwrap().instance.id,
                        id: file.into(),
                        piece: 0,
                        upload: false
                    },
                    &[]
                )
                .unwrap()
            )
            .await
            .unwrap(),
        bytes
    );
    let Response::History { page } = request(
        &child,
        Request::History {
            conversation: child_channel,
            before: None,
            limit: 50,
        },
    )
    .await
    else {
        panic!()
    };
    assert!(page
        .messages
        .iter()
        .any(|m| m.body == "hello on the invited network"));
    eprintln!("combined invitation: chat + exact file export survive same-identity reopen");
    receiver.disconnect().await.unwrap();
    drop(child);
    drop(receiver);
    reopened.shutdown().await.unwrap();
    sender.disconnect().await.unwrap();
    drop(sender);
    drop(sender_node);
    sender_runtime.shutdown().await.unwrap();
    for relay in relays {
        relay.shutdown().await;
    }
}
