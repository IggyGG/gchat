import XCTest
@testable import tauri_plugin_gchat_mobile_platform

final class PushValidationTests: XCTestCase {
    func testOnlyOpaqueGenericHintsAreAccepted() {
        XCTAssertTrue(PushNotifications.isHint(["activity": "message", "reference": String(repeating: "ab", count: 32)]))
        XCTAssertFalse(PushNotifications.isHint(["activity": "file", "reference": String(repeating: "ab", count: 32)]))
        XCTAssertFalse(PushNotifications.isHint(["activity": "message", "reference": "text"]))
        XCTAssertFalse(PushNotifications.isHint(["aps": ["alert": "unexpected"]]))
    }
}
