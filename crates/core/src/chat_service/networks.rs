use super::*;
use gchat_api::{
    InvitationPreview, JoinedNetwork, NetworkRequest, NetworkResponse, NetworkState, NetworkStatus,
};
use gcoms_network::{JoinInvitation, NetworkIdentity, JOIN_INVITATION_PREFIX};
use zeroize::Zeroize;

const MAX_NETWORKS: usize = 8;

#[cfg(all(test, feature = "gc2-carrier", target_os = "linux"))]
#[path = "network_journey_tests.rs"]
mod journey;

/// Encrypted inside the primary service journal, never in frontend storage.
#[derive(Clone, Serialize, Deserialize)]
pub(super) struct RetainedNetwork {
    identity: NetworkIdentity,
    password: String,
}
impl Drop for RetainedNetwork {
    fn drop(&mut self) {
        self.password.zeroize();
    }
}

fn key(identity: &NetworkIdentity) -> String {
    let mut hash = Sha256::new();
    hash.update(b"gchat/network/v1\0");
    hash.update(identity.signed_defaults.defaults.network_id.as_bytes());
    hash.update([0]);
    hash.update(identity.trusted_key_b64.as_bytes());
    hex(&hash.finalize())
}

impl ChatService {
    fn network_identity(&self) -> Result<NetworkIdentity, String> {
        self.runtime
            .network_client()
            .map(|client| client.identity())
            .ok_or_else(|| "This local fixture has no signed network identity".into())
    }

    fn describe_network(
        identity: &NetworkIdentity,
        primary: bool,
        status: NetworkStatus,
    ) -> JoinedNetwork {
        JoinedNetwork {
            id: key(identity),
            name: identity.signed_defaults.defaults.network_id.clone(),
            fingerprint: hex(&Sha256::digest(identity.trusted_key_b64.as_bytes())),
            primary,
            status,
        }
    }

    fn decode_invitation(
        &self,
        code: &str,
    ) -> Result<(JoinInvitation, Option<String>, u64), String> {
        let code = code.trim();
        if code.len() > gchat_api::MAX_NETWORK_INVITATION_BYTES {
            return Err("Invitation exceeds size limit".into());
        }
        let at = now();
        let invitation = if code.starts_with(JOIN_INVITATION_PREFIX) {
            JoinInvitation::decode_at(code, at)?
        } else {
            let network = self.network_identity()?;
            let mut invitation = JoinInvitation {
                version: 1,
                network,
                network_invitation: None,
                channel_invitation: None,
            };
            if code.starts_with(gcoms_network::INVITATION_PREFIX) {
                invitation.network_invitation = Some(code.into());
            } else {
                invitation.channel_invitation = Some(code.into());
            }
            invitation.validate_at(at)?;
            invitation
        };
        let defaults = invitation.network.verify_at(at, 0)?;
        let mut expires = defaults.expires_at;
        if let Some(code) = &invitation.network_invitation {
            expires =
                expires.min(gcoms_network::NetworkInvitation::decode_at(code, at)?.expires_at);
        }
        let channel = if let Some(code) = &invitation.channel_invitation {
            let envelope = gcoms_node::channel_invite::InviteEnvelope::from_link(code)
                .ok_or("Invalid channel invitation")?;
            if envelope.invite.expiry <= at {
                return Err("Channel invitation has expired".into());
            }
            expires = expires.min(envelope.invite.expiry);
            // A network label cannot smuggle another network's relay capabilities.
            #[cfg(feature = "gc2-carrier")]
            if let Some(bundle) = &envelope.gc2_bootstrap {
                if bundle.relays.iter().any(|relay| {
                    !defaults
                        .founders
                        .iter()
                        .any(|founder| founder.service_id == relay.service_id)
                }) {
                    return Err(
                        "Channel invitation contains relays outside its signed network".into(),
                    );
                }
            } else if !invitation.network.same_network(&self.network_identity()?) {
                return Err(
                    "Ask for a current invitation including this network's relay bootstrap".into(),
                );
            }
            Some(envelope.invite.channel.clone())
        } else {
            None
        };
        Ok((invitation, channel, expires))
    }

    pub(super) async fn networks_request(
        &self,
        request: NetworkRequest,
    ) -> Result<NetworkResponse, String> {
        Box::pin(self.networks_request_inner(request)).await
    }

    async fn networks_request_inner(
        &self,
        request: NetworkRequest,
    ) -> Result<NetworkResponse, String> {
        {
            let session = self.session.lock().await;
            if session.as_ref().is_none_or(|session| session.ui_locked) {
                return Err("Unlock your profile first".into());
            }
        }
        match request {
            NetworkRequest::List => {
                let identity = self.network_identity()?;
                let mut networks = vec![Self::describe_network(
                    &identity,
                    true,
                    self.runtime.network_status(),
                )];
                let records = self
                    .session
                    .lock()
                    .await
                    .as_ref()
                    .ok_or("Profile locked")?
                    .state
                    .networks
                    .clone();
                let children = self.networks.lock().await;
                for (id, record) in records {
                    let status = children
                        .get(&id)
                        .map(|child| child.runtime.network_status())
                        .unwrap_or_else(|| NetworkStatus::new(NetworkState::Unavailable));
                    networks.push(Self::describe_network(&record.identity, false, status));
                }
                Ok(NetworkResponse::List { networks })
            }
            NetworkRequest::Inspect { code } => {
                let code = Zeroizing::new(code);
                let (invitation, channel, expires) = self.decode_invitation(&code)?;
                let id = key(&invitation.network);
                let primary = invitation.network.same_network(&self.network_identity()?);
                let known = primary
                    || self
                        .session
                        .lock()
                        .await
                        .as_ref()
                        .ok_or("Profile locked")?
                        .state
                        .networks
                        .contains_key(&id);
                Ok(NetworkResponse::Preview {
                    preview: InvitationPreview {
                        network: Self::describe_network(
                            &invitation.network,
                            primary,
                            NetworkStatus::new(NetworkState::Connecting),
                        ),
                        channel,
                        new_network: !known,
                        expires,
                    },
                })
            }
            NetworkRequest::Call { network, request } => {
                // Lifecycle remains instance-wide. Never permit nested network routing.
                if matches!(
                    *request,
                    Request::Networks { .. }
                        | Request::Unlock { .. }
                        | Request::Lock
                        | Request::Disconnect
                        | Request::Identify
                ) || matches!(&*request, Request::Submit { text, .. } if matches!(lifecycle_request(Request::Submit {
                        operation_id: String::new(), conversation: None, text: text.clone()
                    }), Request::Lock | Request::Disconnect))
                {
                    return Err("Use instance controls for lock, unlock or disconnect".into());
                }
                let response = if network == key(&self.network_identity()?) {
                    Box::pin(self.handle(*request)).await?
                } else {
                    let child = self
                        .networks
                        .lock()
                        .await
                        .get(&network)
                        .cloned()
                        .ok_or("Network unavailable")?;
                    Box::pin(child.handle(*request)).await?
                };
                Ok(NetworkResponse::Result {
                    network,
                    response: Box::new(response),
                })
            }
            NetworkRequest::Join {
                code,
                nickname,
                accepted_network,
                operation_id,
            } => {
                let code = Zeroizing::new(code);
                let _guard = self.network_operations.lock().await;
                let (invitation, channel, _) = self.decode_invitation(&code)?;
                let id = key(&invitation.network);
                if accepted_network != id {
                    return Err("Review and accept this invitation's network first".into());
                }
                if channel.is_some()
                    && (nickname.trim().is_empty()
                        || nickname.len() > 256
                        || nickname.chars().any(char::is_control))
                {
                    return Err("Choose a nickname of 1–256 UTF-8 bytes".into());
                }
                if operation_id.is_empty() || operation_id.len() > 128 {
                    return Err("Invalid invitation operation ID".into());
                }
                let primary = invitation.network.same_network(&self.network_identity()?);
                if let Some(code) = &invitation.channel_invitation {
                    if code.len() + nickname.len() + 7 > gchat_api::MAX_INPUT_BYTES as usize {
                        return Err("Channel invitation exceeds the join command limit".into());
                    }
                }
                let child = if primary {
                    None
                } else {
                    let record = {
                        let mut session = self.session.lock().await;
                        let unlocked = session
                            .as_mut()
                            .filter(|session| !session.ui_locked)
                            .ok_or("Profile locked")?;
                        if let Some(record) = unlocked.state.networks.get(&id) {
                            record.clone()
                        } else {
                            if unlocked.state.networks.len() >= MAX_NETWORKS - 1 {
                                return Err("Network limit reached".into());
                            }
                            // Matching names with different roots never silently replace trust.
                            if invitation.network.signed_defaults.defaults.network_id
                                == self.network_identity()?.signed_defaults.defaults.network_id
                                || unlocked.state.networks.values().any(|record| {
                                    record.identity.signed_defaults.defaults.network_id
                                        == invitation.network.signed_defaults.defaults.network_id
                                })
                            {
                                return Err(
                                    "This network name is already pinned to another identity"
                                        .into(),
                                );
                            }
                            let record = RetainedNetwork {
                                identity: invitation.network.clone(),
                                password: random_id(),
                            };
                            let mut candidate = unlocked.state.clone();
                            candidate.networks.insert(id.clone(), record.clone());
                            unlocked.store.save(&candidate)?;
                            unlocked.state = candidate;
                            record
                        }
                    };
                    Some(Box::pin(self.open_retained_network(&id, &record)).await?)
                };
                let target = child.as_deref().unwrap_or(self);
                if let Some(code) = &invitation.network_invitation {
                    target.runtime.import_network_invitation(code)?;
                }
                let response = if let Some(code) = &invitation.channel_invitation {
                    Box::pin(target.handle(Request::Submit {
                        operation_id,
                        conversation: None,
                        text: format!("/join {code} {}", nickname.trim()),
                    }))
                    .await?
                } else {
                    Response::Applied {
                        conversation: None,
                        notice: Some("Network added. Connecting in the background.".into()),
                    }
                };
                Ok(NetworkResponse::Result {
                    network: id,
                    response: Box::new(response),
                })
            }
        }
    }

    async fn open_retained_network(
        &self,
        id: &str,
        record: &RetainedNetwork,
    ) -> Result<Arc<ChatService>, String> {
        if id != key(&record.identity) {
            return Err("Retained network identity mismatch".into());
        }
        if let Some(child) = self.networks.lock().await.get(id).cloned() {
            let response = Box::pin(child.handle(Request::Unlock {
                passphrase: record.password.clone(),
                create: false,
            }))
            .await?;
            if let Response::Error { message, .. } = response {
                return Err(message);
            }
            return Ok(child);
        }
        let base = self.archive.with_extension("networks");
        crate::paths::ensure_private_dir(&base, "network profiles")?;
        let home = base.join(id);
        crate::paths::ensure_private_dir(&home, "network profile")?;
        let profile = home.join("protocol.enc");
        let runtime = ProtocolRuntime::open_network(
            &profile,
            &record.password,
            !profile.exists(),
            record.identity.clone(),
        )
        .await?;
        let archive = home.join("chat.enc");
        let create = !archive.exists();
        let child = ChatService::new(archive, runtime.clone(), self.capabilities.clone())?;
        let opened = Box::pin(child.handle(Request::Unlock {
            passphrase: record.password.clone(),
            create,
        }))
        .await;
        if !matches!(opened, Ok(Response::Snapshot { .. })) {
            let _ = Box::pin(child.disconnect()).await;
            let _ = runtime.shutdown().await;
            return Err(
                "Cannot unlock this network's retained profile; its files were preserved".into(),
            );
        }
        // Empty overrides select this runtime's pinned signed network. Passing
        // origins as overrides would select the explicit-provider fixture path.
        if let Err(error) = runtime.start_network_maintenance(Vec::new(), true) {
            let _ = Box::pin(child.disconnect()).await;
            let _ = runtime.shutdown().await;
            return Err(error);
        }
        self.networks.lock().await.insert(id.into(), child.clone());
        Ok(child)
    }

    pub(super) async fn restore_networks(&self) -> Result<(), String> {
        let _guard = self.network_operations.lock().await;
        let records = self
            .session
            .lock()
            .await
            .as_ref()
            .ok_or("Profile locked")?
            .state
            .networks
            .clone();
        for (id, record) in records {
            // One failed network cannot prevent access to other networks/history.
            let _ = Box::pin(self.open_retained_network(&id, &record)).await;
        }
        Ok(())
    }

    pub(super) async fn lock_networks(&self) -> Result<(), String> {
        let children: Vec<_> = self.networks.lock().await.values().cloned().collect();
        let mut failure = None;
        for child in children {
            if let Err(error) = Box::pin(child.handle(Request::Lock)).await {
                failure = Some(error);
            }
        }
        failure.map_or(Ok(()), Err)
    }

    pub(super) async fn stop_networks(&self) -> Result<(), String> {
        let children = std::mem::take(&mut *self.networks.lock().await);
        let mut failure = None;
        for child in children.into_values() {
            let saved = Box::pin(child.disconnect()).await;
            let stopped = child.runtime.clone().shutdown().await;
            if let Err(error) = saved.and(stopped) {
                failure = Some(error);
            }
        }
        failure.map_or(Ok(()), Err)
    }

    pub(super) async fn flush_networks(&self) -> Result<(), String> {
        let children: Vec<_> = self.networks.lock().await.values().cloned().collect();
        for child in children {
            Box::pin(child.flush()).await?;
        }
        Ok(())
    }
}

#[cfg(all(test, feature = "gc2-carrier"))]
mod tests {
    use super::*;
    use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine};

    fn invitation(name: &str, seed: u8) -> JoinInvitation {
        let signer = gcoms_crypto::IdentityKeypair::from_seed([seed; 32]);
        let mut defaults = crate::network::installed()
            .unwrap()
            .signed_defaults
            .defaults;
        defaults.network_id = name.into();
        defaults.dns_domain = name.into();
        defaults.provider_urls = vec![format!("https://bootstrap.{name}/")];
        defaults.issued_at = now();
        defaults.expires_at = now() + 3600;
        for (i, founder) in defaults.founders.iter_mut().enumerate() {
            founder.name = format!("r{}.relays.{name}", i + 1);
            founder.service_id = [i as u8 + 1; 32];
            founder.address_hints = vec![format!("93.184.216.71:{}", 15000 + i).parse().unwrap()];
        }
        let grant = gcoms_network::NetworkInvitation {
            version: 1,
            network_id: name.into(),
            provider_urls: defaults.provider_urls.clone(),
            grant: URL_SAFE_NO_PAD.encode([seed; 32]),
            expires_at: now() + 3600,
        };
        JoinInvitation {
            version: 1,
            network: NetworkIdentity {
                trusted_key_b64: URL_SAFE_NO_PAD.encode(signer.public_bytes()),
                signed_defaults: gcoms_network::SignedNetworkDefaults::sign(
                    defaults,
                    &signer,
                    vec![],
                )
                .unwrap(),
            },
            network_invitation: Some(grant.encode().unwrap()),
            channel_invitation: None,
        }
    }

    #[tokio::test(flavor = "multi_thread", worker_threads = 2)]
    #[ignore = "requires the disconnected namespace helper; creates independent protected runtimes"]
    async fn joined_network_registry_is_private_isolated_and_reopens() {
        assert_eq!(
            std::env::var("GCHAT_BOOTSTRAP_NAMESPACE").as_deref(),
            Ok("isolated")
        );
        assert_ne!(
            std::fs::read_link("/proc/self/ns/net")
                .unwrap()
                .to_string_lossy(),
            std::env::var("GCHAT_BOOTSTRAP_HOST_NAMESPACE").unwrap()
        );
        let home = tempfile::tempdir().unwrap();
        crate::private_fs::make_private(home.path(), true).unwrap();
        let pass = "separate-network-journal-test";
        let mut identities = BTreeMap::new();
        for create in [true, false] {
            eprintln!("network registry: primary create={create}");
            let profile = home.path().join("profile");
            let runtime = if create {
                ProtocolRuntime::create_protected(
                    &profile,
                    pass,
                    "93.184.216.71:14435".parse().unwrap(),
                    None,
                    None,
                    &[],
                )
                .await
            } else {
                ProtocolRuntime::unlock_protected(
                    &profile,
                    pass,
                    "93.184.216.71:14435".parse().unwrap(),
                    None,
                    None,
                    &[],
                )
                .await
            }
            .unwrap();
            let service = ChatService::new(
                home.path().join("archive"),
                runtime.clone(),
                vec![
                    Capability::IdentityRead,
                    Capability::ChannelMember,
                    Capability::ChannelAdmin,
                    Capability::EventRead,
                ],
            )
            .unwrap();
            service
                .handle(Request::Unlock {
                    passphrase: pass.into(),
                    create,
                })
                .await
                .unwrap();
            if create {
                for (name, seed) in [("first.invalid", 71), ("second.invalid", 72)] {
                    eprintln!("network registry: add {name}");
                    let invitation = invitation(name, seed);
                    let id = key(&invitation.network);
                    let code = invitation.encode_at(now()).unwrap();
                    assert!(service
                        .networks_request(NetworkRequest::Join {
                            code: code.clone(),
                            nickname: String::new(),
                            accepted_network: "wrong-root".into(),
                            operation_id: random_id()
                        })
                        .await
                        .is_err());
                    assert!(!home.path().join("archive.networks").join(&id).exists());
                    let result = service
                        .networks_request(NetworkRequest::Join {
                            code,
                            nickname: String::new(),
                            accepted_network: id.clone(),
                            operation_id: random_id(),
                        })
                        .await
                        .unwrap();
                    assert!(
                        matches!(result, NetworkResponse::Result { network, .. } if network == id)
                    );
                    let child = service.networks.lock().await[&id].clone();
                    identities.insert(id, child.snapshot().await.unwrap().instance.safety_number);
                }
                assert_ne!(identities.values().next(), identities.values().nth(1));
                let before = std::fs::read(home.path().join("archive.service")).unwrap();
                let registry = service
                    .session
                    .lock()
                    .await
                    .as_ref()
                    .unwrap()
                    .state
                    .networks
                    .clone();
                for record in registry.values() {
                    assert!(!before
                        .windows(record.password.len())
                        .any(|b| b == record.password.as_bytes()));
                }
                let conflict = invitation("first.invalid", 73);
                assert!(service
                    .networks_request(NetworkRequest::Join {
                        code: conflict.encode_at(now()).unwrap(),
                        nickname: String::new(),
                        accepted_network: key(&conflict.network),
                        operation_id: random_id()
                    })
                    .await
                    .is_err());
            }
            let NetworkResponse::List { networks } = service
                .networks_request(NetworkRequest::List)
                .await
                .unwrap()
            else {
                panic!("network list")
            };
            assert_eq!(networks.len(), 3);
            let children = service.networks.lock().await.clone();
            assert_eq!(children.len(), 2);
            for (id, child) in &children {
                assert_eq!(
                    child.snapshot().await.unwrap().instance.safety_number,
                    identities[id]
                );
                assert!(service
                    .networks_request(NetworkRequest::Call {
                        network: id.clone(),
                        request: Box::new(Request::Disconnect)
                    })
                    .await
                    .is_err());
                assert!(service
                    .networks_request(NetworkRequest::Call {
                        network: id.clone(),
                        request: Box::new(Request::Networks {
                            request: NetworkRequest::List
                        })
                    })
                    .await
                    .is_err());
            }
            service.handle(Request::Lock).await.unwrap();
            eprintln!("network registry: all profiles locked");
            assert!(service
                .networks_request(NetworkRequest::List)
                .await
                .is_err());
            for (id, child) in &children {
                assert!(child.snapshot().await.unwrap().instance.locked);
                assert!(service
                    .networks_request(NetworkRequest::Call {
                        network: id.clone(),
                        request: Box::new(Request::Snapshot)
                    })
                    .await
                    .is_err());
                let frame = gchat_api::files::encode_io(
                    &gchat_api::files::FileIo {
                        instance: service.id.clone(),
                        id: format!("{id}:{}", "0".repeat(32)),
                        piece: 0,
                        upload: false,
                    },
                    &[],
                )
                .unwrap();
                assert!(service.file_piece_io(frame).await.is_err());
            }
            service
                .handle(Request::Unlock {
                    passphrase: pass.into(),
                    create: false,
                })
                .await
                .unwrap();
            eprintln!("network registry: all profiles unlocked");
            for child in children.values() {
                assert!(!child.snapshot().await.unwrap().instance.locked);
            }
            service.disconnect().await.unwrap();
            eprintln!("network registry: stopped child runtimes");
            assert!(service.networks.lock().await.is_empty());
            drop(children);
            drop(service);
            runtime.shutdown().await.unwrap();
        }
    }
}
