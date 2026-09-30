//! Explicit, channel-independent contacts. No legacy channel identity is linked.
use super::*;
use base64::{engine::general_purpose::URL_SAFE_NO_PAD as B64, Engine};
use gcoms::sdk::{ApplicationDelivery, ApplicationMessage, ContactCard};

const MIME: &str = "application/vnd.gchat.contact.v1";
const CARD_PREFIX: &str = "gchat-contact:v1:";
const MAX_CONTACTS: usize = 256;
const MAX_PENDING: usize = 512;

#[derive(Clone, Serialize, Deserialize, PartialEq, Eq)]
pub(super) struct Book {
    version: u16,
    contacts: BTreeMap<String, Contact>,
    outbox: BTreeMap<String, Pending>,
}
impl Default for Book {
    fn default() -> Self {
        Self {
            version: 1,
            contacts: BTreeMap::new(),
            outbox: BTreeMap::new(),
        }
    }
}
impl Book {
    pub(super) fn file_cards(&self) -> Vec<ContactCard> {
        self.contacts
            .values()
            .filter(|c| !c.blocked)
            .map(|c| c.card.clone())
            .collect()
    }
    pub(super) fn file_peer(&self, conversation: &str) -> Result<[u8; 32], String> {
        use sha2::{Digest, Sha256};
        let contact = self.contacts.get(conversation).ok_or("Unknown contact")?;
        if contact.blocked {
            return Err("Contact is blocked".into());
        }
        Ok(Sha256::digest(&contact.identity).into())
    }
    pub(super) fn is_empty(&self) -> bool {
        self.contacts.is_empty() && self.outbox.is_empty()
    }
}
#[derive(Clone, Serialize, Deserialize, PartialEq, Eq)]
struct Contact {
    #[serde(default)]
    presence: PresenceState,
    identity: Vec<u8>,
    card: ContactCard,
    alias: String,
    verified: bool,
    blocked: bool,
    messages: Vec<Message>,
    seen: BTreeMap<String, [u8; 32]>,
    files: BTreeMap<String, Content>,
    read: Option<String>,
    error: Option<String>,
}
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
enum ContactPresence {
    Available,
    Away { reason: String },
    Unknown,
}
impl ContactPresence {
    fn api(&self) -> gchat_api::MemberPresence {
        match self {
            Self::Available => gchat_api::MemberPresence::Available,
            Self::Away { reason } => gchat_api::MemberPresence::Away {
                reason: reason.clone(),
            },
            Self::Unknown => gchat_api::MemberPresence::Unknown,
        }
    }
}
#[derive(Clone, Default, Serialize, Deserialize, PartialEq, Eq)]
struct PresenceState {
    desired: Option<ContactPresence>,
    generation: u64,
    renew_at: u64,
    observed_generation: u64,
    observed: Option<ContactPresence>,
    expires_at: u64,
}
fn queue_presence(
    book: &mut Book,
    contact: &str,
    desired: Option<ContactPresence>,
) -> Result<(), String> {
    let peer = book.contacts.get_mut(contact).ok_or("Unknown contact")?;
    if peer.blocked {
        return Err("Contact is blocked".into());
    }
    let id = format!("{contact}/presence");
    if book.outbox.len() >= MAX_PENDING && !book.outbox.contains_key(&id) {
        return Err("Contact outbox is full".into());
    }
    peer.presence.desired = desired.clone();
    peer.presence.generation = peer
        .presence
        .generation
        .saturating_add(1)
        .max(now().saturating_mul(1000));
    peer.presence.renew_at = now().saturating_add(420);
    let envelope = Envelope::Presence {
        generation: peer.presence.generation,
        mode: desired.unwrap_or(ContactPresence::Unknown),
        expires_at: now().saturating_add(600),
    };
    book.outbox.insert(
        id,
        Pending {
            contact: contact.into(),
            wire: packet(&envelope)?,
            last_attempt: 0,
            receipt: true,
            digest: digest(&envelope)?,
        },
    );
    Ok(())
}

#[derive(Clone, Serialize, Deserialize, PartialEq, Eq)]
struct Pending {
    contact: String,
    wire: Vec<u8>,
    last_attempt: u64,
    receipt: bool,
    digest: [u8; 32],
}
#[derive(Clone, Serialize, Deserialize, PartialEq, Eq)]
enum Content {
    Text(String),
    Action(String),
    Notice(String),
    File { content_type: String, body: Vec<u8> },
}
#[derive(Clone, Serialize, Deserialize)]
enum Envelope {
    Message {
        id: [u8; 32],
        content: Content,
    },
    Receipt {
        id: [u8; 32],
        digest: [u8; 32],
    },
    Presence {
        generation: u64,
        mode: ContactPresence,
        expires_at: u64,
    },
}
fn key(identity: &[u8]) -> String {
    format!("contact/{}", hex(&Sha256::digest(identity)))
}
pub(super) fn is_conversation(id: &str) -> bool {
    id.starts_with("contact/")
}
pub(super) fn handles(conversation: Option<&str>, text: &str) -> bool {
    let command = split_head(text).0;
    command.eq_ignore_ascii_case("/contact")
        || (conversation.is_some_and(is_conversation)
            && !hosted::global_command(command)
            && !command.eq_ignore_ascii_case("/list")
            && !command.eq_ignore_ascii_case("/hosted"))
}
pub(super) fn validate_book(book: &Book) -> Result<(), String> {
    if book.version != 1
        || book.contacts.len() > MAX_CONTACTS
        || book.outbox.len() > MAX_PENDING
        || book.contacts.iter().any(|(id, c)| {
            key(&c.identity) != *id
                || c.alias.is_empty()
                || c.messages.len() > 10_000
                || c.seen.len() > 10_000
        })
        || book
            .outbox
            .values()
            .any(|p| !book.contacts.contains_key(&p.contact))
    {
        return Err("Contact archive is outside supported bounds".into());
    }
    Ok(())
}
fn validate_content(content: &Content) -> Result<(), String> {
    let valid = match content {
        Content::Text(text) | Content::Action(text) | Content::Notice(text) => {
            !text.is_empty()
                && text.len() <= 8192
                && !text.chars().any(|c| {
                    c.is_control()
                        && !matches!(
                            c,
                            '\n' | '\t'
                                | '\u{2}'
                                | '\u{3}'
                                | '\u{f}'
                                | '\u{16}'
                                | '\u{1d}'
                                | '\u{1f}'
                        )
                })
        }
        Content::File { content_type, body } => {
            !content_type.is_empty()
                && content_type.len() <= 128
                && content_type.is_ascii()
                && body.len() <= 512 * 1024
        }
    };
    if valid {
        Ok(())
    } else {
        Err("Invalid contact message".into())
    }
}
fn packet(envelope: &Envelope) -> Result<Vec<u8>, String> {
    ApplicationMessage {
        content_type: MIME.into(),
        body: postcard::to_allocvec(envelope).map_err(|e| e.to_string())?,
    }
    .encode()
    .map_err(|e| e.to_string())
}
fn digest(envelope: &Envelope) -> Result<[u8; 32], String> {
    Ok(Sha256::digest(postcard::to_allocvec(envelope).map_err(|e| e.to_string())?).into())
}
fn message(
    id: [u8; 32],
    conversation: &str,
    alias: &str,
    content: &Content,
    mine: bool,
    timestamp: u64,
) -> Option<Message> {
    let (kind, body) = match content {
        Content::Text(s) => (gchat_api::MessageKind::Text, s),
        Content::Action(s) => (gchat_api::MessageKind::Action, s),
        Content::Notice(s) => (gchat_api::MessageKind::Notice, s),
        Content::File { .. } => return None,
    };
    Some(Message {
        highlighted: None,
        message_kind: Some(kind),
        id: hex(&id),
        conversation_id: conversation.into(),
        member_id: (!mine).then(|| conversation.into()),
        nickname: if mine { "You".into() } else { alias.into() },
        body: body.clone(),
        timestamp,
        mine,
        operation_id: None,
        delivery: Some(if mine {
            gchat_api::Delivery::LocalAccepted
        } else {
            gchat_api::Delivery::Delivered
        }),
        result: None,
    })
}
fn queue(book: &mut Book, contact: &str, content: Content, operation: &str) -> Result<(), String> {
    validate_content(&content)?;
    if book.outbox.len() >= MAX_PENDING {
        return Err("Contact outbox is full; wait for pending delivery".into());
    }
    let peer = book.contacts.get_mut(contact).ok_or("Unknown contact")?;
    if peer.blocked {
        return Err("Contact is blocked".into());
    }
    if peer.messages.len() >= 10_000 {
        return Err("Contact archive message limit reached".into());
    }
    // Recover the same local operation rather than enqueue another application ID.
    if peer
        .messages
        .iter()
        .any(|m| m.operation_id.as_deref() == Some(operation))
    {
        return Ok(());
    }
    let id: [u8; 32] = rand::random();
    let envelope = Envelope::Message {
        id,
        content: content.clone(),
    };
    if let Some(mut message) = message(id, contact, &peer.alias, &content, true, now()) {
        message.operation_id = Some(operation.into());
        peer.messages.push(message);
    }
    book.outbox.insert(
        hex(&id),
        Pending {
            contact: contact.into(),
            wire: packet(&envelope)?,
            last_attempt: 0,
            receipt: false,
            digest: digest(&envelope)?,
        },
    );
    Ok(())
}
// Return true only for this protocol. Foreign component/application envelopes
// remain owned by their application and are never consumed here.
fn receive(book: &mut Book, delivery: &ApplicationDelivery) -> Result<bool, String> {
    if delivery.source_component.is_some() || delivery.destination_component.is_some() {
        return Ok(false);
    }
    let Ok(application) = ApplicationMessage::decode(&delivery.body) else {
        return Ok(false);
    };
    if application.content_type != MIME {
        return Ok(false);
    }
    let contact = key(&delivery.peer_identity);
    let Some(peer) = book.contacts.get_mut(&contact) else {
        return Ok(true);
    };
    if peer.blocked {
        return Ok(true);
    }
    let envelope: Envelope = match postcard::take_from_bytes(&application.body) {
        Ok((envelope, [])) => envelope,
        _ => {
            peer.error = Some("Contact sent an invalid message".into());
            return Ok(true);
        }
    };
    match &envelope {
        Envelope::Presence {
            generation,
            mode,
            expires_at,
        } => {
            let valid = !matches!(mode, ContactPresence::Away { reason } if reason.len() > 256 || reason.chars().any(char::is_control));
            if valid
                && *generation > peer.presence.observed_generation
                && *expires_at <= now().saturating_add(600)
            {
                peer.presence.observed_generation = *generation;
                peer.presence.observed = Some(mode.clone());
                peer.presence.expires_at = *expires_at;
            }
            // Presence is a bounded opt-in lease; it never generates receipt loops.
        }
        Envelope::Receipt { id, digest } => {
            let id = hex(id);
            if book
                .outbox
                .get(&id)
                .is_some_and(|p| !p.receipt && p.contact == contact && p.digest == *digest)
            {
                for message in &mut peer.messages {
                    if message.id == id && message.mine {
                        message.delivery = Some(gchat_api::Delivery::Delivered);
                    }
                }
                book.outbox.remove(&id);
            }
        }
        Envelope::Message { id, content } => {
            if let Err(error) = validate_content(content) {
                peer.error = Some(error);
                return Ok(true);
            }
            let hash = digest(&envelope)?;
            let message_id = hex(id);
            if peer.seen.get(&message_id).is_some_and(|old| *old != hash) {
                peer.error =
                    Some("Contact reused a message identity with different content".into());
                return Ok(true);
            }
            if book.outbox.len() >= MAX_PENDING {
                return Err("Contact receipt outbox is full".into());
            }
            if !peer.seen.contains_key(&message_id) {
                if peer.messages.len() >= 10_000 || peer.seen.len() >= 10_000 {
                    return Err("Contact archive limit reached".into());
                }
                if let Some(message) = message(
                    *id,
                    &contact,
                    &peer.alias,
                    content,
                    false,
                    delivery.received_at_unix,
                ) {
                    peer.messages.push(message);
                } else {
                    peer.files.insert(message_id.clone(), content.clone());
                }
                peer.seen.insert(message_id.clone(), hash);
            }
            let receipt = Envelope::Receipt {
                id: *id,
                digest: hash,
            };
            book.outbox.insert(
                format!("{contact}/ack/{message_id}"),
                Pending {
                    contact,
                    wire: packet(&receipt)?,
                    last_attempt: 0,
                    receipt: true,
                    digest: hash,
                },
            );
        }
    }
    Ok(true)
}

pub(super) fn commands() -> Vec<gchat_api::CommandSpec> {
    [
        ("/contact", "card | list | add alias code | update alias code | rename alias new-alias | verify alias fingerprint | block alias | unblock alias | open alias | info alias", "Manage independent contacts; adding a signed card is explicit consent"),
        ("/say", "text", "Send private text"), ("/me", "text", "Send a private action"),
        ("/notice", "text", "Send a notice; notices never trigger automatic replies"),
        ("/whois", "", "Show this contact's identity and verification state"),
        ("/away", "[reason]", "Share away presence with this contact"),
        ("/back", "", "Share available presence with this contact"),
        ("/presence", "on|off", "Opt in to presence for this contact or become invisible"),
        ("/block", "", "Block this contact persistently"), ("/unblock", "", "Unblock this contact"),
        ("/query", "", "Open this independent private conversation"),
        ("/hide", "", "Hide this window and retain history"), ("/close", "", "Hide this window and retain history"),
        ("/help", "", "Show contact commands"),
    ].into_iter().map(|(name,args,description)| gchat_api::CommandSpec { name: name.into(), usage: format!("{name} {args}").trim().into(), description: description.into(), scope: if name == "/contact" { "instance" } else { "conversation" }.into(), capability: Some("DirectMessage".into()), available: true }).collect()
}
pub(super) fn validate(conversation: Option<&str>, text: &str) -> Result<(), String> {
    if text.len() > gchat_api::command_input_limit(text) {
        return Err("Contact input exceeds its bound".into());
    }
    if split_head(text).0.eq_ignore_ascii_case("/contact") {
        return Ok(());
    }
    if !conversation.is_some_and(is_conversation) {
        return Err("Open a contact conversation first".into());
    }
    if !text.starts_with('/')
        || commands()
            .iter()
            .any(|c| c.name.eq_ignore_ascii_case(split_head(text).0))
    {
        Ok(())
    } else {
        Err("Use /help for independent contact commands".into())
    }
}

pub(super) fn conversations(book: &Book, prefs: &preferences::Preferences) -> Vec<Conversation> {
    book.contacts
        .iter()
        .map(|(id, contact)| {
            let read = contact
                .read
                .as_ref()
                .and_then(|id| contact.messages.iter().position(|m| m.id == *id))
                .map_or(0, |i| i + 1);
            Conversation {
                catch_up: None,
                muted: None,
                policy: None,
                provider: None,
                id: id.clone(),
                channel_id: String::new(),
                kind: ConversationKind::Query,
                name: contact.alias.clone(),
                topic: if contact.blocked {
                    "Blocked contact"
                } else if contact.verified {
                    "Verified independent contact"
                } else {
                    "Independent contact — identity not yet verified"
                }
                .into(),
                active: true,
                owner: false,
                visibility: Some("contact".into()),
                directory: None,
                members: vec![Member {
                    presence: Some(if !contact.blocked && contact.presence.expires_at > now() {
                        contact
                            .presence
                            .observed
                            .as_ref()
                            .unwrap_or(&ContactPresence::Unknown)
                            .api()
                    } else {
                        gchat_api::MemberPresence::Unknown
                    }),
                    id: id.clone(),
                    nickname: contact.alias.clone(),
                    is_self: false,
                    recently_active: None,
                    capabilities: Vec::new(),
                }],
                unread: contact.messages[read..]
                    .iter()
                    .filter(|m| !m.mine && !prefs.ignores(id, m.member_id.as_deref(), m.mine))
                    .count()
                    .try_into()
                    .unwrap_or(u32::MAX),
                last_message_id: contact.messages.last().map(|m| m.id.clone()),
                input_limit_bytes: 8192,
                commands: commands(),
            }
        })
        .collect()
}
pub(super) fn history(
    book: &Book,
    id: &str,
    before: Option<&str>,
    limit: u16,
    search: Option<&str>,
) -> Result<Response, String> {
    let contact = book.contacts.get(id).ok_or("Unknown contact")?;
    let query = search.map(str::to_lowercase);
    let messages: Vec<_> = contact
        .messages
        .iter()
        .filter(|m| {
            query.as_ref().is_none_or(|q| {
                m.body.to_lowercase().contains(q) || m.nickname.to_lowercase().contains(q)
            })
        })
        .collect();
    let end = before
        .map(|id| {
            messages
                .iter()
                .position(|m| m.id == id)
                .ok_or("Unknown history cursor")
        })
        .transpose()?
        .unwrap_or(messages.len());
    let start = end.saturating_sub(usize::from(limit.clamp(1, 200)));
    let page: Vec<_> = messages[start..end].iter().map(|m| (*m).clone()).collect();
    Ok(Response::History {
        page: HistoryPage {
            before: (start > 0).then(|| page[0].id.clone()),
            messages: page,
        },
    })
}
pub(super) fn mark_read(book: &mut Book, id: &str, message: &str) -> Result<(), String> {
    let contact = book.contacts.get_mut(id).ok_or("Unknown contact")?;
    let next = contact
        .messages
        .iter()
        .position(|m| m.id == message)
        .ok_or("Unknown read marker")?;
    let old = contact
        .read
        .as_ref()
        .and_then(|id| contact.messages.iter().position(|m| m.id == *id));
    if old.is_none_or(|old| next > old) {
        contact.read = Some(message.into());
    }
    Ok(())
}
fn resolve(book: &Book, alias: &str) -> Result<String, String> {
    if book.contacts.contains_key(alias) {
        return Ok(alias.into());
    }
    book.contacts
        .iter()
        .find(|(_, c)| c.alias.eq_ignore_ascii_case(alias))
        .map(|(id, _)| id.clone())
        .ok_or_else(|| "Unknown contact; use /contact list".into())
}
fn alias(value: &str) -> Result<(), String> {
    if value.is_empty()
        || value.len() > 128
        || value.chars().any(|c| c.is_whitespace() || c.is_control())
    {
        Err("Choose a contact alias of 1–128 bytes without spaces".into())
    } else {
        Ok(())
    }
}
fn description(id: &str, contact: &Contact) -> String {
    format!(
        "{}\nIdentity fingerprint: {}\nVerified: {}\nBlocked: {}\nIndependent of every channel\nLast error: {}",
        contact.alias,
        id.trim_start_matches("contact/"),
        contact.verified,
        contact.blocked,
        contact.error.as_deref().unwrap_or("none")
    )
}
fn block(book: &mut Book, id: &str, blocked: bool) -> Result<(), String> {
    let contact = book.contacts.get_mut(id).ok_or("Unknown contact")?;
    contact.blocked = blocked;
    if blocked {
        contact.presence.desired = None;
        contact.presence.observed = None;
        contact.presence.expires_at = 0;
        for message in &mut contact.messages {
            if message.mine && message.delivery == Some(gchat_api::Delivery::LocalAccepted) {
                message.delivery = Some(gchat_api::Delivery::Failed);
            }
        }
        book.outbox.retain(|_, p| p.contact != id);
    }
    Ok(())
}
impl ChatService {
    pub(super) async fn submit_contact(
        &self,
        conversation: Option<&str>,
        text: &str,
        operation: &str,
    ) -> Result<Response, String> {
        self.require(Capability::DirectMessage)?;
        let (command, args) = if let Some(text) = text.strip_prefix('/') {
            split_head(text)
        } else {
            ("say", text)
        };
        let command = command.to_ascii_lowercase();
        let output = |title: &str, text: String| {
            Ok(Response::Output {
                conversation: conversation.map(str::to_owned),
                output: gchat_api::CommandOutput::Text {
                    title: title.into(),
                    text,
                },
            })
        };
        if command == "contact" {
            let (action, rest) = split_head(args);
            if action.eq_ignore_ascii_case("card") {
                let identity = self
                    .runtime
                    .sdk_client()
                    .refresh_identity()
                    .await
                    .map_err(|e| e.to_string())?;
                return output(
                    "Your contact card — share only with people you choose",
                    format!("{CARD_PREFIX}{}", B64.encode(&identity.contact_card.0)),
                );
            }
            if matches!(action.to_ascii_lowercase().as_str(), "add" | "update") {
                let (name, encoded) = split_head(rest);
                alias(name)?;
                let raw = B64
                    .decode(
                        encoded
                            .strip_prefix(CARD_PREFIX)
                            .ok_or("Use a GChat contact card")?,
                    )
                    .map_err(|_| "Invalid contact card encoding")?;
                let card = ContactCard(raw);
                let identity = self
                    .runtime
                    .sdk_client()
                    .resolve_contact_identity(&card)
                    .await
                    .map_err(|e| e.to_string())?;
                let own = self
                    .runtime
                    .sdk_client()
                    .resolve_contact_identity(&self.runtime.sdk_client().identity().contact_card)
                    .await
                    .map_err(|e| e.to_string())?;
                if identity == own {
                    return Err("This is your own contact card".into());
                }
                let id = key(&identity);
                let mut session = self.session.lock().await;
                let current = session.as_mut().ok_or("Archive is closed")?;
                let mut candidate = current.state.clone();
                if action.eq_ignore_ascii_case("update") {
                    if resolve(&candidate.contacts, name)? != id {
                        return Err(
                            "Contact identity changed; add a separate contact explicitly".into(),
                        );
                    }
                    candidate
                        .contacts
                        .contacts
                        .get_mut(&id)
                        .expect("resolved")
                        .card = card;
                } else {
                    if candidate.contacts.contacts.len() >= MAX_CONTACTS {
                        return Err("Contact limit reached".into());
                    }
                    if candidate.contacts.contacts.contains_key(&id)
                        || candidate
                            .contacts
                            .contacts
                            .values()
                            .any(|c| c.alias.eq_ignore_ascii_case(name))
                    {
                        return Err("Contact or alias already exists; use update or rename".into());
                    }
                    candidate.contacts.contacts.insert(
                        id.clone(),
                        Contact {
                            presence: PresenceState::default(),
                            identity,
                            card,
                            alias: name.into(),
                            verified: false,
                            blocked: false,
                            messages: Vec::new(),
                            seen: BTreeMap::new(),
                            files: BTreeMap::new(),
                            read: None,
                            error: None,
                        },
                    );
                }
                current.store.save(&candidate)?;
                current.state = candidate;
                if let Some(files) = &current.files {
                    files.contacts(&current.state.contacts).await?;
                }
                self.invalidate();
                return Ok(Response::Applied { conversation: Some(id), notice: Some("Contact saved. Share your card with them to enable mutual private messaging; compare fingerprints before marking the identity verified.".into()) });
            }
            let mut session = self.session.lock().await;
            let current = session.as_mut().ok_or("Archive is closed")?;
            if action.eq_ignore_ascii_case("list") || action.is_empty() {
                return output(
                    "Independent contacts",
                    current
                        .state
                        .contacts
                        .contacts
                        .iter()
                        .map(|(id, c)| {
                            format!(
                                "{}{} — {}",
                                c.alias,
                                if c.blocked { " (blocked)" } else { "" },
                                id
                            )
                        })
                        .collect::<Vec<_>>()
                        .join("\n"),
                );
            }
            let (name, extra) = split_head(rest);
            let id = resolve(&current.state.contacts, name)?;
            if action.eq_ignore_ascii_case("info") {
                return output(
                    "Contact identity",
                    description(&id, &current.state.contacts.contacts[&id]),
                );
            }
            if action.eq_ignore_ascii_case("open") {
                return Ok(Response::Applied {
                    conversation: Some(id),
                    notice: None,
                });
            }
            let mut candidate = current.state.clone();
            match action.to_ascii_lowercase().as_str() {
                "rename" => {
                    alias(extra)?;
                    if candidate
                        .contacts
                        .contacts
                        .iter()
                        .any(|(other, c)| *other != id && c.alias.eq_ignore_ascii_case(extra))
                    {
                        return Err("Contact alias already exists".into());
                    }
                    candidate
                        .contacts
                        .contacts
                        .get_mut(&id)
                        .expect("resolved")
                        .alias = extra.into();
                }
                "verify" => {
                    if !extra.eq_ignore_ascii_case(id.trim_start_matches("contact/")) {
                        return Err("Fingerprint does not match this contact".into());
                    }
                    candidate
                        .contacts
                        .contacts
                        .get_mut(&id)
                        .expect("resolved")
                        .verified = true;
                }
                "block" => block(&mut candidate.contacts, &id, true)?,
                "unblock" => block(&mut candidate.contacts, &id, false)?,
                _ => return Err("Use /help for contact commands".into()),
            }
            current.store.save(&candidate)?;
            current.state = candidate;
            if let Some(files) = &current.files {
                files.contacts(&current.state.contacts).await?;
            }
            self.invalidate();
            return Ok(Response::Applied {
                conversation: Some(id),
                notice: None,
            });
        }
        let id = conversation
            .filter(|id| is_conversation(id))
            .ok_or("Open an independent contact conversation")?;
        let mut session = self.session.lock().await;
        let current = session.as_mut().ok_or("Archive is closed")?;
        match command.as_str() {
            "help" => {
                return Ok(Response::Output {
                    conversation: Some(id.into()),
                    output: gchat_api::CommandOutput::Help {
                        commands: self.context_commands(Some(id)),
                    },
                })
            }
            "whois" => {
                return output(
                    "Contact identity",
                    description(
                        id,
                        current
                            .state
                            .contacts
                            .contacts
                            .get(id)
                            .ok_or("Unknown contact")?,
                    ),
                )
            }
            "close" | "hide" => {
                return Ok(Response::Output {
                    conversation: Some(id.into()),
                    output: gchat_api::CommandOutput::Close {
                        conversation: id.into(),
                    },
                })
            }
            "query" => {
                return Ok(Response::Applied {
                    conversation: Some(id.into()),
                    notice: None,
                })
            }
            _ => {}
        }
        let mut candidate = current.state.clone();
        match command.as_str() {
            "away" => {
                if args.len() > 256 || args.chars().any(char::is_control) {
                    return Err(
                        "Away reasons accept up to 256 bytes without control characters".into(),
                    );
                }
                queue_presence(
                    &mut candidate.contacts,
                    id,
                    Some(ContactPresence::Away {
                        reason: args.into(),
                    }),
                )?;
            }
            "back" => queue_presence(
                &mut candidate.contacts,
                id,
                Some(ContactPresence::Available),
            )?,
            "presence" => match args.to_ascii_lowercase().as_str() {
                "on" => queue_presence(
                    &mut candidate.contacts,
                    id,
                    Some(ContactPresence::Available),
                )?,
                "off" => queue_presence(&mut candidate.contacts, id, None)?,
                _ => {
                    return Err(
                        "Use /presence on|off; sharing defaults off for each contact".into(),
                    )
                }
            },
            "say" => queue(
                &mut candidate.contacts,
                id,
                Content::Text(args.into()),
                operation,
            )?,
            "me" => queue(
                &mut candidate.contacts,
                id,
                Content::Action(args.into()),
                operation,
            )?,
            "notice" => queue(
                &mut candidate.contacts,
                id,
                Content::Notice(args.into()),
                operation,
            )?,
            "block" => block(&mut candidate.contacts, id, true)?,
            "unblock" => block(&mut candidate.contacts, id, false)?,
            _ => return Err("Use /help for contact commands".into()),
        }
        current.store.save(&candidate)?;
        current.state = candidate;
        if let Some(files) = &current.files {
            files.contacts(&current.state.contacts).await?;
        }
        self.invalidate();
        Ok(Response::Applied {
            conversation: Some(id.into()),
            notice: None,
        })
    }
}
impl ChatService {
    async fn sync_contacts(&self, cursor: &mut u64) -> Result<(), String> {
        let sdk = self.runtime.sdk_client();
        let incoming = sdk
            .application_inbox(*cursor, 32)
            .await
            .map_err(|e| e.to_string())?;
        if incoming.is_empty() {
            *cursor = 0;
        }
        let mut deferred_error = None;
        for delivery in incoming {
            let consume = {
                let mut session = self.session.lock().await;
                let current = session.as_mut().ok_or("Contact archive is closed")?;
                let mut candidate = current.state.clone();
                match receive(&mut candidate.contacts, &delivery) {
                    Ok(consume) => {
                        if candidate.contacts != current.state.contacts {
                            current.store.save(&candidate)?;
                            current.state = candidate;
                            self.invalidate();
                        }
                        consume
                    }
                    Err(error) => {
                        // Keep this delivery durable and visit it on the next scan.
                        // Continue to other receipts and drain outgoing ACKs even
                        // when one contact or the receipt outbox is full.
                        deferred_error = Some(error);
                        false
                    }
                }
            };
            if consume {
                sdk.commit_application(delivery.sequence, delivery.receipt_digest)
                    .await
                    .map_err(|e| e.to_string())?;
            }
            *cursor = delivery.sequence;
        }
        let outgoing = {
            let mut session = self.session.lock().await;
            let current = session.as_mut().ok_or("Contact archive is closed")?;
            let renew: Vec<_> = current
                .state
                .contacts
                .contacts
                .iter()
                .filter(|(id, c)| {
                    !c.blocked
                        && c.presence.desired.is_some()
                        && c.presence.renew_at <= now()
                        && !current
                            .state
                            .contacts
                            .outbox
                            .contains_key(&format!("{id}/presence"))
                })
                .map(|(id, c)| (id.clone(), c.presence.desired.clone()))
                .collect();
            if !renew.is_empty() {
                let mut candidate = current.state.clone();
                for (id, desired) in renew {
                    if candidate.contacts.outbox.len() < MAX_PENDING {
                        queue_presence(&mut candidate.contacts, &id, desired)?;
                    }
                }
                current.store.save(&candidate)?;
                current.state = candidate;
            }
            let mut pending: Vec<_> = current
                .state
                .contacts
                .outbox
                .iter()
                .filter(|(_, p)| p.last_attempt == 0 || now().saturating_sub(p.last_attempt) >= 30)
                .filter_map(|(id, p)| {
                    current
                        .state
                        .contacts
                        .contacts
                        .get(&p.contact)
                        .filter(|c| !c.blocked)
                        .map(|c| (id.clone(), p.clone(), c.card.clone()))
                })
                .collect();
            pending.sort_by_key(|(_, p, _)| (!p.receipt, p.last_attempt));
            pending.truncate(4);
            pending
        };
        for (id, pending, card) in outgoing {
            // Order block/remove commands against new transport admissions.
            let _send = self.operations.read().await;
            {
                let session = self.session.lock().await;
                let current = session.as_ref().ok_or("Contact archive is closed")?;
                if current
                    .state
                    .contacts
                    .outbox
                    .get(&id)
                    .is_none_or(|p| p.wire != pending.wire)
                    || current
                        .state
                        .contacts
                        .contacts
                        .get(&pending.contact)
                        .is_none_or(|c| c.blocked)
                {
                    continue;
                }
            }
            // Local queue admission is not recipient delivery. The independent
            // authenticated application receipt above is the only promotion.
            let application =
                ApplicationMessage::decode(&pending.wire).map_err(|e| e.to_string())?;
            let failure = sdk
                .submit_durable_opaque(&card, MIME, &application.body)
                .await
                .err()
                .map(|e| e.to_string());
            let mut session = self.session.lock().await;
            let current = session.as_mut().ok_or("Contact archive is closed")?;
            if let Some(stored) = current.state.contacts.outbox.get(&id) {
                if stored.wire != pending.wire {
                    return Err("Contact operation identity changed".into());
                }
                let mut candidate = current.state.clone();
                if let Some(peer) = candidate.contacts.contacts.get_mut(&pending.contact) {
                    peer.error = failure.clone();
                }
                if pending.receipt && failure.is_none() {
                    candidate.contacts.outbox.remove(&id);
                } else {
                    candidate
                        .contacts
                        .outbox
                        .get_mut(&id)
                        .expect("retained")
                        .last_attempt = now();
                }
                current.store.save(&candidate)?;
                current.state = candidate;
                self.invalidate();
            }
        }
        deferred_error.map_or(Ok(()), Err)
    }
    pub(super) fn spawn_contact_worker(service: &Arc<Self>) -> tokio::task::JoinHandle<()> {
        let weak = Arc::downgrade(service);
        let mut stopped = service.stopped.subscribe();
        tokio::spawn(async move {
            let mut tick = tokio::time::interval(Duration::from_millis(500));
            tick.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
            let mut cursor = 0;
            loop {
                tokio::select! { _ = stopped.changed() => break, _ = tick.tick() => {} }
                let Some(service) = weak.upgrade() else {
                    break;
                };
                if *stopped.borrow() {
                    break;
                }
                if !service.capabilities.contains(&Capability::DirectMessage)
                    || service
                        .session
                        .lock()
                        .await
                        .as_ref()
                        .is_none_or(|s| s.state.contacts.is_empty())
                {
                    continue;
                }
                let Ok(_update) = service.update_gate.enter() else {
                    continue;
                };
                let result = tokio::select! { _ = stopped.changed() => break, result = service.sync_contacts(&mut cursor) => result };
                let mut session = service.session.lock().await;
                if let Some(current) = session.as_mut() {
                    let error = result.err();
                    if current.contact_error != error {
                        current.contact_error = error;
                        service.invalidate();
                    }
                }
            }
        })
    }
}

pub(super) fn completions(book: &Book, text: &str) -> Option<Vec<Completion>> {
    for prefix in [
        "/contact open ",
        "/contact info ",
        "/contact block ",
        "/contact unblock ",
        "/contact verify ",
        "/contact update ",
        "/contact rename ",
    ] {
        if let Some(query) = text.strip_prefix(prefix) {
            return Some(
                book.contacts
                    .values()
                    .filter(|c| c.alias.to_lowercase().starts_with(&query.to_lowercase()))
                    .take(20)
                    .map(|c| Completion {
                        text: format!("{prefix}{}", c.alias),
                        description: "Independent contact".into(),
                    })
                    .collect(),
            );
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    fn contact(identity: Vec<u8>, alias: &str) -> Contact {
        Contact {
            presence: PresenceState::default(),
            identity,
            card: ContactCard(vec![]),
            alias: alias.into(),
            verified: false,
            blocked: false,
            messages: Vec::new(),
            seen: BTreeMap::new(),
            files: BTreeMap::new(),
            read: None,
            error: None,
        }
    }
    fn delivery(peer: Vec<u8>, wire: Vec<u8>) -> ApplicationDelivery {
        ApplicationDelivery {
            source_component: None,
            destination_component: None,
            sequence: 1,
            peer_identity: peer,
            message_id: [1; 16],
            received_at_unix: 100,
            body: wire,
            receipt_digest: [2; 32],
        }
    }
    #[test]
    fn receipts_bind_peer_and_content_and_duplicates_never_repeat_messages_or_loop_notices() {
        let mut alice = Book::default();
        let mut bob = Book::default();
        let aid = key(&[1]);
        let bid = key(&[2]);
        alice.contacts.insert(bid.clone(), contact(vec![2], "bob"));
        bob.contacts.insert(aid.clone(), contact(vec![1], "alice"));
        queue(
            &mut alice,
            &bid,
            Content::Notice("maintenance".into()),
            "operation-one",
        )
        .unwrap();
        queue(
            &mut alice,
            &bid,
            Content::Notice("maintenance".into()),
            "operation-one",
        )
        .unwrap();
        assert_eq!(alice.contacts[&bid].messages.len(), 1);
        let outgoing = alice.outbox.values().next().unwrap().wire.clone();
        let received = delivery(vec![1], outgoing);
        receive(&mut bob, &received).unwrap();
        receive(&mut bob, &received).unwrap();
        assert_eq!(bob.contacts[&aid].messages.len(), 1);
        assert_eq!(bob.outbox.len(), 1, "only a receipt, never a notice reply");
        let receipt = bob.outbox.values().next().unwrap().wire.clone();
        receive(&mut alice, &delivery(vec![3], receipt.clone())).unwrap();
        assert_eq!(
            alice.contacts[&bid].messages[0].delivery,
            Some(gchat_api::Delivery::LocalAccepted)
        );
        receive(&mut alice, &delivery(vec![2], receipt.clone())).unwrap();
        assert_eq!(
            alice.contacts[&bid].messages[0].delivery,
            Some(gchat_api::Delivery::Delivered)
        );
        assert!(alice.outbox.is_empty());
        receive(&mut alice, &delivery(vec![2], receipt)).unwrap();
        assert!(
            alice.outbox.is_empty(),
            "receipt replay must not create an ACK loop"
        );
        block(&mut bob, &aid, true).unwrap();
        assert!(bob.outbox.is_empty());
        receive(&mut bob, &received).unwrap();
        assert!(bob.outbox.is_empty());
        assert!(queue(
            &mut bob,
            &aid,
            Content::Text("blocked".into()),
            "operation-two"
        )
        .is_err());
        let restored: Book = serde_json::from_slice(&serde_json::to_vec(&bob).unwrap()).unwrap();
        assert!(restored.contacts[&aid].blocked);
    }
    #[test]
    fn presence_is_opt_in_expires_and_cannot_replay_after_invisible() {
        let mut alice = Book::default();
        let mut bob = Book::default();
        let aid = key(&[1]);
        let bid = key(&[2]);
        alice.contacts.insert(bid.clone(), contact(vec![2], "bob"));
        bob.contacts.insert(aid.clone(), contact(vec![1], "alice"));
        assert!(alice.contacts[&bid].presence.desired.is_none());
        queue_presence(
            &mut alice,
            &bid,
            Some(ContactPresence::Away {
                reason: "lunch".into(),
            }),
        )
        .unwrap();
        let away = alice.outbox.values().next().unwrap().wire.clone();
        receive(&mut bob, &delivery(vec![1], away.clone())).unwrap();
        assert_eq!(
            bob.contacts[&aid].presence.observed,
            Some(ContactPresence::Away {
                reason: "lunch".into()
            })
        );
        assert!(bob.outbox.is_empty(), "presence never causes an ACK loop");
        queue_presence(&mut alice, &bid, None).unwrap();
        receive(
            &mut bob,
            &delivery(vec![1], alice.outbox.values().next().unwrap().wire.clone()),
        )
        .unwrap();
        receive(&mut bob, &delivery(vec![1], away)).unwrap();
        assert_eq!(
            bob.contacts[&aid].presence.observed,
            Some(ContactPresence::Unknown)
        );
        let restored: Book = serde_json::from_slice(&serde_json::to_vec(&alice).unwrap()).unwrap();
        assert!(restored.contacts[&bid].presence.desired.is_none());
        bob.contacts.get_mut(&aid).unwrap().presence.expires_at = now().saturating_sub(1);
        assert_eq!(
            conversations(&bob, &preferences::Preferences::default())[0].members[0].presence,
            Some(gchat_api::MemberPresence::Unknown)
        );
        block(&mut alice, &bid, true).unwrap();
        assert!(alice.outbox.is_empty());
        assert!(queue_presence(&mut alice, &bid, Some(ContactPresence::Available)).is_err());
    }
    #[test]
    fn contact_sidecar_survives_legacy_rewrite_and_does_not_link_scoped_history() {
        let dir = tempfile::tempdir().unwrap();
        let legacy_path = dir.path().join("service");
        let history_path = dir.path().join("hosted-history");
        let (legacy, mut state): (_, UiState) =
            ChatServiceStore::open_or_create(&legacy_path, "password").unwrap();
        let stores =
            persistence::ServiceStateStore::open(legacy, &history_path, &mut state).unwrap();
        stores.save(&state).unwrap();
        assert!(!history_path.with_extension("contacts").exists());
        let id = key(&[2]);
        state
            .contacts
            .contacts
            .insert(id.clone(), contact(vec![2], "alice"));
        queue(
            &mut state.contacts,
            &id,
            Content::Text("independent secret".into()),
            "operation",
        )
        .unwrap();
        stores.save(&state).unwrap();
        let bytes = std::fs::read(history_path.with_extension("contacts")).unwrap();
        assert!(!bytes.windows(18).any(|w| w == b"independent secret"));
        drop(stores);
        let (legacy, mut old): (_, UiState) =
            ChatServiceStore::open_or_create(&legacy_path, "password").unwrap();
        assert!(old.contacts.is_empty());
        legacy.save(&old).unwrap();
        let _stores =
            persistence::ServiceStateStore::open(legacy, &history_path, &mut old).unwrap();
        assert_eq!(old.contacts.contacts[&id].messages.len(), 1);
        assert_eq!(old.contacts.outbox.len(), 1);
        assert!(old.hosted.is_empty());
        assert!(old.observed_channels.is_empty());
        assert_eq!(recall_text("/contact add alice SECRET"), "/contact ");
    }
}
