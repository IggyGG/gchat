//! Desktop contribution options shared by the desktop, terminal and daemon.
#[derive(clap::Args, Clone, Default)]
pub struct RelaySharingArgs {
    /// Disable contributing relay capacity; personal messaging stays available.
    #[arg(long)]
    pub no_relay_sharing: bool,
    /// Keep the listener without requesting a router port mapping.
    #[arg(long)]
    pub no_router_mapping: bool,
    /// Maximum contribution circuits (default 32).
    #[arg(long)]
    pub relay_circuits: Option<usize>,
    /// Maximum contribution connections (default twice the circuit count).
    #[arg(long)]
    pub relay_connections: Option<usize>,
    /// Aggregate contribution bandwidth in bytes per second (default 524288).
    #[arg(long)]
    pub relay_bandwidth: Option<usize>,
}

impl RelaySharingArgs {
    #[cfg(not(any(target_os = "android", target_os = "ios")))]
    pub fn apply(&self) -> Result<(), String> {
        if !self.no_relay_sharing
            && !self.no_router_mapping
            && self.relay_circuits.is_none()
            && self.relay_connections.is_none()
            && self.relay_bandwidth.is_none()
        {
            return Ok(());
        }
        let mut config = crate::runtime::desktop_relay_config()?;
        config.enabled &= !self.no_relay_sharing;
        config.router_mapping &= !self.no_router_mapping;
        if let Some(circuits) = self.relay_circuits {
            config.circuits = circuits;
            config.connections = circuits.saturating_mul(2);
            config.bandwidth_bytes_per_second = config
                .bandwidth_bytes_per_second
                .max(circuits.saturating_mul(8192).saturating_add(256 * 1024));
        }
        if let Some(connections) = self.relay_connections {
            config.connections = connections;
        }
        if let Some(bandwidth) = self.relay_bandwidth {
            config.bandwidth_bytes_per_second = bandwidth;
        }
        config.validate()?;
        crate::runtime::set_desktop_relay_config(config);
        Ok(())
    }
}
