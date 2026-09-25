//! Disconnected qualification host for the real application and chat service.
//! A fixture-owned signing root describes the fixture relays; installed trust
//! and production binaries are never rewritten to accommodate a test network.
#[cfg(all(target_os = "linux", feature = "gc2-carrier"))]
mod fixture {
    use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine};
    use clap::{Parser, Subcommand};
    use gchat_api::{Request, RequestEnvelope, Response, VERSION};
    use gchat_core::{chat_service::ChatService, runtime::ProtocolRuntime};
    use gcoms::sdk::ipc::Capability;
    use std::{io::Write, net::SocketAddr, path::PathBuf, sync::Arc, time::Duration};

    #[derive(Parser)]
    struct Args {
        #[command(subcommand)]
        command: Command,
    }
    #[derive(Subcommand)]
    enum Command {
        Network {
            bootstrap: PathBuf,
            output: PathBuf,
        },
        Serve {
            #[arg(long)]
            home: PathBuf,
            #[arg(long)]
            passphrase_file: PathBuf,
            #[arg(long)]
            network: PathBuf,
            #[arg(long)]
            inbox_card: Option<PathBuf>,
            #[arg(long)]
            listen: SocketAddr,
            #[arg(long)]
            create: bool,
        },
    }

    fn isolated() -> Result<(), String> {
        let current = std::fs::read_link("/proc/self/ns/net").map_err(|e| e.to_string())?;
        let expected =
            std::env::var("GCHAT_FIXTURE_NETNS").map_err(|_| "missing fixture namespace")?;
        let host =
            std::env::var("GCHAT_FIXTURE_HOST_NETNS").map_err(|_| "missing host namespace")?;
        if current.to_string_lossy() != expected || expected == host {
            return Err("turnover host requires the declared disconnected namespace".into());
        }
        Ok(())
    }

    fn network(bootstrap: PathBuf, output: PathBuf) -> Result<(), String> {
        use gcoms_network::{Founder, NetworkDefaults, SignedNetworkDefaults};
        use std::os::unix::fs::OpenOptionsExt;
        let bytes = zeroize::Zeroizing::new(std::fs::read(bootstrap).map_err(|e| e.to_string())?);
        let bundle = gcoms_routing::gc2::directory::BootstrapBundle::decode(&bytes)
            .map_err(|e| e.to_string())?;
        if bundle.relays.len() != 6 {
            return Err("fixture requires six independent relay introductions".into());
        }
        let now = gcoms_network_client::now_unix();
        let signer = gcoms_crypto::IdentityKeypair::from_seed(rand::random());
        let defaults = NetworkDefaults {
            version: 1,
            network_id: "turnover.invalid".into(),
            dns_domain: "turnover.invalid".into(),
            sequence: 1,
            issued_at: now,
            expires_at: now + 6 * 3600,
            provider_urls: vec!["https://bootstrap.turnover.invalid/".into()],
            founders: bundle
                .relays
                .iter()
                .enumerate()
                .map(|(i, relay)| Founder {
                    name: format!("r{}.relays.turnover.invalid", i + 1),
                    service_id: relay.service_id,
                    address_hints: vec![relay.addr],
                })
                .collect(),
        };
        defaults.validate_at(now, 0)?;
        let installed = gcoms_network_client::InstalledNetwork {
            trusted_key_b64: URL_SAFE_NO_PAD.encode(signer.public_bytes()),
            signed_defaults: SignedNetworkDefaults::sign(defaults, &signer, vec![])?,
        };
        installed.defaults_at(now, 0)?;
        let bytes = serde_json::to_vec(&installed).map_err(|e| e.to_string())?;
        std::fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .mode(0o600)
            .open(output)
            .and_then(|mut file| {
                file.write_all(&bytes)?;
                file.sync_all()
            })
            .map_err(|e| e.to_string())
    }

    pub async fn run() -> Result<(), String> {
        isolated()?;
        let Args { command } = Args::parse();
        let Command::Serve {
            home,
            passphrase_file,
            network: config,
            inbox_card,
            listen,
            create,
        } = command
        else {
            let Command::Network { bootstrap, output } = command else {
                unreachable!()
            };
            return network(bootstrap, output);
        };
        gchat_core::private_fs::validate_private_file(&passphrase_file, "fixture secret")?;
        let secret = zeroize::Zeroizing::new(
            std::fs::read_to_string(passphrase_file).map_err(|e| e.to_string())?,
        );
        let network = std::fs::read(config).map_err(|e| e.to_string())?;
        gcoms_network_client::InstalledNetwork::from_json(&network)?
            .defaults_at(gcoms_network_client::now_unix(), 0)?;
        let relay =
            gchat_core::daemon::resolve_inbox_relay(inbox_card.as_deref(), &[], None).await?;
        if let Some(path) = std::env::var_os("GCHAT_PROTOCOL_METRICS") {
            gcoms::runtime::metrics::init(std::path::Path::new(&path))
                .map_err(|e| e.to_string())?;
        }
        let runtime = ProtocolRuntime(
            gcoms::Application::builder("gchat")
                .backend(gcoms::Backend::Embedded)
                .network_config(network)
                .profile(home.join("profile"))
                .unlock_secret(secret.trim_end())
                .create(create)
                .carrier_profile(gcoms::sdk::CarrierProfile::Gc2)
                .listen(listen)
                .advertise(Some(listen))
                .relay(relay)
                .durable_channel_inbox(true)
                .receive_messages(false)
                .network_recovery(false)
                .open()
                .await?,
        );
        let service = ChatService::new(
            home.join("archive"),
            runtime.clone(),
            vec![
                Capability::IdentityRead,
                Capability::ChannelMember,
                Capability::ChannelAdmin,
                Capability::EventRead,
            ],
        )?;
        let response = service
            .dispatch(RequestEnvelope {
                version: VERSION,
                instance_id: Some(service.snapshot().await?.instance.id),
                request: Request::Unlock {
                    passphrase: secret.trim_end().into(),
                    create,
                },
            })
            .await
            .response;
        if !matches!(response, Response::Snapshot { .. }) {
            runtime.shutdown().await?;
            return Err(format!("fixture archive unlock failed: {response:?}"));
        }
        let (stop, receiver) = tokio::sync::watch::channel(false);
        let mut server = tokio::spawn({
            let service = Arc::clone(&service);
            let endpoint = home.join("protocol.chat");
            async move { gchat_core::chat_service::serve(service, &endpoint, receiver).await }
        });
        let mut term = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .map_err(|e| e.to_string())?;
        let early = tokio::select! {
            result = &mut server => Some(result.map_err(|e| e.to_string())?),
            _ = term.recv() => None,
            _ = tokio::signal::ctrl_c() => None,
        };
        let _ = stop.send(true);
        if early.is_none() {
            tokio::time::timeout(Duration::from_secs(10), &mut server)
                .await
                .map_err(|_| "fixture IPC shutdown timeout")?
                .map_err(|e| e.to_string())??;
        }
        service.disconnect().await?;
        runtime.shutdown().await?;
        early.unwrap_or(Ok(()))
    }
}

#[cfg(all(target_os = "linux", feature = "gc2-carrier"))]
#[tokio::main(flavor = "multi_thread", worker_threads = 2)]
async fn main() {
    if let Err(error) = fixture::run().await {
        eprintln!("turnover fixture: {error}");
        std::process::exit(1);
    }
}
#[cfg(not(all(target_os = "linux", feature = "gc2-carrier")))]
fn main() {
    eprintln!("disconnected turnover host requires Linux namespaces");
    std::process::exit(1);
}
