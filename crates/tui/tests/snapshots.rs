//! Text snapshots of every screen at four terminal sizes.
//!
//! `cargo test -p gc-client-tui --test snapshots` compares against
//! `tests/snapshots/<state>@<W>x<H>.txt`; `UPDATE_SNAPSHOTS=1` rewrites them.
//! `scripts/snapshot-png.py` renders the text files to PNGs for review.

mod common;

use common::*;
use crossterm::event::KeyCode;
use gchat_core::store::ArchiveData;
use gchat_tui::app::{App, ChannelFocus, Confirm, OpDone, RelayState, Screen};
use gchat_tui::form::{Form, UnlockMode};
use std::path::Path;

fn locked(mode: UnlockMode) -> App {
    App::new(
        mode,
        Path::new("/home/u/.local/share/gchat/profile.gcprotocol"),
        "/run/user/1000/gchat/gcd.sock",
    )
}

#[test]
fn unlock_create() {
    let mut app = locked(UnlockMode::CreateProfile);
    type_str(&mut app, "hunter22");
    check_all("unlock_create", &app);
}

#[test]
fn unlock_unlock() {
    check_all("unlock_unlock", &locked(UnlockMode::UnlockProfile));
}

#[test]
fn unlock_archive_for_daemon() {
    check_all("unlock_archive", &locked(UnlockMode::CreateArchive));
}

#[test]
fn unlock_mismatch() {
    let mut app = locked(UnlockMode::CreateProfile);
    type_str(&mut app, "hunter22");
    press(&mut app, &[KeyCode::Tab]);
    type_str(&mut app, "hunter23");
    press(&mut app, &[KeyCode::Enter]);
    check_all("unlock_mismatch", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn home_empty_no_catalogs() {
    let (mut app, _events) = app_with(ArchiveData::default()).await;
    app.relay = RelayState::None;
    check_all("home_empty_no_catalogs", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn home_relay_failed() {
    let (mut app, _events) = app_with(ArchiveData::default()).await;
    app.relay = RelayState::Failed("bootstrap endpoint unreachable: dns error".into());
    app.warn(
        "relay unavailable: bootstrap endpoint unreachable: dns error (r to retry, i for details)",
    );
    check_all("home_relay_failed", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn home_populated_unread() {
    let (mut app, _events) = app_with(populated_archive()).await;
    // Everything was "seen" at unlock; make #lounge unread by forgetting it.
    let mut fresh = App::new(UnlockMode::UnlockProfile, Path::new("x"), "");
    fresh.session = app.session.clone();
    fresh.relay = app.relay.clone();
    fresh.runtime = app.runtime.clone();
    fresh.client = app.client.take();
    fresh.screen = Screen::Home;
    check_all("home_populated_unread", &fresh);
}

#[tokio::test(flavor = "multi_thread")]
async fn new_menu() {
    let (mut app, _events) = app_with(populated_archive()).await;
    press(&mut app, &[KeyCode::Char('n')]);
    check_all("new_menu", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn new_menu_pending_join() {
    let (mut app, _events) = app_with(ArchiveData::default()).await;
    app.on_op(OpDone::JoinPrepared {
        display: "me".into(),
        res: Ok((42, vec![7u8; 90])),
    });
    check_all("info_keypackage_long_base64", &app);
    press(&mut app, &[KeyCode::Enter]);
    check_all("form_join_finish", &app);
    press(&mut app, &[KeyCode::Esc]);
    check_all("new_menu_pending_join", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn form_create_channel_toggle() {
    let (mut app, _events) = app_with(ArchiveData::default()).await;
    app.screen = Screen::Form(Form::create_channel());
    type_str(&mut app, "ops");
    press(&mut app, &[KeyCode::Tab]);
    type_str(&mut app, "ghost");
    press(&mut app, &[KeyCode::Tab, KeyCode::Tab, KeyCode::Char(' ')]);
    check_all("form_create_channel_toggle", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn info_invite() {
    let (mut app, _events) = app_with(populated_archive()).await;
    app.on_op(OpDone::ChannelCreated {
        channel: "ops".into(),
        res: Ok(channel_id(1)),
    });
    check_all("info_invite", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn form_join_begin_and_admit() {
    let (mut app, _events) = app_with(ArchiveData::default()).await;
    app.screen = Screen::Form(Form::join_begin());
    check_all("form_join_begin", &app);
    app.screen = Screen::Form(Form::admit());
    type_str(&mut app, "ops");
    press(&mut app, &[KeyCode::Tab]);
    type_str(&mut app, "ada");
    press(&mut app, &[KeyCode::Tab]);
    app.on_paste(&"QUJD".repeat(40));
    check_all("form_admit", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn info_welcome() {
    let (mut app, _events) = app_with(ArchiveData::default()).await;
    app.on_op(OpDone::Admitted {
        res: Ok(vec![0xA5u8; 120]),
    });
    check_all("info_welcome", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn channel_message_focus() {
    let (mut app, _events) = app_with(populated_archive()).await;
    app.screen = Screen::Channel { id: channel_id(1) };
    type_str(&mut app, "typing a reply");
    press(&mut app, &[KeyCode::Left, KeyCode::Left]);
    check_all("channel_message_focus", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn channel_members_focus() {
    let (mut app, _events) = app_with(populated_archive()).await;
    app.screen = Screen::Channel { id: channel_id(1) };
    app.channel_focus = ChannelFocus::Members;
    app.on_tick();
    check_all("channel_members_focus", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn channel_confirm_remove() {
    let (mut app, _events) = app_with(populated_archive()).await;
    app.screen = Screen::Channel { id: channel_id(1) };
    app.channel_focus = ChannelFocus::Members;
    app.on_tick();
    press(&mut app, &[KeyCode::Char('d')]);
    assert!(matches!(app.confirm, Some(Confirm::RemoveMember { .. })));
    check_all("channel_confirm_remove", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn scoped_pm() {
    let (mut app, _events) = app_with(populated_archive()).await;
    app.screen = Screen::ScopedPm { id: ada_pm().id };
    check_all("pm", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn public_listing() {
    let (mut app, _events) = app_with(ArchiveData::default()).await;
    app.screen = Screen::Public {
        descriptor: public_descriptor().descriptor,
    };
    type_str(&mut app, "ghost-runner");
    check_all("public_descriptor", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn help_and_legacy() {
    let (mut app, _events) = app_with(populated_archive()).await;
    app.screen = Screen::Help;
    check_all("help", &app);
    app.screen = Screen::Legacy;
    check_all("legacy", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn identity_screen() {
    let (mut app, _events) = app_with(populated_archive()).await;
    app.pending_joins.push(gchat_tui::app::PendingJoin {
        req_id: 42,
        display: "me".into(),
        package_b64: "QUJD".into(),
    });
    press(&mut app, &[KeyCode::Char('i')]);
    check_all("identity", &app);
}

#[tokio::test(flavor = "multi_thread")]
async fn paste_mode_and_mono_at_phone_width() {
    let (mut app, _events) = app_with(ArchiveData::default()).await;
    app.screen = Screen::Form(Form::admit());
    app.paste_mode = true;
    check("paste_mode", &app, 50, 20).unwrap();
    let (mut mono, _events) = app_with(populated_archive()).await;
    mono.mono = true;
    mono.screen = Screen::Channel { id: channel_id(1) };
    check("mono_channel", &mono, 50, 20).unwrap();
}
