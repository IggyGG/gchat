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

#[test]
fn reconnect_command_keeps_codes_out_of_recall_and_requires_channel_context() {
    assert_eq!(
        recall_text("/reconnect gchat-reconnect1:private"),
        "/reconnect"
    );
    assert_eq!(
        recall_text("/RECONNECT gchat-reconnect1:private"),
        "/reconnect"
    );
    assert_eq!(command_usage("/reconnect"), "/reconnect [code]");
    assert!(command_catalogue(&[Capability::ChannelMember])
        .iter()
        .any(|c| c.text == "/reconnect"));
    assert!(context_channel(&ArchiveData::default(), None).is_err());
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn updater_waits_for_real_mutation_and_refuses_failed_archive_checkpoint() {
    let (home, runtime, service) = fixture().await;
    service
        .handle(Request::Unlock {
            passphrase: "responsiveness-fixture".into(),
            create: true,
        })
        .await
        .unwrap();
    let gate = service.operations.write().await;
    let pending = {
        let service = service.clone();
        tokio::spawn(async move {
            service
                .handle(Request::Submit {
                    operation_id: "update-retained-create".into(),
                    conversation: None,
                    text: "/create #retained owner".into(),
                })
                .await
        })
    };
    // Wait until the actual public request enters maintenance accounting, while
    // the existing operation barrier keeps its mutation unfinished.
    tokio::time::timeout(Duration::from_secs(5), async {
        loop {
            if service.update_gate.active_requests() > 0 {
                break;
            }
            tokio::task::yield_now().await;
        }
    })
    .await
    .unwrap();
    assert!(service.pause_for_update().await.is_err());
    drop(gate);
    let response = pending.await.unwrap().unwrap();
    assert!(matches!(
        response,
        Response::Applied {
            conversation: Some(_),
            ..
        }
    ));
    let archive = home.path().join("archive");
    let backup = home.path().join("archive-retained");
    std::fs::rename(&archive, &backup).unwrap();
    std::fs::create_dir(&archive).unwrap();
    assert!(service.pause_for_update().await.is_err());
    std::fs::remove_dir(&archive).unwrap();
    std::fs::rename(&backup, &archive).unwrap();
    // Failed preparation resumes admission, and the same archive can checkpoint.
    service.handle(Request::Lock).await.unwrap();
    service.pause_for_update().await.unwrap();
    assert!(service
        .handle(Request::Submit {
            operation_id: "must-not-admit-update".into(),
            conversation: None,
            text: "/create #rejected owner".into()
        })
        .await
        .is_err());
    service.resume_after_update().await;
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn idle_windows_share_projection_and_lock_wakes_every_waiter() {
    let (_home, runtime, service) = fixture().await;
    // Keep background file restoration out of this snapshot-cache assertion.
    let gate = service.network_operations.lock().await;
    service
        .handle(Request::Unlock {
            passphrase: "responsiveness-fixture".into(),
            create: true,
        })
        .await
        .unwrap();
    {
        let mut session = service.session.lock().await;
        let state = &mut session.as_mut().unwrap().state;
        for index in 0..OPERATION_LIMIT {
            state.operations.insert(
                format!("retained-{index:04}"),
                OperationRecord {
                    action: "fixture".into(),
                    conversation: None,
                    digest: String::new(),
                    at: now(),
                    rpc: None,
                    response: Some(Response::Output {
                        conversation: None,
                        output: gchat_api::CommandOutput::Text {
                            title: "retained result".into(),
                            text: "x".repeat(1024),
                        },
                    }),
                },
            );
        }
    }
    service.invalidate();
    let first = service.snapshot().await.unwrap();
    assert_eq!(first.operations.as_ref().unwrap().len(), 30);
    let builds = service
        .presentation
        .builds
        .load(std::sync::atomic::Ordering::Relaxed);
    let mut waiters = Vec::new();
    for _ in 0..4 {
        let service = service.clone();
        let after = first.revision.clone();
        waiters.push(tokio::spawn(async move {
            service
                .handle(Request::Events {
                    after,
                    wait_ms: 2000,
                })
                .await
                .unwrap()
        }));
    }
    tokio::time::sleep(Duration::from_millis(450)).await;
    assert!(waiters.iter().all(|w| !w.is_finished()));
    assert_eq!(
        builds,
        service
            .presentation
            .builds
            .load(std::sync::atomic::Ordering::Relaxed),
        "idle windows must not repeatedly project/copy retained history"
    );
    drop(gate);
    service.handle(Request::Lock).await.unwrap();
    for waiter in waiters {
        let result = tokio::time::timeout(Duration::from_secs(1), waiter)
            .await
            .unwrap()
            .unwrap();
        assert!(matches!(result, Response::Changed { revision } if revision != first.revision));
    }
    let locked = service.snapshot().await.unwrap();
    assert!(locked.instance.locked);
    assert!(locked.conversations.is_empty());
    assert!(locked.operations.unwrap().is_empty());
    assert!(locked.activity.unwrap().is_empty());
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn cached_snapshot_observes_local_send_and_cancelled_wait_does_not_consume_changes() {
    let (_home, runtime, service) = fixture().await;
    service
        .handle(Request::Unlock {
            passphrase: "responsiveness-fixture".into(),
            create: true,
        })
        .await
        .unwrap();
    let first = service.snapshot().await.unwrap();
    let cancelled = tokio::spawn({
        let service = service.clone();
        let after = first.revision.clone();
        async move {
            service
                .handle(Request::Events {
                    after,
                    wait_ms: 20000,
                })
                .await
        }
    });
    tokio::task::yield_now().await;
    cancelled.abort();
    let _ = cancelled.await;
    let Response::Applied {
        conversation: Some(channel),
        ..
    } = service
        .handle(Request::Submit {
            operation_id: "cache-create-channel".into(),
            conversation: None,
            text: "/create #cached me".into(),
        })
        .await
        .unwrap()
    else {
        panic!("channel");
    };
    let created = service.snapshot().await.unwrap();
    assert_ne!(created.revision, first.revision);
    assert!(created.conversations.iter().any(|c| c.id == channel));
    service
        .handle(Request::Submit {
            operation_id: "cache-send-message".into(),
            conversation: Some(channel.clone()),
            text: "retained".into(),
        })
        .await
        .unwrap();
    let Response::Changed { revision } = service
        .handle(Request::Events {
            after: created.revision,
            wait_ms: 20000,
        })
        .await
        .unwrap()
    else {
        panic!("changed");
    };
    let sent = service.snapshot().await.unwrap();
    assert_eq!(sent.revision, revision);
    assert!(sent
        .conversations
        .iter()
        .find(|c| c.id == channel)
        .unwrap()
        .last_message_id
        .is_some());
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
}

/// Run explicitly on an otherwise quiet Linux worker. Measure process CPU,
/// including normal background tasks, with one shared profile and four views.
#[cfg(target_os = "linux")]
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
#[ignore = "three 60-second CPU samples; run separately from functional tests"]
async fn idle_cpu_large_history_measurement() {
    fn cpu_ticks() -> u64 {
        let stat = std::fs::read_to_string("/proc/self/stat").unwrap();
        let values: Vec<_> = stat
            .rsplit_once(')')
            .unwrap()
            .1
            .split_whitespace()
            .collect();
        values[11].parse::<u64>().unwrap() + values[12].parse::<u64>().unwrap()
    }
    let ticks_per_second: f64 = String::from_utf8(
        std::process::Command::new("getconf")
            .arg("CLK_TCK")
            .output()
            .unwrap()
            .stdout,
    )
    .unwrap()
    .trim()
    .parse()
    .unwrap();
    let (_home, runtime, service) = fixture().await;
    service
        .handle(Request::Unlock {
            passphrase: "responsiveness-fixture".into(),
            create: true,
        })
        .await
        .unwrap();
    tokio::time::timeout(Duration::from_secs(10), async {
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
            tokio::time::sleep(Duration::from_millis(50)).await;
        }
    })
    .await
    .unwrap();
    {
        let mut session = service.session.lock().await;
        let state = &mut session.as_mut().unwrap().state;
        for index in 0..OPERATION_LIMIT {
            state.operations.insert(
                format!("retained-{index:04}"),
                OperationRecord {
                    action: "fixture".into(),
                    conversation: None,
                    digest: String::new(),
                    at: now(),
                    rpc: None,
                    response: Some(Response::Output {
                        conversation: None,
                        output: gchat_api::CommandOutput::Text {
                            title: "retained result".into(),
                            text: "x".repeat(1024),
                        },
                    }),
                },
            );
        }
    }
    let mut views = Vec::new();
    for _ in 0..4 {
        let service = service.clone();
        views.push(tokio::spawn(async move {
            let mut after = String::new();
            loop {
                if let Response::Changed { revision } = service
                    .handle(Request::Events {
                        after: after.clone(),
                        wait_ms: 20000,
                    })
                    .await
                    .unwrap()
                {
                    after = revision;
                }
            }
        }));
    }
    tokio::time::sleep(Duration::from_secs(2)).await;
    for sample in 0..3 {
        let ticks = cpu_ticks();
        let start = Instant::now();
        tokio::time::sleep(Duration::from_secs(60)).await;
        let elapsed = start.elapsed().as_secs_f64();
        let cpu = (cpu_ticks() - ticks) as f64 / ticks_per_second;
        eprintln!(
            "IDLE_CPU {}",
            serde_json::json!({
                "sample": sample, "wall_seconds": elapsed, "cpu_seconds": cpu,
                "percent_one_core": cpu * 100.0 / elapsed, "operations": OPERATION_LIMIT,
                "views": 4,
            })
        );
    }
    for view in views {
        view.abort();
        let _ = view.await;
    }
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
}
