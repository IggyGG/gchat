//! Conversations and message history (client-local; SPEC §1 allows local
//! archiving — the protocol itself persists nothing).

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Message {
    pub id: [u8; 16],
    pub ts_unix: u64,
    /// Sender display name (own name for outgoing, channel pseudonym or
    /// contact name for incoming).
    pub sender: String,
    pub mine: bool,
    pub text: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum Conversation {
    Direct {
        /// Contact name (key into the contact book).
        peer: String,
        messages: Vec<Message>,
    },
    Channel {
        channel: String,
        /// Our channel-local pseudonym.
        display: String,
        /// True if we own the channel.
        owned: bool,
        messages: Vec<Message>,
    },
}

impl Conversation {
    pub fn key(&self) -> &str {
        match self {
            Conversation::Direct { peer, .. } => peer,
            Conversation::Channel { channel, .. } => channel,
        }
    }

    pub fn messages(&self) -> &[Message] {
        match self {
            Conversation::Direct { messages, .. } => messages,
            Conversation::Channel { messages, .. } => messages,
        }
    }

    pub fn push(&mut self, msg: Message) {
        match self {
            Conversation::Direct { messages, .. } => messages.push(msg),
            Conversation::Channel { messages, .. } => messages.push(msg),
        }
    }

    pub fn contains_id(&self, id: &[u8; 16]) -> bool {
        self.messages().iter().any(|m| &m.id == id)
    }
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct Conversations {
    pub list: Vec<Conversation>,
}

impl Conversations {
    pub fn direct(&mut self, peer: &str) -> &mut Conversation {
        if !self
            .list
            .iter()
            .any(|c| matches!(c, Conversation::Direct { peer: p, .. } if p == peer))
        {
            self.list.push(Conversation::Direct {
                peer: peer.to_string(),
                messages: Vec::new(),
            });
        }
        self.list
            .iter_mut()
            .find(|c| matches!(c, Conversation::Direct { peer: p, .. } if p == peer))
            .unwrap()
    }

    pub fn channel(&mut self, channel: &str) -> Option<&mut Conversation> {
        self.list
            .iter_mut()
            .find(|c| matches!(c, Conversation::Channel { channel: ch, .. } if ch == channel))
    }

    pub fn add_channel(&mut self, channel: &str, display: &str, owned: bool) {
        if self.channel(channel).is_some() {
            return;
        }
        self.list.push(Conversation::Channel {
            channel: channel.to_string(),
            display: display.to_string(),
            owned,
            messages: Vec::new(),
        });
    }

    pub fn remove_channel(&mut self, channel: &str) {
        self.list
            .retain(|c| !matches!(c, Conversation::Channel { channel: ch, .. } if ch == channel));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn msg(id: u8, text: &str) -> Message {
        Message {
            id: [id; 16],
            ts_unix: 1,
            sender: "x".into(),
            mine: false,
            text: text.into(),
        }
    }

    #[test]
    fn direct_created_lazily_and_dedups_by_id() {
        let mut cvs = Conversations::default();
        cvs.direct("ada").push(msg(1, "hi"));
        cvs.direct("ada").push(msg(2, "there"));
        assert_eq!(cvs.list.len(), 1);
        assert!(cvs.direct("ada").contains_id(&[1; 16]));
        assert!(!cvs.direct("ada").contains_id(&[3; 16]));
    }

    #[test]
    fn channel_lifecycle() {
        let mut cvs = Conversations::default();
        cvs.add_channel("ops", "ghost-1", true);
        cvs.add_channel("ops", "ghost-1", true); // idempotent
        assert_eq!(cvs.list.len(), 1);
        cvs.channel("ops").unwrap().push(msg(1, "all hands"));
        assert_eq!(cvs.channel("ops").unwrap().messages().len(), 1);
        cvs.remove_channel("ops");
        assert!(cvs.channel("ops").is_none());
    }
}
