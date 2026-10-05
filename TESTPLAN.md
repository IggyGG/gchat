Selected-flight admission regression, 2026-10-05: reproduce queued and storage-recovery admission against old building/verifying rows. Require the selected release's original build to start, a newer pending release to remain queued, and the old expired request to reconcile with its unchanged request ID and reconciliation-only flag. Non-single-flight admission must retain existing coalescing. All 85 coordinator, flight and minutes controls pass, including bounded background-worker checks; L0 checks 837 paths. Qualify the actual controller image before activation. See [retained evidence](docs/evidence/relay-capacity-20261005/flight-admission.json).

Windows portability regression, 2026-10-05: 90 focused controls pass across `node_image_headroom_test`, `relay_load_run_test`, `release_control_test`, `release_coordinator_test` and `release_minutes_test`; the final dependency-import recheck passes all seven controls. L0 checks 836 source paths. Cover import without fcntl/statvfs, Windows child termination and forced kill with log closure, absolute/root-relative/drive/UNC/traversal evidence paths, and canonical temporary directories. [Retained evidence](docs/evidence/relay-capacity-20261005/windows-portability.json) binds the original Windows failure, source files and local logs. The normal native Windows workflow remains required before claiming Windows qualification.

External hotfix handoff, 2026-10-05: run `release_deployment_test.py`, `release_control_test.py` and `release_host_install_test.py`. Require exact journal and running-artifact hashes, healthy fresh observations, coverage of every pending rollback, durable prior failure retention, crash recovery, and no service mutation or qualification during handoff. Cover a hotfix already recorded as previous by reconciliation, with the older host rollback still unresolved. A handed-off rollout must never reactivate. Managed replacement must preserve the hotfix binary and exact override as rollback, then pass the ordinary canary gates.

Parallel release qualification, 2026-10-05: Linux runs independent GChat, GComs and isolated relay-load jobs for one frozen source pair. Signing requires both native gates; deployment also requires the original 64-client load evidence. Late build results reconcile their original request after the build deadline, and publication has a separate persistent budget after infrastructure is ready. Failed load gates retain evidence and cannot prevent a newer candidate from starting. Implementation is under qualification; this entry does not claim fleet activation.

Release operations repaired, 2026-10-05: controller `7c0db5c` is active after 254 actual-image checks and verification of 239 source files in Kubernetes. Store observation now reuses its pending request and closes finished worker logs; open descriptors fell from 1,022 to 8. The retained Android 1113 observation completed as available. Relay capacity and desktop sharing still require their load and live-delivery gates. See [activation evidence](docs/evidence/relay-capacity-20261005/controller-activated.json).

Disconnected load setup uses the existing single-use SDK invitation API through an owner-only fixture endpoint. It does not qualify reusable HTTPS-provider invitations. Unexpected invitation response shapes fail immediately instead of consuming the setup deadline. The first 64-client attempt was stopped before traffic because the driver used the obsolete bare `/invite` behavior; its evidence is retained.

Relay capacity qualification, 2026-10-05: run GComs transport possession-proof and catalog relay-registration integration tests, forwarding/admission/backoff tests, routing bandwidth tests and runtime sharing persistence tests. Validate paired GChat sources with strict Clippy, core tests and the real turnover host. Run `gcoms/scripts/gchat-turnover.py --build BUILD --out NEW_EVIDENCE --mode relay-load --fixture-host BUILD/bin/turnover_daemon` for the blocking 64-client 30-minute test. Require <1% refusals, recipient p95 <5s, a verified 5,235,248-byte file, successful restart and no wedges. Keep failed attempts and separately prove actual desktop publication, provider withdrawal and delivery through the live fleet.

Node headroom recovery, 2026-10-04: run `python3 -m unittest discover -s scripts/tests -p node_image_headroom_test.py -v`. Six controls cover healthy nodes, sufficient runtime cleanup, missing Docker, the separate Docker store, cleanup failures and insufficient reclaimed space. Require actual free space above 17%, DiskPressure=False, the original anchor identity PVC, enabled timers with successful scheduled runs, and fresh health/version observations for all 17 infrastructure targets. See [live evidence](docs/evidence/stabilization-20261001/node5-recovery-20261004.json).

Release status, 2026-10-04: Linux 0.1.98 and all 17 infrastructure targets are active and healthy. Linux, Windows, both Mac architectures and SDK archives are published. Controller c66c230 runs the production-minutes-v1 publication path in Kubernetes. Original Android and iOS artifacts passed its publication gates. Android 1113 is uploaded, committed to Google Play and processing; iOS 1.1.13 awaits Apple encryption approval, including France. Full GUI qualification and SDK 1.0 remain separate and incomplete. Mobile publication and Apple encryption approval remain separate from full GUI qualification and SDK 1.0; original failed reports are retained.

Routine releases: push `main`; the source mirror and Kubernetes coordinator build, verify, deploy and publish. The local package timer installs signed desktop updates. Inspect with `python3 scripts/release.py status`; use `resume --platform <platform>` for a retained failed stage and `rollback` for recorded infrastructure. See [automatic releases](docs/AUTOMATIC_RELEASES.md) and [current evidence](docs/evidence/stabilization-20261001/launch-simplification.json).

Routine publication now verifies the native build, signatures, permissions, startup lifecycle and eight fresh matching relays. Full mobile GUI upgrade/rollback/history/file journeys run separately with `python3 scripts/release.py qualify --platform android` or `ios`; they do not gate routine upload and never become passes from a build or upload. Routine work has a persistent 60-minute active budget, one transient retry and one-minute source settlement; external review pauses its budget. Native dependencies and compiler outputs are cached, while signed artifacts and every source binding are verified.

## Retained earlier checkpoints

Native fixture simplification, 2026-10-04: retained Android da7073b passes initial enrollment/export and both upgrade and baseline rollback phases with unchanged identity/history/encrypted cache and authenticated acknowledgments, then exhausts the original compatibility deadline during final-restoration history observation. Fresh hierarchy removal, capture and read now share one ADB round trip. Each replacement checks authenticated messages before its OS export; an immediate next replacement performs only its required unlock, while subsequent messaging still reconnects normally. Android partial-transfer observation now requires an exact rendered filename, its adjacent transfer status, exact total and bounded verified counter. iOS empty-prefix handling accepts its actual accessibility placeholder without admitting existing input. All 71 focused controls pass in 2.956 seconds; native qualification is still required and all original deadlines and failed reports remain retained.



The active mobile helper da7073b passed 874 independent CI controls with five existing skips, plus 70 focused controls. It uses the corrected Android app-data cache path, normal system export and exact rendered acknowledgments; iOS narrows exact row queries and reconciles zero-character local input once within the original deadlines. Both actual native runs retain the original signed apps. Controller 7f423f8, all eight node headroom timers and both local release timers remain active. The running Linux executable still matches installed 0.1.98 byte for byte.



Release status, 2026-10-04: all 17 infrastructure targets are healthy and match the release. Linux, Windows, both Mac architectures and SDK 0.1.98 are published. Linux 0.1.98 is installed and its running production-profile executable matches it. Android and iOS installed acceptance, iOS OS invitation arrival, SDK 1.0 and the subsequent unattended release remain open. Apple encryption approval remains IN_REVIEW, including France.

Routine releases use the existing source mirror and Kubernetes coordinator: push main, then inspect with `python3 scripts/release.py status`. Controller 7f423f8 handles bounded temporary GitHub outage recovery. All eight node headroom timers are enabled and their scheduled checks pass. Failed reports, original provider requests and signed application bytes remain retained.

Native follow-up, 2026-10-04: Android 80d68e5 passes exact rendering, authenticated messages and the normal OS export with the original hash. Its encrypted-cache check searched filesDir, but the pinned Tauri Android resolver uses activity.dataDir; the fixture now checks the owned app instance beneath dataDir and still requires one exact encrypted piece. iOS 96d51b6 passes setup but the first keyboard batch enters zero characters. Input now waits for the actual keyboard and permits one local retry only when the complete previous prefix remains unchanged; partial or different values fail. Original command and journey deadlines, failed reports and signed applications remain retained. All 70 focused controls pass in 3.052 seconds; complete native results remain required.



The retained Android cecddf7 run passes exact rendered messages, authenticated acknowledgments in both directions and exact export filename confirmation. It then fails because the system picker has no Show roots control. The helper now accepts the normal Downloads screen directly or opens it through Show roots, using only the two owned DocumentsUI packages and exact Save labels; export hashes remain mandatory. iOS d3a64e5 is independently qualified and running against the original signed apps. Remaining dynamic WebView row queries now bind accessibility elements rather than unstable indices. All 69 focused controls pass in 2.936 seconds; L0 checks 825 paths and API 2/3 contracts remain unchanged. Native results are still required.

Retained iOS d3a64e5 passes visible enrollment, exact identity, initial covered messages, system export, upgrade and baseline rollback with unchanged identity/history/encrypted cache and authenticated acknowledgments. Its final restoration cannot start within the original 600-second compatibility budget. Exact label ancestor queries now narrow file and message row candidates before the existing uniqueness/status checks, removing repeated whole-tree scans without extending any deadline. The failed report remains retained; complete installed qualification is still required.



Release status, 2026-10-03: all 17 infrastructure targets are healthy and match the release. Linux, Windows, both Mac architectures and SDK 0.1.98 are published. Android and iOS installed acceptance remain incomplete; Apple encryption approval is IN_REVIEW, including France. Linux 0.1.98 is installed and the running production-profile executable matches it.

All eight node headroom timers are enabled and scheduled checks pass. Controller 7f423f8 is active after 854 source controls, 214 actual-image controls, 365 Kubernetes controls and verification of 237 source files. Temporary GitHub 502/503/504 errors now use bounded automatic reconciliation of the original request. Both mobile acceptance requests use the qualified same-source helper, with Android focus confirmation and separate iOS visible join stages under unchanged limits. All 17 deployment targets pass a fresh health/version check. Original failures, signed app bytes, API contracts and security checks remain unchanged; mobile launch and OS invitation arrival remain incomplete.

Mobile worker correction (2026-10-04): the retained 7f423f8 Android report proves that keyboard capitalization changed the nickname while focus and its length were correct. The fixture now enters uppercase MOBILE and keeps exact input confirmation. The retained iOS report failed during initial simulator installation before XCTest. Installation now reconciles the actual retained executable after a client timeout and permits one idempotent retry inside the original 120-second operation and 600-second setup budget. Changed binaries, ordinary command errors and exhausted deadlines still fail. All 53 focused mobile controls pass; new native acceptance is required. Original failures, application bytes and APIs remain unchanged.

Mobile observation correction (2026-10-04): helper 0b03781 passes 857 source controls. Its Android run passes OS invitation enrollment, exact nickname entry, identity observation and authenticated recipient delivery, then fails exact pixel recognition. Its iOS run reconciles one stalled install inside 120 seconds, verifies the retained executable, then exposes dropped simulated keyboard characters. Workers now use readable random word canaries with at least 70 bits of body entropy, exact adjacent wrapped-line recognition and message-bound delivery status; iOS uses normal local-only Paste with exact value confirmation and immediate clipboard clearing. Native acceptance remains required. The failed reports and original signed apps are retained.

Owned simulator input correction (2026-10-04): retained helper c8477ae passes 858 source controls, but its iOS system Paste menu never appeared and Android remained on an invitation form before preview. iOS now copies input through simctl to the already bound fresh simulator, reads it back exactly, invokes normal Paste, and clears it after every command including failures; input never enters a shell argument or the host clipboard. Android permits the expected populated form only when its value matches the reserved invitation exactly; different or ambiguous fields remain refused. All 57 focused controls pass. Native acceptance is still required, with original deadlines and signed apps unchanged.

Native follow-up (2026-10-04): retained helper c9d75af passes 861 source controls. Android now passes exact incoming rendering and its authenticated ACK; its exact outgoing message reaches the peer, then the rendered sender receipt observation times out. iOS reaches the retained executable hash check but fails the original install deadline before XCTest. The corrected worker reserves lookup/hash time inside the same 120-second install operation. Android alternates sparse and block OCR within the original observation limits and accounts for the smaller receipt font on an adjacent line, while rejecting storage/local acceptance and unrelated status. All 59 focused controls pass; native acceptance remains required.

Mobile follow-up (2026-10-04): qualified helper d511b97 passes 863 source controls. Android passes OS invitation enrollment, identity, exact rendered messages and authenticated ACKs in both directions, then downloads the baseline cache; export fails because input focus was restricted to GChat rather than the normal system DocumentsUI picker. The helper now permits that picker explicitly and still requires the exact focused filename. iOS again fails initial simulator installation before XCTest. Initial setup installation may use up to 240 seconds inside the existing 600-second setup budget, reserving at least 120 seconds for runner readiness; actual upgrade/rollback installs keep 120 seconds and all executable hashes remain mandatory. All 62 focused controls pass in 2.135 seconds. Installed acceptance remains incomplete; original failures and signed applications are retained.

The exact f30bac0 helper passes 866 source controls with five existing skips in 36.003 seconds; both original mobile stages are resumed with frozen provider requests. Local activation readback proves the running production-profile executable matches installed 0.1.98; the deleted executable belongs to a separate older test profile. See operations/native-helper-f30bac0-qualified-810.json and operations/local-active-readback-814.json. Mobile acceptance remains pending.

The iOS export command can invoke normal reconnect/unlock after the OS picker. It now stages the exact fixture passphrase in the owned simulator clipboard for that command and clears it on either outcome, preserving exact field confirmation. All 63 focused controls pass; this correction still requires native qualification.

Retained helper f30bac0 verifies iOS baseline installation under the existing setup budget, then fails because the system Paste menu is absent. Android passes the incoming rendered message and authenticated ACK and receives its exact outgoing message at the peer; its OCR recognizes a delivered line but cannot match the complete outgoing body. The worker now selects the existing Readable font through normal Android UI and uses normal iOS keyboard input in eight-character chunks, requiring every exact prefix before continuing. Normal password visibility controls permit exact confirmation; clipboard staging and the missing Paste menu are removed. All 62 focused controls pass. Native acceptance remains required, and the failed reports remain retained.

Android helper 2b96f76 selects the normal Readable font and passes incoming exact rendering/authenticated ACK plus exact outgoing input/peer reception, but full outgoing visual matching still fails. OCR currently uses block identifiers as rows, which can split one visual line into many blocks. The correction groups only vertically overlapping words into physical rows while retaining exact full-body and bound-delivered checks. Diagnostic word counts cannot qualify delivery and contain no message text. All 64 focused controls pass. iOS 2b96f76 remains running under its frozen request; no duplicate request is sent.

Retained iOS helper 2b96f76 passes exact passphrase creation and confirmation and all visible join stages. It fails reading identity when a changing accessibility snapshot invalidates an index-bound element. The correction queries the exact identity and safety-number static texts, binds results by accessibility identity, and requires the foreground WebView. Diagnostic field counts contain no identity values. All 64 focused controls pass; actual installed acceptance remains required. Android is resumed separately with the CI-qualified visual-row helper cdc70f5 (868 source controls); its original request remains frozen.

Retained Android cdc70f5 recognizes all 11 expected body words and the delivered status, but cannot assemble a complete adjacent body span. Short lowercase glyphs measure x-height rather than the full CSS line box. The corrected body-row leading allowance matches the existing smaller-font receipt allowance, retaining exact whole-body and receipt binding. Focused checks cover short adjacent lines, distant rows, modified words and unrelated receipts; all 64 controls pass. The flat-row match remains a diagnostic only. iOS is resumed separately on CI-qualified f696b22 (868 source controls); its original request remains frozen. Native acceptance is incomplete.

The latest iOS f696b22 run failed during initial installation before XCTest; its new identity observer was not exercised. The installer now issues one request and polls the actual container/executable hash inside the same deadline, avoiding overlapping installs when registration is delayed. Initial installation remains at most 240 seconds within setup 600; upgrade/rollback remain 120 seconds. Wrong binaries, ordinary command failures and exhausted deadlines still fail. All 65 focused mobile controls pass in 2.159 seconds; API contracts and application bytes are unchanged. Android is running its separately qualified ad8a119 helper (868 CI controls, five existing skips, 30.797 seconds). Installed mobile acceptance remains incomplete.

Native follow-up: a2b7e97 passes 869 CI controls with five existing skips in 34.167 seconds and is active for the running iOS request. Android ad8a119 still fails the outgoing exact visual-body check: all expected word tokens and a delivered line are observed, but the complete ordered body is absent even without row-gap limits. Numeric word positions and row geometry now diagnose ordering without retaining screen text, bodies or screenshots; counts remain insufficient for qualification. All 65 focused controls pass in 2.160 seconds. Original applications and failures remain unchanged; installed mobile acceptance remains incomplete.

Native setup/observation simplification: iOS a2b7e97 now verifies the unchanged baseline with one install, but compilation/test startup exhausts its existing setup budget before any UI command. Only the test fixture is now compiled alongside independent simulator boot and installation; test execution requires both success and the retained app hash, within the same 600 seconds. Android numeric diagnostics show exact word positions interrupted by extra rows. Floating controls occupy the transcript rectangle; their actual owned accessibility button rectangles now exclude covered pixels from OCR. This is a geometry correction, not permission to ignore arbitrary text or accept partial bodies; hidden body words and unrelated delivery still fail. All 67 focused controls pass; native qualification remains required. Original negative reports and signed applications remain retained.

Android c777296 now passes both exact rendered messages and authenticated bidirectional ACKs; actual overlay exclusion removes four button regions. Its baseline file is downloaded, but native export retains one character of the default filename because deletion preceded keyboard/focus readiness. The correction clears only the actual system filename after confirmed focus and IME readiness and observes its empty value before entering the exact new name. Unknown providers, ambiguous fields, changed names and wrong export hashes still fail. All 68 focused controls pass. The c777296 helper is CI-qualified (871 controls, five existing skips, 34.007 seconds); its original iOS provider remains running and is not duplicated. Mobile installed qualification remains incomplete.

Retained iOS c777296 now passes overlapping fixture compilation, exact original baseline installation, owned simulator binding, XCTest readiness and both passphrase fields. It times out at the unchanged 120-second invitation command while native input uses eight-character batches for the long URL. Only invitation input now uses 64-character batches; exact prefixes and the complete final value remain mandatory. Passphrases retain eight-character batches. Public numeric progress reports total and last confirmed length without URL text. All 68 focused controls pass; native acceptance remains required. Android runs independently on CI-qualified cecddf7 (872 controls, five existing skips, 32.497 seconds). No duplicate running request is sent.

The current launch status above supersedes older pending/deployed statements. Original negative outcomes and evidence pointers remain below.

Mobile follow-up (2026-10-03): native helper 8eced78 passed all 809 CI controls in 36.064 seconds. The actual iOS current and baseline archives/executables/signing checks passed; its XCTest bridge did not start before its original deadline. Its helper now reports only static compiler locations, numeric transport/HTTP codes and configuration/exit categories, and notices a dead runner immediately. Android reached its first password input, then lost the app before confirmation: text input now waits for the actual IME and exact focused value before Back, using the existing native smoke helper. No production app is rebuilt or resigned. Both original failures are retained; actual installed acceptance remains required.

Current launch (2026-10-03): all 17 infrastructure targets are deployed and healthy. Linux, Windows, both Mac architectures and SDK 0.1.98 are published. Controller 2b2478e is active with both containers ready, no restarts, 171 actual-image checks and 319 cold-pull Kubernetes checks. The automatic source gate passed 808 tests with five existing skips in 36.462 seconds. Android and iOS installed acceptance remain incomplete after explicit native worker failures; their reports are retained. Apple encryption approval remains IN_REVIEW, including France. Linux 0.1.98 is installed and selected on a fresh launcher start; the open desktop still uses its previous executable. Full launch remains open on the mobile gates and external store availability.

Full Python, source-audit and retained-contract gates now run automatically in the existing Stable contracts CI job on a clean Ubuntu worker with full Git history and the controller's pinned dependencies. The original failed workstation run is retained; its scheduler fixture is corrected. Original store lanes reconcile before background artifact work after the active release. Native helper 9970807 passed the independent automatic source gate (809 tests, five existing skips, 37.610 seconds). Its actual installed runs exposed two further adapter issues: the iOS evidence projection omits the complete simulator, which remains in its original hash-bound nested archive; Android reached Create identity but failed before its first password input. The corrected helper recovers the reviewed original ZIP, verifies its original build bytes, and captures/uploads Android startup pixels only before any input. The corrected input adapter passes against both actual cached iOS builds, including every simulator archive, authority, executable, identity and lifecycle reference (operations/actual-ios-original-adapter-658.json). All 16 focused mobile controls pass; L0 checks 820 paths and API 2/3 contracts remain unchanged. Native acceptance remains required. Retained metadata correction: authenticated retained iOS metadata may omit provider download expiry; exact source, run, hash, signing and lifecycle checks remain required. Android verifies actual launch status and retains a startup image only on its fresh owned AVD before any input or invitation. Controller qualification is separate from the immutable native helper binding. Active mobile launch corrections: baseline rotation requires an unchanged source-bound installed acceptance receipt; older publications remain available but cannot displace the configured qualified seed. Android startup records only fixed control counts and error types. Native acceptance and compatibility finish before store serialization. A separate iOS prerequisite worker reads Apple encryption status without uploading or submitting, so a qualified pending approval can release the global flight while the original store lane continues reconciliation. Tests cover missing legacy receipts, current acceptance effect pointers, changed evidence/sources and failed verdicts; native checks before serialized store submission; no upload even when prerequisite observation sees APPROVED; and fixed diagnostics without private hierarchy text.

Combined source gate passes 801 Python tests with five existing skips (223.575 seconds), L0 checks 820 source paths, and API 2/3 contracts are unchanged. The corrected image still needs qualification and activation; Linux, SDK and Apple Silicon Mac 0.1.98 are available.

The remaining launch corrections cover both original iOS lifecycle report shapes, changed/skipped native evidence and substituted startup receipts, a chain of separately frozen failed helper dispatches, Android accessibility scrolling, and source/evidence/France/age-bound external encryption waiting. Run the full Python suite and L0 before qualifying the corrected image. Apple Silicon Mac 0.1.98 has passed actual installed acceptance and is published.

Controller activation (2026-10-03): the actual b7c0d02 image passes 283 cold-pull Kubernetes controls with 233 source hashes verified. Both live containers are ready with zero restarts. The previous controller image is retained and registry readback verified. Original candidate acceptance is resumed on Android, Windows and both Mac targets; iOS uses one exact failed-verification follow-up. The Apple encryption declaration remains IN_REVIEW, including France. This is not a whole-launch completion claim.

Final source validation for the retained handoff correction passes 793 Python tests with five existing skips (172.304 seconds). L0 checks 820 source paths; 18 stable/three optional methods and API 2 fixtures are unchanged. The original signed applications and original provider failures remain retained. The qualified controller is now active; actual installed-client acceptance and store availability remain separate gates.

Retained handoff controls exercise the exact registered Mac/iOS build report through provider selection and encrypted archive metadata, reject changed provider bytes and foreign workflows/requests, preserve the original failed iOS build, and check every retained lifecycle gate reference. The real Intel Mac provider adapter passes against its existing signed archive (operations/actual-mac-handoff-545.json). Cover exact frozen lifecycle qualification refs, one registered iOS upload, and one verification follow-up after a confirmed failure; unknown/successful/changed predecessors and altered retained evidence must refuse dispatch. Run the full Python suite and L0 before qualifying the controller image.

Checkpoint run 542 passes 787 Python tests with five existing skips in 32.664 seconds. L0 checks 820 source paths; contracts retain 18 stable/three optional methods and unchanged API 2 fixtures. Mobile setup controls exercise the shared Android disposable-device setup with optional packages present or absent, refuse physical/other/preinstalled devices, and verify diagnostic locations exclude private exception messages and profile paths. The original actual emulator setup failure remains retained; a corrected native acceptance run is still required.

Active worker priority: a slow older reconciliation must leave capacity for a resumed active release, in both artifact and acceptance pools, including a one-worker limit. An inactive flight may reconcile a reserved request but cannot issue fresh authority or create a follow-up from its retained failure. Preserve original marker and failure bytes. Focused run 531 passes 293 release tests with four existing skips. The reviewed host installer and production Kubernetes manifest alter qualification/infrastructure fingerprints without reserving application bytes; unknown build and signing inputs stay conservative.

Native acceptance recovery must retain terminal provider failures even when no report was uploaded. Cover one derived frozen follow-up, unchanged signed application inputs, original authority cleanup, source/inventory tampering refusal, and no retry for missing success, expired or ambiguous reports or a truncated provider inventory. Focused run 514 passes all 31 acceptance controls; full run 516 passes 781 tests with five existing skips in 30.501 seconds. Keep provider branch rejection annotations and original failed runs separate from the corrected results.

The asynchronous coordinator fixtures explicitly use zero storage reserve in their owned, bounded scratch directory so they can run in the actual controller image's 256 MiB test tmpfs. Production retains its 16 GiB reserve and storage refusal controls. The original failed image gate is retained; corrected image qualification is required.

## Simplified release controls (2026-10-03)

Full run 502 passes 778 tests with five existing skips. Ten iOS recovery controls retain the strict original registered recovery and cover queued lifecycle waiting, one same-IPA verification dispatch with upload disabled, lost reply reconciliation without resubmission, and rejection of changed sources/helpers, failed lifecycle providers and unbound/expired archives. No compiled application is substituted.

Actual final rollout passes all 17 targets and the final full canary. Registry recovery 504 matches the stopped-writer source tree d4c5cd980ee3b72ada929a814c08b3d3d3e3627c2f8662d5cc43c27708ba455c against the completed copy (926 files, 3,898,893,202 bytes), requires the original Job's positive completion and matching immutable helper, activates the two-replica volume away from node 5, and reads back six exact image manifests and all bound blob sizes. Preserve the earlier 900-second wrapper timeout and automatic original Deployment restore; do not relabel that attempt as a pass.

Full run 485 passes 773 tests with five existing skips. Seven Mac recovery controls preserve the failed original, wait without resubmitting while its follow-up is queued, and reject other candidates/sources, duplicate registrations, changed workflows/repositories, cancelled or failed providers, expired/unbound archives and changed extracted bytes/links. The independent verifier rechecks the complete package ZIP, original native reports, same-input qualification and exact frozen signing/packaging helper before existing signature/updater and installed-smoke checks. Other platforms keep their existing verification path.

Five registry copy controls require a stopped writer, nonoverlapping real paths, unchanged source, exact destination byte/mode equality and safe repeatability. Links and extra destination files refuse a successful receipt; original files are never removed. Actual migration must retain the original Deployment/PVC, observe both healthy replicas, stop the sole registry writer, run the qualified copy, switch with a resource-version guard, then check readiness and original manifest digests. A copy/switch failure restores the original Deployment.

Full run 461 passes 761 Python tests in 30.420 seconds with five existing skips. Mac native reuse tests reject compiler/platform changes, unknown source inputs, workflow changes, cancelled providers and extracted-archive tampering; compare executable modes as well as bytes. The optional reuse path preserves the original failed native report and requires the original positive GChat paired-source receipt. The real retained original/provider archives pass the same validator (operations/mac-native-reuse-verification-458/actual-native-reuse.json). This source-only check does not qualify a packaged installer: actual signing, notarization, installed smoke and independent archive verification remain mandatory. Full controls also preserve strict default behavior when no reuse input is supplied.

The d80c44d actual Kubernetes gate passes 239 controls with 227 source hashes. All three anchors pass covered messaging after a successful corrected DNS pull probe. SDK 0.1.98 availability verifies its own immutable index and all public archive bytes while 0.1.102 remains latest. Retain the original failed pull Jobs and catalog missing-manifest evidence; require a verified rollback image before replacing the healthy catalog.

SDK resume must publish and independently read the older candidate's immutable index and archive while preserving a newer latest index byte for byte. Reject source relabelling under an existing immutable index and same-version source collisions. Publishers share a filesystem lock. Full run 447 passes 758 tests with five existing skips; the expanded reviewed-input fixture also checks inventory and SDK orchestration changes without relaxing unknown/native/build inputs.

Pull probes must retain Always image pulls, no API credentials, explicit namespace DNS and stable identities across recovery. Corrected DNS must produce a different Job identity from the original rejected probe. Invalid or excessive DNS addresses must fail before creating a Job. Full run 441 passes 756 tests with five existing skips. Retain the four actual ghost-bench admission failures; require a successful actual probe before replacing an anchor.

Installed iOS lifecycle must reach its native boundary without CLI globals, with explicit startup verification both enabled and disabled; failure cleanup and the original report must remain intact. Full run 437 passes 754 tests with five existing skips. The original provider run 37065253240 remains failed; its 95,573,668-byte archive has SHA-256 251925d0cdc2b2cc19d176e6090a36f69ccf8b0ea933c509a98ed000ba226f67. A separate actual lifecycle and retained signed-IPA verification must pass before client acceptance.

Run `python3 -m unittest discover -s scripts/tests -p "*_test.py"` with a short SSD TMPDIR; full run 421 passes 753 tests with five existing skips. Require source-bound deployment step receipts, one owned child process with an explicit deadline, fresh coordinator status during a sleeping canary, and separate limits of three artifact workers and six acceptance workers. The deployment child must not open the ledger. A blocked active flight must hold both build admission and deployment selection. Busy rollback requests stay queued. Public status exposes stage/deadline progress without private paths.

SDK reuse controls require completed successful original provider matrices, matching repository/workflow/source, every expected archive and original hash/size. Missing variants and cancelled providers cannot qualify a cache hit. Completed desktop qualification may be reused while mobile variants continue. Changes to toolchains, workflows, tests, policy or unknown files invalidate the input key; only individually reviewed status/prose files are excluded. Reuse receipts preserve original source labels through publication.

Short messaging checks require covered ACKs in both directions and complete cleanup; full rollout boundaries still require interrupted-file recovery. Actual first full canary 403 passed six authenticated ACKs, 16 MiB hash/reopen/export and retained-piece recovery in 122.686 seconds (240.031 seconds overall). All eight native relays subsequently passed their messaging checks. The live e43654f image passed 232 actual Kubernetes controls and 227 source hashes. Require admission controls to hold fresh acceptance and expired revalidation for other flights, reconcile original dispatched acceptance IDs, and poll the active release first. Those three new controls still need their own exact-source image gate. Retain earlier IPC and worker-entry failures, original partial/cancelled SDK archives and the failed Intel native fixture. The isolated unchanged fixture passes on Apple Silicon; that result does not qualify the Intel installer.

The original Windows and Apple Silicon 0.1.98 archives now pass independent
verification of signatures, frozen source inputs, native CI receipts and installed
offline lifecycle/cleanup. The original Windows archive has 58,003,839 bytes; the
Mac archive has 71,818,229 bytes. Their provider hashes match. The shared release
policy records three existing explicit 64-member capacity exclusions and retains
the separate mandatory stress.mls64 gate. Twenty-two policy controls in each repo
reject unreviewed and cross-project exclusions and a missing capacity receipt.
The original failed independent check is retained. Installed-network acceptance
and the remaining native platforms still have to pass; no API changed.

The native network and rollback fixtures now select the existing one-person
invitation policy once, then wait for saved enrollment and the active channel
projection. The earlier canary repeatedly opened the invitation chooser, so it
never obtained a link and timed out after both clients connected. Its failure,
grant revocation, profile cleanup and automatic rollback remain retained. The
corrected fixture preserves API 2, existing authority and the original delivery,
file and total deadlines. All 19 focused network/rollback controls and 702
Python tests pass with five existing skips. Installed-network qualification
remains open.

The qualified maintenance image passes 141 actual-image/Kubernetes tests and
219 source hashes. Its real hourly compaction recipe verifies 23 SDK publications,
shares 120 identical public copies and recovers 8,409,079,808 bytes. All archive
paths and bytes remain; private provider originals stay separate. Available
release storage rises to 21,635,923,968 bytes, above the 16 GiB reserve. The
independent watchdog and main controller remain unchanged. Kubernetes recovers
the transient registry eviction without deleting data or changing disk limits.

The controller's installed-network canary can now reach the eight approved
native relay addresses on TCP 4433. Its earlier egress policy allowed public
443/22 and blocked the actual relay port; probes timed out. The corrected policy
adds only the eight relay /32 addresses and preserves the existing rules. All
eight connection probes pass from the actual controller. The failed journey,
grant revocation, profile cleanup and automatic rollback remain retained. The
normal inventory revision resumes the original rollout; covered messaging/file
and recovery acceptance still have to pass. No application API changed.

Completed public SDK archives now have source-bound duplicate compaction.
It verifies the original build and publication receipts, every selected archive
hash and stable provenance before sharing public copies with identical ownership
and permissions. Private provider originals remain separate. Every URL, byte,
mode and receipt is retained. Bounded maintenance visits recent publications;
tampering, path escapes, symlinks, FIFOs and replacement races fail closed.
The live scan estimates 8,409,079,808 duplicate bytes across 23 publications;
actual reclamation remains pending the qualified maintenance image. All 21
compaction tests and 696 full Python checks pass with five existing skips.

The corrected host installer is installed on all eight native hosts, preserving
service policies and restricted SSH keys. The original qualified binary starts
as gc-relay after the normal inventory correction. Its following network canary
times out before the first client connects; the grant is revoked and the relay
is rolled back. The original failure and correction remain retained, and all
17 targets remain healthy. Fleet/client activation is still required.

The original signed Linux 0.1.98 workflow passes both full native CI gates,
signed packaging, actual infrastructure image tests and packaged desktop/CLI
profile lifecycle and cleanup. Its complete 875,492,915-byte provider ZIP verifies
independently against the original provider digest; the unchanged release handler
checks GPG/updater signatures, source inputs and lifecycle receipts. All 12
infrastructure file hashes and 125 actual-image tests verify. The automatic
rollout reaches relay 1, rejects activation and restores the previous binary;
all 17 targets remain healthy. Installed-network acceptance is still required.

The host installer fixes that activation failure: its private umask had created
binary directories with mode 0700, denying traversal to the service's gc-relay
user. Preparation now repairs those executable directories to 0755 while keeping
installer state private; symlinked binary directories fail closed. Seven host
installer tests and 687 full Python checks pass with five existing skips. The
corrected helper is now installed on the eight native hosts; the original
rollout resumes after its normal inventory correction. No application API or
protocol changed.

Controller generation 59 (`3792ae8`) is active with two ready containers, zero
restarts, 130 actual-image/Kubernetes runtime checks and 219 verified source
hashes. Storage recovery, recent-candidate polling and unique worker logs are
active. Linux/Windows portability passes with independently verified original
provider archives; the previous controller and five private baselines are
verified. The independent watchdog succeeds. The scheduled hourly maintenance
run passes automatically on the controller's node, verifying three native
artifacts and 17 retained images with every original archive and path preserved.
All 685 Python
tests pass with five existing skips; L0 checks 802 paths, 18 stable/three optional
methods remain, and API 2 fixtures are unchanged.

The retained original iOS simulator app passes actual cold launch, relaunch
and its native profile/background/reopen XCTest on the available Apple Silicon
Mac with Xcode 26.2. Its executable is unchanged and is neither rebuilt nor
re-signed. Both original 15-second liveness checks pass, followed by one native
XCTest with no failures or skips (98.556 seconds); owned-device cleanup passes.
The original failed provider verdict remains retained. Native messaging,
fleet/client activation and a subsequent unattended release remain required.

Android build 1115 passes its original provider run automatically; the prior
1113 result remains retained. Independent verification checks the complete
161,556,865-byte archive and both exact Git source archives,
23 retained references, eight native ELF entries with 16 KiB alignment, eight
JVM tests and the installed profile/background/reopen and invitation-picker
journeys. Signing and owned-emulator cleanup pass. Live delivery acceptance is
still required. No SDK 1.0 qualification or whole-fleet activation is claimed.

The original Linux qualification job for release 0.1.98 passes both full native
workspace CI commands on frozen sources `52d28d7`/`8f8fdb3`. Its original provider
ZIP, source pair, derived Rust/npm inputs and every linked log hash verify with
the unchanged qualification handler. The logs record zero failed Rust checks,
680 GChat Python checks with one existing skip, 211 GComs Python checks and both
successful dependency audits. Signing and the infrastructure bundle are building.

The original Intel cold-reopen diagnostic passes five consecutive runs on
unchanged GComs `138b071`, under the original 15-second assertion. Each unskipped
native test completes in 5.61–6.81 seconds; its source/test hash matches the
original failed provider build. That earlier failure remains failed, and current
Mac application qualification is still required. No application or API changed.

Earlier controller implementation checkpoints retain their original observations.

Controller generation 58 (`3fec49a`) is active with two ready containers, zero
restarts, 125 actual-image/Kubernetes runtime checks and 219 verified source
hashes. Its previous digest and five private baselines are verified; the
independent watchdog succeeds. Retained-image compaction verified 15 images and
recovered 4,894,228,480 bytes without removing any paths, bytes or permissions.
The hourly recipe passed on 16 images, recovering another 453,869,568 bytes.
Native Linux/Windows tooling portability passes with retained provider archives.

Storage-blocked builds now have a readiness-based recovery path: sufficient
capacity resumes the original request without a controller revision change.
Older work can be superseded only before its external action; active requests
and receipts remain authoritative. Polling visits recent candidates first while
retaining older active work. All 26 focused recovery controls and 684 Python tests pass with five existing
skips; L0 checks 802 paths and API 2/3 contracts remain unchanged. Actual-image
qualification and activation remain pending.

Worker logs now remain distinct when the host clock returns the same timestamp;
the original build request still reconciles and both logs are retained. The
scheduled compactor also follows the live controller's node so its existing
ReadWriteOnce volume can attach. The original scheduled run never started and
its placement failure is retained. All 685 Python tests pass with five existing
skips, including 27 coordinator controls and the fixed-clock regression. The
corrected native Windows rerun and actual-image activation remain pending.

Native workers now install the pinned `cryptography==50.0.2` test dependency.
Mac/Windows build qualification retains signatures and installed offline lifecycle;
the required live network/file/rollback journey runs after fleet deployment with
fresh acceptance authority. iOS cold launch avoids a redundant terminate request
while retaining the 60-second deadline, both launches, liveness and cleanup. A
retained-app startup probe and an unchanged-source Intel machine-reopen diagnostic
are available. All 673 Python checks pass with five existing skips; native
execution of these worker corrections remains pending. Original failures and
provider archives remain retained. API 3/API 2 coexistence, RPC 1, IPC 26, the
64-member limit and covered receipts are unchanged. Fleet/client activation and
a subsequent unattended release are still required before SDK 1.0.
See `docs/evidence/stabilization-20261001/live-controller-and-acceptance.json`.

Earlier controller checkpoints below retain their original observations; current
activation and pending work are described above.

Rollout selection now requires a qualified Linux target when the production
inventory needs its infrastructure bundle. A newer verified mobile artifact
cannot replace the desired deployment while that bundle is missing; the pointer
advances only after the exact-source infrastructure receipt passes. Active
rollout ownership and monotonic versions remain unchanged. Five regression cases
and the full 672-test Python suite pass with five existing skips. The corrected
controller image still requires its actual-image gate before activation.

Controller generation 56 (`29bd39f`) activates complete worker copy cleanup.
The actual image and independent Kubernetes job pass 113 checks and all 219 source
hashes. Both containers are ready with zero restarts; the previous digest is
retained/repaired, five private baseline archives are verified and the independent
watchdog succeeds. The actual HTTPS/TLS transport delivers authenticated multiple
chunks, recovers the exact fixture hashes and removes keys, native copies and
public ciphertext. This probe uses no real host grant and qualifies transport;
the real native provider/workflow and application journey gates remain open.
Evidence: `docs/evidence/stabilization-20261001/live-controller-and-acceptance.json`.

Controller generation 55 (`add203a`) activates encrypted retained acceptance.
The actual image and independent Kubernetes job pass 113 runtime checks and 219
source hashes; all five configured private baseline archives are verified. Both
containers are ready with zero restarts. The independent watchdog now uses the
previous qualified schema-2-capable image and passes a live run. The handoff's
actual HTTPS/native-worker check remains open.

Cleanup additionally removes the driver's owned current/baseline/peer native ZIPs
and extractions after use, preserving diagnostic reports and the coordinator's
original private archives. A required receipt covers those copies as well as the
temporary key and decrypted transport files. All 667 Python checks pass with five
existing skips; the strengthened cleanup image is being qualified before activation.

Published acceptance ciphertext directories remain traversable by the web server
under the production private umask. The original archives and encrypted-response
journal keep their private permissions. All 28 focused acceptance controls pass;
actual-image qualification remains pending.

Run `release_acceptance_test.py` and the full Python suite with a short SSD TMPDIR.
Require actual multiframe AES-GCM recovery with the original ZIP hash; changed
frames, wrong key/request/purpose, stale/mismatched/ambiguous ready artifacts,
small-order public keys and changed retained copies must fail. Queued workers
must receive no authority or repository secret. Lost dispatch freezes the request
and worker; a closed request cannot issue a new grant. Lost response publication
must restore identical ciphertext without another grant. Retained archives may
outlive provider download expiry, but the original successful run/source,
signatures and native journey still must pass. Successful acceptance requires a
source-bound cleanup receipt for both the temporary key and decrypted archives.
Preserve original private ZIPs and failed reports. Run the actual image gate with
its baked production revision before activation. All 667 Python tests pass with
five existing skips, L0 checks 802 paths and contracts retain 18 stable/three
optional methods with unchanged API 2 fixtures. The new image and native handoff
still need their live qualification; generation 54 remains active.

Run `controller_runtime_test.py` and `release_infrastructure_bundle_test.py`.
Require wrong production revisions, changed/symlinked/unsafe source paths,
failed/skipped tests, test-time source mutations, incomplete inventories and
source/image/log mismatches to fail before a success receipt. Failed images must
retain their log. Execute the actual controller image with its baked revision,
no network, a read-only root and a disposable `/tmp`; do not mount keys or release
state. Schema 2 infrastructure must retain the runtime receipt/log and verify both;
legacy schema 1 source-bound archives remain readable without relabelling them as
having passed the new gate. Seven runtime and eleven infrastructure controls pass;
all 655 Python tests pass with five existing skips. Actual-image execution passes 101 tests and
217 source hashes, with independent Kubernetes validation and previous-image
restoration. Generation 54 and the updated hourly compaction recipe are active.

Release storage compaction is active in controller generation 54 (`ea4fdf8`).
It verifies completed source receipts and original provider ZIPs before sharing
identical extraction and verification copies with hard links. The first live run
retains every path, byte, permission and original archive across 123 builds while
reclaiming 15.62 GiB. All seven platform builds resumed after headroom recovered.
The hourly CronJob (`17 * * * *`, no concurrent runs) passed its first live recipe
check. The actual image passes 101 independent tests and all 217 source hashes;
both controller containers are ready with zero restarts, rollback is retained and
repaired, and the independent watchdog succeeds. Five compaction refusal and
retention controls pass. See the [live receipt](docs/evidence/stabilization-20261001/live-controller-and-acceptance.json).
Actual storage remains 128 GiB; a requested 160 GiB expansion is pending after
Longhorn refused it under existing disk limits. The headroom gate remains in force.
Installed acceptance and qualified fleet/client activation remain required.

## Stable contracts and released clients (2026-10-01)

Run `release_ios_versions_test.py` and `release_prepare_test.py`. Require patch
and minor carries, monotonic allocation above retained invalid reservations,
exhaustion refusal, invalid-number rejection before Git preparation or partial
ledger writes, and idempotent reservation after a lost source-ref publication.
Reproduce a historical invalid reservation for the same source pair and after a
documentation change. Require a distinct valid immutable ref, unchanged original
row/ref, idempotent lost publication recovery, and rejection of a corrupted original
manifest even when its iOS number overflows.
Use the signing worker's existing numeric constraints throughout. Retain the
original failed `1.0.100` worker and require a fresh native build with the automatically reserved valid `1.1.0`
reservation. Controller generation 51 (`421be37`) passes 82 independent checks, retains and
repairs generation 50, and has two ready containers and a successful independent
minute watchdog. Exact reviewed status-receipt updates preserve application and
infrastructure identity; unknown evidence still invalidates them. These controls
do not qualify the signed application.

For retained iOS lifecycle qualification, use the exact labelled visibility
Switch exposed in the real XCTest hierarchy. Verify the exact plaintext input
through normal Show/Hide actions within ten seconds, restore secure entry, and
retain the original 45-second joint unlocked-state assertion. Rerun the same
unmodified application; fixture checks alone cannot qualify its lifecycle.

Retained iOS run `37017329318` passes without rebuilding or re-signing the app or
using a Keychain signing fixture; preserve its exact provider archive and binary
hash alongside the original failed run. This does not qualify network messaging
or mobile upgrade acceptance. Run `release_inputs_test.py` after reviewing status
receipt exclusions; both fingerprints must remain stable for those exact files,
while an unreviewed receipt in the same directory still requires new artifacts.

Run `scripts/check_contracts.py`, the `contracts_test.py` negative controls,
`scripts/check-generated.py` and `scripts/check-released-client.py`. The retained
consumer must use unchanged API 2 client/RPC source, attach to the current real
local endpoint, unlock, send the same operation twice, observe one message and
reopen the profile with identical instance and safety number. Wrong-instance
attachment must fail. Pair preparation binds this consumer graph and lock to
the same companion source used by the application.

Run the API compatibility tests: legacy decoders reject unprojected modern states;
the adapter never promotes service acceptance or failure to delivered, preserves
IDs/text/cursors, handles nested network history and rejects unsupported versions
before admission. UI tests cover identify-only version negotiation, pinned identity,
single mutation admission and optional-method capability selection.

## Deployment reconciliation and idle activation (2026-09-30)

Run `release_linux_qualification_test.py` for the separate Linux qualification
and packaging jobs. Reject missing/failed CI, boolean exit codes, changed source
or dependency inputs, altered/missing logs and locks, another run's artifact and
a digest different from the qualifying job output. A packaging-only retry may
reuse the earlier successful qualification attempt in the same run. Failed
attempts must keep separate archives, and no signing key is available to the
qualification job. Actual native execution remains required; original cancelled
Linux runs retain their original conclusions. Android failure artifacts must
retain `shell-errors.jsonl` without changing the installed smoke/retry policy.

Run `release_acceptance_test.py` and `release_inputs_test.py` for separate immutable
qualification workers. Require the actual Git tree, the original signed-app source
manifest, and the matching request/target; reject changed refs, substituted trees
and modified retained evidence. Reconcile lost ref publication and dispatch replies
without another grant or POST. Only a completed failed run with a verified retained
archive and revoked grant can start a corrected worker. An active follow-up keeps
its request across another controller change. Preserve all original failure bytes.
Acceptance workflow changes preserve app inputs but require new infrastructure.
Run these controls with `GCHAT_CONTROLLER_REVISION` set, as in the real image.
Legacy dispatch fixtures select their prior behavior explicitly; the production
default must use the full controller object and reject moving or malformed refs.
Controller generation 52 (`5db2dbe`) passes all 87 image controls and 212 source
hash checks, retains and repairs its prior image, has two ready containers, and
has a successful independent watchdog. Installed acceptance remains open.

Run `release_acceptance_test.py` for exact native source/archive/platform
bindings, baseline → current → baseline → current identity/history/cache preservation,
covered ACKs, unchanged 16 MiB/360-second/600-second bounds, cleanup, lost dispatch
replies and oversized invitation revocation. Only completed acceptance receipts
can refresh; unknown effects cannot create another worker. Retain the old receipt
and logs. Actual completion requires matching native workers executing retained
signed applications without rebuilding or touching personal profiles, followed by
fresh observations of all eight running relays. A desktop pass cannot qualify a
mobile platform. Component tests are not native acceptance evidence.
Reject identical baseline/current provider runs, archives, sources or installed
binaries. Cleanup failure must still stop other owned children and retain a failed
report. Attribute acceptance failures to their own recovery stage.

Run `python3 -m unittest discover -s scripts/tests -p 'mobile_acceptance_test.py'`.
Reject desktop/ordinary-picker receipts, changed ciphertext, re-signing, changed
post-journey binaries, another message's delivery marker and missing exact-pair
native peers. The actual XCTest loopback bridge must reject incorrect credentials.
It must also reject unknown or duplicate replies and expired command deadlines. Then execute
`mobile-acceptance.yml` on the native Android/iOS workers with retained signed
applications and distinct successful providers. Require baseline-created identity,
rendered history and encrypted cache across all three replacements, genuine picker
export hashes, covered ACKs, the original 16 MiB/360-second/600-second interrupted
network check and verified owned-device/process cleanup. Compile only the XCTest
runner. No application debug API, re-signing or personal-device state can qualify
this gate. Verify iOS passphrase entry through the normal Show/Hide control and
require the exact value in the original ten-second assertion, then hide it again.
The original masked-field failure remains failed; real native rerun is required.
Native UI execution is pending. Controller `5b89c81` passes 76 checks
in an independent Kubernetes Job and is active with both mobile recipes and
verified retained baselines. Retain its first registry-policy failure, corrected
retention/repair result, ready-image observation and independent watchdog success.
Also probe registry access using the real pinned watchdog image and labels: the
original policy must fail, and the scoped registry-pod TCP 5000 correction must
allow actual repair of the exact retained previous digest. Preserve both Jobs and
their logs. A successful routine no-op watchdog is insufficient for this check.
Run `release_config_test.py` to require a reconcilable acceptance recipe and its
freshness limit for every installed platform, with SDK qualification separate.
Run `release_inputs_test.py`: reviewed acceptance/status files change qualification
identity while preserving artifact identity. Reviewed GComs status documents
must also preserve infrastructure identity, so discovery can retain the original
artifact without reserving another app version. Require real-ledger baseline
rotation to the latest available predecessor before seed fallback; current/newer
candidates and identical source pairs cannot qualify. Missing historical archives
may fall back; corrupt source-bound receipts must fail. Unclassified mobile files, application
build scripts/workflows and unreviewed GComs evidence must still change artifacts.
Windows fixture cleanup must close SQLite and temporary upload handles before
removal. Linux grant-store ownership and Kubernetes rollout locks require their
POSIX host; portable invalid-authority guards still execute on every platform.
The first Windows Python failure and corrected native results remain separate.
Windows run `36824009006` passes GChat checks and fails the paired GComs stage;
Android run `36824016393` passes the ordinary profile/picker/no-listener lifecycle.
Neither satisfies the installed network acceptance gate. Controller `dfd65d4`
passes independent watchdog validation, digest-preserving retention and live
readiness with its scoped role; retain those results separately from app rollout.

Run `release_deployment_test.py`, `release_host_install_test.py`,
`release_kubernetes_worker_test.py` and `release_coordinator_test.py` through
unittest discovery. Cover interruption after activation, serial canaries,
rollback, unchanged identity/configuration, concurrent operator changes, missing
image availability, disabled workloads and stale deployment observations.
A lower ordinal rollback must use its recorded pod image, freeze automatic rolling,
replace only the failed pod, preserve higher ordinals and resume after a lost reply.
Restricted SSH uploads must reject changed/partial/oversized bytes and cannot select
unlisted units, executable names or protected paths. Controller-only source changes
must not reuse an infrastructure image from an older source pair.
`release_canary_grant_test.py` checks lost replies, fixed bootstrap authority,
expiry without renewal, idempotent revocation and grant-store permissions.
Registry tests require layer repair even when a manifest survives. Image builds
must derive configuration digests from retained archive bytes even when
Docker reports an image index ID. A different or ambiguous archive tag must fail.
Native OCI exports must preserve the exact archived configuration digest; reject
partial or duplicate OCI layout members. Classic Docker archives must produce a
readable OCI manifest. Rollback must retain and restore actual Docker and OCI
manifest media types without changing their running digest. Earlier OCI receipts
keep their original identity. Require real-image round-trip evidence in addition
to component controls before controller activation.
Linux packaging must reject a missing or changed CLI; the native worker runs both packaged binaries
through isolated unlock, wrong-passphrase refusal, disconnect and reopen.
The push image must use its own qualified configuration/repository; a service-image
configuration cannot authenticate it. `release_inventory_test.py` requires all 17
targets, descending anchor partitions, matching init/runtime containers and the
controller last; missing or duplicated host policies must fail closed.
The live canary producer must use the hash-bound provider archive and exact native
CLI receipt. Missing ACKs, smaller files, late or non-finite measurements, changed
inputs and incomplete cleanup cannot pass. Interrupted cleanup must be limited to
its recorded temporary root, with original logs and failures retained.
`release_rollout_watchdog_test.py` must restore a failed controller independently,
preserve the prior rollout intent across a lost reply, respect backoff and refuse
unrelated workloads or changed source bindings. `release_rollback_image_test.py`
requires pinned previous images, retains their manifest/layers before mutation and
repairs missing remote layers before rollback; changed retained bytes must fail.
UI `idle-updates.test.ts` must reject new activity while native status is pending,
wait for saved drafts/actions, and back off after native deferral. Run the UI type
checks/build and all unit tests. Rust `fleet_host` must reject invalid bootstrap
registration before profile startup; managed updates retain owner-lease and
checkpoint/exit checks. Live completion requires exact running identities for all
managed targets and a subsequent unattended update; component passes alone do not
qualify the deployment process.

`release_infrastructure_bundle_test.py` rejects changed source identities,
provider payload hashes, retained binaries and escaping artifact names before
promotion. Infrastructure must come from the hash-bound provider ZIP, never
self-authenticating extracted cache files. Rollout tests must retain and finish
pending rollback even when a new inventory removes its target. Idle activation
tests must acquire the input guard before native shutdown and release it on defer.

## Completed 64-member protected-network gate (2026-09-30)

The `a460d74`/`624e8b2` source pair passes the full `--members 64` campaign.
Both ten-sender phases require 630 real covered signatures, alongside ordinary
recovery, visible long-backlog recovery, exact 16 MiB resume/export, removal and
replacement. Churn admits 65 distinct identities over time, with the old member
removed before replacement; channel membership stays at 64. All deadlines,
resource capture, cleanup and temporary grant revocation pass. Retain the raw
logs/profiles and [source-bound receipt](docs/evidence/irc-hosted-capacity-20260930/capacity-64-01-pass.json).
Do not require a larger campaign or relabel older 500-member evidence.

## IRC/main invitation integration (2026-09-30)

Merged main's reusable invitation sharing, QR rendering and saved enrollment
progress with hosted channels and contacts. The 64-member maximum is unchanged.
Generated Rust/TypeScript/RPC artifacts include both features; merged UI checks,
unit tests and the client build pass. The companion GComs uses IPC26 to preserve
released IPC23 invitation messages before hosted/file requests. Paired Rust and
protected-network qualification remain pending for this merged source.

## IRC parity: retain the 64-member limit (2026-09-30)

The user confirmed **64 members**, including the owner, as the channel limit.
Hosted creation defaults to 64; `/mode +l` accepts 2–64 and GComs independently
enforces signed policy. Capacity qualification now uses 64 independent members,
ten senders and 630 actual recipient signatures per messaging phase. No larger
campaign is required. The former 500-member run was stopped, its grant revoked,
and its original evidence retained without relabelling it as a pass.

## Independent contacts, preferences and presence

With the paired GComs checkout, run `cargo test --workspace --all-features contact
-- --nocapture` and the `chat_service::preferences` filter through the same
workspace feature set, then strict all-target/all-feature Clippy. The integration
case creates two real protocol identities without channels, exchanges signed
cards, verifies recipient delivery and away presence, tests aliases/highlights/
mute/ignore/unignore, and reopens the encrypted archive to verify block/history/
preference persistence. Unit cases cover exact-peer receipts, stable-ID dedup,
notice-loop prevention, presence opt-out/replay/expiry and rollback isolation.

Regenerate `gchat-types` and its `--rpc` export from the tested source, regenerate
the JavaScript RPC bindings, then run workspace Svelte checks, UI tests and the
production build. Preserve the normal ordinary-message bound; only explicit
contact-card import commands receive the larger bounded input envelope.

## IRC parity and hosted archive isolation

Run paired GComs runtime/service/MLS checks, then `cargo test --workspace
--all-features -- --test-threads=1` and strict workspace Clippy through the normal
paired-source configuration. Run `python3 scripts/check-source.py`, regenerate
Rust/TypeScript RPC contracts, and run `npm run check`, `npm test`, `npm run build`.
Require archive event sequence/dedup checks, separate service acceptance versus
recipient delivery, and a real encrypted sidecar downgrade/reopen test: an older
client rewriting `.service` must leave hosted messages and committed event cursor
intact. Corrupt hosted state must fail closed. Include notices/actions and bounded
IRC formatting in both TUI and shared UI validation. No notice may auto-reply.

Keep native, installed-network, 500-member churn/offline/files and timing evidence
separate from component tests. Large-channel recipient receipt completion remains
on covered transport and is measured separately, per the user's chosen tradeoff.
## Owner-controlled membership recovery

`cargo test -p gchat-core --features gc2-carrier --lib membership_recovery` covers strict preview parsing and the actual encrypted-profile stale-member → recovery → single-use invitation → authenticated message ACK → normal kick → reopen flow. Node tests separately assert exact retained wire/ACK equality, rollback and no future access for removed leaves. Browser `recovery.spec.ts` exercises phone/desktop selection, explicit confirmation/cancel, destination binding and absence of owner controls for members. No personal profile is used by these gates.

## Release tooling portability

`release-tools-check.yml` runs release tooling and retained Mac rollback orchestration
on native Linux and Windows without building applications. Manifest paths use ZIP
POSIX syntax on both hosts and reject drive, backslash, absolute and parent paths.
Only the POSIX coordinator daemon/flock test is platform-specific; ledger and
coordinator state-machine tests run on both. Artifact receipts remain source-bound.

## GCHAT-STORE-2 — Apple marketing asset checks

Run `node --check marketing/app-store/retro-v1/export.mjs`, the exporter with the
existing fixture server, and `python3 scripts/check-source.py`. Require four
1290 × 2796 and four 2048 × 2732 opaque JPEGs, zero capture overflow/browser
errors, no text/frame overlaps and a fitting gallery at 1440/768/375 pixels.
Apple must process every upload as `COMPLETE`; verify dimensions, file sizes,
ordered screenshot IDs and exact metadata readback. MD5 is supplied at upload
commit; do not claim checksum readback when Apple returns null. Preserve the old
assets before replacing them. The iOS draft's missing build and pending encryption
review remain separate release gates, not failures of the asset upload.

## GCHAT-STORE-1 — marketing asset checks

Run `node --check marketing/play-store/retro-v1/export.mjs` and
`python3 scripts/check-source.py`. Start `node ui/browser/server.mjs`, then run
`node marketing/play-store/retro-v1/export.mjs` to capture synthetic conversations
through the real Svelte UI and export the five artboards. Require zero browser
errors/capture overflow, decodable images, a 1024 × 500 opaque feature graphic,
and four 1080 × 1920 JPEGs. Review the gallery at desktop and mobile widths for
readable text and horizontal overflow. Compare every app frame with the released
Android build before upload; native parity is not established by browser renders.
Existing native/security/release acceptance requirements remain unchanged.

## Release admission and approved Windows size

Run release_inputs_test.py, release_prepare_test.py and the existing release
coordinator/ledger/config tests. Require controller-only changes to preserve the
artifact reservation and original manifest; unknown/runtime/build inputs and
executable modes must invalidate it. A pending qualification observation is not
a pass. Run native_network_test.py and windows_installer_test.py: reject 4 MiB
outside Windows, wrong retained binary/source/candidate, changed deadlines, and
all existing authentication/hash/reopen/cleanup failures. The actual signed
Windows 36 installer must separately pass its fresh 4 MiB interrupted journey.

## Windows 36 retained diagnostic inputs

Run `native_network_test.py` and `windows_installer_test.py`. The additional
immutable candidate uses the existing failure/cleanup verifier and original
180-second file budget. Fresh actual Windows network execution remains required.

## Retained iOS startup recovery

Run `ios_lifecycle_test.py` and `ios_retained_test.py` through unittest discovery.
Require exact original failed startup/native/binary bindings, owned-device removal,
new native and lifecycle passes, and complete fresh cleanup. Reject crashes, other
cleanup errors, substituted receipts, changed binaries, skipped native tests and
any attempt to promote the original failed verdict. Native simulator execution
remains a separate required gate before upload.

## Platform acceptance isolation

Run `python3 -m unittest discover -s scripts/tests -p 'release_config_test.py'`.
Require unique platform acceptance paths under a custom state directory for both
execution and reconciliation. SDK compatibility must continue using its own
consumer verifier. These checks do not qualify an application or installer.

## Mac network receipt binding

Run `python3 -m unittest discover -s scripts/tests -p "macos_*test.py"`.
The Mac wrapper consumes its protected invitation before spawning children and
removes it on failure. Tests reject failed network execution despite offline
success, substituted executable/harness receipts, absent post-recovery ACKs and
completion past the original 180-second deadline. Native real-package execution
remains separate from these mocked orchestration checks.

## Retained failed network artifacts

`windows-verify.yml` supports the explicitly pinned Windows 29 artifact after its
failed network journey. Reject unrelated installer failures, changed source/archive
bindings, incomplete cleanup, changed trust stores and failed offline service checks.
Explicit fixture diagnostics must retain provider/environment isolation. Cluster
`native_network_test` and `windows_installer_test`: 29 tests passed. The real Windows
journey remains separately required with the original 180/600-second budgets.

## Original Mac packaging identity

A packaging controller may differ from the native-qualified application. Its
optional coordinator manifest must match the exact original commit/tree pair and
committed app version; a modified digest, another source, or another version is
rejected. Bind and recheck that manifest throughout recovery, retain updater
artifacts, and attest the original candidate. Eighteen cluster packaging tests
pass; packaging/native application outcomes remain separate.

## Protected native worker inputs

Windows release verification now requires the explicit environment-backed network
fixture. Tests reject missing input before installation, consume it before child
execution, and remove the private temporary file even on failure. Existing exact
binary/native binding, authentication, failed-network rejection and cleanup tests
remain mandatory. Mac packaging checks require Developer ID inputs in both signing
stages and updater keys in the packaging stage. Cluster run: 42 focused tests pass;
native application gates retain their separate source-bound outcomes.

## iOS lifecycle input focus

Dismiss the native keyboard and wait for viewport geometry to settle before
revealing the confirmation field. Require that field to be fully inside the
main viewport before focusing and typing. Keep the original create/unlock,
default-off background lock, opted-in Keychain resume, relaunch and cleanup
assertions. Run the native XCTest against the retained app without rebuilding
or re-signing it; preserve the original workflow failure separately.
[Exact simulator evidence](docs/evidence/ios-lifecycle-focus-20260927/summary.json).

## Native external-probe exclusion inventory

Native CI records three additional explicit exclusions: the live deployed-relay
probe (requires a separately authorized fresh bundle), the external native
five-hop bootstrap probe, and the nested native TLS/HTTP2 probe. These require
separate provisioned artifacts and do not constitute desktop application coverage.
Accept only their exact GComs test names in receipt validation; reject unknown
names and using these exclusions in GChat reports. Keep failed native counts,
incomplete harnesses, source bindings and installer acceptance mandatory.
The Windows candidate's original verifier rejection remains retained. Its native
result is 1004 GComs passes / 9 explicit exclusions and 186 GChat passes / 1
namespace exclusion, not successful execution of the excluded tests.

## Ownership-transfer fixture admission

Subscribe to the owner's events before admitting the successor, then require the
authenticated bootstrap-metadata delivery event before requesting transfer. A
successful receiver join does not establish that its ACK has reached the owner.
Keep the production pending-message guard, event-lag failure, channel identity,
successor admission, authenticated leave/close and reopen assertions unchanged.

Retained-profile diagnostics must follow one checkpoint lineage. After a copy has
transmitted, do not restart an older snapshot of that identity: replay and sender
ratchet reuse can invalidate the result. Keep emulator and copied native instances
mutually exclusive, and label cross-platform diagnostics separately from app tests.

## Windows updater signing scope

Verify both updater-key environment entries belong to the NSIS build step,
then require the normal signed-installer, pinned signature and installed-profile
lifecycle checks. A certificate-only preflight cannot qualify updater signing.
Retain run 36328979195's missing-key failure and its completed native checks.

## Publisher host scope

Download-page feed-lock tests run on the POSIX publication host alongside signed
feed/APT tests. Native Windows retains all portable artifact selection and source
receipt tests; it does not host the Linux publisher. Keep all four page tests
mandatory in Linux CI. The retained Windows 0.1.18 failure was an unsupported
`fcntl` import in those four server-side tests, before native Rust validation.

## Current versus archived website downloads

Website tests require one Play link for both Android architectures, no archived
installer links for pending targets, and availability text limited to current
platforms. Reject arbitrary managed URLs and unsupported pending target names.

## Website follows qualified Linux publication

Run `release_publish_test.py`, `website_test.py` and `website_deploy_test.py`.
Require immutable package and signature links, exact source bindings, HTML escaping,
idempotent publication and refusal of stale replay or changed package bytes. The
website must link the managed Linux endpoint instead of an old static installer.
After deployment, verify public page bytes, package hash and unchanged live updater
identity. This changes release delivery only; no native build receipt is relabelled.

## Play release metadata

`release_stores_test.py` requires a display name at most 50 characters, exact
version code and complete immutable journal identity. Preserve unknown-outcome
reconciliation; never create a second edit/upload to repair metadata.

## Linux publication reference regression

Run `python3 -m unittest discover -s scripts/tests -p release_publish_test.py`.
Repeated references to the same verified file must publish once; conflicting
hashes, distinct Debian packages and missing/ambiguous signatures must fail.
Missing package evidence must fail before changing the updater pointer.

## Windows update-owner fixture

Run `maintenance_owner_lease_and_prepared_exit_are_enforced` with a directory
secured by the production cross-platform helper. Keep Windows ACL and Unix mode
checks enabled; do not skip the owner-lease and prepared-exit assertions.

## Portable SDK archive publication

Run `python3 -m unittest discover -s scripts/tests -p release_sdk_test.py`.
Require handles closed before archive verification and rename; interrupted or
corrupted copies leave no temporary file or published index. Retrying an exact
release is idempotent; another source pair cannot replace its version. Validate
on native Windows as part of its normal CI.

## Idle presentation CPU regression

Run the core library chat-service tests, full core integration tests and strict
all-target/all-feature core Clippy against the paired GComs source. Require four
waiting views with 4,096 retained operations to share one idle projection;
lock must wake every view and remove private cached results. Verify local send,
cancelled listener, incoming delivery/ACK, membership/topic, archive failure and
reopen behavior. Unchanged file observations must yield no sidecar candidate,
while a failed save leaves the same update retryable.

Run the ignored `idle_cpu_large_history_measurement` separately on a quiet Linux
worker for three 60-second samples of process CPU with four views:

```sh
cargo test --release -p gchat-core --features gc2-carrier --lib \
  idle_cpu_large_history_measurement -- --ignored --nocapture --test-threads=1
```
 Use the identical fixture and optimization profile on the unmodified
baseline and candidate. Export and hash each executable, verify its source
package and candidate-only test list, and retain both results. Debug-build
measurements remain separate; they are not installed-release CPU estimates.
Run the bounded application file/restart/hash gate; keep the 1 GiB campaign
independent. Never use the user's personal profile for destructive tests.

## Responsive carrier release binding (2026-09-25)

Release tooling accepts distinct profile-22 and profile-46 contracts and rejects
mismatched observed profiles. The three changed release tool/test files are
byte-identical to the paired GComs files tested by the 37 passing release-tool
checks. This is tooling validation; no existing native, installed, store or
privacy receipt is relabelled. Current GComs source sends real data immediately
with independent 10–10,000 ms randomized interactive cover. Older peer and policy
cache compatibility requires the staged rollout described in PRODUCTION_RELEASE.md.

## Runtime rollback data compatibility

On a copy of a completed encrypted application profile, run current → compatible
predecessor → current in an empty disconnected namespace. Require identical
identity and nonempty channel set, exact complete-file export on every phase,
clean shutdown and unchanged source fixture bytes. Keep signed installers,
network reconnection and pending-message delivery outside this limited proof.
[Candidate14/candidate12 receipt](docs/evidence/retained-rollback-20260924/summary.json).

## Disposable mobile lifecycle gates

Run four independent Android AVDs with explicit serials and private profiles,
retaining every failure and cleanup result. Use a verified node-local SDK copy
when shared image storage cannot meet the unchanged 180s boot deadline. Check
profile creation, background/relaunch and picker select/cancel, then visually
inspect retained screenshots. Use native XCTest for the Mac iOS simulator.
Keep exact APK/simulator-source bindings; lifecycle success cannot qualify
network messages, files, live push or a later protocol build. Physical devices
are deferred. [Completed baseline](docs/evidence/emulator-lifecycle-20260924/summary.json).

## Owner-budget reopen candidate

[Exact source/artifact receipt](docs/evidence/owner-recovery-20260924/summary.json):
GChat 20979ba / GComs 296d3b6; node 334/0/2 and application core 65/0/2, strict
node/workspace Clippy, paired Linux daemon/desktop builds and signed Android 1017
emulator lifecycle checks passed. The real constructor regression first reproduced
`active owner alias expired before publication` with the old implementation.
Personal encrypted profiles were preserved during installation; successful user
unlock and the original conversation/file completion remain required.

## Retained 12.5 MiB application workload follow-up

Use the actual NetworkClient and normal Linux sender, one admitted channel/file
and one queued message. Flush/reopen after 1 MiB, retain exact file identity and
bytes, export the completed file and compare SHA-256. The original 600-second
case failed at 10 MiB; its separate continuation completed with matching hash,
queued-message delivery and successful shutdown. See PLAN.md for both receipts.
The later bounded-referral pair likewise missed its original deadline at
11,010,048 bytes; its separate continuation completed the same 13,107,200-byte
file with hash equality, authenticated queued-message delivery and shutdown flush.
Do not relabel either original deadline or infer Android OS responsiveness. The
physical-phone uncertain-persistence pause requires a captured first cause and
its own repair validation.

# Application qualification status and remaining checks

## Inbox recovery candidate, 2026-09-23

[Bound receipt](docs/evidence/inbox-recovery-20260923/summary.json): GChat
`48ccdfb` / GComs `15be948`; node library 333 passed/2 existing exclusions,
GChat core 65 passed/2 disconnected-namespace exclusions, strict node and GChat
workspace Clippy, unchanged paired sources, Linux packaging, signed Android
1015 and emulator installation/reopen/picker checks. Preserve the original
Linux missing-development-library failure and the successful packaging-only
retry. Transport interruptions during evidence export are retained separately.

Actual Linux application checks use two preserved test profiles and the same
installed executable hash: reopen both, verify two inbox subscriptions, submit
once in each direction, match recipient IDs/content and authenticated sender
delivery, then transfer/export and hash-check the new 59,392-byte file. The old
75,776-byte file must also export unchanged after receiver restart. These passed;
transient route recovery delay is still recorded.

Physical-device checks now have a [separate receipt](docs/evidence/inbox-recovery-20260923/physical-device-check.json):
profile-preserving 1015 installation, fresh control-channel join, two-way
authenticated delivery, retained channel/messages and actual 59,392-byte file
export with matching SHA-256 passed. Generic activity notifications were observed
while backgrounded; this does not uniquely identify their triggering message.
The earlier retained-sender join timed out. A later background/reopen attempt
initially failed retained and replacement inbox recovery with TLS EOF and a
replacement-install deadline. Preserve that failed checkpoint. The
[later follow-up](docs/evidence/inbox-recovery-20260923/delayed-recovery-followup.json)
records authenticated delivery after roughly ten minutes/seven recovery attempts
and the completed file surviving reopen; do not call its latency acceptable.

The [cluster control](docs/evidence/inbox-recovery-20260923/cluster-reopen-control.json)
passed fresh provisioning and two normal InstanceHost flush/reopen cycles using
explicit NetworkClient on a current-thread runtime. Readiness was observed at
84.621/61.293/61.526 seconds, polling every ten seconds. It uses the frozen
48ccdfb/15be948 sources with no additional registry packages. It is Linux, has
no channel/file backlog, and does not qualify Android suspend/resume or explain
the longer physical-phone failure. Preserve the initial missing-policy-selector
run and the unchanged-binary retry separately. The worker is disposable; logs,
probe source/lockfile and executable hash remain retained.

Keep the original personal conversation/file and cold-join/late-Welcome failures
open. The personal file remained at 92,274,688/122,980,700 verified bytes after
normal pause/resume. Save As also surfaced an unwanted transient background-paused
UI error. No speculative runtime repair or new Android build follows from these
controls alone.


Recorded checkpoint: **2026-09-21 17:36 UTC**. The completed scopes below come
from retained release manifests and publication receipts. Windows16 failed in
GComs after GChat native CI passed. iOS installed simulator validation passed,
but the Apple upload was rejected. The workflow reported a false upload success;
its original evidence remains retained and does not qualify distribution.
The [compact iOS receipt](docs/evidence/ios-lifecycle-upload-20260921/summary.json)
binds the passing lifecycle, rejected upload and tested parser correction.

## Completed release evidence

| Artifact | Exact source pair (GChat / GComs) | Completed checks |
| --- | --- | --- |
| Linux 0.1.3 `.deb` / AppImage | `102e846` / `27c3bf1` | Retained Linux qualification and signed public delivery; [release manifest](https://github.com/IggyGG/gchat/releases/download/v0.1.3/release-manifest.json). |
| Mac ARM64 0.1.4 DMG | `d78b644` / `3185715` | Native GChat 171 Rust passes / 1 explicit exclusion; GComs 876 / 6. The unchanged signed DMG passed separate signature, copied-app profile/reopen, graphical startup and cleanup checks; [manifest](https://github.com/IggyGG/gchat/releases/download/v0.1.4-macos-aarch64.1/platform-release.json). |
| Mac Intel 0.1.4 DMG | `ab3697a` / `398c751` | Native GChat 160 Rust passes / 1 explicit exclusion; GComs 926 / 6. Signed packaging and actual copied-app service/GUI startup with cleanup passed; [manifest](https://github.com/IggyGG/gchat/releases/download/v0.1.4-macos-x86_64.1/platform-release.json). |
| Android 0.1.4 ARM64 / x86_64 APKs | `ab3697a` / `398c751` | Both native packages, pinned signing and 16 KiB alignment passed. Actual x86_64 API35 profile creation, background locking, reopening, process restart and DocumentsUI cancellation/selection passed; [ARM64 manifest](https://github.com/IggyGG/gchat/releases/download/v0.1.4-android-arm64.1/platform-release.json), [x86_64 manifest](https://github.com/IggyGG/gchat/releases/download/v0.1.4-android-x86_64.1/platform-release.json). |

The ARM Mac verification reused the signed DMG after an earlier packaging-helper
failure. That failed receipt remains failed: its original post-build source and
derived-input rechecks did not execute, and the original optimized native-CI
executable was unavailable for byte comparison. The separate recovery verified
retained source/dependency inputs, native signatures and the actual artifact.
The manifest preserves these limitations; they do not apply by inference to
the independently completed Intel build.

Mac startup checks cover the native window, authenticated IPC, default GC2
service selection, encrypted-profile reopen and wrong-passphrase refusal with
network bootstrap disabled. They do not prove an installed live-network
chat/file journey or full rendered interaction. The pinned Mac signatures do
not establish Apple notarization or downloaded-app Gatekeeper acceptance.
The reported Gatekeeper warning now has a dedicated repair: a new Developer ID
artifact must retain the original app/native identity, compare code/resources
without signatures, retain Apple's Accepted submission, validate the stapled DMG
and pass quarantine-aware assessments with Gatekeeper enabled. Repeat the copied
application service/GUI lifecycle on the replacement. Helper unit passes alone
do not qualify the new signature, Apple acceptance or downloaded-app launch.
Android ARM64 compilation/signing does not establish physical-phone execution;
the same-source x86_64 emulator receipt retains that distinction. See
[Android qualification](docs/ANDROID_RELEASE.md) for the exact workload.

## Pending Windows gate

[Windows16](https://github.com/IggyGG/gchat/actions/runs/35624488869) retains its
passing GChat native CI and failed GComs `node_profile` ownership checks. The
correction makes both pre-created fixture directories private on Windows as
well as Unix and explicitly tests refusal to repair an existing nonprivate
directory. Production ownership checks remain unchanged. Validate the corrected
frozen pair, then require pinned Authenticode signing, actual NSIS installation,
matching installed executable/uninstaller signatures, profile reopening,
uninstall/resource cleanup and unchanged persistent certificate stores.

The result is Windows Server 2022 x64 MSVC/installer-service qualification.
Windows 11 graphical interaction, SmartScreen reputation and installed
live-network messaging/files remain separate. Local Python fixture checks are
not a substitute for that native result. See [Windows release checks](docs/WINDOWS_RELEASE.md).

## Pending iOS gate

[Retained verification](https://github.com/IggyGG/gchat/actions/runs/35631610692)
passed the native installed simulator journey: one test, zero failures/skips,
75.851 seconds. It used the existing simulator executable, exercised fresh
profile creation, background locking, manual reopening, consented Keychain
resume and process relaunch, and completed cleanup. Original source/device IPA
and previous failed journey receipts retain their identities and verdicts.

The subsequent `altool` upload returned zero but reported `product-errors`:
Apple 409 Invalid Export Compliance Code. Treat that upload as rejected despite
the original helper/workflow success. The upload-result regression must reject
error JSON, failure markers, empty or ambiguous output regardless of exit status;
only explicit structured success can establish upload acceptance. The first
Apple encryption declaration is not yet configured. Preserve the signed IPA;
any later package configuration/signature needs its own binding. Physical
devices, live onboarding/chat/files, battery and live APNs remain unqualified.
An APNs entitlement is not a push result. See [iOS release checks](docs/IOS_RELEASE.md).
France is included by owner instruction. The unsigned declaration draft and
technical inventory do not constitute a filing, approval or export-compliance
code. Retain the original Apple rejection until an actual accepted upload and
processing result exist.

## Evidence and regression rules

- Bind each check to the complete source pair, dependency inputs, executable and
  installer hashes; preserve original logs, failures and cleanup receipts.
- Keep source browser tests separate from installed-app execution. Use completed
  native receipts for an unchanged packaging/harness retry; rerun affected checks
  when source or effective dependencies change.
- Follow [TESTING.md](TESTING.md) for Rust, generated-contract, UI and consumer
  checks, and [platform delivery](docs/PLATFORM_RELEASES.md) for signed publication.
- Keep the earlier shared Rust consumer/cache regression and Linux/macOS SDK
  size evidence in the [GComs integration report](https://github.com/IggyGG/gcoms/blob/main/docs/RUST_INTEGRATIONS.md)
  bound to its original inputs.
- Apply [production-minutes-v1](docs/PRODUCTION_RELEASE.md): statistical privacy
  and 24-hour campaigns are no longer release gates. Privacy improvements and
  the other unqualified scopes stay explicitly disclosed; no privacy pass is
  inferred from these releases.


UX-1 local Linux installation completed 2026-09-25: signed Debian package from
GChat bf021883/GComs e8546096 installed and exact executable hash verified.
Packaged and installed lifecycle tests pass; native WebKit first-run, retained
identity, single-error retry, picker/cancel/original PNG, screenshot rejection,
keyboard and 320/1100px checks pass. Full coherent runtime gates pass (168 Rust,
25 native, 59 UI unit, 74 browser; Python 449 pass/5 skips), with strict unchanged
runtime/dependency binding for the final policy/tooling delta. Both dependency
audits pass; five-relay invitation/chat/file/restart journey passes in 182s.
Launchers, fleet process and updater preserved; verified rollback retained.
Evidence: docs/evidence/ux-cards/signed-local-summary.json and docs/UX-CARDS.md.
No public release. Native save/export/drop, other OS, screen-reader/usability
sessions and CMD target selection remain unfinished scopes.

## Bounded release files (2026-09-25)

Use `gchat-turnover.py --mode file-recovery --release-check` with the frozen paired build and qualification host: 16 MiB, 180-second completion and 600-second total ceiling. Require abrupt restart, retained pieces/identity, authenticated chat ACK, final hash and reopen/export. The separate 1 GiB campaign is nonblocking; retain its failed deadlines. Authentication, persistence, signatures and rollback remain mandatory.

## Disclosed latency policy (2026-09-27)

Owner-approved: publish with slow joins/reconnects disclosed and optimize latency
next. R04's 30-second join and R03's 10-second reconnect targets are nonblocking;
authentication, delivery, persistence, signatures and rollback remain mandatory.
Publish the limitation on the downloads page. Existing frozen candidate checks
and recorded failures retain their exact source and outcome bindings.
## Retained Windows network qualification (2026-09-28)

- `scripts.tests.native_network_test`: reject stage/global deadline overruns,
  including a successful response arriving after its original budget.
- `scripts.tests.windows_installer_test`: network failure, different executable
  binding, or a surviving child must fail even when offline lifecycle passed.
- The portable runner must pass against the retained signed Linux executable
  before its native Windows dispatch. Bind the final helper bytes, build manifest,
  native receipt, executable and source pair separately from its prototype run.
- Native Windows uses immutable artifact 10942212091 from successful run
  36345150554. Existing offline installer checks remain mandatory. Upload only
  reports/logs; exclude disposable profile directories and remove the temporary
  invitation. A native result is required before claiming Windows network success.

Release stabilization follow-up, 2026-09-28: retained Windows 36 run
36471307753 passed the owner-approved 4 MiB interruption/reopen/exact-hash journey
in 120.594 seconds (282.844 seconds overall), with authenticated bidirectional
messages and installation/profile/trust cleanup. The original 16 MiB failure is
retained. The same iOS 36 simulator executable passed profile/background/manual
unlock/consented Keychain/relaunch after the UI test committed native keyboard
input before observing the field. No app recompilation or signing change was
needed. These gates alone do not prove Windows rollback or iOS network recovery,
store availability, physical devices, live push or privacy qualification.

## IRC hosted/contact files

Qualify the existing FileRequest and binary piece API with hosted and independent
contact conversation IDs. Verify no legacy scope mapping, whole-file hash,
resumption, block/unblock and locking, handle-collision rejection and combined
cache quota accounting. Repeat the actual independent-contact journey and legacy
file controls after the routing change; the older contacts full-suite receipt
qualifies only its recorded source pair.

### Contact file authorization and recovery

Run the full workspace suite and strict Clippy. The independent-contact journey
must share, accept and export a file using DirectMessage permission without
ChannelMember, retain history across reopen, and reject new file offers after
block. File snapshots and binary I/O enforce the stored conversation's capability.
Quota, one-time scoped activity and retryable file errors have separate assertions.
Large partial-file restart and authenticated completion are also required in the
paired GComs runtime gate; a small complete file is not recovery qualification.

## Opt-in hosted directory and contact-only unlock

Require `/hosted list` globally and `/list` only in hosted context; preserve legacy
list behavior. Validate 64-hex pagination cursors and explicit operator `/publish`
controls against the paired service/runtime/IPC24 tests. Run the independent
contact file journey with DirectMessage but without ChannelMember authority;
IdentityRead alone must not unlock a messaging service.

## Scoped historical names

Run `hosted_name_history` and the hosted archive projection/rollback cases.
Require messages before and after a rename in one recovered batch to retain the
correct respective names even when the supplied snapshot already has the new
name. `/whowas` must retain observations after departure and reopen, remain bounded,
and never search another channel. Existing archives without observations must load.
The directory command-scope test also preserves global `/list` from a contact.

## Immediate hosted send feedback

Require a queued text/action/notice to appear as LocalAccepted before any network
event, with its operation ID retained in the encrypted archive. Replay its message
and service acceptance without adding another bubble or promoting it to Delivered.
Run the hosted archive cases and strict workspace Clippy against the paired runtime;
the runtime's stalled-response/retry/reopen test separately proves local admission
is not blocked by remote I/O.

## Live hosted GChat journey

Run `python3 scripts/hosted-live.py --root NEW_PRIVATE_DIRECTORY --gchat
SOURCE_BOUND_GCHAT --probe SOURCE_BOUND_FLEET_PROBE --invitation-file PRIVATE_INVITATION`. The operator must add only
the emitted `channel.json` ID to the service creation allowlist and then create
`enabled` in the run directory. The harness stops owned daemons on exit and keeps
encrypted profiles/logs. Require offline-owner admission and Topic pending,
authenticated topic recovery, exact recipient receipts, unvoiced denial/voice
grant, offline archive recovery, 16 MiB verified partial resume and unvoiced file
completion. Record feedback and delivery timings separately; this two-client
journey cannot substitute for the 500-member protected-network gate.

The live harness reports `passed` for its bounded correctness journey separately
from `latency_passed`. Require explicit 30s admission, 200ms feedback, 5s small-room
message/ACK, 180s resumed verification and 600s file-workflow observations. Keep
large-channel covered-ACK timing separate. A predicate returning success after
its fixed wait deadline must still fail; run `hosted_live_test.py` for this guard.

Live hosted journey observations poll the local IPC snapshot every 250ms. This
reduces sampling uncertainty around the five-second small-room target; all
elapsed times and deadline checks still use the monotonic wall clock. Earlier
one-second-probe reports retain their original measurements and failed status.

Hosted live07 passes the unchanged 200ms feedback, 5s small-room receipt, 30s
join, 180s resumed verification and 600s file-workflow checks. Bind this result
to runtime `907e54f` and the recorded binary hashes; it covers two real clients,
not the separate 500-member or native installed campaigns.
Recovery compatibility: persisted operation results use the existing Text contract so older views and rollback daemons can read the archive; the requesting updated client receives the typed preview. Focused tests check snapshot/journal compatibility and unchanged error results.

After current-trunk integration, repeat actual membership recovery mint/join/
redeem/ACK/kick/reopen alongside hosted/contact regressions. Regenerate the
combined Rust UI/RPC contract, run both workspace Svelte checks and UI tests/build,
and retain the owner-confirmation browser tests for the merged members panel.

## Protected-network hosted capacity

`scripts/hosted-capacity.py --members 12|64 --root NEW_PRIVATE_DIRECTORY --gchat
EXACT_BINARY --probe EXACT_PROBE --invitation-file PRIVATE_INVITATION` runs actual
independent GChat daemon profiles through the installed protected network. Provision
only the emitted channel ID, then create `enabled`. Run the 12-member smoke before
the 64-member campaign; neither component tests nor a smoke pass can set
`qualified_64`. Retain all profiles, logs, source/binary hashes and ten-second
process RSS/I/O samples. The owner remains offline throughout admission. Require
independent verified rosters, ten simultaneous senders and all authenticated
recipient receipts, offline delivery recovery, real mixed chat/file traffic,
16 MiB pause/reopen/resume/export, removal confidentiality and replacement admission.
Keep 200ms feedback, 30s join and 10s recovery targets; covered large-room receipt
completion is measured separately with a 600s observation bound. Existing 180s
file-resume and 600s full-workflow targets remain unchanged. Cleanup and every
required observation must pass. `hosted_capacity_test.py` rejects missing evidence,
duplicate identities, failed timing/cleanup and promotion of a smoke to 64 members.

Capacity defaults to sequential cold bootstrap. `--startup-concurrency 4` starts
at most four independent profiles together, then submits their membership joins
sequentially. The report records that scheduling; profile/identity checks and
all deadlines are unchanged. Preserve results from the original sequential smoke.

Capacity qualification also requires process resource samples covering every
original profile and the full concurrent profile count. Retain per-process CPU
ticks, RSS and I/O with PIDs and clock frequency. A missing/failed sampler cannot
qualify 64 members. Compare timing targets before rounding display values; the
regression rejects a 200.4ms result against the 200ms feedback limit.

### Large membership backlogs and ordinary recovery

The user selected separate treatment for long membership replay on 2026-09-30.
Keep the 10-second ordinary offline-message gate in every campaign. Measure
membership replay separately in both small and large rooms: whenever it exceeds
10 seconds, require visible, positive applied-record progress. A small room can
also accumulate a long membership backlog. Retain the existing bounded
observation windows: 300 seconds for the smoke and 1,800 seconds for 64 members.
Reports explicitly identify this recovery policy; earlier reports cannot inherit it.
Do not convert earlier failed 10-second results into passes. Confirm that locked
views hide progress, cancellation/errors clear it, and an empty recovery page
clears it after a complete roster. Progress is not a delivery acknowledgment.

The hosted capacity journey rechecks the removed client after the replacement
roster converges: it must remain inactive with no channel/archive replay error.
A transient inactive view between kick and rekey cannot qualify churn recovery.

### IRC-8 hosted worker scheduling

Durable hosted admissions must wake the consumer without an idle timer tick.
Multiple queued admissions coalesce; reads and refused mutations must not cause
extra polling. Keep one-second idle polling, durable consumer commit before ACK,
covered receipt transport and the unchanged five-second small-room live target.

The two-client harness records cleanup independently of correctness and timing.
An exceptional journey must attempt every owned process; a stop failure remains
an explicit cleanup failure and nonzero exit, never a successful final receipt.
