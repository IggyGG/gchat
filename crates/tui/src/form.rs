//! Multi-field wizards for unlock and channel flows.
//! `resolve` turns a submitted form into a command; it is pure and tested.

use crate::input::LineEdit;
use gchat_core::client::b64_decode;
use gcoms::sdk::ChannelId;
use std::path::Path;

/// Shortest passphrase accepted when creating a profile or archive.
pub const MIN_PASSPHRASE_CHARS: usize = 8;

/// Where Esc / a successful submit returns to.
#[derive(Clone, Debug, PartialEq)]
pub enum Back {
    Home,
    NewMenu,
    Channel(ChannelId),
    Quit,
}

#[derive(Clone, Debug, PartialEq)]
pub enum Action {
    Unlock { create: bool },
    CreateChannel,
    JoinWithInvite,
    JoinBegin,
    JoinFinish { req_id: u64, display: String },
    Admit,
    Publish { channel_id: ChannelId },
}

/// What the unlock form is protecting.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum UnlockMode {
    /// New identity + archive in this process.
    CreateProfile,
    /// Existing profile in this process.
    UnlockProfile,
    /// A daemon holds the identity; this passphrase protects a new archive.
    CreateArchive,
    /// A daemon holds the identity; open the existing archive.
    UnlockArchive,
}

impl UnlockMode {
    pub fn creates(self) -> bool {
        matches!(self, Self::CreateProfile | Self::CreateArchive)
    }
}

/// How a field is edited and rendered.
#[derive(Clone, Debug, PartialEq)]
pub enum FieldKind {
    Text,
    /// A fixed set of options cycled with Space/Left/Right.
    Toggle {
        options: &'static [&'static str],
        index: usize,
    },
}

#[derive(Clone, Debug)]
pub struct Field {
    pub label: String,
    pub edit: LineEdit,
    pub kind: FieldKind,
}

impl Field {
    /// The submitted value: typed text, or the selected toggle option.
    pub fn value(&self) -> String {
        match &self.kind {
            FieldKind::Text => self.edit.value.trim().to_string(),
            FieldKind::Toggle { options, index } => {
                options.get(*index).copied().unwrap_or("").to_string()
            }
        }
    }

    pub fn is_toggle(&self) -> bool {
        matches!(self.kind, FieldKind::Toggle { .. })
    }

    pub fn cycle(&mut self, forward: bool) {
        if let FieldKind::Toggle { options, index } = &mut self.kind {
            let len = options.len().max(1);
            *index = if forward {
                (*index + 1) % len
            } else {
                (*index + len - 1) % len
            };
        }
    }
}

#[derive(Clone, Debug)]
pub struct Form {
    pub title: String,
    pub help: Vec<String>,
    pub fields: Vec<Field>,
    pub focus: usize,
    pub action: Action,
    pub back: Back,
}

/// A validated form submission, ready to run against the core.
#[derive(Clone, Debug, PartialEq)]
pub enum WizardCmd {
    Unlock {
        create: bool,
        pass: String,
    },
    CreateChannel {
        channel: String,
        display: String,
        capacity: usize,
        public: bool,
    },
    JoinBegin {
        display: String,
    },
    JoinWithInvite {
        link: String,
        display: String,
    },
    JoinFinish {
        req_id: u64,
        channel: String,
        display: String,
        welcome: Vec<u8>,
    },
    Admit {
        channel: String,
        member: String,
        key_package: Vec<u8>,
    },
    Publish {
        channel_id: ChannelId,
        description: String,
        catalog: String,
    },
}

/// Largest file a blob field will read in place of a pasted value.
const MAX_BLOB_FILE_BYTES: u64 = 256 * 1024;

/// A blob field may hold the path of a file (an outbox export, a download)
/// instead of the blob itself: phones and remote terminals mangle long
/// pastes, but a path is short. Base64 never contains `/` or `\\` and
/// never starts with `~`, so a value that does is treated as a path.
pub fn expand_blob_file(value: &str) -> Result<String, String> {
    let trimmed = value.trim();
    let looks_like_path = trimmed.starts_with('~')
        || trimmed.starts_with('/')
        || trimmed.starts_with("./")
        || trimmed.contains('\\')
        || (trimmed.len() > 1 && trimmed.as_bytes()[1] == b':');
    if !looks_like_path {
        return Ok(trimmed.to_string());
    }
    let path = if let Some(rest) = trimmed.strip_prefix("~/") {
        match std::env::var_os("HOME") {
            Some(home) => std::path::PathBuf::from(home).join(rest),
            None => std::path::PathBuf::from(trimmed),
        }
    } else {
        std::path::PathBuf::from(trimmed)
    };
    let metadata = std::fs::metadata(&path)
        .map_err(|error| format!("cannot read {}: {error}", path.display()))?;
    if !metadata.is_file() {
        return Err(format!("{} is not a file", path.display()));
    }
    if metadata.len() > MAX_BLOB_FILE_BYTES {
        return Err(format!("{} is larger than 256 KiB", path.display()));
    }
    let text = std::fs::read_to_string(&path)
        .map_err(|error| format!("cannot read {}: {error}", path.display()))?;
    Ok(text.chars().filter(|c| !c.is_whitespace()).collect())
}

fn field(label: &str, secret: bool, compact: bool) -> Field {
    Field {
        label: label.into(),
        edit: LineEdit::new(secret, compact),
        kind: FieldKind::Text,
    }
}

fn toggle(label: &str, options: &'static [&'static str]) -> Field {
    Field {
        label: label.into(),
        edit: LineEdit::default(),
        kind: FieldKind::Toggle { options, index: 0 },
    }
}

impl Form {
    /// The passphrase form. `location` names the file being created or
    /// opened; `runtime` describes where the identity lives (shown as-is).
    pub fn unlock(mode: UnlockMode, location: &Path, runtime: &str) -> Form {
        let create = mode.creates();
        let mut help = vec!["gchat — GC/1 secure chat".to_string()];
        match mode {
            UnlockMode::CreateProfile => {
                help.push(format!(
                    "No profile found. This creates a NEW identity at {}.",
                    location.display()
                ));
                help.push(format!(
                    "Choose a passphrase of at least {MIN_PASSPHRASE_CHARS} characters."
                ));
                help.push(
                    "There is no recovery: losing it loses this identity and its history.".into(),
                );
            }
            UnlockMode::UnlockProfile => {
                help.push(format!("profile: {}", location.display()));
                help.push("Enter your passphrase to unlock (a few seconds on phones).".into());
            }
            UnlockMode::CreateArchive => {
                help.push(format!("Your identity lives in the daemon at {runtime}."));
                help.push(format!(
                    "This passphrase protects the local chat archive at {}.",
                    location.display()
                ));
                help.push(format!("Use at least {MIN_PASSPHRASE_CHARS} characters."));
            }
            UnlockMode::UnlockArchive => {
                help.push(format!("daemon: {runtime}"));
                help.push(format!("archive: {}", location.display()));
                help.push("Enter the archive passphrase to unlock.".into());
            }
        }
        if !runtime.is_empty()
            && matches!(mode, UnlockMode::CreateProfile | UnlockMode::UnlockProfile)
        {
            help.push(runtime.to_string());
        }
        let mut fields = vec![field("passphrase", true, false)];
        if create {
            fields.push(field("confirm", true, false));
        }
        Form {
            title: if create { "create profile" } else { "unlock" }.into(),
            help,
            fields,
            focus: 0,
            action: Action::Unlock { create },
            back: Back::Quit,
        }
    }

    pub fn create_channel() -> Form {
        Form {
            title: "create channel".into(),
            help: vec![
                "You become the owner. You let each new member in.".into(),
                "Your display name is shown inside this channel only.".into(),
                "Private channels never appear in catalogs; public ones can be published.".into(),
            ],
            fields: vec![
                field("channel", false, false),
                field("display name", false, false),
                field("capacity (64)", false, false),
                toggle("visibility", &["private", "public"]),
            ],
            focus: 0,
            action: Action::CreateChannel,
            back: Back::NewMenu,
        }
    }

    pub fn join_with_invite() -> Form {
        Form {
            title: "join with invite".into(),
            help: vec![
                "Paste the invite link a friend sent you, and pick a display name.".into(),
                "Your app does the rest — you do not need the owner's address.".into(),
                "If the owner is offline it keeps trying for a couple of minutes.".into(),
                "(You can also give the path of a file holding the link.)".into(),
            ],
            fields: vec![
                field("invite link", false, true),
                field("your display name", false, false),
            ],
            focus: 0,
            action: Action::JoinWithInvite,
            back: Back::NewMenu,
        }
    }

    pub fn join_begin() -> Form {
        Form {
            title: "join private channel (1/2)".into(),
            help: vec![
                "Step 1 makes a join request to send to the channel owner.".into(),
                "Step 2 pastes the invite code the owner sends back.".into(),
                "Your display name is shown inside the channel.".into(),
            ],
            fields: vec![field("display name", false, false)],
            focus: 0,
            action: Action::JoinBegin,
            back: Back::NewMenu,
        }
    }

    pub fn join_finish(req_id: u64, display: &str) -> Form {
        Form {
            title: "join private channel (2/2)".into(),
            help: vec![
                format!("request #{req_id} as {display}"),
                "Type the exact channel name, then paste the invite code the owner sent".into(),
                "(or the path of a file holding it).".into(),
                "Esc keeps this request while gchat runs; quitting discards it, and the".into(),
                "owner would then have to let in a fresh join request.".into(),
            ],
            fields: vec![
                field("channel", false, false),
                field("invite code", false, true),
            ],
            focus: 0,
            action: Action::JoinFinish {
                req_id,
                display: display.into(),
            },
            back: Back::NewMenu,
        }
    }

    pub fn admit() -> Form {
        Form {
            title: "let a member in".into(),
            help: vec![
                "Paste the join request a prospective member sent you, or type the path".into(),
                "of a file that holds it (e.g. ~/Downloads/join-request.txt).".into(),
                "You get back an invite code to send them; only they can use it.".into(),
            ],
            fields: vec![
                field("channel", false, false),
                field("member name", false, false),
                field("join request", false, true),
            ],
            focus: 0,
            action: Action::Admit,
            back: Back::NewMenu,
        }
    }

    pub fn publish(channel_id: ChannelId) -> Form {
        Form {
            title: "publish public channel".into(),
            help: vec![
                "Publish a locally signed descriptor to a credential-free catalog.".into(),
                "Only public channel owners can publish.".into(),
            ],
            fields: vec![
                field("description", false, false),
                field("catalog HTTPS URL", false, false),
            ],
            focus: 0,
            action: Action::Publish { channel_id },
            back: Back::Channel(channel_id),
        }
    }

    pub fn current(&self) -> &Field {
        &self.fields[self.focus.min(self.fields.len().saturating_sub(1))]
    }

    pub fn current_mut(&mut self) -> &mut Field {
        if self.focus >= self.fields.len() {
            self.focus = 0;
        }
        &mut self.fields[self.focus]
    }

    pub fn next(&mut self) {
        self.focus = (self.focus + 1) % self.fields.len();
    }

    pub fn prev(&mut self) {
        self.focus = (self.focus + self.fields.len() - 1) % self.fields.len();
    }

    pub fn on_last(&self) -> bool {
        self.focus + 1 == self.fields.len()
    }

    /// Validate the field values into a command. Pure; no core calls.
    pub fn resolve(&self) -> Result<WizardCmd, String> {
        let v: Vec<String> = self.fields.iter().map(Field::value).collect();
        let need = |i: usize, what: &str| -> Result<String, String> {
            let s = v.get(i).cloned().unwrap_or_default();
            if s.is_empty() {
                Err(format!("{what} required"))
            } else {
                Ok(s)
            }
        };
        let blob = |i: usize, what: &str| -> Result<Vec<u8>, String> {
            let s = expand_blob_file(&need(i, what)?)?;
            b64_decode(&s).ok_or_else(|| format!("{what} is not valid base64"))
        };
        match &self.action {
            Action::Unlock { create } => {
                let pass = need(0, "passphrase")?;
                if *create {
                    if pass.chars().count() < MIN_PASSPHRASE_CHARS {
                        return Err(format!(
                            "passphrase must be at least {MIN_PASSPHRASE_CHARS} characters"
                        ));
                    }
                    if v.get(1) != v.first() {
                        return Err("passphrases do not match".into());
                    }
                }
                Ok(WizardCmd::Unlock {
                    create: *create,
                    pass,
                })
            }
            Action::CreateChannel => {
                let channel = need(0, "channel")?;
                if channel.starts_with('#') {
                    return Err("channel name without the leading #".into());
                }
                if channel.chars().any(char::is_whitespace) {
                    return Err("channel name cannot contain spaces".into());
                }
                if channel.chars().count() > 64 {
                    return Err("channel name must be 64 characters or fewer".into());
                }
                let display = need(1, "display name")?;
                let capacity = if v.get(2).map(|s| s.is_empty()).unwrap_or(true) {
                    64
                } else {
                    v[2].parse::<usize>()
                        .map_err(|_| "capacity must be a number")?
                };
                if capacity == 0 {
                    return Err("capacity must be > 0".into());
                }
                let public = match need(3, "visibility")?.to_ascii_lowercase().as_str() {
                    "public" => true,
                    "private" => false,
                    _ => return Err("visibility must be public or private".into()),
                };
                Ok(WizardCmd::CreateChannel {
                    channel,
                    display,
                    capacity,
                    public,
                })
            }
            Action::JoinWithInvite => {
                // The link may be pasted directly, or given as a file path.
                let link = expand_blob_file(&need(0, "invite link")?)?;
                if link.is_empty() {
                    return Err("invite link required".into());
                }
                Ok(WizardCmd::JoinWithInvite {
                    link,
                    display: need(1, "your display name")?,
                })
            }
            Action::JoinBegin => Ok(WizardCmd::JoinBegin {
                display: need(0, "display name")?,
            }),
            Action::JoinFinish { req_id, display } => Ok(WizardCmd::JoinFinish {
                req_id: *req_id,
                channel: need(0, "channel")?.trim_start_matches('#').to_string(),
                display: display.clone(),
                welcome: blob(1, "invite code")?,
            }),
            Action::Admit => Ok(WizardCmd::Admit {
                channel: need(0, "channel")?.trim_start_matches('#').to_string(),
                member: need(1, "member name")?,
                key_package: blob(2, "join request")?,
            }),
            Action::Publish { channel_id } => Ok(WizardCmd::Publish {
                channel_id: *channel_id,
                description: need(0, "description")?,
                catalog: need(1, "catalog URL")?,
            }),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use gchat_core::client::b64_encode;

    fn fill(form: &mut Form, values: &[&str]) {
        for (f, v) in form.fields.iter_mut().zip(values) {
            match &mut f.kind {
                FieldKind::Text => f.edit.value = v.to_string(),
                FieldKind::Toggle { options, index } => {
                    *index = options.iter().position(|o| o == v).expect("known option");
                }
            }
        }
    }

    #[test]
    fn unlock_requires_match_and_length_on_create() {
        let mut f = Form::unlock(UnlockMode::CreateProfile, Path::new("/tmp/x"), "");
        assert_eq!(f.title, "create profile");
        assert!(f.help.iter().any(|line| line.contains("NEW identity")));
        fill(&mut f, &["pw1", "pw2"]);
        assert_eq!(
            f.resolve().unwrap_err(),
            "passphrase must be at least 8 characters"
        );
        fill(&mut f, &["long-pass-1", "long-pass-2"]);
        assert_eq!(f.resolve().unwrap_err(), "passphrases do not match");
        fill(&mut f, &["long-pass-1", "long-pass-1"]);
        assert_eq!(
            f.resolve().unwrap(),
            WizardCmd::Unlock {
                create: true,
                pass: "long-pass-1".into()
            }
        );
    }

    #[test]
    fn unlock_rejects_empty_passphrase_but_not_short_existing_ones() {
        let mut f = Form::unlock(UnlockMode::UnlockProfile, Path::new("/tmp/x"), "");
        assert_eq!(f.title, "unlock");
        assert_eq!(f.fields.len(), 1);
        fill(&mut f, &[""]);
        assert_eq!(f.resolve().unwrap_err(), "passphrase required");
        fill(&mut f, &["pw"]);
        assert!(f.resolve().is_ok(), "old short passphrases still unlock");
    }

    #[test]
    fn archive_modes_name_the_daemon() {
        let f = Form::unlock(
            UnlockMode::CreateArchive,
            Path::new("/tmp/chat.gcarchive"),
            "/run/gcd.sock",
        );
        assert!(f.help.iter().any(|line| line.contains("/run/gcd.sock")));
        assert_eq!(f.fields.len(), 2);
        let f = Form::unlock(
            UnlockMode::UnlockArchive,
            Path::new("/tmp/chat.gcarchive"),
            "/run/gcd.sock",
        );
        assert_eq!(f.fields.len(), 1);
    }

    #[test]
    fn create_channel_toggle_defaults_private() {
        let mut f = Form::create_channel();
        assert!(f.fields[3].is_toggle());
        assert_eq!(f.fields[3].value(), "private");
        fill(&mut f, &["ops", "ghost-1", ""]);
        assert_eq!(
            f.resolve().unwrap(),
            WizardCmd::CreateChannel {
                channel: "ops".into(),
                display: "ghost-1".into(),
                capacity: 64,
                public: false
            }
        );
        f.fields[3].cycle(true);
        assert_eq!(f.fields[3].value(), "public");
        f.fields[3].cycle(true);
        assert_eq!(f.fields[3].value(), "private");
        f.fields[3].cycle(false);
        assert_eq!(f.fields[3].value(), "public");
        fill(&mut f, &["ops", "ghost-1", "abc", "private"]);
        assert_eq!(f.resolve().unwrap_err(), "capacity must be a number");
        fill(&mut f, &["ops", "ghost-1", "0", "private"]);
        assert_eq!(f.resolve().unwrap_err(), "capacity must be > 0");
        fill(&mut f, &["ops", "ghost-1", "128", "public"]);
        assert_eq!(
            f.resolve().unwrap(),
            WizardCmd::CreateChannel {
                channel: "ops".into(),
                display: "ghost-1".into(),
                capacity: 128,
                public: true
            }
        );
    }

    #[test]
    fn create_channel_validates_the_name() {
        let mut f = Form::create_channel();
        fill(&mut f, &["#ops", "me", "", "private"]);
        assert!(f.resolve().unwrap_err().contains("leading #"));
        fill(&mut f, &["op s", "me", "", "private"]);
        assert!(f.resolve().unwrap_err().contains("spaces"));
        fill(&mut f, &[&"x".repeat(65), "me", "", "private"]);
        assert!(f.resolve().unwrap_err().contains("64"));
    }

    #[test]
    fn join_finish_decodes_welcome_and_strips_hash() {
        let mut f = Form::join_finish(42, "ghost-1");
        assert!(f.help[0].contains("#42"));
        fill(&mut f, &["ops", "%%%"]);
        assert!(f.resolve().unwrap_err().contains("base64"));
        fill(&mut f, &["#ops", &b64_encode(b"welcome-bytes")]);
        assert_eq!(
            f.resolve().unwrap(),
            WizardCmd::JoinFinish {
                req_id: 42,
                channel: "ops".into(),
                display: "ghost-1".into(),
                welcome: b"welcome-bytes".to_vec()
            }
        );
    }

    #[test]
    fn join_with_invite_takes_a_link_and_display() {
        let mut f = Form::join_with_invite();
        // Missing link is rejected.
        fill(&mut f, &["", "alice"]);
        assert!(f.resolve().is_err());
        fill(&mut f, &["ABC-invite_link", "alice"]);
        assert_eq!(
            f.resolve().unwrap(),
            WizardCmd::JoinWithInvite {
                link: "ABC-invite_link".into(),
                display: "alice".into(),
            }
        );
    }

    #[test]
    fn blob_fields_accept_a_file_path() {
        let dir = tempfile::tempdir().unwrap();
        let file = dir.path().join("kp.txt");
        std::fs::write(&file, format!("{}\n", b64_encode(b"kp-from-file"))).unwrap();
        let mut f = Form::admit();
        fill(&mut f, &["ops", "ada", file.to_str().unwrap()]);
        assert_eq!(
            f.resolve().unwrap(),
            WizardCmd::Admit {
                channel: "ops".into(),
                member: "ada".into(),
                key_package: b"kp-from-file".to_vec()
            }
        );
        fill(&mut f, &["ops", "ada", "/definitely/missing.txt"]);
        assert!(f.resolve().unwrap_err().contains("cannot read"));
        assert_eq!(expand_blob_file(" QUJD ").unwrap(), "QUJD");
    }

    #[test]
    fn admit_decodes_key_package() {
        let mut f = Form::admit();
        fill(&mut f, &["ops", "ada", "not-base64!"]);
        assert!(f.resolve().unwrap_err().contains("base64"));
        fill(&mut f, &["ops", "ada", &b64_encode(b"kp")]);
        assert_eq!(
            f.resolve().unwrap(),
            WizardCmd::Admit {
                channel: "ops".into(),
                member: "ada".into(),
                key_package: b"kp".to_vec()
            }
        );
    }

    #[test]
    fn publish_returns_to_its_channel() {
        let f = Form::publish(ChannelId([7; 32]));
        assert_eq!(f.back, Back::Channel(ChannelId([7; 32])));
    }

    #[test]
    fn focus_wraps_around() {
        let mut f = Form::admit();
        assert_eq!(f.focus, 0);
        f.prev();
        assert_eq!(f.focus, 2);
        f.next();
        assert_eq!(f.focus, 0);
        assert!(!f.on_last());
        f.prev();
        assert!(f.on_last());
    }
}
