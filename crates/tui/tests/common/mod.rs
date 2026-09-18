//! Fixtures for driving `App` without a node: a fake SDK, staged archive
//! data, key drivers, and the text-snapshot comparator.
#![allow(dead_code)]

use async_trait::async_trait;
use crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use gchat_core::client::ClientHandle;
use gchat_core::model::{
    CachedDescriptor, ChannelRecord, MemberId, MemberRecord, Message, ScopedPmId, ScopedPmRecord,
};
use gchat_core::store::ArchiveData;
use gchat_tui::app::{App, RelayState, RuntimeKind, Unlocked};
use gchat_tui::form::UnlockMode;
use gchat_tui::ui::render_to_lines;
use gcoms::sdk::{
    ActivityBucket, AutomaticJoinEndpoint, Blob, ChannelId, ChannelMemberSummary, ChannelRole,
    ChannelVisibility, ClientEvent, ContactCard, GcClient, Identity, JoinRequest, JoinedChannel,
    MessageId, PresenceMode, PublicChannelDescriptor, SdkError,
};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::mpsc;

/// Fixed clock so `[HH:MM]` stamps are stable: 2026-09-05 10:30 UTC.
pub const T0: u64 = 1_788_604_200;

/// A `GcClient` that answers from canned data and never touches the network.
pub struct FakeSdk {
    pub identity: Identity,
    pub events: std::sync::Mutex<Option<mpsc::Receiver<ClientEvent>>>,
}

impl FakeSdk {
    pub fn new() -> (Arc<Self>, mpsc::Sender<ClientEvent>) {
        let (tx, rx) = mpsc::channel(64);
        let sdk = Arc::new(FakeSdk {
            identity: Identity {
                contact_card: ContactCard(b"fake-contact-card".to_vec()),
                safety_number: "12345 67890 24680 13579 11223 34455".into(),
            },
            events: std::sync::Mutex::new(Some(rx)),
        });
        (sdk, tx)
    }
}

fn unsupported<T>() -> Result<T, SdkError> {
    Err(SdkError::Runtime("fake sdk".into()))
}

#[async_trait]
impl GcClient for FakeSdk {
    fn identity(&self) -> Identity {
        self.identity.clone()
    }
    async fn refresh_identity(&self) -> Result<Identity, SdkError> {
        Ok(self.identity.clone())
    }
    async fn sign_identity_digest(&self, _digest: [u8; 32]) -> Result<Vec<u8>, SdkError> {
        unsupported()
    }
    async fn sign_principal_binding_hash(&self, _hash: [u8; 32]) -> Result<Vec<u8>, SdkError> {
        unsupported()
    }
    fn subscribe_events(&self) -> mpsc::Receiver<ClientEvent> {
        self.events
            .lock()
            .unwrap()
            .take()
            .unwrap_or_else(|| mpsc::channel(1).1)
    }
    async fn list_channels(&self) -> Result<Vec<JoinedChannel>, SdkError> {
        Ok(Vec::new())
    }
    async fn channel_roster(&self, _channel: &str) -> Result<Vec<ChannelMemberSummary>, SdkError> {
        Ok(Vec::new())
    }
    async fn public_channel_descriptor(
        &self,
        _channel: &str,
        _description: &str,
        _activity: ActivityBucket,
        _automatic_join: AutomaticJoinEndpoint,
        _expires_at_unix: u64,
    ) -> Result<PublicChannelDescriptor, SdkError> {
        unsupported()
    }
    async fn send_direct(
        &self,
        _peer: &ContactCard,
        _body: &[u8],
        _via: Option<&ContactCard>,
    ) -> Result<(), SdkError> {
        unsupported()
    }
    async fn set_direct_presence(
        &self,
        _peer: &ContactCard,
        _mode: PresenceMode,
        _lease_secs: u32,
        _via: Option<&ContactCard>,
    ) -> Result<(), SdkError> {
        unsupported()
    }
    async fn set_direct_presence_opt_in(
        &self,
        _peer: &ContactCard,
        _enabled: bool,
        _via: Option<&ContactCard>,
    ) -> Result<(), SdkError> {
        unsupported()
    }
    async fn create_channel(
        &self,
        _channel: &str,
        _display_name: &str,
        _capacity: usize,
        _visibility: ChannelVisibility,
    ) -> Result<ChannelId, SdkError> {
        unsupported()
    }
    async fn prepare_channel_join(&self, _display_name: &str) -> Result<JoinRequest, SdkError> {
        unsupported()
    }
    async fn channel_key_package(&self, _request: JoinRequest) -> Result<Blob, SdkError> {
        unsupported()
    }
    async fn admit_channel(
        &self,
        _channel: &str,
        _key_package: &Blob,
        _member_name: &str,
    ) -> Result<Blob, SdkError> {
        unsupported()
    }
    async fn join_channel(
        &self,
        _request: JoinRequest,
        _channel: &str,
        _visibility: ChannelVisibility,
        _welcome: &Blob,
    ) -> Result<(), SdkError> {
        unsupported()
    }
    async fn send_channel(&self, _channel: &str, _body: &[u8]) -> Result<(), SdkError> {
        unsupported()
    }
    async fn set_channel_presence(
        &self,
        _channel: &str,
        _mode: PresenceMode,
        _lease_secs: u32,
    ) -> Result<(), SdkError> {
        unsupported()
    }
    async fn set_channel_presence_opt_in(
        &self,
        _channel: &str,
        _enabled: bool,
    ) -> Result<(), SdkError> {
        unsupported()
    }
    async fn send_channel_direct(
        &self,
        _channel: &str,
        _member_id: [u8; 32],
        _body: &[u8],
    ) -> Result<MessageId, SdkError> {
        unsupported()
    }
    async fn remove_channel_member(
        &self,
        _channel: &str,
        _member_id: [u8; 32],
    ) -> Result<(), SdkError> {
        unsupported()
    }
}

pub fn channel_id(n: u8) -> ChannelId {
    ChannelId([n; 32])
}
pub fn member_id(n: u8) -> MemberId {
    MemberId([n; 32])
}

pub fn member(n: u8, name: &str, is_self: bool) -> MemberRecord {
    MemberRecord {
        id: member_id(n),
        display_name: name.into(),
        join_order: u32::from(n),
        joined_at_unix: Some(T0),
        is_self,
    }
}

pub fn message(n: u8, sender: (u8, &str), mine: bool, text: &str) -> Message {
    Message {
        id: [n; 16],
        ts_unix: T0 + u64::from(n) * 60,
        sender_member_id: Some(member_id(sender.0)),
        sender_name: sender.1.into(),
        mine,
        text: text.into(),
    }
}

/// `#ops`: you (owner) plus ada and bob, three messages.
pub fn ops_channel() -> ChannelRecord {
    ChannelRecord {
        id: channel_id(1),
        protocol_name: "ops".into(),
        title: "ops".into(),
        visibility: ChannelVisibility::Private,
        role: ChannelRole::Owner,
        joined_at_unix: T0,
        active: true,
        self_member_id: Some(member_id(10)),
        members: vec![
            member(10, "you", true),
            member(11, "ada", false),
            member(12, "bob", false),
        ],
        messages: vec![
            message(1, (11, "ada"), false, "morning! is the relay up?"),
            message(2, (10, "you"), true, "yes, since last night"),
            message(
                3,
                (12, "bob"),
                false,
                "great. long message to check wrapping on narrow phone terminals where the transcript pane is only fifty columns wide",
            ),
        ],
    }
}

/// `#lounge`: a public channel you are a plain member of, one message.
pub fn lounge_channel() -> ChannelRecord {
    ChannelRecord {
        id: channel_id(2),
        protocol_name: "lounge".into(),
        title: "lounge".into(),
        visibility: ChannelVisibility::Public,
        role: ChannelRole::Member,
        joined_at_unix: T0,
        active: true,
        self_member_id: Some(member_id(20)),
        members: vec![member(20, "you", true), member(21, "cyd", false)],
        messages: vec![message(4, (21, "cyd"), false, "welcome to the lounge")],
    }
}

pub fn ada_pm() -> ScopedPmRecord {
    ScopedPmRecord {
        id: ScopedPmId {
            channel_id: channel_id(1),
            self_member_id: member_id(10),
            remote_member_id: member_id(11),
        },
        remote_display_name: "ada".into(),
        messages: vec![
            message(5, (11, "ada"), false, "psst, got a minute?"),
            message(6, (10, "you"), true, "sure"),
        ],
        active: true,
    }
}

pub fn public_descriptor() -> CachedDescriptor {
    CachedDescriptor {
        descriptor: PublicChannelDescriptor {
            version: 1,
            expires_at_unix: T0 + 6 * 24 * 3600,
            channel_id: channel_id(3),
            owner_public_key: vec![],
            capacity: 200,
            title: "town-square".into(),
            description: "Open discussion for everyone on this relay.".into(),
            activity: ActivityBucket::Today,
            automatic_join: AutomaticJoinEndpoint {
                catalog: "https://catalog.example/".into(),
                endpoint: "https://catalog.example/v1/channels/x/join".into(),
            },
            signature: vec![],
        },
        published_at_unix: T0 - 24 * 3600,
    }
}

/// Archive with the populated fixtures above. Descriptors are filtered by
/// signature at render time, so the public row only appears via `Public`.
pub fn populated_archive() -> ArchiveData {
    ArchiveData {
        daemon_safety_number: "12345 67890 24680 13579 11223 34455".into(),
        channels: vec![ops_channel(), lounge_channel()],
        scoped_pms: vec![ada_pm()],
        public_descriptors: vec![],
        legacy: Default::default(),
    }
}

/// An unlocked app over `data`, plus the event injector.
pub async fn app_with(data: ArchiveData) -> (App, mpsc::Sender<ClientEvent>) {
    let (sdk, events) = FakeSdk::new();
    let client = ClientHandle::in_memory(sdk, data).await.unwrap();
    let mut app = App::new(
        UnlockMode::UnlockProfile,
        Path::new("/home/u/.local/share/gchat/profile.gcprotocol"),
        "",
    );
    app.session.profile = Some(PathBuf::from(
        "/home/u/.local/share/gchat/profile.gcprotocol",
    ));
    app.session.archive = Some(PathBuf::from("/home/u/.local/share/gchat/chat.gcarchive"));
    app.session.outbox = Some(PathBuf::from("/home/u/.local/share/gchat/outbox"));
    app.on_unlocked(Unlocked {
        client,
        runtime: RuntimeKind::Hosted,
        relay: RelayState::Ready("203.0.113.5:8443".into()),
        catalog_warning: None,
    });
    // Consume the fading "unlocked" status so snapshots are stable.
    app.status.clear();
    (app, events)
}

pub fn key(code: KeyCode) -> KeyEvent {
    KeyEvent::new(code, KeyModifiers::NONE)
}

/// Press keys 100 ms apart (never a paste burst).
pub fn press(app: &mut App, codes: &[KeyCode]) {
    let mut now = Instant::now();
    for code in codes {
        now += Duration::from_millis(100);
        app.on_key_at(key(*code), now);
    }
}

pub fn type_str(app: &mut App, text: &str) {
    press(app, &text.chars().map(KeyCode::Char).collect::<Vec<_>>());
}

pub const SIZES: [(u16, u16); 4] = [(100, 30), (80, 24), (50, 20), (90, 15)];

fn snapshot_dir() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("snapshots")
}

/// Compare a render to `tests/snapshots/<name>@<W>x<H>.txt`.
/// `UPDATE_SNAPSHOTS=1` rewrites the file instead of failing.
pub fn check(name: &str, app: &App, width: u16, height: u16) -> Result<(), String> {
    let lines = render_to_lines(app, width, height);
    assert!(
        lines
            .iter()
            .all(|line| gchat_tui::text::display_width(line) <= usize::from(width)),
        "{name}@{width}x{height}: a row exceeds the terminal width"
    );
    let actual = lines.join("\n") + "\n";
    let path = snapshot_dir().join(format!("{name}@{width}x{height}.txt"));
    let update = std::env::var_os("UPDATE_SNAPSHOTS").is_some();
    match std::fs::read_to_string(&path) {
        Ok(expected) if expected == actual => Ok(()),
        Ok(expected) if !update => Err(format!(
            "snapshot mismatch for {} (UPDATE_SNAPSHOTS=1 to accept)\n{}",
            path.display(),
            diff(&expected, &actual)
        )),
        Err(_) if !update => Err(format!(
            "missing snapshot {} (UPDATE_SNAPSHOTS=1 to create)\n--- actual ---\n{actual}",
            path.display()
        )),
        _ => {
            std::fs::create_dir_all(snapshot_dir()).map_err(|e| e.to_string())?;
            std::fs::write(&path, actual).map_err(|e| e.to_string())?;
            Ok(())
        }
    }
}

/// Check one state at every size; collect all failures before panicking.
pub fn check_all(name: &str, app: &App) {
    let failures = SIZES
        .iter()
        .filter_map(|(w, h)| check(name, app, *w, *h).err())
        .collect::<Vec<_>>();
    assert!(failures.is_empty(), "{}", failures.join("\n\n"));
}

/// Line diff: `-` expected, `+` actual, with a little context.
fn diff(expected: &str, actual: &str) -> String {
    let left: Vec<&str> = expected.lines().collect();
    let right: Vec<&str> = actual.lines().collect();
    let mut out = String::new();
    let rows = left.len().max(right.len());
    for i in 0..rows {
        match (left.get(i), right.get(i)) {
            (Some(l), Some(r)) if l == r => out.push_str(&format!("  {l}\n")),
            (Some(l), Some(r)) => {
                out.push_str(&format!("- {l}\n+ {r}\n"));
            }
            (Some(l), None) => out.push_str(&format!("- {l}\n")),
            (None, Some(r)) => out.push_str(&format!("+ {r}\n")),
            (None, None) => {}
        }
    }
    out
}
