//! Hosted channel commands and encrypted archive projection shared by every UI.
use super::*;
use gcoms::sdk::hosted_client as h;

#[derive(Clone, PartialEq, Eq, Serialize, Deserialize)]
pub(super) struct Archive {
    channel: h::Channel,
    cursor: u64,
    messages: Vec<Message>,
    #[serde(default)]
    files: BTreeMap<String, h::Content>,
    #[serde(default)]
    operations: BTreeMap<String, String>,
    #[serde(default)]
    error: Option<String>,
    #[serde(default)]
    names: Vec<ObservedName>,
}
#[derive(Clone, PartialEq, Eq, Serialize, Deserialize)]
struct ObservedName {
    member: [u8; 32],
    nickname: String,
    observed_at: u64,
}
fn remember_queued(room: &mut Archive, id: [u8; 32], content: &h::Content, operation: &str) {
    let id = hex(&id);
    room.operations.insert(id.clone(), operation.into());
    let (kind, body) = match content {
        h::Content::Text(body) => (gchat_api::MessageKind::Text, body),
        h::Content::Action(body) => (gchat_api::MessageKind::Action, body),
        h::Content::Notice(body) => (gchat_api::MessageKind::Notice, body),
        _ => return,
    };
    if room.messages.iter().any(|message| message.id == id) {
        return;
    }
    room.messages.push(Message {
        highlighted: None,
        message_kind: Some(kind),
        id,
        conversation_id: key(room.channel.id),
        member_id: Some(hex(&room.channel.self_member)),
        nickname: observed_nickname(room, room.channel.self_member),
        body: body.clone(),
        timestamp: now(),
        mine: true,
        operation_id: Some(operation.into()),
        delivery: Some(gchat_api::Delivery::LocalAccepted),
        result: None,
    });
}
fn observe_name(room: &mut Archive, member: [u8; 32], nickname: &str, observed_at: u64) {
    if room
        .names
        .iter()
        .rev()
        .find(|n| n.member == member)
        .is_some_and(|n| n.nickname == nickname)
    {
        return;
    }
    room.names.push(ObservedName {
        member,
        nickname: nickname.into(),
        observed_at,
    });
    if room.names.len() > 2048 {
        room.names.remove(0);
    }
}
fn observed_nickname(room: &Archive, member: [u8; 32]) -> String {
    room.names
        .iter()
        .rev()
        .find(|n| n.member == member)
        .map(|n| n.nickname.clone())
        .or_else(|| {
            room.channel
                .members
                .iter()
                .find(|m| m.id == member)
                .map(|m| m.nickname.clone())
        })
        .unwrap_or_else(|| format!("member-{}", &hex(&member)[..8]))
}
fn whowas(room: &Archive, query: &str) -> Result<String, String> {
    if query.is_empty() || query.len() > 128 {
        return Err("Usage: /whowas nickname-or-scoped-id".into());
    }
    let rows: Vec<_> = room
        .names
        .iter()
        .rev()
        .filter(|n| {
            n.nickname.eq_ignore_ascii_case(query) || hex(&n.member).eq_ignore_ascii_case(query)
        })
        .take(64)
        .map(|n| {
            format!(
                "{} · {} · {}",
                n.nickname,
                hex(&n.member),
                if n.observed_at == 0 {
                    "retained membership snapshot".into()
                } else {
                    let age = now().saturating_sub(n.observed_at);
                    if age < 60 {
                        "observed less than a minute ago".into()
                    } else if age < 3600 {
                        format!("observed {} minute(s) ago", age / 60)
                    } else if age < 86400 {
                        format!("observed {} hour(s) ago", age / 3600)
                    } else {
                        format!("observed {} day(s) ago", age / 86400)
                    }
                }
            )
        })
        .collect();
    Ok(if rows.is_empty() {
        "No matching name in this channel's retained observations.".into()
    } else {
        rows.join("\n")
    })
}
impl Archive {
    pub(super) fn file_channel(&self) -> [u8; 32] {
        self.channel.id
    }
    pub(super) fn active(&self) -> bool {
        self.channel.active
    }
}
pub(super) fn is_conversation(id: &str) -> bool {
    id.starts_with("hosted/")
}
fn key(id: [u8; 32]) -> String {
    format!("hosted/{}", hex(&id))
}
pub(super) fn global_command(text: &str) -> bool {
    preferences::handles(text)
        || text.eq_ignore_ascii_case("/contact")
        || matches!(
            text.to_ascii_lowercase().as_str(),
            "/network" | "/status" | "/create" | "/join" | "/lock" | "/quit" | "/disconnect"
        )
}
pub(super) fn handles(conversation: Option<&str>, text: &str) -> bool {
    let command = split_head(text).0;
    command.eq_ignore_ascii_case("/hosted")
        || (conversation.is_some_and(is_conversation) && !global_command(command))
}
pub(super) fn validate(conversation: Option<&str>, text: &str) -> Result<(), String> {
    if text.len() > 8192 {
        return Err("Hosted messages accept at most 8192 UTF-8 bytes".into());
    }
    if !text.starts_with('/') {
        return conversation
            .filter(|id| is_conversation(id))
            .map(|_| ())
            .ok_or_else(|| "Open a hosted channel first".into());
    }
    let name = split_head(text).0.to_ascii_lowercase();
    if name == "/hosted" || commands().iter().any(|c| c.name == name) {
        Ok(())
    } else {
        Err("Command unavailable in this hosted channel; use /help".into())
    }
}
pub(super) fn commands() -> Vec<gchat_api::CommandSpec> {
    [
        ("/help", "", "Show hosted channel commands"),
        ("/list", "[cursor]", "Browse explicitly published hosted channels"),
        ("/publish", "name|--remove", "Publish a public directory name, or withdraw it; the topic remains encrypted"),
        ("/say", "text", "Send literal text"), ("/me", "text", "Send an action"), ("/notice", "text", "Send a notice; notices never trigger automatic replies"),
        ("/topic", "[text|--clear]", "Read or change this channel's topic"), ("/nick", "nickname", "Change your channel nickname"),
        ("/mode", "[+o|-o|+v|-v|+b|-b|+e|-e|+I|-I member | +m|-m|+i|-i|+t|-t | +k|-k | +l number | private|secret|public]", "Inspect or change channel policy"),
        ("/invite", "[seconds]", "Create a single-use invitation; usable after its policy change is accepted"),
        ("/links", "", "Show retained invitation links"),
        ("/motd", "", "Show the service message of the day"),
        ("/rules", "", "Show service rules"),
        ("/admin", "", "Show the network operator contact"),
        ("/server-info", "", "Show the service profile and limits"),
        ("/kick", "member [reason]", "Remove a member and rotate encryption keys"), ("/owner", "member", "Transfer channel ownership"),
        ("/part", "[reason]", "Leave and retain history; owners first transfer or close"), ("/close-channel", "[reason]", "Close the channel for every member"),
        ("/away", "[reason]", "Opt in to away presence with an optional reason"), ("/back", "", "Opt in to available presence"), ("/presence", "on|off", "Share presence or become invisible; sharing defaults off"),
        ("/names", "", "List members, roles and channel-scoped identities"), ("/who", "", "List this channel's members"), ("/whois", "member", "Inspect a channel-scoped identity"),
        ("/whowas", "nickname-or-scoped-id", "Show retained names observed in this channel"),
        ("/ping", "", "Measure an authenticated service recovery round trip"), ("/refresh", "", "Recover accepted channel records"),
        ("/hide", "", "Hide this window and keep receiving"), ("/close", "", "Hide this window and keep receiving"),
    ].into_iter().map(|(name,args,description)| gchat_api::CommandSpec { name: name.into(), usage: format!("{name} {args}").trim().into(), description: description.into(), scope: "conversation".into(), capability: Some("HostedChannels".into()), available: true }).collect()
}
fn role_name(member: &h::Member) -> &str {
    if member.role == h::Role::Owner {
        "owner"
    } else if member.operator {
        "operator"
    } else if member.voice {
        "voice"
    } else {
        "member"
    }
}
pub(super) fn conversations(state: &UiState) -> Vec<Conversation> {
    state
        .hosted
        .iter()
        .map(|(id, archive)| {
            let channel = &archive.channel;
            let read = state
                .read
                .get(id)
                .and_then(|id| archive.messages.iter().position(|m| m.id == *id))
                .map_or(0, |n| n + 1);
            Conversation {
                muted: None,
                policy: Some(gchat_api::ChannelPolicy {
                    profile: "hosted-mls-pq-v1".into(),
                    capacity: channel.capacity,
                    moderated: channel.moderated,
                    invite_only: channel.invite_only,
                    topic_operators: channel.topic_operators,
                    presence_enabled: channel.presence_opt_in,
                }),
                provider: None,
                id: id.clone(),
                channel_id: hex(&channel.id),
                kind: if channel.active {
                    ConversationKind::Channel
                } else {
                    ConversationKind::Archive
                },
                name: format!("#{}", channel.alias.trim_start_matches('#')),
                topic: if channel.topic_pending {
                    "Topic pending".into()
                } else {
                    channel.topic.clone()
                },
                active: channel.active,
                owner: channel
                    .members
                    .iter()
                    .any(|m| m.id == channel.self_member && m.role == h::Role::Owner),
                visibility: Some(
                    match channel.discovery {
                        h::Discovery::Public => "public",
                        h::Discovery::Private => "private",
                        h::Discovery::Secret => "secret",
                    }
                    .into(),
                ),
                directory: None,
                members: channel
                    .members
                    .iter()
                    .map(|m| Member {
                        id: hex(&m.id),
                        nickname: m.nickname.clone(),
                        is_self: m.id == channel.self_member,
                        recently_active: None,
                        capabilities: vec![format!("channel.{}", role_name(m))],
                        presence: Some(match &m.presence {
                            h::Presence::Available => gchat_api::MemberPresence::Available,
                            h::Presence::Away { reason } => gchat_api::MemberPresence::Away {
                                reason: reason.clone(),
                            },
                            _ => gchat_api::MemberPresence::Unknown,
                        }),
                    })
                    .collect(),
                unread: archive.messages[read..]
                    .iter()
                    .filter(|m| {
                        !m.mine
                            && !state
                                .preferences
                                .ignores(id, m.member_id.as_deref(), m.mine)
                    })
                    .count()
                    .min(u32::MAX as usize) as u32,
                last_message_id: archive.messages.last().map(|m| m.id.clone()),
                input_limit_bytes: 8192,
                commands: commands(),
            }
        })
        .collect()
}
pub(super) fn history(
    room: &Archive,
    before: Option<&str>,
    limit: u16,
    search: Option<&str>,
) -> Result<Response, String> {
    let messages: Vec<_> = room
        .messages
        .iter()
        .filter(|m| {
            search.is_none_or(|q| {
                m.body.to_lowercase().contains(q) || m.nickname.to_lowercase().contains(q)
            })
        })
        .collect();
    let end = before
        .map(|id| {
            messages
                .iter()
                .position(|m| m.id == id)
                .ok_or("history cursor is not in this conversation")
        })
        .transpose()?
        .unwrap_or(messages.len());
    let start = end.saturating_sub(usize::from(limit.clamp(1, 200)));
    let page: Vec<_> = messages[start..end].iter().map(|m| (*m).clone()).collect();
    let before = if start > 0 {
        page.first().map(|m| m.id.clone())
    } else {
        None
    };
    Ok(Response::History {
        page: HistoryPage {
            messages: page,
            before,
        },
    })
}
pub(super) fn mark_read(
    current: &mut Unlocked,
    conversation: &str,
    message: &str,
) -> Result<(), String> {
    let room = current
        .state
        .hosted
        .get(conversation)
        .ok_or("Unknown hosted channel")?;
    let next = room
        .messages
        .iter()
        .position(|m| m.id == message)
        .ok_or("Unknown read marker")?;
    let old = current
        .state
        .read
        .get(conversation)
        .and_then(|id| room.messages.iter().position(|m| m.id == *id));
    if old.is_none_or(|index| next > index) {
        let mut candidate = current.state.clone();
        candidate.read.insert(conversation.into(), message.into());
        current.store.save(&candidate)?;
        current.state = candidate;
    }
    Ok(())
}
fn directory_cursor(value: &str) -> Result<[u8; 32], String> {
    if value.len() != 64 || !value.bytes().all(|b| b.is_ascii_hexdigit()) {
        return Err("Use the directory's next-page cursor".into());
    }
    let mut id = [0; 32];
    for (i, byte) in id.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&value[2 * i..2 * i + 2], 16)
            .map_err(|_| "Invalid directory cursor")?;
    }
    Ok(id)
}
fn member(channel: &h::Channel, query: &str) -> Result<[u8; 32], String> {
    if let Some(member) = channel.members.iter().find(|m| hex(&m.id) == query) {
        return Ok(member.id);
    }
    let matches: Vec<_> = channel
        .members
        .iter()
        .filter(|m| {
            m.nickname
                .eq_ignore_ascii_case(query.trim_start_matches('@'))
        })
        .collect();
    match matches.as_slice() {
        [m] => Ok(m.id),
        [] => Err("Member is not in this channel".into()),
        _ => Err("Nickname is ambiguous; use the scoped identity from /names".into()),
    }
}
fn scoped_identity(channel: &h::Channel, query: &str) -> Result<[u8; 32], String> {
    if query.len() == 64 && query.bytes().all(|b| b.is_ascii_hexdigit()) {
        let mut id = [0; 32];
        for (i, byte) in id.iter_mut().enumerate() {
            *byte = u8::from_str_radix(&query[i * 2..i * 2 + 2], 16)
                .map_err(|_| "Invalid scoped identity")?;
        }
        return Ok(id);
    }
    member(channel, query)
}
fn delivery(value: &h::Delivery) -> gchat_api::Delivery {
    match value {
        h::Delivery::Pending => gchat_api::Delivery::LocalAccepted,
        h::Delivery::ServiceAccepted { .. } => gchat_api::Delivery::ServiceAccepted,
        h::Delivery::Delivered => gchat_api::Delivery::Delivered,
        h::Delivery::Failed { .. } => gchat_api::Delivery::Failed,
    }
}
fn describe_change(change: &h::Change, name: &impl Fn([u8; 32]) -> String) -> String {
    let switch = |enabled: bool| if enabled { "enabled" } else { "disabled" };
    match change {
        h::Change::Mode(mode, on) => format!(
            "{} {}",
            switch(*on),
            match mode {
                h::Mode::Moderated => "moderated posting",
                h::Mode::InviteOnly => "invite-only admission",
                h::Mode::TopicOperators => "operator-only topics",
            }
        ),
        h::Change::Operator(id, on) => {
            format!("{} operator permission for {}", switch(*on), name(*id))
        }
        h::Change::Voice(id, on) => format!("{} voice for {}", switch(*on), name(*id)),
        h::Change::AccessList(list, id, on) => format!(
            "{} {} {} the {} list",
            if *on { "added" } else { "removed" },
            name(*id),
            if *on { "to" } else { "from" },
            match list {
                h::AccessList::Ban => "ban",
                h::AccessList::Exemption => "ban exemption",
                h::AccessList::InviteException => "invite exception",
            }
        ),
        h::Change::Listing(name) => {
            if name.is_empty() {
                "withdrew public directory publication".into()
            } else {
                format!("published the public directory name {name}")
            }
        }
        h::Change::Capacity(n) => format!("set capacity to {n}"),
        h::Change::Discovery(value) => format!(
            "made channel discovery {}",
            match value {
                h::Discovery::Public => "public",
                h::Discovery::Private => "private",
                h::Discovery::Secret => "secret",
            }
        ),
        h::Change::Transfer(id) => format!("transferred ownership to {}", name(*id)),
        h::Change::Kick(id) => format!("removed {}", name(*id)),
        h::Change::Leave => "left the channel".into(),
        h::Change::Close => "closed the channel".into(),
        h::Change::Role(id, role) => format!(
            "changed {}'s role to {}",
            name(*id),
            match role {
                h::Role::Owner => "owner",
                h::Role::Operator => "operator",
                h::Role::Voice => "voice",
                h::Role::Member => "member",
            }
        ),
        h::Change::Invitation { expires_at, .. } => {
            if *expires_at == 0 {
                "revoked an invitation".into()
            } else {
                "created a single-use invitation".into()
            }
        }
        h::Change::AccessCode { verifier } => {
            if verifier.is_some() {
                "rotated the reusable admission code".into()
            } else {
                "disabled the reusable admission code".into()
            }
        }
    }
}
fn apply(state: &mut UiState, channel: h::Channel, events: Vec<h::Event>) -> Result<u64, String> {
    let conversation = key(channel.id);
    let room = state
        .hosted
        .entry(conversation.clone())
        .or_insert_with(|| Archive {
            channel: channel.clone(),
            cursor: 0,
            messages: Vec::new(),
            files: BTreeMap::new(),
            operations: BTreeMap::new(),
            error: None,
            names: Vec::new(),
        });
    if room.names.is_empty() {
        // Older hosted archives already retain authenticated message authors.
        // Seed observations without copying message bodies or linking any room.
        let retained: Vec<_> = room
            .messages
            .iter()
            .filter_map(|message| {
                let member = directory_cursor(message.member_id.as_deref()?).ok()?;
                Some((member, message.nickname.clone(), message.timestamp))
            })
            .collect();
        for (member, nickname, at) in retained {
            observe_name(room, member, &nickname, at);
        }
        for member in room.channel.members.clone() {
            observe_name(room, member.id, &member.nickname, 0);
        }
    }
    room.channel = channel;
    for event in events {
        if event.channel != room.channel.id {
            return Err("Hosted event belongs to a different channel".into());
        }
        if event.sequence <= room.cursor {
            continue;
        }
        if event.sequence != room.cursor + 1 {
            return Err("Hosted archive event gap; refusing acknowledgement".into());
        }
        let nickname = |sender: [u8; 32]| observed_nickname(room, sender);
        let mut activity = None;
        match event.kind {
            h::EventKind::Message {
                id,
                sender,
                content,
                delivery: status,
            } => {
                let id = hex(&id);
                let (kind, body) = match content {
                    h::Content::Text(body) => (Some(gchat_api::MessageKind::Text), body),
                    h::Content::Action(body) => (Some(gchat_api::MessageKind::Action), body),
                    h::Content::Notice(body) => (Some(gchat_api::MessageKind::Notice), body),
                    h::Content::File { content_type, .. }
                        if content_type == gcoms::sdk::sharing_v2::COMPLETION_TYPE =>
                    {
                        (None, String::new())
                    }
                    content @ h::Content::File { .. } => {
                        room.files.insert(id.clone(), content);
                        (None, String::new())
                    }
                    h::Content::Topic(topic) => {
                        activity = Some((
                            "topic",
                            format!("{} set the topic: {topic}", nickname(sender)),
                        ));
                        (None, String::new())
                    }
                    h::Content::Nickname(name) => {
                        activity =
                            Some(("nickname", format!("{} is now {name}", nickname(sender))));
                        observe_name(room, sender, &name, event.accepted_at);
                        (None, String::new())
                    }
                    h::Content::Presence { .. } | h::Content::TopicState { .. } => {
                        (None, String::new())
                    }
                };
                if let Some(kind) = kind {
                    if !room.messages.iter().any(|m| m.id == id) {
                        room.messages.push(Message {
                            highlighted: None,
                            message_kind: Some(kind),
                            id: id.clone(),
                            conversation_id: conversation.clone(),
                            member_id: Some(hex(&sender)),
                            nickname: observed_nickname(room, sender),
                            body,
                            timestamp: event.accepted_at,
                            mine: sender == room.channel.self_member,
                            operation_id: room.operations.get(&id).cloned(),
                            delivery: (sender == room.channel.self_member)
                                .then(|| delivery(&status)),
                            result: None,
                        });
                    }
                }
            }
            h::EventKind::Delivery { id, state: status } => {
                if let Some(message) = room.messages.iter_mut().find(|m| m.id == hex(&id)) {
                    message.delivery = Some(delivery(&status));
                }
                if let h::Delivery::Failed { reason } = status {
                    activity = Some(("send_failed", reason));
                }
            }
            h::EventKind::Activity {
                actor,
                change,
                reason,
            } => {
                activity = Some((
                    "policy",
                    format!(
                        "{} ({}) {}{}",
                        nickname(actor),
                        hex(&actor),
                        describe_change(&change, &nickname),
                        reason.map_or_else(String::new, |r| format!(": {r}"))
                    ),
                ));
            }
            h::EventKind::Joined { member, nickname } => {
                observe_name(room, member, &nickname, event.accepted_at);
                activity = Some(("join", format!("{nickname} ({}) joined", hex(&member))));
            }
            h::EventKind::Removed => {
                activity = Some((
                    "removed",
                    "Your channel membership ended; history is retained".into(),
                ));
            }
            h::EventKind::Unavailable { sender, reason } => {
                activity = Some((
                    "unavailable",
                    format!("Message from {} unavailable: {reason}", nickname(sender)),
                ));
            }
            h::EventKind::OperationFailed { reason } => {
                activity = Some(("operation_failed", reason));
            }
        }
        if let Some((kind, text)) = activity {
            state.activity.push(gchat_api::Activity {
                id: format!("{conversation}/{}", event.sequence),
                conversation: conversation.clone(),
                kind: kind.into(),
                text,
                timestamp: event.accepted_at,
            });
        }
        room.cursor = event.sequence;
    }
    for message in &mut room.messages {
        if message.operation_id.is_none() {
            message.operation_id = room.operations.get(&message.id).cloned();
        }
    }
    if state.activity.len() > 2000 {
        state.activity.drain(..state.activity.len() - 2000);
    }
    Ok(room.cursor)
}
impl ChatService {
    async fn hosted_exchange(&self, request: h::Request) -> Result<h::Reply, String> {
        self.require(Capability::HostedChannels)?;
        self.runtime
            .sdk_client()
            .hosted_channels(request)
            .await
            .map_err(|e| e.to_string())
    }
    async fn archive_hosted(&self, channel: h::Channel, recovered: bool) -> Result<(), String> {
        let h::Reply::Events(events) = self
            .hosted_exchange(h::Request::Events {
                channel: channel.id,
                after: 0,
                limit: 256,
            })
            .await?
        else {
            return Err("Invalid hosted event reply".into());
        };
        let id = channel.id;
        let has_events = !events.is_empty();
        let through = {
            let mut session = self.session.lock().await;
            let current = session.as_mut().ok_or("Archive is closed")?;
            let mut candidate = current.state.clone();
            let through = apply(&mut candidate, channel, events)?;
            if recovered {
                candidate
                    .hosted
                    .get_mut(&key(id))
                    .expect("applied channel")
                    .error = None;
            }
            if candidate.hosted != current.state.hosted
                || candidate.activity != current.state.activity
            {
                current.store.save(&candidate)?;
                current.state = candidate;
            }
            through
        };
        self.invalidate();
        if through > 0 && has_events {
            self.hosted_exchange(h::Request::CommitEvents {
                channel: id,
                through,
            })
            .await?;
        }
        Ok(())
    }
    pub(super) fn spawn_hosted_worker(service: &Arc<Self>) -> tokio::task::JoinHandle<()> {
        let weak = Arc::downgrade(service);
        let mut stopped = service.stopped.subscribe();
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(1));
            interval.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
            loop {
                tokio::select! {_ = stopped.changed()=>break, _=interval.tick()=>{}}
                let Some(service) = weak.upgrade() else { break };
                if *stopped.borrow() {
                    break;
                }
                if !service.capabilities.contains(&Capability::HostedChannels)
                    || service.session.lock().await.is_none()
                {
                    continue;
                }
                let Ok(_update) = service.update_gate.enter() else {
                    continue;
                };
                let work = async {
                    let h::Reply::Channels(channels) =
                        service.hosted_exchange(h::Request::List).await?
                    else {
                        return Err("Invalid hosted listing".to_string());
                    };
                    for channel in channels {
                        let id = channel.id;
                        // Archive locally queued events even while service recovery is offline.
                        service.archive_hosted(channel, false).await?;
                        match service
                            .hosted_exchange(h::Request::Sync { channel: id })
                            .await
                        {
                            Ok(h::Reply::Channel(channel)) => {
                                service.archive_hosted(*channel, true).await?
                            }
                            Ok(_) => return Err("Invalid hosted sync reply".into()),
                            Err(error) => {
                                let mut session = service.session.lock().await;
                                if let Some(current) = session.as_mut() {
                                    if current
                                        .state
                                        .hosted
                                        .get(&key(id))
                                        .is_some_and(|r| r.error.as_ref() != Some(&error))
                                    {
                                        let mut candidate = current.state.clone();
                                        candidate
                                            .hosted
                                            .get_mut(&key(id))
                                            .expect("present")
                                            .error = Some(error);
                                        current.store.save(&candidate)?;
                                        current.state = candidate;
                                        service.invalidate();
                                    }
                                }
                            }
                        }
                    }
                    Ok::<_, String>(())
                };
                let result = tokio::select! {_ = stopped.changed()=>break, result = work=>result};
                let mut session = service.session.lock().await;
                if let Some(current) = session.as_mut() {
                    let error = result.err();
                    if current.hosted_error != error {
                        current.hosted_error = error;
                        service.invalidate();
                    }
                }
            }
        })
    }
    pub(super) async fn submit_hosted(
        &self,
        conversation: Option<&str>,
        text: &str,
        operation_id: &str,
    ) -> Result<Response, String> {
        let (command, args) = if let Some(command) = text.strip_prefix('/') {
            split_head(command)
        } else {
            ("say", text)
        };
        let output = |title: &str, text: String| {
            Ok(Response::Output {
                conversation: conversation.map(str::to_owned),
                output: gchat_api::CommandOutput::Text {
                    title: title.into(),
                    text,
                },
            })
        };
        let applied = || {
            Ok(Response::Applied {
                conversation: conversation.map(str::to_owned),
                notice: None,
            })
        };
        let browse_args = if command.eq_ignore_ascii_case("list") {
            Some(args)
        } else if command.eq_ignore_ascii_case("hosted")
            && split_head(args).0.eq_ignore_ascii_case("list")
        {
            Some(split_head(args).1)
        } else {
            None
        };
        if let Some(cursor) = browse_args {
            let target = self
                .runtime
                .network_client()
                .ok_or("Hosted discovery requires an installed network")?
                .hosted_endpoints()
                .map_err(|e| e.to_string())?
                .into_iter()
                .next()
                .ok_or("Network has no hosted endpoint")?;
            let after = if cursor.is_empty() {
                None
            } else {
                Some(directory_cursor(cursor)?)
            };
            let h::Reply::Directory { entries, next } = self
                .hosted_exchange(h::Request::Directory {
                    endpoint: target,
                    after,
                    limit: 16,
                })
                .await?
            else {
                return Err("Invalid hosted directory reply".into());
            };
            let mut lines = entries
                .into_iter()
                .map(|entry| match entry.link {
                    Some(link) => format!(
                        "{} [{}] · {}/{} members\n/hosted join {} {} nickname",
                        entry.name,
                        hex(&entry.channel),
                        entry.members,
                        entry.capacity,
                        link.0,
                        entry.name
                    ),
                    None => format!(
                        "{} [{}] · {}/{} members · invitation required",
                        entry.name,
                        hex(&entry.channel),
                        entry.members,
                        entry.capacity
                    ),
                })
                .collect::<Vec<_>>();
            if lines.is_empty() {
                lines.push("No public hosted channels on this page.".into());
            }
            if let Some(next) = next {
                lines.push(format!("Next page: /hosted list {}", hex(&next)));
            }
            return output("Public hosted channels", lines.join("\n\n"));
        }
        if command.eq_ignore_ascii_case("hosted") {
            let (verb, args) = split_head(args);
            let request=match verb {
                "create"=>{
                    let parts:Vec<_>=args.split_whitespace().collect(); if !(2..=3).contains(&parts.len()){return Err("Usage: /hosted create #name nickname [private|public|code]".into())}
                    let target=self.runtime.network_client().ok_or("Hosted creation requires an installed network")?.hosted_endpoints().map_err(|e|e.to_string())?.into_iter().next().ok_or("Network has no hosted endpoint")?;
                    let admission=match parts.get(2).copied().unwrap_or("private"){"private"=>h::Admission::InviteOnly,"public"=>h::Admission::Public,"code"=>h::Admission::ReusableCode,_=>return Err("Choose private, public or code admission".into())};
                    h::Request::Create{endpoint:target,alias:parts[0].trim_start_matches('#').into(),nickname:parts[1].into(),capacity:500,admission}
                }
                "join"=>{let parts:Vec<_>=args.split_whitespace().collect(); if parts.len()!=3{return Err("Usage: /hosted join link #alias nickname".into())} h::Request::Join{link:h::InviteLink(parts[0].into()),alias:parts[1].trim_start_matches('#').into(),nickname:parts[2].into()} }
                _=>return Err("Usage: /hosted list [cursor] | /hosted create #name nickname [private|public|code] | /hosted join link #alias nickname".into()),
            };
            let h::Reply::Channel(channel) = self.hosted_exchange(request).await? else {
                return Err("Invalid hosted admission reply".into());
            };
            let id = key(channel.id);
            self.archive_hosted(*channel, false).await?;
            return Ok(Response::Applied {
                conversation: Some(id),
                notice: Some(
                    "Channel admission queued. It becomes active after the service accepts it."
                        .into(),
                ),
            });
        }
        let conversation = conversation.ok_or("Open a hosted channel")?;
        let channel = {
            let session = self.session.lock().await;
            session
                .as_ref()
                .filter(|s| !s.ui_locked)
                .and_then(|s| s.state.hosted.get(conversation))
                .ok_or("Hosted channel is unavailable")?
                .channel
                .clone()
        };
        let id = channel.id;
        let content = match command.to_ascii_lowercase().as_str() {
            "say" => Some(h::Content::Text(args.into())),
            "me" => Some(h::Content::Action(args.into())),
            "notice" => Some(h::Content::Notice(args.into())),
            "nick" => Some(h::Content::Nickname(args.into())),
            "topic" if !args.is_empty() => Some(h::Content::Topic(if args == "--clear" {
                String::new()
            } else {
                args.into()
            })),
            _ => None,
        };
        if let Some(content) = content {
            let h::Reply::Queued(message) = self
                .hosted_exchange(h::Request::Send {
                    channel: id,
                    content: content.clone(),
                })
                .await?
            else {
                return Err("Invalid queued message reply".into());
            };
            let mut session = self.session.lock().await;
            let current = session.as_mut().ok_or("Archive is closed")?;
            let mut candidate = current.state.clone();
            let room = candidate
                .hosted
                .get_mut(conversation)
                .ok_or("Unknown channel")?;
            remember_queued(room, message, &content, operation_id);
            current.store.save(&candidate)?;
            current.state = candidate;
            return applied();
        }
        let change = match command.to_ascii_lowercase().as_str() {
            "help" => {
                return Ok(Response::Output {
                    conversation: Some(conversation.into()),
                    output: gchat_api::CommandOutput::Help {
                        commands: self.context_commands(Some(conversation)),
                    },
                })
            }
            "motd" | "rules" | "admin" | "server-info" => {
                use gcoms::sdk::hosted as wire;
                let reply = self
                    .runtime
                    .sdk_client()
                    .hosted_request(
                        &channel.endpoint,
                        wire::Request {
                            version: wire::VERSION,
                            channel: id,
                            operation: wire::Operation::Info,
                        },
                    )
                    .await
                    .map_err(|e| e.to_string())?;
                let wire::Reply::Info(info) = reply else {
                    return Err("Service information is unavailable".into());
                };
                return match command.to_ascii_lowercase().as_str() {
                    "motd" => output("Message of the day", info.motd),
                    "rules" => output("Service rules", info.rules),
                    "admin" => output("Network operator", info.operator_contact),
                    _ => output("Service information", format!("Profiles: {}\nExtensions: {}\nMaximum members: {}\nMaximum page records: {}\nMaximum request bytes: {}\nPublic creation: {}\nService requests/second: {}\nSource requests/second: {}", info.profiles.join(", "), info.extensions.join(", "), info.max_members, info.max_page_records, info.max_http_bytes, info.public_creation, info.requests_per_second.map_or_else(|| "not advertised".into(), |n| n.to_string()), info.source_requests_per_second.map_or_else(|| "not advertised".into(), |n| n.to_string()))),
                };
            }
            "topic" => {
                return output(
                    "Topic",
                    if channel.topic_pending {
                        "Topic pending — waiting for an authorized member to provide it.".into()
                    } else {
                        channel.topic
                    },
                )
            }
            "names" | "who" => {
                return output(
                    "Channel members",
                    channel
                        .members
                        .iter()
                        .map(|m| format!("{} [{}] {}", m.nickname, role_name(m), hex(&m.id)))
                        .collect::<Vec<_>>()
                        .join("\n"),
                )
            }
            "whowas" => {
                let session = self.session.lock().await;
                let room = session
                    .as_ref()
                    .filter(|s| !s.ui_locked)
                    .and_then(|s| s.state.hosted.get(conversation))
                    .ok_or("Hosted channel is unavailable")?;
                return output("Names observed in this channel", whowas(room, args)?);
            }
            "whois" => {
                let id = member(&channel, args)?;
                let m = channel
                    .members
                    .iter()
                    .find(|m| m.id == id)
                    .expect("resolved");
                return output(
                    "Channel identity",
                    format!(
                        "{}\n{}\nRole: {}\nPresence: {}",
                        m.nickname,
                        hex(&id),
                        role_name(m),
                        match &m.presence {
                            h::Presence::Available => "Available".into(),
                            h::Presence::Away { reason } if reason.is_empty() => "Away".into(),
                            h::Presence::Away { reason } => format!("Away: {reason}"),
                            h::Presence::Unknown => "Unknown".into(),
                            h::Presence::Invisible => "Unknown".into(),
                        }
                    ),
                );
            }
            "hide" | "close" => {
                return Ok(Response::Output {
                    conversation: Some(conversation.into()),
                    output: gchat_api::CommandOutput::Close {
                        conversation: conversation.into(),
                    },
                })
            }
            "ping" | "refresh" => {
                let start = Instant::now();
                let h::Reply::Channel(channel) = self
                    .hosted_exchange(h::Request::Sync { channel: id })
                    .await?
                else {
                    return Err("Invalid hosted sync reply".into());
                };
                self.archive_hosted(*channel, true).await?;
                return output(
                    "Channel recovery",
                    format!("Completed in {} ms", start.elapsed().as_millis()),
                );
            }
            "away" | "back" | "presence" => {
                let (enabled, state) = match command.to_ascii_lowercase().as_str() {
                    "away" => (
                        true,
                        h::Presence::Away {
                            reason: args.into(),
                        },
                    ),
                    "back" => (true, h::Presence::Available),
                    _ => match args {
                        "on" => (true, h::Presence::Available),
                        "off" => (false, h::Presence::Invisible),
                        _ => return Err("Usage: /presence on|off".into()),
                    },
                };
                self.hosted_exchange(h::Request::SetPresence {
                    channel: id,
                    enabled,
                    state,
                })
                .await?;
                return applied();
            }
            "invite" => {
                let ttl_secs = if args.is_empty() {
                    86400
                } else {
                    args.parse()
                        .map_err(|_| "Invitation lifetime must be seconds")?
                };
                let h::Reply::Link(link) = self
                    .hosted_exchange(h::Request::Invite {
                        channel: id,
                        ttl_secs,
                    })
                    .await?
                else {
                    return Err("Invalid invitation reply".into());
                };
                return output("Invitation queued",format!("Usable after the policy change is accepted. Share privately:\n/hosted join {} #{} nickname",link.0,channel.alias));
            }
            "links" => {
                let h::Reply::Links(links) = self
                    .hosted_exchange(h::Request::Links { channel: id })
                    .await?
                else {
                    return Err("Invalid links reply".into());
                };
                return output(
                    "Retained invitation links",
                    links
                        .iter()
                        .map(|l| format!("/hosted join {} #{} nickname", l.0, channel.alias))
                        .collect::<Vec<_>>()
                        .join("\n"),
                );
            }
            "kick" => {
                let (who, reason) = split_head(args);
                (h::Change::Kick(member(&channel, who)?), reason)
            }
            "owner" => (h::Change::Transfer(member(&channel, args)?), ""),
            "part" => (h::Change::Leave, args),
            "close-channel" => (h::Change::Close, args),
            "publish" => (
                h::Change::Listing(if args == "--remove" {
                    String::new()
                } else {
                    if args.is_empty() {
                        return Err("Usage: /publish name|--remove".into());
                    }
                    args.into()
                }),
                "",
            ),
            "mode" => {
                if args.is_empty() {
                    return output(
                        "Channel modes",
                        format!(
                            "{}{}{} +l {} {:?}",
                            if channel.moderated { "+m" } else { "-m" },
                            if channel.invite_only { " +i" } else { " -i" },
                            if channel.topic_operators {
                                " +t"
                            } else {
                                " -t"
                            },
                            channel.capacity,
                            channel.discovery
                        ),
                    );
                }
                let (mode, value) = split_head(args);
                if value.is_empty() && matches!(mode, "+b" | "+e" | "+I") {
                    let entries = match mode {
                        "+b" => &channel.bans,
                        "+e" => &channel.exemptions,
                        _ => &channel.invite_exceptions,
                    };
                    return output(
                        "Channel access list",
                        entries
                            .iter()
                            .map(|id| hex(id))
                            .collect::<Vec<_>>()
                            .join("\n"),
                    );
                }

                let on = mode.starts_with('+');
                match mode {
                    "+k" | "-k" => {
                        let reply = self
                            .hosted_exchange(if on {
                                h::Request::RotateCode { channel: id }
                            } else {
                                h::Request::ClearCode { channel: id }
                            })
                            .await?;
                        return match reply{h::Reply::Link(link)=>output("Reusable code queued",format!("Share privately after acceptance:\n/hosted join {} #{} nickname",link.0,channel.alias)),_=>applied()};
                    }
                    "+m" | "-m" => (h::Change::Mode(h::Mode::Moderated, on), ""),
                    "+i" | "-i" => (h::Change::Mode(h::Mode::InviteOnly, on), ""),
                    "+t" | "-t" => (h::Change::Mode(h::Mode::TopicOperators, on), ""),
                    "+o" | "-o" => (h::Change::Operator(member(&channel, value)?, on), ""),
                    "+v" | "-v" => (h::Change::Voice(member(&channel, value)?, on), ""),
                    "+b" | "-b" | "+e" | "-e" | "+I" | "-I" => (
                        h::Change::AccessList(
                            match &mode[1..] {
                                "b" => h::AccessList::Ban,
                                "e" => h::AccessList::Exemption,
                                _ => h::AccessList::InviteException,
                            },
                            scoped_identity(&channel, value)?,
                            on,
                        ),
                        "",
                    ),
                    "+l" => (
                        h::Change::Capacity(value.parse().map_err(|_| "Capacity must be 2–500")?),
                        "",
                    ),
                    "private" => (h::Change::Discovery(h::Discovery::Private), ""),
                    "secret" => (h::Change::Discovery(h::Discovery::Secret), ""),
                    "public" => (h::Change::Discovery(h::Discovery::Public), ""),
                    _ => return Err("Unknown channel mode; use /help".into()),
                }
            }
            _ => return Err("Unknown hosted command; use /help".into()),
        };
        self.hosted_exchange(h::Request::Change {
            channel: id,
            change: change.0,
            reason: change.1.into(),
        })
        .await?;
        applied()
    }
}

pub(super) fn errors(state: &UiState) -> Vec<gchat_api::ProviderStatus> {
    state
        .hosted
        .iter()
        .filter_map(|(id, archive)| {
            archive
                .error
                .as_ref()
                .map(|error| gchat_api::ProviderStatus {
                    id: id.clone(),
                    code: "hosted_recovery".into(),
                    message: format!("#{}: {error}", archive.channel.alias),
                    retryable: true,
                })
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    fn channel() -> h::Channel {
        h::Channel {
            id: [1; 32],
            alias: "room".into(),
            endpoint: "https://example.invalid/v1/hosted".into(),
            self_member: [2; 32],
            epoch: 2,
            revision: 0,
            active: true,
            topic: String::new(),
            topic_pending: false,
            members: vec![
                h::Member {
                    id: [2; 32],
                    nickname: "alice".into(),
                    role: h::Role::Owner,
                    operator: true,
                    voice: false,
                    presence: h::Presence::Unknown,
                },
                h::Member {
                    id: [3; 32],
                    nickname: "bob".into(),
                    role: h::Role::Member,
                    operator: false,
                    voice: false,
                    presence: h::Presence::Away {
                        reason: "lunch".into(),
                    },
                },
            ],
            capacity: 500,
            bans: vec![],
            exemptions: vec![],
            invite_exceptions: vec![],
            moderated: false,
            invite_only: true,
            topic_operators: true,
            discovery: h::Discovery::Private,
            cursor: 2,
            pending: 0,
            presence_opt_in: false,
        }
    }
    fn event(sequence: u64, kind: h::EventKind) -> h::Event {
        h::Event {
            sequence,
            channel: [1; 32],
            accepted_at: 100 + sequence,
            kind,
        }
    }
    #[test]
    fn legacy_rewrite_cannot_discard_hosted_history_or_acknowledged_cursor() {
        let dir = tempfile::tempdir().unwrap();
        let legacy_path = dir.path().join("service");
        let hosted_path = dir.path().join("hosted-history");
        let (legacy, mut state): (_, UiState) =
            ChatServiceStore::open_or_create(&legacy_path, "password").unwrap();
        let store = persistence::ServiceStateStore::open(legacy, &hosted_path, &mut state).unwrap();
        store.save(&state).unwrap();
        assert!(
            !hosted_path.exists(),
            "unlock must not create a hosted archive"
        );
        apply(
            &mut state,
            channel(),
            vec![event(
                1,
                h::EventKind::Message {
                    id: [9; 32],
                    sender: [3; 32],
                    content: h::Content::Text("retained".into()),
                    delivery: h::Delivery::Delivered,
                },
            )],
        )
        .unwrap();
        store.save(&state).unwrap();
        let retained = std::fs::read(&hosted_path).unwrap();
        assert!(!retained.windows(8).any(|w| w == b"retained"));
        drop(store);
        // A legacy client sees and rewrites only its unchanged settings file.
        let (legacy, mut old): (_, UiState) =
            ChatServiceStore::open_or_create(&legacy_path, "password").unwrap();
        assert!(old.hosted.is_empty());
        old.presence_enabled = true;
        legacy.save(&old).unwrap();
        assert_eq!(std::fs::read(&hosted_path).unwrap(), retained);
        let store = persistence::ServiceStateStore::open(legacy, &hosted_path, &mut old).unwrap();
        assert_eq!(old.hosted[&key([1; 32])].cursor, 1);
        assert_eq!(old.hosted[&key([1; 32])].messages[0].body, "retained");
        assert!(old.presence_enabled);
        drop(store);
        let mut damaged = retained;
        *damaged.last_mut().unwrap() ^= 1;
        std::fs::write(&hosted_path, damaged).unwrap();
        let (legacy, mut old): (_, UiState) =
            ChatServiceStore::open_or_create(&legacy_path, "password").unwrap();
        assert!(persistence::ServiceStateStore::open(legacy, &hosted_path, &mut old).is_err());
    }

    #[test]
    fn archive_replay_deduplicates_and_never_promotes_service_acceptance_to_delivery() {
        let mut state = UiState::default();
        let room = channel();
        apply(&mut state, room.clone(), vec![]).unwrap();
        remember_queued(
            state.hosted.get_mut(&key(room.id)).unwrap(),
            [9; 32],
            &h::Content::Notice("maintenance".into()),
            "queued-notice",
        );
        let immediate = &state.hosted[&key(room.id)].messages;
        assert_eq!(
            immediate.len(),
            1,
            "local admission is visible before any network event"
        );
        assert_eq!(
            immediate[0].delivery,
            Some(gchat_api::Delivery::LocalAccepted)
        );
        let events = vec![
            event(
                1,
                h::EventKind::Message {
                    id: [9; 32],
                    sender: [2; 32],
                    content: h::Content::Notice("maintenance".into()),
                    delivery: h::Delivery::Pending,
                },
            ),
            event(
                2,
                h::EventKind::Delivery {
                    id: [9; 32],
                    state: h::Delivery::ServiceAccepted { sequence: 7 },
                },
            ),
        ];
        assert_eq!(apply(&mut state, room.clone(), events.clone()).unwrap(), 2);
        assert_eq!(apply(&mut state, room.clone(), events).unwrap(), 2);
        let archive = &state.hosted[&key(room.id)];
        assert_eq!(archive.messages.len(), 1);
        assert_eq!(
            archive.messages[0].message_kind,
            Some(gchat_api::MessageKind::Notice)
        );
        assert_eq!(
            archive.messages[0].delivery,
            Some(gchat_api::Delivery::ServiceAccepted)
        );
        let encoded = serde_json::to_vec(&state.hosted).unwrap();
        let restored: BTreeMap<String, Archive> = serde_json::from_slice(&encoded).unwrap();
        assert!(restored == state.hosted);
        let legacy = serde_json::to_vec(&state).unwrap();
        assert!(!serde_json::from_slice::<serde_json::Value>(&legacy)
            .unwrap()
            .as_object()
            .unwrap()
            .contains_key("hosted"));
        let mut candidate = state.clone();
        assert!(apply(
            &mut candidate,
            room.clone(),
            vec![event(4, h::EventKind::Removed)]
        )
        .is_err());
        assert_eq!(state.hosted[&key(room.id)].cursor, 2);
        let projected = conversations(&state);
        assert_eq!(
            projected[0].members[1].presence,
            Some(gchat_api::MemberPresence::Away {
                reason: "lunch".into()
            })
        );
        assert!(!projected[0].policy.as_ref().unwrap().presence_enabled);
    }
    #[test]
    fn hosted_name_history_preserves_event_order_and_scope_after_departure() {
        let mut state = UiState::default();
        let mut current = channel();
        let sender = current.members[0].id;
        let before = current.members[0].nickname.clone();
        apply(&mut state, current.clone(), vec![]).unwrap();
        current.members[0].nickname = "renamed".into();
        let message = |id| h::EventKind::Message {
            id: [id; 32],
            sender,
            content: h::Content::Text("retained".into()),
            delivery: h::Delivery::Pending,
        };
        apply(
            &mut state,
            current.clone(),
            vec![
                event(1, message(11)),
                event(
                    2,
                    h::EventKind::Message {
                        id: [12; 32],
                        sender,
                        content: h::Content::Nickname("renamed".into()),
                        delivery: h::Delivery::Pending,
                    },
                ),
                event(3, message(13)),
            ],
        )
        .unwrap();
        current.members.retain(|m| m.id != sender);
        apply(&mut state, current.clone(), vec![]).unwrap();
        let room = &state.hosted[&key(current.id)];
        assert_eq!(room.messages[0].nickname, before);
        assert_eq!(room.messages[1].nickname, "renamed");
        assert!(whowas(room, &before).unwrap().contains(&hex(&sender)));
        assert!(whowas(room, "renamed").unwrap().contains(&hex(&sender)));
        let encoded = serde_json::to_vec(room).unwrap();
        let reopened: Archive = serde_json::from_slice(&encoded).unwrap();
        assert_eq!(whowas(&reopened, &hex(&sender)).unwrap().lines().count(), 2);
        let mut legacy: serde_json::Value = serde_json::from_slice(&encoded).unwrap();
        legacy.as_object_mut().unwrap().remove("names");
        state
            .hosted
            .insert(key(current.id), serde_json::from_value(legacy).unwrap());
        apply(&mut state, current.clone(), vec![]).unwrap();
        assert!(whowas(&state.hosted[&key(current.id)], &before)
            .unwrap()
            .contains(&hex(&sender)));
        let mut other = channel();
        other.id = [77; 32];
        other.members.clear();
        apply(&mut state, other.clone(), vec![]).unwrap();
        assert!(!whowas(&state.hosted[&key(other.id)], "renamed")
            .unwrap()
            .contains(&hex(&sender)));
    }
    #[test]
    fn hosted_directory_commands_are_scoped_and_cursors_are_bounded() {
        assert!(handles(Some("hosted/room"), "/list"));
        assert!(!handles(Some("channel/legacy"), "/list"));
        assert!(!contacts::handles(Some("contact/peer"), "/list"));
        assert!(handles(None, "/hosted list"));
        assert!(validate(Some("hosted/room"), "/publish #public").is_ok());
        assert!(commands().iter().any(|c| c.name == "/publish"));
        assert_eq!(directory_cursor(&hex(&[17; 32])).unwrap(), [17; 32]);
        for bad in ["not-a-cursor", &"0".repeat(63), &"é".repeat(32)] {
            assert!(directory_cursor(bad).is_err());
        }
    }

    #[test]
    fn admission_secrets_are_not_recalled_and_scoped_bans_can_be_removed_after_departure() {
        assert_eq!(recall_text("/hosted join SECRET #room bob"), "/hosted ");
        let mut room = channel();
        room.members[1].nickname = "alice".into();
        assert!(member(&room, "alice").is_err());
        assert_eq!(scoped_identity(&room, &hex(&[7; 32])).unwrap(), [7; 32]);
        assert!(scoped_identity(&room, "unknown person").is_err());
        assert!(commands().iter().any(|c| c.name == "/notice"));
    }
}
