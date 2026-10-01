import Foundation
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

    func require(_ value: Bool) throws {
        if !value { throw Failure.observation }
    }

    func wait(_ seconds: TimeInterval = 60, _ check: @escaping () -> Bool) throws {
        let result = XCTWaiter.wait(for: [XCTNSPredicateExpectation(
            predicate: NSPredicate { _, _ in check() }, object: nil)], timeout: seconds)
        try require(result == .completed)
    }

    func element(_ label: String) -> XCUIElement {
        app.descendants(matching: .any).matching(NSPredicate(format: "label == %@", label)).firstMatch
    }

    func click(_ label: String) throws {
        let target = element(label)
        try wait { target.exists && target.isHittable }
        target.tap()
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
        for _ in 0..<4 {
            if field.isHittable { break }
            app.webViews.firstMatch.swipeUp()
        }
        try require(field.isHittable)
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
        field.typeText(value)
        try dismissKeyboard()
        if field.elementType == .secureTextField {
            let label = field.label
            try require(!label.isEmpty)
            try passphraseVisibility("Show passphrase")
            let revealed = app.webViews.textFields.matching(NSPredicate(format: "label == %@", label)).firstMatch
            try wait(10) { revealed.exists && (revealed.value as? String) == value }
            try passphraseVisibility("Hide passphrase")
            try wait(10) { field.exists }
        } else {
            try require(!((field.value as? String) ?? "").isEmpty)
        }
    }

    func passphraseVisibility(_ title: String) throws {
        let button = app.webViews.buttons[title].firstMatch
        let main = app.webViews.otherElements.matching(NSPredicate(format: "label == %@", "main")).firstMatch
        try wait(10) { button.exists && main.exists }
        let deadline = ProcessInfo.processInfo.systemUptime + 10
        while button.exists && (!button.isHittable || !main.frame.contains(button.frame))
                && ProcessInfo.processInfo.systemUptime < deadline {
            if button.frame.midY < main.frame.minY {
                app.webViews.firstMatch.swipeDown()
            } else {
                app.webViews.firstMatch.swipeUp()
            }
        }
        try require(button.isHittable && main.frame.contains(button.frame))
        button.tap()
    }

    func unlock(_ create: Bool, _ value: String) throws {
        passphrase = value
        app.launch()
        let button = create ? "Create identity" : "Reconnect"
        try wait(30) { self.element(button).exists }
        try type(app.webViews.secureTextFields.firstMatch, passphrase)
        if create {
            try require(app.webViews.secureTextFields.count == 2)
            try type(app.webViews.secureTextFields.element(boundBy: 1), passphrase)
        }
        try click(button)
        try wait(120) {
            !self.element(button).exists &&
            (self.element("Connect to GChat").exists || self.element("Message or command").exists)
        }
    }

    func allLabels(_ root: XCUIElement) -> [String] {
        root.descendants(matching: .any).allElementsBoundByIndex.map { $0.label }
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
        URLSession.shared.dataTask(with: request) { data, response, _ in
            defer { ready.signal() }
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
        func string(_ name: String) throws -> String {
            guard let value = command[name] as? String else { throw Failure.protocolBinding }
            return value
        }
        switch op {
        case "ready", "finish":
            return true
        case "stop":
            app.terminate()
            try wait(10) { self.app.state == .notRunning }
            return true
        case "unlock":
            try unlock(command["create"] as? Bool == true, try string("passphrase"))
            return true
        case "join":
            try click("Review invitation")
            try wait(120) { self.element("Your nickname in this channel").exists }
            try type(app.webViews.textFields.firstMatch, "mobile")
            try click("Join")
            try wait(120) { self.element("Message or command").exists }
            return true
        case "identity":
            let network = app.buttons.matching(NSPredicate(format: "label BEGINSWITH %@", "Network:")).firstMatch
            try wait { network.exists && network.isHittable }
            network.tap()
            try click("Your identity")
            let values = Set(allLabels(app.webViews.firstMatch))
            let ids = values.filter { $0.range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil }
            let safety = values.filter {
                $0.range(of: "^[A-Z2-7]{8}( [A-Z2-7]{8}){4}$", options: .regularExpression) != nil
            }
            try require(ids.count == 1 && safety.count == 1)
            let identity = ids.first! + "\n" + safety.first!
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
            return NSNull()
        case "export":
            let name = try string("name")
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
            if element("Reconnect").exists { try unlock(false, passphrase) }
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
                _ = try? request("/result", ["id": id, "passed": false])
                // Never attach or print a hierarchy, screenshot, invitation,
                // passphrase, command arguments or raw UI values.
                XCTFail("The retained application's UI command failed.")
                return
            }
        }
        XCTFail("The original mobile test-runner deadline expired.")
    }
}
