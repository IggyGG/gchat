//! Disconnected qualification host for the real application and chat service.
//! A fixture-owned signing root describes the fixture relays; installed trust
//! and production binaries are never rewritten to accommodate a test network.
#[cfg(all(target_os = "linux", feature = "gc2-carrier"))]
mod fixture {
    use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine};
    use clap::{Parser, Subcommand};
    use gchat_api::{Request, RequestEnvelope, Response, VERSION};
    use gchat_core::{chat_service::ChatService, runtime::ProtocolRuntime};
    use gcoms::sdk::{ipc::Capability, GcClient};
    use std::{io::Write, net::SocketAddr, path::PathBuf, sync::Arc, time::Duration};

    #[derive(Parser)]
    struct Args {
        #[command(subcommand)]
        command: Command,
    }
    #[derive(Subcommand)]
    enum Command {
        /// Core contribution service in the declared disconnected namespace.
        Contribute {
            #[arg(long)]
            listen: SocketAddr,
            #[arg(long)]
            bootstrap: PathBuf,
            #[arg(long)]
            introduction: PathBuf,
            #[arg(long)]
            verified: PathBuf,
            #[arg(long)]
            diagnostics: PathBuf,
        },
        /// A separate process verifies the listener before publication.
        Verify {
            introduction: PathBuf,
            verified: PathBuf,
        },
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
            /// Owner-only setup endpoint; uses the released single-use SDK API.
            #[arg(long)]
            fixture_invitations: bool,
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

    fn fixture_bootstrap(
        path: &std::path::Path,
    ) -> Result<gcoms_routing::gc2::directory::BootstrapBundle, String> {
        use std::io::Read;
        isolated()?;
        gchat_core::private_fs::validate_private_file(path, "fixture routing introductions")?;
        let mut bytes = zeroize::Zeroizing::new(Vec::new());
        std::fs::File::open(path)
            .map_err(|e| e.to_string())?
            .take(6 + 8 * 155 + 1)
            .read_to_end(&mut bytes)
            .map_err(|e| e.to_string())?;
        gcoms_routing::gc2::directory::BootstrapBundle::decode(&bytes).map_err(|e| e.to_string())
    }

    async fn refresh_fixture_routing(
        runtime: ProtocolRuntime,
        path: PathBuf,
    ) -> Result<(), String> {
        let mut current = fixture_bootstrap(&path)?;
        let identities: Vec<_> = current
            .relays
            .iter()
            .map(|r| (r.addr, r.service_id, r.reentry_cap))
            .collect();
        loop {
            let bundle = fixture_bootstrap(&path)?;
            if bundle
                .relays
                .iter()
                .map(|r| (r.addr, r.service_id, r.reentry_cap))
                .collect::<Vec<_>>()
                != identities
            {
                return Err("fixture introduction changed its verified relay identity".into());
            }
            if bundle.relays != current.relays {
                runtime
                    .embedded()
                    .ok_or("fixture requires an embedded runtime")?
                    .node()
                    .install_gc2_routing_bootstrap(&bundle)?;
                eprintln!(
                    "fixture routing introductions renewed: {} relays",
                    bundle.relays.len()
                );
                current = bundle;
            }
            tokio::time::sleep(Duration::from_secs(5)).await;
        }
    }

    async fn invitation_setup(runtime: ProtocolRuntime, home: PathBuf) -> Result<(), String> {
        use std::os::unix::fs::{MetadataExt, PermissionsExt};
        use tokio::io::{AsyncReadExt, AsyncWriteExt};
        #[derive(serde::Deserialize)]
        #[serde(deny_unknown_fields)]
        struct Invitation {
            channel: String,
        }
        let endpoint = home.join("fixture-invitations.sock");
        let owner = std::fs::metadata(&home).map_err(|e| e.to_string())?.uid();
        let listener = tokio::net::UnixListener::bind(&endpoint).map_err(|e| e.to_string())?;
        std::fs::set_permissions(&endpoint, std::fs::Permissions::from_mode(0o600))
            .map_err(|e| e.to_string())?;
        loop {
            let (mut stream, _) = listener.accept().await.map_err(|e| e.to_string())?;
            if stream.peer_cred().map_err(|e| e.to_string())?.uid() != owner {
                continue;
            }
            let mut raw = Vec::new();
            tokio::time::timeout(
                Duration::from_secs(5),
                (&mut stream).take(1025).read_to_end(&mut raw),
            )
            .await
            .map_err(|_| "fixture invitation request timed out")?
            .map_err(|e| e.to_string())?;
            let result = async {
                if raw.len() > 1024 {
                    return Err("fixture invitation request too large".to_string());
                }
                let request: Invitation =
                    serde_json::from_slice(&raw).map_err(|e| e.to_string())?;
                runtime
                    .sdk_client()
                    .create_channel_invitation(&request.channel, 3600)
                    .await
                    .map_err(|e| e.to_string())
            }
            .await;
            let response = match result {
                Ok(invite) => {
                    serde_json::json!({"link": invite.link, "localOnly": invite.local_only})
                }
                Err(error) => serde_json::json!({"error": error}),
            };
            stream
                .write_all(&serde_json::to_vec(&response).map_err(|e| e.to_string())?)
                .await
                .map_err(|e| e.to_string())?;
        }
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

    async fn contribute(
        listen: SocketAddr,
        bootstrap: PathBuf,
        introduction: PathBuf,
        verified: PathBuf,
        diagnostics: PathBuf,
    ) -> Result<(), String> {
        use gcoms_routing::{Directory, RelayService, ServicePolicy};
        use gcoms_transport::{server::Tp1Server, tls::TlsIdentity, TokenRegistry};
        use std::sync::atomic::{AtomicBool, Ordering};
        let ready = Arc::new(AtomicBool::new(false));
        let identity = TlsIdentity::generate().map_err(|e| e.to_string())?;
        let relay = RelayService::new(
            listen,
            identity.service_id(),
            rand::random(),
            Arc::new(Directory::new()),
            ServicePolicy {
                max_circuits: 32,
                transit_ready: Some(ready.clone()),
                ..Default::default()
            },
        )
        .map_err(|e| e.to_string())?;
        relay.configure_contribution_bandwidth(512 * 1024);
        let bundle = gcoms_routing::gc2::directory::BootstrapBundle::decode(
            &std::fs::read(&bootstrap).map_err(|e| e.to_string())?,
        )
        .map_err(|e| e.to_string())?;
        relay
            .gc2_directory()
            .remember(&bundle, gcoms_network_client::now_unix())
            .map_err(|e| e.to_string())?;
        let own = gcoms_routing::gc2::directory::BootstrapBundle {
            relays: vec![relay.gc2_introduction(gcoms_network_client::now_unix())],
        }
        .encode()
        .map_err(|e| e.to_string())?;
        private_write(&introduction, &own)?;
        let server = Tp1Server::bind_with_identity(
            listen,
            TokenRegistry::new(),
            Arc::new(|_, _| Ok(None)),
            Arc::new(|_| None),
            &identity,
        )
        .await
        .map_err(|e| e.to_string())?;
        let mut task = tokio::spawn(
            server
                .with_limits(gcoms_transport::ServerLimits {
                    max_connections: 64,
                    ..Default::default()
                })
                .with_dispatch_factory(relay.gc2_handler_factory())
                .run(),
        );
        let mut term = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .map_err(|e| e.to_string())?;
        loop {
            tokio::select! {
                result=&mut task => { result.map_err(|e|e.to_string())?.map_err(|e|e.to_string())?; break; },
                _=term.recv()=>break,
                _=tokio::time::sleep(Duration::from_secs(1))=> {
                    relay.gc2_directory().remember(&fixture_bootstrap(&bootstrap)?,gcoms_network_client::now_unix())
                        .map_err(|e|e.to_string())?;
                    let own=gcoms_routing::gc2::directory::BootstrapBundle {
                        relays:vec![relay.gc2_introduction(gcoms_network_client::now_unix())],
                    }.encode().map_err(|e|e.to_string())?;
                    private_replace(&introduction,&own)?;
                    if verified.is_file() { ready.store(true,Ordering::Release); }
                    let record=serde_json::json!({"circuits":32,"connections":64,"bandwidth_bytes_per_second":512*1024,
                        "published":ready.load(Ordering::Acquire),"transferred_bytes":relay.contribution_bytes()});
                    private_replace(&diagnostics,&serde_json::to_vec(&record).map_err(|e|e.to_string())?)?;
                }
            }
        }
        ready.store(false, Ordering::Release);
        task.abort();
        Ok(())
    }

    fn private_write(path: &std::path::Path, bytes: &[u8]) -> Result<(), String> {
        use std::os::unix::fs::OpenOptionsExt;
        std::fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .mode(0o600)
            .open(path)
            .and_then(|mut file| file.write_all(bytes))
            .map_err(|e| e.to_string())
    }
    fn private_replace(path: &std::path::Path, bytes: &[u8]) -> Result<(), String> {
        let mut file =
            tempfile::NamedTempFile::new_in(path.parent().ok_or("fixture parent missing")?)
                .map_err(|e| e.to_string())?;
        gchat_core::private_fs::make_private(file.path(), false)?;
        file.write_all(bytes).map_err(|e| e.to_string())?;
        file.persist(path).map_err(|e| e.to_string())?;
        Ok(())
    }

    pub async fn run() -> Result<(), String> {
        isolated()?;
        let Args { command } = Args::parse();
        match command {
            Command::Contribute {
                listen,
                bootstrap,
                introduction,
                verified,
                diagnostics,
            } => return contribute(listen, bootstrap, introduction, verified, diagnostics).await,
            Command::Verify {
                introduction,
                verified,
            } => {
                let bundle = gcoms_routing::gc2::directory::BootstrapBundle::decode(
                    &std::fs::read(introduction).map_err(|e| e.to_string())?,
                )
                .map_err(|e| e.to_string())?;
                if bundle.relays.len() != 1 {
                    return Err("one contribution required".into());
                }
                let intro = &bundle.relays[0];
                let client = gcoms_transport::Tp1Client::new().map_err(|e| e.to_string())?;
                let proof = gcoms_routing::gc2::discovery::refresh(&client, intro, &[])
                    .await
                    .map_err(|e| e.to_string())?;
                if !proof.relays.iter().any(|own| own == intro) {
                    return Err("contribution listener changed".into());
                }
                return private_write(&verified, b"verified\n");
            }
            _ => {}
        }
        let Command::Serve {
            home,
            passphrase_file,
            network: config,
            inbox_card,
            listen,
            create,
            fixture_invitations,
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
        let setup = fixture_invitations
            .then(|| tokio::spawn(invitation_setup(runtime.clone(), home.clone())));
        let path = std::env::var_os("GC_ROUTING_BOOTSTRAP").ok_or("fixture bootstrap missing")?;
        let mut routing = tokio::spawn(refresh_fixture_routing(runtime.clone(), path.into()));
        let mut server = tokio::spawn({
            let service = Arc::clone(&service);
            let endpoint = home.join("protocol.chat");
            async move { gchat_core::chat_service::serve(service, &endpoint, receiver).await }
        });
        let mut term = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .map_err(|e| e.to_string())?;
        let (server_finished, early) = tokio::select! {
            result = &mut server => (true, Some(result.map_err(|e| e.to_string())?)),
            result = &mut routing => (false, Some(result.map_err(|e|e.to_string())?)),
            _ = term.recv() => (false, None),
            _ = tokio::signal::ctrl_c() => (false, None),
        };
        let _ = stop.send(true);
        routing.abort();
        if let Some(setup) = setup {
            setup.abort();
            let _ = setup.await;
            std::fs::remove_file(home.join("fixture-invitations.sock"))
                .map_err(|e| e.to_string())?;
        }
        if !server_finished {
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
