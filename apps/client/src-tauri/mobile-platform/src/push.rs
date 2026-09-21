use serde::{Deserialize, Serialize};

/// Native-only data. Device tokens are never exposed to the webview or Debug.
#[derive(Clone, Deserialize, Serialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct PushDevice {
    pub enabled: bool,
    pub permission: String,
    pub platform: String,
    pub token: Option<String>,
    pub tapped: bool,
}

impl PushDevice {
    pub fn usable_token(&self) -> Option<&str> {
        if !self.enabled || self.permission != "granted" {
            return None;
        }
        let token = self.token.as_deref()?;
        let valid = match self.platform.as_str() {
            "apns" => {
                (32..=512).contains(&token.len())
                    && token.len() % 2 == 0
                    && token.bytes().all(|b| b.is_ascii_hexdigit())
            }
            "fcm" => {
                (1..=4096).contains(&token.len()) && token.bytes().all(|b| b.is_ascii_graphic())
            }
            _ => false,
        };
        valid.then_some(token)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn permission_and_opt_in_gate_every_token() {
        let mut value = PushDevice {
            enabled: true,
            permission: "granted".into(),
            platform: "fcm".into(),
            token: Some("fixture-token".into()),
            tapped: true,
        };
        assert!(value.usable_token().is_some());
        value.permission = "denied".into();
        assert!(value.usable_token().is_none());
        value.permission = "granted".into();
        value.enabled = false;
        assert!(value.usable_token().is_none());
        value.enabled = true;
        value.token = Some("bad\nvalue".into());
        assert!(value.usable_token().is_none());
        value.platform = "apns".into();
        value.token = Some("af".repeat(32));
        assert!(value.usable_token().is_some());
    }
}
