//! Transient, confirmed replay progress. No archive or protocol format changes.
use super::*;

#[derive(Default)]
pub(super) struct Progress(BTreeMap<String, Entry>);
struct Entry {
    start: u64,
    cursor: u64,
    visible: bool,
    show_at: Instant,
}
impl Progress {
    pub(super) fn begin(&mut self, id: &str, cursor: u64, now: Instant) -> Instant {
        let entry = self.0.entry(id.into()).or_insert(Entry {
            start: cursor,
            cursor,
            visible: false,
            show_at: now + Duration::from_secs(2),
        });
        entry.cursor = cursor;
        entry.show_at
    }
    pub(super) fn show(&mut self, id: &str) {
        if let Some(entry) = self.0.get_mut(id) {
            entry.visible = true;
        }
    }
    pub(super) fn finish(&mut self, id: &str, cursor: u64) {
        if let Some(entry) = self.0.get_mut(id) {
            if cursor > entry.cursor {
                entry.cursor = cursor;
            } else {
                self.clear(id);
            }
        }
    }
    pub(super) fn clear(&mut self, id: &str) {
        self.0.remove(id);
    }
    pub(super) fn retain(&mut self, ids: &std::collections::BTreeSet<String>) {
        self.0.retain(|id, _| ids.contains(id));
    }
    pub(super) fn view(&self, id: &str) -> Option<gchat_api::ChannelCatchUp> {
        self.0
            .get(id)
            .filter(|entry| entry.visible)
            .map(|entry| gchat_api::ChannelCatchUp {
                applied_records: entry.cursor.saturating_sub(entry.start),
            })
    }
}

/// Errors, task cancellation and shutdown must never leave a busy indicator.
pub(super) struct Attempt<'a> {
    pub service: &'a ChatService,
    pub id: String,
    pub completed: bool,
}
impl Drop for Attempt<'_> {
    fn drop(&mut self) {
        if !self.completed {
            self.service
                .hosted_catchup
                .lock()
                .expect("hosted catch-up")
                .clear(&self.id);
            self.service.invalidate();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pages_accumulate_only_confirmed_progress_and_clear_after_empty_page() {
        let mut progress = Progress::default();
        let now = Instant::now();
        assert_eq!(
            progress.begin("hosted/a", 100, now),
            now + Duration::from_secs(2)
        );
        assert!(progress.view("hosted/a").is_none());
        progress.show("hosted/a");
        assert_eq!(progress.view("hosted/a").unwrap().applied_records, 0);
        progress.finish("hosted/a", 132);
        progress.begin("hosted/a", 132, now + Duration::from_secs(40));
        assert_eq!(progress.view("hosted/a").unwrap().applied_records, 32);
        progress.finish("hosted/a", 164);
        assert_eq!(progress.view("hosted/a").unwrap().applied_records, 64);
        assert!(progress.view("hosted/b").is_none());
        progress.begin("hosted/a", 164, now + Duration::from_secs(80));
        progress.finish("hosted/a", 164);
        assert!(progress.view("hosted/a").is_none());
    }
}
