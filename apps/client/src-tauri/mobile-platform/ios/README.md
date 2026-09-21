# iOS native implementation

Tauri links this static Swift package into the GChat iOS application. Minimum iOS is 15.
The package uses the application's private Keychain; it requests no shared Keychain access group.
`kSecAttrAccessibleWhenUnlockedThisDeviceOnly` items do not synchronize to iCloud or migrate to another device.

Run `UnlockVaultTests` in an app-hosted iOS simulator test target after Tauri prepares `.tauri/tauri-api`.
Keychain behavior on locked physical devices remains a separate device check. UIKit background/foreground
notifications call Rust directly; the webview and JavaScript need not be executing.
