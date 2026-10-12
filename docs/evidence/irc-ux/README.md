# IRC UX qualification

The [summary](summary.json) binds the UI source, companion npm input, production
assets and retained test logs. The screenshots use isolated, fictional data.

- [Desktop conversation](desktop.png): persistent channel/user lists and compact
  grouped activity.
- [Mobile conversation](mobile.png): full-width transcript and header navigation.
- [Busy mobile state](busy-mobile.png): four uncertain sends and four concurrent
  transfers, with one representation per operation and a reachable composer.
- [200% zoom](zoom.png): readable Help with the Back control on-screen.
- [Native Linux WebKit](native-linux.png): multiline message after local acceptance.

The task record in `test-evidence/irc-ux/` retains the full width/font/secondary
screen matrices, original failures and native receipts. Direct visual inspection
of those images found issues that the initial DOM assertions missed; the repaired
cases have regression assertions for actual contrast and viewport bounds.

The native harness uses GTK3/WebKitGTK 4.1 and the shared GChat workspace. It
qualifies native rendering and interactions with fixture state. Signed installers,
live transport and Windows/macOS release acceptance retain their own gates.
