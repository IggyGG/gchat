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
            let (input, events) = mpsc::channel(1);
            subscribers.push((input, runtime.forward_events(events, None)));
        }
        let before = runtime.persistence_diagnostics();
        let event = ClientEvent::EventsLagged { skipped: 1 };
        background.send(event.clone()).await.unwrap();
        for (input, _) in &subscribers {
            input.send(event.clone()).await.unwrap();
        }
        for (_, events) in &mut subscribers {
            assert_eq!(
                tokio::time::timeout(Duration::from_secs(5), events.recv())
                    .await
                    .unwrap(),
                Some(event.clone())
            );
        }
        tokio::time::timeout(Duration::from_secs(5), async {
            while runtime.persistence_diagnostics().calls["event"].completed
                == before.calls["event"].completed
            {
                tokio::task::yield_now().await;
            }
        })
        .await
        .unwrap();
        let after = runtime.persistence_diagnostics();
        assert_eq!(
            after.calls["subscriber"].completed - before.calls["subscriber"].completed,
            observers
        );
        assert_eq!(
            after.profile.completed - before.profile.completed,
            1 + observers
        );
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
