//! Never stop a host while a local request or admitted RPC still owns work.
use std::{collections::BTreeSet, sync::Mutex};

#[derive(Default)]
struct State {
    paused: bool,
    requests: usize,
    operations: BTreeSet<String>,
}
#[derive(Default)]
pub(super) struct UpdateGate(Mutex<State>);
pub(super) struct RequestGuard<'a>(&'a UpdateGate);

impl UpdateGate {
    #[cfg(test)]
    pub fn active_requests(&self) -> usize {
        self.0.lock().unwrap().requests
    }
    pub fn enter(&self) -> Result<RequestGuard<'_>, String> {
        let mut state = self.0.lock().map_err(|_| "Maintenance state unavailable")?;
        if state.paused {
            return Err("This instance is preparing an update. Retry after it restarts.".into());
        }
        state.requests += 1;
        Ok(RequestGuard(self))
    }
    pub fn admitted(&self, id: String) {
        self.0
            .lock()
            .expect("maintenance state")
            .operations
            .insert(id);
    }
    pub fn completed(&self, id: &str) {
        self.0
            .lock()
            .expect("maintenance state")
            .operations
            .remove(id);
    }
    pub fn pause(&self) -> Result<(), String> {
        let mut state = self.0.lock().map_err(|_| "Maintenance state unavailable")?;
        if state.requests != 0 || !state.operations.is_empty() {
            return Err("An operation is still finishing. The update will wait.".into());
        }
        state.paused = true;
        Ok(())
    }
    pub fn resume(&self) {
        self.0.lock().expect("maintenance state").paused = false;
    }
}
impl Drop for RequestGuard<'_> {
    fn drop(&mut self) {
        self.0 .0.lock().expect("maintenance state").requests -= 1;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn admission_outlives_request_until_durable_completion() {
        let gate = UpdateGate::default();
        let request = gate.enter().unwrap();
        gate.admitted("original-id".into());
        drop(request);
        assert!(gate.pause().is_err());
        gate.completed("original-id");
        gate.pause().unwrap();
        assert!(gate.enter().is_err());
        gate.resume();
        assert!(gate.enter().is_ok());
    }
    #[test]
    fn outstanding_request_is_not_cancelled_by_preparation() {
        let gate = UpdateGate::default();
        let request = gate.enter().unwrap();
        assert!(gate.pause().is_err());
        drop(request);
        gate.pause().unwrap();
    }
}
