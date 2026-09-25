//! The first-channel journey on the production path: two hosted runtimes
//! (profile.gcprotocol + chat.gcarchive each), private channel, key-package
//! join, messages both ways, scoped PM, restart, lock collision.

use gchat_core::client::{ClientHandle, NodeEvent};
use gchat_core::runtime::ProtocolRuntime;
use gcoms::sdk::ChannelVisibility;
use std::net::SocketAddr;
use std::path::Path;
use std::time::Duration;

fn addr() -> SocketAddr {
    "127.0.0.1:0".parse().unwrap()
}

async fn open(dir: &Path, name: &str, pass: &str, create: bool) -> ClientHandle {
    let profile = dir.join(format!("{name}.gcprotocol"));
    let archive = dir.join(format!("{name}.gcarchive"));
    let runtime = if create {
        ProtocolRuntime::create_fixture(&profile, pass, addr(), None, None, &[]).await
    } else {
        ProtocolRuntime::unlock_fixture(&profile, pass, addr(), None, None, &[]).await
    }
    .unwrap();
    ClientHandle::open_hosted(&archive, pass, runtime, create)
        .await
        .unwrap()
}

async fn wait_for<F: Fn() -> bool>(what: &str, ready: F) {
    let deadline = tokio::time::Instant::now() + Duration::from_secs(20);
    while !ready() {
        assert!(tokio::time::Instant::now() < deadline, "{what} timeout");
        tokio::time::sleep(Duration::from_millis(50)).await;
    }
}

#[tokio::test(flavor = "multi_thread")]
async fn first_channel_journey_on_hosted_runtimes() {
    let dir = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(dir.path(), true).unwrap();
    let owner = open(dir.path(), "owner", "owner-pass-8", true).await;
    let member = open(dir.path(), "member", "member-pass-8", true).await;
    assert_ne!(owner.safety_number(), member.safety_number());
    assert!(!owner.contact_card().is_empty());
    let mut member_events = member.subscribe();
    let mut owner_events = owner.subscribe();

    // Owner creates; member joins with the three-message exchange.
    let channel_id = owner
        .create_channel("ops", "owner", 8, ChannelVisibility::Private)
        .await
        .unwrap();
    let (request, package) = member.prepare_join("member").await.unwrap();
    let welcome = owner.admit("ops", &package, "member").await.unwrap();
    member
        .join_channel(request, "ops", "member", &welcome)
        .await
        .unwrap();
    owner.reconcile_channels().await.unwrap();
    // `members` lists the others: one each.
    assert_eq!(owner.members(channel_id).len(), 1);
    assert_eq!(member.members(channel_id).len(), 1);

    // A message each way, observed both as an event and in the archive.
    owner
        .send_channel(channel_id, "hello member")
        .await
        .unwrap();
    let event = tokio::time::timeout(Duration::from_secs(20), async {
        loop {
            match member_events.recv().await {
                Some(NodeEvent::ChannelMessage { .. }) => break,
                Some(_) => continue,
                None => panic!("member event stream closed"),
            }
        }
    })
    .await;
    assert!(event.is_ok(), "member never saw the channel message");
    wait_for("member archive", || {
        member.channel(channel_id).is_some_and(|c| {
            c.messages
                .iter()
                .any(|m| m.text == "hello member" && !m.mine)
        })
    })
    .await;
    // The archive keeps the actual wire ID and only authenticated ACKs promote delivery.
    let received_id = member
        .channel(channel_id)
        .unwrap()
        .messages
        .iter()
        .find(|m| m.text == "hello member" && !m.mine)
        .unwrap()
        .id;
    wait_for("sender authenticated delivery", || {
        owner.channel(channel_id).is_some_and(|c| {
            c.messages.iter().any(|m| {
                m.mine && m.id == received_id && m.delivery == Some(gchat_api::Delivery::Delivered)
            })
        })
    })
    .await;
    member
        .send_channel(channel_id, "hello owner")
        .await
        .unwrap();
    wait_for("owner archive", || {
        owner.channel(channel_id).is_some_and(|c| {
            c.messages
                .iter()
                .any(|m| m.text == "hello owner" && !m.mine)
        })
    })
    .await;

    // A channel-scoped PM, both directions.
    let remote = owner
        .members(channel_id)
        .into_iter()
        .find(|m| m.display_name == "member")
        .unwrap();
    let pm = owner.open_scoped_pm(channel_id, remote.id).unwrap();
    owner.send_scoped_pm(pm, "psst").await.unwrap();
    let event = tokio::time::timeout(Duration::from_secs(20), async {
        loop {
            match member_events.recv().await {
                Some(NodeEvent::ChannelDirectMessage { .. }) => break,
                Some(_) => continue,
                None => panic!("member event stream closed"),
            }
        }
    })
    .await;
    assert!(event.is_ok(), "member never saw the scoped PM");
    wait_for("member pm archive", || {
        member
            .home_items()
            .iter()
            .any(|item| matches!(item, gchat_core::model::HomeItem::ScopedPm(p) if p.messages.iter().any(|m| m.text == "psst")))
    })
    .await;
    let member_pm = member
        .home_items()
        .into_iter()
        .find_map(|item| match item {
            gchat_core::model::HomeItem::ScopedPm(p) => Some(p.id),
            _ => None,
        })
        .unwrap();
    member
        .send_scoped_pm(member_pm, "back at you")
        .await
        .unwrap();
    let _ = tokio::time::timeout(Duration::from_secs(20), async {
        loop {
            match owner_events.recv().await {
                Some(NodeEvent::ChannelDirectMessage { .. }) => break,
                Some(_) => continue,
                None => break,
            }
        }
    })
    .await;
    wait_for("owner pm archive", || {
        owner
            .scoped_pm(pm)
            .is_some_and(|p| p.messages.iter().any(|m| m.text == "back at you"))
    })
    .await;

    // A second opener collides on the profile lock with a clear message.
    let profile = dir.path().join("owner.gcprotocol");
    let collision =
        ProtocolRuntime::unlock_fixture(&profile, "owner-pass-8", addr(), None, None, &[])
            .await
            .err()
            .expect("profile must be locked while the first runtime lives");
    assert!(collision.contains("already in use"), "{collision}");

    // Restart the owner: identity, roster, history and PM all survive.
    let safety = owner.safety_number().to_string();
    owner.shutdown().await.unwrap();
    tokio::time::sleep(Duration::from_millis(100)).await;
    let reopened = open(dir.path(), "owner", "owner-pass-8", false).await;
    assert_eq!(reopened.safety_number(), safety);
    let restored = reopened.channel(channel_id).unwrap();
    assert!(restored.messages.iter().any(|m| m.text == "hello owner"));
    assert!(restored.messages.iter().any(|m| m.text == "hello member"));
    assert!(reopened
        .members(channel_id)
        .iter()
        .any(|m| m.id == remote.id));
    assert!(reopened
        .scoped_pm(pm)
        .unwrap()
        .messages
        .iter()
        .any(|m| m.text == "back at you"));
    reopened.shutdown().await.unwrap();
    member.shutdown().await.unwrap();
    tokio::time::sleep(Duration::from_millis(100)).await;

    // Wrong passphrases are refused; nothing is recreated.
    assert!(ProtocolRuntime::unlock_fixture(
        &dir.path().join("member.gcprotocol"),
        "wrong-pass-8",
        addr(),
        None,
        None,
        &[]
    )
    .await
    .is_err());
    let runtime = ProtocolRuntime::unlock_fixture(
        &dir.path().join("member.gcprotocol"),
        "member-pass-8",
        addr(),
        None,
        None,
        &[],
    )
    .await
    .unwrap();
    let archive = dir.path().join("member.gcarchive");
    assert!(
        ClientHandle::open_hosted(&archive, "wrong-pass-8", runtime.clone(), false)
            .await
            .is_err()
    );
    assert!(archive.exists());
    runtime.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread")]
async fn failed_archive_write_keeps_channel_and_private_deliveries_for_reopen() {
    let dir = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(dir.path(), true).unwrap();
    let owner = open(dir.path(), "sender", "sender-pass", true).await;
    let receiver = open(dir.path(), "receiver", "receiver-pass", true).await;
    let channel = owner
        .create_channel("archive-fault", "owner", 8, ChannelVisibility::Private)
        .await
        .unwrap();
    let (request, package) = receiver.prepare_join("receiver").await.unwrap();
    let welcome = owner
        .admit("archive-fault", &package, "receiver")
        .await
        .unwrap();
    receiver
        .join_channel(request, "archive-fault", "receiver", &welcome)
        .await
        .unwrap();
    owner.reconcile_channels().await.unwrap();
    receiver.save().await.unwrap();
    let safety = receiver.safety_number().to_owned();
    let archive = dir.path().join("receiver.gcarchive");
    let retained = dir.path().join("receiver.retained");
    std::fs::rename(&archive, &retained).unwrap();
    std::fs::create_dir(&archive).unwrap();
    let mut events = receiver.subscribe();
    owner
        .send_channel(channel, "retained despite archive fault")
        .await
        .unwrap();
    let remote = owner
        .members(channel)
        .into_iter()
        .find(|m| m.display_name == "receiver")
        .unwrap();
    let pm = owner.open_scoped_pm(channel, remote.id).unwrap();
    owner
        .send_scoped_pm(pm, "private archive fault")
        .await
        .unwrap();
    // The native authenticated receipt is allowed once the profile journal is durable.
    // It must never stand in for an archive write or cause plaintext loss on restart.
    wait_for("durable receive journal", || receiver.sdk_client().is_ok()).await;
    let sdk = receiver.sdk_client().unwrap();
    tokio::time::timeout(Duration::from_secs(20), async {
        loop {
            if sdk.channel_inbox().await.unwrap().len() == 2 {
                break;
            }
            tokio::time::sleep(Duration::from_millis(50)).await;
        }
    })
    .await
    .unwrap();
    tokio::time::sleep(Duration::from_millis(400)).await;
    let deliveries = sdk.channel_inbox().await.unwrap();
    wait_for("visible archive storage status", || {
        receiver.archive_waiting_for_storage()
    })
    .await;
    let id = deliveries
        .iter()
        .find_map(|(_, _, event)| match event {
            NodeEvent::ChannelMessage { message_id, .. } => Some(message_id.0),
            _ => None,
        })
        .unwrap();
    let private_id = deliveries
        .iter()
        .find_map(|(_, _, event)| match event {
            NodeEvent::ChannelDirectMessage { message_id, .. } => Some(message_id.0),
            _ => None,
        })
        .unwrap();
    assert!(receiver
        .archive_snapshot()
        .scoped_pms
        .iter()
        .all(|p| p.messages.iter().all(|m| m.id != private_id)));
    assert!(!receiver
        .channel(channel)
        .unwrap()
        .messages
        .iter()
        .any(|m| m.id == id));
    while let Ok(Some(event)) = tokio::time::timeout(Duration::from_millis(20), events.recv()).await
    {
        assert!(
            !matches!(
                event,
                NodeEvent::ChannelMessage { .. } | NodeEvent::ChannelDirectMessage { .. }
            ),
            "failed archive candidate was published"
        );
    }
    assert!(
        receiver.shutdown().await.is_err(),
        "archive failpoint must affect shutdown too"
    );
    drop(sdk);
    std::fs::remove_dir(&archive).unwrap();
    std::fs::rename(&retained, &archive).unwrap();
    let reopened = open(dir.path(), "receiver", "receiver-pass", false).await;
    assert_eq!(reopened.safety_number(), safety);
    wait_for("same retained message after reopen", || {
        reopened
            .channel(channel)
            .unwrap()
            .messages
            .iter()
            .any(|m| m.id == id && m.text == "retained despite archive fault")
    })
    .await;
    assert_eq!(
        reopened
            .channel(channel)
            .unwrap()
            .messages
            .iter()
            .filter(|m| m.id == id)
            .count(),
        1
    );
    wait_for("same retained private message", || {
        reopened.archive_snapshot().scoped_pms.iter().any(|p| {
            p.messages
                .iter()
                .any(|m| m.id == private_id && m.text == "private archive fault")
        })
    })
    .await;
    wait_for("archive storage status clears after recovery", || {
        !reopened.archive_waiting_for_storage()
    })
    .await;
    reopened.shutdown().await.unwrap();
    owner.shutdown().await.unwrap();
}
