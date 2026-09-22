# Conversation workspace

Channels, users and files open as overlays from the circular edge controls. The
channel drawer's `+` starts Join/Create. Drawers do not resize messages; Escape,
the inward arrow or the backdrop closes them and restores focus. The network dot
is next to the brand, with the instance identity under **Your identity**.

There is no permanent Status conversation. Unlock restores the last available
conversation in this view; an obsolete Status selection chooses the first one.
With no conversations, Join/Create is shown. `/status` remains a private command
result. A missing activity signal is not an identity or delivery failure. Self is
marked `you`; peers only show a recent activity label when one exists.

`?` and `/help` render private terminal output. Clicking a command prepares it in
the composer without sending it. Invitations, find results and operation details
also remain private. Checking an uncertain operation queries its original ID;
it never resubmits. The result store deduplicates recovered and live responses.
Create asks for name, visibility and nickname in private-answer mode and requires
confirmation. Escape or `/cancel` restores the conversation draft. Join retains
an explicit signed-network preview and confirmation. Settings, unlock and native
file pickers remain separate controls.

Desktop uses one header. Linux/Windows window controls sit beside `?`; macOS
retains its native traffic lights in an overlay title bar. Closing the desktop
view preserves the receiving service; `/disconnect` remains the explicit stop.
Mobile and browser views do not show desktop window controls.

## App invitation links

The canonical form is `gcoms://join#GCI1-…`. The unchanged signed invitation
carries network, relay and optional channel authority. URL hosts, queries and
paths cannot override that authority. A custom scheme is a convenience, not a
verified origin: the receiver still validates the signed payload and requires
explicit acceptance of a new network. There is no website redirect or fallback.

Copy/Share produces an app link only when it fits 8 KiB. Larger invitations use
the full code or a file; nothing is truncated. Complete/raw code and Save as are
available. Pasting a link or `/join <link>` opens the same review. Existing raw
invitations and files continue to work.

The native deep-link plugin registers the scheme for desktop and mobile bundles.
Cold/warm activation uses a bounded, memory-only inbox, deduplicating repeated OS
notifications. Locked views wait for unlock; reviewing is not joining. Profile
replacement clears pending activations. Explicit `--home` desktop launches keep
independent windows; ordinary OS invitation activation targets the default GUI.
The separate `--interactive` receiving process never enters the single-instance
GUI path. Links and their bearer payloads must not be logged.

Browser tests exercise mobile/desktop widths, zoom, keyboard navigation, drafts,
picker suspension, inline results and explicit invitation consent. Native scheme
registration, traffic lights and OS activation require their own platform checks;
a browser or Linux result does not qualify other OS installers.
