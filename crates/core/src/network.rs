//! GChat's application-owned default network. GComs accepts caller-supplied trust.
use std::{io::Read, path::Path};

pub fn installed() -> Result<gcoms_network_client::InstalledNetwork, String> {
    gcoms_network_client::InstalledNetwork::from_json(include_bytes!(
        "../assets/gchat-network.json"
    ))
}
pub fn provider_urls() -> Result<Vec<String>, String> {
    let network = installed()?;
    Ok(network
        .defaults_at(network.signed_defaults.defaults.issued_at, 0)?
        .provider_urls)
}

pub(crate) fn installed_json() -> Vec<u8> {
    include_bytes!("../assets/gchat-network.json").to_vec()
}

/// An operator may select a separately signed network for a new instance.
/// The SDK still binds retained profiles to their original network/root.
pub(crate) fn selected_json(path: Option<&Path>) -> Result<Vec<u8>, String> {
    let Some(path) = path else {
        return Ok(installed_json());
    };
    if !path.is_absolute()
        || path.components().any(|p| matches!(p, std::path::Component::ParentDir))
    {
        return Err("network configuration must have an absolute path".into());
    }
    crate::private_fs::validate_private_parent(path, "network configuration")?;
    crate::private_fs::validate_private_file(path, "network configuration")?;
    const LIMIT: u64 = 512 * 1024;
    let mut bytes = Vec::new();
    std::fs::File::open(path)
        .map_err(|e| format!("open network configuration: {e}"))?
        .take(LIMIT + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| format!("read network configuration: {e}"))?;
    if bytes.len() as u64 > LIMIT {
        return Err("network configuration exceeds size bound".into());
    }
    let network = gcoms_network_client::InstalledNetwork::from_json(&bytes)?;
    network.defaults_at(gcoms_network_client::now_unix(), 0)?;
    Ok(bytes)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn selected_network_requires_private_bounded_signed_configuration() {
        let dir = tempfile::tempdir().unwrap();
        crate::private_fs::make_private(dir.path(), true).unwrap();
        let path = dir.path().join("network.json");
        let original = installed_json();
        std::fs::write(&path, &original).unwrap();
        crate::private_fs::make_private(&path, false).unwrap();
        assert_eq!(selected_json(None).unwrap(), original);
        assert_eq!(selected_json(Some(&path)).unwrap(), original);
        let mut changed: serde_json::Value = serde_json::from_slice(&original).unwrap();
        changed["signed_defaults"]["defaults"]["network_id"] = "different-network".into();
        std::fs::write(&path, serde_json::to_vec(&changed).unwrap()).unwrap();
        assert!(selected_json(Some(&path)).is_err());
        std::fs::write(&path, vec![b' '; 512 * 1024 + 1]).unwrap();
        assert!(selected_json(Some(&path)).unwrap_err().contains("size bound"));
        assert!(selected_json(Some(Path::new("network.json"))).is_err());
        #[cfg(unix)]
        {
            use std::os::unix::fs::{symlink, PermissionsExt};
            std::fs::write(&path, &original).unwrap();
            std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o644)).unwrap();
            assert!(selected_json(Some(&path)).is_err());
            crate::private_fs::make_private(&path, false).unwrap();
            let alias = dir.path().join("alias.json");
            symlink(&path, &alias).unwrap();
            assert!(selected_json(Some(&alias)).is_err());
        }
    }
}
