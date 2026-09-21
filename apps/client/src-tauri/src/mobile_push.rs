//! Optional provider hints for the already-running mobile profile. Registration
//! metadata stays in the same OS vault as remembered credentials, in separate slots.
use gchat_core::chat_service::{host::InstanceHost, ChatEndpoint};
use rand::RngCore;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    io::Write,
    path::{Path, PathBuf},
    time::{Duration, SystemTime, UNIX_EPOCH},
};
use tauri_plugin_gchat_mobile_platform::{
    MobilePlatformExt, PushDevice, RememberSecret, UnlockSecret,
};

#[derive(Clone, Default, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Status {
    pub enabled: bool,
    pub permission: String,
    pub registered: bool,
    pub message: String,
}

#[derive(Default, Deserialize, Serialize)]
struct Policy {
    enabled: bool,
    networks: Vec<String>,
}
#[derive(Deserialize, Serialize)]
struct Registration {
    nonce: [u8; 32],
    revision: u64,
    token_hash: String,
    origin: String,
    reference: String,
    management_token: String,
    expires: u64,
    #[serde(default)]
    registration_pending: bool,
}
impl Default for Registration {
    fn default() -> Self {
        let mut nonce = [0; 32];
        rand::rngs::OsRng.fill_bytes(&mut nonce);
        Self {
            nonce,
            revision: 0,
            token_hash: String::new(),
            origin: String::new(),
            reference: String::new(),
            management_token: String::new(),
            expires: 0,
            registration_pending: false,
        }
    }
}
impl Registration {
    fn next_revision(&mut self) -> Result<u64, String> {
        self.revision = self
            .revision
            .checked_add(1)
            .filter(|value| *value <= i64::MAX as u64)
            .ok_or("Notification revision exhausted")?;
        Ok(self.revision)
    }
    fn needs_registration(&self, token: &str, now: u64) -> bool {
        self.token_hash != digest(token.as_bytes())
            || self.expires <= now.saturating_add(3600)
            || self.reference.is_empty()
    }
}

pub struct Push {
    path: PathBuf,
    policy: Policy,
    policy_error: bool,
    cursor: usize,
    status: Status,
    client: reqwest::Client,
}
fn now() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}
fn digest(bytes: &[u8]) -> String {
    Sha256::digest(bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}
fn hex32(text: &str) -> Result<[u8; 32], String> {
    if text.len() != 64 || !text.bytes().all(|b| b.is_ascii_hexdigit()) {
        return Err("Invalid notification reference".into());
    }
    let mut bytes = [0; 32];
    for (i, byte) in bytes.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&text[i * 2..i * 2 + 2], 16)
            .map_err(|_| "Invalid notification reference")?;
    }
    Ok(bytes)
}
fn endpoint(origin: &str, path: &str) -> Result<reqwest::Url, String> {
    let url = reqwest::Url::parse(origin).map_err(|_| "Invalid notification gateway")?;
    if url.origin().ascii_serialization() != "https://push.gchat.boo"
        || url.scheme() != "https"
        || url.host_str().is_none()
        || !url.username().is_empty()
        || url.password().is_some()
        || url.query().is_some()
        || url.fragment().is_some()
        || !matches!(url.path(), "" | "/")
    {
        return Err("Invalid notification gateway".into());
    }
    url.join(path)
        .map_err(|_| "Invalid notification gateway".into())
}
impl Push {
    pub fn new(home: &Path) -> Result<Self, String> {
        let path = home.join("push-policy.json");
        // Optional notification metadata can fail closed without making the
        // encrypted profile, chat or ordinary reconnect inaccessible.
        let (policy, policy_error) = match std::fs::read(&path) {
            Ok(bytes) => match serde_json::from_slice(&bytes) {
                Ok(value) => (value, false),
                Err(_) => (Policy::default(), true),
            },
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                (Policy::default(), false)
            }
            Err(_) => (Policy::default(), true),
        };
        let policy_error = policy_error
            || policy.networks.len() > 8
            || policy.networks.iter().any(|name| name.len() > 128);
        let policy = if policy_error {
            Policy::default()
        } else {
            policy
        };
        let client = reqwest::Client::builder()
            .https_only(true)
            .redirect(reqwest::redirect::Policy::none())
            .timeout(Duration::from_secs(10))
            .build()
            .map_err(|_| "Notification transport is unavailable")?;
        Ok(Self {
            path,
            status: Status {
                enabled: policy.enabled,
                ..Status::default()
            },
            policy,
            policy_error,
            cursor: 0,
            client,
        })
    }
    fn persist_policy(&self) -> Result<(), String> {
        let parent = self.path.parent().ok_or("Missing profile directory")?;
        let mut file = tempfile::NamedTempFile::new_in(parent)
            .map_err(|_| "Cannot save notification policy")?;
        let bytes =
            serde_json::to_vec(&self.policy).map_err(|_| "Cannot encode notification policy")?;
        file.write_all(&bytes)
            .and_then(|()| file.as_file().sync_all())
            .map_err(|_| "Cannot save notification policy")?;
        file.persist(&self.path)
            .map_err(|_| "Cannot save notification policy")?;
        #[cfg(unix)]
        std::fs::File::open(parent)
            .and_then(|f| f.sync_all())
            .map_err(|_| "Cannot save notification policy")?;
        Ok(())
    }
    pub fn status(&self) -> Status {
        self.status.clone()
    }
    fn slot(host: &InstanceHost, network: &str) -> String {
        format!(
            "push_{}",
            digest(format!("{}:{network}", host.instance_id()).as_bytes())
        )
    }
    async fn load(&self, app: &tauri::AppHandle, slot: &str) -> Result<Registration, String> {
        match app
            .mobile_platform()
            .get_secret(slot)
            .await
            .map_err(|_| "Notification storage is locked")?
        {
            Some(value) => serde_json::from_str(value.as_str())
                .map_err(|_| "Notification storage is damaged".into()),
            None => Ok(Registration::default()),
        }
    }
    async fn save(
        &self,
        app: &tauri::AppHandle,
        slot: &str,
        value: &Registration,
    ) -> Result<(), String> {
        let bytes = serde_json::to_string(value).map_err(|_| "Cannot encode notification state")?;
        let secret = UnlockSecret::new(bytes)
            .map_err(|_| "Notification state exceeds native storage limit")?;
        app.mobile_platform()
            .store_secret(slot, secret, RememberSecret::Confirmed)
            .await
            .map_err(|_| "Cannot save notification state".into())
    }
    async fn post(
        &self,
        origin: &str,
        path: &str,
        body: serde_json::Value,
    ) -> Result<serde_json::Value, String> {
        let mut response = self
            .client
            .post(endpoint(origin, path)?)
            .json(&body)
            .send()
            .await
            .map_err(|_| "Notification gateway is unavailable")?;
        if !response.status().is_success() {
            return Err("Notification gateway rejected registration".into());
        }
        let mut bytes = Vec::new();
        while let Some(chunk) = response
            .chunk()
            .await
            .map_err(|_| "Notification response failed")?
        {
            if bytes.len() + chunk.len() > 8192 {
                return Err("Notification response is too large".into());
            }
            bytes.extend_from_slice(&chunk);
        }
        serde_json::from_slice(&bytes).map_err(|_| "Invalid notification response".into())
    }
    pub async fn configure(
        &mut self,
        app: &tauri::AppHandle,
        host: &InstanceHost,
        enabled: bool,
    ) -> Result<Status, String> {
        if enabled {
            host.push_networks().await?;
        }
        // Durable disable precedes native callbacks and all network cleanup.
        self.policy.enabled = enabled;
        self.persist_policy()?;
        self.policy_error = false;
        let device = match tokio::time::timeout(
            Duration::from_secs(30),
            app.mobile_platform().push_device(Some(enabled)),
        )
        .await
        {
            Ok(Ok(device)) => device,
            _ => {
                self.policy.enabled = false;
                self.persist_policy()?;
                // Invalidate a late native permission/token completion. Native
                // generation checks ensure it cannot turn opt-in back on.
                let _ = tokio::time::timeout(
                    Duration::from_secs(5),
                    app.mobile_platform().push_device(Some(false)),
                )
                .await;
                return Err("Notifications are unavailable; ordinary chat still works".into());
            }
        };
        if enabled && (!device.enabled || device.permission != "granted") {
            self.policy.enabled = false;
            self.persist_policy()?;
        }
        self.status.enabled = self.policy.enabled;
        self.status.permission = device.permission;
        self.status.registered = false;
        self.status.message = if self.policy.enabled {
            "Notifications enabled; registering securely after reconnect"
        } else {
            "Notifications off; removing relay registrations"
        }
        .into();
        Ok(self.status())
    }
    pub async fn reconcile(&mut self, app: &tauri::AppHandle, host: &InstanceHost) -> Status {
        if self.policy_error {
            let _ = app.mobile_platform().push_device(Some(false)).await;
            self.status.enabled = false;
            self.status.registered = false;
            self.status.message = "Notifications are off because their settings could not be read. Chat is unaffected; enable notifications to repair settings.".into();
            return self.status();
        }
        match app.mobile_platform().push_device(None).await {
            Ok(device) => self.reconcile_device(app, host, device).await,
            Err(_) => {
                self.status.message =
                    "Notifications unavailable; normal reconnect is unchanged".into()
            }
        }
        self.status()
    }
    async fn reconcile_device(
        &mut self,
        app: &tauri::AppHandle,
        host: &InstanceHost,
        device: PushDevice,
    ) {
        self.status.enabled = self.policy.enabled;
        self.status.permission = device.permission.clone();
        self.status.registered = false;
        self.status.message = if device.tapped {
            "Unlock GChat to read new activity"
        } else {
            ""
        }
        .into();
        let result = self.sync(app, host, &device).await;
        if let Err(error) = result {
            self.status.message = error;
        }
    }
    async fn sync(
        &mut self,
        app: &tauri::AppHandle,
        host: &InstanceHost,
        device: &PushDevice,
    ) -> Result<(), String> {
        let active = host.push_networks().await;
        if self.policy.enabled {
            if let Ok(networks) = &active {
                let mut changed = false;
                for network in networks {
                    if !self.policy.networks.contains(network) {
                        self.policy.networks.push(network.clone());
                        changed = true;
                    }
                }
                if changed {
                    self.persist_policy()?;
                }
            }
        }
        let enabled = self.policy.enabled && device.usable_token().is_some();
        if self.policy.enabled && !enabled {
            return Err(if device.enabled && device.permission == "granted" {
                "Waiting for the notification service; normal chat is available"
            } else {
                "Allow notifications in system settings, then reopen GChat"
            }
            .into());
        }
        if enabled {
            active.as_ref().map_err(|error| error.clone())?;
        }
        let mut networks = self.policy.networks.clone();
        if !networks.is_empty() {
            let start = self.cursor % networks.len();
            networks.rotate_left(start);
        }
        let mut failure = None;
        for network in &networks {
            // Advance before I/O: a stalled network or suspension cannot always
            // consume the next reconciliation budget ahead of other networks.
            self.cursor = self.cursor.wrapping_add(1);
            let slot = Self::slot(host, network);
            let mut state = self.load(app, &slot).await?;
            if !enabled {
                if state.reference.is_empty() && !state.registration_pending {
                    continue;
                }
                let mut pending;
                if active.as_ref().is_ok_and(|items| items.contains(network)) {
                    let revision = state.next_revision()?;
                    self.save(app, &slot, &state).await?;
                    pending = host
                        .bind_push_notifications(network, [0; 32], revision, now() + 3600)
                        .await
                        .is_err();
                    // An authenticated installation-scoped revocation also works
                    // after a lost registration response rotated management tokens.
                    let revision = state.next_revision()?;
                    state.registration_pending = true;
                    self.save(app, &slot, &state).await?;
                    use gcoms::runtime::push_notifications::{
                        PushPlatform, PushRegistrationRequest,
                    };
                    let token = "0".repeat(64);
                    let ticket = host
                        .request_push_revocation(
                            network,
                            PushRegistrationRequest {
                                app_id: "boo.gchat.app".into(),
                                installation_nonce: state.nonce,
                                platform: if device.platform == "apns" {
                                    PushPlatform::Apns
                                } else {
                                    PushPlatform::Fcm
                                },
                                token: token.clone(),
                                revision,
                                visible: false,
                            },
                        )
                        .await;
                    match ticket {
                        Ok(ticket) => {
                            let result = self.post(&ticket.gateway_origin, "v1/unregister", serde_json::json!({
                                "ticket":ticket.ticket,"platform":device.platform,"token":token,"visible":false,
                            })).await;
                            pending |= result.is_err();
                        }
                        Err(_) => pending = true,
                    }
                } else {
                    pending = true;
                }
                if !pending {
                    state.reference.clear();
                    state.management_token.clear();
                    state.token_hash.clear();
                    state.expires = 0;
                    state.registration_pending = false;
                    self.save(app, &slot, &state).await?;
                } else {
                    failure = Some(
                        "Notifications off; relay cleanup will retry when GChat reconnects"
                            .to_string(),
                    );
                }
                continue;
            }
            if !active.as_ref().is_ok_and(|items| items.contains(network)) {
                continue;
            }
            let token = device
                .usable_token()
                .ok_or("Notification token is pending")?;
            if state.needs_registration(token, now()) || state.registration_pending {
                let revision = state.next_revision()?;
                state.registration_pending = true;
                self.save(app, &slot, &state).await?;
                use gcoms::runtime::push_notifications::{PushPlatform, PushRegistrationRequest};
                let platform = if device.platform == "apns" {
                    PushPlatform::Apns
                } else {
                    PushPlatform::Fcm
                };
                let ticket = host
                    .request_push_registration(
                        network,
                        PushRegistrationRequest {
                            app_id: "boo.gchat.app".into(),
                            installation_nonce: state.nonce,
                            platform,
                            token: token.into(),
                            revision,
                            visible: true,
                        },
                    )
                    .await?;
                endpoint(&ticket.gateway_origin, "v1/register")?;
                let response = self.post(&ticket.gateway_origin, "v1/register", serde_json::json!({"ticket":ticket.ticket, "platform":device.platform, "token":token, "visible":true})).await?;
                let reference = response["reference"]
                    .as_str()
                    .ok_or("Missing notification reference")?;
                let management = response["management_token"]
                    .as_str()
                    .ok_or("Missing notification receipt")?;
                hex32(reference)?;
                hex32(management)?;
                let expires = response["expires"]
                    .as_u64()
                    .filter(|value| *value > now() && *value <= now() + 7 * 86400)
                    .ok_or("Invalid notification expiry")?;
                state.reference = reference.into();
                state.management_token = management.into();
                state.expires = expires;
                state.origin = ticket.gateway_origin;
                state.token_hash = digest(token.as_bytes());
                state.registration_pending = false;
                self.save(app, &slot, &state).await?;
            }
            let revision = state.next_revision()?;
            self.save(app, &slot, &state).await?;
            host.bind_push_notifications(
                network,
                hex32(&state.reference)?,
                revision,
                (now() + 23 * 3600).min(state.expires),
            )
            .await?;
        }
        if let Some(failure) = failure {
            return Err(failure);
        }
        self.status.registered = enabled;
        if self.status.message.is_empty() {
            self.status.message = if enabled {
                "Notifications on; messages remain encrypted"
            } else {
                "Notifications off"
            }
            .into();
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rotates_token_before_expiry_and_never_reuses_a_revision() {
        let mut state = Registration::default();
        assert!(state.needs_registration("token", 100));
        state.reference = "ab".repeat(32);
        state.token_hash = digest(b"token");
        state.expires = 10_000;
        assert!(!state.needs_registration("token", 100));
        assert!(state.needs_registration("replacement", 100));
        assert!(state.needs_registration("token", 9_000));
        assert_eq!(state.next_revision().unwrap(), 1);
        let mut restored: Registration =
            serde_json::from_str(&serde_json::to_string(&state).unwrap()).unwrap();
        assert_eq!(restored.nonce, state.nonce);
        assert_eq!(restored.next_revision().unwrap(), 2);
        restored.revision = i64::MAX as u64;
        assert!(restored.next_revision().is_err());
    }
    #[test]
    fn gateway_is_https_origin_only_and_references_are_bounded() {
        for bad in [
            "http://gateway",
            "https://u:p@gateway",
            "https://gateway/path",
            "https://gateway?token=x",
            "https://gateway/#x",
            "https://other-operator.example",
            "https://push.gchat.boo:8443",
        ] {
            assert!(endpoint(bad, "v1/register").is_err());
        }
        assert_eq!(
            endpoint("https://push.gchat.boo", "v1/register")
                .unwrap()
                .as_str(),
            "https://push.gchat.boo/v1/register"
        );
        assert!(hex32(&"af".repeat(32)).is_ok());
        assert!(hex32(&"zz".repeat(32)).is_err());
    }
    #[test]
    fn damaged_optional_policy_does_not_prevent_opening_chat() {
        let dir = tempfile::tempdir().unwrap();
        std::fs::write(dir.path().join("push-policy.json"), b"damaged").unwrap();
        let push = Push::new(dir.path()).unwrap();
        assert!(push.policy_error);
        assert!(!push.policy.enabled);
        assert_eq!(
            std::fs::read(dir.path().join("push-policy.json")).unwrap(),
            b"damaged"
        );
    }
    #[test]
    fn disable_policy_is_durable_without_deleting_registration_counters() {
        let dir = tempfile::tempdir().unwrap();
        let mut push = Push::new(dir.path()).unwrap();
        assert!(!push.status().enabled);
        push.policy.enabled = true;
        push.policy.networks.push("primary".into());
        push.persist_policy().unwrap();
        push.policy.enabled = false;
        push.persist_policy().unwrap();
        let restored = Push::new(dir.path()).unwrap();
        assert!(!restored.policy.enabled);
        assert_eq!(restored.policy.networks, ["primary"]);
    }
}
