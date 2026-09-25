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
| Mobile | Four cluster Android emulators; native Mac-hosted iOS simulator foreground/lifecycle; physical Android/iPhone and live provider push deferred | R01,R03,R04,R07,R10,R12 |
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

The Android emulator driver accepts `--port 5554`, `5556`, `5558` or `5560`
with separate `--output` directories for concurrent devices. Each device owns
its AVD, uses explicit serial-scoped ADB calls and refuses occupied console/ADB
ports. It uses two virtual CPUs and 2 GiB guest RAM. Reuse verified signed APKs
for harness changes; do not rebuild the app to change emulator orchestration.
The installed lifecycle smoke blocks that fixture app's external traffic and
therefore does not qualify network delivery or push. Those require separate
multi-participant fixtures and provider/device evidence.

Disposable Android setup completes the SDK image's setup wizard, keeps the
emulator awake and dismisses its unprotected swipe keyguard before launch. It
does not change GChat permissions or apply these actions to physical devices.
Its swipe lock is disabled only after verifying `ro.kernel.qemu=1`.
Keyboard observations use `dumpsys -t 1 input_method --dump-priority CRITICAL`:
[Android's service priority argument](https://android.googlesource.com/platform/frameworks/base/+/master/services/core/java/com/android/server/utils/PriorityDump.java)
selects the manager's own state. An interrupted dump is not a visibility sample;
the observer retries within the original ten-second deadline and requires two
successful, settled samples. Persistent observer failure remains a failed test.
Late observations remain failures; setup errors, system ANRs and app errors are
retained separately. Each AVD has a distinct name as well as a distinct port.

For disconnected application journeys, `crates/core/examples/turnover_daemon.rs`
hosts the real application facade and ChatService with a fixture-owned signed
network describing the six actual relays. The controller passes its exact binary
through `../gcoms/scripts/gchat-turnover.py --fixture-host PATH`. This keeps
installed trust unchanged and avoids pretending private relay seeds belong to the
installed network. Its `network` and `serve` subcommands require the controller's
declared network namespace. Profile reopen supplies neither a new identity nor
replacement bootstrap material. The helper's source, Cargo inputs and binary
hash are bound separately from the production daemon. This is core/service
qualification, not an installed desktop or provider onboarding result.

The turnover controller uses typed invitation inspection/join, preserving the
inspected network ID. Combined invitations must not be submitted as ordinary
chat text. `--mode file-recovery --file-bytes 1073741824` adds a 1 GiB transfer,
abrupt receiver termination after verified partial progress, retained piece
checks, authenticated chat after recovery and independent export hashing before
and after reopening. This mode does not substitute for credential/carrier expiry.

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

Browserless access is already configured, but browser emulation does not install
the native iOS application. Use the available Mac iOS simulator for native build,
UI and lifecycle checks. Keep physical-device and live APNs qualification open
until exercised on a compatible device; do not substitute browser results.

The user deferred physical-device testing on both Android and iPhone for now.
Continue emulator, simulator and automated qualification without waiting for a
physical device. Physical-device upgrades, battery behavior and live APNs/FCM
delivery remain unverified; this deferral does not qualify them. Actual network
message/file delivery remains a separate required automated journey. The simulator
builder verifies Xcode 26.2 and requires its selected iPhoneSimulator platform;
the installation directory may be named `Xcode.app`. It does not use a device
signer or provisioning account. Retain native XCTest screenshots and distinguish
profile/Keychain lifecycle checks from actual network messaging and live push.

## Incoming archive transaction candidate

The disconnected archive-failure case reproduced publication and authenticated
delivery of a message which disappeared after abrupt receiver restart. The
candidate opts GChat's embedded runtime into a bounded sealed channel inbox
before receiving starts. The inbox commits plaintext with receive/ACK state;
GChat saves its archive before consuming that inbox record and publishing the
message. Channel and channel-private messages use the same ownership rule;
file pieces retain their separate journal. Failed archive writes leave the
record available across reopening, rather than exposing an unsaved RAM update.

The protocol checkpoint wrapper is `GCNSTM`. Older binaries cannot read that
wrapper: a release must include a state-compatible rollback binary. Restoring an
old profile backup after newer messages were acknowledged is not safe rollback.
External legacy IPC archive consumers are not covered by this opt-in embedded
transaction. Component checks, actual abrupt-restart checks and installed
upgrade checks remain separately bound; a source implementation is not a pass.
