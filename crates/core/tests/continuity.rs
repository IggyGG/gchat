use gchat_core::client::ClientHandle;
use gchat_core::model::MemberId;
use gcoms_sdk::ChannelVisibility;
use std::net::SocketAddr;

fn addr() -> SocketAddr {
    "127.0.0.1:0".parse().unwrap()
}

#[tokio::test(flavor = "multi_thread")]
async fn channel_roster_transcript_and_scoped_pm_survive_restart() {
    let dir = tempfile::tempdir().unwrap();
    let owner_path = dir.path().join("owner.gcstore");
    let member_path = dir.path().join("member.gcstore");
    let owner = ClientHandle::create_profile_fixture(&owner_path, "owner", addr(), None, None)
        .await
        .unwrap();
    let member = ClientHandle::create_profile_fixture(&member_path, "member", addr(), None, None)
        .await
        .unwrap();
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
    member.reconcile_channels().await.unwrap();

    owner
        .send_channel(channel_id, "channel history")
        .await
        .unwrap();
    let remote = owner
        .members(channel_id)
        .into_iter()
        .find(|candidate| candidate.display_name == "member")
        .unwrap();
    let pm_id = owner.open_scoped_pm(channel_id, remote.id).unwrap();
    owner.send_scoped_pm(pm_id, "scoped history").await.unwrap();
    owner.shutdown().await.unwrap();
    tokio::time::sleep(std::time::Duration::from_millis(100)).await;

    let reopened = ClientHandle::unlock_fixture(&owner_path, "owner", addr(), None, None)
        .await
        .unwrap();
    let restored = reopened.channel(channel_id).unwrap();
    assert!(restored
        .messages
        .iter()
        .any(|message| message.text == "channel history"));
    assert!(reopened
        .scoped_pm(pm_id)
        .unwrap()
        .messages
        .iter()
        .any(|message| message.text == "scoped history"));
    assert!(reopened
        .members(channel_id)
        .iter()
        .any(|candidate| candidate.id == MemberId(remote.id.0)));
    reopened.shutdown().await.unwrap();
    member.shutdown().await.unwrap();
}

#[tokio::test]
async fn production_loopback_profile_unlocks_without_publishing_a_direct_inbox() {
    let dir = tempfile::tempdir().unwrap();
    gchat_core::private_fs::make_private(dir.path(), true).unwrap();
    let path = dir.path().join("offline.gcstore");
    let client = tokio::time::timeout(
        std::time::Duration::from_secs(10),
        ClientHandle::create_profile(&path, "offline-passphrase", addr(), None, None),
    )
    .await
    .unwrap()
    .unwrap();
    assert!(client.sdk_client().unwrap().node().uses_onion_routing());
    assert!(client
        .sdk_client()
        .unwrap()
        .node()
        .current_info()
        .await
        .unwrap()
        .aliases
        .is_empty());
    client.save().await.unwrap();
    client.shutdown().await.unwrap();
    let reopened = tokio::time::timeout(
        std::time::Duration::from_secs(10),
        ClientHandle::unlock(&path, "offline-passphrase", addr(), None, None),
    )
    .await
    .unwrap()
    .unwrap();
    assert!(reopened.sdk_client().unwrap().node().uses_onion_routing());
    assert!(reopened
        .sdk_client()
        .unwrap()
        .node()
        .current_info()
        .await
        .unwrap()
        .aliases
        .is_empty());
    reopened.shutdown().await.unwrap();
}
