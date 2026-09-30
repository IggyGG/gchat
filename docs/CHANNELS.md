# Channels and invitations

Click the active channel name to open its details. Use **Invite someone** to copy
one invitation containing the network and starting channel. The recipient pastes
it into **Join** and confirms the displayed network identity.

`/invite` offers **One person** (one join, one hour), **Friends** (25 joins,
seven days) and **Devices** (100 joins, 90 days). Custom expiry and admission
limits are independent; unlimited values require an explicit choice. Everyone
uses their own identity. Retries do not consume a second join, but a fresh
identity does. A copied invitation can admit its holder, so share it privately.

Use `/invites` to see counts, share again or revoke. Revocation blocks new
admissions without removing existing members; an already committed join can
still finish. The owner must be online to admit a member. Device invitations
grant channel membership, not permission to execute commands or administer
the channel.

Joining creates one saved enrollment. Its focused screen shows network,
reply-route and admission progress. Close it freely and use `/enrollments` to
return; retries resume the same identity and request. Cancellation is available
before admission may have happened. After that, complete the join and use
`/part` to leave. Completed requests can be removed from the list without
leaving their channel.

Reusable members can catch up through a bounded journal of 128 membership
epochs. Legacy members retain the conservative convergence barrier. Reaching
a storage or epoch bound reports backpressure instead of dropping unacknowledged
messages. New archives require the updated client; keep the pre-upgrade encrypted
backup for rollback rather than opening them with an older writer.

- `/nick Alice` changes your display name in the current channel. Your identity,
  message history and membership stay the same.
- `/topic` displays the topic. An owner or administrator can use `/topic text`
  or `/topic --clear` to change it.
- `/part` requests authenticated removal from the channel. It is not merely
  hiding the window; removal completes when the owner processes the request.
  Your local history remains available as an archive.
- `/owner nickname-or-member-id` transfers a private channel to an existing
  member. The channel identity and history are retained.
- `/part --transfer nickname-or-member-id` transfers ownership and requests
  your removal. The new owner can then invite and remove members.
- `/part --close` closes a channel you own for everyone. Offline members learn
  of closure when they reconnect. Existing local history is retained; pending
  messages are not reported as delivered just because the channel closes.

Channel details offer these actions directly, including an explicit confirmation
for leaving or closing. Duplicate display names are disambiguated by member ID.
Ownership transfer requires settled pending messages and is currently supported
for private channels. Topic, nickname and ownership updates are authenticated
inside the encrypted channel and saved before acknowledgment or publication.

`/hide` only hides a conversation. It does not leave its membership. Use **Help**
for the complete command list; `/font`, `/find`, `/lock` and `/disconnect` keep
infrequent controls out of the main workspace.


## Minimal workspace

The channel drawer starts hidden. Open it with the channel button, use **+ Add
channel** to join or create, and collapse it with the inward arrow. Topics appear
next to the active channel and below its name in the drawer. Unread counts stay
separate from optional recently-active observations.

Creation defaults to private. `/create --public #name nickname` creates an
encrypted public channel; it does not silently publish it. The owner can publish
that same channel from Details or `/publish https://directory.example/`. A failed
publication must be retried against the existing channel, not another creation.

Invitations and command responses open in a full-screen Details view. A compact
**Only you** entry reopens the retained result. Original and recovered replies
are identified by network, instance and operation ID. Closing a view does not
cancel a request. **Refresh status** checks the original operation without
submitting it again. An unknown outcome is not a failed operation or confirmed
delivery. The encrypted service journal retains safe command names and results;
command arguments and message contents are not copied into request metadata.

Member changes, topic changes and file offers observed by this profile appear in
the conversation. Initial roster loading establishes a baseline. Change notices
do not invent an actor or claim that removing a member was voluntary. The local
observation timestamp is not a signed remote event time.

Recently-active sharing is optional and defaults off. `/presence on` enables
short-lived channel signals for this profile; `/presence off` stops them. Unknown
means there is no fresh observation, not that the person is offline. Presence is
kept in memory and never used as a condition for message delivery.

## Reconnect existing members

If both devices show messages as **accepted locally** but neither receives them,
keep them online and use `/reconnect` in the affected channel. Copy the resulting
command to the other member through another app and run it in that same channel.
This exchanges current encrypted addresses; it does not leave, rejoin, reset
history or resend messages with new identities. Saved messages retry normally,
and delivery is confirmed only by recipient acknowledgments.

A reconnect code is not a new-member invitation. It works only for current
members of the same membership epoch while its addresses remain valid. If it
expires, create a fresh code. This is an explicit fallback when all retained
peer addresses have expired, not automatic discovery of offline members.

If the network remains disconnected, open **Network → Connection details** (or
run `/status --details`). This shows local route and subscription counts without
addresses, invitation tokens or identity keys. It does not retry a saved action.
An operation's Details view retains its recorded error alongside a later generic
“outcome unknown” reply; neither indicates delivery or authorizes automatic replay.

Connection details also reports the background inbox recovery phase, attempt count, bounded last backend failure and whether an unconfirmed owner checkpoint has paused recovery. These local diagnostics do not alter retry timing, lease authority or delivery acknowledgements.

A stalled retained inbox no longer blocks every later recovery round: after two
failed retained attempts, background recovery proceeds to authenticated inbox
replacement. The previous inboxes retain their original cleanup deadlines; saved
messages and membership are preserved. Connection details identifies the recovery
stage if the round times out. This does not imply recipient delivery.
