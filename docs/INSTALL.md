# Install GChat

Download signed releases from [gchat.boo](https://gchat.boo/#downloads) or the
[GitHub release mirror](https://github.com/IggyGG/gchat/releases). The first
release is a developer preview. A download is listed only after its installation
and signing checks pass.

You need a network invitation from the person inviting you. It begins `GCNI1-`.
Relay addresses and the network's public verification key are already included.

## Windows 11, x86_64

Run the GChat setup executable. It installs for your user and installs Microsoft's
WebView2 runtime when necessary. Open GChat from the Start menu. Check that the
installer's digital signature matches the publisher listed in the release notes.
This preview uses a self-signed **Gh0st** certificate. Windows will not recognize
it as a publicly trusted publisher and may block or warn about the installer.
Verify its detached signature and published fingerprint before approving it.

## macOS, Apple Silicon and Intel

Choose the download matching About This Mac: Apple chips use Apple Silicon;
Intel processors use Intel. Open the DMG and drag GChat into Applications, then
launch it. This preview uses a self-signed **Gh0st** certificate and is not
Apple-notarized. macOS may block its launch. Verify the detached signature and
published fingerprint before granting a per-application exception; do not disable
system-wide security controls.

## Linux, x86_64

On Ubuntu 24.04/26.04, open the `.deb` with your package installer, or run
`sudo apt install ./GChat_VERSION_amd64.deb` using the actual downloaded filename.
This installs declared runtime dependencies. The AppImage is an alternative:
allow execution in its file properties, then launch it. If your system requires
FUSE compatibility packages, install those through its package manager.

Every download has a detached OpenPGP signature. Obtain the public release key
and compare its fingerprint with the release notes and website before trusting it:

```sh
gpg --import gchat-release-key.asc
gpg --fingerprint
gpg --verify GChat_FILENAME.asc GChat_FILENAME
```

Use the actual artifact filename in place of `GChat_FILENAME`. Downloading a
`.deb` directly does not make `apt` verify its detached signature automatically.

## First launch

1. Open GChat and choose a passphrase for your identity and encrypted history.
   Keep it safe; there is no passphrase reset.
2. Paste your network invitation or select its text file, then choose **Import
   and connect**. The included Hetzner relays are selected automatically.
3. Wait for **Connected to the GChat network**. Then join a channel using a
   separate conversation invitation, or create a channel and invite a friend.

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
