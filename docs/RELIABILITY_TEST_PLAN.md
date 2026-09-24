# Reliability implementation and device test matrix

The paired [GComs requirements](https://github.com/IggyGG/gcoms/blob/main/docs/RELIABILITY_RELEASE.md)
are authoritative for the 2026-09-24 reliability release. In paired development use
`../gcoms/docs/RELIABILITY_RELEASE.md`. Graph routing follows the working-network
release; it is not an additional release blocker.

| Layer | Required cases | Requirement IDs |
| --- | --- | --- |
| Shared runtime | Owner/inbox expiry, middle refresh, unrelated published churn, consecutive turnover, carrier cap | R03,R05,R06,R09,R11 |
| Scheduling | Ten simultaneous native senders/forwarders, stalled channels, saturation/release, chat during bulk | R02,R08,R11 |
| Persistence | Exact outbox ID/wire across failed writes and restart, archive failure before publication, no early ACK | R05,R06,R11 |
| UI | Immediate progress, rapid sends, autoscroll, mentions/self styling, actionable Details, invitation guidance, mobile overlays | R01,R02,R04,R07 |
| Files | Small cross-platform export, ~123 MB interrupted/resumed, 1 GiB cluster transfer with concurrent chat, independent SHA-256 | R06,R07,R08 |
| Mobile | Four cluster Android emulators; Android arm64 physical upgrade; iOS cloud foreground/lifecycle; live provider push separately | R01,R03,R04,R07,R10,R12 |
| Release | Native Linux/macOS/Windows checks, Android/iOS artifacts, profile-preserving upgrade, pinned signatures, safe rollback | R12 |

Run cluster fixtures with distinct profiles and no personal secrets. Keep actual
native UI, in-process runtime, emulator, physical-device, live push and installed
artifact results distinct. A mocked UI response is not real delivery evidence.
Use existing GComs application/turnover/fleet harnesses and GChat browser/native
tests; retain all independent failures rather than stopping at the first failure.

Only rebuild a platform when its source/packaging changes require it. The final
package pair must include the tested GComs runtime, not a similarly named older
revision. Failed and late-continuation receipts remain separate. Cluster workloads
must not compete with compilation for their reserved CPU/disk during timing checks.

## Current execution boundary

- Starting source: GComs `293680e`, GChat `d6b2947`, clean task worktrees.
- Android 1019 run `35954372544` completed with successful compilation/signing but
  a failed installed-app smoke/cleanup step. It is not a qualified update and is
  not to be promoted merely because an APK exists.
- The original personal 122,980,700-byte export already matched its source hash;
  delayed ACK/reconnect behavior remains a failure of latency, not file integrity.
- No data clear, reinstall-with-uninstall, identity replacement or automatic
  replay under a new operation ID is permitted to repair a retained profile.

Maintain current run results in source-bound evidence and keep only small decisive
summaries in Git. Complete live APNs on a provider/device preserving the required
signing; ordinary BrowserStack iOS functional checks do not establish that result.
