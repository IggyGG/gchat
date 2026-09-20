//! Compatibility methods implemented using generated, typed service calls.
use crate::{rpc, ChatError, Request, Response};
use gcoms_rpc::{CallError, Client, OperationHandle, OperationId, ReplyBody};

pub(super) fn error(error: CallError<ChatError>) -> ChatError {
    match error {
        CallError::Service(error) => error,
        CallError::Rpc(error) => ChatError {
            code: serde_json::to_value(error.code)
                .ok()
                .and_then(|v| v.as_str().map(str::to_owned))
                .unwrap_or_else(|| "protocol".into()),
            message: error.message,
        },
        CallError::OutcomeUnknown(_) => ChatError {
            code: "outcome_unknown".into(),
            message:
                "Operation was interrupted after admission; it will not be sent again automatically"
                    .into(),
        },
        CallError::Unavailable(_) => ChatError {
            code: "unavailable".into(),
            message: "Operation result is unavailable".into(),
        },
    }
}

pub(super) async fn request<T: gcoms_rpc::Transport>(
    client: Client<T>,
    request: Request,
) -> Result<Response, ChatError> {
    let client = rpc::ChatClient::new(client);
    Ok(match request {
        Request::Files { request } => Response::Files {
            snapshot: client.files(request).await.map_err(error)?,
        },
        Request::Identify => Response::Instance {
            instance: client.identify().await.map_err(error)?,
        },
        Request::Unlock { passphrase, create } => Response::Snapshot {
            snapshot: client.unlock(passphrase, create).await.map_err(error)?,
        },
        Request::Lock => Response::Instance {
            instance: client.lock().await.map_err(error)?,
        },
        Request::Disconnect => Response::Snapshot {
            snapshot: client.disconnect().await.map_err(error)?,
        },
        Request::Snapshot => Response::Snapshot {
            snapshot: client.snapshot().await.map_err(error)?,
        },
        Request::Networks { request } => Response::Networks {
            response: client.networks(request).await.map_err(error)?,
        },
        Request::NetworkStatus => Response::NetworkStatus {
            status: client.network_status().await.map_err(error)?,
        },
        Request::ImportNetworkInvitation { code } => Response::NetworkStatus {
            status: client
                .import_network_invitation(code)
                .await
                .map_err(error)?,
        },
        Request::Catalogue { conversation } => Response::Catalogue {
            commands: client.catalogue(conversation).await.map_err(error)?,
        },
        Request::History {
            conversation,
            before,
            limit,
        } => Response::History {
            page: client
                .history(conversation, before, limit)
                .await
                .map_err(error)?,
        },
        Request::Search {
            conversation,
            text,
            before,
            limit,
        } => Response::History {
            page: client
                .search(conversation, text, before, limit)
                .await
                .map_err(error)?,
        },
        Request::Submit {
            operation_id,
            conversation,
            text,
        } => {
            if text.trim() == "/lock" {
                Response::Instance {
                    instance: client.lock().await.map_err(error)?,
                }
            } else if matches!(text.trim(), "/disconnect" | "/quit") {
                Response::Snapshot {
                    snapshot: client.disconnect().await.map_err(error)?,
                }
            } else if let Some(code) = network_invitation(&text) {
                client
                    .import_network_invitation(code.into())
                    .await
                    .map_err(error)?;
                Response::Applied {
                    conversation: None,
                    notice: Some("Network invitation saved. Connecting in the background.".into()),
                }
            } else {
                let mut prepared = client
                    .prepare_submit(conversation, text)
                    .map_err(|e| error(CallError::Rpc(e)))?;
                prepared.handle.operation.id =
                    OperationId::new(operation_id).map_err(|e| error(CallError::Rpc(e)))?;
                if let Some(existing) = client
                    .inner
                    .handles()
                    .list()
                    .map_err(|e| error(CallError::Rpc(e)))?
                    .into_iter()
                    .find(|h| {
                        h.destination == prepared.handle.destination
                            && h.instance == prepared.handle.instance
                            && h.service == prepared.handle.service
                            && h.method == "submit"
                            && h.operation.id == prepared.handle.operation.id
                    })
                {
                    prepared.handle = existing;
                }
                let result = client
                    .inner
                    .start_and_wait(&prepared)
                    .await
                    .map_err(error)?;
                let _ = client.inner.handles().forget(&prepared.handle);
                result.into()
            }
        }
        Request::Complete { conversation, text } => Response::Completed {
            items: client.complete(conversation, text).await.map_err(error)?,
        },
        Request::MarkRead {
            conversation,
            message_id,
        } => {
            let prepared = client
                .prepare_mark_read(conversation, message_id)
                .map_err(|e| error(CallError::Rpc(e)))?;
            let applied = client
                .inner
                .start_and_wait(&prepared)
                .await
                .map_err(error)?;
            let _ = client.inner.handles().forget(&prepared.handle);
            Response::Applied {
                conversation: applied.conversation,
                notice: applied.notice,
            }
        }
        Request::Events { after, wait_ms } => Response::Changed {
            revision: client.events(after, wait_ms).await.map_err(error)?,
        },
    })
}

pub(super) async fn status<T: gcoms_rpc::Transport>(
    client: &Client<T>,
    id: &str,
) -> Result<ReplyBody, ChatError> {
    let handle = handle(client, id)?;
    client
        .status(&handle)
        .await
        .map_err(|e| error(CallError::Rpc(e)))
}
pub(super) async fn resume<T: gcoms_rpc::Transport>(
    client: &Client<T>,
    id: &str,
) -> Result<Response, ChatError> {
    let result = client
        .resume::<rpc::SubmitOutcome, ChatError>(&handle(client, id)?)
        .await
        .map(Into::into)
        .map_err(error)?;
    if let Ok(handles) = client.handles().list() {
        for h in handles.into_iter().filter(|h| {
            h.instance == client.instance()
                && h.destination == client.destination()
                && h.method == "submit"
                && h.operation.id.as_str() == id
        }) {
            let _ = client.handles().forget(&h);
        }
    }
    Ok(result)
}
fn handle<T: gcoms_rpc::Transport>(
    client: &Client<T>,
    id: &str,
) -> Result<OperationHandle, ChatError> {
    Ok(OperationHandle {
        destination: client.destination().into(),
        instance: client.instance().into(),
        service: rpc::SERVICE.into(),
        version: rpc::SERVICE_VERSION,
        method: "submit".into(),
        operation: gcoms_rpc::OperationToken {
            id: OperationId::new(id).map_err(|e| error(CallError::Rpc(e)))?,
            deadline: gcoms_rpc::DecimalU64(0),
        },
    })
}

fn network_invitation(text: &str) -> Option<&str> {
    let (command, args) = text.trim().split_once(char::is_whitespace)?;
    let (action, code) = args.trim().split_once(char::is_whitespace)?;
    (command.eq_ignore_ascii_case("/network") && action.eq_ignore_ascii_case("join"))
        .then_some(code.trim())
}
