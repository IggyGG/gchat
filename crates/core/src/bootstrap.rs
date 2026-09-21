//! GChat supplies its network trust; recovery and transport belong to GComs.
pub use gcoms::runtime::bootstrap::{http_builder, parse_bootstrap_urls};
pub use gcoms::runtime::contacts::fetch_relay_provision;
pub fn default_provider_urls() -> Vec<String> {
    option_env!("GC_DEFAULT_RELAY_BOOTSTRAP")
        .filter(|value| !value.trim().is_empty())
        .map(|value| {
            value
                .split(',')
                .map(str::trim)
                .filter(|v| !v.is_empty())
                .map(str::to_string)
                .collect()
        })
        .unwrap_or_else(|| {
            crate::network::provider_urls().expect("bundled GChat network defaults must be valid")
        })
}
pub fn import_network_invitation(
    profile: &std::path::Path,
    file: &std::path::Path,
) -> Result<(), String> {
    gcoms_network_client::NetworkClient::for_profile(profile, crate::network::installed()?)?
        .import_invitation_file(file)
}
