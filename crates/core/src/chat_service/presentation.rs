//! Cached, change-driven UI projection. This never acknowledges protocol delivery.
use super::*;

pub(super) struct Presentation {
    changed: watch::Sender<u64>,
    cache: std::sync::Mutex<Option<Cached>>,
    #[cfg(test)]
    builds: std::sync::atomic::AtomicUsize,
}
struct Cached {
    service_version: u64,
    client_version: u64,
    expires: Instant,
    locked: bool,
    snapshot: Arc<Snapshot>,
}
impl Default for Presentation {
    fn default() -> Self {
        Self {
            changed: watch::channel(0).0,
            cache: std::sync::Mutex::new(None),
            #[cfg(test)]
            builds: std::sync::atomic::AtomicUsize::new(0),
        }
    }
}
pub(super) struct InvalidateOnDrop<'a>(pub &'a ChatService);
impl Drop for InvalidateOnDrop<'_> {
    fn drop(&mut self) {
        self.0.invalidate();
    }
}

impl ChatService {
    pub(super) fn invalidate(&self) {
        // Clear sensitive cached data on lock as well as making the version stale.
        self.presentation
            .cache
            .lock()
            .expect("presentation cache")
            .take();
        self.presentation
            .changed
            .send_modify(|v| *v = v.wrapping_add(1));
    }

    pub(super) fn provider_fingerprint(&self) -> Vec<u8> {
        serde_json::to_vec(&(
            &*self.projection.read().expect("projection lock"),
            &*self.provider_error.read().expect("provider state lock"),
        ))
        .expect("serializable provider projection")
    }

    pub async fn snapshot(&self) -> Result<Snapshot, String> {
        Ok((*self.presentation_snapshot().await?.0).clone())
    }

    async fn presentation_snapshot(&self) -> Result<(Arc<Snapshot>, Instant), String> {
        // Lifecycle and mutations use this same lock: never return unlocked data
        // after a completed lock, even when a previous attachment populated cache.
        let mut session = self.session.lock().await;
        let service_version = *self.presentation.changed.borrow();
        let client_version = session
            .as_ref()
            .map(|s| *s.client.presentation_changes().borrow())
            .unwrap_or(0);
        let locked = session.as_ref().is_none_or(|s| s.ui_locked);
        let now = Instant::now();
        if let Some(cached) = self
            .presentation
            .cache
            .lock()
            .expect("presentation cache")
            .as_ref()
        {
            if cached.service_version == service_version
                && cached.client_version == client_version
                && cached.locked == locked
                && cached.expires > now
            {
                return Ok((cached.snapshot.clone(), cached.expires));
            }
        }
        if let Some(current) = session.as_mut().filter(|s| !s.ui_locked) {
            Self::refresh_channel_topics(current).await?;
        }
        let mut expires = now + Duration::from_secs(7 * 24 * 3600);
        if let Some(current) = session.as_ref().filter(|s| !s.ui_locked) {
            if let Some(at) = current.client.next_presence_expiry() {
                expires = expires.min(at);
            }
            // Operation retention is time-based even without any new events.
            if let Some(seconds) = current
                .state
                .operations
                .values()
                .map(|r| r.at.saturating_add(7 * 24 * 3600))
                .filter(|end| *end > super::now())
                .map(|end| end.saturating_sub(super::now()))
                .min()
            {
                expires = expires.min(now + Duration::from_secs(seconds));
            }
        }
        let snapshot = Arc::new(self.project(session.as_ref()));
        #[cfg(test)]
        self.presentation
            .builds
            .fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        // Save the versions read BEFORE building. Any concurrent incoming event
        // leaves this entry stale and wakes waiters instead of getting lost.
        *self.presentation.cache.lock().expect("presentation cache") = Some(Cached {
            service_version,
            client_version,
            expires,
            locked,
            snapshot: snapshot.clone(),
        });
        Ok((snapshot, expires))
    }

    pub(super) async fn wait_for_changes(
        &self,
        after: String,
        wait_ms: u16,
    ) -> Result<Response, String> {
        let deadline = Instant::now() + Duration::from_millis(u64::from(wait_ms.min(20_000)));
        let mut changes = self.presentation.changed.subscribe();
        let mut stopped = self.stopped.subscribe();
        loop {
            // Subscribe before checking the snapshot, including the first unlock.
            changes.borrow_and_update();
            let mut client_changes = self
                .session
                .lock()
                .await
                .as_ref()
                .map(|s| s.client.presentation_changes());
            let (snapshot, expires) = self.presentation_snapshot().await?;
            if snapshot.revision != after || Instant::now() >= deadline {
                return Ok(Response::Changed {
                    revision: snapshot.revision.clone(),
                });
            }
            if *stopped.borrow() {
                return Err("instance disconnected".into());
            }
            tokio::select! {
                _ = changes.changed() => {},
                _ = async { match client_changes.as_mut() {
                    Some(changes) => { let _ = changes.changed().await; },
                    None => std::future::pending::<()>().await,
                } } => {},
                _ = stopped.changed() => return Err("instance disconnected".into()),
                _ = tokio::time::sleep_until(deadline.min(expires).into()) => {},
            }
        }
    }
}
