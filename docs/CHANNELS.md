# Channels and invitations

Click the active channel name to open its details. Use **Invite someone** to copy
one invitation containing the network and starting channel. The recipient pastes
it into **Join** and confirms the displayed network identity.

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
