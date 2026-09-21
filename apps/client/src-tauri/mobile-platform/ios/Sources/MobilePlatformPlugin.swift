import Foundation
import Tauri
import UIKit
import WebKit

@_silgen_name("gchat_mobile_platform_lifecycle")
private func nativeLifecycle(_ state: UInt8)

private struct SlotArgs: Decodable { let slot: String }
private struct StoreArgs: Decodable { let slot: String; let secret: String; let confirmed: Bool }
private struct SecretReply: Encodable { let secret: String? }

final class MobilePlatformPlugin: Plugin {
    private let vault = UnlockVault()
    private static let worker = DispatchQueue(label: "boo.gchat.app.unlock-vault")
    private var observers: [NSObjectProtocol] = []

    @objc public override func load(webview: WKWebView) {
        guard observers.isEmpty else { return }
        let center = NotificationCenter.default
        observers.append(center.addObserver(forName: UIApplication.didEnterBackgroundNotification,
                                            object: nil, queue: .main) { _ in nativeLifecycle(2) })
        observers.append(center.addObserver(forName: UIApplication.didBecomeActiveNotification,
                                            object: nil, queue: .main) { _ in nativeLifecycle(1) })
        // Inactive (e.g. a transient system dialog) is not background.
        switch UIApplication.shared.applicationState {
        case .active: nativeLifecycle(1)
        case .background: nativeLifecycle(2)
        default: break
        }
    }

    deinit { observers.forEach(NotificationCenter.default.removeObserver) }

    @objc public func getSecret(_ invoke: Invoke) {
        let args: SlotArgs
        do { args = try invoke.parseArgs(SlotArgs.self) }
        catch { invoke.reject("Invalid unlock storage request", code: "INVALID_ARGUMENT"); return }
        Self.worker.async { [self] in
            do { invoke.resolve(SecretReply(secret: try vault.read(slot: args.slot))) }
            catch { invoke.reject("Unlock storage is unavailable", code: "VAULT_UNAVAILABLE") }
        }
    }

    @objc public func storeSecret(_ invoke: Invoke) {
        let args: StoreArgs
        do { args = try invoke.parseArgs(StoreArgs.self) }
        catch { invoke.reject("Invalid unlock storage request", code: "INVALID_ARGUMENT"); return }
        Self.worker.async { [self] in
            do { try vault.store(slot: args.slot, secret: args.secret, confirmed: args.confirmed); invoke.resolve() }
            catch { invoke.reject("Unlock storage is unavailable", code: "VAULT_UNAVAILABLE") }
        }
    }

    @objc public func deleteSecret(_ invoke: Invoke) {
        let args: SlotArgs
        do { args = try invoke.parseArgs(SlotArgs.self) }
        catch { invoke.reject("Invalid unlock storage request", code: "INVALID_ARGUMENT"); return }
        Self.worker.async { [self] in
            do { try vault.delete(slot: args.slot); invoke.resolve() }
            catch { invoke.reject("Unlock storage is unavailable", code: "VAULT_UNAVAILABLE") }
        }
    }
}

@_cdecl("init_plugin_gchat_mobile_platform")
func initPlugin() -> Plugin { MobilePlatformPlugin() }
