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

    func waitForUnlockedProfile() {
        // Foreground activation can initially expose the pre-background WebView
        // snapshot. Await the complete target state within the original budget,
        // rather than accepting one old heading then failing on its next frame.
        var readySince: TimeInterval?
        let ready = NSPredicate { _, _ in
            let unlocked = self.app.state == .runningForeground
                && self.heading("Connect to GChat").exists
                && !self.heading("Reconnect this instance").exists
                && !self.heading("Create your GChat identity").exists
            guard unlocked else { readySince = nil; return false }
            let now = ProcessInfo.processInfo.systemUptime
            if readySince == nil { readySince = now }
            return now - readySince! >= 1
        }
        expectation(for: ready, evaluatedWith: nil)
        waitForExpectations(timeout: 45)
        XCTAssertFalse(app.webViews.staticTexts.matching(NSPredicate(
            format: "label CONTAINS %@", "secure device storage was unavailable"
        )).firstMatch.exists)
    }

    func enterPassphrase() {
        let field = app.webViews.secureTextFields.firstMatch
        XCTAssertTrue(field.waitForExistence(timeout: 15))
        field.tap()
        field.typeText(passphrase)
        // WKWebView's native input accessory can cover the form button even
        // when XCTest reports that button as hittable. Use the same Done
        // control as a person, then require the keyboard to leave before tapping.
        let done = app.toolbars.buttons["Done"].firstMatch
        if app.keyboards.firstMatch.exists || done.exists {
            XCTAssertTrue(done.waitForExistence(timeout: 10))
            done.tap()
        }
        let main = app.webViews.otherElements.matching(NSPredicate(format: "label == %@", "main")).firstMatch
        var previousFrame: CGRect?
        var settledSince: TimeInterval?
        let settled = NSPredicate { _, _ in
            guard !self.app.keyboards.firstMatch.exists, !done.exists, main.exists else {
                settledSince = nil
                return false
            }
            let frame = main.frame
            let now = ProcessInfo.processInfo.systemUptime
            if previousFrame != frame || settledSince == nil {
                previousFrame = frame
                settledSince = now
            }
            return now - settledSince! >= 1
        }
        expectation(for: settled, evaluatedWith: nil)
        waitForExpectations(timeout: 10)
    }

    func tapFormButton(_ title: String) {
        let button = app.webViews.buttons[title]
        let main = app.webViews.otherElements.matching(NSPredicate(format: "label == %@", "main")).firstMatch
        // isHittable alone can expose the pre-keyboard frame. Never submit by
        // tapping coordinates clipped behind the native input accessory.
        XCTAssertFalse(app.keyboards.firstMatch.exists)
        XCTAssertFalse(app.toolbars.buttons["Done"].firstMatch.exists)
        XCTAssertTrue(button.exists && button.isHittable)
        XCTAssertTrue(main.exists && main.frame.contains(button.frame))
        button.tap()
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
        tapFormButton("Create identity")
        waitForUnlockedProfile()
        screenshot("02-encrypted-profile-created")

        // Default-off credential storage must require manual unlock on return.
        backgroundAndActivate()
        XCTAssertTrue(heading("Reconnect this instance").waitForExistence(timeout: 30))
        screenshot("03-background-requires-passphrase")
        enterPassphrase()
        let remember = app.webViews.switches
            .matching(NSPredicate(format: "label == %@", "Remember on this device")).firstMatch
        XCTAssertTrue(remember.waitForExistence(timeout: 10))
        remember.tap()
        XCTAssertEqual(remember.value as? String, "1")
        tapFormButton("Reconnect")
        waitForUnlockedProfile()
        screenshot("03b-consented-manual-reopen")

        // This now uses the native simulator Keychain after explicit consent.
        backgroundAndActivate()
        waitForUnlockedProfile()
        screenshot("04-consented-keychain-resume")
        app.terminate()
        app.launch()
        waitForUnlockedProfile()
        screenshot("05-retained-profile-relaunch")
    }
}
