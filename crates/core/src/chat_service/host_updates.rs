//! Maintenance is local-owner authenticated by the existing private IPC server.
use super::host::InstanceHost;
use gchat_api::{PrepareUpdateResult as ResultState, UpdateRequest};
use std::{
    collections::BTreeMap,
    time::{Duration, Instant},
};

#[derive(Default)]
pub(super) struct State {
    views: BTreeMap<String, Instant>,
    prepared: Option<(String, String)>,
}

impl State {
    pub(super) fn preparing(&self) -> bool {
        self.prepared.is_some()
    }
}

impl InstanceHost {
    pub async fn wait_for_update_exit(&self) {
        let mut exit = self.update_exit.subscribe();
        while !*exit.borrow_and_update() {
            if exit.changed().await.is_err() {
                return;
            }
        }
    }

    pub(super) async fn update(&self, request: UpdateRequest) -> Result<ResultState, String> {
        if !self.config.uses_protocol_ipc() {
            return Err("Mobile application updates are managed by the app store".into());
        }
        let view = match &request {
            UpdateRequest::Heartbeat { view }
            | UpdateRequest::Detach { view }
            | UpdateRequest::Prepare { view, .. }
            | UpdateRequest::Abort { view, .. }
            | UpdateRequest::Exit { view, .. } => view,
        };
        if !crate::build_info::valid_hex(view, 32) {
            return Err("Invalid update view identifier".into());
        }
        if let UpdateRequest::Prepare { release, .. }
        | UpdateRequest::Abort { release, .. }
        | UpdateRequest::Exit { release, .. } = &request
        {
            if !crate::build_info::valid_hex(release, 64) {
                return Err("Invalid release identifier".into());
            }
        }
        let mut updates = self.updates.lock().await;
        updates
            .views
            .retain(|_, seen| seen.elapsed() < Duration::from_secs(45));
        // A closed/crashed view cannot leave all future owners permanently paused.
        if updates
            .prepared
            .as_ref()
            .is_some_and(|(owner, _)| !updates.views.contains_key(owner))
        {
            if let Some(current) = self.running.lock().await.as_ref() {
                current.service.resume_after_update().await;
            }
            updates.prepared = None;
        }
        match request {
            UpdateRequest::Heartbeat { view } => {
                if updates
                    .prepared
                    .as_ref()
                    .is_some_and(|(owner, _)| owner != &view)
                {
                    return Ok(ResultState::Busy { reason: "This instance is preparing an update. Open the new window after it restarts.".into() });
                }
                if updates.views.len() >= 32 && !updates.views.contains_key(&view) {
                    return Err("Too many attached update views".into());
                }
                updates.views.insert(view, Instant::now());
                Ok(ResultState::Attached)
            }
            UpdateRequest::Detach { view } => {
                if updates
                    .prepared
                    .as_ref()
                    .is_some_and(|(owner, _)| owner == &view)
                {
                    if let Some(current) = self.running.lock().await.as_ref() {
                        current.service.resume_after_update().await;
                    }
                    updates.prepared = None;
                }
                updates.views.remove(&view);
                Ok(ResultState::Attached)
            }
            UpdateRequest::Prepare { view, release } => {
                if !updates.views.contains_key(&view) {
                    return Err("Attach this view before preparing an update".into());
                }
                if updates.views.keys().any(|id| id != &view) {
                    return Ok(ResultState::Busy {
                        reason: "Another GChat window is attached. Close it before restarting."
                            .into(),
                    });
                }
                if let Some(owner) = &updates.prepared {
                    if owner != &(view.clone(), release.clone()) {
                        return Ok(ResultState::Busy {
                            reason: "Another update is being prepared.".into(),
                        });
                    }
                } else {
                    let running = match self.running.try_lock() {
                        Ok(running) => running,
                        Err(_) => {
                            return Ok(ResultState::Busy {
                                reason: "The instance is changing state. Retry shortly.".into(),
                            })
                        }
                    };
                    if let Some(current) = running.as_ref() {
                        if let Err(reason) = current.service.pause_for_update().await {
                            return Ok(ResultState::Busy { reason });
                        }
                    }
                    updates.prepared = Some((view, release));
                }
                Ok(ResultState::Ready {
                    process_id: std::process::id(),
                    boot_id: self.boot.clone(),
                })
            }
            UpdateRequest::Exit { view, release } => {
                if updates.prepared.as_ref() != Some(&(view, release))
                    || self.running.lock().await.is_some()
                {
                    return Err(
                        "Update must be prepared and the instance checkpointed before exit".into(),
                    );
                }
                let exit = self.update_exit.clone();
                tokio::spawn(async move {
                    tokio::time::sleep(Duration::from_millis(250)).await;
                    let _ = exit.send(true);
                });
                Ok(ResultState::Ready {
                    process_id: std::process::id(),
                    boot_id: self.boot.clone(),
                })
            }
            UpdateRequest::Abort { view, release } => {
                if updates.prepared.as_ref() == Some(&(view, release)) {
                    if let Some(current) = self.running.lock().await.as_ref() {
                        current.service.resume_after_update().await;
                    }
                    updates.prepared = None;
                }
                Ok(ResultState::Attached)
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::super::host::InstanceConfig;
    use super::*;

    #[tokio::test]
    async fn maintenance_owner_lease_and_prepared_exit_are_enforced() {
        let directory = tempfile::tempdir().unwrap();
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            std::fs::set_permissions(directory.path(), std::fs::Permissions::from_mode(0o700))
                .unwrap();
        }
        let mut config = InstanceConfig::from_home(Some(directory.path())).unwrap();
        config.protocol_backend = gcoms::Backend::Embedded;
        let host = InstanceHost::new(config).unwrap();
        let a = "a".repeat(32);
        let b = "b".repeat(32);
        let release = "c".repeat(64);
        assert!(host
            .update(UpdateRequest::Prepare {
                view: a.clone(),
                release: release.clone()
            })
            .await
            .is_err());
        assert!(host
            .update(UpdateRequest::Heartbeat { view: "bad".into() })
            .await
            .is_err());
        for view in [&a, &b] {
            host.update(UpdateRequest::Heartbeat { view: view.clone() })
                .await
                .unwrap();
        }
        assert!(matches!(
            host.update(UpdateRequest::Prepare {
                view: a.clone(),
                release: release.clone()
            })
            .await
            .unwrap(),
            ResultState::Busy { .. }
        ));
        host.update(UpdateRequest::Detach { view: b.clone() })
            .await
            .unwrap();
        assert!(matches!(
            host.update(UpdateRequest::Prepare {
                view: a.clone(),
                release: release.clone()
            })
            .await
            .unwrap(),
            ResultState::Ready { .. }
        ));
        assert!(host
            .update(UpdateRequest::Exit {
                view: b,
                release: release.clone()
            })
            .await
            .is_err());
        // Owner disappearance releases maintenance without changing the profile.
        host.updates
            .lock()
            .await
            .views
            .insert(a.clone(), Instant::now() - Duration::from_secs(46));
        host.update(UpdateRequest::Heartbeat { view: a.clone() })
            .await
            .unwrap();
        assert!(host
            .update(UpdateRequest::Exit {
                view: a.clone(),
                release: release.clone()
            })
            .await
            .is_err());
        host.update(UpdateRequest::Prepare {
            view: a.clone(),
            release: release.clone(),
        })
        .await
        .unwrap();
        let exit = host.wait_for_update_exit();
        host.update(UpdateRequest::Exit { view: a, release })
            .await
            .unwrap();
        tokio::time::timeout(Duration::from_secs(2), exit)
            .await
            .unwrap();
    }
}
