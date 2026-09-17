//! Application state: screens, key handling and command results.
//! Everything here is synchronous and testable without a terminal or a node.

use crate::form::{Back, Form, UnlockMode};
use crate::input::LineEdit;
use crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use gchat_core::client::{b64_encode, ClientHandle, NodeEvent};
use gchat_core::model::{HomeId, HomeItem, MemberId, ScopedPmId};
use gcoms_sdk::{ChannelId, ChannelRole, PublicChannelDescriptor};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::time::Instant;

const SAVE_TICKS: u64 = 120;
/// Info/Ok status lines disappear after this many ticks (250 ms each).
const STATUS_TICKS: u64 = 32;
/// Keys closer together than this are treated as a paste in blob fields.
const PASTE_BURST_MS: u128 = 40;

#[derive(Clone, Debug, Default)]
pub enum Screen {
    Unlock(Form),
    #[default]
    Home,
    Help,
    Legacy,
    NewMenu {
        sel: usize,
    },
    Form(Form),
    Info {
        title: String,
        body: Vec<String>,
        /// What `y` copies (and `e` exports).
        copy: Option<String>,
        /// Base name for the outbox file.
        export_name: &'static str,
        next: Box<Screen>,
    },
    Channel {
        id: ChannelId,
    },
    ScopedPm {
        id: ScopedPmId,
    },
    Public {
        descriptor: PublicChannelDescriptor,
    },
}

/// Rows of the New menu, static entries plus one per pending join.
#[derive(Clone, Debug, PartialEq)]
pub enum NewAction {
    CreateChannel,
    JoinWithInvite,
    JoinBegin,
    Admit,
    FinishJoin(u64),
    ShowKeyPackage(u64),
}

#[derive(Debug)]
pub enum Cmd {
    Spawn(crate::form::WizardCmd),
    SendChannel {
        id: ChannelId,
        text: String,
    },
    SendPm {
        id: ScopedPmId,
        text: String,
    },
    JoinPublic {
        descriptor: PublicChannelDescriptor,
        display: String,
    },
    /// Owner: mint a single-use invite link for the given channel.
    CreateInvite {
        id: ChannelId,
        name: String,
    },
    RemoveMember {
        channel: ChannelId,
        member: MemberId,
    },
    Save {
        manual: bool,
    },
    /// Re-fetch catalogs and retry a failed relay bootstrap.
    Refresh,
    Copy(String),
    Export {
        name: &'static str,
        text: String,
    },
    Quit,
}

/// Where the identity for this session lives.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RuntimeKind {
    /// Protocol runtime hosted inside this process.
    Hosted,
    /// Attached to a daemon over the socket at the given path.
    Daemon(PathBuf),
    /// Legacy combined store (`--store` without a daemon).
    Embedded,
}

/// Result of the relay bootstrap for this session.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum RelayState {
    /// No relay configured (`--no-relay` or nothing compiled in).
    None,
    /// A relay card was supplied or fetched.
    Ready(String),
    /// Bootstrap failed; the node runs without a relay.
    Failed(String),
    /// Identity lives in a daemon; the relay is its business.
    Daemon,
}

/// Everything a successful unlock hands the UI.
pub struct Unlocked {
    pub client: ClientHandle,
    pub runtime: RuntimeKind,
    pub relay: RelayState,
    pub catalog_warning: Option<String>,
}

pub enum OpDone {
    Unlock(Result<Unlocked, String>),
    Sent {
        text: String,
        res: Result<(), String>,
    },
    PublicJoined {
        descriptor: PublicChannelDescriptor,
        display: String,
        res: Result<(), String>,
    },
    ChannelCreated {
        channel: String,
        res: Result<ChannelId, String>,
    },
    Wizard {
        back: Back,
        res: Result<String, String>,
    },
    JoinPrepared {
        display: String,
        res: Result<(u64, Vec<u8>), String>,
    },
    Admitted {
        res: Result<Vec<u8>, String>,
    },
    JoinFinished {
        req_id: u64,
        channel: String,
        res: Result<(), String>,
    },
    /// An invite link was minted for a channel the user owns.
    InviteCreated {
        channel: String,
        res: Result<String, String>,
    },
    /// An invite-link redemption finished; `Ok` is the joined channel name.
    InviteJoined {
        res: Result<String, String>,
    },
    /// A relay retry finished; `Ok` makes the host reopen with the card.
    RelayFetched(Result<String, String>),
    /// A one-line outcome that does not change the screen.
    Notice(Result<String, String>),
    /// A background problem from the hosted runtime.
    Warning(String),
    Saved {
        res: Result<(), String>,
        manual: bool,
    },
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum ChannelFocus {
    Members,
    #[default]
    Message,
}

/// Status line severity. Info/Ok fade; Warn/Err stay until the next key.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum StatusKind {
    #[default]
    Info,
    Ok,
    Warn,
    Err,
}

/// A destructive action waiting for `y`.
#[derive(Clone, Debug, PartialEq)]
pub enum Confirm {
    RemoveMember {
        channel: ChannelId,
        member: MemberId,
        name: String,
    },
    QuitWithPendingJoins,
}

/// A private join started in this session and not yet finished.
#[derive(Clone, Debug, PartialEq)]
pub struct PendingJoin {
    pub req_id: u64,
    pub display: String,
    pub package_b64: String,
}

/// Static facts about this session shown on the identity screen.
#[derive(Clone, Debug, Default)]
pub struct SessionInfo {
    pub profile: Option<PathBuf>,
    pub archive: Option<PathBuf>,
    pub outbox: Option<PathBuf>,
}

pub struct App {
    pub client: Option<ClientHandle>,
    pub screen: Screen,
    pub status: String,
    pub status_kind: StatusKind,
    status_tick: u64,
    pub pending_changes: bool,
    pub home_sel: usize,
    pub member_sel: usize,
    pub channel_focus: ChannelFocus,
    pub input: LineEdit,
    pub scroll: u16,
    pub confirm: Option<Confirm>,
    pub pending_joins: Vec<PendingJoin>,
    pub runtime: Option<RuntimeKind>,
    pub relay: RelayState,
    pub session: SessionInfo,
    /// Terminal size from the last resize event (0 = unknown).
    pub size: (u16, u16),
    /// Explicit paste mode for terminals without bracketed paste.
    pub paste_mode: bool,
    /// Render without colour (NO_COLOR, dumb terminals, --mono).
    pub mono: bool,
    seen: HashMap<HomeId, usize>,
    selected_home: Option<HomeId>,
    selected_member: Option<MemberId>,
    last_key_at: Option<Instant>,
    ticks: u64,
    cmds: Vec<Cmd>,
    pub quit: bool,
}

impl App {
    /// A fresh app showing the passphrase form. `location` is the file the
    /// passphrase protects; `runtime` is a free-text line for the form.
    pub fn new(mode: UnlockMode, location: &Path, runtime: &str) -> Self {
        Self {
            client: None,
            screen: Screen::Unlock(Form::unlock(mode, location, runtime)),
            status: String::new(),
            status_kind: StatusKind::Info,
            status_tick: 0,
            pending_changes: false,
            home_sel: 0,
            member_sel: 0,
            channel_focus: ChannelFocus::Message,
            input: LineEdit::default(),
            scroll: 0,
            confirm: None,
            pending_joins: Vec::new(),
            runtime: None,
            relay: RelayState::None,
            session: SessionInfo::default(),
            size: (0, 0),
            paste_mode: false,
            mono: false,
            seen: HashMap::new(),
            selected_home: None,
            selected_member: None,
            last_key_at: None,
            ticks: 0,
            cmds: Vec::new(),
            quit: false,
        }
    }

    /// Set the status line. Info/Ok expire; Warn/Err persist.
    pub fn set_status(&mut self, value: String, kind: StatusKind) {
        self.status = value;
        self.status_kind = kind;
        self.status_tick = self.ticks;
    }
    pub fn info(&mut self, value: impl Into<String>) {
        self.set_status(value.into(), StatusKind::Info);
    }
    pub fn ok(&mut self, value: impl Into<String>) {
        self.set_status(value.into(), StatusKind::Ok);
    }
    pub fn warn(&mut self, value: impl Into<String>) {
        self.set_status(value.into(), StatusKind::Warn);
    }
    pub fn err(&mut self, value: impl Into<String>) {
        self.set_status(value.into(), StatusKind::Err);
    }
    pub fn drain_cmds(&mut self) -> Vec<Cmd> {
        std::mem::take(&mut self.cmds)
    }
    pub fn home_items(&self) -> Vec<HomeItem> {
        self.client
            .as_ref()
            .map_or_else(Vec::new, ClientHandle::home_items)
    }
    /// True when a home row has messages the user has not looked at.
    pub fn is_unread(&self, item: &HomeItem) -> bool {
        let count = match item {
            HomeItem::Joined(channel) => channel.messages.len(),
            HomeItem::ScopedPm(pm) => pm.messages.len(),
            HomeItem::Public(_) => return false,
        };
        count > self.seen.get(&item.id()).copied().unwrap_or(0)
    }
    /// Rows of the New menu for the current session.
    pub fn new_menu(&self) -> Vec<(String, String, NewAction)> {
        let mut rows = vec![
            (
                "create channel".into(),
                "you become the owner".into(),
                NewAction::CreateChannel,
            ),
            (
                "join with invite".into(),
                "paste an invite link a friend sent you".into(),
                NewAction::JoinWithInvite,
            ),
            (
                "join private channel (advanced)".into(),
                "manual: get a join request to send the owner".into(),
                NewAction::JoinBegin,
            ),
            (
                "let a member in (advanced)".into(),
                "manual: paste a join request, get an invite code".into(),
                NewAction::Admit,
            ),
        ];
        for pending in &self.pending_joins {
            rows.push((
                format!("complete join #{}", pending.req_id),
                format!("paste the invite code for {}", pending.display),
                NewAction::FinishJoin(pending.req_id),
            ));
            rows.push((
                format!("show join request #{}", pending.req_id),
                "copy or export it again".into(),
                NewAction::ShowKeyPackage(pending.req_id),
            ));
        }
        rows
    }
    fn key_package_screen(&self, pending: &PendingJoin) -> Screen {
        Screen::Info {
            title: format!("join request #{} ({})", pending.req_id, pending.display),
            body: vec![
                "Send this join request to the channel owner (y copies, e exports a file).".into(),
                "Then wait for the invite code and complete the join from New.".into(),
                "A paste field also takes the path of a file holding it (e.g. ~/Downloads/invite-code.txt)."
                    .into(),
                String::new(),
                pending.package_b64.clone(),
            ],
            copy: Some(pending.package_b64.clone()),
            export_name: "join-request",
            next: Box::new(Screen::Form(Form::join_finish(
                pending.req_id,
                &pending.display,
            ))),
        }
    }
    pub fn on_paste(&mut self, raw: &str) {
        match &mut self.screen {
            Screen::Unlock(form) | Screen::Form(form) => {
                let field = form.current_mut();
                if !field.is_toggle() {
                    field.edit.paste(raw);
                }
            }
            Screen::Channel { .. } if self.channel_focus == ChannelFocus::Message => {
                self.input.paste(raw)
            }
            Screen::ScopedPm { .. } | Screen::Public { .. } => self.input.paste(raw),
            _ => {}
        }
    }
    pub fn on_resize(&mut self, width: u16, height: u16) {
        self.size = (width, height);
    }
    pub fn on_key(&mut self, key: KeyEvent) {
        self.on_key_at(key, Instant::now());
    }
    /// Key handling with an explicit clock so paste bursts are testable.
    pub fn on_key_at(&mut self, key: KeyEvent, now: Instant) {
        let burst = self
            .last_key_at
            .is_some_and(|last| now.duration_since(last).as_millis() < PASTE_BURST_MS);
        self.last_key_at = Some(now);
        if key.code == KeyCode::Char('c') && key.modifiers.contains(KeyModifiers::CONTROL) {
            self.cmds.push(Cmd::Quit);
            return;
        }
        if matches!(self.status_kind, StatusKind::Warn | StatusKind::Err) {
            // A key acknowledges a persistent status.
            self.status.clear();
            self.status_kind = StatusKind::Info;
        }
        if let Some(confirm) = self.confirm.take() {
            self.key_confirm(confirm, key);
            return;
        }
        let mut screen = std::mem::take(&mut self.screen);
        self.key_screen(&mut screen, key, burst);
        self.screen = screen;
    }
    fn key_confirm(&mut self, confirm: Confirm, key: KeyEvent) {
        match confirm {
            Confirm::QuitWithPendingJoins => {
                if key.code == KeyCode::Char('q') {
                    self.cmds.push(Cmd::Quit);
                } else {
                    self.info("staying; finish the join from New");
                }
            }
            Confirm::RemoveMember {
                channel,
                member,
                name,
            } => {
                if key.code == KeyCode::Char('y') {
                    self.info(format!("removing @{name}…"));
                    self.cmds.push(Cmd::RemoveMember { channel, member });
                } else {
                    self.info("cancelled");
                }
            }
        }
    }
    fn key_screen(&mut self, screen: &mut Screen, key: KeyEvent, burst: bool) {
        match screen.clone() {
            Screen::Channel { id } => {
                self.key_channel(screen, id, key);
                return;
            }
            Screen::ScopedPm { id } => {
                self.key_pm(screen, id, key);
                return;
            }
            Screen::Public { descriptor } => {
                self.key_public(screen, descriptor, key);
                return;
            }
            _ => {}
        }
        match screen {
            Screen::Unlock(form) | Screen::Form(form) => {
                if let Some(next) = self.key_form(form, key, burst) {
                    *screen = next;
                }
            }
            Screen::Home => self.key_home(screen, key),
            Screen::Help | Screen::Legacy => match key.code {
                KeyCode::Esc | KeyCode::Char('q') => *screen = Screen::Home,
                KeyCode::Up | KeyCode::Char('k') => self.scroll = self.scroll.saturating_sub(1),
                KeyCode::Down | KeyCode::Char('j') => self.scroll = self.scroll.saturating_add(1),
                _ => {}
            },
            Screen::NewMenu { sel } => {
                let rows = self.new_menu();
                match key.code {
                    KeyCode::Esc | KeyCode::Char('q') => *screen = Screen::Home,
                    KeyCode::Up | KeyCode::Char('k') => *sel = sel.saturating_sub(1),
                    KeyCode::Down | KeyCode::Char('j') => {
                        *sel = (*sel + 1).min(rows.len().saturating_sub(1))
                    }
                    KeyCode::Enter => {
                        if let Some((_, _, action)) = rows.get(*sel) {
                            *screen = match action {
                                NewAction::CreateChannel => Screen::Form(Form::create_channel()),
                                NewAction::JoinWithInvite => Screen::Form(Form::join_with_invite()),
                                NewAction::JoinBegin => Screen::Form(Form::join_begin()),
                                NewAction::Admit => Screen::Form(Form::admit()),
                                NewAction::FinishJoin(id) => {
                                    match self.pending_joins.iter().find(|p| p.req_id == *id) {
                                        Some(p) => {
                                            Screen::Form(Form::join_finish(p.req_id, &p.display))
                                        }
                                        None => Screen::Home,
                                    }
                                }
                                NewAction::ShowKeyPackage(id) => {
                                    match self.pending_joins.iter().find(|p| p.req_id == *id) {
                                        Some(p) => self.key_package_screen(p),
                                        None => Screen::Home,
                                    }
                                }
                            }
                        }
                    }
                    _ => {}
                }
            }
            Screen::Info {
                copy,
                next,
                body,
                export_name,
                ..
            } => match key.code {
                KeyCode::Esc | KeyCode::Enter | KeyCode::Char('q') => {
                    self.scroll = 0;
                    *screen = (**next).clone();
                }
                KeyCode::Char('y') => match copy {
                    Some(value) => self.cmds.push(Cmd::Copy(value.clone())),
                    None => self.info("nothing to copy on this screen"),
                },
                KeyCode::Char('e') => match copy {
                    Some(value) => self.cmds.push(Cmd::Export {
                        name: export_name,
                        text: value.clone(),
                    }),
                    None => self.info("nothing to export on this screen"),
                },
                KeyCode::Up | KeyCode::Char('k') => self.scroll = self.scroll.saturating_sub(1),
                KeyCode::Down | KeyCode::Char('j') => {
                    self.scroll = self.scroll.saturating_add(1).min(body.len() as u16 * 8)
                }
                KeyCode::PageUp => self.scroll = self.scroll.saturating_sub(10),
                KeyCode::PageDown => {
                    self.scroll = self.scroll.saturating_add(10).min(body.len() as u16 * 8)
                }
                _ => {}
            },
            Screen::Channel { .. } | Screen::ScopedPm { .. } | Screen::Public { .. } => {
                unreachable!("chat screens are dispatched above")
            }
        }
    }
    fn key_form(&mut self, form: &mut Form, key: KeyEvent, burst: bool) -> Option<Screen> {
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        let compact = form.current().edit.compact;
        // Terminals without bracketed paste deliver a pasted blob as a fast
        // key burst; embedded newlines/tabs must not submit or move focus.
        let pasting = self.paste_mode || (compact && burst);
        match key.code {
            KeyCode::Char('p') if ctrl => {
                self.paste_mode = !self.paste_mode;
                if self.paste_mode {
                    self.info("paste mode: Enter and Tab are ignored until Ctrl-P again");
                } else {
                    self.info("paste mode off");
                }
            }
            KeyCode::Esc => {
                if form.back == Back::Quit {
                    self.cmds.push(Cmd::Quit);
                    return None;
                }
                return Some(back_screen(form.back.clone()));
            }
            KeyCode::Tab | KeyCode::Down if !pasting => form.next(),
            KeyCode::Tab if pasting => {}
            KeyCode::BackTab | KeyCode::Up => form.prev(),
            KeyCode::Enter if pasting => {}
            KeyCode::Enter => {
                if form.on_last() {
                    match form.resolve() {
                        Ok(command) => self.cmds.push(Cmd::Spawn(command)),
                        Err(error) => self.err(error),
                    }
                } else {
                    form.next();
                }
            }
            KeyCode::Char(' ') | KeyCode::Right if form.current().is_toggle() => {
                form.current_mut().cycle(true)
            }
            KeyCode::Left if form.current().is_toggle() => form.current_mut().cycle(false),
            KeyCode::Backspace => form.current_mut().edit.backspace(),
            KeyCode::Delete => form.current_mut().edit.delete(),
            KeyCode::Left => form.current_mut().edit.left(),
            KeyCode::Right => form.current_mut().edit.right(),
            KeyCode::Home => form.current_mut().edit.home(),
            KeyCode::End => form.current_mut().edit.end(),
            KeyCode::Char('a') if ctrl => form.current_mut().edit.home(),
            KeyCode::Char('e') if ctrl => form.current_mut().edit.end(),
            KeyCode::Char('u') if ctrl => form.current_mut().edit.clear(),
            KeyCode::Char('w') if ctrl => form.current_mut().edit.delete_word(),
            KeyCode::Char(value) if !ctrl && !form.current().is_toggle() => {
                form.current_mut().edit.push(value)
            }
            _ => {}
        }
        None
    }
    fn key_home(&mut self, screen: &mut Screen, key: KeyEvent) {
        let items = self.home_items();
        match key.code {
            KeyCode::Up | KeyCode::Char('k') => self.home_sel = self.home_sel.saturating_sub(1),
            KeyCode::Down | KeyCode::Char('j') => {
                if !items.is_empty() {
                    self.home_sel = (self.home_sel + 1).min(items.len() - 1);
                }
            }
            KeyCode::Enter => {
                if let Some(item) = items.get(self.home_sel) {
                    self.input.clear();
                    self.scroll = 0;
                    self.channel_focus = ChannelFocus::Message;
                    self.selected_member = None;
                    self.mark_seen(item);
                    *screen = match item {
                        HomeItem::Joined(channel) => Screen::Channel { id: channel.id },
                        HomeItem::ScopedPm(pm) => Screen::ScopedPm { id: pm.id },
                        HomeItem::Public(public) => Screen::Public {
                            descriptor: public.descriptor.clone(),
                        },
                    };
                }
            }
            KeyCode::Char('n') => *screen = Screen::NewMenu { sel: 0 },
            KeyCode::Char('?') => {
                self.scroll = 0;
                *screen = Screen::Help;
            }
            KeyCode::Char('l') => {
                self.scroll = 0;
                *screen = Screen::Legacy;
            }
            KeyCode::Char('i') => {
                self.scroll = 0;
                *screen = self.identity_screen();
            }
            KeyCode::Char('r') => {
                if self.client.is_some() {
                    self.info("refreshing…");
                    self.cmds.push(Cmd::Refresh);
                }
            }
            KeyCode::Char('s') => self.cmds.push(Cmd::Save { manual: true }),
            KeyCode::Char('q') => {
                if self.has_pending_joins() && self.confirm.is_none() {
                    // Prepared joins live only in this process (the node does
                    // not persist key-package secrets), so warn once.
                    self.confirm = Some(Confirm::QuitWithPendingJoins);
                    self.warn(format!(
                        "{} pending join(s) will be lost on quit; press q again to quit, any other key to stay",
                        self.pending_joins.len()
                    ));
                } else {
                    self.cmds.push(Cmd::Quit);
                }
            }
            _ => {}
        }
        self.selected_home = items.get(self.home_sel).map(HomeItem::id);
    }
    fn mark_seen(&mut self, item: &HomeItem) {
        let count = match item {
            HomeItem::Joined(channel) => channel.messages.len(),
            HomeItem::ScopedPm(pm) => pm.messages.len(),
            HomeItem::Public(_) => return,
        };
        self.seen.insert(item.id(), count);
    }
    /// True when quitting would throw away a join the owner may already
    /// have approved.
    pub fn has_pending_joins(&self) -> bool {
        !self.pending_joins.is_empty()
    }
    /// The `i` screen: who you are and where things live.
    pub fn identity_screen(&self) -> Screen {
        let mut body = Vec::new();
        let mut copy = None;
        match &self.client {
            Some(client) => {
                let safety = client.safety_number().to_string();
                let grouped = safety
                    .chars()
                    .filter(|c| !c.is_whitespace())
                    .collect::<Vec<_>>()
                    .chunks(5)
                    .map(|chunk| chunk.iter().collect::<String>())
                    .collect::<Vec<_>>()
                    .join(" ");
                body.push(format!("safety number: {grouped}"));
                body.push("Compare it out-of-band with people you talk to.".into());
                body.push(String::new());
                body.push(format!("listen: {}", client.listen_addr()));
                let catalogs = client.catalog_urls();
                if catalogs.is_empty() {
                    body.push(
                        "catalogs: none (public channels hidden; add --catalog-url or GC_CATALOG_URLS)"
                            .into(),
                    );
                } else {
                    body.push(format!("catalogs: {}", catalogs.join(", ")));
                }
                copy = Some(safety);
            }
            None => body.push("not unlocked".into()),
        }
        body.push(match &self.runtime {
            Some(RuntimeKind::Hosted) => "runtime: in this process".to_string(),
            Some(RuntimeKind::Daemon(socket)) => {
                format!("runtime: daemon at {}", socket.display())
            }
            Some(RuntimeKind::Embedded) => "runtime: legacy embedded store".to_string(),
            None => "runtime: none".to_string(),
        });
        body.push(match &self.relay {
            RelayState::None => {
                "relay: none (awaiting an invite or saved routing information)".to_string()
            }
            RelayState::Ready(label) => format!("relay: {label}"),
            RelayState::Failed(reason) => format!("relay: FAILED ({reason}); press r on Home"),
            RelayState::Daemon => "relay: managed by the daemon".to_string(),
        });
        for (label, path) in [
            ("profile", &self.session.profile),
            ("archive", &self.session.archive),
            ("outbox", &self.session.outbox),
        ] {
            if let Some(path) = path {
                body.push(format!("{label}: {}", path.display()));
            }
        }
        body.push(format!("pending joins: {}", self.pending_joins.len()));
        body.push(String::new());
        body.push("y copies the safety number; e exports your contact card.".into());
        Screen::Info {
            title: "identity".into(),
            body,
            copy,
            export_name: "contact-card",
            next: Box::new(Screen::Home),
        }
    }
    fn edit_input(&mut self, key: KeyEvent) {
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        match key.code {
            KeyCode::Backspace => self.input.backspace(),
            KeyCode::Delete => self.input.delete(),
            KeyCode::Left => self.input.left(),
            KeyCode::Right => self.input.right(),
            KeyCode::Home => self.input.home(),
            KeyCode::End => self.input.end(),
            KeyCode::Char('a') if ctrl => self.input.home(),
            KeyCode::Char('e') if ctrl => self.input.end(),
            KeyCode::Char('u') if ctrl => self.input.clear(),
            KeyCode::Char('w') if ctrl => self.input.delete_word(),
            KeyCode::Char(value) if !ctrl => self.input.push(value),
            _ => {}
        }
    }
    fn key_channel(&mut self, screen: &mut Screen, id: ChannelId, key: KeyEvent) {
        let members = self
            .client
            .as_ref()
            .map_or_else(Vec::new, |client| client.members(id));
        self.sync_member_selection(&members);
        match key.code {
            KeyCode::Esc => {
                self.input.clear();
                *screen = Screen::Home;
            }
            KeyCode::Tab | KeyCode::BackTab => {
                self.channel_focus = match self.channel_focus {
                    ChannelFocus::Members => ChannelFocus::Message,
                    ChannelFocus::Message => ChannelFocus::Members,
                };
            }
            KeyCode::Up if self.channel_focus == ChannelFocus::Members => {
                self.member_sel = self.member_sel.saturating_sub(1);
                self.selected_member = members.get(self.member_sel).map(|member| member.id);
            }
            KeyCode::Down if self.channel_focus == ChannelFocus::Members => {
                if !members.is_empty() {
                    self.member_sel = (self.member_sel + 1).min(members.len() - 1);
                    self.selected_member = members.get(self.member_sel).map(|member| member.id);
                }
            }
            KeyCode::Enter if self.channel_focus == ChannelFocus::Members => {
                if let (Some(client), Some(member)) = (&self.client, members.get(self.member_sel)) {
                    match client.open_scoped_pm(id, member.id) {
                        Ok(pm) => {
                            self.scroll = 0;
                            *screen = Screen::ScopedPm { id: pm };
                        }
                        Err(error) => self.err(error),
                    }
                }
            }
            KeyCode::Enter if !self.input.is_empty() => {
                let text = self.input.take();
                self.scroll = 0;
                self.cmds.push(Cmd::SendChannel { id, text });
            }
            KeyCode::Up if self.channel_focus == ChannelFocus::Message => {
                self.scroll = self.scroll.saturating_add(1)
            }
            KeyCode::Down if self.channel_focus == ChannelFocus::Message => {
                self.scroll = self.scroll.saturating_sub(1)
            }
            KeyCode::PageUp if self.channel_focus == ChannelFocus::Message => {
                self.scroll = self.scroll.saturating_add(10)
            }
            KeyCode::PageDown if self.channel_focus == ChannelFocus::Message => {
                self.scroll = self.scroll.saturating_sub(10)
            }
            KeyCode::Char('p') if self.channel_focus == ChannelFocus::Members => {
                *screen = Screen::Form(Form::publish(id))
            }
            KeyCode::Char('i') if self.channel_focus == ChannelFocus::Members => {
                // Only the owner can mint invites; give a member a plain reason
                // rather than surfacing a raw node error.
                match self.client.as_ref().and_then(|client| client.channel(id)) {
                    Some(channel) if channel.role == ChannelRole::Owner => {
                        self.cmds.push(Cmd::CreateInvite {
                            id,
                            name: channel.title,
                        });
                    }
                    Some(_) => self.warn("only the channel owner can invite people"),
                    None => self.err("channel is not active"),
                }
            }
            KeyCode::Char('d') if self.channel_focus == ChannelFocus::Members => {
                if let Some(member) = members.get(self.member_sel) {
                    self.confirm = Some(Confirm::RemoveMember {
                        channel: id,
                        member: member.id,
                        name: member.display_name.clone(),
                    });
                    self.warn(format!(
                        "remove @{} from this channel? y = yes, any other key = no",
                        member.display_name
                    ));
                }
            }
            _ if self.channel_focus == ChannelFocus::Message => self.edit_input(key),
            _ => {}
        }
    }
    /// How to get someone into a channel you own.
    pub fn invite_screen(&self, id: ChannelId) -> Screen {
        let name = self
            .client
            .as_ref()
            .and_then(|client| client.channel(id))
            .map_or_else(|| "channel".to_string(), |channel| channel.title);
        Screen::Info {
            title: format!("invite to #{name}"),
            body: vec![
                format!("#{name} is yours. To add a friend:"),
                String::new(),
                " 1. Open the channel, press Tab to focus members, and press i.".into(),
                "    That makes a one-time invite link.".into(),
                " 2. Send them the link. They pick New > 'join with invite' and".into(),
                "    paste it — no addresses, no back-and-forth.".into(),
                String::new(),
                "Keep gchat open until they join, so their app can reach you.".into(),
            ],
            copy: None,
            export_name: "invite",
            next: Box::new(Screen::Channel { id }),
        }
    }

    fn sync_member_selection(&mut self, members: &[gchat_core::model::MemberRecord]) {
        if let Some(index) = self
            .selected_member
            .and_then(|id| members.iter().position(|member| member.id == id))
        {
            self.member_sel = index;
        } else {
            self.member_sel = self.member_sel.min(members.len().saturating_sub(1));
            self.selected_member = members.get(self.member_sel).map(|member| member.id);
        }
    }
    fn key_pm(&mut self, screen: &mut Screen, id: ScopedPmId, key: KeyEvent) {
        match key.code {
            KeyCode::Esc => {
                self.input.clear();
                self.scroll = 0;
                *screen = Screen::Channel { id: id.channel_id };
            }
            KeyCode::Enter if !self.input.is_empty() => {
                let text = self.input.take();
                self.scroll = 0;
                self.cmds.push(Cmd::SendPm { id, text });
            }
            KeyCode::Up => self.scroll = self.scroll.saturating_add(1),
            KeyCode::Down => self.scroll = self.scroll.saturating_sub(1),
            KeyCode::PageUp => self.scroll = self.scroll.saturating_add(10),
            KeyCode::PageDown => self.scroll = self.scroll.saturating_sub(10),
            _ => self.edit_input(key),
        }
    }
    fn key_public(
        &mut self,
        screen: &mut Screen,
        descriptor: PublicChannelDescriptor,
        key: KeyEvent,
    ) {
        match key.code {
            KeyCode::Esc => {
                self.input.clear();
                *screen = Screen::Home;
            }
            KeyCode::Enter if !self.input.is_empty() => {
                let display = self.input.value.clone();
                self.info(format!(
                    "joining #{}: preparing join request…",
                    descriptor.title
                ));
                self.cmds.push(Cmd::JoinPublic {
                    descriptor,
                    display,
                });
            }
            _ => self.edit_input(key),
        }
    }
    pub fn on_unlocked(&mut self, unlocked: Unlocked) {
        let Unlocked {
            client,
            runtime,
            relay,
            catalog_warning,
        } = unlocked;
        for item in client.home_items() {
            self.mark_seen(&item);
        }
        self.client = Some(client);
        self.runtime = Some(runtime);
        self.screen = Screen::Home;
        let relay_note = match &relay {
            RelayState::Failed(reason) => Some(format!(
                "relay unavailable: {reason} (r to retry, i for details)"
            )),
            _ => None,
        };
        self.relay = relay;
        match (relay_note, catalog_warning) {
            (Some(relay), Some(catalog)) => self.warn(format!("{relay}; catalogs: {catalog}")),
            (Some(relay), None) => self.warn(relay),
            (None, Some(catalog)) => {
                self.warn(format!("catalogs unavailable: {catalog} (r to retry)"))
            }
            (None, None) => self.ok("unlocked"),
        }
    }
    pub fn on_op(&mut self, op: OpDone) {
        match op {
            OpDone::Unlock(Ok(unlocked)) => self.on_unlocked(unlocked),
            OpDone::Unlock(Err(error)) => self.err(format!("unlock failed: {error}")),
            OpDone::Sent { text, res } => match res {
                Ok(()) => {
                    self.pending_changes = true;
                    self.ok("sent");
                }
                Err(error) => {
                    self.input.set(text);
                    self.err(format!("send failed: {error}"));
                }
            },
            OpDone::PublicJoined {
                descriptor,
                display,
                res,
            } => match res {
                Ok(()) => {
                    self.input.clear();
                    self.screen = Screen::Home;
                    self.ok(format!("joined #{}", descriptor.title));
                }
                Err(error) => {
                    self.input.set(display);
                    self.screen = Screen::Public { descriptor };
                    self.err(format!("join failed: {error}; press Enter to retry"));
                }
            },
            OpDone::ChannelCreated { channel, res } => match res {
                Ok(id) => {
                    self.pending_changes = true;
                    self.ok(format!("created #{channel}"));
                    self.scroll = 0;
                    self.screen = self.invite_screen(id);
                }
                Err(error) => self.err(format!("create failed: {error}")),
            },
            OpDone::Wizard { back, res } => match res {
                Ok(message) => {
                    self.pending_changes = true;
                    self.ok(message);
                    self.scroll = 0;
                    self.screen = back_screen(back);
                }
                Err(error) => self.err(format!("error: {error}")),
            },
            OpDone::JoinPrepared { display, res } => match res {
                Ok((req_id, package)) => {
                    let pending = PendingJoin {
                        req_id,
                        display,
                        package_b64: b64_encode(&package),
                    };
                    self.scroll = 0;
                    self.screen = self.key_package_screen(&pending);
                    self.pending_joins.push(pending);
                }
                Err(error) => self.err(error),
            },
            OpDone::Admitted { res } => match res {
                Ok(welcome) => {
                    let welcome = b64_encode(&welcome);
                    self.scroll = 0;
                    self.screen = Screen::Info {
                        title: "invite code for the new member".into(),
                        body: vec![
                            "Send this exact invite code to the member (y copies, e exports)."
                                .into(),
                            "They paste it under New > complete join, with the channel name."
                                .into(),
                            String::new(),
                            welcome.clone(),
                        ],
                        copy: Some(welcome),
                        export_name: "invite-code",
                        next: Box::new(Screen::Home),
                    };
                }
                Err(error) => self.err(error),
            },
            OpDone::JoinFinished {
                req_id,
                channel,
                res,
            } => match res {
                Ok(()) => {
                    self.on_join_finished(req_id);
                    self.pending_changes = true;
                    self.scroll = 0;
                    self.screen = Screen::Home;
                    self.ok(format!("joined #{channel}"));
                }
                Err(error) => self.err(format!("join failed: {error}")),
            },
            OpDone::RelayFetched(res) => match res {
                Ok(label) => self.relay = RelayState::Ready(label),
                Err(error) => self.relay = RelayState::Failed(error),
            },
            OpDone::Notice(res) => match res {
                Ok(message) => self.ok(message),
                Err(error) => self.err(error),
            },
            OpDone::Warning(message) => self.warn(message),
            OpDone::Saved { res, manual } => match res {
                Ok(()) => {
                    self.pending_changes = false;
                    if manual {
                        self.ok("saved");
                    }
                }
                Err(error) => self.err(format!("save failed: {error}")),
            },
            OpDone::InviteCreated { channel, res } => match res {
                Ok(link) => {
                    self.scroll = 0;
                    self.screen = Screen::Info {
                        title: format!("invite to #{channel}"),
                        body: vec![
                            "Send this invite link to ONE friend (y copies, e exports a file)."
                                .into(),
                            "They pick New > 'join with invite' and paste it — that's all.".into(),
                            "It works once and expires in an hour. Keep gchat open until they"
                                .into(),
                            "join, so their app can reach you.".into(),
                            String::new(),
                            link.clone(),
                        ],
                        copy: Some(link),
                        export_name: "invite-link",
                        next: Box::new(Screen::Home),
                    };
                }
                Err(error) => self.err(format!("could not create invite: {error}")),
            },
            OpDone::InviteJoined { res } => match res {
                Ok(channel) => {
                    self.pending_changes = true;
                    self.scroll = 0;
                    self.screen = Screen::Home;
                    self.ok(format!("joined #{channel}"));
                }
                Err(error) => self.err(format!("join failed: {error}")),
            },
        }
    }
    /// Called after a join finished; drops the pending record.
    pub fn on_join_finished(&mut self, req_id: u64) {
        self.pending_joins
            .retain(|pending| pending.req_id != req_id);
    }
    pub fn on_node_event(&mut self, event: NodeEvent) {
        match event {
            NodeEvent::ChannelRosterChanged { .. } => self.info("channel roster updated"),
            NodeEvent::ChannelRemoved { channel } => {
                let viewed = match self.screen {
                    Screen::Channel { id } => Some(id),
                    Screen::ScopedPm { id } => Some(id.channel_id),
                    _ => None,
                };
                let viewing_removed = viewed.is_some_and(|id| {
                    self.client
                        .as_ref()
                        .and_then(|client| client.channel_protocol_name(id))
                        .as_deref()
                        == Some(channel.as_str())
                });
                if viewing_removed {
                    self.screen = Screen::Home;
                    self.warn("channel membership lost; history retained read-only");
                } else {
                    self.warn(format!("left #{channel}; history retained read-only"));
                }
            }
            NodeEvent::EventsLagged { skipped } => {
                self.warn(format!("event stream lagged by {skipped}"))
            }
            NodeEvent::ChannelMessage { .. } | NodeEvent::ChannelDirectMessage { .. } => {
                self.pending_changes = true
            }
            _ => {}
        }
    }
    pub fn on_tick(&mut self) {
        self.ticks += 1;
        if matches!(self.status_kind, StatusKind::Info | StatusKind::Ok)
            && !self.status.is_empty()
            && self.ticks.saturating_sub(self.status_tick) >= STATUS_TICKS
        {
            self.status.clear();
        }
        let items = self.home_items();
        self.home_sel = self
            .selected_home
            .and_then(|id| items.iter().position(|item| item.id() == id))
            .unwrap_or_else(|| self.home_sel.min(items.len().saturating_sub(1)));
        // Whatever is open counts as read.
        let open = match self.screen {
            Screen::Channel { id } => Some(HomeId::Channel(id)),
            Screen::ScopedPm { id } => Some(HomeId::ScopedPm(id)),
            _ => None,
        };
        if let Some(open) = open {
            if let Some(item) = items.iter().find(|item| item.id() == open) {
                self.mark_seen(item);
            }
        }
        if let Screen::Channel { id } = self.screen {
            let members = self
                .client
                .as_ref()
                .map_or_else(Vec::new, |client| client.members(id));
            self.sync_member_selection(&members);
        }
        if self.ticks.is_multiple_of(SAVE_TICKS) && self.pending_changes && self.client.is_some() {
            self.cmds.push(Cmd::Save { manual: false });
        }
    }
}

fn back_screen(back: Back) -> Screen {
    match back {
        Back::Home | Back::Quit => Screen::Home,
        Back::NewMenu => Screen::NewMenu { sel: 0 },
        Back::Channel(id) => Screen::Channel { id },
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Duration;

    fn key(code: KeyCode) -> KeyEvent {
        KeyEvent::new(code, KeyModifiers::NONE)
    }
    fn app() -> App {
        App::new(UnlockMode::UnlockProfile, Path::new("x"), "")
    }
    fn press(app: &mut App, codes: &[KeyCode]) {
        let mut now = Instant::now();
        for code in codes {
            now += Duration::from_millis(100);
            app.on_key_at(key(*code), now);
        }
    }
    fn type_str(app: &mut App, text: &str) {
        press(app, &text.chars().map(KeyCode::Char).collect::<Vec<_>>());
    }

    #[test]
    fn guidance_opens() {
        let mut app = app();
        app.screen = Screen::Home;
        app.on_key(key(KeyCode::Char('?')));
        assert!(matches!(app.screen, Screen::Help));
    }
    #[test]
    fn mixed_home_selection_is_typed() {
        let mut app = app();
        app.selected_home = Some(HomeId::Channel(ChannelId([1; 32])));
        app.on_tick();
        assert_eq!(app.home_sel, 0);
    }

    #[test]
    fn channel_focus_makes_member_actions_explicit_and_keeps_scroll_out_of_composition() {
        let mut app = app();
        app.screen = Screen::Channel {
            id: ChannelId([1; 32]),
        };
        app.on_key(key(KeyCode::Char('x')));
        app.on_key(key(KeyCode::Up));
        assert_eq!(app.input.value, "x");
        assert_eq!(app.scroll, 1);
        assert_eq!(app.channel_focus, ChannelFocus::Message);

        app.on_key(key(KeyCode::Tab));
        app.on_key(key(KeyCode::Char('y')));
        app.on_key(key(KeyCode::Enter));
        assert_eq!(app.channel_focus, ChannelFocus::Members);
        assert_eq!(app.input.value, "x");
        assert!(app.drain_cmds().is_empty());
        assert!(matches!(app.screen, Screen::Channel { .. }));
    }

    #[test]
    fn member_identity_survives_roster_resort() {
        use gchat_core::model::MemberRecord;

        let member = |value, name: &str| MemberRecord {
            id: MemberId([value; 32]),
            display_name: name.into(),
            join_order: value.into(),
            joined_at_unix: None,
            is_self: false,
        };
        let mut app = app();
        app.selected_member = Some(MemberId([2; 32]));
        app.member_sel = 1;
        app.sync_member_selection(&[member(2, "two"), member(1, "one")]);
        assert_eq!(app.member_sel, 0);
        assert_eq!(app.selected_member, Some(MemberId([2; 32])));
    }

    #[test]
    fn roster_events_are_live_and_unrelated_membership_loss_keeps_the_screen() {
        let mut app = app();
        app.screen = Screen::Channel {
            id: ChannelId([1; 32]),
        };
        app.on_node_event(NodeEvent::ChannelRosterChanged {
            channel: "room".into(),
            channel_id: ChannelId([1; 32]),
        });
        assert_eq!(app.status, "channel roster updated");
        app.on_node_event(NodeEvent::ChannelRemoved {
            channel: "other-room".into(),
        });
        assert!(matches!(app.screen, Screen::Channel { .. }));
        assert!(app.status.contains("other-room"));
    }

    #[test]
    fn esc_on_unlock_quits_instead_of_dead_home() {
        let mut app = App::new(UnlockMode::CreateProfile, Path::new("/tmp/p"), "");
        app.on_key(key(KeyCode::Esc));
        assert!(matches!(app.screen, Screen::Unlock(_)));
        assert!(matches!(app.drain_cmds().as_slice(), [Cmd::Quit]));
    }

    #[test]
    fn r_in_public_pseudonym_types() {
        let mut app = app();
        let descriptor = PublicChannelDescriptor {
            version: 1,
            expires_at_unix: 999,
            channel_id: ChannelId([9; 32]),
            owner_public_key: vec![],
            capacity: 2,
            title: "room".into(),
            description: String::new(),
            activity: gcoms_sdk::ActivityBucket::None,
            automatic_join: gcoms_sdk::AutomaticJoinEndpoint {
                catalog: String::new(),
                endpoint: String::new(),
            },
            signature: vec![],
        };
        app.screen = Screen::Public {
            descriptor: descriptor.clone(),
        };
        type_str(&mut app, "ghost-runner");
        assert_eq!(app.input.value, "ghost-runner");
        assert!(app.drain_cmds().is_empty());
        app.on_key(key(KeyCode::Enter));
        assert!(matches!(
            app.drain_cmds().as_slice(),
            [Cmd::JoinPublic { display, .. }] if display == "ghost-runner"
        ));
    }

    #[test]
    fn remove_member_requires_y() {
        let mut app = app();
        // No client, so the member list is empty: `d` must be a no-op.
        app.screen = Screen::Channel {
            id: ChannelId([1; 32]),
        };
        app.channel_focus = ChannelFocus::Members;
        app.on_key(key(KeyCode::Char('d')));
        assert!(app.confirm.is_none());
        // With a pending confirm, anything but `y` cancels.
        app.confirm = Some(Confirm::RemoveMember {
            channel: ChannelId([1; 32]),
            member: MemberId([2; 32]),
            name: "ada".into(),
        });
        app.on_key(key(KeyCode::Char('n')));
        assert!(app.confirm.is_none());
        assert!(app.drain_cmds().is_empty());
        assert_eq!(app.status, "cancelled");
        app.confirm = Some(Confirm::RemoveMember {
            channel: ChannelId([1; 32]),
            member: MemberId([2; 32]),
            name: "ada".into(),
        });
        app.on_key(key(KeyCode::Char('y')));
        assert!(matches!(
            app.drain_cmds().as_slice(),
            [Cmd::RemoveMember { member, .. }] if *member == MemberId([2; 32])
        ));
        assert!(matches!(app.screen, Screen::Channel { .. }));
    }

    #[test]
    fn pending_join_survives_esc_and_reappears_in_new_menu() {
        let mut app = app();
        app.screen = Screen::Home;
        app.on_op(OpDone::JoinPrepared {
            display: "me".into(),
            res: Ok((7, b"package".to_vec())),
        });
        assert!(
            matches!(&app.screen, Screen::Info { copy: Some(c), .. } if c == &b64_encode(b"package"))
        );
        app.on_key(key(KeyCode::Enter));
        assert!(matches!(&app.screen, Screen::Form(f) if f.title.contains("2/2")));
        app.on_key(key(KeyCode::Esc));
        assert!(matches!(app.screen, Screen::NewMenu { .. }));
        let rows = app.new_menu();
        // 4 base rows (create / join-with-invite / advanced join / advanced
        // let-in) plus 2 rows for the one pending join.
        assert_eq!(rows.len(), 6);
        assert_eq!(rows[4].2, NewAction::FinishJoin(7));
        press(
            &mut app,
            &[
                KeyCode::Down,
                KeyCode::Down,
                KeyCode::Down,
                KeyCode::Down,
                KeyCode::Enter,
            ],
        );
        assert!(matches!(&app.screen, Screen::Form(f) if f.title.contains("2/2")));
        app.on_join_finished(7);
        assert_eq!(app.new_menu().len(), 4);
    }

    #[test]
    fn status_info_expires_but_error_persists_until_a_key() {
        let mut app = app();
        app.screen = Screen::Home;
        app.ok("sent");
        for _ in 0..STATUS_TICKS {
            app.on_tick();
        }
        assert_eq!(app.status, "");
        app.err("boom");
        for _ in 0..STATUS_TICKS * 2 {
            app.on_tick();
        }
        assert_eq!(app.status, "boom");
        app.on_key(key(KeyCode::Down));
        assert_eq!(app.status, "");
        assert_eq!(app.status_kind, StatusKind::Info);
    }

    #[test]
    fn enter_during_paste_burst_is_ignored_in_blob_field() {
        let mut app = app();
        app.screen = Screen::Form(Form::admit());
        // Focus the key package field (index 2).
        press(&mut app, &[KeyCode::Tab, KeyCode::Tab]);
        let now = Instant::now();
        let burst = "QUJD\nREVG".chars().enumerate();
        for (index, c) in burst {
            let code = if c == '\n' {
                KeyCode::Enter
            } else {
                KeyCode::Char(c)
            };
            app.on_key_at(key(code), now + Duration::from_millis(index as u64));
        }
        assert!(app.drain_cmds().is_empty(), "burst Enter must not submit");
        let Screen::Form(form) = &app.screen else {
            panic!("still on the form")
        };
        assert_eq!(form.fields[2].edit.value, "QUJDREVG");
        // A deliberate Enter later still submits (and fails validation).
        app.on_key_at(key(KeyCode::Enter), now + Duration::from_secs(1));
        assert!(app.status.contains("required"));
    }

    #[test]
    fn ctrl_p_paste_mode_holds_enter_on_any_field() {
        let mut app = app();
        app.screen = Screen::Form(Form::join_begin());
        app.on_key(KeyEvent::new(KeyCode::Char('p'), KeyModifiers::CONTROL));
        assert!(app.paste_mode);
        press(
            &mut app,
            &[KeyCode::Char('a'), KeyCode::Enter, KeyCode::Char('b')],
        );
        assert!(app.drain_cmds().is_empty());
        app.on_key(KeyEvent::new(KeyCode::Char('p'), KeyModifiers::CONTROL));
        press(&mut app, &[KeyCode::Enter]);
        assert!(matches!(app.drain_cmds().as_slice(), [Cmd::Spawn(_)]));
    }

    #[test]
    fn visibility_toggle_cycles_with_space_and_arrows() {
        let mut app = app();
        app.screen = Screen::Form(Form::create_channel());
        press(&mut app, &[KeyCode::Tab, KeyCode::Tab, KeyCode::Tab]);
        press(&mut app, &[KeyCode::Char(' ')]);
        let Screen::Form(form) = &app.screen else {
            panic!()
        };
        assert_eq!(form.fields[3].value(), "public");
        press(&mut app, &[KeyCode::Char('x'), KeyCode::Left]);
        let Screen::Form(form) = &app.screen else {
            panic!()
        };
        assert_eq!(
            form.fields[3].value(),
            "private",
            "typing into a toggle is ignored"
        );
    }

    #[test]
    fn quit_warns_once_when_a_join_is_pending() {
        let mut app = app();
        app.screen = Screen::Home;
        app.pending_joins.push(PendingJoin {
            req_id: 3,
            display: "me".into(),
            package_b64: "QUJD".into(),
        });
        app.on_key(key(KeyCode::Char('q')));
        assert!(app.drain_cmds().is_empty(), "first q only warns");
        assert!(app.status.contains("pending join"));
        app.on_key(key(KeyCode::Char('x')));
        assert!(app.drain_cmds().is_empty());
        app.on_key(key(KeyCode::Char('q')));
        app.on_key(key(KeyCode::Char('q')));
        assert!(matches!(app.drain_cmds().as_slice(), [Cmd::Quit]));
    }

    #[test]
    fn q_backs_out_of_menus_and_info() {
        let mut app = app();
        app.screen = Screen::NewMenu { sel: 0 };
        app.on_key(key(KeyCode::Char('q')));
        assert!(matches!(app.screen, Screen::Home));
        app.screen = Screen::Info {
            title: "t".into(),
            body: vec!["x".into()],
            copy: None,
            export_name: "x",
            next: Box::new(Screen::Home),
        };
        app.on_key(key(KeyCode::Char('q')));
        assert!(matches!(app.screen, Screen::Home));
        assert!(app.drain_cmds().is_empty());
    }

    #[test]
    fn info_copy_and_export_use_the_explicit_value() {
        let mut app = app();
        app.screen = Screen::Info {
            title: "t".into(),
            body: vec![
                "a much longer instruction line than the value".into(),
                "v".into(),
            ],
            copy: Some("v".into()),
            export_name: "thing",
            next: Box::new(Screen::Home),
        };
        app.on_key(key(KeyCode::Char('y')));
        app.on_key(key(KeyCode::Char('e')));
        assert!(matches!(
            app.drain_cmds().as_slice(),
            [Cmd::Copy(c), Cmd::Export { name: "thing", text }] if c == "v" && text == "v"
        ));
    }

    #[test]
    fn relay_retry_outcome_replaces_the_failed_reason() {
        let mut app = app();
        app.relay = RelayState::Failed("dns".into());
        app.on_op(OpDone::RelayFetched(Err("still dns".into())));
        assert_eq!(app.relay, RelayState::Failed("still dns".into()));
        app.on_op(OpDone::Notice(Err(
            "relay still unavailable: still dns".into()
        )));
        assert!(app.status.contains("relay still unavailable"));
        assert_eq!(app.status_kind, StatusKind::Err);
    }

    #[test]
    fn home_keys_open_identity_and_refresh_only_when_unlocked() {
        let mut app = app();
        app.screen = Screen::Home;
        app.on_key(key(KeyCode::Char('r')));
        assert!(app.drain_cmds().is_empty());
        app.on_key(key(KeyCode::Char('i')));
        assert!(matches!(&app.screen, Screen::Info { title, .. } if title == "identity"));
        let Screen::Info { body, .. } = &app.screen else {
            panic!()
        };
        assert!(body.iter().any(|line| line == "not unlocked"));
        assert!(body.iter().any(|line| line.starts_with("relay: none")));
    }
}
