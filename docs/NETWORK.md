# Default network and recovery

GChat uses the public signing root and signed network defaults bundled by
`gcoms-runtime` in `crates/runtime/assets/gchat-network.json`. The `gcoms`
application facade selects these defaults unless an application supplies its own
signed configuration through `Application::builder(...).network_config(...)`.
The configuration contains no invitation credential. Both new and retained
profiles preserve monotonic network state.

The installed providers are `https://bootstrap-hel.gchat.boo/` and
`https://bootstrap-fsn.gchat.boo/`, backed by the published Hetzner relays. The
application, daemon and TUI use the same signed preset. No relay credentials are
shipped in installers. An invitation never replaces an existing network's trust
root or identity.

## One invitation for a network and a channel

Use **Invite someone** in channel details (or `/invite`) to copy a combined
`GCI1-` invitation. It includes the network's signed public configuration and relay
addresses plus access to that channel. It does not copy your personal provisioning
grant. A separately issued network grant can also be included by an operator.

The recipient uses **Join**, pastes the invitation, checks the network identity
and starting channel, and confirms. An unfamiliar network opens as a separate
network with its own identity, encrypted history and file storage. Existing
networks remain available in the channel list. A familiar name with a different
signing root is rejected; a name alone is not proof of network identity.

Joined networks are retained in the encrypted profile and reopen with the same
identities. Locking or disconnecting closes access to every joined network.
Files and commands stay bound to the network where they were started, even if
you switch channels while an operation is pending.

Legacy channel-only invitations remain usable within the selected network.
An operator's network-only invitation connects a profile but does not grant
membership of a private channel. See [channel commands](CHANNELS.md).

## Installed network provisioning

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

With the explicit `gc2-carrier` profile, both recovery paths request HTTP
provisioning envelope v3, marked `routing_protocol: "gc2"`, and import native
GCRB2 introductions. Envelope v2 is legacy GCRB1; it is not GC/2 support.
Current clients reject an older response without conversion or downgrade.
The provider must be built with GComs catalog's `experimental-gc2` feature;
adding the client feature does not upgrade an operated provider.
Signed defaults, invitation grants and normal HTTPS verification remain required
for the installed network. Retained current-protocol directory state is tried
before provider recovery and is also used when reporting invitation requirements.
If a retained profile has no invitation grant, re-entry may use the caller's
full recovery deadline. The 30-second provider-fallback interval does not erase
retained authority or turn slow reconnection into an invitation requirement.
An unavailable route still fails at the original deadline.

The source regression `bootstrap::gc2_tests::production_bootstrap_fresh_reopen_and_recovery`
runs the production profile against authenticated local TLS and four relays in a
disconnected namespace. Run its compiled all-feature `gchat_core` test binary via
`python3 scripts/test-bootstrap-namespace.py --binary <path> --output <new directory>`.
It checks fresh import, both subscription classes, retained identity/directory,
cached installed-network re-entry and retry after downgrade refusal. The separate
unavailable-route check exercises a 35-second caller deadline without an
invitation, so it exceeds the provider-fallback interval. The
GComs network-client TLS suite checks signed-default/grant provisioning.
These source checks do not qualify an installed artifact against operated providers
or establish client-observer privacy. The ordinary Rust suite leaves the namespace
case ignored, so retain its separate execution receipt.

Before launch, operators must demonstrate invitation onboarding, provider failover,
relay restart recovery, withdrawal/retry behavior, rollback, and capacity under the
intended preview population. Previous private-lab measurements do not qualify the
public extracted release. Do not publish private contact cards or credential-bearing
logs as evidence.
