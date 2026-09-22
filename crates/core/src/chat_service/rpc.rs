//! Typed chat handlers and an adapter over the existing encrypted chat journal.
//! Legacy submit IDs, SHA-256 digests and responses retain their original meaning.
use super::*;
use gchat_api::{
    rpc::{Applied, Chat, ChatDispatcher, ChatSubmitArgs, SubmitOutcome, SERVICE, SERVICE_VERSION},
    ChatError, CommandSpec,
};
use gcoms::rpc::{
    Admission, CallContext, Dispatch, ErrorCode, Invocation, OperationKey, OperationStore, Outcome,
    ReplyBody, RpcError,
};

#[derive(Clone, Serialize, Deserialize)]
pub(super) struct RecordBinding {
    key: OperationKey,
    result: Option<ReplyBody>,
}

fn storage(message: impl Into<String>) -> RpcError {
    RpcError::new(ErrorCode::Storage, message)
}
fn locked() -> RpcError {
    RpcError::new(
        ErrorCode::Unauthorized,
        "unlock the selected archive to inspect operation results",
    )
}
fn domain(message: String) -> ChatError {
    ChatError {
        code: "rejected".into(),
        message,
    }
}
fn record_id(key: &OperationKey) -> String {
    if key.method == "submit" {
        key.operation_id.as_str().into()
    } else {
        format!("rpc:{}:{}", key.method, key.operation_id.as_str())
    }
}

impl ChatService {
    fn check_key(&self, key: &OperationKey) -> Result<(), RpcError> {
        if key.caller != "local-owner"
            || key.instance != self.id
            || key.service != SERVICE
            || key.version != SERVICE_VERSION
            || !matches!(
                key.method.as_str(),
                "submit" | "mark_read" | "network_operation"
            )
        {
            return Err(RpcError::new(
                ErrorCode::Unauthorized,
                "chat operation binding mismatch",
            ));
        }
        Ok(())
    }
    fn rpc_record(
        key: &OperationKey,
        record: &OperationRecord,
    ) -> Result<gcoms::rpc::OperationRecord, RpcError> {
        if let Some(binding) = &record.rpc {
            if binding.key != *key {
                return Err(RpcError::new(
                    ErrorCode::Conflict,
                    "operation belongs to another method or caller",
                ));
            }
        } else if key.method != "submit" {
            return Err(RpcError::new(
                ErrorCode::Unavailable,
                "operation unavailable",
            ));
        }
        // A legacy response was itself durably saved before acknowledgement.
        let result = record
            .rpc
            .as_ref()
            .and_then(|r| r.result.clone())
            .or_else(|| {
                record.response.clone().map(|response| {
                    if matches!(&response, Response::Error { code, .. } if code == "outcome_unknown") {
                        return ReplyBody::OutcomeUnknown;
                    }
                    let outcome = gcoms::rpc::encode_outcome(SubmitOutcome::try_from(response));
                    match outcome {
                        Ok(outcome) => ReplyBody::Done { outcome },
                        Err(error) => ReplyBody::Failed { error },
                    }
                })
            });
        Ok(gcoms::rpc::OperationRecord {
            key: key.clone(),
            digest: record.digest.clone(),
            admitted_at: gcoms::rpc::DecimalU64(record.at),
            retain_until: gcoms::rpc::DecimalU64(
                record.at.saturating_add(gcoms::rpc::DEFAULT_RETENTION_SECS),
            ),
            result,
        })
    }
    async fn rpc_get(
        &self,
        key: &OperationKey,
        at: u64,
    ) -> Result<Option<gcoms::rpc::OperationRecord>, RpcError> {
        self.check_key(key)?;
        let session = self.session.lock().await;
        let unlocked = session
            .as_ref()
            .filter(|s| !s.ui_locked)
            .ok_or_else(locked)?;
        unlocked
            .state
            .operations
            .get(&record_id(key))
            .filter(|r| r.at.saturating_add(gcoms::rpc::DEFAULT_RETENTION_SECS) > at)
            .map(|r| Self::rpc_record(key, r))
            .transpose()
    }
    async fn rpc_admit(
        &self,
        key: &OperationKey,
        digest: &str,
        deadline: u64,
        at: u64,
    ) -> Result<Admission, RpcError> {
        self.check_key(key)?;
        let mut session = self.session.lock().await;
        let unlocked = session
            .as_mut()
            .filter(|s| !s.ui_locked)
            .ok_or_else(locked)?;
        let id = record_id(key);
        if let Some(old) = unlocked
            .state
            .operations
            .get(&id)
            .filter(|r| r.at.saturating_add(gcoms::rpc::DEFAULT_RETENTION_SECS) > at)
        {
            if old.digest != digest {
                return Err(RpcError::new(
                    ErrorCode::Conflict,
                    "operation ID was used with different contents",
                ));
            }
            return Ok(Admission::Existing(Box::new(Self::rpc_record(key, old)?)));
        }
        if deadline <= at || deadline > at.saturating_add(600) {
            return Err(RpcError::new(
                ErrorCode::Expired,
                "submission deadline expired",
            ));
        }
        let mut candidate = unlocked.state.clone();
        candidate
            .operations
            .retain(|_, r| r.at.saturating_add(gcoms::rpc::DEFAULT_RETENTION_SECS) > at);
        if candidate.operations.len() >= OPERATION_LIMIT {
            return Err(RpcError::new(
                ErrorCode::Busy,
                "chat operation journal is full",
            ));
        }
        candidate.operations.insert(
            id,
            OperationRecord {
                action: String::new(),
                conversation: None,
                digest: digest.into(),
                at,
                response: None,
                rpc: Some(RecordBinding {
                    key: key.clone(),
                    result: None,
                }),
            },
        );
        unlocked.store.save(&candidate).map_err(storage)?;
        unlocked.state = candidate;
        Ok(Admission::New)
    }
    async fn rpc_complete(&self, key: &OperationKey, result: ReplyBody) -> Result<(), RpcError> {
        self.check_key(key)?;
        let mut session = self.session.lock().await;
        // A view locking while an admitted operation completes must not discard
        // its result. Reading the result still requires an unlocked view.
        let unlocked = session.as_mut().ok_or_else(locked)?;
        let mut candidate = unlocked.state.clone();
        let record = candidate
            .operations
            .get_mut(&record_id(key))
            .ok_or_else(|| storage("operation admission missing"))?;
        let binding = record
            .rpc
            .as_mut()
            .ok_or_else(|| storage("RPC admission missing"))?;
        if binding.key != *key {
            return Err(RpcError::new(
                ErrorCode::Conflict,
                "operation binding changed",
            ));
        }
        if binding.result.as_ref().is_some_and(|old| old != &result) {
            return Err(RpcError::new(
                ErrorCode::Conflict,
                "operation already completed",
            ));
        }
        binding.result = Some(result);
        unlocked.store.save(&candidate).map_err(storage)?;
        unlocked.state = candidate;
        Ok(())
    }
}

struct ChatStore<S>(Arc<S>);
#[async_trait::async_trait]
impl<S: ChatEndpoint> OperationStore for ChatStore<S> {
    async fn admit(
        &self,
        key: &OperationKey,
        digest: &str,
        deadline: u64,
        now: u64,
    ) -> Result<Admission, RpcError> {
        self.0
            .clone()
            .rpc_service()
            .await
            .ok_or_else(locked)?
            .rpc_admit(key, digest, deadline, now)
            .await
    }
    async fn complete(&self, key: &OperationKey, result: ReplyBody) -> Result<(), RpcError> {
        self.0
            .clone()
            .rpc_service()
            .await
            .ok_or_else(locked)?
            .rpc_complete(key, result)
            .await
    }
    async fn get(
        &self,
        key: &OperationKey,
        now: u64,
    ) -> Result<Option<gcoms::rpc::OperationRecord>, RpcError> {
        self.0
            .clone()
            .rpc_service()
            .await
            .ok_or_else(locked)?
            .rpc_get(key, now)
            .await
    }
}

struct Handlers<S>(Arc<S>);
impl<S: ChatEndpoint> Handlers<S> {
    async fn request(&self, request: Request) -> Result<Response, ChatError> {
        let response = self
            .0
            .dispatch(RequestEnvelope {
                version: VERSION,
                instance_id: Some(self.0.instance_id().into()),
                request,
            })
            .await
            .response;
        match response {
            Response::Error { code, message } => Err(ChatError { code, message }),
            response => Ok(response),
        }
    }
}
macro_rules! expect_response {
    ($self:ident, $request:expr, $variant:ident, $field:ident) => {
        match $self.request($request).await? {
            Response::$variant { $field } => Ok($field),
            _ => Err(ChatError {
                code: "protocol".into(),
                message: "unexpected chat handler response".into(),
            }),
        }
    };
}
#[async_trait::async_trait]
impl<S: ChatEndpoint> Chat for Handlers<S> {
    async fn files(
        &self,
        request: gchat_api::FileRequest,
    ) -> Result<gchat_api::FileSnapshot, ChatError> {
        expect_response!(self, Request::Files { request }, Files, snapshot)
    }

    async fn identify(&self) -> Result<InstanceInfo, ChatError> {
        expect_response!(self, Request::Identify, Instance, instance)
    }
    async fn unlock(&self, passphrase: String, create: bool) -> Result<Snapshot, ChatError> {
        expect_response!(
            self,
            Request::Unlock { passphrase, create },
            Snapshot,
            snapshot
        )
    }
    async fn lock(&self) -> Result<InstanceInfo, ChatError> {
        expect_response!(self, Request::Lock, Instance, instance)
    }
    async fn disconnect(&self) -> Result<Snapshot, ChatError> {
        expect_response!(self, Request::Disconnect, Snapshot, snapshot)
    }
    async fn snapshot(&self) -> Result<Snapshot, ChatError> {
        expect_response!(self, Request::Snapshot, Snapshot, snapshot)
    }
    async fn network_status(&self) -> Result<gchat_api::NetworkStatus, ChatError> {
        expect_response!(self, Request::NetworkStatus, NetworkStatus, status)
    }
    async fn networks(
        &self,
        request: gchat_api::NetworkRequest,
    ) -> Result<gchat_api::NetworkResponse, ChatError> {
        expect_response!(self, Request::Networks { request }, Networks, response)
    }
    async fn network_operation(
        &self,
        context: CallContext,
        mut request: gchat_api::NetworkRequest,
    ) -> Result<gchat_api::NetworkResponse, ChatError> {
        let operation = context
            .operation
            .ok_or_else(|| domain("operation token missing".into()))?;
        match &mut request {
            gchat_api::NetworkRequest::Join { operation_id, .. } => {
                *operation_id = operation.id.as_str().into()
            }
            gchat_api::NetworkRequest::Call { request, .. } => match request.as_mut() {
                Request::Submit { operation_id, .. } => {
                    *operation_id = operation.id.as_str().into()
                }
                Request::MarkRead { .. } => {}
                _ => {
                    return Err(domain(
                        "This network request is not a durable operation".into(),
                    ))
                }
            },
            _ => {
                return Err(domain(
                    "This network request is not a durable operation".into(),
                ))
            }
        }
        let result = self.networks(request).await.map_err(|error| ChatError {
            code: "outcome_unknown".into(),
            message: error.message,
        })?;
        if let gchat_api::NetworkResponse::Result { response, .. } = &result {
            if let Response::Error { code, message } = response.as_ref() {
                return Err(ChatError {
                    code: code.clone(),
                    message: message.clone(),
                });
            }
        }
        Ok(result)
    }
    async fn import_network_invitation(
        &self,
        code: String,
    ) -> Result<gchat_api::NetworkStatus, ChatError> {
        expect_response!(
            self,
            Request::ImportNetworkInvitation { code },
            NetworkStatus,
            status
        )
    }
    async fn catalogue(&self, conversation: Option<String>) -> Result<Vec<CommandSpec>, ChatError> {
        expect_response!(
            self,
            Request::Catalogue { conversation },
            Catalogue,
            commands
        )
    }
    async fn history(
        &self,
        conversation: String,
        before: Option<String>,
        limit: u16,
    ) -> Result<HistoryPage, ChatError> {
        expect_response!(
            self,
            Request::History {
                conversation,
                before,
                limit
            },
            History,
            page
        )
    }
    async fn search(
        &self,
        conversation: String,
        text: String,
        before: Option<String>,
        limit: u16,
    ) -> Result<HistoryPage, ChatError> {
        expect_response!(
            self,
            Request::Search {
                conversation,
                text,
                before,
                limit
            },
            History,
            page
        )
    }
    async fn submit(
        &self,
        context: CallContext,
        conversation: Option<String>,
        text: String,
    ) -> Result<SubmitOutcome, ChatError> {
        let operation = context
            .operation
            .ok_or_else(|| domain("operation token missing".into()))?;
        let service = self
            .0
            .clone()
            .rpc_service()
            .await
            .ok_or_else(|| domain("instance disconnected".into()))?;
        let response = service
            .handle_mode(
                Request::Submit {
                    operation_id: operation.id.as_str().into(),
                    conversation,
                    text,
                },
                true,
            )
            .await
            .map_err(|message| ChatError {
                code: "outcome_unknown".into(),
                message,
            })?;
        SubmitOutcome::try_from(response)
    }
    async fn complete(
        &self,
        conversation: Option<String>,
        text: String,
    ) -> Result<Vec<Completion>, ChatError> {
        expect_response!(
            self,
            Request::Complete { conversation, text },
            Completed,
            items
        )
    }
    async fn mark_read(
        &self,
        conversation: String,
        message_id: String,
    ) -> Result<Applied, ChatError> {
        match self
            .request(Request::MarkRead {
                conversation,
                message_id,
            })
            .await?
        {
            Response::Applied {
                conversation,
                notice,
            } => Ok(Applied {
                conversation,
                notice,
            }),
            _ => Err(domain("unexpected mark-read response".into())),
        }
    }
    async fn events(&self, after: String, wait_ms: u16) -> Result<String, ChatError> {
        expect_response!(self, Request::Events { after, wait_ms }, Changed, revision)
    }
}

struct ChatDispatch<S>(ChatDispatcher<Handlers<S>>);
#[async_trait::async_trait]
impl<S: ChatEndpoint> Dispatch for ChatDispatch<S> {
    fn descriptor(&self) -> gcoms::rpc::Service {
        self.0.descriptor()
    }
    fn validate(
        &self,
        method: &str,
        args: serde_json::Value,
    ) -> Result<serde_json::Value, RpcError> {
        let value = self.0.validate(method, args)?;
        if method == "import_network_invitation"
            && args_size(&value) > gchat_api::MAX_NETWORK_INVITATION_BYTES
        {
            return Err(RpcError::invalid("network invitation exceeds size limit"));
        }

        if method == "submit" {
            let args: ChatSubmitArgs = serde_json::from_value(value.clone())
                .map_err(|e| RpcError::invalid(e.to_string()))?;
            if args.text.is_empty() || args.text.len() > gchat_api::MAX_INPUT_BYTES {
                return Err(RpcError::invalid("submit text exceeds chat input bounds"));
            }
            if matches!(args.text.trim(), "/lock" | "/disconnect" | "/quit") {
                return Err(RpcError::invalid(
                    "use the lock or disconnect session method",
                ));
            }
        }
        Ok(value)
    }
    fn digest(&self, method: &str, args: &serde_json::Value) -> Result<String, RpcError> {
        if method == "submit" {
            let args: ChatSubmitArgs = serde_json::from_value(args.clone())
                .map_err(|e| RpcError::invalid(e.to_string()))?;
            return Ok(hex(&Sha256::digest(
                serde_json::to_vec(&(args.conversation.as_ref(), &args.text))
                    .map_err(|e| RpcError::invalid(e.to_string()))?,
            )));
        }
        self.0.digest(method, args)
    }
    async fn invoke(
        &self,
        context: CallContext,
        method: &str,
        args: serde_json::Value,
    ) -> Result<Outcome, RpcError> {
        let outcome = self.0.invoke(context, method, args).await?;
        if matches!(method, "submit" | "network_operation")
            && matches!(&outcome, Outcome::Error(value) if value["code"] == "outcome_unknown")
        {
            // Keep the admitted operation uncertain; an execution/storage
            // failure after effects is not a definitive domain rejection.
            return Err(RpcError::new(
                ErrorCode::Unavailable,
                "chat operation outcome unknown",
            ));
        }
        Ok(outcome)
    }
}

pub fn router<S: ChatEndpoint>(endpoint: Arc<S>) -> Result<Arc<gcoms::rpc::Router>, RpcError> {
    let mut router = gcoms::rpc::Router::new(endpoint.instance_id(), 32, MAX_FRAME_BYTES);
    router.register(
        Arc::new(ChatDispatch(ChatDispatcher(Handlers(endpoint.clone())))),
        Arc::new(ChatStore(endpoint)),
        Arc::new(|caller: &gcoms::rpc::Caller, _: &str, _: u16, _: &str| {
            caller.principal == "local-owner"
        }),
    )?;
    Ok(Arc::new(router))
}

/// Read-only lookup used by compatibility clients retaining old submit IDs.
pub fn status_request(
    instance: &str,
    operation_id: gcoms::rpc::OperationId,
) -> gcoms::rpc::Request {
    gcoms::rpc::Request {
        rpc: gcoms::rpc::WIRE_VERSION,
        id: gcoms::rpc::new_id(),
        instance: instance.into(),
        service: SERVICE.into(),
        version: SERVICE_VERSION,
        method: "submit".into(),
        invocation: Invocation::Status { operation_id },
    }
}

fn args_size(value: &serde_json::Value) -> usize {
    value
        .get("code")
        .and_then(|v| v.as_str())
        .map_or(0, str::len)
}
