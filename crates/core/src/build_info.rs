//! Release workers bind these values before compiling the paired application.
pub fn current() -> Option<gchat_api::BuildInfo> {
    let release = option_env!("GCHAT_RELEASE_ID")?;
    let chat = option_env!("GCHAT_SOURCE_COMMIT")?;
    let coms = option_env!("GCOMS_SOURCE_COMMIT")?;
    let version = option_env!("GCHAT_APP_VERSION")?;
    if !valid_hex(release, 64) || !valid_hex(chat, 40) || !valid_hex(coms, 40) {
        return None;
    }
    Some(gchat_api::BuildInfo {
        release_id: release.into(),
        gchat_commit: chat.into(),
        gcoms_commit: coms.into(),
        version: version.into(),
    })
}

pub(crate) fn valid_hex(value: &str, length: usize) -> bool {
    value.len() == length
        && value
            .bytes()
            .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
}
