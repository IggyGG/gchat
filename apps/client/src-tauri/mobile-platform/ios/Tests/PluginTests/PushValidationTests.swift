import XCTest
@testable import tauri_plugin_gchat_mobile_platform

final class PushValidationTests: XCTestCase {
    func testOnlyOpaqueGenericHintsAreAccepted() {
        XCTAssertTrue(PushNotifications.isHint(["gcoms_activity": "message", "gcoms_reference": String(repeating: "ab", count: 32)]))
        XCTAssertFalse(PushNotifications.isHint(["gcoms_activity": "file", "gcoms_reference": String(repeating: "ab", count: 32)]))
        XCTAssertFalse(PushNotifications.isHint(["gcoms_activity": "message", "gcoms_reference": "text"]))
        XCTAssertFalse(PushNotifications.isHint(["activity": "message", "reference": String(repeating: "ab", count: 32)]))
        XCTAssertFalse(PushNotifications.isHint(["aps": ["alert": "unexpected"]]))
    }
}
