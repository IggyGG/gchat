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

Validation in progress: npm unit suite 50 passing; Svelte checks clean. Final
receipts are recorded below when qualification completes. Five-person usability
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
in for these OS interactions or for screen-reader review. No installer release or
running-installation update is included in this source change.

## Qualification prerequisite repair

The inherited CI pin b6f9bb0 predates the already-landed file metadata inspection
and central-component builder APIs, so current GChat cannot compile against it.
The current GComs main 9157143 supplies those APIs and requires five independent
GC/2 relays. Update the CI pin and the isolated invitation fixture from four to
five relays together. This repairs qualification inputs, without changing the
application protocol or runtime behavior. The first four-relay journey failed
while waiting for the sender inbox, before invitation creation. That failed
receipt is retained separately from the corrected run.
