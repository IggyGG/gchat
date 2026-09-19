//! Runs `Cmd`s against the core. Nothing here blocks the render loop: every
//! core call is spawned and reports back through the op channel.

use crate::app::{App, Cmd, OpDone, RelayState, RuntimeKind, StatusKind, Unlocked};
use crate::clipboard;
use crate::form::{Back, UnlockMode, WizardCmd};
use gchat_core::client::{ClientHandle, NodeInfo};
use gchat_core::paths::AppPaths;
use gchat_core::runtime::ProtocolRuntime;
use gchat_core::store::StoreKind;
use std::net::SocketAddr;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tokio::sync::mpsc;
use zeroize::Zeroizing;

/// How long a minted invite link stays valid.
const INVITE_TTL_SECS: u64 = 3600;
/// How long the friend's app waits for the owner to service a redeem before
/// giving up (covers a briefly-offline owner).
const JOIN_WAIT_SECS: u64 = 120;

/// Where the identity comes from for this session.
#[derive(Clone, Debug)]
pub enum Mode {
    /// Protocol runtime hosted in-process: `profile` + `archive` on disk.
    Hosted {
        profile: PathBuf,
        archive: PathBuf,
        create_profile: bool,
    },
    /// Attach to a daemon; only the archive is ours.
    Attached { socket: PathBuf, archive: PathBuf },
    /// Legacy combined store (`--store` with no daemon).
    Legacy { store: PathBuf, create: bool },
}

impl Mode {
    pub fn unlock_mode(&self) -> UnlockMode {
        match self {
            Mode::Hosted {
                create_profile: true,
                ..
            }
            | Mode::Legacy { create: true, .. } => UnlockMode::CreateProfile,
            Mode::Hosted { .. } | Mode::Legacy { .. } => UnlockMode::UnlockProfile,
            Mode::Attached { archive, .. } => {
                if archive.exists() {
                    UnlockMode::UnlockArchive
                } else {
                    UnlockMode::CreateArchive
                }
            }
        }
    }
    /// The file the passphrase protects.
    pub fn location(&self) -> &Path {
        match self {
            Mode::Hosted { profile, .. } => profile,
            Mode::Attached { archive, .. } => archive,
            Mode::Legacy { store, .. } => store,
        }
    }
    /// Free text for the unlock form's runtime line.
    pub fn runtime_line(&self) -> String {
        match self {
            Mode::Hosted { .. } => String::new(),
            Mode::Attached { socket, .. } => socket.display().to_string(),
            Mode::Legacy { .. } => "legacy combined store".into(),
        }
    }
}

/// How the inbox relay is obtained.
#[derive(Clone, Debug)]
pub enum RelaySource {
    None,
    Card(NodeInfo),
    Bootstrap(Vec<String>),
}

/// Long-lived context the executor needs for every command.
pub struct RuntimeCtx {
    pub mode: Mode,
    pub paths: Option<AppPaths>,
    pub listen: SocketAddr,
    pub local_fixture: bool,
    pub gc2_carrier: bool,
    pub advertise: Option<SocketAddr>,
    pub catalog_urls: Vec<String>,
    pub relay: RelaySource,
    pub op_tx: mpsc::UnboundedSender<OpDone>,
}

impl RuntimeCtx {
    pub fn outbox(&self) -> Option<PathBuf> {
        self.paths.as_ref().map(|paths| paths.outbox.clone())
    }
}

// Local profile startup never waits for DNS or a bootstrap endpoint.
fn resolve_relay(source: &RelaySource) -> (Option<NodeInfo>, RelayState) {
    match source {
        RelaySource::None => (None, RelayState::None),
        RelaySource::Card(card) => (Some(card.clone()), RelayState::Ready(relay_label(card))),
        RelaySource::Bootstrap(_) => (None, RelayState::Ready("connecting…".into())),
    }
}

fn relay_label(card: &NodeInfo) -> String {
    card.aliases
        .first()
        .map_or_else(|| "relay".into(), |alias| alias.target.address.to_string())
}

/// Path of a written outbox file.
fn export(outbox: &Path, name: &str, text: &str) -> Result<PathBuf, String> {
    gchat_core::paths::ensure_private_dir(outbox, "outbox")?;
    let stamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map_or(0, |d| d.as_secs());
    let path = outbox.join(format!("{name}-{stamp}.txt"));
    let mut options = std::fs::OpenOptions::new();
    options.write(true).create_new(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.mode(0o600);
    }
    let mut file = options
        .open(&path)
        .map_err(|error| format!("write {}: {error}", path.display()))?;
    use std::io::Write;
    file.write_all(text.as_bytes())
        .and_then(|_| file.write_all(b"\n"))
        .and_then(|_| file.sync_all())
        .map_err(|error| error.to_string())?;
    drop(file);
    // Owner-only on every platform (an elevated Windows shell would
    // otherwise leave the file owned by Administrators).
    gchat_core::private_fs::make_private(&path, false)?;
    Ok(path)
}

/// Starts (or performs inline) the core call a Cmd stands for.
pub fn spawn_cmd(cmd: Cmd, app: &mut App, ctx: &mut RuntimeCtx) {
    let tx = ctx.op_tx.clone();
    match cmd {
        Cmd::Quit => app.quit = true,
        Cmd::Copy(text) => {
            let outcome = clipboard::copy(&text);
            let kind = if outcome.is_failure() {
                StatusKind::Err
            } else if outcome == clipboard::CopyOutcome::Osc52 {
                StatusKind::Warn
            } else {
                StatusKind::Ok
            };
            app.set_status(outcome.message(), kind);
        }
        Cmd::Export { name, text } => match ctx.outbox() {
            Some(outbox) => match export(&outbox, name, &text) {
                Ok(path) => app.ok(format!("exported to {}", path.display())),
                Err(error) => app.err(error),
            },
            None => app.err("no outbox for this session (run with default paths or --home)"),
        },
        Cmd::Save { manual } => {
            let Some(client) = app.client.clone() else {
                return;
            };
            if manual {
                app.info("saving…");
            }
            tokio::spawn(async move {
                let res = client.save().await;
                let _ = tx.send(OpDone::Saved { res, manual });
            });
        }
        Cmd::Refresh => {
            let Some(client) = app.client.clone() else {
                return;
            };
            // One combined notice, so a relay outcome is never overwritten
            // by the (usually faster) catalog result.
            let relay_urls = match (&app.relay, &ctx.relay) {
                (RelayState::Failed(_), RelaySource::Bootstrap(urls)) => Some(urls.clone()),
                _ => None,
            };
            let has_catalogs = !client.catalog_urls().is_empty();
            tokio::spawn(async move {
                let mut notes = Vec::new();
                let mut failed = false;
                if let Some(urls) = relay_urls {
                    match client.bootstrap_routing(&urls).await {
                        Ok(label) => {
                            let _ = tx.send(OpDone::RelayFetched(Ok(label)));
                            notes.push("relay reachable again".to_string());
                        }
                        Err(error) => {
                            failed = true;
                            notes.push(format!("relay still unavailable: {error}"));
                        }
                    }
                }
                if has_catalogs {
                    match client.refresh_catalogs().await {
                        Ok(()) => notes.push("catalogs refreshed".into()),
                        Err(error) => {
                            failed = true;
                            notes.push(format!("catalogs: {error}"));
                        }
                    }
                }
                if notes.is_empty() {
                    notes.push("nothing to refresh (no relay failure, no catalogs)".into());
                }
                let text = notes.join("; ");
                let _ = tx.send(OpDone::Notice(if failed { Err(text) } else { Ok(text) }));
            });
        }
        Cmd::SendChannel { id, text } => {
            let Some(client) = app.client.clone() else {
                return;
            };
            app.info("sending…");
            tokio::spawn(async move {
                let res = client.send_channel(id, &text).await;
                let _ = tx.send(OpDone::Sent { text, res });
            });
        }
        Cmd::SendPm { id, text } => {
            let Some(client) = app.client.clone() else {
                return;
            };
            app.info("sending channel-scoped PM…");
            tokio::spawn(async move {
                let res = client.send_scoped_pm(id, &text).await;
                let _ = tx.send(OpDone::Sent { text, res });
            });
        }
        Cmd::JoinPublic {
            descriptor,
            display,
        } => {
            let Some(client) = app.client.clone() else {
                return;
            };
            tokio::spawn(async move {
                let res = client.join_public(&descriptor, &display).await;
                let _ = tx.send(OpDone::PublicJoined {
                    descriptor,
                    display,
                    res,
                });
            });
        }
        Cmd::CreateInvite { id, name } => {
            let Some(client) = app.client.clone() else {
                return;
            };
            app.info("creating invite…");
            tokio::spawn(async move {
                let res = client.create_invite(id, INVITE_TTL_SECS).await;
                let _ = tx.send(OpDone::InviteCreated { channel: name, res });
            });
        }
        Cmd::RemoveMember { channel, member } => {
            let Some(client) = app.client.clone() else {
                return;
            };
            tokio::spawn(async move {
                let res = client
                    .remove_member(channel, member)
                    .await
                    .map(|_| "member removed".into());
                let _ = tx.send(OpDone::Notice(res));
            });
        }
        Cmd::Spawn(wizard) => spawn_wizard(wizard, app, ctx),
    }
}

fn spawn_wizard(wizard: WizardCmd, app: &mut App, ctx: &mut RuntimeCtx) {
    let tx = ctx.op_tx.clone();
    match wizard {
        WizardCmd::Unlock { create, pass } => spawn_unlock(create, pass, app, ctx),
        WizardCmd::CreateChannel {
            channel,
            display,
            capacity,
            public,
        } => {
            let Some(client) = app.client.clone() else {
                return;
            };
            app.info(format!("creating #{channel}…"));
            tokio::spawn(async move {
                let res = client
                    .create_channel(
                        &channel,
                        &display,
                        capacity,
                        if public {
                            gcoms_sdk::ChannelVisibility::Public
                        } else {
                            gcoms_sdk::ChannelVisibility::Private
                        },
                    )
                    .await;
                let _ = tx.send(OpDone::ChannelCreated { channel, res });
            });
        }
        WizardCmd::JoinBegin { display } => {
            let Some(client) = app.client.clone() else {
                return;
            };
            app.info("preparing join request…");
            tokio::spawn(async move {
                let res = client.prepare_join(&display).await;
                let _ = tx.send(OpDone::JoinPrepared { display, res });
            });
        }
        WizardCmd::JoinWithInvite { link, display } => {
            let Some(client) = app.client.clone() else {
                return;
            };
            app.info("joining… (waiting for the channel owner to be online)");
            tokio::spawn(async move {
                let res = client
                    .join_with_invite(&link, &display, JOIN_WAIT_SECS)
                    .await;
                let _ = tx.send(OpDone::InviteJoined { res });
            });
        }
        WizardCmd::JoinFinish {
            req_id,
            channel,
            display,
            welcome,
        } => {
            let Some(client) = app.client.clone() else {
                return;
            };
            app.info(format!("joining #{channel}…"));
            tokio::spawn(async move {
                let res = client
                    .join_channel(req_id, &channel, &display, &welcome)
                    .await;
                let _ = tx.send(OpDone::JoinFinished {
                    req_id,
                    channel,
                    res,
                });
            });
        }
        WizardCmd::Admit {
            channel,
            member,
            key_package,
        } => {
            let Some(client) = app.client.clone() else {
                return;
            };
            app.info(format!("admitting {member}…"));
            tokio::spawn(async move {
                let res = client.admit(&channel, &key_package, &member).await;
                let _ = tx.send(OpDone::Admitted { res });
            });
        }
        WizardCmd::Publish {
            channel_id,
            description,
            catalog,
        } => {
            let Some(client) = app.client.clone() else {
                return;
            };
            app.info("publishing…");
            tokio::spawn(async move {
                let res = client
                    .publish_channel(channel_id, &description, &catalog)
                    .await
                    .map(|_| "public descriptor published".into());
                let _ = tx.send(OpDone::Wizard {
                    back: Back::Channel(channel_id),
                    res,
                });
            });
        }
    }
}

fn spawn_unlock(create: bool, pass: String, app: &mut App, ctx: &mut RuntimeCtx) {
    app.info(if create {
        "creating profile…"
    } else {
        "unlocking…"
    });
    let tx = ctx.op_tx.clone();
    let mode = ctx.mode.clone();
    let listen = ctx.listen;
    let local_fixture = ctx.local_fixture;
    let gc2_carrier = ctx.gc2_carrier;
    let advertise = ctx.advertise;
    let catalog_urls = ctx.catalog_urls.clone();
    let pass = Zeroizing::new(pass);
    let relay_source = ctx.relay.clone();
    let warn_tx = tx.clone();
    tokio::spawn(async move {
        let (relay_card, relay_state) = if matches!(mode, Mode::Attached { .. }) {
            (None, RelayState::Daemon)
        } else {
            resolve_relay(&relay_source)
        };
        let booted: Result<(ClientHandle, RuntimeKind), String> = match &mode {
            Mode::Hosted {
                profile,
                archive,
                create_profile,
            } => {
                // Hosted relay transit admits public targets; no private
                // FRWD target CIDRs are implicitly allowed.
                let runtime = if *create_profile {
                    if local_fixture {
                        ProtocolRuntime::create_fixture(
                            profile,
                            &pass,
                            listen,
                            advertise,
                            relay_card,
                            &[],
                        )
                        .await
                    } else if gc2_carrier {
                        ProtocolRuntime::create_protected(
                            profile,
                            &pass,
                            listen,
                            advertise,
                            relay_card,
                            &[],
                        )
                        .await
                    } else {
                        ProtocolRuntime::create(profile, &pass, listen, advertise, relay_card, &[])
                            .await
                    }
                } else {
                    if local_fixture {
                        ProtocolRuntime::unlock_fixture(
                            profile,
                            &pass,
                            listen,
                            advertise,
                            relay_card,
                            &[],
                        )
                        .await
                    } else if gc2_carrier {
                        ProtocolRuntime::unlock_protected(
                            profile,
                            &pass,
                            listen,
                            advertise,
                            relay_card,
                            &[],
                        )
                        .await
                    } else {
                        ProtocolRuntime::unlock(profile, &pass, listen, advertise, relay_card, &[])
                            .await
                    }
                }
                .map_err(|error| friendly_lock_error(error, profile));
                match runtime {
                    Ok(runtime) => {
                        let sink_tx = warn_tx.clone();
                        runtime.set_error_sink(Arc::new(move |message| {
                            let _ = sink_tx.send(OpDone::Warning(message));
                        }));
                        let create_archive = !archive.exists();
                        match ClientHandle::open_hosted(
                            archive,
                            &pass,
                            runtime.clone(),
                            create_archive,
                        )
                        .await
                        {
                            Ok(client) => Ok((client, RuntimeKind::Hosted)),
                            Err(error) => {
                                let _ = runtime.shutdown().await;
                                Err(error)
                            }
                        }
                    }
                    Err(error) => Err(error),
                }
            }
            Mode::Attached { socket, archive } => {
                let create = !archive.exists();
                ClientHandle::connect_daemon(archive, &pass, socket, create)
                    .await
                    .map(|client| (client, RuntimeKind::Daemon(socket.clone())))
                    .map_err(|error| friendly_socket_error(error, socket))
            }
            Mode::Legacy { store, create } => {
                let result = if *create {
                    if local_fixture {
                        ClientHandle::create_profile_fixture(
                            store, &pass, listen, advertise, relay_card,
                        )
                        .await
                    } else {
                        ClientHandle::create_profile(store, &pass, listen, advertise, relay_card)
                            .await
                    }
                } else {
                    if local_fixture {
                        ClientHandle::unlock_fixture(store, &pass, listen, advertise, relay_card)
                            .await
                    } else {
                        ClientHandle::unlock(store, &pass, listen, advertise, relay_card).await
                    }
                };
                result
                    .map(|client| (client, RuntimeKind::Embedded))
                    .map_err(|error| friendly_lock_error(error, store))
            }
        };
        match booted {
            Ok((client, runtime)) => {
                // Hand the local archive to the existing UI immediately. Discovery
                // and catalog recovery complete using the same notices as refresh.
                let background = client.clone();
                let _ = tx.send(OpDone::Unlock(Ok(Unlocked {
                    client,
                    runtime,
                    relay: relay_state,
                    catalog_warning: None,
                })));
                if let RelaySource::Bootstrap(urls) = relay_source {
                    if !matches!(mode, Mode::Attached { .. }) && !local_fixture {
                        let result = background.bootstrap_routing(&urls).await;
                        let _ = tx.send(OpDone::RelayFetched(result));
                    }
                }
                if let Err(error) = background.configure_catalogs(&catalog_urls).await {
                    let _ = tx.send(OpDone::Warning(error));
                }
            }
            Err(error) => {
                let _ = tx.send(OpDone::Unlock(Err(error)));
            }
        }
    });
}

/// A locked profile almost always means another gchat (or a daemon).
fn friendly_lock_error(error: String, path: &Path) -> String {
    if error.contains("already in use") {
        format!(
            "{} is locked by another process (a running gchat or gchat daemon?). \
             Stop it, or attach to it with: gchat --daemon-socket <socket>",
            path.display()
        )
    } else {
        error
    }
}

fn friendly_socket_error(error: String, socket: &Path) -> String {
    if error.contains("No such file") || error.contains("refused") || error.contains("os error") {
        format!(
            "cannot reach the daemon at {}: {error}. Is `gchat daemon` running?",
            socket.display()
        )
    } else {
        error
    }
}

/// Decide the mode from the flags and the filesystem (see the plan's
/// create-vs-unlock matrix). Never mints an identity silently.
pub fn decide_mode(
    paths: &AppPaths,
    store: Option<&Path>,
    create_flag: bool,
    daemon_socket: Option<&Path>,
    probe_live: bool,
) -> Result<Mode, String> {
    if let Some(socket) = daemon_socket {
        let archive = store.map_or_else(|| paths.archive.clone(), Path::to_path_buf);
        return Ok(Mode::Attached {
            socket: socket.to_path_buf(),
            archive,
        });
    }
    if let Some(store) = store {
        return match gchat_core::store::store_kind(store) {
            Ok(StoreKind::Combined) => Ok(Mode::Legacy {
                store: store.to_path_buf(),
                create: false,
            }),
            Ok(StoreKind::Protocol) => Ok(Mode::Hosted {
                profile: store.to_path_buf(),
                archive: store.with_file_name("chat.gcarchive"),
                create_profile: false,
            }),
            Ok(StoreKind::Archive) => Err(format!(
                "{} is a chat archive; pass --daemon-socket to use it with a daemon",
                store.display()
            )),
            Err(_) if !store.exists() && create_flag => Ok(Mode::Legacy {
                store: store.to_path_buf(),
                create: true,
            }),
            Err(_) if !store.exists() => Err(format!(
                "no store at {}; pass --create to make a new identity here, or check the path",
                store.display()
            )),
            Err(error) => Err(format!("{}: {error}", store.display())),
        };
    }
    if probe_live {
        return Ok(Mode::Attached {
            socket: paths.socket.clone(),
            archive: paths.archive.clone(),
        });
    }
    let profile_exists = paths.profile.exists();
    let archive_exists = paths.archive.exists();
    if !profile_exists && archive_exists {
        return Err(format!(
            "{} exists but {} is missing; restore the profile or move the archive away \
             (a new identity would not be able to read it)",
            paths.archive.display(),
            paths.profile.display()
        ));
    }
    Ok(Mode::Hosted {
        profile: paths.profile.clone(),
        archive: paths.archive.clone(),
        create_profile: !profile_exists,
    })
}

/// Try the default socket briefly. A live daemon means attach mode.
pub async fn probe_daemon(socket: &Path) -> bool {
    // A Unix socket is a filesystem object; a Windows pipe path is a logical
    // name that `gc-sdk` maps to `\\.\pipe\...`, so only skip the connect
    // attempt where the path is expected to exist.
    if cfg!(unix) && !socket.exists() {
        return false;
    }
    use gcoms_sdk::ipc::Capability;
    let attempt =
        gcoms_sdk::IpcClient::connect(socket, "gchat-probe", vec![Capability::IdentityRead]);
    matches!(
        tokio::time::timeout(std::time::Duration::from_millis(500), attempt).await,
        Ok(Ok(_))
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use gchat_core::paths::{resolve_with, Platform};

    fn paths(dir: &Path) -> AppPaths {
        resolve_with(Some(dir), Platform::Unix, &|_| None).unwrap()
    }

    #[test]
    fn fresh_home_hosts_and_creates() {
        let temp = tempfile::tempdir().unwrap();
        let mode = decide_mode(&paths(temp.path()), None, false, None, false).unwrap();
        assert!(matches!(
            mode,
            Mode::Hosted {
                create_profile: true,
                ..
            }
        ));
        assert_eq!(mode.unlock_mode(), UnlockMode::CreateProfile);
    }

    #[test]
    fn orphan_archive_is_an_error_not_a_new_identity() {
        let temp = tempfile::tempdir().unwrap();
        let p = paths(temp.path());
        std::fs::write(&p.archive, b"GCCAR2junk").unwrap();
        let error = decide_mode(&p, None, false, None, false).unwrap_err();
        assert!(error.contains("profile.gcprotocol is missing"), "{error}");
    }

    #[test]
    fn live_socket_attaches() {
        let temp = tempfile::tempdir().unwrap();
        let mode = decide_mode(&paths(temp.path()), None, false, None, true).unwrap();
        assert!(matches!(mode, Mode::Attached { .. }));
        assert_eq!(mode.unlock_mode(), UnlockMode::CreateArchive);
    }

    #[test]
    fn explicit_store_never_silently_creates() {
        let temp = tempfile::tempdir().unwrap();
        let p = paths(temp.path());
        let missing = temp.path().join("typo.gcstore");
        let error = decide_mode(&p, Some(&missing), false, None, false).unwrap_err();
        assert!(error.contains("--create"), "{error}");
        let mode = decide_mode(&p, Some(&missing), true, None, false).unwrap();
        assert!(matches!(mode, Mode::Legacy { create: true, .. }));
    }

    #[test]
    fn lock_errors_explain_themselves() {
        let text = friendly_lock_error("profile is already in use: x".into(), Path::new("/p"));
        assert!(text.contains("gchat daemon"));
        assert_eq!(
            friendly_lock_error("other".into(), Path::new("/p")),
            "other"
        );
    }
}
