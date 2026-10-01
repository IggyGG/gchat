//! Explicit local component attachment to an existing GChat identity.
use gcoms_sdk::{component::RoutingPolicy, machine::MachineRegistry};
use serde::{Deserialize, Serialize};

pub const CONFIG_LIMIT: u64 = 1024 * 1024;

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub struct FleetConfig {
    pub version: u16,
    pub safety_number: String,
    pub primary_component: [u8; 16],
    pub registry: MachineRegistry,
}

impl FleetConfig {
    pub fn validate(&self) -> Result<(), String> {
        self.registry.validate().map_err(|e| e.to_string())?;
        if self.version != 1
            || self.safety_number.is_empty()
            || self.safety_number.len() > 160
            || self.primary_component == [0; 16]
            || self.registry.components.len() >= 64
            || self
                .registry
                .components
                .iter()
                .any(|c| c.credentials.component_id == self.primary_component)
        {
            return Err("invalid fleet identity or component partition".into());
        }
        Ok(())
    }

    /// The transport partition is fixed across registry reloads. Remote peer
    /// permissions remain in authenticated component IPC, never in chat IPC.
    pub fn policy(&self) -> RoutingPolicy {
        let mut policy = self.registry.routing_policy();
        policy.components.push(self.primary_component);
        policy.components.sort();
        policy.bootstrap_listeners.sort();
        policy.routes.clear();
        policy
    }

    pub fn same_partition(&self, other: &Self) -> bool {
        self.safety_number == other.safety_number
            && self.primary_component == other.primary_component
            && self.policy().components == other.policy().components
            && self.policy().bootstrap_listeners == other.policy().bootstrap_listeners
    }
}
