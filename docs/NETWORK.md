# Default network and recovery

GChat uses the public signing root and signed network defaults bundled by
`gcoms-runtime` in `crates/runtime/assets/gchat-network.json`. The `gcoms`
application facade selects these defaults unless an application supplies its own
signed configuration through `Application::builder(...).network_config(...)`.
The configuration contains no invitation credential. Both new and retained
profiles preserve monotonic network state.

Obtain an invitation from the network operator and import it through GChat's
onboarding flow. The operator's public identity, invitation procedure, capacity,
acceptable use and status/support contact must be recorded before public launch.
Those deployment decisions are tracked in `release/publication.json`; they are not
inferred from an endpoint being reachable.

Recovery tries retained private routing state and bounded provider requests.
Use explicit network settings for a separately operated deployment. DNS registration
is opt-in; withdrawing consent must preserve and retry the removal request across
restarts. A relay restart, expired invitation and provider outage are separate cases.
Do not erase a working identity/archive as a connectivity repair.

Before launch, operators must demonstrate invitation onboarding, provider failover,
relay restart recovery, withdrawal/retry behavior, rollback, and capacity under the
intended preview population. Previous private-lab measurements do not qualify the
public extracted release. Do not publish private contact cards or credential-bearing
logs as evidence.
