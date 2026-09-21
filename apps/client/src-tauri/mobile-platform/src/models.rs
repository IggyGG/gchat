use zeroize::Zeroizing;

use crate::{Error, Result};

/// Explicit caller confirmation of the user's remember-unlock choice.
/// There is no default and plugin initialization never stores anything.
#[derive(Clone, Copy, Debug)]
pub enum RememberSecret {
    Confirmed,
}

/// An unlock credential which is redacted in diagnostics and zeroized on drop.
/// Native platform bridges necessarily make temporary JVM/Swift string copies.
pub struct UnlockSecret(Zeroizing<String>);

impl UnlockSecret {
    pub fn new(value: String) -> Result<Self> {
        let value = Zeroizing::new(value);
        if value.is_empty() || value.len() > 4096 || value.contains('\0') {
            return Err(Error::InvalidSecret);
        }
        Ok(Self(value))
    }

    pub fn as_str(&self) -> &str {
        self.0.as_str()
    }
}

impl std::fmt::Debug for UnlockSecret {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("UnlockSecret([REDACTED])")
    }
}

pub(crate) fn validate_slot(slot: &str) -> Result<()> {
    if slot.is_empty()
        || slot.len() > 128
        || !slot
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
    {
        return Err(Error::InvalidSlot);
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validates_opaque_slots_and_redacts_secret() {
        for bad in ["", "../profile", "a/b", "a\\b", "hello world", "å"] {
            assert!(validate_slot(bad).is_err());
        }
        assert!(validate_slot(&"a".repeat(129)).is_err());
        assert!(validate_slot("profile_a-2").is_ok());
        for bad in [String::new(), "a\0b".into(), "a".repeat(4097)] {
            assert!(UnlockSecret::new(bad).is_err());
        }
        let secret = UnlockSecret::new("test credential".into()).unwrap();
        assert_eq!(secret.as_str(), "test credential");
        assert_eq!(format!("{secret:?}"), "UnlockSecret([REDACTED])");
    }
}
