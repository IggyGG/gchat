# Workspace consistency audit

This audit covers GChat views, the shared service, native exports, and the paired
GComs file service. It does not relabel prior installers as containing these changes.

| Finding | Change or remaining limit |
| --- | --- |
| Original and recovered invite replies append twice | One result per network/instance/operation; browser race regression |
| Check result appears inert | Details shows action, ID, state, response/error and last check; explicit status refresh |
| Large result cards hide conversation | Full-screen closable result view and compact Only you entry |
| Desktop sidebar always visible despite default state | Hidden drawer on all widths, stable opener and collapse arrow |
| Join/Create compete with variable-height composer | Single Add channel chooser |
| Creation displays Joining | Separate Creating/Joining progress and explicit public/private selection |
| Topic absent from workspace header | Header and channel subtitle; observed topic changes in transcript |
| Membership/file changes have no timeline representation | Encrypted retained activity with initial-baseline and repeated-refresh deduplication |
| File download claims saved before OS reports success | Native destination picker; exact returned path/URI; neutral cancellation |
| Repeat verified import creates another payload share | Same-scope verified cache reuse and durable commit aliases |
| Older cache reader can mistake an alias for a complete payload | Superseded import is non-serving; retries retain the canonical file identity |
| Offline activity withdrawal prevents unlocking | Confirmed local opt-out remains effective; unavailable peer notification does not reject profile reopening |
| Unverified independent offers share a claimed digest | Still distinct; merging these without manifest verification would be unsafe |
| Presence risks implying delivery or human attention | Opt-in, expiring Recently active/Unknown; no delivery gating |
| Archive save error followed by event publication | Unchanged existing behavior: RAM archive state may remain visible after a save failure. Committed-only projection and abrupt-loss durability remain separate follow-up work; UI activity is not a durability acknowledgement |
| Android hardware Back and external document providers | Browser/keyboard coverage does not establish physical-device behavior |

Validation receipts belong to the exact new sources. Store review, external
publication and existing installed applications remain distinct from local UI
and component checks. No saved user profile should be reset to apply this update.

Local validation on 2026-09-22: GChat workspace 146 passed and two existing
namespace exclusions; 39 UI unit cases, 29 browser cases, 21 native-library
cases and the native desktop compile check passed. Python ran 407 cases with
one existing skip. Strict GChat workspace and affected GComs Clippy passed.
The final cache compatibility change passed all 15 ordinary swarm cases,
the GChat file/reopen regression, file-transfer Clippy and native checks.
The separate 1 GiB swarm case remains excluded from this UI check. Earlier
full-suite evidence is retained separately from these final affected-path checks.
