//! Released attachment dialects. Adapters never grant authority or replay work.
use crate::{
    Delivery, Message, NetworkRequest, NetworkResponse, Request, Response, ResponseEnvelope,
    VERSION,
};

pub const LEGACY_VERSION: u16 = 2;
pub const SUPPORTED_VERSIONS: &[u16] = &[LEGACY_VERSION, VERSION];

#[allow(dead_code)] // Retained released DTOs also decode archived client fixtures.
#[path = "compat_v2.rs"]
pub mod v2;

pub fn supported(version: u16) -> bool {
    SUPPORTED_VERSIONS.contains(&version)
}

pub fn accepts(version: u16, request: &Request) -> bool {
    if !supported(version) {
        return false;
    }
    if version == VERSION {
        return true;
    }
    // Validate the released request dialect before any operation is admitted.
    // Nested calls must not smuggle future methods into a legacy attachment.
    if let Request::Networks {
        request: NetworkRequest::Call { request, .. },
    } = request
    {
        if !accepts(version, request) {
            return false;
        }
    }
    serde_json::to_value(request)
        .ok()
        .is_some_and(|value| serde_json::from_value::<v2::Request>(value).is_ok())
}

pub fn response(version: u16, mut envelope: ResponseEnvelope) -> ResponseEnvelope {
    if !supported(version) {
        return envelope;
    }
    envelope.version = version;
    if version == LEGACY_VERSION {
        project(&mut envelope.response);
    }
    envelope
}

fn message(value: &mut Message) {
    value.message_kind = None;
    value.highlighted = None;
    value.delivery = match value.delivery.take() {
        Some(Delivery::ServiceAccepted) => Some(Delivery::LocalAccepted),
        Some(Delivery::Failed) => None,
        value => value,
    };
}

fn conversation(value: &mut crate::Conversation) {
    value.policy = None;
    value.catch_up = None;
    value.muted = None;
    for member in &mut value.members {
        member.presence = None;
    }
}

fn project(value: &mut Response) {
    match value {
        Response::History { page } => {
            for row in &mut page.messages {
                message(row);
            }
        }
        Response::Snapshot { snapshot } => {
            snapshot.presence_enabled = None;
            for row in &mut snapshot.conversations {
                conversation(row);
            }
        }
        Response::Projection { conversations, .. } => {
            for row in conversations {
                conversation(row);
            }
        }
        Response::Networks {
            response: NetworkResponse::Result { response, .. },
        } => project(response),
        _ => {}
    }
}

pub fn legacy_response(mut value: Response) -> Response {
    project(&mut value);
    value
}

pub fn legacy_history(mut value: crate::HistoryPage) -> crate::HistoryPage {
    for row in &mut value.messages {
        message(row);
    }
    value
}

/// Feature advertisements describe interfaces, never permissions. Permission
/// grants still come exclusively from the existing authenticated host checks.
pub fn capabilities() -> Vec<String> {
    let mut values: Vec<_> = SUPPORTED_VERSIONS
        .iter()
        .map(|version| format!("chat.api.{version}"))
        .collect();
    values.push(format!("chat.rpc.{}", crate::rpc::SERVICE_VERSION));
    values.extend(
        crate::rpc::ChatContract::descriptor()
            .methods
            .into_iter()
            .map(|method| format!("chat.method.{}", method.id)),
    );
    values
}
