# Packaged desktop service smoke

`scripts/test-native-application.py` checks the service built into the actual
GChat desktop executable on macOS, Windows or Linux. It does not compile a probe
or use a separately built daemon. It requires Python 3.11 or newer.

After installing or extracting the package, run:

```sh
python3 scripts/test-native-application.py \
  --binary /Applications/GChat.app/Contents/MacOS/gchat-desktop \
  --build-manifest retained-installer/build.json \
  --native-receipt retained-native/native-provenance/native-ci.json \
  --output retained-smoke
```

On Windows use the installed `.exe` path and `python`; on Linux use the extracted
or installed `gchat-desktop` executable, not `AppRun`. The executable basename,
SHA-256 and size must match one `executables` entry in `build.json`. The manifest
must bind a successful native receipt with the exact same source/dependency
inputs and native target. Historical manifests without executable bindings are
refused; do not edit one retroactively to manufacture qualification.

The harness creates an owner-private temporary profile, disables network
bootstrap and removes inherited GChat/provider environment overrides. It starts
the application in its existing `--interactive` service mode, checks locked
startup, creates and unlocks the encrypted profile/archive, records a hash of
the protocol identity, disconnects and requests orderly process shutdown. A
second process reopens the same instance, rejects a wrong passphrase, unlocks
with the original ephemeral passphrase and verifies the same protocol identity.
On Windows it uses the existing private shutdown-request file; Unix hosts use
the application's SIGTERM handler. Cleanup removes only the newly created
temporary profile. Existing user profiles are never selected.

Passphrases are generated in memory and sent over owner-only local IPC; they do
not appear in arguments or receipts. Unix sockets and Windows named pipes use
the actual application API framing and instance/version checks. A killed IPC
worker bounds stalled reads. Reports retain hashes of the executable, manifest,
native receipt, harness and process logs, with failures and cleanup recorded.
An existing output directory is never overwritten.

This is an **offline packaged-service lifecycle** check. It does not establish
GUI/WebView startup, interactive usability, installer execution, signature trust,
Gatekeeper acceptance, network delivery, upgrade/rollback, push delivery or
all-egress privacy. The package extraction/installation and signing evidence
remain separate. No relay directory or network invitation is installed and no
production network contact is requested; this is not a packet-level proof of no
egress. The binary may create its normal ephemeral local transport listener.
The service harness does not launch the GUI. The separate macOS DMG wrapper
below exercises the actual graphical path using `--no-network-bootstrap`.

## macOS copied-app startup

```sh
python3 scripts/test-macos-bundle.py \
  --build-manifest retained-installer/build.json \
  --native-receipt retained-native/native-provenance/native-ci.json \
  --output retained-dmg-smoke
```

This native Mac wrapper rehashes the single manifest-bound DMG, verifies its
signature and the publication-pinned leaf certificate, mounts it read-only and
copies the application into a private disposable Applications directory. It
reverifies the copied bundle's signature, signer and actual executable before
running the service lifecycle check.

It then launches that copied executable **without `--interactive` or a carrier
override**, with a fresh private `--home` and `--no-network-bootstrap`. Core
Graphics must observe an on-screen window owned by that exact GUI PID, and the
UI must start its own service before IPC can return the fresh locked instance.
The harness checks locked protocol/archive state and verifies the auto-started
service uses the copied executable, isolated paths and disabled bootstrap. It
closes only its GUI and matching service, checks endpoint removal, detaches the
DMG and removes its private installation/profile. Cleanup failure fails the gate.

`gui_startup_passed` means native window/process plus UI-triggered IPC startup.
The nested GUI receipt remains explicit that rendered interaction and a network
journey are untested. It verifies the GUI default forwards `--gc2-carrier` to the
actual auto-started service; this confirms carrier selection, not authenticated
network connectivity. An unavailable
WindowServer/session fails distinctly as `native_window_unavailable`; it is not
silently replaced with a service-only pass. No Accessibility permission, screen
capture, trust-store change or system `/Applications` modification is requested.

Both macOS architectures and Windows must execute this harness natively; a Linux
pass does not qualify those hosts. Focused Python tests exercise the harness's
binding, failure and cleanup behavior with a fake IPC process, not real GChat
encryption or platform qualification.
