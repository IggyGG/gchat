//! gchat: terminal client for the GC/1 protocol, and (as `gchat daemon`)
//! the headless runtime.

use clap::{Parser, Subcommand};
use crossterm::event::{self, DisableBracketedPaste, EnableBracketedPaste, Event, KeyEventKind};
use crossterm::execute;
use crossterm::terminal::{
    disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen,
};
use gchat_core::client::{decode_relay_card, NodeEvent};
use gchat_core::daemon::DaemonArgs;
use gchat_core::paths::{self, AppPaths};
use gchat_tui::app::{App, OpDone};
use gchat_tui::exec::{decide_mode, probe_daemon, spawn_cmd, Mode, RelaySource, RuntimeCtx};
use gchat_tui::ui;
use ratatui::backend::CrosstermBackend;
use ratatui::Terminal;
use std::io::stdout;
use std::net::SocketAddr;
use std::path::PathBuf;
use std::time::Duration;
use tokio::sync::mpsc;

#[derive(Parser)]
#[command(
    name = "gchat",
    version,
    about = "Private, end-to-end encrypted chat in your terminal. Just run `gchat` to start.",
    long_about = "gchat is a private chat app that runs in your terminal.\n\n\
Run `gchat` with no arguments to start: the first time, it asks you to choose a \
passphrase (8+ characters) and creates an encrypted profile in your home directory. \
There is no passphrase reset, so pick one you will remember.\n\n\
Your messages reach participants through a relay (a server that holds them until the other \
participant is online). A default relay is built in; `--relay-bootstrap-url` points at a \
different one and `--no-relay` uses saved routing information or an invite.\n\n\
`gchat paths` shows where your profile and messages are stored and which relay is in use. \
`gchat` starts or attaches to one background instance. Ctrl+Q closes only this view.\n\n\
Use /help or F1 for commands, Alt+Left/Right for windows, F5 for channels, F6 for nicks, \
Tab for completion, Ctrl+F for transcript search and Ctrl+End for latest messages. \
/lock hides the archive in every view while receiving continues; /quit disconnects the instance."
)]
struct Cli {
    #[command(subcommand)]
    command: Option<Command>,
    #[command(flatten)]
    ui: UiArgs,
}

#[derive(Subcommand)]
enum Command {
    /// Save an installation network invitation from an owner-private file.
    Network {
        #[arg(long)]
        invitation_file: PathBuf,
    },
    /// Keep receiving messages in the background while the app is closed
    /// (same as `gcd`; uses the same profile and paths).
    Daemon(Box<DaemonArgs>),
    /// Show where your profile and messages live, which relay is in use, and
    /// whether a background daemon is running.
    Paths,
    /// Copy a stopped legacy combined profile into a new instance, preserving its identity.
    Migrate {
        #[arg(long)]
        source: PathBuf,
        #[arg(long)]
        destination: PathBuf,
        #[arg(long)]
        passphrase_file: PathBuf,
    },
}

#[derive(clap::Args, Clone)]
struct UiArgs {
    /// Read older combined stores through the compatibility terminal interface.
    #[arg(long)]
    legacy_ui: bool,
    /// Bind to this exact shared chat endpoint without starting another service.
    #[arg(long)]
    chat_socket: Option<PathBuf>,
    /// Directory holding profile, archive and socket (replaces the platform
    /// defaults). Also read from `GCHAT_HOME`.
    #[arg(long, env = "GCHAT_HOME")]
    home: Option<PathBuf>,
    /// Legacy encrypted profile store (`.gcstore`), or a `.gcprotocol` profile.
    /// Without it the platform default profile is used.
    #[arg(long)]
    store: Option<PathBuf>,
    /// With --store: create the store if it does not exist.
    #[arg(long)]
    create: bool,
    /// Explicit direct transport for disposable local fixtures.
    #[arg(long, hide = true)]
    local_fixture: bool,
    /// Local listener. Defaults to an ephemeral loopback port; a daemon uses
    /// 127.0.0.1:8443.
    #[arg(long)]
    listen: Option<SocketAddr>,
    /// Reachable address published in this client's contact card.
    #[arg(long)]
    advertise: Option<SocketAddr>,
    /// Contact-card file for a relay that will host this client's inboxes.
    #[arg(long)]
    inbox_relay_file: Option<PathBuf>,
    /// Trusted HTTPS bootstrap endpoint for automatic inbox provisioning.
    /// Repeatable; also `GC_RELAY_BOOTSTRAP_URLS` (comma separated).
    #[arg(
        long = "relay-bootstrap-url",
        env = "GC_RELAY_BOOTSTRAP_URLS",
        value_delimiter = ','
    )]
    relay_bootstrap_urls: Vec<String>,
    /// JSON file `{"relay_bootstrap_urls": [...]}` with bootstrap endpoints.
    #[arg(long)]
    relay_bootstrap_config: Option<PathBuf>,
    /// Do not use any relay, even the one compiled in.
    #[arg(long)]
    no_relay: bool,
    /// Attach to the chat service beside this protocol socket; --store is
    /// then the chat archive. Use --chat-socket to select the chat endpoint directly.
    #[arg(long)]
    daemon_socket: Option<PathBuf>,
    /// Public catalog base URL. Repeat for multiple catalogs.
    #[arg(long = "catalog-url", env = "GC_CATALOG_URLS", value_delimiter = ',')]
    catalog_urls: Vec<String>,
    /// File containing one public catalog base URL per line.
    #[arg(long, env = "GC_CATALOG_CONFIG")]
    catalog_config: Option<PathBuf>,
    /// Render without colour (also honours NO_COLOR).
    #[arg(long)]
    mono: bool,
}

/// Restores the terminal on drop (normal exit and unwinding).
struct TermGuard;

impl Drop for TermGuard {
    fn drop(&mut self) {
        let _ = disable_raw_mode();
        let _ = execute!(stdout(), LeaveAlternateScreen, DisableBracketedPaste);
    }
}

fn install_panic_hook() {
    let prev = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        let _ = disable_raw_mode();
        let _ = execute!(stdout(), LeaveAlternateScreen, DisableBracketedPaste);
        prev(info);
    }));
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();
    let result = match cli.command {
        Some(Command::Daemon(mut args)) => {
            if args.home.is_none() {
                args.home = cli.ui.home.clone();
            }
            gchat_core::daemon::run(*args).await
        }
        Some(Command::Paths) => print_paths(&cli.ui).await,
        Some(Command::Network { invitation_file }) => import_network(&cli.ui, &invitation_file),
        Some(Command::Migrate {
            source,
            destination,
            passphrase_file,
        }) => migrate(&source, &destination, &passphrase_file),
        None => run(cli.ui).await,
    };
    if let Err(e) = result {
        eprintln!("gchat: {e}");
        std::process::exit(1);
    }
}

fn migrate(
    source: &std::path::Path,
    destination: &std::path::Path,
    passphrase_file: &std::path::Path,
) -> Result<(), String> {
    gchat_core::private_fs::validate_private_file(passphrase_file, "migration passphrase")?;
    gchat_core::private_fs::validate_private_parent(passphrase_file, "migration passphrase")?;
    if std::fs::metadata(passphrase_file)
        .map_err(|e| e.to_string())?
        .len()
        > 4096
    {
        return Err("passphrase exceeds bound".into());
    }
    let passphrase = zeroize::Zeroizing::new(
        std::fs::read_to_string(passphrase_file).map_err(|e| e.to_string())?,
    );
    gchat_core::store::migrate_combined(
        source,
        destination,
        passphrase.trim_end_matches(['\r', '\n']),
    )?;
    println!(
        "Migrated instance: {}. The original encrypted profile is retained.",
        destination.display()
    );
    Ok(())
}

fn import_network(args: &UiArgs, invitation_file: &std::path::Path) -> Result<(), String> {
    let paths = paths::resolve(args.home.as_deref())?;
    let profile = args.store.clone().unwrap_or(paths.profile);
    let parent = profile.parent().ok_or("profile parent missing")?;
    paths::ensure_private_dir(parent, "network instance")?;
    gchat_core::bootstrap::import_network_invitation(&profile, invitation_file)?;
    println!("Network invitation saved for this instance.");
    Ok(())
}

async fn print_paths(args: &UiArgs) -> Result<(), String> {
    let paths = paths::resolve(args.home.as_deref())?;
    let live = probe_daemon(&paths.socket).await;
    println!("data      {}", paths.data_dir.display());
    println!("config    {}", paths.config_dir.display());
    println!("runtime   {}", paths.runtime_dir.display());
    println!(
        "profile   {}{}",
        paths.profile.display(),
        if paths.profile.exists() {
            ""
        } else {
            "  (missing: first run creates it)"
        }
    );
    println!(
        "archive   {}{}",
        paths.archive.display(),
        if paths.archive.exists() {
            ""
        } else {
            "  (missing)"
        }
    );
    println!("outbox    {}", paths.outbox.display());
    println!(
        "socket    {}  {}",
        paths.socket.display(),
        if live {
            "(daemon running: gchat attaches)"
        } else {
            "(no daemon: gchat hosts the runtime)"
        }
    );
    let relay = relay_source(args)?;
    match &relay {
        RelaySource::None if args.no_relay => {
            println!("relay     saved routing information or an invite (--no-relay)");
        }
        RelaySource::None => {
            println!("relay     not configured");
            println!("          use the GChat network defaults and import a network invitation.");
        }
        RelaySource::Card(_) => println!("relay     card file"),
        RelaySource::Bootstrap(urls) => println!("relay     {}", urls.join(", ")),
    }
    let mut ok = true;
    for (dir, label) in paths.private_dirs() {
        if dir.exists() {
            match gchat_core::private_fs::validate_private_dir(dir, label) {
                Ok(()) => println!("ok        {label} is private"),
                Err(error) => {
                    ok = false;
                    println!("PROBLEM   {}", paths::remediation(dir, &error));
                }
            }
        }
    }
    if ok {
        Ok(())
    } else {
        Err("fix the problems above and run again".into())
    }
}

fn relay_source(args: &UiArgs) -> Result<RelaySource, String> {
    if args.no_relay {
        return Ok(RelaySource::None);
    }
    if let Some(path) = &args.inbox_relay_file {
        if !args.relay_bootstrap_urls.is_empty() || args.relay_bootstrap_config.is_some() {
            return Err(
                "--inbox-relay-file cannot be combined with relay bootstrap options".into(),
            );
        }
        let card = std::fs::read_to_string(path).map_err(|e| e.to_string())?;
        return Ok(RelaySource::Card(decode_relay_card(&card)?));
    }
    // Flags already merged the env var; the config file is added here.
    let mut urls = gchat_core::daemon::bootstrap_values(
        &args.relay_bootstrap_urls,
        args.relay_bootstrap_config.as_deref(),
    )?;
    urls.dedup();
    if urls.is_empty() {
        urls.extend(gchat_core::bootstrap::default_provider_urls());
    }
    Ok(if urls.is_empty() {
        RelaySource::None
    } else {
        RelaySource::Bootstrap(urls)
    })
}

async fn run_shared(args: UiArgs) -> Result<(), String> {
    use gchat_core::chat_service::host::{ensure_running, InstanceConfig};
    let mut config = InstanceConfig::from_home(args.home.as_deref())?;
    if let Some(socket) = args.chat_socket {
        let client = gchat_api::ChatClient::connect(&socket, None).await?;
        return gchat_tui::service_ui::run(client, args.mono).await;
    }
    let explicit_daemon = args.daemon_socket.is_some();
    if let Some(socket) = args.daemon_socket.clone() {
        config.protocol_socket = socket;
    }
    if let Some(store) = args.store.clone() {
        if explicit_daemon {
            config.archive = store;
        } else {
            if store.exists()
                && gchat_core::store::store_kind(&store)? == gchat_core::store::StoreKind::Combined
            {
                return Err("this is a legacy combined store; use --legacy-ui until it is migrated to an instance".into());
            }
            config.archive = store.with_file_name("chat.gcarchive");
            config.profile = store;
        }
    }
    config.listen = args.listen.unwrap_or(config.listen);
    config.advertise = args.advertise;
    config.network_recovery = !args.no_relay;
    config.local_fixture = args.local_fixture;
    config.relay_file = args.inbox_relay_file.clone();
    config.relay_urls = match relay_source(&args)? {
        RelaySource::Bootstrap(urls) => urls,
        _ => Vec::new(),
    };
    config.catalog_urls = args.catalog_urls.clone();
    if let Some(path) = args.catalog_config {
        config.catalog_urls.extend(
            std::fs::read_to_string(path)
                .map_err(|e| e.to_string())?
                .lines()
                .map(str::trim)
                .filter(|s| !s.is_empty() && !s.starts_with('#'))
                .map(str::to_owned),
        );
    }
    let client = if explicit_daemon {
        gchat_api::ChatClient::connect(&config.chat_endpoint(), None).await?
    } else {
        ensure_running(
            &config,
            &std::env::current_exe().map_err(|e| e.to_string())?,
            true,
        )
        .await?
    };
    gchat_tui::service_ui::run(client, args.mono || std::env::var_os("NO_COLOR").is_some()).await
}

async fn run(mut args: UiArgs) -> Result<(), String> {
    if !args.legacy_ui {
        return run_shared(args).await;
    }
    if let Some(path) = &args.catalog_config {
        let configured = std::fs::read_to_string(path).map_err(|error| error.to_string())?;
        args.catalog_urls.extend(
            configured
                .lines()
                .map(str::trim)
                .filter(|line| !line.is_empty() && !line.starts_with('#'))
                .map(str::to_owned),
        );
    }
    if args.daemon_socket.is_some() && (args.advertise.is_some() || args.inbox_relay_file.is_some())
    {
        return Err(
            "--daemon-socket cannot be combined with --advertise or --inbox-relay-file".into(),
        );
    }
    if args
        .advertise
        .is_some_and(|addr| addr.ip().is_unspecified())
    {
        return Err("--advertise must be a reachable address, not a wildcard".into());
    }
    let relay = relay_source(&args)?;
    let paths: AppPaths = paths::resolve(args.home.as_deref())?;
    let using_defaults = args.store.is_none() && args.daemon_socket.is_none();
    if using_defaults {
        for (dir, label) in paths.private_dirs() {
            paths::ensure_private_dir(dir, label)?;
        }
    }
    let live = using_defaults && probe_daemon(&paths.socket).await;
    let mode = decide_mode(
        &paths,
        args.store.as_deref(),
        args.create,
        args.daemon_socket.as_deref(),
        live,
    )?;
    let listen = args.listen.unwrap_or_else(|| {
        if args.local_fixture {
            "127.0.0.1:0"
        } else {
            "0.0.0.0:0"
        }
        .parse()
        .expect("static address")
    });
    // The local archive opens before private routing discovery starts.
    install_panic_hook();

    // Terminal input arrives on a dedicated std thread (crossterm's poll
    // is blocking); events are forwarded into the tokio loop.
    let (term_tx, mut term_rx) = mpsc::unbounded_channel::<Event>();
    std::thread::spawn(move || loop {
        match event::poll(Duration::from_millis(200)) {
            Ok(true) => match event::read() {
                Ok(ev) => {
                    if term_tx.send(ev).is_err() {
                        break;
                    }
                }
                Err(_) => break,
            },
            Ok(false) => {}
            Err(_) => break,
        }
    });
    let (op_tx, mut op_rx) = mpsc::unbounded_channel::<OpDone>();
    let mut ctx = RuntimeCtx {
        mode: mode.clone(),
        paths: Some(paths.clone()),
        listen,
        local_fixture: args.local_fixture,
        advertise: args.advertise,
        catalog_urls: args.catalog_urls.clone(),
        relay,
        op_tx,
    };

    let outcome = {
        enable_raw_mode().map_err(|e| e.to_string())?;
        execute!(stdout(), EnterAlternateScreen, EnableBracketedPaste)
            .map_err(|e| e.to_string())?;
        let _guard = TermGuard;
        let mut terminal =
            Terminal::new(CrosstermBackend::new(stdout())).map_err(|e| e.to_string())?;

        let mut app = App::new(mode.unlock_mode(), mode.location(), &mode.runtime_line());
        app.mono = args.mono
            || std::env::var_os("NO_COLOR").is_some_and(|v| !v.is_empty())
            || matches!(std::env::var("TERM").as_deref(), Ok("dumb") | Ok("linux"));
        app.session.profile = match &mode {
            Mode::Hosted { profile, .. } => Some(profile.clone()),
            Mode::Legacy { store, .. } => Some(store.clone()),
            Mode::Attached { .. } => None,
        };
        app.session.archive = match &mode {
            Mode::Hosted { archive, .. } | Mode::Attached { archive, .. } => Some(archive.clone()),
            Mode::Legacy { .. } => None,
        };
        app.session.outbox = Some(paths.outbox.clone());
        if let Ok((w, h)) = crossterm::terminal::size() {
            app.on_resize(w, h);
        }
        let mut node_rx: Option<mpsc::Receiver<NodeEvent>> = None;
        let mut tick = tokio::time::interval(Duration::from_millis(250));
        loop {
            tokio::select! {
                Some(ev) = term_rx.recv() => match ev {
                    Event::Key(k) if k.kind == KeyEventKind::Press => app.on_key(k),
                    Event::Paste(s) => app.on_paste(&s),
                    Event::Resize(w, h) => app.on_resize(w, h),
                    _ => {}
                },
                Some(op) = op_rx.recv() => match op {
                    OpDone::Unlock(Ok(unlocked)) => {
                        node_rx = Some(unlocked.client.subscribe());
                        app.on_unlocked(unlocked);
                    }
                    other => app.on_op(other),
                },
                ev = recv_node(&mut node_rx) => app.on_node_event(ev),
                _ = tick.tick() => app.on_tick(),
            }
            for cmd in app.drain_cmds() {
                spawn_cmd(cmd, &mut app, &mut ctx);
            }
            terminal
                .draw(|f| ui::draw(f, &app))
                .map_err(|e| e.to_string())?;
            if app.quit {
                break;
            }
        }
        app.client.clone()
    };
    match outcome {
        Some(client) => {
            println!("gchat: saving…");
            client.shutdown().await?;
            println!("gchat: session saved");
        }
        None => println!("gchat: nothing unlocked; no changes made"),
    }
    Ok(())
}

/// Waits for the next node event; pends forever when no client is
/// connected yet (or the node shut down).
async fn recv_node(rx: &mut Option<mpsc::Receiver<NodeEvent>>) -> NodeEvent {
    loop {
        match rx {
            Some(r) => match r.recv().await {
                Some(ev) => return ev,
                None => *rx = None,
            },
            None => std::future::pending::<()>().await,
        }
    }
}
