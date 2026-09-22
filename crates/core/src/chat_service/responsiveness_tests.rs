use super::*;

async fn fixture() -> (tempfile::TempDir, ProtocolRuntime, Arc<ChatService>) {
    let home = tempfile::tempdir().unwrap();
    crate::private_fs::make_private(home.path(), true).unwrap();
    let runtime = ProtocolRuntime::create_fixture(
        &home.path().join("profile"),
        "responsiveness-fixture",
        "127.0.0.1:0".parse().unwrap(),
        None,
        None,
        &[],
    )
    .await
    .unwrap();
    let service = ChatService::new(
        home.path().join("archive"),
        runtime.clone(),
        vec![
            Capability::IdentityRead,
            Capability::ChannelMember,
            Capability::ChannelAdmin,
            Capability::EventRead,
        ],
    )
    .unwrap();
    (home, runtime, service)
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn local_unlock_does_not_wait_for_background_restoration() {
    let (_home, runtime, service) = fixture().await;
    let gate = service.network_operations.lock().await;
    let reply = tokio::time::timeout(
        Duration::from_secs(10),
        service.handle(Request::Unlock {
            passphrase: "responsiveness-fixture".into(),
            create: true,
        }),
    )
    .await
    .expect("local unlock must not wait for the held restoration barrier")
    .unwrap();
    assert!(matches!(reply, Response::Snapshot { snapshot } if !snapshot.instance.locked));
    assert!(service
        .session
        .lock()
        .await
        .as_ref()
        .unwrap()
        .files
        .is_none());
    drop(gate);
    service.handle(Request::Lock).await.unwrap();
    assert!(service
        .handle(Request::Unlock {
            passphrase: "wrong".into(),
            create: false
        })
        .await
        .is_err());
    assert!(service.snapshot().await.unwrap().instance.locked);
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn ordinary_send_can_progress_beside_another_send_and_retains_correlation() {
    let (_home, runtime, service) = fixture().await;
    service
        .handle(Request::Unlock {
            passphrase: "responsiveness-fixture".into(),
            create: true,
        })
        .await
        .unwrap();
    let Response::Applied {
        conversation: Some(channel),
        ..
    } = service
        .handle(Request::Submit {
            operation_id: "create-concurrent-fixture".into(),
            conversation: None,
            text: "/create #parallel me".into(),
        })
        .await
        .unwrap()
    else {
        panic!("channel")
    };
    let in_flight_send = service.operations.read().await;
    let reply = tokio::time::timeout(
        Duration::from_secs(5),
        service.handle(Request::Submit {
            operation_id: "parallel-message-0001".into(),
            conversation: Some(channel.clone()),
            text: "first".into(),
        }),
    )
    .await
    .expect("another send must not globally block admission")
    .unwrap();
    assert!(matches!(reply, Response::Applied { .. }), "{reply:?}");
    drop(in_flight_send);
    let Response::History { page } = service
        .handle(Request::History {
            conversation: channel,
            before: None,
            limit: 20,
        })
        .await
        .unwrap()
    else {
        panic!("history")
    };
    assert_eq!(
        page.messages[0].operation_id.as_deref(),
        Some("parallel-message-0001")
    );
    assert_eq!(
        page.messages[0].delivery,
        Some(gchat_api::Delivery::LocalAccepted)
    );
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
}

#[test]
fn message_metadata_preserves_old_archive_layout_and_survives_sidecar_reopen() {
    use crate::model::{Message as StoredMessage, ScopedPmRecord};
    let home = tempfile::tempdir().unwrap();
    crate::private_fs::make_private(home.path(), true).unwrap();
    let message = StoredMessage {
        id: [7; 16],
        operation_id: Some("same-operation".into()),
        delivery: Some(gchat_api::Delivery::Delivered),
        ts_unix: 42,
        sender_member_id: None,
        sender_name: "Me".into(),
        mine: true,
        text: "retained history".into(),
    };
    // The old message has precisely these positional fields, with no metadata.
    let old_message = (
        &message.id,
        message.ts_unix,
        message.sender_member_id,
        &message.sender_name,
        message.mine,
        &message.text,
    );
    assert_eq!(
        postcard::to_allocvec(&message).unwrap(),
        postcard::to_allocvec(&old_message).unwrap()
    );
    let mut archive = ArchiveData::default();
    archive.scoped_pms.push(ScopedPmRecord {
        id: ScopedPmId {
            channel_id: gcoms::sdk::ChannelId([1; 32]),
            self_member_id: MemberId([2; 32]),
            remote_member_id: MemberId([3; 32]),
        },
        remote_display_name: "Peer".into(),
        messages: vec![message],
        active: true,
    });
    let old_archive = (
        &archive.daemon_safety_number,
        &archive.channels,
        &archive.scoped_pms,
        &archive.public_descriptors,
        &archive.legacy,
    );
    assert_eq!(
        postcard::to_allocvec(&archive).unwrap(),
        postcard::to_allocvec(&old_archive).unwrap()
    );
    let (archive_store, _) = crate::store::ArchiveStore::create(
        &home.path().join("archive"),
        "test-pass",
        "safety".into(),
    )
    .unwrap();
    archive_store.save(&archive).unwrap();
    drop(archive_store);
    let (_, reopened) =
        crate::store::ArchiveStore::open(&home.path().join("archive"), "test-pass").unwrap();
    assert_eq!(reopened.scoped_pms[0].messages[0].text, "retained history");
    assert!(reopened.scoped_pms[0].messages[0].operation_id.is_none());
    let (store, mut state): (_, UiState) =
        ChatServiceStore::open_or_create(&home.path().join("ui"), "test-pass").unwrap();
    observe_messages(&mut state, &archive);
    store.save(&state).unwrap();
    drop(store);
    let (_, mut state): (_, UiState) =
        ChatServiceStore::open_or_create(&home.path().join("ui"), "test-pass").unwrap();
    observe_messages(&mut state, &reopened); // No RAM hints must not erase a retained ACK.
    let visible = super::message("pm", &reopened.scoped_pms[0].messages[0], &state);
    assert_eq!(visible.operation_id.as_deref(), Some("same-operation"));
    assert_eq!(visible.delivery, Some(gchat_api::Delivery::Delivered));
}
