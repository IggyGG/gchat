//! Focused invitation controls shared by desktop, mobile and the TUI.
use super::*;
use gcoms::sdk::{
    EnrollmentStatus, InvitationPolicy, InvitationPreset, InvitationReply, InvitationRequest,
};

pub(super) fn id(value: &str) -> Result<[u8; 16], String> {
    if value.len() != 32 || !value.bytes().all(|b| b.is_ascii_hexdigit()) {
        return Err("Use the invitation or enrollment ID shown in its details".into());
    }
    let mut bytes = [0; 16];
    for (index, byte) in bytes.iter_mut().enumerate() {
        *byte =
            u8::from_str_radix(&value[index * 2..index * 2 + 2], 16).map_err(|_| "Invalid ID")?;
    }
    Ok(bytes)
}
pub(super) fn policy(args: &str, now: u64) -> Result<InvitationPolicy, String> {
    let words = args.split_whitespace().collect::<Vec<_>>();
    match words.as_slice() {
        ["person"] => InvitationPreset::OnePerson.policy(now),
        ["friends"] => InvitationPreset::Friends.policy(now),
        ["devices"] => InvitationPreset::Devices.policy(now),
        ["custom", days, count] => {
            let expires_at = if *days == "never" {
                None
            } else {
                let days = days
                    .parse::<u64>()
                    .map_err(|_| "Use a positive number of days or never")?;
                if days == 0 {
                    return Err("Use at least one day, or explicitly choose never".into());
                }
                Some(
                    now.checked_add(days.checked_mul(86400).ok_or("Lifetime is too large")?)
                        .ok_or("Lifetime is too large")?,
                )
            };
            let max_admissions = if *count == "unlimited" {
                None
            } else {
                Some(
                    count
                        .parse::<u64>()
                        .map_err(|_| "Use a positive admission limit or unlimited")?,
                )
            };
            let policy = InvitationPolicy {
                expires_at,
                max_admissions,
            };
            policy.validate_new(now)?;
            Ok(policy)
        }
        _ => Err(
            "Use /invite person|friends|devices, or /invite custom days|never count|unlimited"
                .into(),
        ),
    }
}
pub(super) fn enrollment(status: EnrollmentStatus) -> gchat_api::CommandOutput {
    gchat_api::CommandOutput::Enrollment {
        id: hex(&status.id),
        channel: status.channel,
        phase: serde_json::to_value(status.phase)
            .expect("phase")
            .as_str()
            .expect("string phase")
            .into(),
        attempts: status.attempts,
        message: status.last_error,
    }
}

/// Keep the ordinary operation journal readable by older views and avoid a
/// second retained copy of the bearer credential. The admission ledger and
/// /enrollments remain the authoritative resumable state.
pub(super) fn retained_response(response: &Response) -> Response {
    use gchat_api::CommandOutput;
    let Response::Output {
        conversation,
        output,
    } = response
    else {
        return response.clone();
    };
    let (title, text) = match output {
        CommandOutput::InvitationOptions { .. } => (
            "Channel invitations",
            "Use /invite to choose an invitation policy.".into(),
        ),
        CommandOutput::ReusableInvitation { id, .. } => (
            "Invitation created",
            format!("Invitation {id}. Use /invites to share or revoke it."),
        ),
        CommandOutput::Invitations { .. } => (
            "Channel invitations",
            "Use /invites for current admission counts and controls.".into(),
        ),
        CommandOutput::Enrollment { id, phase, .. } => (
            "Saved channel join",
            format!(
                "Request {id}; observed state: {phase}. Use /enrollments for current progress."
            ),
        ),
        CommandOutput::Enrollments { .. } => (
            "Saved channel joins",
            "Use /enrollments for current progress and controls.".into(),
        ),
        _ => return super::membership_recovery::retained_response(response),
    };
    Response::Output {
        conversation: conversation.clone(),
        output: CommandOutput::Text {
            title: title.into(),
            text,
        },
    }
}
impl ChatService {
    pub(super) async fn enrollment_request(
        &self,
        code: &str,
        action: &str,
    ) -> Result<Response, String> {
        self.require(Capability::ChannelMember)?;
        let client = {
            let session = self.session.lock().await;
            session
                .as_ref()
                .filter(|s| !s.ui_locked)
                .ok_or("Unlock your profile first")?
                .client
                .clone()
        };
        let id = id(code)?;
        let request = match action {
            "status" => InvitationRequest::EnrollmentStatus { id },
            "resume" => InvitationRequest::ResumeEnrollment { id },
            "cancel" => InvitationRequest::CancelEnrollment { id },
            "retire" => InvitationRequest::RetireEnrollment { id },
            _ => return Err("Unknown enrollment action".into()),
        };
        match self
            .runtime
            .sdk_client()
            .invitations(request)
            .await
            .map_err(|e| e.to_string())?
        {
            InvitationReply::Enrollment(status) => {
                if status.phase == gcoms::sdk::EnrollmentPhase::Joined {
                    client.reconcile_channels().await?;
                    self.invalidate();
                }
                Ok(Response::Output {
                    conversation: None,
                    output: enrollment(status),
                })
            }
            InvitationReply::Retired => Ok(Response::Applied {
                conversation: None,
                notice: Some(
                    "Completed enrollment removed from the list; membership is unchanged.".into(),
                ),
            }),
            _ => Err("Unexpected enrollment response".into()),
        }
    }
    pub(super) async fn invitation_command(
        &self,
        channel: &ChannelRecord,
        name: &str,
        args: &str,
        conversation: Option<&str>,
    ) -> Result<Response, String> {
        self.require(Capability::ChannelAdmin)?;
        if channel.role != ChannelRole::Owner {
            return Err("Only the channel owner can manage invitations".into());
        }
        use gchat_api::CommandOutput;
        let output = if name == "invite" && args.is_empty() {
            CommandOutput::InvitationOptions {
                channel: channel.title.clone(),
            }
        } else {
            let request = match name {
                "invite" => InvitationRequest::Create {
                    channel: channel.protocol_name.clone(),
                    policy: policy(args, now())?,
                },
                "share-invite" => InvitationRequest::Share {
                    channel: channel.protocol_name.clone(),
                    id: id(args)?,
                },
                "revoke-invite" => InvitationRequest::Revoke {
                    channel: channel.protocol_name.clone(),
                    id: id(args)?,
                },
                "retire-invite" => InvitationRequest::Retire {
                    channel: channel.protocol_name.clone(),
                    id: id(args)?,
                },
                "invites" => InvitationRequest::List {
                    channel: channel.protocol_name.clone(),
                },
                _ => return Err("Unknown invitation command".into()),
            };
            let mut reply = self
                .runtime
                .sdk_client()
                .invitations(request)
                .await
                .map_err(|e| e.to_string())?;
            if matches!(
                reply,
                InvitationReply::Revoked(_) | InvitationReply::Retired
            ) {
                reply = self
                    .runtime
                    .sdk_client()
                    .invitations(InvitationRequest::List {
                        channel: channel.protocol_name.clone(),
                    })
                    .await
                    .map_err(|e| e.to_string())?;
            }
            match reply {
                InvitationReply::Created(value) => CommandOutput::ReusableInvitation {
                    channel: channel.title.clone(),
                    link: value.link,
                    id: hex(&value.id),
                    expires: value.policy.expires_at,
                    limit: value.policy.max_admissions,
                    local_only: value.local_only,
                },
                InvitationReply::Listed(records) => CommandOutput::Invitations {
                    channel: channel.title.clone(),
                    records: records
                        .into_iter()
                        .map(|r| gchat_api::InvitationRecord {
                            id: hex(&r.id),
                            expires: r.policy.expires_at,
                            limit: r.policy.max_admissions,
                            admitted: r.admissions,
                            pending: r.pending,
                            revoked: r.revoked_at.is_some(),
                        })
                        .collect(),
                },
                _ => return Err("Unexpected invitation response".into()),
            }
        };
        Ok(Response::Output {
            conversation: conversation.map(str::to_owned),
            output,
        })
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn invitation_receipts_keep_bearers_out_of_the_compatible_operation_journal() {
        let response = Response::Output {
            conversation: Some("channel/test".into()),
            output: gchat_api::CommandOutput::ReusableInvitation {
                channel: "friends".into(),
                link: "private-invitation-secret".into(),
                id: "0123".into(),
                expires: None,
                limit: Some(25),
                local_only: true,
            },
        };
        let retained = retained_response(&response);
        let json = serde_json::to_string(&retained).unwrap();
        assert!(!json.contains("private-invitation-secret"));
        assert!(!json.contains("reusable_invitation"));
        assert!(json.contains("/invites"));
        assert_eq!(
            serde_json::to_string(&retained_response(&retained)).unwrap(),
            json
        );
        assert!(matches!(
            response,
            Response::Output {
                output: gchat_api::CommandOutput::ReusableInvitation { .. },
                ..
            }
        ));
    }
    #[test]
    fn custom_bounds_are_independent_explicit_and_overflow_checked() {
        assert_eq!(policy("friends", 100).unwrap().max_admissions, Some(25));
        assert_eq!(
            policy("custom never 1", 100).unwrap(),
            InvitationPolicy {
                expires_at: None,
                max_admissions: Some(1)
            }
        );
        assert_eq!(
            policy("custom 7 unlimited", 100).unwrap(),
            InvitationPolicy {
                expires_at: Some(604900),
                max_admissions: None
            }
        );
        for bad in [
            "",
            "unlimited",
            "custom 0 1",
            "custom never 0",
            "custom 18446744073709551615 1",
            "friends extra",
        ] {
            assert!(policy(bad, 100).is_err(), "{bad}");
        }
        assert!(id(&"a".repeat(32)).is_ok());
        assert!(id(&"é".repeat(16)).is_err());
    }
}
