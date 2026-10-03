import Foundation
import UIKit
import XCTest

// The HTTP endpoint belongs to the XCTest process on the native worker.
// The retained application receives only normal UI input and deep links.
final class GChatAcceptanceTests: XCTestCase {
    enum Failure: Error { case observation, protocolBinding, unsupported }
    let app = XCUIApplication(bundleIdentifier: "boo.gchat.app")
    var bodies = Set<String>()
    var files = Set<String>()
    var passphrase = ""
    var endpoint = ""
    var token = ""
    var phase = "ready" {
        didSet { print("GCHAT_ACCEPTANCE_UI_PHASE=\(phase)") }
    }

    func require(_ value: Bool, line: UInt = #line) throws {
        if !value {
            print("GCHAT_ACCEPTANCE_OBSERVATION_FAILURE=\(line)")
            throw Failure.observation
        }
    }

    func wait(_ seconds: TimeInterval = 60, line: UInt = #line, _ check: @escaping () -> Bool) throws {
        let result = XCTWaiter.wait(for: [XCTNSPredicateExpectation(
            predicate: NSPredicate { _, _ in check() }, object: nil)], timeout: seconds)
        try require(result == .completed, line: line)
    }

    func element(_ label: String) -> XCUIElement {
        app.descendants(matching: .any).matching(NSPredicate(format: "label == %@", label)).firstMatch
    }

    func click(_ label: String) throws {
        let target = element(label)
        try wait { target.exists && target.isHittable }
        target.tap()
    }

    func tapVisible(_ target: XCUIElement) throws {
        try wait { target.exists && target.isHittable }
        let frame = target.frame
        try require(frame.width > 0 && frame.height > 0 && app.frame.contains(frame))
        app.coordinate(withNormalizedOffset: CGVector(dx: 0, dy: 0))
            .withOffset(CGVector(dx: frame.midX - app.frame.minX,
                                 dy: frame.midY - app.frame.minY)).tap()
    }

    func dismissKeyboard() throws {
        let done = app.toolbars.buttons["Done"].firstMatch
        let hide = app.keyboards.buttons["Hide keyboard"].firstMatch
        if app.keyboards.firstMatch.exists || done.exists {
            try wait(10) { (done.exists && done.isHittable) || (hide.exists && hide.isHittable) }
            if done.exists && done.isHittable { done.tap() } else { hide.tap() }
        }
        try wait(10) { !self.app.keyboards.firstMatch.exists && !done.exists }
    }

    func type(_ field: XCUIElement, _ value: String) throws {
        try wait(20) { field.exists }
        let main = app.webViews.otherElements.matching(NSPredicate(format: "label == %@", "main")).firstMatch
        try wait(20) { main.exists }
        for _ in 0..<6 {
            if field.isHittable && main.frame.contains(field.frame) { break }
            if field.frame.midY < main.frame.minY {
                app.webViews.firstMatch.swipeDown()
            } else {
                app.webViews.firstMatch.swipeUp()
            }
        }
        try require(field.isHittable && main.frame.contains(field.frame))
        var focused = false
        for _ in 0..<3 {
            let frame = field.frame
            app.coordinate(withNormalizedOffset: CGVector(dx: 0, dy: 0))
                .withOffset(CGVector(dx: frame.midX - app.frame.minX,
                                     dy: frame.midY - app.frame.minY)).tap()
            let expectation = XCTNSPredicateExpectation(
                predicate: NSPredicate(format: "hasKeyboardFocus == true"), object: field)
            if XCTWaiter.wait(for: [expectation], timeout: 2) == .completed {
                focused = true
                break
            }
        }
        try require(focused)
        // The host copies and verifies this command's input through simctl on
        // the bound, fresh simulator. The test runner's background pasteboard
        // is not an authority for the foreground application's clipboard.
        // Only the normal system Paste action enters the unchanged app.
        field.press(forDuration: 1)
        let menuPaste = app.menuItems["Paste"].firstMatch
        let buttonPaste = app.buttons["Paste"].firstMatch
        try wait(10) { (menuPaste.exists && menuPaste.isHittable) ||
            (buttonPaste.exists && buttonPaste.isHittable) }
        let paste = menuPaste.exists && menuPaste.isHittable ? menuPaste : buttonPaste
        paste.tap()
        try dismissKeyboard()
        if field.elementType == .secureTextField {
            let label = field.label
            try require(!label.isEmpty)
            try passphraseVisibility("Show passphrase")
            let revealed = app.webViews.textFields.matching(NSPredicate(format: "label == %@", label)).firstMatch
            do {
                try wait(10) { revealed.exists && (revealed.value as? String) == value }
            } catch {
                let actual = revealed.exists ? (revealed.value as? String) ?? "" : ""
                print("GCHAT_ACCEPTANCE_INPUT_FIELD_PRESENT=\(revealed.exists ? 1 : 0)")
                print("GCHAT_ACCEPTANCE_INPUT_VALUE_LENGTH=\(actual.count)")
                print("GCHAT_ACCEPTANCE_INPUT_EXPECTED_LENGTH=\(value.count)")
                print("GCHAT_ACCEPTANCE_INPUT_VALUE_MASKED=\(actual.contains("•") || actual.contains("●") ? 1 : 0)")
                throw error
            }
            try passphraseVisibility("Hide passphrase")
            try wait(10) { field.exists }
        } else {
            try wait(10) { (field.value as? String) == value }
        }
    }

    func passphraseVisibility(_ title: String) throws {
        // WKWebView exposes the aria-pressed visibility toggle as a Switch.
        let control = app.webViews.switches.matching(NSPredicate(format: "label == %@", title)).firstMatch
        let main = app.webViews.otherElements.matching(NSPredicate(format: "label == %@", "main")).firstMatch
        try wait(10) { control.exists && main.exists }
        let deadline = ProcessInfo.processInfo.systemUptime + 10
        while control.exists && (!control.isHittable || !main.frame.contains(control.frame))
                && ProcessInfo.processInfo.systemUptime < deadline {
            if control.frame.midY < main.frame.minY {
                app.webViews.firstMatch.swipeDown()
            } else {
                app.webViews.firstMatch.swipeUp()
            }
        }
        try require(control.isHittable && main.frame.contains(control.frame))
        control.tap()
    }

    func unlock(_ create: Bool, _ value: String, launch: Bool = true) throws {
        passphrase = value
        phase = "unlock-start"
        if launch { app.launch() }
        let button = create ? "Create identity" : "Reconnect"
        for _ in 0..<4 {
            if element(button).exists { break }
            app.webViews.firstMatch.swipeUp()
        }
        try wait(30) { self.element(button).exists }
        // Revealing the submit control can place the passphrase above the fold.
        app.webViews.firstMatch.swipeDown()
        app.webViews.firstMatch.swipeDown()
        phase = "unlock-passphrase"
        try type(app.webViews.secureTextFields.firstMatch, passphrase)
        if create {
            phase = "unlock-confirm"
            try require(app.webViews.secureTextFields.count == 2)
            try type(app.webViews.secureTextFields.element(boundBy: 1), passphrase)
        }
        phase = "unlock-submit"
        try click(button)
        phase = "unlock-ready"
        try wait(120) {
            !self.element(button).exists &&
            (self.element("Connect to GChat").exists || self.element("Message or command").exists)
        }
    }

    func allLabels(_ root: XCUIElement) -> [String] {
        root.descendants(matching: .any).allElementsBoundByIndex.map { $0.label }
    }

    func publicObservation() -> [String: Bool] {
        return ["review_invitation": element("Review invitation").exists,
            "create_identity": element("Create identity").exists,
            "reconnect": element("Reconnect").exists,
            "connect_to_gchat": element("Connect to GChat").exists,
            "close_dialog": element("Close dialog").exists,
            "nickname": element("Your nickname in this channel").exists,
            "joined": element("Joined").exists,
            "composer": element("Message or command").exists,
            "invitation": app.webViews.textViews.matching(NSPredicate(format: "label == %@", "Invitation")).firstMatch.exists,
            "continue": element("Continue").exists,
            "webview": app.webViews.firstMatch.exists,
            "foreground": app.state == .runningForeground]
    }

    func row(_ name: String, action: String? = nil) throws -> XCUIElement {
        var selected: XCUIElement?
        try wait(120) {
            for candidate in self.app.webViews.otherElements.allElementsBoundByIndex.reversed() {
                let values = Set(self.allLabels(candidate))
                if values.contains(name) && values.intersection(self.files) == Set([name]) {
                    if let action = action {
                        let button = candidate.buttons.matching(NSPredicate(format: "label == %@", action)).firstMatch
                        if button.exists && button.isHittable { selected = candidate; return true }
                    } else {
                        selected = candidate
                        return true
                    }
                }
            }
            return false
        }
        guard let selected = selected else { throw Failure.observation }
        return selected
    }

    func fileAction(_ name: String, _ action: String) throws {
        files.insert(name)
        let button = app.buttons.matching(NSPredicate(format: "label BEGINSWITH %@", "Files:")).firstMatch
        try wait { button.exists && button.isHittable }
        button.tap()
        let target = try row(name, action: action)
        target.buttons.matching(NSPredicate(format: "label == %@", action)).firstMatch.tap()
        if action != "Save file…" { try click("Close dialog") }
    }

    func request(_ path: String, _ value: [String: Any]) throws -> [String: Any] {
        guard let url = URL(string: endpoint + path) else { throw Failure.protocolBinding }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 20
        request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: value)
        let ready = DispatchSemaphore(value: 0)
        var answer: [String: Any]?
        URLSession.shared.dataTask(with: request) { data, response, error in
            defer { ready.signal() }
            if let error = error as NSError? {
                print("GCHAT_ACCEPTANCE_BRIDGE_TRANSPORT=\(error.code)")
            }
            if let response = response as? HTTPURLResponse, response.statusCode != 200 {
                print("GCHAT_ACCEPTANCE_BRIDGE_HTTP=\(response.statusCode)")
            }
            guard (response as? HTTPURLResponse)?.statusCode == 200,
                  let data = data, data.count <= 196608,
                  let decoded = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return }
            answer = decoded
        }.resume()
        guard ready.wait(timeout: .now() + 25) == .success, let answer = answer else {
            throw Failure.protocolBinding
        }
        return answer
    }

    func perform(_ command: [String: Any]) throws -> Any {
        guard let op = command["op"] as? String else { throw Failure.protocolBinding }
        phase = op
        func string(_ name: String) throws -> String {
            guard let value = command[name] as? String else { throw Failure.protocolBinding }
            return value
        }
        switch op {
        case "ready":
            guard let device = ProcessInfo.processInfo.environment["SIMULATOR_UDID"],
                  UUID(uuidString: device) != nil else { throw Failure.protocolBinding }
            return ["device": device]
        case "finish":
            return true
        case "stop":
            app.terminate()
            try wait(10) { self.app.state == .notRunning }
            return true
        case "unlock":
            try unlock(command["create"] as? Bool == true, try string("passphrase"))
            return true
        case "join_invitation":
            phase = "join-arrival"
            try wait(30) { self.app.state == .runningForeground && self.element("Connect to GChat").exists }
            // First-run notification settings can cover the arrival notice.
            if element("Close dialog").exists { try click("Close dialog") }
            phase = "join-review"
            let invitation = try string("invitation")
            try require(invitation.hasPrefix("gcoms:") && invitation.utf8.count <= 180000)
            let field = app.webViews.textViews.matching(NSPredicate(format: "label == %@", "Invitation")).firstMatch
            try type(field, invitation)
            try require((field.value as? String) == invitation)
            try click("Continue")
            return true
        case "join_accept":
            phase = "join-preview"
            try wait(120) { self.element("Your nickname in this channel").exists }
            phase = "join-input"
            try type(app.webViews.textFields.firstMatch, "MOBILE")
            phase = "join-accept"
            try click("Join")
            return true
        case "join_connected":
            phase = "join-connected"
            try wait(120) { self.element("Message or command").exists || self.element("Joined").exists }
            return element("Joined").exists ? "joined" : "selected"
        case "join_select":
            if command["joined"] as? Bool == true {
                try require(element("Joined").exists)
                try click("Close dialog")
                try click("Channels")
                let channel = app.descendants(matching: .any).matching(NSPredicate(
                    format: "label MATCHES %@", "#?\\s*mobile-release(?:\\s+\\d+)?")).firstMatch
                try wait { channel.exists && channel.isHittable }
                channel.tap()
            }
            phase = "join-ready"
            try wait(30) {
                let close = self.element("Close dialog")
                if self.element("Notifications").exists && close.exists && close.isHittable {
                    close.tap()
                    return false
                }
                return self.element("Message or command").exists
            }
            return true
        case "identity":
            if element("Notifications").exists && element("Close dialog").exists {
                try click("Close dialog")
            }
            phase = "identity-network"
            let network = app.buttons.matching(NSPredicate(format: "label BEGINSWITH %@", "Network:")).firstMatch
            try tapVisible(network)
            phase = "identity-details"
            try tapVisible(element("Your identity"))
            phase = "identity-value"
            var ids = Set<String>()
            var safety = Set<String>()
            try wait {
                let values = Set(self.allLabels(self.app.webViews.firstMatch))
                ids = values.filter { $0.range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil }
                safety = values.filter {
                    $0.range(of: "^[A-Z2-7]{8}( [A-Z2-7]{8}){4}$", options: .regularExpression) != nil
                }
                return ids.count == 1 && safety.count == 1
            }
            let identity = ids.first! + "\n" + safety.first!
            phase = "identity-close"
            try click("Close dialog")
            return identity
        case "send":
            let body = try string("body")
            bodies.insert(body)
            try type(app.webViews.textViews.matching(NSPredicate(format: "label == %@", "Message or command")).firstMatch, body)
            try click("Send")
            return true
        case "received":
            let body = try string("body")
            bodies.insert(body)
            return element(body).exists
        case "delivered":
            let body = try string("body")
            bodies.formUnion(command["known_bodies"] as? [String] ?? [])
            for candidate in app.webViews.otherElements.allElementsBoundByIndex.reversed() {
                let values = Set(allLabels(candidate))
                if values.contains(body) && values.intersection(bodies) == Set([body]) &&
                    values.contains(where: { $0.trimmingCharacters(in: .whitespaces) == "· delivered" }) {
                    return true
                }
            }
            return false
        case "history":
            guard let expected = command["bodies"] as? [String], !expected.isEmpty else {
                throw Failure.protocolBinding
            }
            bodies.formUnion(expected)
            var missing = Set(expected)
            var scrolled = 0
            for _ in 0..<12 {
                missing.subtract(allLabels(app.webViews.firstMatch))
                if missing.isEmpty { break }
                app.webViews.firstMatch.swipeDown()
                scrolled += 1
            }
            try require(missing.isEmpty)
            for _ in 0..<scrolled { app.webViews.firstMatch.swipeUp() }
            return true
        case "file_action":
            try fileAction(try string("name"), try string("action"))
            return true
        case "progress":
            let name = try string("name")
            guard let size = command["size"] as? Int else { throw Failure.protocolBinding }
            files.insert(name)
            for candidate in app.webViews.otherElements.allElementsBoundByIndex.reversed() {
                let values = Set(allLabels(candidate))
                if !values.contains(name) || values.intersection(files) != Set([name]) { continue }
                for value in values {
                    let parts = value.replacingOccurrences(of: ",", with: "").components(separatedBy: " / ")
                    if parts.count == 2 && parts[1] == String(size) + " bytes verified",
                       let verified = Int(parts[0]) { return verified }
                }
            }
            let button = app.buttons.matching(NSPredicate(format: "label BEGINSWITH %@", "Files:")).firstMatch
            try wait(10) { button.exists && button.isHittable }
            button.tap()
            let file = try row(name)
            let complete = allLabels(file).contains { $0.contains(" · complete · ") }
            try click("Close dialog")
            if complete { return size }
            return NSNull()
        case "export":
            let name = try string("name")
            phase = "export-picker"
            try fileAction(name, "Save file…")
            try wait(30) {
                self.element("On My iPhone").exists || self.element("Save").exists ||
                self.element("Export").exists || self.element("Browse").exists
            }
            if element("Browse").exists && element("Browse").isHittable { try click("Browse") }
            if element("On My iPhone").exists && element("On My iPhone").isHittable { try click("On My iPhone") }
            if element("GChat").exists && element("GChat").isHittable { try click("GChat") }
            else if element("Downloads").exists && element("Downloads").isHittable { try click("Downloads") }
            if element("Save").exists { try click("Save") } else { try click("Export") }
            try wait(30) { self.app.webViews.firstMatch.exists }
            if element("Reconnect").exists {
                phase = "export-unlock"
                try unlock(false, passphrase, launch: false)
            }
            phase = "export-result"
            var saved = ""
            try wait(60) {
                saved = self.allLabels(self.app.webViews.firstMatch).first {
                    $0.hasPrefix("Saved to file:")
                } ?? ""
                return !saved.isEmpty
            }
            if element("Close dialog").exists { try click("Close dialog") }
            return String(saved.dropFirst("Saved to ".count))
        default:
            throw Failure.unsupported
        }
    }

    func testRetainedNetworkJourney() throws {
        continueAfterFailure = false
        endpoint = ProcessInfo.processInfo.environment["GCHAT_TEST_BRIDGE_URL"] ?? ""
        token = ProcessInfo.processInfo.environment["GCHAT_TEST_BRIDGE_TOKEN"] ?? ""
        print("GCHAT_ACCEPTANCE_BRIDGE_CONFIGURATION=\(endpoint.hasPrefix("http://127.0.0.1:") && !token.isEmpty ? 1 : 0)")
        try require(endpoint.hasPrefix("http://127.0.0.1:") && !token.isEmpty)
        let end = ProcessInfo.processInfo.systemUptime + 1500
        while ProcessInfo.processInfo.systemUptime < end {
            let command = try request("/next", ["ready": true])
            if command["op"] as? String == "idle" { continue }
            guard let id = command["id"] as? String else { throw Failure.protocolBinding }
            do {
                let value = try perform(command)
                _ = try request("/result", ["id": id, "passed": true, "value": value])
                if command["op"] as? String == "finish" { return }
            } catch {
                _ = try? request("/result", ["id": id, "passed": false, "phase": phase,
                    "observation": publicObservation()])
                // Never attach or print a hierarchy, screenshot, invitation,
                // passphrase, command arguments or raw UI values.
                XCTFail("The retained application's UI command failed.")
                return
            }
        }
        XCTFail("The original mobile test-runner deadline expired.")
    }
}
