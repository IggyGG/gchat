import XCTest

/// Targets the installed, unmodified GChat app. No application test hooks,
/// network invitations or injected archive/profile contents are used.
@MainActor
final class GChatLifecycleTests: XCTestCase {
    let app = XCUIApplication(bundleIdentifier: "boo.gchat.app")
    let passphrase = "simulator lifecycle fixture only 2026"

    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    override func tearDownWithError() throws {
        if app.state != .notRunning {
            let hierarchy = XCTAttachment(string: app.debugDescription)
            hierarchy.name = "final-accessibility-hierarchy"
            hierarchy.lifetime = .keepAlways
            add(hierarchy)
            screenshot("99-final-state")
        }
    }

    func heading(_ title: String) -> XCUIElement {
        app.webViews.staticTexts.matching(NSPredicate(format: "label == %@", title)).firstMatch
    }

    func screenshot(_ name: String) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    func enterPassphrase() {
        let field = app.webViews.secureTextFields.firstMatch
        XCTAssertTrue(field.waitForExistence(timeout: 15))
        field.tap()
        field.typeText(passphrase)
        // WKWebView's native input accessory can cover the form button even
        // when XCTest reports that button as hittable. Use the same Done
        // control as a person, then require the keyboard to leave before tapping.
        if app.keyboards.firstMatch.exists {
            let done = app.toolbars.buttons["Done"].firstMatch
            XCTAssertTrue(done.waitForExistence(timeout: 10))
            done.tap()
        }
        let hidden = NSPredicate { _, _ in !self.app.keyboards.firstMatch.exists }
        expectation(for: hidden, evaluatedWith: nil)
        waitForExpectations(timeout: 10)
    }

    func backgroundAndActivate() {
        XCUIDevice.shared.press(.home)
        let background = NSPredicate { _, _ in self.app.state != .runningForeground }
        expectation(for: background, evaluatedWith: nil)
        waitForExpectations(timeout: 10)
        // Exercise a real background interval. This is not an OS suspension or
        // power-loss test and makes no guarantee about iOS background budgets.
        Thread.sleep(forTimeInterval: 2)
        app.activate()
    }

    func testProfileBackgroundAndReopen() {
        app.launch()
        XCTAssertTrue(heading("Create your GChat identity").waitForExistence(timeout: 30))
        screenshot("01-fresh-profile")
        enterPassphrase()
        app.webViews.buttons["Create identity"].tap()
        XCTAssertTrue(heading("Connect to GChat").waitForExistence(timeout: 45))
        screenshot("02-encrypted-profile-created")

        // Default-off credential storage must require manual unlock on return.
        backgroundAndActivate()
        XCTAssertTrue(heading("Reconnect this instance").waitForExistence(timeout: 30))
        screenshot("03-background-requires-passphrase")
        enterPassphrase()
        let remember = app.webViews.descendants(matching: .any)
            .matching(NSPredicate(format: "label == %@", "Remember on this device")).firstMatch
        XCTAssertTrue(remember.waitForExistence(timeout: 10))
        remember.tap()
        app.webViews.buttons["Reconnect"].tap()
        XCTAssertTrue(heading("Connect to GChat").waitForExistence(timeout: 45))

        // This now uses the native simulator Keychain after explicit consent.
        backgroundAndActivate()
        XCTAssertTrue(heading("Connect to GChat").waitForExistence(timeout: 45))
        XCTAssertFalse(heading("Reconnect this instance").exists)
        screenshot("04-consented-keychain-resume")
        app.terminate()
        app.launch()
        XCTAssertTrue(heading("Connect to GChat").waitForExistence(timeout: 45))
        XCTAssertFalse(heading("Create your GChat identity").exists)
        XCTAssertFalse(heading("Reconnect this instance").exists)
        screenshot("05-retained-profile-relaunch")
    }
}
