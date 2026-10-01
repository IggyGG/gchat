use gchat_api::{
    compat, Delivery, HistoryPage, Message, NetworkResponse, Request, Response, ResponseEnvelope,
    VERSION,
};

fn history() -> Response {
    Response::History {
        page: HistoryPage {
            before: Some("retained-cursor".into()),
            messages: [
                Delivery::LocalAccepted,
                Delivery::ServiceAccepted,
                Delivery::Delivered,
                Delivery::Failed,
            ]
            .into_iter()
            .enumerate()
            .map(|(i, delivery)| Message {
                id: format!("message-{i}"),
                conversation_id: "channel/test".into(),
                member_id: None,
                nickname: "peer".into(),
                body: "  λ\nretained text  ".into(),
                timestamp: 1,
                mine: true,
                operation_id: Some(format!("operation-{i}")),
                delivery: Some(delivery),
                result: None,
                message_kind: Some(gchat_api::MessageKind::Notice),
                highlighted: Some(true),
            })
            .collect(),
        },
    }
}

#[test]
fn released_api_2_decodes_history_without_false_delivery_or_changed_identity() {
    let response = compat::response(
        2,
        ResponseEnvelope {
            version: VERSION,
            instance_id: "same-instance".into(),
            response: history(),
        },
    );
    let old: compat::v2::ResponseEnvelope =
        serde_json::from_value(serde_json::to_value(&response).unwrap()).unwrap();
    assert_eq!(old.version, 2);
    assert_eq!(old.instance_id, "same-instance");
    let compat::v2::Response::History { page } = old.response else {
        panic!("history")
    };
    assert_eq!(page.before.as_deref(), Some("retained-cursor"));
    assert_eq!(
        page.messages[0].delivery,
        Some(compat::v2::Delivery::LocalAccepted)
    );
    assert_eq!(
        page.messages[1].delivery,
        Some(compat::v2::Delivery::LocalAccepted)
    );
    assert_eq!(
        page.messages[2].delivery,
        Some(compat::v2::Delivery::Delivered)
    );
    assert_eq!(page.messages[3].delivery, None);
    for (i, row) in page.messages.iter().enumerate() {
        assert_eq!(row.id, format!("message-{i}"));
        assert_eq!(row.operation_id, Some(format!("operation-{i}")));
        assert_eq!(row.body, "  λ\nretained text  ");
    }
}

#[test]
fn network_scoped_history_uses_the_same_released_adapter() {
    let response = compat::response(
        2,
        ResponseEnvelope {
            version: VERSION,
            instance_id: "same".into(),
            response: Response::Networks {
                response: NetworkResponse::Result {
                    network: "network-id".into(),
                    response: Box::new(history()),
                },
            },
        },
    );
    let old: compat::v2::ResponseEnvelope =
        serde_json::from_value(serde_json::to_value(response).unwrap()).unwrap();
    assert!(matches!(
        old.response,
        compat::v2::Response::Networks { .. }
    ));
}

#[test]
fn unknown_versions_are_rejected_before_admission() {
    assert!(compat::accepts(2, &Request::Identify));
    assert!(compat::accepts(3, &Request::Identify));
    assert!(!compat::accepts(1, &Request::Identify));
    assert!(!compat::accepts(4, &Request::Identify));
}

#[test]
fn detailed_history_remains_available_without_legacy_projection() {
    let response = compat::response(
        3,
        ResponseEnvelope {
            version: VERSION,
            instance_id: "same".into(),
            response: history(),
        },
    );
    let Response::History { page } = response.response else {
        panic!("history")
    };
    assert_eq!(page.messages[1].delivery, Some(Delivery::ServiceAccepted));
    assert_eq!(page.messages[3].delivery, Some(Delivery::Failed));
    assert_eq!(
        page.messages[3].message_kind,
        Some(gchat_api::MessageKind::Notice)
    );
}
