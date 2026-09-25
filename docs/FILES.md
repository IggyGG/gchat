# Files in private conversations

Open **Files** in an unlocked channel or private conversation. In the desktop
app, select a local file to share it. An interrupted import can be resumed by
selecting the same source with **Resume import**. Files are limited to 10 GiB.
Recipients choose **Download & share**; seeing an offer does not download its
contents. Pause retains verified progress. Resume uses whichever authorized
peers currently hold the missing pieces. A waiting state means no usable source
is currently supplying a missing piece.

Accepted pieces are automatically shared while the instance is unlocked. Channel
files are available to current members, including members who join later. Private
conversation files remain restricted to their two channel identities. The source
can go offline after other peers have retained all required pieces between them.

**Save to Downloads** writes a verified completed file in the desktop's Downloads
directory. Existing files are never overwritten. Export errors leave no partial
destination. Saved files are separate from the encrypted cache. **Remove cached
copy** stops this instance sharing that copy; it cannot erase peers' copies.

The default cache reserves 10 GiB and retains completed copies for seven days.
Cache settings accept 1 MiB–1 TiB and 1–365 days. Reservations include overhead.
Active downloads and imports are protected from eviction; completed copies may
be evicted to admit an explicitly accepted file. **Show all cached files** lets
you remove retained copies from conversations you have left. Loss of membership
pauses incomplete downloads and releases their active slots. Completed local
copies remain exportable by their unlocked owner; further network access requires
current membership. Lowering the quota blocks new
admission until space becomes available without discarding active work. Unaccepted
offers cannot evict completed data. This cache is temporary availability support,
not an archival storage promise.

The terminal attachment supports:

```text
/file send /local/path/to/file
/file resume-import <handle> /local/path/to/file
/file list [all]
/file cache <MiB> <days>
/file accept <handle>
/file pause <handle>
/file resume <handle>
/file cancel <handle>
/file save <handle> /local/output/path
```

Paths may contain spaces; do not quote them. Imports and exports read local files
in the attachment process. Paths never reach the chat service. Retry an interrupted
send using its original operation, or use `resume-import` with the handle from
`/file list` after restarting the terminal.
The file list shows state, verified bytes, candidate peers and errors.
Browser attachments show progress and controls; native import/export currently
requires the desktop or terminal app.

The additive `files.v1` capability advertises these controls. Version 2 JSON RPC
carries bounded metadata and opaque handles. A separate bounded binary frame on
the existing owner-authenticated local endpoint carries one 256 KiB import/export
piece at a time. It is pinned to the selected instance, requires unlock and, for import/network access, current
membership, and is not exposed by the HTTP gateway. File network records never
enter the text transcript. The archive's encrypted service state retains the
cache key and settings; the sibling `.pieces` directory stores encrypted metadata
and immutable encrypted pieces. A cache recovery error disables file operations
without preventing access to chat history; it leaves the cache intact for recovery.

See GComs' `docs/PRIVATE_FILES.md` for wire/storage details and transport limitations.
Local tests do not establish production GC/2 Bulk fairness, privacy qualification,
or native desktop/mobile release acceptance.
# Selecting the desktop carrier

Native installers include the carrier implementation. Starting a new desktop
instance with `gchat-desktop --home /path/to/instance --gc2-carrier` explicitly
selects responsive profile 46 (immediate real traffic, random interactive cover suppressed after sent data, observable bulk).
The automatically started service receives that selection too. The option
controls service startup; stop an already running service before changing its
startup configuration. Existing GC/1 sessions require the protocol's explicit
authenticated migration and must not be silently reopened as GC/2 sessions.

This option does not constitute a production migration decision or privacy
qualification. Mobile qualification remains deferred.


## Saving and repeated shares

Native clients ask for an export destination. They report the returned path or
document URI only after the write succeeds; cancellation is neutral. Invitation
**Share…** and **Save as…** are separate actions. Browser-only downloads report a
download request rather than claiming a known saved path.

A repeated local import can reuse an existing complete, verified file in the
same channel/private-conversation scope. Size and SHA-256 must match, retained
bytes are reverified, and the original import ID remains a durable alias for
commit recovery. Filename equality is insufficient. Existing encrypted pieces
remain bound to their original manifest; they are never transplanted to a new
share ID or another scope. Local verification may still read the selected file.

An advertised matching digest without a verified local copy is not sufficient
for this reuse path. Independently encrypted offers that have not been verified
locally remain distinct transfers. Offering peers and peers that supplied
verified pieces remain separate counts.
