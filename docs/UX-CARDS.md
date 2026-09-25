# UX-1: welcome, shared theme and original invitation cards

Implementation started 2026-09-25, Codex. Keep Boo and the IRC conversation
character evergreen: charcoal, muted mint, readable entry forms, silent short
feedback and reduced-motion support. No seasonal theme or extra decoration.

The shared EntryFrame waits for actual identity state, distinguishes identity
unlock from archive unlock, and confirms new passphrases. Existing recovery
instructions remain authoritative; no reset or backup system is added. Cards
opened while locked are staged in memory until explicit review after unlock.
A changed profile discards that staged card. Credentials are never persisted
in browser storage by this flow.

An original PNG contains one uncompressed iTXt entry named GChat.Invitation,
carrying the existing invitation unchanged. Import bounds file size to 8 MiB,
pixels to 4 Mi, checks chunk lengths and CRCs, rejects animation and duplicate
payloads. The picture is a carrier, not an authority. The service still checks
signatures/expiry and produces the network/channel preview before explicit join.
Screenshots and image recompression lose the invitation. Text invitation export
and import remain available. Native desktop saving uses the existing private
temporary-file and no-overwrite save path. No new dependency is introduced.

Current trunk already supports combined invitations, routing bootstrap and
idempotent joins. Reuse those contracts; no additional network-grant issuer or
migration is needed. The existing combined-invitation service journey is the
real-network acceptance test. UI tests separately prove export/import, staging,
service rejection, consent, first-run confirmation, focus and narrow layouts.

CMD consumes the same entry component and theme. Its access-token authentication
is unchanged; progressive enhancement adds immediate pending feedback. Observe,
Signals and Fleet retain their workflows with shared colors and legible labels.

Automated qualification completed 2026-09-25. The final receipt is
the retained `test-evidence/ux-cards/summary.json` in the original task evidence. Five-person usability
sessions and native Windows/macOS visual/save-dialog qualification require real
participants/platform runs and are not represented by browser fixtures.
Code-match tooling is unavailable in this session (codematch=unreachable).

## Release acceptance still requiring people/platforms

Use five participants unfamiliar with this build, including one keyboard-only
participant. Give each an original invitation PNG without coaching. Ask them to
open the application, create or unlock an identity, explain the destination shown
in the review, join, send a message and return after a simulated connection loss.
Then provide a screenshot instead of the original card and observe recovery.
Record completion, hesitation, wrong turns and what they believe is stored locally;
do not record passphrases or usable invitations. Resolve recurring confusion
before release. This protocol is prepared, not a claim that sessions occurred.

On Linux, Windows and macOS, verify a real native save dialog, cancellation,
refusal to overwrite an existing destination, original-file pick/drop, keyboard
focus and restart with retained identity. Browser fixture success does not stand
in for these OS interactions or for screen-reader review. The initial source change did not publish installers or update installations.
The subsequent local Linux installation is recorded below.

## Qualification prerequisite repair

The inherited CI pin b6f9bb0 predates the already-landed file metadata inspection
and central-component builder APIs, so current GChat cannot compile against it.
The current GComs main 9157143 supplies those APIs and requires five independent
GC/2 relays. Update the CI pin and the isolated invitation fixture from four to
five relays together. This repairs qualification inputs, without changing the
application protocol or runtime behavior. The first four-relay journey failed
while waiting for the sender inbox, before invitation creation. That failed
receipt is retained separately from the corrected run.

## Completed automated qualification

Implementation source: GChat 2713dfc with GComs 9157143; CMD d57914b.
GChat has 158 passing Rust workspace tests (two isolated-network cases excluded
from the ordinary suite), strict Clippy, both formatting checks, 23 passing Linux
native tests, a clean native compile check, 50 UI unit tests, 52 browser tests and
a successful production frontend build. Svelte reports no errors or warnings.
The Python harness has 406 passes and one platform skip. Node 22.22.1 and npm
11.19.1 pass the final frontend gates; Rust is 1.98.0.

The corrected five-relay combined-invitation journey passes separately in 311
seconds, including network acceptance, chat, file transfer and restart retention.
The helper confirms unchanged host interfaces and namespace. This is an isolated
protocol fixture, not a public-fleet privacy or throughput qualification.

CMD has 486 passing unit tests (343 infrastructure-gated skips), clean type/lint
checks, 22 ordinary browser passes (two infrastructure skips), and two additional
configured-login passes for pending/error behavior and submission without JS.
Production-built login visuals were reviewed at 390 and 1100 pixels; GChat
welcome visuals at 320 and 1100 pixels and the exported card were also reviewed.

The initial harness run exceeded Unix socket path limits under the managed
temporary directory; the rerun uses a short private SSD path. The combined
workspace/native build exceeded its 16 GiB quota after workspace tests and native
compilation passed. Native tests and the isolated journey were then built in
separate jobs with debug symbols omitted, preserving normal test assertions.
Earlier failed/interrupted logs are retained separately. Frozen source identities
and derived dependency inputs were verified unchanged. No application runtime
behavior was altered to accommodate qualification.

## Linux installation follow-up

The real Linux WebKit check found a rejected passphrase announced both inline
and in the workspace notice bar. Locked views now keep that message beside the
passphrase field; unlocked operation notices are unchanged. A browser regression
checks one announcement and successful retry. Type checks, all 53 browser tests
and the production frontend build pass (`native-polish-frontend.log`). Native
candidate and retained-profile upgrade evidence is recorded separately from
public installer qualification; user sessions and other operating systems remain
unqualified until their actual runs.


The initial local Linux executable used GChat ffb9517 and GComs 9157143,
with frozen source archives and verified derived dependency inputs. Its two user
launchers were briefly selected, then restored after newer backend and automatic
update work arrived on trunk. The guarded rollback succeeded. The candidate is
retained, but does not replace the installed application. Production profiles and
running services were not changed or restarted. CMD deployment awaits target
selection. No public release was performed.

The final executable passed native first-run confirmation/creation, rejected
unlock without encrypted-file changes, retained-identity GUI unlock, and one
inline rejection notification. Linux WebKitGTK/X11 picker open/cancel, original
PNG staging, screenshot rejection, keyboard focus and 320/1100px rendering were
also checked on the preceding candidate; the final frontend differs only in
locked-notice visibility. These runs use disposable profiles and an isolated
Xvfb/session bus. See [local installation receipt](evidence/ux-cards/local-summary.json).
Native save/export dialogs, overwrite handling and drag-and-drop still need
qualification, alongside Windows/macOS, screen-reader and five-person usability
sessions. Browser export tests and Rust save tests do not substitute for those
OS interactions. No public download or signing claim is made by this receipt.
