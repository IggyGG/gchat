# English Play Store listing — submitted 2026-09-29

Google accepted this update for the default English (UK), `en-GB`, listing,
including all five images below. The immediate public-page check still showed
the old content. The submission receipt and published-build UI source comparison
are recorded in `publication.json`.

## App name

GChat.boo: Old-School Chat

## Short description

Old-school channels and nicknames, with encrypted messages and file sharing

## Full description

Remember when a chat room felt like a place?

GChat brings that old-school feeling to invitation-based conversations: familiar nicknames, channels, timestamps and a clear space to talk. Catch up with your people, share a file, and pick up the conversation where you left it.

YOUR PEOPLE, YOUR CHANNELS
Organise conversations in channels and choose a nickname. Join using an invitation from someone you trust. A combined invitation can include both the network connection and the channel.

ENCRYPTED MESSAGES AND FILES
Send encrypted messages and files. Your profile and conversation state are stored locally with encryption, protected by your passphrase.

NO PHONE NUMBER OR EMAIL ACCOUNT
Create a local identity and join by invitation. You do not need to give GChat a telephone number or email address to get started.

A FAMILIAR CHAT FEEL
Enjoy a focused chat window with nicknames and timestamps. GChat takes inspiration from classic chat clients and uses its own network; it does not connect to IRC servers.

OPEN SOURCE
Explore the code at https://github.com/IggyGG/gchat

BEFORE YOU JOIN
You need an invitation to a GChat network. Keep your passphrase safe: there is no central password reset. Recipients can retain content you share. Encryption does not hide every connection detail, and traffic-analysis resistance remains under development.

Optional mobile activity notifications use Apple or Google push services and contain no message text, sender names or filenames. Availability depends on the network operator and platform; background delivery is not guaranteed.

Privacy and support: https://gchat.boo/privacy.html

## Asset order and alternative text

| Upload | File | Alternative text |
| --- | --- | --- |
| Feature graphic | `exports/feature.png` | GChat: Old-school chat. Your people. Channels, nicknames and encrypted conversations. |
| Phone screenshot 1 | `exports/01-conversation.jpg` | A GChat channel with nicknames, timestamps and a sample conversation between Ada and Iggy. |
| Phone screenshot 2 | `exports/02-channels.jpg` | GChat channel navigation with general, design and archive conversations. |
| Phone screenshot 3 | `exports/03-files.jpg` | GChat's files panel shows notes.txt shared in a sample channel. |
| Phone screenshot 4 | `exports/04-invitation.jpg` | Join GChat with an invitation, without providing a telephone number or email address. |

## Publishing notes

Screens show the real shared Svelte interface with synthetic data from its browser fixture. Before submission, the UI, application frontend and public assets were confirmed identical to the source of published Android build 1055. Native device screenshot verification was not performed, and native system bars are not fabricated. For future revisions, repeat the released-build comparison and replace any mismatching capture. The two original live setup screenshots are retained in `source/live-*.png` for comparison.

The feature graphic is 1024 × 500 PNG, opaque. The four phone images are 1080 × 1920 JPEG. Each gives approximately 63% of the total image area to the unmodified app capture. Text is outside the capture. The current app icon is retained; no replacement icon is proposed.

Use the English main listing's Graphics fields in Play Console. Upload the feature graphic and the four screenshots in the order above; preview before submitting. This pack does not change binaries, data-safety answers, privacy policy or store state.

The creative direction uses the familiarity of mIRC-era chat without its name or logo in the images. No rankings, reviews, user counts, platform compatibility or stronger privacy guarantees are invented.

## Basis and measurement

The live listing, retrieved 2026-09-29, has only identity-creation and invitation-entry screenshots. Its current short description is: “Encrypted conversations and files. Join by invitation, without a phone number.” The proposed first screenshot instead shows the central chat experience. Capabilities and limitations above are based on that listing and the current app source.

Reference: [current listing](https://play.google.com/store/apps/details?id=boo.gchat.app), [Google's preview asset requirements](https://support.google.com/googleplay/android-developer/answer/9866151?hl=en).

After native parity review, test the graphics against the current listing using a Play Console store-listing experiment where available. Keep copy constant during the graphics test. Use store-listing acquisition rate as the main measure, segment results by language and acquisition source, and wait for sufficient evidence before claiming an improvement. Test the new copy separately.
