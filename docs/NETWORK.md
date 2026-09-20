# Default network and recovery

`crates/core/assets/gchat-network.json` contains GChat's installed public signing
root and signed network defaults. It contains no invitation credential. Generic
GComs libraries have no built-in operated network. Both new and retained profiles
use the application's selected trust document and preserve monotonic network state.

The installed providers are `https://bootstrap-hel.gchat.boo/` and
`https://bootstrap-fsn.gchat.boo/`, backed by the published Hetzner relays. The
application, daemon and TUI use the same signed preset. No relay credentials are
shipped in installers, and importing an invitation does not replace the trust root.

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

The source regression `bootstrap::gc2_tests::production_bootstrap_fresh_reopen_and_recovery`
runs the production profile against authenticated local TLS and four relays in a
disconnected namespace. Run its compiled all-feature `gchat_core` test binary via
`python3 scripts/test-bootstrap-namespace.py --binary <path> --output <new directory>`.
It checks fresh import, both subscription classes, retained identity/directory,
cached installed-network re-entry and retry after downgrade refusal. The separate
GComs network-client TLS suite checks signed-default/grant provisioning.
These source checks do not qualify an installed artifact against operated providers
or establish client-observer privacy. The ordinary Rust suite leaves the namespace
case ignored, so retain its separate execution receipt.

Before launch, operators must demonstrate invitation onboarding, provider failover,
relay restart recovery, withdrawal/retry behavior, rollback, and capacity under the
intended preview population. Previous private-lab measurements do not qualify the
public extracted release. Do not publish private contact cards or credential-bearing
logs as evidence.
