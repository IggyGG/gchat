//! Real RPC admission and encrypted journal, with a bounded effect/failure fixture.
use super::*;
use std::sync::atomic::{AtomicUsize, Ordering};
use tokio::sync::Notify;

async fn fixture() -> (tempfile::TempDir, ProtocolRuntime, Arc<ChatService>) {
    let home = tempfile::tempdir().unwrap();
    crate::private_fs::make_private(home.path(), true).unwrap();
    let runtime = ProtocolRuntime::create_fixture(
        &home.path().join("profile"),
        "liveness-fixture",
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
        ],
    )
    .unwrap();
    service
        .handle(Request::Unlock {
            passphrase: "liveness-fixture".into(),
            create: true,
        })
        .await
        .unwrap();
    (home, runtime, service)
}

struct UncertainEndpoint {
    service: Arc<ChatService>,
    effect: std::path::PathBuf,
    entered: Notify,
    finish: Notify,
    calls: AtomicUsize,
    panic: bool,
}
#[async_trait::async_trait]
impl ChatEndpoint for UncertainEndpoint {
    fn instance_id(&self) -> &str {
        &self.service.id
    }
    async fn rpc_service(self: Arc<Self>) -> Option<Arc<ChatService>> {
        Some(self.service.clone())
    }
    async fn dispatch(&self, request: RequestEnvelope) -> ResponseEnvelope {
        assert!(matches!(request.request, Request::Networks { .. }));
        self.calls.fetch_add(1, Ordering::SeqCst);
        let mut effect = std::fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&self.effect)
            .unwrap();
        std::io::Write::write_all(&mut effect, b"one durable effect").unwrap();
        effect.sync_all().unwrap();
        self.entered.notify_one();
        self.finish.notified().await;
        assert!(!self.panic, "controlled failure after the effect");
        ResponseEnvelope {
            version: VERSION,
            instance_id: self.service.id.clone(),
            response: Response::Error {
                code: "outcome_unknown".into(),
                message: "Effect happened; no confirmed result".into(),
            },
        }
    }
    async fn flush(&self) -> Result<(), String> {
        self.service.flush().await
    }
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn stopped_uncertain_rpc_releases_update_gate_without_replaying_effects() {
    for panic in [false, true] {
        let (home, runtime, service) = fixture().await;
        tokio::time::timeout(Duration::from_secs(30), async {
            let endpoint = Arc::new(UncertainEndpoint { service: service.clone(), effect: home.path().join("effect"),
                entered: Notify::new(), finish: Notify::new(), calls: AtomicUsize::new(0), panic });
            let router = router(endpoint.clone()).unwrap();
            let caller = gcoms::rpc::Caller { principal: "local-owner".into() };
            let id = gcoms::rpc::OperationId::new("uncertain-operation-fixture").unwrap();
            let request = gcoms::rpc::Request {
                rpc: gcoms::rpc::WIRE_VERSION, id: gcoms::rpc::new_id(), instance: service.id.clone(),
                service: SERVICE.into(), version: SERVICE_VERSION, method: "network_operation".into(),
                invocation: Invocation::Call {
                    args: serde_json::json!({"request": gchat_api::NetworkRequest::Call {
                        network: "fixture".into(), request: Box::new(Request::MarkRead { conversation: "fixture".into(), message_id: "message".into() })
                    }}),
                    operation: Some(gcoms::rpc::OperationToken { id: id.clone(), deadline: gcoms::rpc::DecimalU64(gcoms::rpc::unix_time() + 60) }),
                },
            };
            assert_eq!(router.handle(caller.clone(), request.clone()).await.body, ReplyBody::Running);
            endpoint.entered.notified().await;
            assert_eq!(std::fs::read(&endpoint.effect).unwrap(), b"one durable effect");
            assert!(service.pause_for_update().await.is_err(), "active admitted worker must block maintenance");
            endpoint.finish.notify_one();
            let mut status = request.clone();
            status.invocation = Invocation::Status { operation_id: id.clone() };
            loop {
                let body = router.handle(caller.clone(), status.clone()).await.body;
                if body == ReplyBody::OutcomeUnknown { break; }
                assert_eq!(body, ReplyBody::Running);
                tokio::task::yield_now().await;
            }
            assert_eq!(router.handle(caller, request).await.body, ReplyBody::OutcomeUnknown);
            assert_eq!(endpoint.calls.load(Ordering::SeqCst), 1, "retry must never repeat the effect");
            let key = OperationKey { caller: "local-owner".into(), instance: service.id.clone(), service: SERVICE.into(),
                version: SERVICE_VERSION, method: "network_operation".into(), operation_id: id };
            assert_eq!(service.rpc_get(&key, gcoms::rpc::unix_time()).await.unwrap().unwrap().result, None);
            service.pause_for_update().await.expect("finished uncertain worker no longer owns work");
            service.resume_after_update().await;
            router.shutdown().await;
        }).await.expect("bounded uncertain RPC lifecycle");
        service.disconnect().await.unwrap();
        runtime.shutdown().await.unwrap();
    }
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn failed_completion_save_releases_liveness_but_preserves_unknown_admission() {
    let (home, runtime, service) = fixture().await;
    let at = gcoms::rpc::unix_time();
    let mut key = OperationKey {
        caller: "local-owner".into(),
        instance: service.id.clone(),
        service: SERVICE.into(),
        version: SERVICE_VERSION,
        method: "submit".into(),
        operation_id: gcoms::rpc::OperationId::new("completion-save-failure-fixture").unwrap(),
    };
    assert!(matches!(
        service
            .rpc_admit(&key, "same-digest", at + 60, at)
            .await
            .unwrap(),
        Admission::New
    ));
    let archive = home.path().join("archive.service");
    let backup = home.path().join("archive.service-backup");
    std::fs::rename(&archive, &backup).unwrap();
    std::fs::create_dir(&archive).unwrap();
    let result = ReplyBody::Done {
        outcome: Outcome::Ok(serde_json::json!({"value": "retained typed result"})),
    };
    let failed = service.rpc_complete(&key, result.clone()).await;
    std::fs::remove_dir(&archive).unwrap();
    std::fs::rename(&backup, &archive).unwrap();
    assert_eq!(failed.unwrap_err().code, ErrorCode::Storage);
    assert_eq!(
        service.rpc_get(&key, at).await.unwrap().unwrap().result,
        None
    );
    assert!(matches!(
        service
            .rpc_admit(&key, "same-digest", at + 60, at)
            .await
            .unwrap(),
        Admission::Existing(_)
    ));
    service.pause_for_update().await.unwrap();
    service.resume_after_update().await;
    // A known result still holds the gate throughout its completion write.
    key.operation_id = gcoms::rpc::OperationId::new("completion-success-fixture").unwrap();
    assert!(matches!(
        service
            .rpc_admit(&key, "known-digest", at + 60, at)
            .await
            .unwrap(),
        Admission::New
    ));
    assert!(service.pause_for_update().await.is_err());
    service.rpc_complete(&key, result.clone()).await.unwrap();
    assert_eq!(
        service.rpc_get(&key, at).await.unwrap().unwrap().result,
        Some(result)
    );
    service.pause_for_update().await.unwrap();
    service.resume_after_update().await;
    service.disconnect().await.unwrap();
    runtime.shutdown().await.unwrap();
}
