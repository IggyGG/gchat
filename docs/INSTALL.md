# Install GChat

Download signed releases from [gchat.boo](https://gchat.boo/#downloads) or the
[GitHub release mirror](https://github.com/IggyGG/gchat/releases). A download is
listed only after its installation and signing checks pass. The release notes
identify the tested platforms and remaining limitations.

Ask someone for a conversation invitation. It can include both the network
settings and a channel, so you can join in one step. A network-only invitation
(`GCNI1-`) connects you without joining a channel. Relay addresses and the
network's public verification key are included; no manual relay setup is needed.

## Windows 11, x86_64

Run the GChat setup executable. It installs for your user and installs Microsoft's
WebView2 runtime when necessary. Open GChat from the Start menu. Check that the
installer's digital signature matches the publisher listed in the release notes.
Desktop releases use a self-signed **Gh0st** certificate. Windows will not recognize
it as a publicly trusted publisher and may block or warn about the installer.
Verify its detached signature and published fingerprint before approving it.

## macOS, Apple Silicon and Intel

Choose the download matching About This Mac: Apple chips use Apple Silicon;
Intel processors use Intel. Open the DMG and drag GChat into Applications, then
launch it. Desktop releases use a self-signed **Gh0st** certificate and are not
Apple-notarized. macOS may block its launch. Verify the detached signature and
published fingerprint before granting a per-application exception; do not disable
system-wide security controls.

For the existing self-signed DMG, the message “Apple could not verify” indicates
that Gatekeeper cannot establish Apple notarization. After verifying the official
download, attempt to open it, then choose **System Settings → Privacy & Security →
Open Anyway** for that specific file and confirm **Open**. If the warning names the
DMG, do this before copying GChat into Applications. Follow
[Apple's instructions](https://support.apple.com/en-us/102445); a warning that an
app will damage your computer is a different case. Developer ID signing and
notarization are being prepared for replacement Mac downloads.

## Linux, x86_64

On Ubuntu 24.04/26.04, open the `.deb` with your package installer, or run
`sudo apt install ./GChat_VERSION_amd64.deb` using the actual downloaded filename.
This installs declared runtime dependencies. The AppImage is an alternative:
allow execution in its file properties, then launch it. If your system requires
FUSE compatibility packages, install those through its package manager.

Every direct download has a detached OpenPGP signature. Obtain the public release key
and compare its fingerprint with the release notes and website before trusting it:

```sh
gpg --import gchat-release-key.asc
gpg --fingerprint
gpg --verify GChat_FILENAME.asc GChat_FILENAME
```

Use the actual artifact filename in place of `GChat_FILENAME`. Downloading a
`.deb` directly does not make `apt` verify its detached signature automatically.

## Android

Choose the ARM64 APK in Downloads for a supported phone; the x86_64
APK is intended for compatible emulators. Android 8.0/API 26 or later is required.
Verify the download, open it, and allow installation from that source if prompted.
Subsequent APKs must use the same signing identity to update the existing app.
Do not uninstall first: Android removes app-private history on uninstall.

Returning from the invitation file picker locks the default profile. Unlock with
your passphrase and choose **Continue** to restore the selected invitation. The
selection is held in memory for up to five minutes; it is not saved to disk.
Current profile/picker validation is emulator-based; physical-device testing and
background push delivery remain unfinished.

## iPhone and iPad

iOS distribution uses TestFlight through the **GChat.boo** App Store Connect
record. Install from the TestFlight invitation once a processed build is available;
an archived IPA is not a direct-install download. iOS 15 or later is required.
Simulator startup checks do not establish physical-device behavior.

On both mobile platforms, **Remember on this device** is optional and off by
default. Without it, unlock with your passphrase after suspension. Background
notification delivery remains unfinished; open GChat to reconnect and retrieve
messages. The release notes distinguish app startup, messaging/file tests and
physical-device checks.

## First launch

1. Open GChat and choose a passphrase for your identity and encrypted history.
   Keep it safe; there is no passphrase reset.
2. Use **Join** in the channel list to paste an invitation or select its text
   file. Review the network and channel, choose a nickname when asked, and join.
   The included relay settings are used automatically.
3. The network dot turns green when connected. Select it for connection details
   or to replace an expired network invitation. **Create** in the channel list
   starts a new channel; `/invite` creates a conversation invitation.

In the terminal client, create/unlock your identity, paste the `GCNI1-` network
invitation, and press Enter. `/network join` remains available. Headless instances
can import an owner-private file with `gchat network --invitation-file PATH`.
Never put the invitation or passphrase in a shell command argument.

An expired invitation needs a replacement. A provider outage needs time to retry;
it does not require a new identity. Keep existing profile, archive, and network
state. Public DNS naming remains opt-in.

## Updates and removal

Download the next signed installer and install it over the existing application.
Quit/disconnect the running instance first. Updates preserve identity and history;
removing the application should also retain these files unless you explicitly
remove them. `gchat paths` shows the locations. Back up a stopped instance's private
data before upgrades, and retain its passphrase separately.

The desktop application starts its own local worker. No Rust toolchain, Node.js,
manual daemon setup, or custom relay configuration is needed for installed users.
