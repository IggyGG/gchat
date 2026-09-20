use super::*;
use std::time::Duration;

async fn fixture() -> (tempfile::TempDir, ProtocolRuntime) {
    let dir = tempfile::tempdir().unwrap();
    crate::private_fs::make_private(dir.path(), true).unwrap();
    let runtime = ProtocolRuntime::create_fixture(
        &dir.path().join("protocol"),
        "test-only-passphrase",
        "127.0.0.1:0".parse().unwrap(),
        None,
        None,
        &[],
    )
    .await
    .unwrap();
    (dir, runtime)
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn event_write_measurement_by_subscriber_count() {
    let (_dir, runtime) = fixture().await;
    for observers in [0, 1, 4] {
        let (background, source) = mpsc::channel(1);
        runtime.spawn_event_persistence_from(source);
        let mut subscribers = Vec::new();
        for _ in 0..observers {
            subscribers.push(runtime.forward_events(None));
        }
        let before = runtime.persistence_diagnostics();
        let event = ClientEvent::EventsLagged { skipped: 1 };
        background.send(event.clone()).await.unwrap();
        for events in &mut subscribers {
            assert_eq!(
                tokio::time::timeout(Duration::from_secs(5), events.recv())
                    .await
                    .unwrap(),
                Some(event.clone())
            );
        }
        tokio::time::timeout(Duration::from_secs(5), async {
            while runtime.persistence_diagnostics().publication_attempts
                == before.publication_attempts
            {
                tokio::task::yield_now().await;
            }
        })
        .await
        .unwrap();
        let after = runtime.persistence_diagnostics();
        assert_eq!(
            after.calls["event"].completed - before.calls["event"].completed,
            1
        );
        assert_eq!(after.profile.completed - before.profile.completed, 1);
        println!(
            "{}",
            serde_json::json!({
                "event":"persistence_measurement", "observers":observers,
                "writes":after.profile.completed - before.profile.completed,
                "committed_bytes":after.profile.committed_bytes - before.profile.committed_bytes,
                "write_us":after.profile.atomic_write_us - before.profile.atomic_write_us,
                "total_us":after.profile.total_us - before.profile.total_us,
            })
        );
        drop(subscribers);
        drop(background);
    }
    runtime.shutdown().await.unwrap();
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn persistence_barrier_precedes_every_observer_and_failed_write_closes_them() {
    let (dir, runtime) = fixture().await;
    runtime.set_error_sink(Arc::new(|_| {}));
    let (input, source) = mpsc::channel(2);
    runtime.spawn_event_persistence_from(source);
    let mut first = runtime.sdk_client().subscribe_events();
    let mut second = runtime.sdk_client().subscribe_events();
    let before = runtime.persistence_diagnostics();
    let locked = runtime.0.save_lock.lock().await;
    let event = ClientEvent::EventsLagged { skipped: 2 };
    input.send(event.clone()).await.unwrap();
    tokio::time::timeout(Duration::from_secs(5), async {
        while runtime.persistence_diagnostics().calls["event"].requested
            == before.calls["event"].requested
        {
            tokio::task::yield_now().await;
        }
    })
    .await
    .unwrap();
    assert!(matches!(
        first.try_recv(),
        Err(mpsc::error::TryRecvError::Empty)
    ));
    assert!(matches!(
        second.try_recv(),
        Err(mpsc::error::TryRecvError::Empty)
    ));
    assert_eq!(
        runtime.persistence_diagnostics().profile.completed,
        before.profile.completed
    );
    drop(locked);
    for subscriber in [&mut first, &mut second] {
        assert_eq!(
            tokio::time::timeout(Duration::from_secs(5), subscriber.recv())
                .await
                .unwrap(),
            Some(event.clone())
        );
    }
    assert_eq!(
        runtime.persistence_diagnostics().profile.completed - before.profile.completed,
        1
    );

    // Fail the real atomic replacement, not a mocked save future. No event
    // from that failed barrier may reach either observer.
    let committed_before_failure = runtime.persistence_diagnostics().profile.committed_bytes;
    let profile = dir.path().join("protocol");
    let retained = dir.path().join("retained");
    std::fs::rename(&profile, &retained).unwrap();
    std::fs::create_dir(&profile).unwrap();
    input
        .send(ClientEvent::EventsLagged { skipped: 3 })
        .await
        .unwrap();
    for subscriber in [&mut first, &mut second] {
        assert_eq!(
            tokio::time::timeout(Duration::from_secs(5), subscriber.recv())
                .await
                .unwrap(),
            None
        );
    }
    assert_eq!(
        runtime.persistence_diagnostics().calls["event"].failed,
        before.calls["event"].failed + 1
    );
    assert_eq!(
        runtime.persistence_diagnostics().profile.committed_bytes,
        committed_before_failure
    );

    std::fs::remove_dir(&profile).unwrap();
    std::fs::rename(retained, &profile).unwrap();
    let mut recovered = runtime.sdk_client().subscribe_events();
    let retry = ClientEvent::EventsLagged { skipped: 4 };
    input.send(retry.clone()).await.unwrap();
    assert_eq!(
        tokio::time::timeout(Duration::from_secs(5), recovered.recv())
            .await
            .unwrap(),
        Some(retry)
    );
    runtime.shutdown().await.unwrap();
    let (_store, data) = ProtocolStore::open(&profile, "test-only-passphrase").unwrap();
    assert!(
        data.node_state.is_some(),
        "the last successful snapshot reopens"
    );
}

#[tokio::test]
async fn persistence_failure_cannot_be_lost_behind_a_slow_observer() {
    let (events, source) = broadcast::channel(2);
    let (sender, _receiver) = mpsc::channel(1);
    let (failures, failure_rx) = watch::channel(0);
    let worker = tokio::spawn(forward_protocol_events(source, sender, failure_rx, None));
    events
        .send(ClientEvent::EventsLagged { skipped: 1 })
        .unwrap();
    tokio::task::yield_now().await;
    for skipped in 2..20 {
        events.send(ClientEvent::EventsLagged { skipped }).unwrap();
    }
    failures.send_modify(|generation| *generation += 1);
    tokio::time::timeout(Duration::from_secs(2), worker)
        .await
        .unwrap()
        .unwrap();
}

#[tokio::test]
async fn persistence_fanout_reports_lag_without_another_save() {
    let (events, source) = broadcast::channel(2);
    let (sender, mut receiver) = mpsc::channel(4);
    let (_failures, failure_rx) = watch::channel(0);
    for skipped in 10..14 {
        events.send(ClientEvent::EventsLagged { skipped }).unwrap();
    }
    let worker = tokio::spawn(forward_protocol_events(source, sender, failure_rx, None));
    assert_eq!(
        receiver.recv().await,
        Some(ClientEvent::EventsLagged { skipped: 2 })
    );
    assert_eq!(
        receiver.recv().await,
        Some(ClientEvent::EventsLagged { skipped: 12 })
    );
    assert_eq!(
        receiver.recv().await,
        Some(ClientEvent::EventsLagged { skipped: 13 })
    );
    drop(receiver);
    tokio::time::timeout(Duration::from_secs(2), worker)
        .await
        .unwrap()
        .unwrap();
}
