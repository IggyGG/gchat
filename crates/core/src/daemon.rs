//! Headless standalone runtime shared by `gchat daemon` and the desktop worker.

use crate::bootstrap::{fetch_relay_provision, parse_bootstrap_urls};
use crate::client::{decode_relay_card, NodeInfo};
use crate::private_fs::{validate_private_file, validate_private_parent};
use gcoms_sdk::ipc::Capability;
use std::net::SocketAddr;
use std::path::{Path, PathBuf};
use zeroize::Zeroizing;

#[derive(clap::Args, Clone)]
pub struct DaemonArgs {
    /// Start the instance locked; a bound UI unlocks it through the chat API.
    #[arg(long)]
    pub interactive: bool,
    /// Public catalog available to all UIs attached to this instance.
    #[arg(long)]
    pub chat_catalog_url: Vec<String>,
    /// Directory holding profile, archive and socket (replaces the platform
    /// defaults). Also read from `GCHAT_HOME`.
    #[arg(long, env = "GCHAT_HOME")]
    pub home: Option<PathBuf>,
    /// Encrypted client profile used by the daemon. Defaults to the platform
    /// profile path (see `gchat paths`).
    #[arg(long)]
    pub store: Option<PathBuf>,
    /// File containing the profile passphrase. A trailing CR/LF is removed.
    /// Defaults to `<config dir>/passphrase`.
    #[arg(long)]
    pub passphrase_file: Option<PathBuf>,
    /// Read the protocol passphrase from a private parent-process stdin pipe.
    #[arg(long, conflicts_with = "passphrase_file")]
    pub passphrase_stdin: bool,
    /// Service-owned chat archive. Chat scope enables the default automatically.
    #[arg(long)]
    pub chat_archive: Option<PathBuf>,
    /// Optionally unlock the service archive at startup using a private file.
    #[arg(long)]
    pub chat_passphrase_file: Option<PathBuf>,
    /// Local socket or Windows named-pipe endpoint exposed to SDK clients.
    /// Defaults to the platform runtime path.
    #[arg(long)]
    pub socket: Option<PathBuf>,
    /// Owner-only request file used by Windows per-user task shutdown.
    #[cfg(windows)]
    #[arg(long)]
    pub shutdown_request_file: Option<PathBuf>,
    /// Create a new profile; refuses to overwrite an existing profile.
    #[arg(long)]
    pub create: bool,
    /// Explicit direct transport for disposable local fixtures.
    #[arg(long, hide = true)]
    pub local_fixture: bool,
    /// Local GC listener.
    #[arg(long, default_value = "127.0.0.1:8443")]
    pub listen: SocketAddr,
    /// Reachable address published in this profile's contact card.
    #[arg(long)]
    pub advertise: Option<SocketAddr>,
    /// Contact-card file for a full relay hosting this profile's inboxes.
    #[arg(long)]
    pub inbox_relay_file: Option<PathBuf>,
    /// Private CIDR this daemon's FRWD target policy may dial — `CIDR`
    /// allows every target port in the range, `CIDR:PORT` pins one port
    /// (repeatable; one value also via `GC_FRWD_PRIVATE_CIDR`). Without it
    /// only public targets are permitted.
    #[arg(long = "allow-frwd-private-cidr", env = "GC_FRWD_PRIVATE_CIDR")]
    pub allow_frwd_private_cidrs: Vec<String>,
    /// Trusted HTTPS bootstrap endpoint for automatic inbox provisioning.
    /// Repeatable; may also come from `GC_RELAY_BOOTSTRAP_URLS` or
    /// `--relay-bootstrap-config`. Mutually exclusive with
    /// `--inbox-relay-file`.
    #[arg(long = "relay-bootstrap-url")]
    pub relay_bootstrap_urls: Vec<String>,
    /// JSON file `{"relay_bootstrap_urls": ["https://...", ...]}` with
    /// trusted bootstrap endpoints.
    #[arg(long)]
    pub relay_bootstrap_config: Option<PathBuf>,
    /// Keep local service and saved relay re-entry; disable direct HTTPS recovery.
    #[arg(long)]
    pub no_network_bootstrap: bool,
    /// Capability set exposed by this daemon socket.
    #[arg(long, value_enum, default_value_t = Scope::Chat)]
    pub scope: Scope,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, clap::ValueEnum)]
pub enum Scope {
    Chat,
}
pub fn scope_capabilities(_scope: Scope) -> Vec<Capability> {
    crate::chat_service::host::capabilities()
}
/// The three files a daemon needs, after platform defaults are applied.
pub struct DaemonPaths {
    pub store: PathBuf,
    pub passphrase_file: PathBuf,
    pub socket: PathBuf,
    /// True when `--socket` was omitted; the runtime directory is then ours
    /// to create. Explicit sockets keep their caller's directory untouched.
    pub socket_defaulted: bool,
}

impl DaemonArgs {
    /// Fill omitted `--store`, `--passphrase-file` and `--socket` from the
    /// platform defaults. Explicit values never consult the environment.
    pub fn resolve_paths(&self) -> Result<DaemonPaths, String> {
        let defaults =
            if self.store.is_none() || self.passphrase_file.is_none() || self.socket.is_none() {
                Some(crate::paths::resolve(self.home.as_deref())?)
            } else {
                None
            };
        let pick = |explicit: &Option<PathBuf>,
                    default: fn(&crate::paths::AppPaths) -> &PathBuf| {
            explicit
                .clone()
                .unwrap_or_else(|| default(defaults.as_ref().expect("defaults resolved")).clone())
        };
        Ok(DaemonPaths {
            store: pick(&self.store, |paths| &paths.profile),
            passphrase_file: pick(&self.passphrase_file, |paths| &paths.passphrase_file),
            socket: pick(&self.socket, |paths| &paths.socket),
            socket_defaulted: self.socket.is_none(),
        })
    }
}

/// Read a passphrase file, dropping a trailing CR/LF.
pub fn read_passphrase_file(path: &Path) -> Result<Zeroizing<String>, String> {
    use std::io::Read;
    let mut passphrase = Zeroizing::new(String::new());
    std::fs::File::open(path)
        .map_err(|_| "read passphrase file")?
        .take(4097)
        .read_to_string(&mut passphrase)
        .map_err(|_| "read passphrase file")?;
    if passphrase.len() > 4096 {
        return Err("passphrase file exceeds 4096 bytes".into());
    }
    while passphrase.ends_with('\r') || passphrase.ends_with('\n') {
        passphrase.pop();
    }
    if passphrase.is_empty() {
        return Err("passphrase file is empty".into());
    }
    Ok(passphrase)
}

/// Resolve the inbox relay from a private card file, or from bootstrap
/// endpoints (flags, `GC_RELAY_BOOTSTRAP_URLS`, JSON config), or none.
pub async fn resolve_inbox_relay(
    inbox_relay_file: Option<&Path>,
    relay_bootstrap_urls: &[String],
    relay_bootstrap_config: Option<&Path>,
) -> Result<Option<NodeInfo>, String> {
    if inbox_relay_file.is_some()
        && (!relay_bootstrap_urls.is_empty() || relay_bootstrap_config.is_some())
    {
        return Err("--inbox-relay-file cannot be combined with relay bootstrap options".into());
    }
    if let Some(path) = inbox_relay_file {
        validate_private_file(path, "inbox relay card")?;
        validate_private_parent(path, "inbox relay card")?;
        let card = std::fs::read_to_string(path)
            .map_err(|error| format!("read inbox relay card: {error}"))?;
        return Ok(Some(decode_relay_card(&card)?));
    }
    let values = bootstrap_values(relay_bootstrap_urls, relay_bootstrap_config)?;
    if values.is_empty() {
        return Ok(None);
    }
    let endpoints = parse_bootstrap_urls(&values, false)
        .map_err(|error| format!("relay bootstrap: {error}"))?;
    let card = fetch_relay_provision(&endpoints, false)
        .await
        .map_err(|error| format!("relay bootstrap failed: {error}"))?;
    Ok(Some(card))
}

/// Merge bootstrap URLs from flags, the environment and the JSON config file.
pub fn bootstrap_values(
    relay_bootstrap_urls: &[String],
    relay_bootstrap_config: Option<&Path>,
) -> Result<Vec<String>, String> {
    let mut values = relay_bootstrap_urls.to_vec();
    if let Ok(env_urls) = std::env::var("GC_RELAY_BOOTSTRAP_URLS") {
        values.extend(env_urls.split(',').map(str::trim).map(str::to_string));
    }
    if let Some(path) = relay_bootstrap_config {
        validate_private_file(path, "relay bootstrap config")?;
        let bytes =
            std::fs::read(path).map_err(|error| format!("read relay bootstrap config: {error}"))?;
        let config: serde_json::Value = serde_json::from_slice(&bytes)
            .map_err(|error| format!("parse relay bootstrap config: {error}"))?;
        let urls = config
            .get("relay_bootstrap_urls")
            .and_then(serde_json::Value::as_array)
            .ok_or("relay bootstrap config must contain relay_bootstrap_urls")?;
        for url in urls {
            let url = url
                .as_str()
                .ok_or("relay_bootstrap_urls entries must be strings")?;
            values.push(url.to_string());
        }
    }
    values.retain(|value| !value.is_empty());
    Ok(values)
}

/// Host a standalone chat instance until the owning service is stopped.
pub async fn run(args: DaemonArgs) -> Result<(), String> {
    use crate::chat_service::{
        host::{InstanceConfig, InstanceHost},
        ChatEndpoint,
    };
    let paths = args.resolve_paths()?;
    if !args.allow_frwd_private_cidrs.is_empty() {
        return Err("standalone GChat does not configure private relay forwarding".into());
    }
    if args.create && paths.store.exists() {
        return Err("profile already exists".into());
    }
    let config = InstanceConfig {
        profile: paths.store.clone(),
        archive: args
            .chat_archive
            .clone()
            .unwrap_or_else(|| paths.store.with_file_name("chat.gcarchive")),
        protocol_socket: paths.socket,
        listen: args.listen,
        advertise: args.advertise,
        relay_file: args.inbox_relay_file.clone(),
        relay_urls: bootstrap_values(
            &args.relay_bootstrap_urls,
            args.relay_bootstrap_config.as_deref(),
        )?,
        catalog_urls: args.chat_catalog_url.clone(),
        network_recovery: !args.no_network_bootstrap,
        local_fixture: args.local_fixture,
    };
    let endpoint = config.chat_endpoint();
    let host = InstanceHost::new(config)?;
    if !args.interactive {
        let passphrase = if args.passphrase_stdin {
            use std::io::Read;
            let mut secret = Zeroizing::new(String::new());
            std::io::stdin()
                .take(4097)
                .read_to_string(&mut secret)
                .map_err(|_| "read passphrase")?;
            if secret.len() > 4096 {
                return Err("passphrase input exceeds bound".into());
            }
            while secret.ends_with(['\r', '\n']) {
                secret.pop();
            }
            secret
        } else {
            validate_private_parent(&paths.passphrase_file, "passphrase")?;
            validate_private_file(&paths.passphrase_file, "passphrase")?;
            read_passphrase_file(&paths.passphrase_file)?
        };
        let response = host
            .dispatch(gchat_api::RequestEnvelope {
                version: gchat_api::VERSION,
                instance_id: Some(host.instance_id().into()),
                request: gchat_api::Request::Unlock {
                    passphrase: passphrase.to_string(),
                    create: args.create,
                },
            })
            .await;
        if let gchat_api::Response::Error { message, .. } = response.response {
            return Err(message);
        }
        if let Some(path) = args.chat_passphrase_file.as_deref() {
            let result = async {
                validate_private_parent(path, "archive passphrase")?;
                validate_private_file(path, "archive passphrase")?;
                let secret = read_passphrase_file(path)?;
                let response = host
                    .dispatch(gchat_api::RequestEnvelope {
                        version: gchat_api::VERSION,
                        instance_id: Some(host.instance_id().into()),
                        request: gchat_api::Request::Unlock {
                            passphrase: secret.to_string(),
                            create: false,
                        },
                    })
                    .await;
                match response.response {
                    gchat_api::Response::Error { message, .. } => Err(message),
                    _ => Ok(()),
                }
            }
            .await;
            if let Err(error) = result {
                host.flush().await?;
                return Err(error);
            }
        }
    }
    let (stop, receiver) = tokio::sync::watch::channel(false);
    let mut server =
        tokio::spawn(async move { crate::chat_service::serve(host, &endpoint, receiver).await });
    let result = tokio::select! {
        result = &mut server => return result.map_err(|e| e.to_string())?,
        signal = shutdown_signal(#[cfg(windows)] args.shutdown_request_file.as_deref()) => signal,
    };
    let _ = stop.send(true);
    let saved = server.await.map_err(|e| e.to_string())?;
    result.and(saved)
}
#[cfg(unix)]
async fn shutdown_signal() -> Result<(), String> {
    let mut terminate = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
        .map_err(|error| error.to_string())?;
    tokio::select! {
        result = tokio::signal::ctrl_c() => result.map_err(|error| error.to_string()),
        _ = terminate.recv() => Ok(()),
    }
}

#[cfg(windows)]
async fn shutdown_signal(request_file: Option<&std::path::Path>) -> Result<(), String> {
    let Some(request_file) = request_file else {
        return tokio::signal::ctrl_c()
            .await
            .map_err(|error| error.to_string());
    };
    validate_private_parent(request_file, "shutdown request")?;
    if request_file.exists() {
        validate_private_file(request_file, "shutdown request")?;
        std::fs::remove_file(request_file).map_err(|error| error.to_string())?;
    }
    loop {
        tokio::select! {
            result = tokio::signal::ctrl_c() => return result.map_err(|error| error.to_string()),
            _ = tokio::time::sleep(std::time::Duration::from_millis(250)) => {}
        }
        if request_file.exists() {
            validate_private_file(request_file, "shutdown request")?;
            std::fs::remove_file(request_file).map_err(|error| error.to_string())?;
            return Ok(());
        }
    }
}
