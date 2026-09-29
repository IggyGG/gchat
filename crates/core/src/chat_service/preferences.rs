//! Local IRC workflows. Identity filters are explicitly scoped to a conversation.
use super::*;
use std::collections::BTreeSet;

#[derive(Clone, Default, Serialize, Deserialize, PartialEq, Eq)]
pub(super) struct Preferences {
    muted: BTreeSet<String>,
    ignored: BTreeMap<String, BTreeSet<String>>,
    highlights: BTreeSet<String>,
    aliases: BTreeMap<String, String>,
}
impl Preferences {
    pub(super) fn is_empty(&self) -> bool {
        self == &Self::default()
    }
    pub(super) fn muted(&self, conversation: &str) -> bool {
        self.muted.contains(conversation)
    }
    pub(super) fn ignores(&self, conversation: &str, member: Option<&str>, mine: bool) -> bool {
        !mine
            && member.is_some_and(|m| {
                self.ignored
                    .get(conversation)
                    .is_some_and(|ids| ids.contains(m))
            })
    }
    pub(super) fn highlighted(&self, message: &Message) -> bool {
        !message.mine
            && self
                .highlights
                .iter()
                .any(|word| message.body.to_lowercase().contains(word))
    }
    pub(super) fn expand(&self, text: &str) -> Result<String, String> {
        let (name, rest) = split_head(text);
        let Some(expansion) = self.aliases.get(&name.to_ascii_lowercase()) else {
            return Ok(text.into());
        };
        // Exactly one expansion: aliases cannot recursively invoke aliases or commands.
        let expanded = if rest.is_empty() {
            expansion.clone()
        } else {
            format!("{expansion} {rest}")
        };
        if expanded.len() > gchat_api::command_input_limit(&expanded) {
            return Err("Expanded alias exceeds input limit".into());
        }
        Ok(expanded)
    }
    pub(super) fn completions(&self) -> Vec<Completion> {
        self.aliases
            .keys()
            .map(|name| Completion {
                text: name.clone(),
                description: "Local command alias".into(),
            })
            .collect()
    }
}
pub(super) fn handles(text: &str) -> bool {
    matches!(
        split_head(text).0.to_ascii_lowercase().as_str(),
        "/mute" | "/ignore" | "/unignore" | "/highlight" | "/alias" | "/unalias"
    )
}
pub(super) fn commands() -> Vec<gchat_api::CommandSpec> {
    [
        (
            "/mute",
            "[on|off]",
            "Suppress unread indicators for this conversation; retain its history",
        ),
        (
            "/ignore",
            "[member]",
            "Hide a member's messages in this conversation; history stays encrypted",
        ),
        (
            "/unignore",
            "member",
            "Show this scoped member's messages again",
        ),
        (
            "/highlight",
            "[add text|remove text|list]",
            "Highlight matching incoming text locally",
        ),
        (
            "/alias",
            "[name /command arguments]",
            "Save a local alias for one command; arguments are appended literally",
        ),
        ("/unalias", "name", "Remove a local command alias"),
    ]
    .into_iter()
    .map(|(name, args, description)| gchat_api::CommandSpec {
        name: name.into(),
        usage: format!("{name} {args}"),
        description: description.into(),
        scope: if matches!(name, "/mute" | "/ignore" | "/unignore") {
            "conversation"
        } else {
            "instance"
        }
        .into(),
        capability: None,
        available: true,
    })
    .collect()
}
pub(super) fn decorate(preferences: &Preferences, mut response: Response) -> Response {
    if let Response::History { page } = &mut response {
        page.messages
            .retain(|m| !preferences.ignores(&m.conversation_id, m.member_id.as_deref(), m.mine));
        for message in &mut page.messages {
            message.highlighted = Some(preferences.highlighted(message));
        }
    }
    response
}
impl ChatService {
    pub(super) async fn submit_preference(
        &self,
        conversation: Option<&str>,
        text: &str,
    ) -> Result<Response, String> {
        let (command, args) = split_head(text);
        let mut session = self.session.lock().await;
        let current = session.as_mut().ok_or("Archive is closed")?;
        let projected = self.project(Some(current));
        let room = conversation.and_then(|id| projected.conversations.iter().find(|c| c.id == id));
        let mut candidate = current.state.clone();
        let prefs = &mut candidate.preferences;
        let mut lines = Vec::new();
        match command.to_ascii_lowercase().as_str() {
            "/mute" => {
                let room = room.ok_or("Open a conversation first")?;
                match args.to_ascii_lowercase().as_str() {
                    "on" => {
                        prefs.muted.insert(room.id.clone());
                    }
                    "off" => {
                        prefs.muted.remove(&room.id);
                    }
                    "" => {}
                    _ => return Err("Use /mute on|off".into()),
                }
                lines.push(format!("Conversation muted: {}", prefs.muted(&room.id)));
            }
            "/ignore" | "/unignore" => {
                let room = room.ok_or("Open a conversation first")?;
                let ignored = prefs.ignored.entry(room.id.clone()).or_default();
                if args.is_empty() && command.eq_ignore_ascii_case("/ignore") {
                    lines.extend(ignored.iter().cloned());
                } else {
                    let members: Vec<_> = room
                        .members
                        .iter()
                        .filter(|m| m.id == args || m.nickname.eq_ignore_ascii_case(args))
                        .collect();
                    let id = if members.len() == 1 && !members[0].is_self {
                        members[0].id.clone()
                    } else if command.eq_ignore_ascii_case("/unignore") && ignored.contains(args) {
                        args.into()
                    } else {
                        return Err(
                            "Choose one other member by exact scoped ID or unambiguous nickname"
                                .into(),
                        );
                    };
                    if command.eq_ignore_ascii_case("/ignore") {
                        if ignored.len() >= 500 {
                            return Err("Ignore list is full".into());
                        }
                        ignored.insert(id);
                    } else {
                        ignored.remove(&id);
                    }
                    lines.push("Local scoped filter updated".into());
                }
            }
            "/highlight" => {
                let (action, value) = split_head(args);
                let value = value.to_lowercase();
                match action.to_ascii_lowercase().as_str() {
                    "add"
                        if !value.is_empty()
                            && value.len() <= 128
                            && !value.chars().any(char::is_control) =>
                    {
                        if prefs.highlights.len() >= 64 {
                            return Err("Highlight limit reached".into());
                        }
                        prefs.highlights.insert(value);
                    }
                    "remove" => {
                        prefs.highlights.remove(&value);
                    }
                    "list" | "" => {}
                    _ => {
                        return Err(
                            "Use /highlight add text|remove text|list (up to 128 bytes)".into()
                        )
                    }
                }
                lines.extend(prefs.highlights.iter().cloned());
            }
            "/alias" | "/unalias" => {
                let (name, expansion) = split_head(args);
                if name.is_empty() && command.eq_ignore_ascii_case("/alias") {
                    lines.extend(
                        prefs
                            .aliases
                            .iter()
                            .map(|(name, expansion)| format!("{name} {expansion}")),
                    );
                } else {
                    let name = format!("/{}", name.trim_start_matches('/').to_ascii_lowercase());
                    if name.len() < 2
                        || name.len() > 33
                        || !name[1..]
                            .bytes()
                            .all(|b| b.is_ascii_alphanumeric() || b == b'-')
                    {
                        return Err("Use an alias name of 1–32 letters, numbers or dashes".into());
                    }
                    if command.eq_ignore_ascii_case("/unalias") {
                        prefs.aliases.remove(&name);
                    } else {
                        if self
                            .context_commands(conversation)
                            .iter()
                            .any(|c| c.name == name)
                            || hosted::commands()
                                .iter()
                                .chain(contacts::commands().iter())
                                .any(|c| c.name == name)
                        {
                            return Err("An alias cannot replace a built-in command".into());
                        }
                        // Credential and lifecycle commands require their explicit native flows.
                        let target = split_head(expansion).0.to_ascii_lowercase();
                        if !matches!(
                            target.as_str(),
                            "/say"
                                | "/me"
                                | "/notice"
                                | "/who"
                                | "/whois"
                                | "/names"
                                | "/topic"
                                | "/away"
                                | "/back"
                                | "/ping"
                                | "/help"
                                | "/status"
                                | "/refresh"
                        ) || expansion.len() > 1024
                            || expansion.contains(['\n', '\r', '\0'])
                        {
                            return Err(
                                "Choose one chat or information command, up to 1024 bytes".into()
                            );
                        }
                        if prefs.aliases.len() >= 64 {
                            return Err("Alias limit reached".into());
                        }
                        prefs.aliases.insert(name, expansion.into());
                    }
                    lines.push("Local aliases updated".into());
                }
            }
            _ => return Err("Unknown preference command".into()),
        }
        current.store.save(&candidate)?;
        current.state = candidate;
        self.invalidate();
        Ok(Response::Output {
            conversation: conversation.map(str::to_owned),
            output: gchat_api::CommandOutput::Text {
                title: "Local preferences".into(),
                text: if lines.is_empty() {
                    "None".into()
                } else {
                    lines.join("\n")
                },
            },
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn filters_never_link_channels_and_alias_arguments_remain_literal() {
        let mut prefs = Preferences::default();
        prefs
            .ignored
            .entry("hosted/a".into())
            .or_default()
            .insert("member".into());
        assert!(prefs.ignores("hosted/a", Some("member"), false));
        assert!(!prefs.ignores("hosted/b", Some("member"), false));
        assert!(!prefs.ignores("hosted/a", Some("member"), true));
        prefs.aliases.insert("/wave".into(), "/me waves".into());
        assert_eq!(
            prefs.expand("/WAVE /part; $(exit)").unwrap(),
            "/me waves /part; $(exit)"
        );
        assert_eq!(prefs.expand("normal text").unwrap(), "normal text");
    }
}
