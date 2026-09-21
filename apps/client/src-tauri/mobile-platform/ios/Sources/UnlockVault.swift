import Foundation
import Security

internal enum VaultFailure: Error { case invalidArgument, consentRequired, unavailable }

/// Device-only, unlocked-device Keychain storage. No files or preferences hold plaintext.
internal final class UnlockVault {
    private static let service = "boo.gchat.app.unlock.v1"

    static func validSlot(_ slot: String) -> Bool {
        let bytes = Array(slot.utf8)
        return (1...128).contains(bytes.count) && bytes.allSatisfy {
            (65...90).contains($0) || (97...122).contains($0) || (48...57).contains($0) || $0 == 45 || $0 == 95
        }
    }

    static func validSecret(_ secret: String) -> Bool {
        !secret.isEmpty && secret.utf8.count <= 4096 && !secret.utf8.contains(0)
    }

    private func query(_ slot: String) throws -> [String: Any] {
        guard Self.validSlot(slot) else { throw VaultFailure.invalidArgument }
        return [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: Self.service,
            kSecAttrAccount as String: slot,
            kSecAttrSynchronizable as String: false
        ]
    }

    func store(slot: String, secret: String, confirmed: Bool) throws {
        guard confirmed else { throw VaultFailure.consentRequired }
        guard Self.validSecret(secret) else { throw VaultFailure.invalidArgument }
        let base = try query(slot)
        var bytes = Data(secret.utf8)
        defer { bytes.resetBytes(in: 0..<bytes.count) }
        let attributes: [String: Any] = [
            kSecValueData as String: bytes,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]
        let updated = SecItemUpdate(base as CFDictionary, attributes as CFDictionary)
        if updated == errSecSuccess { return }
        guard updated == errSecItemNotFound else { throw VaultFailure.unavailable }
        var added = base
        attributes.forEach { added[$0.key] = $0.value }
        let result = SecItemAdd(added as CFDictionary, nil)
        guard result == errSecSuccess else { throw VaultFailure.unavailable }
    }

    func read(slot: String) throws -> String? {
        var request = try query(slot)
        request[kSecReturnData as String] = true
        request[kSecMatchLimit as String] = kSecMatchLimitOne
        var value: CFTypeRef?
        let result = SecItemCopyMatching(request as CFDictionary, &value)
        if result == errSecItemNotFound { return nil }
        guard result == errSecSuccess, var data = value as? Data else { throw VaultFailure.unavailable }
        defer { data.resetBytes(in: 0..<data.count) }
        guard data.count <= 4096, let secret = String(data: data, encoding: .utf8), Self.validSecret(secret) else {
            throw VaultFailure.unavailable
        }
        return secret
    }

    func delete(slot: String) throws {
        let result = SecItemDelete(try query(slot) as CFDictionary)
        guard result == errSecSuccess || result == errSecItemNotFound else { throw VaultFailure.unavailable }
    }
}
