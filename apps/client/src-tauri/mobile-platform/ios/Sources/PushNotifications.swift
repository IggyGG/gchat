import Foundation
import UIKit
import UserNotifications
import ObjectiveC

struct PushArgs: Decodable { let enabled: Bool? }
struct PushReply: Encodable {
    let enabled: Bool
    let permission: String
    let platform = "apns"
    let token: String?
    let tapped: Bool
}

/// One app-native delegate. It never starts/unlocks a GComs profile in a callback.
final class PushNotifications: NSObject, UNUserNotificationCenterDelegate {
    static let shared = PushNotifications()
    private let policy = "boo.gchat.push.enabled"
    private let tokenSlot = "native_push_token"
    private var installed = false
    private var tapped = false
    private var generation: UInt64 = 0
    private let vault = UnlockVault()
    var enabled: Bool { UserDefaults.standard.bool(forKey: policy) }

    // Tao owns UIApplicationDelegate. Add only absent optional APNs methods;
    // never replace a framework or another plugin's implementation.
    private func install() throws {
        guard !installed else { return }
        guard let delegate = UIApplication.shared.delegate,
              let cls: AnyClass = object_getClass(delegate) else { throw PushError.unavailable }
        let success = NSSelectorFromString("application:didRegisterForRemoteNotificationsWithDeviceToken:")
        let failure = NSSelectorFromString("application:didFailToRegisterForRemoteNotificationsWithError:")
        let received = NSSelectorFromString("application:didReceiveRemoteNotification:fetchCompletionHandler:")
        guard class_getInstanceMethod(cls, success) == nil,
              class_getInstanceMethod(cls, failure) == nil,
              class_getInstanceMethod(cls, received) == nil else { throw PushError.unavailable }
        let center = UNUserNotificationCenter.current()
        guard center.delegate == nil || center.delegate === self else { throw PushError.unavailable }
        let registered: @convention(block) (AnyObject, UIApplication, NSData) -> Void = { _, _, data in
            DispatchQueue.main.async { Self.shared.registered(data as Data) }
        }
        let failed: @convention(block) (AnyObject, UIApplication, NSError) -> Void = { _, _, _ in
            // Retry during the next foreground session; never log provider data.
        }
        typealias FetchCompletion = @convention(block) (UIBackgroundFetchResult) -> Void
        let hint: @convention(block) (AnyObject, UIApplication, NSDictionary, FetchCompletion) -> Void = { _, _, _, complete in
            // Default locked profiles stay locked. The foreground lifecycle does
            // bounded recovery after normal unlock; no daemon is created here.
            complete(.noData)
        }
        guard class_addMethod(cls, success, imp_implementationWithBlock(registered), "v@:@@"),
              class_addMethod(cls, failure, imp_implementationWithBlock(failed), "v@:@@"),
              class_addMethod(cls, received, imp_implementationWithBlock(hint), "v@:@@@") else { throw PushError.unavailable }
        center.delegate = self
        installed = true
    }
    func restore() {
        guard enabled else { return }
        do { try install(); UIApplication.shared.registerForRemoteNotifications() } catch { /* Status remains pending. */ }
    }
    func configure(_ value: Bool?, completion: @escaping (Result<PushReply, Error>) -> Void) {
        dispatchPrecondition(condition: .onQueue(.main))
        if let value = value {
            generation &+= 1
            if !value {
                UserDefaults.standard.set(false, forKey: policy)
                UIApplication.shared.unregisterForRemoteNotifications()
                UNUserNotificationCenter.current().removeAllDeliveredNotifications()
                do { try vault.delete(slot: tokenSlot) } catch { /* Policy prevents reuse even if deletion fails. */ }
                snapshot(completion); return
            }
            let expected = generation
            UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
                DispatchQueue.main.async {
                    guard self.generation == expected else { self.snapshot(completion); return }
                    guard error == nil, granted else {
                        UserDefaults.standard.set(false, forKey: self.policy)
                        self.snapshot(completion); return
                    }
                    do {
                        try self.install()
                        UserDefaults.standard.set(true, forKey: self.policy)
                        UIApplication.shared.registerForRemoteNotifications()
                        self.snapshot(completion)
                    } catch { completion(.failure(error)) }
                }
            }
        } else { snapshot(completion) }
    }
    private func registered(_ data: Data) {
        guard enabled, (16...256).contains(data.count) else { return }
        let token = data.map { String(format: "%02x", $0) }.joined()
        try? vault.store(slot: tokenSlot, secret: token, confirmed: true)
    }
    private func snapshot(_ completion: @escaping (Result<PushReply, Error>) -> Void) {
        UNUserNotificationCenter.current().getNotificationSettings { settings in
            DispatchQueue.main.async {
                let granted = settings.authorizationStatus == .authorized || settings.authorizationStatus == .provisional
                let token: String?
                if self.enabled && granted { token = try? self.vault.read(slot: self.tokenSlot) } else { token = nil }
                if self.enabled && granted && token == nil {
                    try? self.install()
                    UIApplication.shared.registerForRemoteNotifications()
                }
                let reply = PushReply(enabled: self.enabled, permission: granted ? "granted" : "denied", token: token, tapped: self.tapped)
                self.tapped = false
                completion(.success(reply))
            }
        }
    }
    static func isHint(_ values: [AnyHashable: Any]) -> Bool {
        guard values["gcoms_activity"] as? String == "message", let reference = values["gcoms_reference"] as? String,
              reference.count == 64 else { return false }
        return reference.utf8.allSatisfy { (48...57).contains($0) || (97...102).contains($0) }
    }
    func userNotificationCenter(_ center: UNUserNotificationCenter, willPresent notification: UNNotification,
                                withCompletionHandler completion: @escaping (UNNotificationPresentationOptions) -> Void) {
        completion(enabled && Self.isHint(notification.request.content.userInfo) ? [.banner, .sound] : [])
    }
    func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse,
                                withCompletionHandler completion: @escaping () -> Void) {
        if enabled && Self.isHint(response.notification.request.content.userInfo) { tapped = true }
        completion()
    }
}
private enum PushError: Error { case unavailable }
