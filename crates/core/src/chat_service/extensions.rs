//! Optional application capabilities. Authority remains at the configured application.
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use zeroize::Zeroizing;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CommandExtension {
    url: String,
    token_file: PathBuf,
}
#[derive(Serialize)]
pub struct CommandRequest<'a> {
    pub version: u16,
    pub instance_id: &'a str,
    pub operation_id: &'a str,
    pub action: &'a str,
    pub room: &'a str,
    pub text: &'a str,
    pub before: Option<&'a str>,
    pub limit: u16,
}
impl CommandExtension {
    pub fn load(archive: &Path) -> Result<Option<Self>, String> {
        let path = archive.with_extension("extensions.json");
        if !path.exists() {
            return Ok(None);
        }
        crate::private_fs::validate_private_file(&path, "chat extension configuration")?;
        if std::fs::metadata(&path).map_err(|e| e.to_string())?.len() > 4096 {
            return Err("extension configuration exceeds bound".into());
        }
        let mut config: Self =
            serde_json::from_slice(&std::fs::read(&path).map_err(|e| e.to_string())?)
                .map_err(|e| e.to_string())?;
        let url = url::Url::parse(&config.url).map_err(|e| e.to_string())?;
        let loopback = url
            .host_str()
            .is_some_and(|h| matches!(h, "localhost" | "127.0.0.1" | "[::1]"));
        if !url.username().is_empty()
            || url.password().is_some()
            || url.fragment().is_some()
            || !(url.scheme() == "https" || (url.scheme() == "http" && loopback))
        {
            return Err(
                "extension requires HTTPS or explicit loopback HTTP without URL credentials".into(),
            );
        }
        if config.token_file.is_relative() {
            config.token_file = path.parent().unwrap().join(config.token_file);
        }
        Ok(Some(config))
    }
    pub async fn call(&self, request: CommandRequest<'_>) -> Result<gchat_api::Response, String> {
        crate::private_fs::validate_private_file(&self.token_file, "chat extension credential")?;
        crate::private_fs::validate_private_parent(&self.token_file, "chat extension credential")?;
        if std::fs::metadata(&self.token_file)
            .map_err(|e| e.to_string())?
            .len()
            > 4096
        {
            return Err("extension credential exceeds bound".into());
        }
        let token = Zeroizing::new(
            std::fs::read_to_string(&self.token_file).map_err(|_| "read extension credential")?,
        );
        let client = reqwest::Client::builder()
            .redirect(reqwest::redirect::Policy::none())
            .timeout(std::time::Duration::from_secs(
                if request.action == "send" || request.action == "query" {
                    120
                } else {
                    10
                },
            ))
            .build()
            .map_err(|e| e.to_string())?;
        let mut response = client
            .post(&self.url)
            .bearer_auth(token.trim_end_matches(['\r', '\n']))
            .json(&request)
            .send()
            .await
            .map_err(|_| "command extension unavailable")?;
        if !response.status().is_success() {
            return Ok(gchat_api::Response::Error {
                code: match response.status().as_u16() {
                    401 => "authentication",
                    403 => "forbidden",
                    409 => "rejected",
                    400 | 404 | 413 | 422 => "rejected",
                    _ => "unavailable",
                }
                .into(),
                message: format!(
                    "Conversation provider refused the request ({})",
                    response.status()
                ),
            });
        }
        let mut body = Vec::new();
        while let Some(chunk) = response
            .chunk()
            .await
            .map_err(|_| "extension response interrupted")?
        {
            if body.len() + chunk.len() > gchat_api::MAX_FRAME_BYTES {
                return Err("extension response exceeds bound".into());
            }
            body.extend_from_slice(&chunk);
        }
        let response: gchat_api::Response =
            serde_json::from_slice(&body).map_err(|_| "invalid extension response")?;
        Ok(response)
    }
}
