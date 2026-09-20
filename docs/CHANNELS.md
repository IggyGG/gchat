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
