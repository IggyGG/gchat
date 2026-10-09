//! Same UI/service commands, three real encrypted profiles and loopback nodes.
//! This is an application journey, not a deployed-provider/device receipt.
use super::*;
use crate::chat_service::ChatEndpoint;
use gchat_api::{
    files::{encode_io, FileIo},
    CommandOutput, FileRequest, FileState,
};

async fn request(service: &Arc<ChatService>, req: Request) -> Response {
    let response = Box::pin(service.handle(req)).await.unwrap();
    assert!(!matches!(response, Response::Error { .. }), "{response:?}");
    response
}
async fn command(service: &Arc<ChatService>, conversation: Option<&str>, text: String) -> Response {
    request(
        service,
        Request::Submit {
            operation_id: random_id(),
            conversation: conversation.map(str::to_owned),
            text,
        },
    )
    .await
}
async fn open(home: &Path, reopen: bool, port: u16) -> (ProtocolRuntime, Arc<ChatService>) {
    crate::paths::ensure_private_dir(home, "invitation fixture").unwrap();
    let path = home.join("protocol.enc");
    let address = format!("127.0.0.1:{port}").parse().unwrap();
    let runtime = if reopen {
        ProtocolRuntime::unlock_fixture(&path, "test-only-passphrase", address, None, None, &[])
            .await
            .unwrap()
    } else {
        ProtocolRuntime::create_fixture(&path, "test-only-passphrase", address, None, None, &[])
            .await
            .unwrap()
    };
    let service = ChatService::new(
        home.join("archive"),
        runtime.clone(),
        vec![
            Capability::IdentityRead,
            Capability::ChannelMember,
            Capability::ChannelAdmin,
            Capability::EventRead,
        ],
    )
    .unwrap();
    request(
        &service,
        Request::Unlock {
            passphrase: "test-only-passphrase".into(),
            create: !reopen,
        },
    )
    .await;
    tokio::time::timeout(Duration::from_secs(15), async {
        loop {
            if service
                .session
                .lock()
                .await
                .as_ref()
                .unwrap()
                .files
                .is_some()
            {
                break;
            }
            tokio::time::sleep(Duration::from_millis(20)).await;
        }
    })
    .await
    .expect("file runtime opens independently");
    (runtime, service)
}
async fn join(service: &Arc<ChatService>, link: &str, name: &str) -> String {
    let response = command(service, None, format!("/join {link} {name}")).await;
    let Response::Output {
        output: CommandOutput::Enrollment { id, .. },
        ..
    } = response
    else {
        panic!("saved enrollment response: {response:?}")
    };
    tokio::time::timeout(Duration::from_secs(80),async {loop {
        let response=request(service,Request::Enrollment{id:id.clone(),action:"status".into()}).await;
        if matches!(response,Response::Output{output:CommandOutput::Enrollment{phase,..},..} if phase=="joined") {break;}
        tokio::time::sleep(Duration::from_millis(100)).await;
    }}).await.expect("durable enrollment finishes");
    service.snapshot().await.unwrap().conversations[0]
        .id
        .clone()
}
async fn history_contains(service: &Arc<ChatService>, channel: &str, text: &str) {
    tokio::time::timeout(Duration::from_secs(45), async {
        loop {
            if let Response::History { page } = request(
                service,
                Request::History {
                    conversation: channel.into(),
                    before: None,
                    limit: 100,
                },
            )
            .await
            {
                if page.messages.iter().any(|m| m.body == text) {
                    break;
                }
            }
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
    })
    .await
    .expect("remote message in encrypted archive");
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn typed_invitation_response_retries_and_reopens_without_another_mint() {
    use gchat_api::rpc::{ChatClient as TypedChat, SubmitOutcome};
    use gcoms::rpc::{Caller, Client, EmbeddedTransport, ErrorCode};
    tokio::time::timeout(Duration::from_secs(60), async {
        let home = tempfile::tempdir().unwrap();
        crate::private_fs::make_private(home.path(), true).unwrap();
        let (runtime, service) = Box::pin(open(home.path(), false, 0)).await;
        command(&service, None, "/create reusable Owner".into()).await;
        let channel = service.snapshot().await.unwrap().conversations[0]
            .id
            .clone();
        let typed = |service: Arc<ChatService>| {
            TypedChat::new(Client::new(
                EmbeddedTransport {
                    router: rpc::router(service.clone()).unwrap(),
                    caller: Caller {
                        principal: "local-owner".into(),
                    },
                    destination: "invitation-fixture".into(),
                },
                service.id.clone(),
            ))
        };
        let client = typed(service.clone());
        let prepared = client
            .prepare_submit(Some(channel.clone()), "/invite friends".into())
            .unwrap();
        let response: Response = client.inner.start_and_wait(&prepared).await.unwrap().into();
        let Response::Output {
            output: CommandOutput::ReusableInvitation { link, id, .. },
            ..
        } = &response
        else {
            panic!("typed invitation must return its bearer result: {response:?}")
        };
        assert!(!link.is_empty());
        assert_eq!(id.len(), 32);
        let expected = serde_json::to_value(&response).unwrap();
        let repeated: Response = client.inner.start_and_wait(&prepared).await.unwrap().into();
        assert_eq!(serde_json::to_value(repeated).unwrap(), expected);
        let snapshot = service.snapshot().await.unwrap();
        assert!(!serde_json::to_string(&snapshot).unwrap().contains(link));
        let operation = snapshot
            .operations
            .as_ref()
            .unwrap()
            .iter()
            .find(|r| r.id == prepared.handle.operation.id.as_str())
            .unwrap();
        assert!(matches!(operation.output, Some(CommandOutput::Text { .. })));
        assert!(client.lock().await.unwrap().locked);
        assert_eq!(
            client
                .inner
                .status(&prepared.handle)
                .await
                .unwrap_err()
                .code,
            ErrorCode::Unauthorized
        );
        client
            .unlock("test-only-passphrase".into(), false)
            .await
            .unwrap();
        drop(client);
        service.disconnect().await.unwrap();
        drop(service);
        runtime.shutdown().await.unwrap();

        let (runtime, service) = Box::pin(open(home.path(), true, 0)).await;
        let client = typed(service.clone());
        let resumed = client
            .inner
            .resume::<SubmitOutcome, gchat_api::ChatError>(&prepared.handle)
            .await
            .unwrap();
        assert_eq!(
            serde_json::to_value(Response::from(resumed)).unwrap(),
            expected
        );
        let repeated: Response = client.inner.start_and_wait(&prepared).await.unwrap().into();
        assert_eq!(serde_json::to_value(repeated).unwrap(), expected);
        let Response::Output {
            output: CommandOutput::Invitations { records, .. },
            ..
        } = command(&service, Some(&channel), "/invites".into()).await
        else {
            panic!("invitation ledger")
        };
        assert_eq!(
            records.len(),
            1,
            "same operation must not consume another invitation slot"
        );
        assert_eq!(&records[0].id, id);
        assert!(!serde_json::to_string(&service.snapshot().await.unwrap())
            .unwrap()
            .contains(link));
        drop(client);
        service.disconnect().await.unwrap();
        drop(service);
        runtime.shutdown().await.unwrap();
    })
    .await
    .expect("bounded single-profile typed invitation recovery");
}

#[tokio::test(flavor = "multi_thread", worker_threads = 4)]
async fn friends_reuse_one_invitation_for_chat_file_reopen_and_revocation() {
    tokio::time::timeout(Duration::from_secs(180), Box::pin(journey()))
        .await
        .expect("bounded three-client journey");
}
async fn journey() {
    eprintln!("three-client journey started");
    let home = tempfile::tempdir().unwrap();
    crate::private_fs::make_private(home.path(), true).unwrap();
    let (owner_runtime, owner) = Box::pin(open(&home.path().join("owner"), false, 0)).await;
    eprintln!("owner profile ready");
    command(&owner, None, "/create friends Owner".into()).await;
    let channel = owner.snapshot().await.unwrap().conversations[0].id.clone();
    assert!(matches!(
        command(&owner, Some(&channel), "/invite".into()).await,
        Response::Output {
            output: CommandOutput::InvitationOptions { .. },
            ..
        }
    ));
    let response = command(&owner, Some(&channel), "/invite friends".into()).await;
    let Response::Output {
        output:
            CommandOutput::ReusableInvitation {
                link,
                id,
                limit,
                local_only,
                ..
            },
        ..
    } = response
    else {
        panic!("reusable invitation response: {response:?}")
    };
    assert_eq!(limit, Some(25));
    assert!(local_only);
    let alice_home = home.path().join("alice");
    let (alice_runtime, alice) = Box::pin(open(&alice_home, false, 0)).await;
    let (bob_runtime, bob) = Box::pin(open(&home.path().join("bob"), false, 0)).await;
    eprintln!("all three profiles ready");
    let (alice_channel, bob_channel) =
        tokio::join!(join(&alice, &link, "Alice"), join(&bob, &link, "Bob"));
    let response = command(&owner, Some(&channel), "/invites".into()).await;
    assert!(
        matches!(response,Response::Output{output:CommandOutput::Invitations{records,..},..} if records[0].admitted==2)
    );
    command(&owner, Some(&channel), "hello friends".into()).await;
    tokio::join!(
        history_contains(&alice, &alice_channel, "hello friends"),
        history_contains(&bob, &bob_channel, "hello friends")
    );
    command(&bob, Some(&bob_channel), "hello back".into()).await;
    history_contains(&owner, &channel, "hello back").await;
    let file = "73737373737373737373737373737373";
    let bytes = vec![0x7b; 16 * 1024 + 11];
    request(
        &owner,
        Request::Files {
            request: FileRequest::Prepare {
                id: file.into(),
                conversation: channel.clone(),
                name: "friends.bin".into(),
                size_bytes: bytes.len().to_string(),
            },
        },
    )
    .await;
    owner
        .clone()
        .file_io(
            encode_io(
                &FileIo {
                    instance: owner.snapshot().await.unwrap().instance.id,
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
        &owner,
        Request::Files {
            request: FileRequest::Commit { id: file.into() },
        },
    )
    .await;
    tokio::time::timeout(Duration::from_secs(40), async {
        loop {
            if let Response::Files { snapshot } = request(
                &alice,
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
    .expect("file offer reaches Alice");
    request(
        &alice,
        Request::Files {
            request: FileRequest::Accept { id: file.into() },
        },
    )
    .await;
    tokio::time::timeout(Duration::from_secs(40), async {
        loop {
            if let Response::Files { snapshot } = request(
                &alice,
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
    .expect("file completely verified");
    let identity = alice.snapshot().await.unwrap().instance.safety_number;
    let port = alice_runtime
        .embedded()
        .unwrap()
        .node()
        .current_info()
        .await
        .unwrap()
        .aliases[0]
        .target
        .address
        .port();
    alice.flush().await.unwrap();
    alice.disconnect().await.unwrap();
    drop(alice);
    alice_runtime.shutdown().await.unwrap();
    let (alice_runtime, alice) = Box::pin(open(&alice_home, true, port)).await;
    assert_eq!(
        alice.snapshot().await.unwrap().instance.safety_number,
        identity
    );
    history_contains(&alice, &alice_channel, "hello friends").await;
    assert_eq!(
        alice
            .clone()
            .file_io(
                encode_io(
                    &FileIo {
                        instance: alice.snapshot().await.unwrap().instance.id,
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
    command(&owner, Some(&channel), format!("/revoke-invite {id}")).await;
    command(
        &owner,
        Some(&channel),
        "members stay after revocation".into(),
    )
    .await;
    history_contains(&bob, &bob_channel, "members stay after revocation").await;
    // A fresh identity receives a durable rejected status, never membership.
    let (outsider_runtime, outsider) =
        Box::pin(open(&home.path().join("outsider"), false, 0)).await;
    let Response::Output {
        output: CommandOutput::Enrollment { id: op, .. },
        ..
    } = command(&outsider, None, format!("/join {link} Outsider")).await
    else {
        panic!("saved join")
    };
    tokio::time::timeout(Duration::from_secs(30), async {
        loop {
            if let Response::Output {
                output:
                    CommandOutput::Enrollment {
                        message: Some(message),
                        ..
                    },
                ..
            } = request(
                &outsider,
                Request::Enrollment {
                    id: op.clone(),
                    action: "status".into(),
                },
            )
            .await
            {
                if message.contains("revoked") {
                    break;
                }
            }
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
    })
    .await
    .expect("revocation refusal returned to fresh identity");
    assert!(outsider.snapshot().await.unwrap().conversations.is_empty());
    request(
        &outsider,
        Request::Enrollment {
            id: op.clone(),
            action: "cancel".into(),
        },
    )
    .await;
    request(
        &outsider,
        Request::Enrollment {
            id: op,
            action: "retire".into(),
        },
    )
    .await;
    eprintln!("same invitation: two identities, bidirectional messages, exact 16KiB file, encrypted reopen, revocation and cancellation passed");
    for (runtime, service) in [
        (outsider_runtime, outsider),
        (alice_runtime, alice),
        (bob_runtime, bob),
        (owner_runtime, owner),
    ] {
        service.disconnect().await.unwrap();
        drop(service);
        runtime.shutdown().await.unwrap();
    }
}
