//! The first-channel journey on the production path: two hosted runtimes
//! (profile.gcprotocol + chat.gcarchive each), private channel, key-package
//! join, messages both ways, scoped PM, restart, lock collision.

use gchat_core::client::{ClientHandle, NodeEvent};
use gchat_core::runtime::ProtocolRuntime;
use gcoms_sdk::ChannelVisibility;
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
