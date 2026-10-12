# IRC conversation UX

## Implementation record (2026-10-12)

Task: `irc-ux`, session `ses_ecfcc0addffeQ7yUYkn2r1X2L5`.
Starting GChat source: `cce917396d2cb4c3b5cb62a78eda262d37dbcd32`.
The user chose persistent desktop channel and nick lists, independently
collapsible, with drawers on small screens.

Acceptance scope:

- One stable message row from optimistic send to receipt; preserved whitespace,
  IRC formatting and accurate, compact delivery states.
- Compact private results, grouped routine activity and expandable diagnostics.
- Persistent wide-screen navigation, visible unread activity and saved layout.
- Caret-aware keyboard completion/history, search highlighting and context jump,
  searchable help, quiet notification opt-in and clear offline/read-only states.
- Stable scrollback/date markers/read visibility, consistent forms and typography.
- Browser and native Linux WebKit visual review at 320/390/768/1100/1440px,
  short windows, zoom, long/Unicode/colored text, noisy and uncertain states.
- Existing UI/contract checks and meaningful regression coverage; publication to
  the configured Forgejo trunk after verification.

Status: implementation in progress. No runtime/visual pass is claimed yet.
Retained evidence will be under `test-evidence/irc-ux/`.

## Code comparison

The pre-change `followTail` comparison found
`mozilla-frontend-infra/react-lazylog:src/components/ScrollFollow/index.jsx`
(2025 snapshot, cosine 0.7264, rerank 0.9099). Its explicit follow/stop state
supports preserving user scroll intent; GChat additionally retains an element
anchor. The IRC style comparison found generic ANSI formatter code rather than
a close browser implementation (`UnseenFaith/komada:src/classes/console/Colors.js`,
cosine 0.7030, rerank 0.9325). Neither result establishes rendering correctness;
computed-style and actual visual checks are required.
