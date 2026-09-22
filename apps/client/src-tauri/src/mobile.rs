//! An app-owned, outbound-only instance. Mobile never launches a desktop daemon.
use gchat_api::{Request, RequestEnvelope, Response, ResponseEnvelope, VERSION};
use gchat_core::chat_service::{
    host::{InstanceConfig, InstanceHost},
    ChatEndpoint,
};
use std::{
    future::Future,
    io::Write,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex as StateMutex,
    },
};
#[cfg(any(target_os = "android", target_os = "ios"))]
use tauri::{Emitter, Manager};
use tauri_plugin_gchat_mobile_platform::{
    LifecycleEvent, MobilePlatformExt, RememberSecret, UnlockSecret,
};
use tokio::sync::{watch, Mutex, RwLock};

/// The native callback and the async lifecycle worker share this short lock.
/// A stale foreground completion can never reopen admission after a later event.
#[derive(Debug)]
struct Admission {
    revision: u64,
    foreground: bool,
    open: bool,
}
impl Admission {
    fn new() -> Self {
        Self {
            revision: 0,
            foreground: true,
            open: true,
        }
    }
    fn publish(&mut self, event: LifecycleEvent) -> u64 {
        self.revision = self.revision.wrapping_add(1);
        self.foreground = event == LifecycleEvent::Foreground;
        self.open = false;
        self.revision
    }
    fn current_foreground(&self, revision: u64) -> bool {
        self.revision == revision && self.foreground
    }
    fn resume(&mut self, revision: u64) -> bool {
        if !self.current_foreground(revision) {
            return false;
        }
        self.open = true;
        true
    }
}

pub struct Attachment {
    host: Arc<InstanceHost>,
    router: RwLock<Arc<gcoms::rpc::Router>>,
    admission: StateMutex<Admission>,
    changed: watch::Sender<u64>,
    transitioning: Mutex<()>,
    activity: RwLock<()>,
    credentials: Mutex<()>,
    auto_resume: AtomicBool,
    remember_path: PathBuf,
    push: Mutex<crate::mobile_push::Push>,
    push_changed: tokio::sync::Notify,
}

fn remember_enabled(path: &Path) -> bool {
    std::fs::read(path).is_ok_and(|contents| contents == b"enabled\n")
}

/// This non-secret opt-in survives a failed native credential deletion. Missing
/// or damaged state is disabled; an intentional lock cannot unlock on restart.
fn persist_remember(path: &Path, enabled: bool) -> Result<(), String> {
    let parent = path.parent().ok_or("Missing mobile profile directory")?;
    let mut pending = tempfile::NamedTempFile::new_in(parent).map_err(|e| e.to_string())?;
    pending
        .write_all(if enabled { b"enabled\n" } else { b"disabled\n" })
        .map_err(|e| e.to_string())?;
    pending.as_file().sync_all().map_err(|e| e.to_string())?;
    pending.persist(path).map_err(|e| e.to_string())?;
    // Android/iOS require the directory barrier too. Windows only compiles this
    // mobile module for its shared unit tests and cannot open directories as files.
    #[cfg(unix)]
    std::fs::File::open(parent)
        .and_then(|dir| dir.sync_all())
        .map_err(|e| e.to_string())?;
    Ok(())
}

fn lifecycle_request(request: &Request) -> bool {
    matches!(request, Request::Lock | Request::Disconnect)
        || matches!(request, Request::Submit { text, .. } if lifecycle_text(text))
}
fn lifecycle_text(text: &str) -> bool {
    matches!(text.trim(), "/lock" | "/disconnect" | "/quit")
}

impl Attachment {
    pub fn new(home: &Path) -> Result<Arc<Self>, String> {
        gchat_core::paths::ensure_private_dir(home, "mobile instance")?;
        let mut config = InstanceConfig::from_home(Some(home))?;
        config.protocol_backend = gcoms::Backend::NetworkClient;
        config.gc2_carrier = true;
        let host = InstanceHost::new(config)?;
        let router = gchat_core::chat_service::rpc::router(host.clone())
            .map_err(|error| error.to_string())?;
        let remember_path = home.join("remember-unlock");
        let enabled = remember_enabled(&remember_path);
        Ok(Arc::new(Self {
            host,
            router: RwLock::new(router),
            admission: StateMutex::new(Admission::new()),
            changed: watch::channel(0).0,
            transitioning: Mutex::new(()),
            activity: RwLock::new(()),
            credentials: Mutex::new(()),
            auto_resume: AtomicBool::new(enabled),
            remember_path,
            push: Mutex::new(crate::mobile_push::Push::new(home)?),
            push_changed: tokio::sync::Notify::new(),
        }))
    }

    fn require_foreground(&self) -> Result<(), String> {
        let gate = self.admission.lock().unwrap_or_else(|e| e.into_inner());
        if gate.open && gate.foreground {
            Ok(())
        } else {
            Err("GChat is paused while the app is in the background".into())
        }
    }
    fn current_foreground(&self, revision: u64) -> bool {
        self.admission
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .current_foreground(revision)
    }
    fn native_event(&self, event: LifecycleEvent) -> u64 {
        let revision = self
            .admission
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .publish(event);
        self.changed.send_replace(revision);
        revision
    }

    /// The task, rather than a possibly cancelled webview invocation, owns the
    /// runtime admission. In particular an unlock must reach InstanceHost's
    /// retained Running slot before a lifecycle drain can checkpoint it.
    async fn admitted<T, F, Fut>(self: Arc<Self>, operation: F) -> Result<T, String>
    where
        T: Send + 'static,
        F: FnOnce(Arc<Self>) -> Fut + Send + 'static,
        Fut: Future<Output = Result<T, String>> + Send + 'static,
    {
        tokio::spawn(async move {
            let _active = self.activity.read().await;
            self.require_foreground()?;
            operation(self.clone()).await
        })
        .await
        .map_err(|_| "Mobile operation worker stopped".to_string())?
    }

    /// Event polls and retryable notification reconciliation can end on
    /// suspension. Admitted chat operations retain their separate durable path;
    /// no long poll keeps the checkpoint drain lock occupied.
    async fn poll<T>(&self, future: impl Future<Output = T>) -> Result<T, String> {
        let mut changed = self.changed.subscribe();
        self.require_foreground()?;
        tokio::select! {
            biased;
            _ = changed.changed() => Err("GChat lifecycle changed; reconnect the view".into()),
            result = future => Ok(result),
        }
    }

    /// Stop admitting before draining owned commands. RPC workers retain their
    /// operation IDs on shutdown; cancellation is never reported as delivery.
    async fn background(&self, app: Option<&tauri::AppHandle>) -> Result<(), String> {
        let _transition = self.transitioning.lock().await;
        self.router.read().await.shutdown().await;
        let _drained = self.activity.write().await;
        // Existing live aliases get one bounded refresh before shutdown; failure
        // cannot delay checkpointing indefinitely or imply successful delivery.
        let _ = tokio::time::timeout(std::time::Duration::from_secs(5), async {
            if let Some(app) = app {
                self.push.lock().await.reconcile(app, &self.host).await;
            }
        })
        .await;
        self.host.flush().await
    }

    async fn foreground(&self, app: &tauri::AppHandle, revision: u64) -> Result<(), String> {
        let _transition = self.transitioning.lock().await;
        if !self.current_foreground(revision) {
            return Ok(());
        }
        let router = gchat_core::chat_service::rpc::router(self.host.clone())
            .map_err(|error| error.to_string())?;
        *self.router.write().await = router;
        let _credential = self.credentials.lock().await;
        let result = async {
            if self.auto_resume.load(Ordering::Acquire) {
                if let Some(secret) = app
                    .mobile_platform()
                    .get_secret(self.host.instance_id())
                    .await
                    .map_err(|error| error.to_string())?
                {
                    if !self.current_foreground(revision) {
                        return Ok(());
                    }
                    let response = self
                        .host
                        .dispatch(RequestEnvelope {
                            version: VERSION,
                            instance_id: Some(self.host.instance_id().into()),
                            request: Request::Unlock {
                                passphrase: secret.as_str().to_owned(),
                                create: false,
                            },
                        })
                        .await;
                    if let Response::Error { message, .. } = response.response {
                        return Err(message);
                    }
                }
            }
            Ok(())
        }
        .await;
        // Even failed device-key access must leave the manual unlock UI usable.
        let resumed = self
            .admission
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .resume(revision);
        if !resumed {
            self.router.read().await.shutdown().await;
            self.host.flush().await?;
        }
        self.push_changed.notify_one();
        result
    }

    async fn forget(&self, app: &tauri::AppHandle) -> Result<(), String> {
        self.auto_resume.store(false, Ordering::Release);
        let policy = persist_remember(&self.remember_path, false);
        let removed = app
            .mobile_platform()
            .delete_secret(self.host.instance_id())
            .await;
        if policy.is_err() || removed.is_err() {
            return Err("GChat is locked, but removing the remembered device credential failed. Keep this device private and retry unlocking without Remember, then lock again.".into());
        }
        Ok(())
    }
}

#[tauri::command]
pub async fn chat_request(
    app: tauri::AppHandle,
    state: tauri::State<'_, Arc<Attachment>>,
    envelope: RequestEnvelope,
) -> Result<ResponseEnvelope, String> {
    if envelope.version != VERSION
        || (!matches!(envelope.request, Request::Identify)
            && envelope.instance_id.as_deref() != Some(state.host.instance_id()))
    {
        return Err("selected instance or version mismatch".into());
    }
    if matches!(envelope.request, Request::Unlock { .. }) {
        return Err("Use the native mobile unlock command".into());
    }
    if matches!(envelope.request, Request::Events { .. }) {
        return state.poll(state.host.dispatch(envelope)).await;
    }
    state
        .inner()
        .clone()
        .admitted(move |state| async move {
            let closing = lifecycle_request(&envelope.request);
            let _credential = if closing {
                Some(state.credentials.lock().await)
            } else {
                None
            };
            let forgotten = if closing {
                state.forget(&app).await
            } else {
                Ok(())
            };
            let response = state.host.dispatch(envelope).await;
            if closing
                && (forgotten.is_err() || matches!(response.response, Response::Error { .. }))
            {
                // Even a failed archive lock must not leave an unlocked app after
                // reporting a failed attempt to remove device credentials.
                state.host.flush().await?;
            }
            forgotten?;
            Ok(response)
        })
        .await
}

#[tauri::command]
pub async fn chat_rpc(
    app: tauri::AppHandle,
    state: tauri::State<'_, Arc<Attachment>>,
    request: gcoms::rpc::Request,
) -> Result<gcoms::rpc::Reply, String> {
    if request.rpc != gcoms::rpc::WIRE_VERSION
        || request.instance != state.host.instance_id()
        || request.service != gchat_api::rpc::SERVICE
        || request.version != gchat_api::rpc::SERVICE_VERSION
    {
        return Err("selected instance or service version mismatch".into());
    }
    if request.method == "unlock" {
        return Err("Use the native mobile unlock command".into());
    }
    if let gcoms::rpc::Invocation::Call { args, .. } = &request.invocation {
        if request.method == "submit"
            && args
                .get("text")
                .and_then(|text| text.as_str())
                .is_some_and(lifecycle_text)
        {
            // The shared UI maps these to dedicated session methods already.
            // Do not hide credential changes inside a separately durable worker.
            return Err("Use the lock or disconnect method for lifecycle commands".into());
        }
    }
    if request.method == "events" {
        let router = state.router.read().await.clone();
        let reply = state
            .poll(router.handle(
                gcoms::rpc::Caller {
                    principal: "local-owner".into(),
                },
                request.clone(),
            ))
            .await?;
        request
            .check_reply(&reply)
            .map_err(|error| error.to_string())?;
        return Ok(reply);
    }
    state
        .inner()
        .clone()
        .admitted(move |state| async move {
            let closing = matches!(request.method.as_str(), "lock" | "disconnect")
                && matches!(request.invocation, gcoms::rpc::Invocation::Call { .. });
            let _credential = if closing {
                Some(state.credentials.lock().await)
            } else {
                None
            };
            let forgotten = if closing {
                state.forget(&app).await
            } else {
                Ok(())
            };
            let router = state.router.read().await.clone();
            let reply = router
                .handle(
                    gcoms::rpc::Caller {
                        principal: "local-owner".into(),
                    },
                    request.clone(),
                )
                .await;
            if closing
                && (forgotten.is_err()
                    || !matches!(
                        reply.body,
                        gcoms::rpc::ReplyBody::Done {
                            outcome: gcoms::rpc::Outcome::Ok(_)
                        }
                    ))
            {
                state.host.flush().await?;
            }
            forgotten?;
            request
                .check_reply(&reply)
                .map_err(|error| error.to_string())?;
            Ok(reply)
        })
        .await
}

#[tauri::command]
pub async fn chat_file_io(
    state: tauri::State<'_, Arc<Attachment>>,
    request: tauri::ipc::Request<'_>,
) -> Result<tauri::ipc::Response, String> {
    let tauri::ipc::InvokeBody::Raw(frame) = request.body() else {
        return Err("Expected a binary file frame".into());
    };
    let (header, _) = gchat_api::files::decode_io(frame)?;
    if header.instance != state.host.instance_id() {
        return Err("File request belongs to another instance".into());
    }
    let frame = frame.clone();
    let bytes = state
        .inner()
        .clone()
        .admitted(move |state| async move { state.host.clone().file_io(frame).await })
        .await?;
    Ok(tauri::ipc::Response::new(bytes))
}

#[derive(serde::Serialize)]
struct UnlockResult {
    response: Response,
    warning: Option<String>,
}

/// User-confirmed storage goes directly to the OS vault after a successful
/// unlock. Neither an OS credential nor a saved passphrase is returned to JS.
#[tauri::command]
async fn chat_mobile_unlock(
    app: tauri::AppHandle,
    state: tauri::State<'_, Arc<Attachment>>,
    passphrase: String,
    create: bool,
    remember: bool,
) -> Result<UnlockResult, String> {
    let passphrase = zeroize::Zeroizing::new(passphrase);
    state.inner().clone().admitted(move |state| async move {
        let _credential = state.credentials.lock().await;
        let response = state.host.dispatch(RequestEnvelope {
            version: VERSION,
            instance_id: Some(state.host.instance_id().into()),
            request: Request::Unlock { passphrase: passphrase.to_string(), create },
        }).await.response;
        if let Response::Error { message, .. } = response { return Err(message); }
        state.auto_resume.store(false, Ordering::Release);
        let disabled = persist_remember(&state.remember_path, false);
        let stored = if remember && disabled.is_ok() {
            match UnlockSecret::new(passphrase.to_string()) {
                Ok(secret) => app.mobile_platform().store_secret(state.host.instance_id(), secret, RememberSecret::Confirmed).await.map_err(|e| e.to_string()),
                Err(error) => Err(error.to_string()),
            }.and_then(|()| persist_remember(&state.remember_path, true))
        } else {
            let removed = app.mobile_platform().delete_secret(state.host.instance_id()).await.map_err(|e| e.to_string());
            disabled.and(removed)
        };
        state.auto_resume.store(remember && stored.is_ok(), Ordering::Release);
        state.push_changed.notify_one();
        Ok(UnlockResult {
            response,
            warning: stored.err().map(|_| if remember {
                "GChat opened, but secure device storage was unavailable. You will need your passphrase after suspension.".into()
            } else {
                "GChat opened, but the saved device credential could not be removed. Lock and retry before sharing this device.".into()
            }),
        })
    }).await
}

#[tauri::command]
async fn chat_mobile_push_status(
    state: tauri::State<'_, Arc<Attachment>>,
) -> Result<crate::mobile_push::Status, String> {
    Ok(state.push.lock().await.status())
}

#[tauri::command]
async fn chat_mobile_push_configure(
    app: tauri::AppHandle,
    state: tauri::State<'_, Arc<Attachment>>,
    enabled: bool,
) -> Result<crate::mobile_push::Status, String> {
    state
        .inner()
        .clone()
        .admitted(move |state| async move {
            let status = state
                .push
                .lock()
                .await
                .configure(&app, &state.host, enabled)
                .await;
            state.push_changed.notify_one();
            status
        })
        .await
}

#[tauri::command]
fn chat_mobile_available() -> bool {
    true
}

#[tauri::command]
#[cfg(any(target_os = "android", target_os = "ios"))]
async fn chat_file_save(
    app: tauri::AppHandle,
    state: tauri::State<'_, Arc<Attachment>>,
    id: String,
) -> Result<String, String> {
    // Staging performs bounded cache reads; after staging the picker/copy owns
    // only private file handles. Suspension must never wait for a native picker.
    state.require_foreground()?;
    crate::mobile_export::save(&app, state.host.clone(), &id).await
}

#[tauri::command]
#[cfg(any(target_os = "android", target_os = "ios"))]
async fn chat_invitation_save(
    app: tauri::AppHandle,
    state: tauri::State<'_, Arc<Attachment>>,
    invitation: String,
) -> Result<Option<String>, String> {
    state.require_foreground()?;
    crate::mobile_export::save_invitation(&app, invitation).await
}

#[cfg(any(target_os = "android", target_os = "ios"))]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_gchat_mobile_platform::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .setup(|app| {
            let state = Attachment::new(&app.path().app_data_dir()?.join("instance"))
                .map_err(std::io::Error::other)?;
            let (events, mut receiver) = tokio::sync::mpsc::unbounded_channel();
            let gate = state.clone();
            let subscription = tauri_plugin_gchat_mobile_platform::on_lifecycle(move |event| {
                // Close admission before queueing, and bind any reopen to this
                // exact generation, not whichever event the worker last saw.
                let revision = gate.native_event(event);
                let _ = events.send((event, revision));
            });
            app.manage(subscription);
            app.manage(state.clone());
            let push_state = state.clone();
            let push_app = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                let mut interval = tokio::time::interval(std::time::Duration::from_secs(30));
                interval.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);
                loop {
                    tokio::select! { _ = interval.tick() => {}, _ = push_state.push_changed.notified() => {} }
                    let app = push_app.clone();
                    let _ = push_state.clone().admitted(move |state| async move {
                        // Push is opportunistic: a lifecycle transition cancels
                        // this poll before the profile's checkpoint drain.
                        let status = state.poll(tokio::time::timeout(std::time::Duration::from_secs(60), async {
                            state.push.lock().await.reconcile(&app, &state.host).await
                        })).await?;
                        if let Ok(status) = status { let _ = app.emit("gchat-push-status", status); }
                        Ok(())
                    }).await;
                }
            });
            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                while let Some((event, revision)) = receiver.recv().await {
                    let result = match event {
                        LifecycleEvent::Background => state.background(Some(&handle)).await,
                        LifecycleEvent::Foreground => state.foreground(&handle, revision).await,
                    };
                    if let Err(error) = result {
                        let _ = handle.emit("gchat-lifecycle-error", error);
                    }
                }
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            chat_request,
            chat_rpc,
            chat_file_io,
            chat_file_save,
            chat_invitation_save,
            chat_mobile_unlock,
            chat_mobile_available,
            chat_mobile_push_status,
            chat_mobile_push_configure,
        ])
        .run(tauri::generate_context!())
        .expect("gchat mobile application");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn queued_foreground_cannot_reopen_after_a_newer_background() {
        let mut gate = Admission::new();
        let first = gate.publish(LifecycleEvent::Foreground);
        gate.publish(LifecycleEvent::Background);
        assert!(!gate.resume(first));
        assert!(!gate.open);
        let current = gate.publish(LifecycleEvent::Foreground);
        assert!(gate.resume(current));
        assert!(gate.open);
    }

    #[test]
    fn background_closes_before_worker_and_resume_needs_exact_revision() {
        let mut gate = Admission::new();
        gate.publish(LifecycleEvent::Background);
        assert!(!gate.open);
        let pending = gate.publish(LifecycleEvent::Foreground);
        assert!(!gate.open);
        gate.publish(LifecycleEvent::Background);
        let latest = gate.publish(LifecycleEvent::Foreground);
        assert!(!gate.resume(pending));
        assert!(gate.resume(latest));
    }

    #[test]
    fn remembered_unlock_is_explicit_and_lock_persists_suppression() {
        let directory = tempfile::tempdir().unwrap();
        let path = directory.path().join("remember-unlock");
        assert!(!remember_enabled(&path));
        persist_remember(&path, true).unwrap();
        assert!(remember_enabled(&path));
        // This write precedes native credential deletion: even a vault error
        // cannot make a new Attachment consume the old OS credential.
        persist_remember(&path, false).unwrap();
        assert!(!remember_enabled(&path));
        std::fs::write(&path, b"damaged").unwrap();
        assert!(!remember_enabled(&path));
    }

    #[tokio::test]
    async fn cancelled_view_keeps_owned_work_until_background_can_drain() {
        let directory = tempfile::tempdir().unwrap();
        let state = Attachment::new(&directory.path().join("instance")).unwrap();
        let (entered, started) = tokio::sync::oneshot::channel();
        let (release, resume) = tokio::sync::oneshot::channel();
        let committed = Arc::new(AtomicBool::new(false));
        let completed = committed.clone();
        let call = tokio::spawn(state.clone().admitted(move |_| async move {
            let _ = entered.send(());
            resume.await.map_err(|e| e.to_string())?;
            completed.store(true, Ordering::Release);
            Ok(())
        }));
        started.await.unwrap();
        call.abort();
        assert!(call.await.unwrap_err().is_cancelled());
        state.native_event(LifecycleEvent::Background);
        let draining = state.clone();
        let drain = tokio::spawn(async move { draining.background(None).await });
        tokio::task::yield_now().await;
        assert!(!drain.is_finished());
        release.send(()).unwrap();
        tokio::time::timeout(std::time::Duration::from_secs(2), drain)
            .await
            .unwrap()
            .unwrap()
            .unwrap();
        assert!(committed.load(Ordering::Acquire));
        assert!(state.clone().admitted(|_| async { Ok(()) }).await.is_err());
    }

    #[tokio::test]
    async fn native_background_cancels_read_only_poll_without_waiting_for_poll_timeout() {
        let directory = tempfile::tempdir().unwrap();
        let state = Attachment::new(&directory.path().join("instance")).unwrap();
        let (entered, started) = tokio::sync::oneshot::channel();
        let observing = state.clone();
        let poll = tokio::spawn(async move {
            observing
                .poll(async {
                    let _ = entered.send(());
                    std::future::pending::<()>().await
                })
                .await
        });
        started.await.unwrap();
        state.native_event(LifecycleEvent::Background);
        assert!(
            tokio::time::timeout(std::time::Duration::from_secs(2), poll)
                .await
                .unwrap()
                .unwrap()
                .is_err()
        );
        state.background(None).await.unwrap();
    }
}
