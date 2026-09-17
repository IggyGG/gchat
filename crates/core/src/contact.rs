//! Contact book: channel-independent peers with verification state.

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Contact {
    /// Local display name (user-chosen).
    pub name: String,
    /// base64url NodeInfo card, exactly as received out-of-band.
    pub card: String,
    /// Safety number of the peer's identity key at add time.
    pub safety_number: String,
    /// True once the user confirmed the safety number out-of-band.
    pub verified: bool,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct ContactBook {
    pub contacts: Vec<Contact>,
}

impl ContactBook {
    pub fn add(&mut self, contact: Contact) -> Result<(), String> {
        if self.contacts.iter().any(|c| c.name == contact.name) {
            return Err("name taken".into());
        }
        if self.contacts.iter().any(|c| c.card == contact.card) {
            return Err("card already in contacts".into());
        }
        self.contacts.push(contact);
        Ok(())
    }

    pub fn get(&self, name: &str) -> Option<&Contact> {
        self.contacts.iter().find(|c| c.name == name)
    }

    pub fn get_mut(&mut self, name: &str) -> Option<&mut Contact> {
        self.contacts.iter_mut().find(|c| c.name == name)
    }

    pub fn remove(&mut self, name: &str) -> bool {
        let before = self.contacts.len();
        self.contacts.retain(|c| c.name != name);
        self.contacts.len() != before
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn contact(name: &str) -> Contact {
        Contact {
            name: name.into(),
            card: format!("card-{name}"),
            safety_number: "AAAA2345 BBBB6789 CCCC2345 DDDD6789 EEEE2345".into(),
            verified: false,
        }
    }

    #[test]
    fn add_get_remove() {
        let mut book = ContactBook::default();
        book.add(contact("ada")).unwrap();
        assert!(book.add(contact("ada")).is_err());
        assert!(book.get("ada").is_some());
        book.get_mut("ada").unwrap().verified = true;
        assert!(book.get("ada").unwrap().verified);
        assert!(book.remove("ada"));
        assert!(book.get("ada").is_none());
    }
}
