#![cfg(any(unix, windows))]
use gchat_api::{ChatClient, Request, RequestEnvelope, Response, Snapshot, VERSION};
use gchat_core::{
    chat_service::{self, ChatService},
    runtime::ProtocolRuntime,
};
use gcoms::sdk::{ipc::Capability, ChannelVisibility, GcClient};
use std::{path::Path, sync::Arc, time::Duration};

const PASS: &str = "shared-archive-passphrase";

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn channel_owner_can_transfer_and_leave_without_replacing_channel_identity() {
    if let Ok(path) = std::env::var("GCHAT_TEST_METRICS") {
        gcoms_node::metrics::init(std::path::Path::new(&path)).unwrap();
    }
    let a = tempfile::tempdir().unwrap();
    let b = tempfile::tempdir().unwrap();
    let c = tempfile::tempdir().unwrap();
    let ar = open_runtime(a.path(), true).await;
    let br = open_runtime(b.path(), true).await;
    let cr = open_runtime(c.path(), true).await;
    let service = make_service(a.path(), ar.clone());
    unlock(&service, true).await;
    let Response::Applied {
        conversation: Some(channel),
        ..
    } = submit(
        &service,
        "ownership-create1",
        None,
        "/create #handoff original",
    )
    .await
    else {
        panic!("create");
    };
    let owner = ar.sdk_client();
    let next = br.sdk_client();
    let newcomer = cr.sdk_client();
    let id = owner.list_channels().await.unwrap()[0].id;
    let join = next.prepare_channel_join("successor").await.unwrap();
    let package = next.channel_key_package(join).await.unwrap();
    let welcome = owner
        .admit_channel("handoff", &package, "successor")
        .await
        .unwrap();
    next.join_channel(join, "handoff", ChannelVisibility::Private, &welcome)
        .await
        .unwrap();
    let next_service = make_service(b.path(), br.clone());
    unlock(&next_service, true).await;
    assert!(matches!(
        submit(&service, "ownership-refresh", None, "/refresh").await,
        Response::Applied { .. }
    ));
    let response = submit(
        &service,
        "ownership-part-01",
        Some(&channel),
        "/part --transfer successor",
    )
    .await;
    assert!(matches!(response, Response::Applied { .. }), "{response:?}");
    eprintln!("handoff: accepted transfer and leave");
    tokio::time::timeout(Duration::from_secs(25), async {
        loop {
            let old = owner.list_channels().await.unwrap();
            let current = next.list_channels().await.unwrap();
            if old.is_empty() && current[0].role == gcoms::sdk::ChannelRole::Owner {
                break;
            }
            tokio::time::sleep(Duration::from_millis(50)).await;
        }
    })
    .await
    .unwrap_or_else(|error| panic!("authenticated leave is processed by successor: {error}"));
    assert_eq!(next.list_channels().await.unwrap()[0].id, id);
    let join = newcomer.prepare_channel_join("newcomer").await.unwrap();
    let package = newcomer.channel_key_package(join).await.unwrap();
    let welcome = next
        .admit_channel("handoff", &package, "newcomer")
        .await
        .unwrap();
    newcomer
        .join_channel(join, "handoff", ChannelVisibility::Private, &welcome)
        .await
        .unwrap();
    assert_eq!(newcomer.list_channels().await.unwrap()[0].id, id);
    assert_eq!(next.channel_roster("handoff").await.unwrap().len(), 2);
    let mut incoming = next.subscribe_events();
    newcomer
        .send_channel("handoff", b"after ownership transfer")
        .await
        .unwrap();
    tokio::time::timeout(Duration::from_secs(15), async {
        loop { if matches!(incoming.recv().await, Some(gcoms::sdk::ClientEvent::ChannelMessage { body, .. }) if body == b"after ownership transfer") { break; } }
    }).await.unwrap();
    let archive = service.snapshot().await.unwrap();
    assert!(!archive.conversations[0].active);
    assert_eq!(
        archive
            .activity
            .as_ref()
            .unwrap()
            .iter()
            .filter(|a| a.kind == "left" && a.conversation == archive.conversations[0].id)
            .count(),
        1
    );
    assert_eq!(service.snapshot().await.unwrap().activity, archive.activity);
    assert_eq!(
        archive.conversations[0].kind,
        gchat_api::ConversationKind::Archive
    );
    assert!(
        newcomer
            .change_channel("handoff", gcoms::sdk::ChannelChange::Close)
            .await
            .is_err(),
        "members cannot close the channel"
    );
    let current = next_service.snapshot().await.unwrap();
    let channel = current
        .conversations
        .iter()
        .find(|c| c.active)
        .unwrap()
        .id
        .clone();
    let response = submit(
        &next_service,
        "ownership-close01",
        Some(&channel),
        "/part --close",
    )
    .await;
    assert!(matches!(response, Response::Applied { .. }), "{response:?}");
    tokio::time::timeout(Duration::from_secs(15), async {
        while !newcomer.list_channels().await.unwrap().is_empty()
            || !next.list_channels().await.unwrap().is_empty()
        {
            tokio::time::sleep(Duration::from_millis(50)).await;
        }
    })
    .await
    .expect("authenticated closure reaches all members");
    assert!(next.send_channel("handoff", b"after close").await.is_err());
    assert!(newcomer
        .send_channel("handoff", b"after close")
        .await
        .is_err());
    service.disconnect().await.unwrap();
    next_service.disconnect().await.unwrap();
    drop(service);
    drop(next_service);
    drop(owner);
    drop(next);
    drop(newcomer);
    drop(incoming);
    ar.shutdown().await.unwrap();
    br.shutdown().await.unwrap();
    cr.shutdown().await.unwrap();
    let reopened = open_runtime(b.path(), false).await;
    assert!(
        reopened
            .sdk_client()
            .list_channels()
            .await
            .unwrap()
            .is_empty(),
        "closure survives restart"
    );
    reopened.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn channel_topic_and_nickname_are_authenticated_shared_and_retained() {
    let a = tempfile::tempdir().unwrap();
    let b = tempfile::tempdir().unwrap();
    let ar = open_runtime(a.path(), true).await;
    let br = open_runtime(b.path(), true).await;
    let service = make_service(a.path(), ar.clone());
    unlock(&service, true).await;
    let Response::Applied {
        conversation: Some(channel),
        ..
    } = submit(
        &service,
        "metadata-create-01",
        None,
        "/create #metadata owner",
    )
    .await
    else {
        panic!("create");
    };
    let original = service.snapshot().await.unwrap();
    assert!(
        original.activity.as_ref().unwrap().is_empty(),
        "initial roster is a baseline, not joins"
    );
    let stable_id = original.conversations[0].members[0].id.clone();
    for (operation, text) in [
        ("metadata-topic-01", "/topic A shared topic"),
        ("metadata-nick-001", "/nick Host"),
    ] {
        let response = submit(&service, operation, Some(&channel), text).await;
        assert!(matches!(response, Response::Applied { .. }), "{response:?}");
    }
    let owner = ar.sdk_client();
    let peer = br.sdk_client();
    let join = peer.prepare_channel_join("participant").await.unwrap();
    let key = peer.channel_key_package(join).await.unwrap();
    let welcome = owner
        .admit_channel("metadata", &key, "participant")
        .await
        .unwrap();
    peer.join_channel(join, "metadata", ChannelVisibility::Private, &welcome)
        .await
        .unwrap();
    let receiver = make_service(b.path(), br.clone());
    unlock(&receiver, true).await;
    let receiver_channel = receiver.snapshot().await.unwrap().conversations[0]
        .id
        .clone();
    tokio::time::timeout(Duration::from_secs(15), async {
        loop {
            let state = receiver.snapshot().await.unwrap();
            let row = &state.conversations[0];
            if row.topic == "A shared topic"
                && row
                    .members
                    .iter()
                    .any(|m| m.id == stable_id && m.nickname == "Host")
            {
                break;
            }
            tokio::time::sleep(Duration::from_millis(50)).await;
        }
    })
    .await
    .expect("newly admitted member receives existing metadata");
    assert!(
        matches!(submit(&receiver, "metadata-forged-01", Some(&receiver_channel), "/topic forged").await, Response::Error { code, .. } if code == "rejected")
    );
    assert!(matches!(
        submit(
            &receiver,
            "metadata-peer-nick",
            Some(&receiver_channel),
            "/nick Guest"
        )
        .await,
        Response::Applied { .. }
    ));
    assert_eq!(
        owner.channel_topic("metadata").await.unwrap(),
        "A shared topic"
    );
    let state = service.snapshot().await.unwrap();
    assert_eq!(
        state.conversations[0]
            .members
            .iter()
            .find(|m| m.is_self)
            .unwrap()
            .id,
        stable_id
    );
    receiver.disconnect().await.unwrap();
    service.disconnect().await.unwrap();
    drop(owner);
    drop(peer);
    drop(receiver);
    drop(service);
    ar.shutdown().await.unwrap();
    br.shutdown().await.unwrap();
    let reopened = open_runtime(a.path(), false).await;
    let service = make_service(a.path(), reopened.clone());
    unlock(&service, false).await;
    let state = service.snapshot().await.unwrap();
    assert_eq!(state.conversations[0].topic, "A shared topic");
    let activity = state.activity.as_ref().unwrap();
    assert_eq!(
        activity
            .iter()
            .filter(|a| a.kind == "topic" && a.text == "Topic: A shared topic")
            .count(),
        1
    );
    let again = service.snapshot().await.unwrap();
    assert_eq!(
        again.activity, state.activity,
        "refresh/reopen cannot repeat activity"
    );
    let operation = state
        .operations
        .as_ref()
        .unwrap()
        .iter()
        .find(|r| r.id == "metadata-topic-01")
        .unwrap();
    assert_eq!(operation.action, "/topic");
    assert_eq!(operation.state, "complete");
    assert_eq!(operation.conversation.as_deref(), Some(channel.as_str()));
    let own = state.conversations[0]
        .members
        .iter()
        .find(|m| m.is_self)
        .unwrap();
    assert_eq!(own.nickname, "Host");
    assert_eq!(own.id, stable_id);
    service.disconnect().await.unwrap();
    reopened.shutdown().await.unwrap();
}

#[cfg(feature = "gc2-carrier")]
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn desktop_default_protected_profile_creates_and_reopens() {
    use chat_service::{
        host::{InstanceConfig, InstanceHost},
        ChatEndpoint,
    };
    let dir = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(dir.path(), true).unwrap();
    let mut config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    assert_eq!(config.listen, "0.0.0.0:0".parse().unwrap());
    assert!(config.advertise.is_none());
    config.gc2_carrier = true;
    // Test desktop startup, independently of provider availability.
    config.network_recovery = false;
    let mut identity = None;
    for create in [true, false] {
        let host = InstanceHost::new(config.clone()).unwrap();
        let response = host
            .dispatch(RequestEnvelope {
                version: VERSION,
                instance_id: Some(host.instance_id().into()),
                request: Request::Unlock {
                    passphrase: PASS.into(),
                    create,
                },
            })
            .await;
        let Response::Snapshot { snapshot } = response.response else {
            panic!("default desktop unlock failed: {response:?}");
        };
        assert!(!snapshot.instance.locked);
        if let Some(expected) = &identity {
            assert_eq!(expected, &snapshot.instance.safety_number);
        } else {
            identity = Some(snapshot.instance.safety_number.clone());
        }
        host.flush().await.unwrap();
    }
}

#[tokio::test(flavor = "multi_thread")]
async fn typed_completion_storage_failure_stays_unknown_live_and_after_reopen() {
    use gcoms::rpc::{CallError, Caller, Client, EmbeddedTransport, ReplyBody};
    use std::sync::atomic::{AtomicUsize, Ordering};
    use tokio::sync::Notify;
    let dir = tempfile::tempdir().unwrap();
    let runtime = open_runtime(dir.path(), true).await;
    let entered = Arc::new(Notify::new());
    let release = Arc::new(Notify::new());
    let calls = Arc::new(AtomicUsize::new(0));
    let route = axum::Router::new().route("/", axum::routing::post({
        let entered = entered.clone(); let release = release.clone(); let calls = calls.clone();
        move |axum::Json(input): axum::Json<serde_json::Value>| {
            let entered = entered.clone(); let release = release.clone(); let calls = calls.clone();
            async move {
                if input["action"] == "list" { return axum::Json(serde_json::json!({"kind":"projection","conversations":[],"revision":"fixture"})); }
                calls.fetch_add(1, Ordering::SeqCst);
                entered.notify_one(); release.notified().await;
                axum::Json(serde_json::json!({"kind":"applied","conversation":null,"notice":null}))
            }
        }
    }));
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let url = format!("http://{}/", listener.local_addr().unwrap());
    let server = tokio::spawn(async move {
        axum::serve(listener, route).await.unwrap();
    });
    for (name, bytes) in [
        (
            "chat.extensions.json",
            serde_json::to_vec(&serde_json::json!({"url":url,"token_file":"test-token"})).unwrap(),
        ),
        ("test-token", b"disposable-storage-fixture".to_vec()),
    ] {
        let path = dir.path().join(name);
        std::fs::write(&path, bytes).unwrap();
        gchat_core::private_fs::make_private(&path, false).unwrap();
    }
    let service = make_service(dir.path(), runtime.clone());
    unlock(&service, true).await;
    assert!(matches!(
        submit(
            &service,
            "create-storage-fixture",
            None,
            "/create #work tester"
        )
        .await,
        Response::Applied { .. }
    ));
    let id = service.snapshot().await.unwrap().instance.id;
    let typed = |service: Arc<ChatService>| {
        gchat_api::rpc::ChatClient::new(Client::new(
            EmbeddedTransport {
                router: chat_service::rpc::router(service).unwrap(),
                caller: Caller {
                    principal: "local-owner".into(),
                },
                destination: "storage-fixture".into(),
            },
            id.clone(),
        ))
    };
    let client = typed(service.clone());
    let prepared = client
        .prepare_submit(None, "/cmd #work ping".into())
        .unwrap();
    assert_eq!(
        client.inner.start(&prepared).await.unwrap(),
        ReplyBody::Running
    );
    tokio::time::timeout(Duration::from_secs(3), entered.notified())
        .await
        .unwrap();
    // The operation is admitted and the benign fixture counted its effect. A
    // directory at the journal filename forces only terminal persistence to fail.
    let journal = dir.path().join("chat.service");
    let retained = dir.path().join("chat.service.retained");
    std::fs::rename(&journal, &retained).unwrap();
    std::fs::create_dir(&journal).unwrap();
    gchat_core::private_fs::make_private(&journal, true).unwrap();
    release.notify_one();
    assert!(matches!(
        client
            .inner
            .resume::<gchat_api::rpc::SubmitOutcome, gchat_api::ChatError>(&prepared.handle)
            .await,
        Err(CallError::OutcomeUnknown(_))
    ));
    std::fs::remove_dir(&journal).unwrap();
    std::fs::rename(&retained, &journal).unwrap();
    assert_eq!(
        client.inner.start(&prepared).await.unwrap(),
        ReplyBody::OutcomeUnknown
    );
    assert_eq!(calls.load(Ordering::SeqCst), 1);
    drop(client);
    service.disconnect().await.unwrap();
    drop(service);
    let service = make_service(dir.path(), runtime.clone());
    unlock(&service, false).await;
    assert_eq!(
        typed(service.clone()).inner.start(&prepared).await.unwrap(),
        ReplyBody::OutcomeUnknown
    );
    assert!(matches!(
        submit(&service, prepared.handle.operation.id.as_str(), None, "/cmd #work ping").await,
        Response::Error { code, .. } if code == "outcome_unknown"
    ));
    assert_eq!(calls.load(Ordering::SeqCst), 1);
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
    server.abort();
}

#[tokio::test(flavor = "multi_thread")]
async fn slow_command_keeps_reads_and_lock_available_without_duplicate_admission() {
    use tokio::sync::Notify;
    let dir = tempfile::tempdir().unwrap();
    let runtime = open_runtime(dir.path(), true).await;
    let entered = Arc::new(Notify::new());
    let release = Arc::new(Notify::new());
    let calls = Arc::new(std::sync::atomic::AtomicUsize::new(0));
    let route = axum::Router::new().route(
        "/",
        axum::routing::post({
            let entered = entered.clone();
            let release = release.clone();
            let calls = calls.clone();
            move |axum::Json(input): axum::Json<serde_json::Value>| {
                let entered = entered.clone();
                let release = release.clone();
                let calls = calls.clone();
                async move {
                    if input["action"] == "list" { return axum::Json(serde_json::json!({"kind":"projection","conversations":[],"revision":"fixture"})); }
                    calls.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
                    entered.notify_one();
                    release.notified().await;
                    axum::Json(serde_json::json!({"kind":"applied","conversation":null,"notice":null}))
                }
            }
        }),
    );
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let url = format!("http://{}/", listener.local_addr().unwrap());
    let server = tokio::spawn(async move {
        axum::serve(listener, route).await.unwrap();
    });
    for (name, bytes) in [
        (
            "chat.extensions.json",
            serde_json::to_vec(&serde_json::json!({"url":url,"token_file":"test-token"})).unwrap(),
        ),
        ("test-token", b"disposable-fixture-token".to_vec()),
    ] {
        let path = dir.path().join(name);
        std::fs::write(&path, bytes).unwrap();
        gchat_core::private_fs::make_private(&path, false).unwrap();
    }
    let service = make_service(dir.path(), runtime.clone());
    unlock(&service, true).await;
    let Response::Applied {
        conversation: Some(channel),
        ..
    } = submit(&service, "create-before-slow", None, "/create #work tester").await
    else {
        panic!("create failed")
    };
    let command = tokio::spawn({
        let service = service.clone();
        async move { submit(&service, "slow-command-original", None, "/cmd #work ping").await }
    });
    tokio::time::timeout(Duration::from_secs(3), entered.notified())
        .await
        .expect("extension request reached handler");
    let check = async {
        assert!(!service.snapshot().await.unwrap().instance.locked);
        assert!(matches!(
            request(
                &service,
                Request::History {
                    conversation: channel,
                    before: None,
                    limit: 200
                }
            )
            .await,
            Response::History { .. }
        ));
        assert!(
            matches!(request(&service, Request::Lock).await, Response::Instance { instance } if instance.locked)
        );
    };
    tokio::time::timeout(Duration::from_secs(2), check)
        .await
        .expect("network command must not hold the session lock");
    release.notify_one();
    assert!(matches!(command.await.unwrap(), Response::Applied { .. }));
    unlock(&service, false).await;
    assert!(matches!(
        submit(&service, "slow-command-original", None, "/cmd #work ping").await,
        Response::Applied { .. }
    ));
    assert_eq!(calls.load(std::sync::atomic::Ordering::SeqCst), 1);
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
    server.abort();
    let _ = server.await;
}

async fn open_runtime(home: &Path, create: bool) -> ProtocolRuntime {
    gchat_core::private_fs::make_private(home, true).unwrap();
    let path = home.join("profile.gcprotocol");
    if create {
        ProtocolRuntime::create_fixture(
            &path,
            PASS,
            "127.0.0.1:0".parse().unwrap(),
            None,
            None,
            &[],
        )
        .await
        .unwrap()
    } else {
        ProtocolRuntime::unlock_fixture(
            &path,
            PASS,
            "127.0.0.1:0".parse().unwrap(),
            None,
            None,
            &[],
        )
        .await
        .unwrap()
    }
}
fn make_service(home: &Path, runtime: ProtocolRuntime) -> Arc<ChatService> {
    ChatService::new(
        home.join("chat.gcarchive"),
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
async fn request(service: &ChatService, request: Request) -> Response {
    let id = service.snapshot().await.unwrap().instance.id;
    service
        .dispatch(RequestEnvelope {
            version: VERSION,
            instance_id: Some(id),
            request,
        })
        .await
        .response
}
async fn unlock(service: &ChatService, create: bool) {
    let reply = request(
        service,
        Request::Unlock {
            passphrase: PASS.into(),
            create,
        },
    )
    .await;
    assert!(matches!(reply, Response::Snapshot { .. }), "{reply:?}");
}
async fn submit(
    service: &ChatService,
    id: &str,
    conversation: Option<&str>,
    text: &str,
) -> Response {
    request(
        service,
        Request::Submit {
            operation_id: id.into(),
            conversation: conversation.map(str::to_string),
            text: text.into(),
        },
    )
    .await
}
async fn snapshot(client: &ChatClient) -> Snapshot {
    let Response::Snapshot { snapshot } = client.request(Request::Snapshot).await.unwrap() else {
        panic!("expected snapshot")
    };
    snapshot
}

#[tokio::test(flavor = "multi_thread")]
async fn two_ui_clients_share_archive_commands_and_pinned_instance() {
    let dir = tempfile::tempdir().unwrap();
    let runtime = open_runtime(dir.path(), true).await;
    let service = make_service(dir.path(), runtime.clone());
    let socket = dir.path().join("chat.sock");
    let (stop, rx) = tokio::sync::watch::channel(false);
    let server = tokio::spawn({
        let service = service.clone();
        let socket = socket.clone();
        async move { chat_service::serve(service, &socket, rx).await }
    });
    let first = tokio::time::timeout(Duration::from_secs(30), async {
        loop {
            if let Ok(client) = ChatClient::connect(&socket, None).await {
                break client;
            }
            assert!(
                !server.is_finished(),
                "chat service stopped before readiness"
            );
            tokio::time::sleep(Duration::from_millis(20)).await;
        }
    })
    .await
    .expect("chat service became ready");
    let second = ChatClient::connect(&socket, Some(first.instance_id()))
        .await
        .unwrap();
    assert!(ChatClient::connect(&socket, Some("another-instance"))
        .await
        .is_err());
    assert!(snapshot(&first).await.instance.locked);
    first
        .request(Request::Unlock {
            passphrase: PASS.into(),
            create: true,
        })
        .await
        .unwrap();
    let created = first
        .request(Request::Submit {
            operation_id: "create-channel-operation".into(),
            conversation: None,
            text: "/create #general tester".into(),
        })
        .await
        .unwrap();
    let Response::Applied {
        conversation: Some(channel),
        ..
    } = created
    else {
        panic!("expected channel")
    };
    let before = snapshot(&second).await;
    assert_eq!(before.conversations[0].id, channel);
    // Queries use the same typed handlers through both compatibility surfaces.
    for query in [
        Request::Identify,
        Request::Snapshot,
        Request::Catalogue {
            conversation: Some(channel.clone()),
        },
        Request::History {
            conversation: channel.clone(),
            before: None,
            limit: 20,
        },
        Request::Search {
            conversation: channel.clone(),
            text: "nothing".into(),
            before: None,
            limit: 20,
        },
        Request::Complete {
            conversation: Some(channel.clone()),
            text: "/hel".into(),
        },
        Request::Events {
            after: String::new(),
            wait_ms: 0,
        },
    ] {
        let legacy = first.request_v2(query.clone()).await.unwrap();
        let typed = second.request_typed(query).await.unwrap();
        assert_eq!(
            serde_json::to_value(legacy).unwrap(),
            serde_json::to_value(typed).unwrap()
        );
    }
    let sent = Request::Submit {
        operation_id: "send-message-operation".into(),
        conversation: Some(channel.clone()),
        text: "  Exact λ text\nsecond line  ".into(),
    };
    first.request(sent.clone()).await.unwrap();
    second.request(sent.clone()).await.unwrap();
    first.request_v2(sent.clone()).await.unwrap();
    assert!(matches!(
        first
            .operation_status("send-message-operation")
            .await
            .unwrap(),
        gcoms::rpc::ReplyBody::Done { .. }
    ));
    let Response::History { page } = second
        .request(Request::History {
            conversation: channel.clone(),
            before: None,
            limit: 100,
        })
        .await
        .unwrap()
    else {
        panic!("expected history")
    };
    assert_eq!(page.messages.len(), 1, "retry must not send twice");
    assert_eq!(page.messages[0].nickname, "tester");
    assert_eq!(page.messages[0].body, "  Exact λ text\nsecond line  ");
    let read = Request::MarkRead {
        conversation: channel.clone(),
        message_id: page.messages[0].id.clone(),
    };
    let typed_read = first.request_typed(read.clone()).await.unwrap();
    let old_read = second.request_v2(read).await.unwrap();
    assert_eq!(
        serde_json::to_value(typed_read).unwrap(),
        serde_json::to_value(old_read).unwrap()
    );
    let changed = first
        .request(Request::Submit {
            operation_id: "send-message-operation".into(),
            conversation: Some(channel.clone()),
            text: "changed".into(),
        })
        .await
        .unwrap_err();
    assert!(changed.contains("different contents"));
    assert_ne!(before.revision, snapshot(&second).await.revision);
    assert_eq!(
        snapshot(&first).await.command_history,
        snapshot(&second).await.command_history
    );
    let Response::Completed { items } = first
        .request(Request::Complete {
            conversation: Some(channel),
            text: "/que".into(),
        })
        .await
        .unwrap()
    else {
        panic!()
    };
    assert_eq!(items[0].text, "/query");
    first.request(Request::Lock).await.unwrap();
    assert!(snapshot(&second).await.instance.locked);
    assert!(snapshot(&second).await.conversations.is_empty());
    assert!(second
        .request(Request::Unlock {
            passphrase: "wrong".into(),
            create: false
        })
        .await
        .is_err());
    // Locking views preserves the sole archive writer and its background receiver.
    let collision = make_service(dir.path(), runtime.clone());
    assert!(matches!(
        request(
            &collision,
            Request::Unlock {
                passphrase: PASS.into(),
                create: false
            }
        )
        .await,
        Response::Error { .. }
    ));
    drop(collision);
    first
        .request(Request::Unlock {
            passphrase: PASS.into(),
            create: false,
        })
        .await
        .unwrap();
    assert_eq!(snapshot(&second).await.conversations.len(), 1);

    stop.send(true).unwrap();
    server.await.unwrap().unwrap();
    drop(first);
    drop(second);
    drop(service);
    runtime.clone().shutdown().await.unwrap();
    drop(runtime);
    tokio::time::sleep(Duration::from_millis(100)).await;

    let runtime = open_runtime(dir.path(), false).await;
    let restored = make_service(dir.path(), runtime.clone());
    unlock(&restored, false).await;
    let state = restored.snapshot().await.unwrap();
    assert_eq!(state.instance.id, before.instance.id);
    assert_eq!(state.conversations.len(), 1);
    assert_ne!(state.instance.boot_id, before.instance.boot_id);
    assert!(matches!(
        request(&restored, sent).await,
        Response::Applied { .. }
    ));
    let disk = std::fs::read(dir.path().join("chat.gcarchive")).unwrap();
    assert!(!disk.windows(b"Exact".len()).any(|w| w == b"Exact"));
    drop(restored);
    runtime.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread")]
async fn separate_instances_and_archive_lock_are_preserved() {
    let a = tempfile::tempdir().unwrap();
    let b = tempfile::tempdir().unwrap();
    let ar = open_runtime(a.path(), true).await;
    let br = open_runtime(b.path(), true).await;
    let first = make_service(a.path(), ar.clone());
    let second = make_service(b.path(), br.clone());
    unlock(&first, true).await;
    unlock(&second, true).await;
    let ainfo = first.snapshot().await.unwrap().instance;
    let binfo = second.snapshot().await.unwrap().instance;
    assert_ne!(ainfo.id, binfo.id);
    assert_ne!(ainfo.safety_number, binfo.safety_number);
    let denied = second
        .dispatch(RequestEnvelope {
            version: VERSION,
            instance_id: Some(ainfo.id),
            request: Request::Snapshot,
        })
        .await;
    assert!(matches!(denied.response, Response::Error { .. }));
    let collision = make_service(a.path(), ar.clone());
    assert!(matches!(
        request(
            &collision,
            Request::Unlock {
                passphrase: PASS.into(),
                create: false
            }
        )
        .await,
        Response::Error { .. }
    ));
    assert!(matches!(
        submit(&first, "first-only-channel", None, "/create #first tester").await,
        Response::Applied { .. }
    ));
    assert!(second.snapshot().await.unwrap().conversations.is_empty());
    drop(collision);
    drop(first);
    drop(second);
    ar.shutdown().await.unwrap();
    br.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread")]
async fn query_identity_is_scoped_to_channel_for_every_participant() {
    let a = tempfile::tempdir().unwrap();
    let b = tempfile::tempdir().unwrap();
    let ar = open_runtime(a.path(), true).await;
    let br = open_runtime(b.path(), true).await;
    let owner = ar.sdk_client();
    let peer = br.sdk_client();
    for name in ["one", "two"] {
        owner
            .create_channel(name, "owner", 8, ChannelVisibility::Private)
            .await
            .unwrap();
        let request = peer.prepare_channel_join("participant").await.unwrap();
        let key = peer.channel_key_package(request).await.unwrap();
        let welcome = owner
            .admit_channel(name, &key, "participant")
            .await
            .unwrap();
        peer.join_channel(request, name, ChannelVisibility::Private, &welcome)
            .await
            .unwrap();
    }
    let service = make_service(a.path(), ar.clone());
    unlock(&service, true).await;
    let channels = service.snapshot().await.unwrap().conversations;
    assert_eq!(channels.len(), 2);
    let first = submit(
        &service,
        "query-channel-one",
        Some(&channels[0].id),
        "/query participant",
    )
    .await;
    let second = submit(
        &service,
        "query-channel-two",
        Some(&channels[1].id),
        "/query participant",
    )
    .await;
    let Response::Applied {
        conversation: Some(first),
        ..
    } = first
    else {
        panic!()
    };
    let Response::Applied {
        conversation: Some(second),
        ..
    } = second
    else {
        panic!()
    };
    assert_ne!(first, second);
    assert_ne!(
        channels[0].members.iter().find(|m| !m.is_self).unwrap().id,
        channels[1].members.iter().find(|m| !m.is_self).unwrap().id
    );
    let mut events = owner.subscribe_events();
    assert!(matches!(
        submit(&service, "lock-command-check", None, "/lock").await,
        Response::Instance { .. }
    ));
    assert!(service.snapshot().await.unwrap().conversations.is_empty());
    peer.send_channel("one", b"received while views locked")
        .await
        .unwrap();
    tokio::time::timeout(Duration::from_secs(20), async {
        loop {
            match events.recv().await {
                Some(gcoms::sdk::ClientEvent::ChannelMessage { body, .. })
                    if body == b"received while views locked" =>
                {
                    break
                }
                Some(_) => {}
                None => panic!("receiver closed while views locked"),
            }
        }
    })
    .await
    .expect("locked instance receives messages");
    unlock(&service, false).await;
    let channel = channels.iter().find(|c| c.name == "#one").unwrap();
    tokio::time::timeout(Duration::from_secs(5), async {
        loop {
            let response = request(
                &service,
                Request::History {
                    conversation: channel.id.clone(),
                    before: None,
                    limit: 200,
                },
            )
            .await;
            if let Response::History { page } = response {
                if page
                    .messages
                    .iter()
                    .any(|m| m.body == "received while views locked" && !m.mine)
                {
                    break;
                }
            }
            tokio::time::sleep(Duration::from_millis(50)).await;
        }
    })
    .await
    .expect("received message archived while locked");
    service.disconnect().await.unwrap();
    drop(service);
    ar.shutdown().await.unwrap();
    br.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread")]
async fn host_disconnect_cancels_attached_pollers_and_releases_instance_locks() {
    use chat_service::{
        host::{InstanceConfig, InstanceHost},
        ChatEndpoint,
    };
    let dir = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(dir.path(), true).unwrap();
    let mut config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    config.relay_urls.clear();
    config.network_recovery = false;
    config.local_fixture = true;
    config.listen = "127.0.0.1:0".parse().unwrap();
    let host = InstanceHost::new(config).unwrap();
    let Response::Instance { instance } = host
        .dispatch(RequestEnvelope {
            version: VERSION,
            instance_id: None,
            request: Request::Identify,
        })
        .await
        .response
    else {
        panic!("identify")
    };
    let call = |request| RequestEnvelope {
        version: VERSION,
        instance_id: Some(instance.id.clone()),
        request,
    };
    let first = host
        .dispatch(call(Request::Unlock {
            passphrase: PASS.into(),
            create: true,
        }))
        .await;
    let Response::Snapshot { snapshot: first } = first.response else {
        panic!("unlock: {first:?}")
    };
    let poll = tokio::spawn({
        let host = host.clone();
        let request = call(Request::Events {
            after: first.revision.clone(),
            wait_ms: 20_000,
        });
        async move { host.dispatch(request).await }
    });
    tokio::time::sleep(Duration::from_millis(50)).await;
    let disconnected = tokio::time::timeout(
        Duration::from_secs(5),
        host.dispatch(call(Request::Submit {
            operation_id: "disconnect-command-check".into(),
            conversation: None,
            text: "/disconnect".into(),
        })),
    )
    .await
    .expect("disconnect must cancel pollers");
    assert!(matches!(disconnected.response, Response::Snapshot { .. }));
    tokio::time::timeout(Duration::from_secs(1), poll)
        .await
        .unwrap()
        .unwrap();
    let reopened = host
        .dispatch(call(Request::Unlock {
            passphrase: PASS.into(),
            create: false,
        }))
        .await;
    let Response::Snapshot { snapshot: reopened } = reopened.response else {
        panic!("reopen: {reopened:?}")
    };
    assert_eq!(
        first.instance.safety_number,
        reopened.instance.safety_number
    );
    assert_eq!(first.instance.id, reopened.instance.id);
    assert!(
        !reopened.instance.locked,
        "one passphrase reopens both stores when it matches"
    );
    let archived = host
        .dispatch(call(Request::Unlock {
            passphrase: PASS.into(),
            create: false,
        }))
        .await;
    assert!(
        matches!(archived.response, Response::Snapshot { snapshot } if !snapshot.instance.locked)
    );
    host.flush().await.unwrap();
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn typed_host_resumes_the_same_journal_across_lock_and_protocol_restart() {
    use chat_service::{
        host::{InstanceConfig, InstanceHost},
        ChatEndpoint,
    };
    use gchat_api::rpc::{ChatClient as TypedChat, SubmitOutcome};
    let dir = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(dir.path(), true).unwrap();
    let mut config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    config.relay_urls.clear();
    config.network_recovery = false;
    config.local_fixture = true;
    config.listen = "127.0.0.1:0".parse().unwrap();
    let host = InstanceHost::new(config).unwrap();
    let router = chat_service::rpc::router(host.clone()).unwrap();
    let make_client = || {
        TypedChat::new(gcoms::rpc::Client::new(
            gcoms::rpc::EmbeddedTransport {
                router: router.clone(),
                caller: gcoms::rpc::Caller {
                    principal: "local-owner".into(),
                },
                destination: "selected-host".into(),
            },
            host.instance_id(),
        ))
    };
    let client = make_client();
    assert!(client.identify().await.unwrap().protocol_locked);
    assert!(
        !client
            .unlock(PASS.into(), true)
            .await
            .unwrap()
            .instance
            .locked
    );
    let prepared = client
        .prepare_submit(None, "/create #typed tester".into())
        .unwrap();
    client.inner.start(&prepared).await.unwrap();
    let saved = serde_json::to_string(&prepared.handle).unwrap();
    drop(client);
    let client = make_client();
    let handle = serde_json::from_str(&saved).unwrap();
    let outcome: SubmitOutcome = client
        .inner
        .resume::<SubmitOutcome, gchat_api::ChatError>(&handle)
        .await
        .unwrap();
    let legacy = host
        .dispatch(RequestEnvelope {
            version: VERSION,
            instance_id: Some(host.instance_id().into()),
            request: Request::Submit {
                operation_id: prepared.handle.operation.id.as_str().into(),
                conversation: None,
                text: "/create #typed tester".into(),
            },
        })
        .await
        .response;
    assert_eq!(
        serde_json::to_value(Response::from(outcome)).unwrap(),
        serde_json::to_value(legacy).unwrap()
    );
    assert!(client.lock().await.unwrap().locked);
    assert_eq!(
        client.inner.status(&handle).await.unwrap_err().code,
        gcoms::rpc::ErrorCode::Unauthorized
    );
    client.unlock(PASS.into(), false).await.unwrap();
    assert!(matches!(
        client.inner.status(&handle).await.unwrap(),
        gcoms::rpc::ReplyBody::Done { .. }
    ));
    // Every restart must release the protocol lock, including event workers.
    for _ in 0..3 {
        assert!(client.disconnect().await.unwrap().instance.protocol_locked);
        assert_eq!(
            client.inner.status(&handle).await.unwrap_err().code,
            gcoms::rpc::ErrorCode::Unauthorized
        );
        client.unlock(PASS.into(), false).await.unwrap();
        assert!(matches!(
            client.inner.status(&handle).await.unwrap(),
            gcoms::rpc::ReplyBody::Done { .. }
        ));
    }
    assert_eq!(client.snapshot().await.unwrap().conversations.len(), 1);
    host.flush().await.unwrap();
}

#[test]
fn migration_preserves_identity_original_bytes_and_legacy_archive() {
    use gchat_core::store::{migrate_combined, ArchiveStore, ProtocolStore, Store};
    let dir = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(dir.path(), true).unwrap();
    let source = dir.path().join("original.gcstore");
    let destination = dir.path().join("migrated");
    let (store, mut data) = Store::create(&source, PASS).unwrap();
    data.archive
        .legacy
        .conversations
        .direct("old-contact")
        .push(gchat_core::conversation::Message {
            id: [12; 16],
            ts_unix: 1,
            sender: "old-contact".into(),
            mine: false,
            text: "unmapped legacy text".into(),
        });
    store.save(&data).unwrap();
    let original = std::fs::read(&source).unwrap();
    assert!(
        migrate_combined(&source, &destination, PASS).is_err(),
        "live source must remain locked"
    );
    drop(store);
    assert!(migrate_combined(&source, &destination, "wrong").is_err());
    assert!(!destination.exists());
    migrate_combined(&source, &destination, PASS).unwrap();
    assert_eq!(std::fs::read(&source).unwrap(), original);
    assert_eq!(
        std::fs::read(destination.join("legacy.gcstore")).unwrap(),
        original
    );
    let (_, protocol) = ProtocolStore::open(&destination.join("profile.gcprotocol"), PASS).unwrap();
    let (_, archive) = ArchiveStore::open(&destination.join("chat.gcarchive"), PASS).unwrap();
    assert_eq!(protocol.identity_seed, data.identity_seed);
    assert_eq!(
        archive.legacy.conversations.list[0].messages()[0].text,
        "unmapped legacy text"
    );
    assert!(archive.scoped_pms.is_empty());
    assert!(migrate_combined(&source, &destination, PASS).is_err());
}

#[tokio::test(flavor = "multi_thread")]
async fn conversation_history_search_and_recall_keep_context_beyond_two_hundred_messages() {
    let dir = tempfile::tempdir().unwrap();
    let runtime = open_runtime(dir.path(), true).await;
    let service = make_service(dir.path(), runtime.clone());
    unlock(&service, true).await;
    let Response::Applied {
        conversation: Some(channel),
        ..
    } = submit(
        &service,
        "create-history-fixture",
        None,
        "/create #history tester",
    )
    .await
    else {
        panic!("create history channel");
    };
    for index in 0..205 {
        let response = submit(
            &service,
            &format!("history-message-{index:04}"),
            Some(&channel),
            &format!("history fixture {index:03}"),
        )
        .await;
        assert!(matches!(response, Response::Applied { .. }), "{response:?}");
    }
    let Response::History { page } = request(
        &service,
        Request::History {
            conversation: channel.clone(),
            before: None,
            limit: 200,
        },
    )
    .await
    else {
        panic!("history");
    };
    assert_eq!(page.messages.len(), 200);
    assert_eq!(page.messages[0].body, "history fixture 005");
    assert!(page
        .messages
        .iter()
        .all(|m| m.delivery == Some(gchat_api::Delivery::LocalAccepted)));
    let Response::History { page: earlier } = request(
        &service,
        Request::History {
            conversation: channel.clone(),
            before: page.before,
            limit: 200,
        },
    )
    .await
    else {
        panic!("earlier history");
    };
    assert_eq!(earlier.messages.len(), 5);
    assert_eq!(earlier.messages[0].body, "history fixture 000");
    assert!(earlier.before.is_none());
    let Response::History { page: found } = request(
        &service,
        Request::Search {
            conversation: channel.clone(),
            text: "FIXTURE 00".into(),
            before: None,
            limit: 4,
        },
    )
    .await
    else {
        panic!("search");
    };
    assert_eq!(
        found
            .messages
            .iter()
            .map(|m| m.body.as_str())
            .collect::<Vec<_>>(),
        vec![
            "history fixture 006",
            "history fixture 007",
            "history fixture 008",
            "history fixture 009"
        ]
    );
    let Response::History { page: earlier } = request(
        &service,
        Request::Search {
            conversation: channel.clone(),
            text: "FIXTURE 00".into(),
            before: found.before,
            limit: 200,
        },
    )
    .await
    else {
        panic!("search earlier");
    };
    assert_eq!(earlier.messages.len(), 6);
    let snapshot = service.snapshot().await.unwrap();
    assert!(snapshot
        .input_history
        .iter()
        .filter(|h| h.text.starts_with("history fixture"))
        .all(|h| h.conversation.as_ref() == Some(&channel)));
    let Response::Catalogue { commands } =
        request(&service, Request::Catalogue { conversation: None }).await
    else {
        panic!("catalogue");
    };
    assert!(
        !commands
            .iter()
            .find(|c| c.name == "/query")
            .unwrap()
            .available
    );
    assert!(
        !commands
            .iter()
            .find(|c| c.name == "/part")
            .unwrap()
            .available
    );
    request(&service, Request::Lock).await;
    assert!(
        matches!(request(&service, Request::Search { conversation: channel, text: "fixture".into(), before: None, limit: 200 }).await, Response::Error { code, .. } if code == "locked")
    );
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread")]
async fn provider_revocation_removes_cached_conversations_and_stops_automatic_retry() {
    use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
    let dir = tempfile::tempdir().unwrap();
    let runtime = open_runtime(dir.path(), true).await;
    let allowed = Arc::new(AtomicBool::new(true));
    let calls = Arc::new(AtomicUsize::new(0));
    let route = axum::Router::new().route("/", axum::routing::post({
        let allowed = allowed.clone(); let calls = calls.clone();
        move || { let allowed = allowed.clone(); let calls = calls.clone(); async move {
            calls.fetch_add(1, Ordering::SeqCst);
            axum::Json(if allowed.load(Ordering::SeqCst) { serde_json::json!({"kind":"projection", "revision":"allowed", "conversations":[{"id":"extension/cmd/room", "provider":"cmd", "channelId":"extension/cmd/room", "kind":"channel", "name":"#provider", "topic":"private provider topic", "active":true, "owner":true, "members":[], "unread":0, "lastMessageId":null, "inputLimitBytes":8000, "commands":[]}]}) } else { serde_json::json!({"kind":"error", "code":"forbidden", "message":"Current provider membership required"}) })
        } }
    }));
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let url = format!("http://{}/", listener.local_addr().unwrap());
    let server = tokio::spawn(async move {
        axum::serve(listener, route).await.unwrap();
    });
    for (name, bytes) in [
        (
            "chat.extensions.json",
            serde_json::to_vec(&serde_json::json!({"url":url,"token_file":"test-token"})).unwrap(),
        ),
        ("test-token", b"disposable-token".to_vec()),
    ] {
        let path = dir.path().join(name);
        std::fs::write(&path, bytes).unwrap();
        gchat_core::private_fs::make_private(&path, false).unwrap();
    }
    let service = make_service(dir.path(), runtime.clone());
    unlock(&service, true).await;
    submit(&service, "refresh-provider-start", None, "/refresh").await;
    assert!(service
        .snapshot()
        .await
        .unwrap()
        .conversations
        .iter()
        .any(|c| c.id == "extension/cmd/room"));
    allowed.store(false, Ordering::SeqCst);
    submit(&service, "refresh-provider-revoked", None, "/refresh").await;
    let snapshot = service.snapshot().await.unwrap();
    assert!(snapshot.conversations.is_empty());
    assert_eq!(snapshot.provider_errors[0].code, "forbidden");
    assert!(!snapshot.provider_errors[0].retryable);
    let count = calls.load(Ordering::SeqCst);
    tokio::time::sleep(Duration::from_secs(3)).await;
    assert_eq!(
        calls.load(Ordering::SeqCst),
        count,
        "permanent failures need explicit recovery"
    );
    allowed.store(true, Ordering::SeqCst);
    submit(&service, "refresh-provider-recover", None, "/refresh").await;
    assert!(service.snapshot().await.unwrap().provider_errors.is_empty());
    assert_eq!(service.snapshot().await.unwrap().conversations.len(), 1);
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
    server.abort();
    let _ = server.await;
}

#[tokio::test(flavor = "multi_thread")]
async fn network_invitation_is_local_private_and_survives_reopen_without_chat_authority() {
    use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine};
    let dir = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(dir.path(), true).unwrap();
    let profile = dir.path().join("profile.gcprotocol");
    let runtime = ProtocolRuntime::create(
        &profile,
        PASS,
        "127.0.0.1:0".parse().unwrap(),
        None,
        None,
        &[],
    )
    .await
    .unwrap();
    let service = make_service(dir.path(), runtime.clone());
    unlock(&service, true).await;
    let before = service.snapshot().await.unwrap();
    let grant = URL_SAFE_NO_PAD.encode([37u8; 32]);
    let code = format!(
        "GCNI1-{}",
        URL_SAFE_NO_PAD.encode(
            serde_json::to_vec(&serde_json::json!({
                "version": 1, "network_id": "gchat.boo",
                "provider_urls": gchat_core::bootstrap::default_provider_urls(),
                "grant": grant, "expires_at": gcoms_network_client::now_unix() + 3600
            }))
            .unwrap()
        )
    );
    // Even with a provider destination and mixed-case command this stays local.
    let response = submit(
        &service,
        "network-invitation-local-01",
        Some("extension/cmd/missing"),
        &format!("/NETWORK join {code}"),
    )
    .await;
    assert!(matches!(response, Response::Applied { .. }), "{response:?}");
    let after = service.snapshot().await.unwrap();
    assert_eq!(before.conversations, after.conversations);
    assert_eq!(before.instance.safety_number, after.instance.safety_number);
    let projection = serde_json::to_string(&after).unwrap();
    assert!(!projection.contains(&code));
    assert!(!projection.contains(&grant));
    assert!(projection.contains("/network join "));
    assert!(!runtime.network_dns_status().await.unwrap().opted_in);
    assert!(matches!(
        submit(
            &service,
            "network-dns-consent-01",
            Some("extension/cmd/missing"),
            "/network dns on"
        )
        .await,
        Response::Applied { .. }
    ));
    let names = runtime.network_dns_status().await.unwrap();
    assert!(names.opted_in);
    assert!(
        names.name.is_none(),
        "consent cannot invent a reachable listener"
    );
    service.disconnect().await.unwrap();
    drop(service);
    runtime.shutdown().await.unwrap();
    let network = gcoms_network_client::NetworkClient::for_profile(
        &profile,
        gchat_core::network::installed().unwrap(),
    )
    .unwrap();
    assert!(network.has_invitation().unwrap());
    assert!(network.name_status().unwrap().opted_in);
    drop(network);
    let reopened = ProtocolRuntime::unlock(
        &profile,
        PASS,
        "127.0.0.1:0".parse().unwrap(),
        None,
        None,
        &[],
    )
    .await
    .unwrap();
    let service = make_service(dir.path(), reopened.clone());
    unlock(&service, false).await;
    let after = service.snapshot().await.unwrap();
    assert_eq!(before.instance.safety_number, after.instance.safety_number);
    assert_eq!(before.conversations, after.conversations);
    assert!(!serde_json::to_string(&after).unwrap().contains(&grant));
    assert!(matches!(
        submit(&service, "network-dns-revoke-01", None, "/network dns off").await,
        Response::Applied { .. }
    ));
    assert!(!reopened.network_dns_status().await.unwrap().opted_in);
    service.disconnect().await.unwrap();
    reopened.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread")]
async fn file_controls_binary_io_lock_and_restart_keep_plaintext_out_of_archive() {
    use chat_service::ChatEndpoint;
    use gchat_api::files::{encode_io, FileIo, PIECE_BYTES};
    use gchat_api::{FileRequest, FileState};
    let dir = tempfile::tempdir().unwrap();
    let runtime = open_runtime(dir.path(), true).await;
    let service = make_service(dir.path(), runtime.clone());
    unlock(&service, true).await;
    let Response::Applied {
        conversation: Some(channel),
        ..
    } = submit(
        &service,
        "create-file-channel-fixture",
        None,
        "/create #files tester",
    )
    .await
    else {
        panic!("create channel");
    };
    let handle = "01010101010101010101010101010101";
    let response = request(
        &service,
        Request::Files {
            request: FileRequest::Prepare {
                id: handle.into(),
                conversation: channel.clone(),
                name: "fixture.bin".into(),
                size_bytes: (PIECE_BYTES + 7).to_string(),
            },
        },
    )
    .await;
    assert!(matches!(response, Response::Files { .. }), "{response:?}");
    let instance = service.snapshot().await.unwrap().instance.id;
    let frame = |piece, upload, bytes: &[u8]| {
        encode_io(
            &FileIo {
                instance: instance.clone(),
                id: handle.into(),
                piece,
                upload,
            },
            bytes,
        )
        .unwrap()
    };
    let piece = vec![0xa7; PIECE_BYTES];
    service
        .clone()
        .file_io(frame(0, true, &piece))
        .await
        .unwrap();
    service
        .clone()
        .file_io(frame(0, true, &piece))
        .await
        .unwrap();
    assert!(service
        .clone()
        .file_io(frame(0, true, &vec![0x5a; PIECE_BYTES]))
        .await
        .is_err());
    service
        .clone()
        .file_io(frame(1, true, b"retained"))
        .await
        .unwrap_err(); // Exact final-piece bounds.
    service
        .clone()
        .file_io(frame(1, true, b"content"))
        .await
        .unwrap();
    let committed = request(
        &service,
        Request::Files {
            request: FileRequest::Commit { id: handle.into() },
        },
    )
    .await;
    assert!(
        matches!(committed,Response::Files { snapshot } if matches!(snapshot.files[0].state,FileState::Complete))
    );
    // Selecting already verified content again returns the original share. A lost
    // commit response is recoverable using the second import ID after reopening.
    let duplicate = "02020202020202020202020202020202";
    let prepared = request(
        &service,
        Request::Files {
            request: FileRequest::Prepare {
                id: duplicate.into(),
                conversation: channel.clone(),
                name: "again.bin".into(),
                size_bytes: (PIECE_BYTES + 7).to_string(),
            },
        },
    )
    .await;
    assert!(matches!(prepared, Response::Files { .. }));
    for (index, data) in [(0, piece.as_slice()), (1, b"content".as_slice())] {
        service
            .clone()
            .file_io(
                encode_io(
                    &FileIo {
                        instance: instance.clone(),
                        id: duplicate.into(),
                        piece: index,
                        upload: true,
                    },
                    data,
                )
                .unwrap(),
            )
            .await
            .unwrap();
    }
    let Response::Files { snapshot: reused } = request(
        &service,
        Request::Files {
            request: FileRequest::Commit {
                id: duplicate.into(),
            },
        },
    )
    .await
    else {
        panic!("reuse failed")
    };
    assert_eq!(reused.files.len(), 1);
    assert_eq!(reused.files[0].id, handle);
    assert!(reused.files[0].publication.is_none());
    assert!(!serde_json::to_string(&reused)
        .unwrap()
        .contains("publication"));
    let Response::Files {
        snapshot: published,
    } = request(
        &service,
        Request::Files {
            request: FileRequest::Publications {
                conversation: Some(channel.clone()),
            },
        },
    )
    .await
    else {
        panic!("publication metadata");
    };
    assert_eq!(published.files.len(), 2);
    assert_eq!(published.files[0].name, "fixture.bin");
    assert_eq!(published.files[1].name, "again.bin");
    assert_eq!(published.files[1].id, duplicate);
    let commitments: Vec<_> = published
        .files
        .iter()
        .map(|f| f.publication.clone().unwrap())
        .collect();
    assert_eq!(commitments[0].sequence, "1");
    assert_eq!(commitments[1].sequence, "2");
    assert_eq!(commitments[0].sha256, commitments[1].sha256);
    assert_eq!(commitments[1].canonical_id, handle);
    assert_eq!(
        commitments[0].publisher_safety_number,
        service.snapshot().await.unwrap().instance.safety_number
    );
    {
        use sha2::Digest;
        let mut digest = sha2::Sha256::new();
        digest.update(&piece);
        digest.update(b"content");
        assert_eq!(commitments[0].sha256, format!("{:x}", digest.finalize()));
    }
    assert_eq!(
        reused.files[0].aliases.as_deref(),
        Some(&[duplicate.to_string()][..])
    );
    let activities = service.snapshot().await.unwrap().activity.unwrap();
    assert_eq!(
        activities
            .iter()
            .filter(|e| e.kind == "file" && e.conversation == channel)
            .count(),
        1
    );
    assert_eq!(
        service.clone().file_io(frame(0, false, &[])).await.unwrap(),
        piece
    );
    request(&service, Request::Lock).await;
    assert!(service.clone().file_io(frame(0, false, &[])).await.is_err());
    assert!(matches!(
        request(
            &service,
            Request::Files {
                request: FileRequest::List { conversation: None }
            }
        )
        .await,
        Response::Error { .. }
    ));
    unlock(&service, false).await;
    let Response::Files {
        snapshot: recovered,
    } = request(
        &service,
        Request::Files {
            request: FileRequest::Commit {
                id: duplicate.into(),
            },
        },
    )
    .await
    else {
        panic!("lost commit recovery")
    };
    assert_eq!(recovered.files.len(), 1);
    assert_eq!(recovered.files[0].id, handle);
    assert_eq!(
        service
            .snapshot()
            .await
            .unwrap()
            .activity
            .unwrap()
            .iter()
            .filter(|e| e.kind == "file" && e.conversation == channel)
            .count(),
        1
    );
    let Response::History { page } = request(
        &service,
        Request::History {
            conversation: channel.clone(),
            before: None,
            limit: 200,
        },
    )
    .await
    else {
        panic!("history")
    };
    assert!(page.messages.iter().all(|m| !m.body.contains("content")));
    service.disconnect().await.unwrap();
    drop(service);
    let service = make_service(dir.path(), runtime.clone());
    unlock(&service, false).await;
    let Response::Files {
        snapshot: retained_publications,
    } = request(
        &service,
        Request::Files {
            request: FileRequest::Publications {
                conversation: Some(channel.clone()),
            },
        },
    )
    .await
    else {
        panic!("retained publication metadata");
    };
    assert_eq!(
        retained_publications
            .files
            .iter()
            .map(|f| f.publication.clone().unwrap())
            .collect::<Vec<_>>(),
        commitments
    );
    assert_eq!(
        service.clone().file_io(frame(1, false, &[])).await.unwrap(),
        b"content"
    );
    let result = request(
        &service,
        Request::Files {
            request: FileRequest::Cancel { id: handle.into() },
        },
    )
    .await;
    assert!(
        matches!(result,Response::Files{snapshot} if matches!(snapshot.files[0].state,FileState::Cancelled))
    );
    assert!(service.clone().file_io(frame(0, false, &[])).await.is_err());
    service.disconnect().await.unwrap();
    drop(service);
    let journal = dir.path().join("chat.pieces").join(handle).join("state");
    let mut sealed = std::fs::read(&journal).unwrap();
    sealed[0] ^= 1;
    std::fs::write(&journal, sealed).unwrap();
    let service = make_service(dir.path(), runtime.clone());
    unlock(&service, false).await;
    assert!(!service.snapshot().await.unwrap().instance.locked);
    assert!(
        matches!(request(&service, Request::Files { request: FileRequest::List { conversation: None } }).await,
        Response::Error { message, .. } if message.contains("File cache unavailable"))
    );
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread")]
async fn files_cross_real_private_channel_after_acceptance_without_transcript_records() {
    use chat_service::ChatEndpoint;
    use gchat_api::files::{encode_io, FileIo};
    use gchat_api::{FileRequest, FileState};
    let a = tempfile::tempdir().unwrap();
    let b = tempfile::tempdir().unwrap();
    let ar = open_runtime(a.path(), true).await;
    let br = open_runtime(b.path(), true).await;
    let owner = ar.sdk_client();
    let peer = br.sdk_client();
    owner
        .create_channel("files-network", "owner", 8, ChannelVisibility::Private)
        .await
        .unwrap();
    let join = peer.prepare_channel_join("peer").await.unwrap();
    let welcome = owner
        .admit_channel(
            "files-network",
            &peer.channel_key_package(join).await.unwrap(),
            "peer",
        )
        .await
        .unwrap();
    peer.join_channel(join, "files-network", ChannelVisibility::Private, &welcome)
        .await
        .unwrap();
    let sender = make_service(a.path(), ar.clone());
    let receiver = make_service(b.path(), br.clone());
    unlock(&sender, true).await;
    unlock(&receiver, true).await;
    let channel = sender.snapshot().await.unwrap().conversations[0].id.clone();
    let receiver_channel = receiver.snapshot().await.unwrap().conversations[0]
        .id
        .clone();
    let handle = "02020202020202020202020202020202";
    let bytes = vec![0x7b; 32 * 1024 + 11];
    let prepared = request(
        &sender,
        Request::Files {
            request: FileRequest::Prepare {
                id: handle.into(),
                conversation: channel.clone(),
                name: "network.bin".into(),
                size_bytes: bytes.len().to_string(),
            },
        },
    )
    .await;
    assert!(matches!(prepared, Response::Files { .. }), "{prepared:?}");
    let header = FileIo {
        instance: sender.snapshot().await.unwrap().instance.id,
        id: handle.into(),
        piece: 0,
        upload: true,
    };
    sender
        .clone()
        .file_io(encode_io(&header, &bytes).unwrap())
        .await
        .unwrap();
    assert!(matches!(
        request(
            &sender,
            Request::Files {
                request: FileRequest::Commit { id: handle.into() }
            }
        )
        .await,
        Response::Files { .. }
    ));
    tokio::time::timeout(Duration::from_secs(90), async {
        loop {
            if let Response::Files { snapshot } = request(
                &receiver,
                Request::Files {
                    request: FileRequest::List { conversation: None },
                },
            )
            .await
            {
                if let Some(file) = snapshot.files.iter().find(|f| f.id == handle) {
                    assert!(matches!(file.state, FileState::Offered));
                    assert_eq!(file.verified_bytes, "0");
                    break;
                }
            }
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
    })
    .await
    .expect("private offer arrives");
    assert!(matches!(
        request(
            &receiver,
            Request::Files {
                request: FileRequest::Accept { id: handle.into() }
            }
        )
        .await,
        Response::Files { .. }
    ));
    owner
        .send_channel("files-network", b"chat alongside attachment")
        .await
        .unwrap();
    tokio::time::timeout(Duration::from_secs(120), async {
        loop {
            if let Response::Files { snapshot } = request(
                &receiver,
                Request::Files {
                    request: FileRequest::List { conversation: None },
                },
            )
            .await
            {
                if snapshot
                    .files
                    .iter()
                    .any(|f| f.id == handle && matches!(f.state, FileState::Complete))
                {
                    break;
                }
            }
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
    })
    .await
    .expect("verified download completes");
    let header = FileIo {
        instance: receiver.snapshot().await.unwrap().instance.id,
        id: handle.into(),
        piece: 0,
        upload: false,
    };
    assert_eq!(
        receiver
            .clone()
            .file_io(encode_io(&header, &[]).unwrap())
            .await
            .unwrap(),
        bytes
    );
    let Response::History { page } = request(
        &receiver,
        Request::History {
            conversation: receiver_channel,
            before: None,
            limit: 200,
        },
    )
    .await
    else {
        panic!("history")
    };
    assert!(page
        .messages
        .iter()
        .any(|m| m.body == "chat alongside attachment"));
    assert!(page
        .messages
        .iter()
        .all(|m| !m.body.contains("GCAPP1") && !m.body.contains("network.bin")));
    sender.disconnect().await.unwrap();
    receiver.disconnect().await.unwrap();
    ar.shutdown().await.unwrap();
    br.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread")]
async fn native_file_paths_stay_local_and_export_never_clobbers() {
    let dir = tempfile::tempdir().unwrap();
    let runtime = open_runtime(dir.path(), true).await;
    let service = make_service(dir.path(), runtime.clone());
    unlock(&service, true).await;
    let Response::Applied {
        conversation: Some(channel),
        ..
    } = submit(
        &service,
        "create-native-file-fixture",
        None,
        "/create #files tester",
    )
    .await
    else {
        panic!("channel")
    };
    let socket = dir.path().join("chat.sock");
    let (stop, rx) = tokio::sync::watch::channel(false);
    let server = tokio::spawn({
        let service = service.clone();
        let socket = socket.clone();
        async move { chat_service::serve(service, &socket, rx).await }
    });
    let client = tokio::time::timeout(Duration::from_secs(10), async {
        loop {
            if let Ok(client) = ChatClient::connect(&socket, None).await {
                break client;
            }
            tokio::time::sleep(Duration::from_millis(20)).await;
        }
    })
    .await
    .unwrap();
    let source = dir.path().join("source.bin");
    let destination = dir.path().join("saved.bin");
    let bytes = vec![0xd3; 256 * 1024 + 3];
    std::fs::write(&source, &bytes).unwrap();
    let handle = "03030303030303030303030303030303";
    client.import_file(handle, &channel, &source).await.unwrap();
    client.import_file(handle, &channel, &source).await.unwrap();
    client.save_file(handle, &destination).await.unwrap();
    assert_eq!(std::fs::read(&destination).unwrap(), bytes);
    std::fs::write(&destination, b"keep existing").unwrap();
    assert!(client.save_file(handle, &destination).await.is_err());
    assert_eq!(std::fs::read(&destination).unwrap(), b"keep existing");
    client.request(Request::Lock).await.unwrap();
    assert!(client
        .save_file(handle, &dir.path().join("locked.bin"))
        .await
        .is_err());
    assert!(!dir.path().join("locked.bin").exists());
    stop.send(true).unwrap();
    server.await.unwrap().unwrap();
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread")]
async fn typed_network_import_is_private_bounded_and_requires_unlock() {
    use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine};
    use gchat_api::{rpc::ChatClient as TypedChat, NetworkState};
    use gcoms::rpc::{Caller, Client, EmbeddedTransport};
    let dir = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(dir.path(), true).unwrap();
    let profile = dir.path().join("profile.gcprotocol");
    // This fixture measures invitation admission, not provider recovery. The
    // application facade starts maintenance automatically, so disable HTTPS
    // recovery explicitly to keep unrelated authenticated refreshes out of the
    // byte-for-byte rejected-import assertion below.
    let runtime = ProtocolRuntime(
        gcoms::Application::builder("gchat")
            .network_config(include_bytes!("../assets/gchat-network.json").to_vec())
            .profile(&profile)
            .unlock_secret(PASS)
            .listen("127.0.0.1:0".parse().unwrap())
            .create(true)
            .durable_channel_inbox(true)
            .receive_messages(false)
            .network_recovery(false)
            .open()
            .await
            .unwrap(),
    );
    let service = make_service(dir.path(), runtime.clone());
    let id = service.snapshot().await.unwrap().instance.id;
    let client = TypedChat::new(Client::new(
        EmbeddedTransport {
            router: chat_service::rpc::router(service.clone()).unwrap(),
            caller: Caller {
                principal: "local-owner".into(),
            },
            destination: "network-test".into(),
        },
        id,
    ));
    assert_eq!(
        client.network_status().await.unwrap().state,
        NetworkState::Locked
    );
    assert!(client
        .import_network_invitation("GCNI1-invalid".into())
        .await
        .is_err());
    unlock(&service, true).await;
    assert_eq!(
        client.network_status().await.unwrap().state,
        NetworkState::InvitationRequired
    );
    let before = service.snapshot().await.unwrap();
    let grant = URL_SAFE_NO_PAD.encode([81u8; 32]);
    let invitation = |network: &str, expires: u64| {
        format!("GCNI1-{}", URL_SAFE_NO_PAD.encode(serde_json::to_vec(&serde_json::json!({
        "version": 1, "network_id": network, "provider_urls": gchat_core::bootstrap::default_provider_urls(),
        "grant": grant, "expires_at": expires,
    })).unwrap()))
    };
    let code = invitation("gchat.boo", gcoms_network_client::now_unix() + 3600);
    assert_eq!(
        client
            .import_network_invitation(code.clone())
            .await
            .unwrap()
            .state,
        NetworkState::Connecting
    );
    let state_file = profile.with_extension("network").join("network.json");
    let saved = std::fs::read(&state_file).unwrap();
    for invalid in [
        invitation("another.example", gcoms_network_client::now_unix() + 3600),
        invitation("gchat.boo", 1),
        "x".repeat(gchat_api::MAX_NETWORK_INVITATION_BYTES + 1),
    ] {
        assert!(client.import_network_invitation(invalid).await.is_err());
        assert_eq!(std::fs::read(&state_file).unwrap(), saved);
    }
    let after = service.snapshot().await.unwrap();
    assert_eq!(before.command_history, after.command_history);
    assert_eq!(
        serde_json::to_value(&before.input_history).unwrap(),
        serde_json::to_value(&after.input_history).unwrap()
    );
    assert_eq!(before.instance.safety_number, after.instance.safety_number);
    assert!(!serde_json::to_string(&after).unwrap().contains(&grant));
    assert!(client.inner.handles().list().unwrap().is_empty());
    gchat_core::private_fs::validate_private_file(&state_file, "network state").unwrap();
    client.lock().await.unwrap();
    assert!(client.import_network_invitation(code).await.is_err());
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread", worker_threads = 4)]
async fn chat_host_uses_shared_gcoms_and_reopens_the_same_archive() {
    use chat_service::{
        host::{InstanceConfig, InstanceHost},
        ChatEndpoint,
    };
    let dir = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(dir.path(), true).unwrap();
    let endpoint = dir.path().join("gcoms.sock");
    let (stop, stopped) = tokio::sync::oneshot::channel();
    let socket = endpoint.clone();
    let daemon = tokio::spawn(async move {
        gcoms::daemon::serve(&socket, async {
            let _ = stopped.await;
        })
        .await
    });
    for _ in 0..100 {
        if gcoms::control::exchange(&endpoint, gcoms::control::Request::Ping)
            .await
            .is_ok()
        {
            break;
        }
        tokio::time::sleep(Duration::from_millis(10)).await;
    }
    let mut config = InstanceConfig::from_home(Some(dir.path())).unwrap();
    config.protocol_backend = gcoms::Backend::Attach { endpoint };
    config.local_fixture = true;
    config.listen = "127.0.0.1:0".parse().unwrap();
    config.network_recovery = false;
    config.relay_urls.clear();
    let host = InstanceHost::new(config).unwrap();
    let Response::Instance { instance } = host
        .dispatch(RequestEnvelope {
            version: VERSION,
            instance_id: None,
            request: Request::Identify,
        })
        .await
        .response
    else {
        panic!("identify")
    };
    let call = |request| RequestEnvelope {
        version: VERSION,
        instance_id: Some(instance.id.clone()),
        request,
    };
    let response = host
        .dispatch(call(Request::Unlock {
            passphrase: PASS.into(),
            create: true,
        }))
        .await
        .response;
    let Response::Snapshot { snapshot: first } = response else {
        panic!("unlock: {response:?}")
    };
    let created = host
        .dispatch(call(Request::Submit {
            operation_id: "shared-create-room".into(),
            conversation: None,
            text: "/create #shared alice".into(),
        }))
        .await
        .response;
    assert!(!matches!(created, Response::Error { .. }), "{created:?}");
    let Response::Snapshot { snapshot: before } =
        host.dispatch(call(Request::Snapshot)).await.response
    else {
        panic!("snapshot")
    };
    let stopped = host
        .dispatch(call(Request::Submit {
            operation_id: "shared-disconnect".into(),
            conversation: None,
            text: "/disconnect".into(),
        }))
        .await
        .response;
    assert!(matches!(stopped, Response::Snapshot { .. }), "{stopped:?}");
    let response = host
        .dispatch(call(Request::Unlock {
            passphrase: PASS.into(),
            create: false,
        }))
        .await
        .response;
    let Response::Snapshot { snapshot: reopened } = response else {
        panic!("reopen: {response:?}")
    };
    assert_eq!(
        first.instance.safety_number,
        reopened.instance.safety_number
    );
    assert_eq!(before.conversations, reopened.conversations);
    host.flush().await.unwrap();
    stop.send(()).unwrap();
    daemon.await.unwrap().unwrap();
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn channel_visibility_and_operation_details_are_explicit_and_lock_private() {
    let dir = tempfile::tempdir().unwrap();
    let runtime = open_runtime(dir.path(), true).await;
    let service = make_service(dir.path(), runtime.clone());
    unlock(&service, true).await;
    for (id, command) in [
        ("visibility-private-01", "/create #private owner"),
        ("visibility-public-001", "/create --public #public owner"),
    ] {
        assert!(matches!(
            submit(&service, id, None, command).await,
            Response::Applied { .. }
        ));
    }
    let snapshot = service.snapshot().await.unwrap();
    let public = snapshot
        .conversations
        .iter()
        .find(|c| c.name == "#public")
        .unwrap();
    assert_eq!(public.visibility.as_deref(), Some("public"));
    assert!(public.directory.is_none(), "creation is not publication");
    assert_eq!(
        snapshot
            .conversations
            .iter()
            .find(|c| c.name == "#private")
            .unwrap()
            .visibility
            .as_deref(),
        Some("private")
    );
    assert_eq!(snapshot.presence_enabled, Some(false));
    assert!(snapshot
        .operations
        .as_ref()
        .unwrap()
        .iter()
        .all(|r| r.action == "/create"));
    assert!(matches!(
        request(&service, Request::Lock).await,
        Response::Instance { .. }
    ));
    let locked = service.snapshot().await.unwrap();
    assert!(locked.operations.unwrap().is_empty());
    assert!(locked.activity.unwrap().is_empty());
    unlock(&service, false).await;
    assert_eq!(
        service.snapshot().await.unwrap().operations.unwrap().len(),
        2
    );
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
}

#[tokio::test]
async fn activity_sharing_preference_survives_profile_reopen() {
    let dir = tempfile::tempdir().unwrap();
    for (index, (previous, command, expected)) in [
        (false, "/presence on", true),
        (true, "/presence off", false),
        (false, "/presence off", false),
    ]
    .into_iter()
    .enumerate()
    {
        let runtime = open_runtime(dir.path(), index == 0).await;
        let service = make_service(dir.path(), runtime.clone());
        unlock(&service, index == 0).await;
        assert_eq!(
            service.snapshot().await.unwrap().presence_enabled,
            Some(previous)
        );
        let response = submit(
            &service,
            &format!("activity-sharing-{index:04}"),
            None,
            command,
        )
        .await;
        assert!(matches!(response, Response::Applied { .. }), "{response:?}");
        assert_eq!(
            service.snapshot().await.unwrap().presence_enabled,
            Some(expected)
        );
        service.disconnect().await.unwrap();
        runtime.shutdown().await.unwrap();
    }
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn reconnect_command_exchanges_existing_member_routes_without_rejoining() {
    let a = tempfile::tempdir().unwrap();
    let b = tempfile::tempdir().unwrap();
    let ar = open_runtime(a.path(), true).await;
    let br = open_runtime(b.path(), true).await;
    let service = make_service(a.path(), ar.clone());
    unlock(&service, true).await;
    let Response::Output {
        output: gchat_api::CommandOutput::Text { title, text },
        ..
    } = submit(&service, "connection-details-01", None, "/status --details").await
    else {
        panic!("connection details should be available without a channel");
    };
    assert_eq!(title, "Connection details");
    assert!(text.contains("Ready entries:"));
    assert!(text.contains("Interactive subscriptions:"));
    assert!(text.contains("Bulk subscriptions:"));
    assert!(text.contains("Owner checkpoint paused: false"));
    assert!(text.contains("Last recovery failure:"));
    assert!(!text.contains("127.0.0.1"));
    let Response::Applied {
        conversation: Some(channel),
        ..
    } = submit(
        &service,
        "reconnect-create",
        None,
        "/create #reconnect owner",
    )
    .await
    else {
        panic!("create");
    };
    let owner = ar.sdk_client();
    let peer = br.sdk_client();
    let join = peer.prepare_channel_join("peer").await.unwrap();
    let package = peer.channel_key_package(join).await.unwrap();
    let welcome = owner
        .admit_channel("reconnect", &package, "peer")
        .await
        .unwrap();
    peer.join_channel(join, "reconnect", ChannelVisibility::Private, &welcome)
        .await
        .unwrap();
    let receiver = make_service(b.path(), br.clone());
    unlock(&receiver, true).await;
    let receiver_channel = receiver.snapshot().await.unwrap().conversations[0]
        .id
        .clone();
    let Response::Output {
        output: gchat_api::CommandOutput::Text { text: code, .. },
        ..
    } = submit(
        &receiver,
        "reconnect-export",
        Some(&receiver_channel),
        "/reconnect",
    )
    .await
    else {
        panic!("member exports reconnect code");
    };
    assert!(code.starts_with("gchat-reconnect1:"));
    let reply = submit(
        &service,
        "reconnect-import",
        Some(&channel),
        &format!("/reconnect {code}"),
    )
    .await;
    assert!(matches!(reply, Response::Applied { .. }), "{reply:?}");
    let state = service.snapshot().await.unwrap();
    assert_eq!(state.conversations[0].id, channel);
    assert_eq!(state.conversations[0].members.len(), 2);
    assert!(!state
        .command_history
        .iter()
        .any(|text| text.contains(&code)));
    let mut incoming = peer.subscribe_events();
    let reply = submit(
        &service,
        "reconnect-send-001",
        Some(&channel),
        "after reconnect",
    )
    .await;
    assert!(matches!(reply, Response::Applied { .. }), "{reply:?}");
    tokio::time::timeout(Duration::from_secs(15), async {
        loop {
            if matches!(incoming.recv().await, Some(gcoms::sdk::ClientEvent::ChannelMessage { body, .. }) if body == b"after reconnect") { break; }
        }
    }).await.expect("message reaches existing peer");
    service.disconnect().await.unwrap();
    receiver.disconnect().await.unwrap();
    ar.shutdown().await.unwrap();
    br.shutdown().await.unwrap();
}
