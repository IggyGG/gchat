import XCTest
@testable import tauri_plugin_gchat_mobile_platform

final class UnlockVaultTests: XCTestCase {
    func testValidationRejectsPathsAndInvalidSecrets() {
        for slot in ["", "../x", "a/b", "a\\b", "a b", "å", String(repeating: "a", count: 129)] {
            XCTAssertFalse(UnlockVault.validSlot(slot))
        }
        XCTAssertTrue(UnlockVault.validSlot("profile_A-123"))
        XCTAssertFalse(UnlockVault.validSecret(""))
        XCTAssertFalse(UnlockVault.validSecret("a\0b"))
        XCTAssertFalse(UnlockVault.validSecret(String(repeating: "a", count: 4097)))
    }

    // Execute in an app-hosted iOS test target with ordinary private Keychain
    // access. This does not require a shared access-group entitlement.
    func testOptInRoundTripUpdateAndDelete() throws {
        let vault = UnlockVault()
        let slot = "test_" + UUID().uuidString
        defer { try? vault.delete(slot: slot) }
        XCTAssertNil(try vault.read(slot: slot))
        XCTAssertThrowsError(try vault.store(slot: slot, secret: "fixture secret", confirmed: false))
        XCTAssertNil(try vault.read(slot: slot))
        try vault.store(slot: slot, secret: "fixture secret", confirmed: true)
        XCTAssertEqual(try vault.read(slot: slot), "fixture secret")
        try vault.store(slot: slot, secret: "replacement", confirmed: true)
        XCTAssertEqual(try vault.read(slot: slot), "replacement")
        try vault.delete(slot: slot)
        XCTAssertNil(try vault.read(slot: slot))
        try vault.delete(slot: slot)
    }
}
