use super::hex;
use gcoms::sdk::{MembershipRecoveryRequest, MembershipRecoveryStatus};

fn bytes<const N: usize>(text: &str) -> Result<[u8; N], String> {
    if text.len() != N * 2
        || !text
            .bytes()
            .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
    {
        return Err("Invalid recovery preview; open Channel recovery again".into());
    }
    let mut result = [0; N];
    for (i, v) in result.iter_mut().enumerate() {
        *v = u8::from_str_radix(&text[i * 2..i * 2 + 2], 16)
            .map_err(|_| "Invalid recovery identifier")?;
    }
    Ok(result)
}

pub(super) fn parse(args: &str) -> Result<MembershipRecoveryRequest, String> {
    let mut words = args.split_whitespace();
    let token = words.next().ok_or("Missing recovery preview")?;
    let fields: Vec<_> = token.split('.').collect();
    if fields.len() != 4 {
        return Err("Invalid recovery preview".into());
    }
    let remove_members = words.map(bytes).collect::<Result<Vec<_>, _>>()?;
    if remove_members.is_empty() || remove_members.len() > 128 {
        return Err("Select between 1 and 128 members".into());
    }
    Ok(MembershipRecoveryRequest {
        channel_id: bytes(fields[0])?,
        epoch: fields[1].parse().map_err(|_| "Invalid recovery epoch")?,
        pending_commit: if fields[2] == "-" {
            None
        } else {
            Some(bytes(fields[2])?)
        },
        revision: bytes(fields[3])?,
        remove_members,
    })
}

pub(super) fn output(channel: &str, status: MembershipRecoveryStatus) -> gchat_api::CommandOutput {
    let expected = format!(
        "{}.{}.{}.{}",
        hex(&status.channel_id),
        status.epoch,
        status
            .pending_commit
            .map(|id| hex(&id))
            .unwrap_or_else(|| "-".into()),
        hex(&status.revision)
    );
    gchat_api::CommandOutput::MembershipRecovery {
        channel: channel.into(),
        expected,
        epoch: status.epoch.to_string(),
        pending: status.pending_commit.is_some(),
        retained_messages: status.retained_messages,
        members: status
            .members
            .into_iter()
            .map(|m| gchat_api::RecoveryMember {
                id: hex(&m.member_id),
                nickname: m.display_name,
                is_self: m.is_self,
                missing_commit: m.missing_commit,
                pending_messages: m.pending_messages,
            })
            .collect(),
    }
}

// Keep saved operations readable by already-installed views and rollback
// daemons. Only the requesting updated client receives the new typed preview.
pub(super) fn retained_response(response: &gchat_api::Response) -> gchat_api::Response {
    use gchat_api::{CommandOutput, Response};
    let Response::Output {
        conversation,
        output:
            CommandOutput::MembershipRecovery {
                channel,
                epoch,
                pending,
                retained_messages,
                members,
                ..
            },
    } = response
    else {
        return response.clone();
    };
    Response::Output {
        conversation: conversation.clone(),
        output: CommandOutput::Text {
            title: format!("Membership recovery: #{channel}"),
            text: format!("Observed epoch {epoch}; {} members; membership acknowledgements pending: {pending}; {retained_messages} retained messages. Revocation is not message delivery. Use /recover-membership for a fresh preview.", members.len()),
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn recovery_preview_roundtrip_and_bounded_validation() {
        let status = MembershipRecoveryStatus {
            channel_id: [1; 32],
            epoch: u64::MAX,
            pending_commit: Some([2; 16]),
            revision: [3; 32],
            members: vec![],
            retained_messages: 2,
        };
        let gchat_api::CommandOutput::MembershipRecovery { expected, .. } = output("test", status)
        else {
            panic!("wrong output")
        };
        let request = parse(&format!("{expected} {}", hex(&[4; 32]))).unwrap();
        assert_eq!(request.epoch, u64::MAX);
        assert_eq!(request.remove_members, vec![[4; 32]]);
        assert!(parse(&expected).is_err());
        assert!(parse("wrong x").is_err());
        assert!(parse(&format!("{expected} {}", "é".repeat(32))).is_err());
        assert!(parse(&format!(
            "{expected} {}",
            vec![hex(&[4; 32]); 129].join(" ")
        ))
        .is_err());
    }

    #[test]
    fn retained_recovery_response_uses_the_existing_text_contract() {
        let response = gchat_api::Response::Output {
            conversation: Some("channel/test".into()),
            output: output(
                "test",
                MembershipRecoveryStatus {
                    channel_id: [1; 32],
                    epoch: 3,
                    pending_commit: None,
                    revision: [3; 32],
                    members: vec![],
                    retained_messages: 2,
                },
            ),
        };
        let retained = retained_response(&response);
        let value = serde_json::to_value(&retained).unwrap();
        assert_eq!(value["kind"], "output");
        assert_eq!(value["output"]["kind"], "text");
        assert!(value["output"].get("expected").is_none());
        assert_eq!(
            value,
            serde_json::to_value(retained_response(&retained)).unwrap()
        );
        let error = gchat_api::Response::Error {
            code: "outcome_unknown".into(),
            message: "save failed".into(),
        };
        assert_eq!(
            serde_json::to_value(retained_response(&error)).unwrap(),
            serde_json::to_value(error).unwrap()
        );
    }

    #[tokio::test(flavor = "multi_thread", worker_threads = 2)]
    async fn membership_recovery_invitation_delivery_kick_and_reopen() {
        use crate::chat_service::*;
        use gcoms::sdk::{ChannelStatus, ChannelVisibility, ClientEvent};
        let home = tempfile::tempdir().unwrap();
        crate::private_fs::make_private(home.path(), true).unwrap();
        async fn runtime(path: &std::path::Path) -> ProtocolRuntime {
            ProtocolRuntime::create_fixture(
                path,
                "disposable-recovery",
                "127.0.0.1:0".parse().unwrap(),
                None,
                None,
                &[],
            )
            .await
            .unwrap()
        }
        async fn submit(service: &ChatService, channel: Option<&str>, text: &str) -> Response {
            service
                .handle(Request::Submit {
                    operation_id: uuid::Uuid::new_v4().to_string(),
                    conversation: channel.map(str::to_owned),
                    text: text.into(),
                })
                .await
                .unwrap()
        }
        async fn ack(
            events: &mut tokio::sync::mpsc::Receiver<ClientEvent>,
            expected: Option<gcoms::sdk::MessageId>,
        ) {
            tokio::time::timeout(Duration::from_secs(30), async {
                loop {
                    if let ClientEvent::ChannelDelivered { message_id, .. } =
                        events.recv().await.unwrap()
                    {
                        if expected.is_none_or(|id| id == message_id) {
                            break;
                        }
                    }
                }
            })
            .await
            .expect("authenticated message ACK");
        }
        let owner_runtime = runtime(&home.path().join("owner")).await;
        let service = ChatService::new(
            home.path().join("archive"),
            owner_runtime.clone(),
            vec![
                Capability::IdentityRead,
                Capability::ChannelMember,
                Capability::ChannelAdmin,
                Capability::EventRead,
            ],
        )
        .unwrap();
        service
            .handle(Request::Unlock {
                passphrase: "disposable-recovery".into(),
                create: true,
            })
            .await
            .unwrap();
        let Response::Applied {
            conversation: Some(channel),
            ..
        } = submit(&service, None, "/create #recovery owner").await
        else {
            panic!("create")
        };
        let owner = owner_runtime.sdk_client();
        let first_runtime = runtime(&home.path().join("first")).await;
        let first = first_runtime.sdk_client();
        let join = first.prepare_channel_join("stale-first").await.unwrap();
        let kp = first.channel_key_package(join).await.unwrap();
        let mut owner_events = owner.subscribe_events();
        let welcome = owner
            .admit_channel("recovery", &kp, "stale-first")
            .await
            .unwrap();
        first
            .join_channel(join, "recovery", ChannelVisibility::Private, &welcome)
            .await
            .unwrap();
        ack(&mut owner_events, None).await;
        let next = first.prepare_channel_join("stale-second").await.unwrap();
        let next_package = first.channel_key_package(next).await.unwrap();
        drop(first);
        first_runtime.shutdown().await.unwrap();
        // The old leaf is offline at epoch 1 while the owner's durable commit
        // adds the second leaf at epoch 2. No ACK or force-clear shortcut.
        owner
            .admit_channel("recovery", &next_package, "stale-second")
            .await
            .unwrap();
        assert_eq!(
            owner.list_channels().await.unwrap()[0].status,
            ChannelStatus::MembershipPending
        );
        let Response::Output {
            output:
                gchat_api::CommandOutput::MembershipRecovery {
                    expected, members, ..
                },
            ..
        } = submit(&service, Some(&channel), "/recover-membership").await
        else {
            panic!("preview")
        };
        assert_eq!(members.len(), 3);
        let ids = members
            .iter()
            .filter(|m| !m.is_self)
            .map(|m| m.id.clone())
            .collect::<Vec<_>>()
            .join(" ");
        let command = format!("/recover-membership {expected} {ids}");
        for _ in 0..2 {
            let Response::Output {
                output:
                    gchat_api::CommandOutput::MembershipRecovery {
                        members,
                        pending,
                        epoch,
                        ..
                    },
                ..
            } = submit(&service, Some(&channel), &command).await
            else {
                panic!("recover")
            };
            assert_eq!(members.len(), 1);
            assert!(!pending);
            assert_eq!(epoch, "3");
        }
        assert!(matches!(
            submit(&service, Some(&channel), "owner-only after recovery").await,
            Response::Applied { .. }
        ));
        // Saved responses must remain readable by pre-recovery clients and
        // daemons. They must not persist the newly added enum discriminator.
        let snapshot = service.snapshot().await.unwrap();
        for op in snapshot.operations.unwrap() {
            if op.action == "/recover-membership" {
                assert!(matches!(
                    op.output,
                    Some(gchat_api::CommandOutput::Text { .. })
                ));
            }
        }
        let session = service.session.lock().await;
        let encoded = serde_json::to_string(&session.as_ref().unwrap().state).unwrap();
        assert!(!encoded.contains("membership_recovery"));
        drop(session);
        // Use the real single-use invitation API and remote redemption, as a
        // third-party SDK consumer does; the old KeyPackage is never reused.
        let replacement_runtime = runtime(&home.path().join("replacement")).await;
        let replacement = replacement_runtime.sdk_client();
        let invitation = owner
            .create_channel_invitation("recovery", 300)
            .await
            .unwrap();
        replacement
            .join_channel_invitation(&invitation.link, "replacement", 60)
            .await
            .unwrap();
        ack(&mut owner_events, None).await;
        let mut received = replacement.subscribe_events();
        let id = owner
            .send_channel_tracked("recovery", b"after recovery with ACK")
            .await
            .unwrap();
        tokio::time::timeout(Duration::from_secs(30), async {
            loop {
                if let ClientEvent::ChannelMessage {
                    message_id, body, ..
                } = received.recv().await.unwrap()
                {
                    if message_id == id {
                        assert_eq!(body, b"after recovery with ACK");
                        break;
                    }
                }
            }
        })
        .await
        .expect("replacement received exact message");
        ack(&mut owner_events, Some(id)).await;
        assert!(
            replacement
                .channel_recovery("recovery", None)
                .await
                .is_err(),
            "member cannot use owner recovery"
        );
        submit(&service, Some(&channel), "/refresh").await;
        assert!(matches!(
            submit(&service, Some(&channel), "/kick replacement").await,
            Response::Applied { .. }
        ));
        assert_eq!(
            owner
                .channel_recovery("recovery", None)
                .await
                .unwrap()
                .members
                .len(),
            1
        );
        drop(replacement);
        replacement_runtime.shutdown().await.unwrap();
        service.disconnect().await.unwrap();
        drop(service);
        drop(owner);
        owner_runtime.shutdown().await.unwrap();
        let restored = ProtocolRuntime::unlock_fixture(
            &home.path().join("owner"),
            "disposable-recovery",
            "127.0.0.1:0".parse().unwrap(),
            None,
            None,
            &[],
        )
        .await
        .unwrap();
        let status = restored
            .sdk_client()
            .channel_recovery("recovery", None)
            .await
            .unwrap();
        assert_eq!(status.members.len(), 1);
        assert!(status.pending_commit.is_none());
        restored
            .sdk_client()
            .send_channel("recovery", b"after reopen")
            .await
            .unwrap();
        restored.shutdown().await.unwrap();
    }
}
