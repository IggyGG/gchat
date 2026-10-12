# IRC conversation UX

## Conversation first

At 1000 CSS pixels and above, compact channel and user lists remain beside the
conversation. Each has an independent collapse control; these display preferences
are saved on the device. Narrow windows use modal drawers, with Escape/backdrop
closure and focus restoration. Channel unread counts remain visible in the
conversation header when navigation is closed. An `@` badge indicates an unread
mention or configured highlight; read-only history inspection never marks it read.

Messages keep one renderer, nickname, whitespace and timeline identity through
pending, local acceptance and recipient acknowledgement. Delivery is distinct from
reading. Unconfirmed outcomes say so; “Checking” appears only during a real check.
Operation details query the original ID and do not resubmit it.

Routine consecutive joins, parts, topic and nickname events collapse into one
expandable line. Messages, actionable events, long gaps and dates break groups.
Full event text and identities remain in the expansion. Pending/error feedback
stays beside its operation; unrelated failures are summarized separately.
Files show compact progress in chat, with exact details in Files.

## Interaction and rendering

- Tab completes at the caret while preserving trailing text. Ambiguous choices
  use arrows/Tab and Enter; Escape dismisses them. History navigation starts at
  the appropriate input boundary and restores the draft.
- Help has command search, common actions and keyboard shortcuts. Selecting an
  action opens its form or prepares the composer, without sending.
- Find emphasizes literal matches and opens their original conversation context.
- Covered conversations are not marked read. Scrollback has stable anchors for
  messages, activity and transfers; incoming updates preserve the reader's place.
- Notifications are an optional inline invitation, rather than an automatic
  modal after unlock. Connection trouble and read-only state have readable labels.
- Fixedsys and readable monospace share a layout. IRC styles remain text and
  bounded palette colors. Inverse uses the real theme ink; unreadable explicit
  color pairs receive a contrasting foreground while preserving original text.
  Mentions inherit this corrected ink inside colored spans.
- Forms have scoped field IDs, associated errors, consistent actions and focus.
  Multiline input resizes in native webviews without relying on `field-sizing`.

## Qualification

Implementation sources: `d0a7999`, `f259d2b`. The latter passes 76 UI unit tests,
105 Chromium browser checks and zero-error/zero-warning Svelte checks. Native
Linux WebKitGTK 2.52.6 passes all four rendering/interaction checks at each of
320, 390 and 1100 pixels. The visual matrix additionally covers 768/1440 pixels,
short windows, 200% zoom, font fallback, Unicode, all 256 IRC color pairs,
grouped activity, uncertain operations and secondary screens.

Final visual refinement and WebKit browser qualification are in progress. Retained
screenshots, original failed attempts and source-bound summaries live under
`test-evidence/irc-ux/`. Reproduction commands are in [TESTING.md](../TESTING.md).
Native webview evidence uses isolated fixture data; signed package, live network
and other OS installer qualification use their normal release gates.

## Code comparison

The pre-change `followTail` comparison found
`mozilla-frontend-infra/react-lazylog:src/components/ScrollFollow/index.jsx`
(2025 snapshot, cosine 0.7264, rerank 0.9099). Its explicit follow/stop state
supports preserving user scroll intent; GChat additionally retains an element
anchor. The IRC style comparison found generic ANSI formatter code rather than
a close browser implementation (`UnseenFaith/komada:src/classes/console/Colors.js`,
cosine 0.7030, rerank 0.9325). Neither result establishes rendering correctness;
computed-style and actual visual checks are required.

Post-change contrast comparison found
`nextcloud/server:apps/workflowengine/src/helpers/contrast.ts`
(cosine 0.7658, rerank 0.9399), using the same 4.5 contrast threshold and black/white
fallback. GChat uses the standard luminance formula over its fixed palette and
theme values, with computed-style coverage of every pair; it adds no dependency.
The unread queue comparison found
`signalapp/Signal-Android:app/src/main/java/org/thoughtcrime/securesms/messages/WebSocketDrainer.kt`
(2025 snapshot, cosine 0.6519, rerank 0.8439). It is not a matching implementation;
the useful shared idiom is single-owner draining with cleanup. GChat's read-only
scanner additionally rejects superseded profile/unread tokens and repeated cursors.
