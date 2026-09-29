use super::*;

// Preserve the hosted event cursor together with its messages and activity in a
// file that legacy GChat cannot rewrite. Only acknowledge runtime events after
// both writes succeed; a crash between writes replays the same events safely.
#[derive(Default, Serialize, Deserialize)]
struct Retained {
    channels: BTreeMap<String, hosted::Archive>,
    activity: Vec<gchat_api::Activity>,
}

pub(super) struct ServiceStateStore {
    legacy: ChatServiceStore,
    hosted: ChatServiceStore,
    contacts: ChatServiceStore,
    preferences: ChatServiceStore,
}
impl ServiceStateStore {
    pub(super) fn open(
        legacy: ChatServiceStore,
        path: &std::path::Path,
        state: &mut UiState,
    ) -> Result<Self, String> {
        let (hosted, retained): (_, Retained) = legacy.hosted_companion(path)?;
        let (contacts, book) = legacy.contact_companion(&path.with_extension("contacts"))?;
        let (preferences, prefs) =
            legacy.preferences_companion(&path.with_extension("preferences"))?;
        state.preferences = prefs;
        contacts::validate_book(&book)?;
        state.contacts = book;
        state.hosted = retained.channels;
        state
            .activity
            .retain(|a| !a.conversation.starts_with("hosted/"));
        state.activity.extend(retained.activity);
        state.activity.sort_by_key(|a| a.timestamp);
        Ok(Self {
            legacy,
            hosted,
            contacts,
            preferences,
        })
    }
    pub(super) fn verify_passphrase(&self, secret: &str) -> Result<(), String> {
        self.legacy.verify_passphrase(secret)
    }
    pub(super) fn save(&self, state: &UiState) -> Result<(), String> {
        if !state.hosted.is_empty() || self.hosted.initialized() {
            self.hosted.save(&Retained {
                channels: state.hosted.clone(),
                activity: state
                    .activity
                    .iter()
                    .filter(|a| a.conversation.starts_with("hosted/"))
                    .cloned()
                    .collect(),
            })?;
        }
        if !state.contacts.is_empty() || self.contacts.initialized() {
            self.contacts.save(&state.contacts)?;
        }
        if !state.preferences.is_empty() || self.preferences.initialized() {
            self.preferences.save(&state.preferences)?;
        }
        let mut legacy = state.clone();
        legacy
            .activity
            .retain(|a| !a.conversation.starts_with("hosted/"));
        self.legacy.save(&legacy)
    }
}
