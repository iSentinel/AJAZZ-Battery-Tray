import AppKit
import Foundation
import Darwin
import IOKit.hid
import ServiceManagement

/// Reads battery and can set only the dock's documented on-board clock.
enum ApexBattery {
    enum Status: Equatable {
        case battery(Int)
        case notConnected
        case unavailable
        case accessUnknown
        case timedOut
        case unsupportedCollection

        var compatibleReceiverPresent: Bool? {
            switch self {
            case .battery, .unavailable: return true
            case .notConnected: return false
            case .accessUnknown, .unsupportedCollection, .timedOut: return nil
            }
        }
    }

    private static let vendorID = 0x3151
    private static let productID = 0x5007
    private static let usagePage = 0xFFFF
    private static let usage = 0x02

    /// Decode a feature report returned for report ID 0x05.
    static func parse(_ report: [UInt8]) -> Int? {
        let value = report.withUnsafeBufferPointer {
            AjazzBatteryPercent($0.baseAddress, $0.count)
        }
        return value < 0 ? nil : Int(value)
    }

    static func read(trace: ((String) -> Void)? = nil) -> Status {
        let lease = AjazzAcquireIoLease()
        guard lease >= 0 else {
            trace?("I/O lease unavailable; no request")
            return .accessUnknown
        }
        defer { AjazzReleaseIoLease(lease) }
        let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
        let criteria: [String: Any] = [
            kIOHIDVendorIDKey as String: vendorID,
            kIOHIDProductIDKey as String: productID
        ]
        IOHIDManagerSetDeviceMatching(manager, criteria as CFDictionary)
        trace?("STEP: manager.open")
        let managerResult = IOHIDManagerOpen(manager, IOOptionBits(kIOHIDOptionsTypeNone))
        trace?(String(format: "manager.open=0x%08x", UInt32(bitPattern: managerResult)))
        guard managerResult == kIOReturnSuccess else { return .accessUnknown }
        defer { IOHIDManagerClose(manager, IOOptionBits(kIOHIDOptionsTypeNone)) }

        trace?("STEP: receiver.enumerate")
        let found = IOHIDManagerCopyDevices(manager) as? Set<IOHIDDevice> ?? []
        trace?("receiver.hid_count=\(found.count)")
        guard !found.isEmpty else { return .notConnected }
        var matched = false
        var opened = false
        for device in found where matchesVendorUsage(device) {
            matched = true
            if let trace = trace {
                let revision = (IOHIDDeviceGetProperty(device, "VersionNumber" as CFString) as? NSNumber)?.stringValue ?? "unknown"
                let size = (IOHIDDeviceGetProperty(device, "MaxFeatureReportSize" as CFString) as? NSNumber)?.stringValue ?? "unknown"
                trace("collection.revision=\(revision) feature_bytes=\(size)")
            }
            let result = poll(device, trace: trace)
            opened = opened || result.opened
            if let value = result.percent { return .battery(value) }
        }
        return noSampleStatus(matched: matched, opened: opened)
    }

    static func noSampleStatus(matched: Bool, opened: Bool) -> Status {
        if !matched { return .unsupportedCollection }
        return opened ? .unavailable : .accessUnknown
    }

    /// Builds the documented 64-byte macOS feature payload for dock RTC updates.
    static func makeClockPayload(_ date: Date) -> [UInt8] {
        let fields = Calendar.current.dateComponents(
            [.year, .month, .day, .hour, .minute, .second], from: date)
        let year = fields.year ?? 2000
        var payload = [UInt8](repeating: 0, count: 64)
        payload[0] = 0x28
        payload[7] = 0xD7
        payload[8] = UInt8((year >> 8) & 0xFF)
        payload[9] = UInt8(year & 0xFF)
        payload[10] = UInt8(fields.month ?? 1)
        payload[11] = UInt8(fields.day ?? 1)
        payload[12] = UInt8(fields.hour ?? 0)
        payload[13] = UInt8(fields.minute ?? 0)
        payload[14] = UInt8(fields.second ?? 0)
        return payload
    }

    /// Transfers local wall-clock time to the same vendor HID collection.
    static func syncClock() -> Bool {
        let lease = AjazzAcquireIoLease()
        guard lease >= 0 else { return false }
        defer { AjazzReleaseIoLease(lease) }
        let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
        let criteria: [String: Any] = [
            kIOHIDVendorIDKey as String: vendorID,
            kIOHIDProductIDKey as String: productID
        ]
        IOHIDManagerSetDeviceMatching(manager, criteria as CFDictionary)
        guard IOHIDManagerOpen(manager, IOOptionBits(kIOHIDOptionsTypeNone)) == kIOReturnSuccess else {
            return false
        }
        defer { IOHIDManagerClose(manager, IOOptionBits(kIOHIDOptionsTypeNone)) }
        guard let found = IOHIDManagerCopyDevices(manager) as? Set<IOHIDDevice> else {
            return false
        }
        for device in found where matchesVendorUsage(device) {
            if sendClock(device) { return true }
        }
        return false
    }


    /// Gate every SetReport call to supported telemetry or RTC packets.
    static func validClockFrame(_ data: [UInt8]) -> Bool {
        guard data.count == 64, data[0] == 0x28, data[7] == 0xD7,
              data[1..<7].allSatisfy({ $0 == 0 }),
              data[15...].allSatisfy({ $0 == 0 }) else { return false }
        let year = Int(data[8]) * 256 + Int(data[9])
        let month = Int(data[10])
        let day = Int(data[11])
        let hour = Int(data[12])
        let minute = Int(data[13])
        let second = Int(data[14])
        guard (2020...2099).contains(year), (1...12).contains(month) else {
            return false
        }
        let leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)
        let days = [31, leap ? 29 : 28, 31, 30, 31, 30,
                    31, 31, 30, 31, 30, 31]
        return day >= 1 && day <= days[month - 1] &&
               hour < 24 && minute < 60 && second < 60
    }

    static func validTelemetryFrame(_ data: [UInt8]) -> Bool {
        return (65...256).contains(data.count) && data[0] == 0 &&
               data[1] == 0xF7 && data[2...].allSatisfy({ $0 == 0 })
    }

    private static func sendClock(_ device: IOHIDDevice) -> Bool {
        guard IOHIDDeviceOpen(device, IOOptionBits(kIOHIDOptionsTypeNone)) == kIOReturnSuccess else {
            return false
        }
        defer { IOHIDDeviceClose(device, IOOptionBits(kIOHIDOptionsTypeNone)) }
        let payload = makeClockPayload(Date())
        guard validClockFrame(payload) else { return false }
        let status = payload.withUnsafeBufferPointer { data in
            IOHIDDeviceSetReport(device, kIOHIDReportTypeFeature,
                                 CFIndex(payload[0]), data.baseAddress!, data.count)
        }
        return status == kIOReturnSuccess
    }


    /// Reads public HID product metadata without sending a device command.
    static func diagnostics() -> String {
        let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
        let criteria: [String: Any] = [
            kIOHIDVendorIDKey as String: vendorID,
            kIOHIDProductIDKey as String: productID
        ]
        IOHIDManagerSetDeviceMatching(manager, criteria as CFDictionary)
        guard IOHIDManagerOpen(manager, IOOptionBits(kIOHIDOptionsTypeNone)) == kIOReturnSuccess else {
            return "Unable to open HID manager."
        }
        defer { IOHIDManagerClose(manager, IOOptionBits(kIOHIDOptionsTypeNone)) }
        guard let found = IOHIDManagerCopyDevices(manager) as? Set<IOHIDDevice> else {
            return "No compatible receiver detected."
        }
        let matched = found.filter { matchesVendorUsage($0) }
        let product = matched.first.flatMap {
            IOHIDDeviceGetProperty($0, kIOHIDProductKey as CFString) as? String
        } ?? "unknown"
        return "VID:PID: 3151:5007\n" +
               "Product name: \(product)\n" +
               "Matching vendor HID collections: \(matched.count)\n" +
               "Usage page / usage: FFFF / 0002\n" +
               "Firmware / display capabilities: not queried\n" +
               "No serial numbers or private USB paths are shown."
    }

    private static func matchesVendorUsage(_ device: IOHIDDevice) -> Bool {
        let page = (IOHIDDeviceGetProperty(device, kIOHIDPrimaryUsagePageKey as CFString) as? NSNumber)?.intValue
        let item = (IOHIDDeviceGetProperty(device, kIOHIDPrimaryUsageKey as CFString) as? NSNumber)?.intValue
        return page == usagePage && item == usage
    }

    private static func poll(_ device: IOHIDDevice, trace: ((String) -> Void)? = nil) -> (opened: Bool, percent: Int?) {
        trace?("STEP: collection.open")
        let opened = IOHIDDeviceOpen(device, IOOptionBits(kIOHIDOptionsTypeNone))
        trace?(String(format: "collection.open=0x%08x", UInt32(bitPattern: opened)))
        guard opened == kIOReturnSuccess else {
            return (false, nil)
        }
        defer { IOHIDDeviceClose(device, IOOptionBits(kIOHIDOptionsTypeNone)) }
        // Match the receiver's Windows request: report ID 0, first payload byte 0xF7.
        for count in [65, 67] {
            var request = [UInt8](repeating: 0, count: count)
            request[1] = 0xF7
            guard validTelemetryFrame(request) else { continue }
            trace?("STEP: F7.set.length=\(count)")
            let write = request.withUnsafeBufferPointer { data in
                IOHIDDeviceSetReport(device, kIOHIDReportTypeFeature, 0, data.baseAddress!, data.count)
            }
            trace?(String(format: "F7.set.length=%d result=0x%08x", count, UInt32(bitPattern: write)))
            guard write == kIOReturnSuccess else { continue }
            Thread.sleep(forTimeInterval: 0.03)
            var reply = [UInt8](repeating: 0, count: count)
            reply[0] = 0x05
            var actualLength: CFIndex = count
            trace?("STEP: 05.get.length=\(count)")
            let read = reply.withUnsafeMutableBufferPointer { data in
                IOHIDDeviceGetReport(device, kIOHIDReportTypeFeature, 5, data.baseAddress!, &actualLength)
            }
            trace?(String(format: "05.get.result=0x%08x length=%d", UInt32(bitPattern: read), Int(actualLength)))
            if read == kIOReturnSuccess && (0...count).contains(actualLength) {
                trace?("05.reply.first_bytes=" + reply.prefix(min(8, Int(actualLength)))
                    .map { String(format: "%02x", $0) }.joined(separator: " "))
                if let trace = trace {
                    let gate = reply.withUnsafeBufferPointer {
                        String(cString: AjazzF7ReplyGateName($0.baseAddress, Int(actualLength)))
                    }
                    trace("F7 policy gate: " + gate)
                }
            }
            if read == kIOReturnSuccess && (3...count).contains(actualLength),
               let percent = parse(Array(reply.prefix(Int(actualLength)))) {
                return (true, percent)
            }
        }
        return (true, nil)
    }
}

/// Session provenance only: the Apple reader has no stable receiver identity.
struct ApexSessionObservation {
    private(set) var lastVerified: Date?

    mutating func observe(_ status: ApexBattery.Status, at time: Date) {
        if case .battery(let value) = status, (1...100).contains(value) {
            lastVerified = time
        } else if status == .notConnected {
            lastVerified = nil
        }
    }

    func presentation(_ status: ApexBattery.Status, at now: Date) -> ApexBattery.Status {
        guard case .battery(let value) = status else { return status }
        guard (1...100).contains(value), let stamp = lastVerified,
              AjazzSampleAgeIsCurrent(now.timeIntervalSince(stamp)) else { return .unavailable }
        return status
    }
}

/// Native AppKit menu bar user interface, without a Dock window.
final class TrayController: NSObject, NSApplicationDelegate, NSMenuDelegate {
    private var statusItem: NSStatusItem!
    private var statusMenu: NSMenu!
    private var detailItem: NSMenuItem!
    private var clockItem: NSMenuItem!
    private var lastClockAttempt = Date.distantPast
    private var receiverWasPresent = false
    private var manualClockSync = false
    private var timer: Timer?
    private var polling = false
    private var closing = false
    private let diagnosticSession = AjazzSessionCreate()
    private var sessionStatusItem: NSMenuItem?
    private var sessionStartItem: NSMenuItem?
    private var sessionCaptureItems = [NSMenuItem]()
    private var sessionSaveItem: NSMenuItem?
    private var sessionDiscardItem: NSMenuItem?
    private var diagnosticRunning = false
    private var diagnosticCancellation: ApexWorkerCancellation?
    private var runDiagnosticItem: NSMenuItem?
    private var cancelDiagnosticItem: NSMenuItem?
    private var activeCancellation: ApexWorkerCancellation?
    private let isolatedPolling = CommandLine.arguments == [
        CommandLine.arguments[0], "--experimental-isolated-polling"
    ]
    private let batteryHistory = BatteryHistoryWriter()
    private let batteryAlerts = BatteryAlertPolicy()
    private var historyWindow: BatteryHistoryWindowController?
    private var bluetoothWindow: BluetoothBatteryWindowController?
    private var startupMenuItem: NSMenuItem?
    private var intervalItems = [NSMenuItem]()
    private var displayedStatus = ApexBattery.Status.accessUnknown
    private var sessionObservation = ApexSessionObservation()
    private var lastClockSent: Bool?
    private var journalFailedWrites: UInt64 = 0

    deinit { AjazzSessionDestroy(diagnosticSession) }

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        statusItem = NSStatusBar.system.statusItem(
            withLength: NSStatusItem.variableLength)
        statusItem.button?.title = "🔋?"
        NSApp.applicationIconImage = TrayAppearance.appIcon(TrayAppearance.choice("ApplicationIconColor"))
        buildStatusMenu()
        recordJournalEvent(AjazzEventStarted, AjazzReasonNone)
        if isolatedPolling { recordJournalEvent(AjazzEventIsolatedPollingEnabled, AjazzReasonNone) }
        configureTimer()
        refresh()
    }

    /// Record closed GUI events; journal failure never prevents normal operation.
    private func recordJournalEvent(_ event: AjazzOperationalEvent, _ reason: AjazzOperationalReason,
                                    durationMs: Int64 = -1) {
        let support = FileManager.default.urls(for: .applicationSupportDirectory,
                                                in: .userDomainMask).first
        let ok = support?.withUnsafeFileSystemRepresentation { path in
            AjazzJournalEditionTimedEvent(path, false, event, reason, time(nil), durationMs)
        } ?? false
        if !ok && journalFailedWrites < UInt64.max { journalFailedWrites += 1 }
    }

    func applicationWillTerminate(_ notification: Notification) {
        recordJournalEvent(AjazzEventStopped, AjazzReasonNone)
    }

    private func command(_ key: String, _ action: Selector) -> NSMenuItem {
        let item = NSMenuItem(title: AppText.text(key),
                              action: action, keyEquivalent: "")
        item.target = self
        return item
    }

    private func buildStatusMenu() {
        statusMenu = NSMenu(title: "AJAZZ Battery Tray")
        statusMenu.delegate = self
        detailItem = NSMenuItem(
            title: AppText.text("Checking 2.4 GHz receiver…"),
            action: nil, keyEquivalent: "")
        detailItem.isEnabled = false
        statusMenu.addItem(detailItem)
        statusMenu.addItem(.separator())
        statusMenu.addItem(command("Refresh now", #selector(refresh)))
        statusMenu.addItem(command("Battery history chart...",
                                   #selector(showBatteryHistory)))
        statusMenu.addItem(command("Check connected Bluetooth battery...",
                                   #selector(showBluetoothBattery)))
        statusMenu.addItem(command("Sync dock time now", #selector(syncClockNow)))
        clockItem = NSMenuItem(title: "", action: nil, keyEquivalent: "")
        clockItem.isEnabled = false
        updateClockStatus()
        statusMenu.addItem(clockItem)
        statusMenu.addItem(.separator())
        let settings = NSMenuItem(title: AppText.text("Settings"),
                                  action: nil, keyEquivalent: "")
        settings.submenu = buildSettingsMenu()
        statusMenu.addItem(settings)
        let diagnostics = NSMenuItem(title: AppText.text("Diagnostics"),
                                     action: nil, keyEquivalent: "")
        diagnostics.submenu = buildDiagnosticsMenu()
        statusMenu.addItem(diagnostics)
        statusMenu.addItem(.separator())
        statusMenu.addItem(command("Quit AJAZZ Battery Tray", #selector(quit)))
        statusItem.menu = statusMenu
        refreshStartupMenu()
    }

    private func buildDiagnosticsMenu() -> NSMenu {
        let menu = NSMenu(title: AppText.text("Diagnostics"))
        menu.autoenablesItems = false
        menu.addItem(command("Device diagnostics...", #selector(showDiagnostics)))
        let run = command("Run HID diagnostics...", #selector(runHIDDiagnostics))
        let cancel = command("Cancel HID diagnostics", #selector(cancelHIDDiagnostics))
        runDiagnosticItem = run
        cancelDiagnosticItem = cancel
        menu.addItem(run)
        menu.addItem(cancel)
        updateDiagnosticMenu()
        let sessionItem = NSMenuItem(title: AppText.text("Diagnostic session"), action: nil, keyEquivalent: "")
        sessionItem.submenu = buildDiagnosticSessionMenu()
        menu.addItem(sessionItem)
        menu.addItem(command("Copy diagnostic report", #selector(copyDeviceReport)))
        menu.addItem(command("Open battery history folder...",
                              #selector(openHistoryFolder)))
        return menu
    }

    private func buildDiagnosticSessionMenu() -> NSMenu {
        let menu = NSMenu(title: AppText.text("Diagnostic session"))
        menu.autoenablesItems = false
        let count = NSMenuItem(title: "", action: nil, keyEquivalent: "")
        count.isEnabled = false
        sessionStatusItem = count
        menu.addItem(count)
        let start = command("Start diagnostic session", #selector(startDiagnosticSession))
        sessionStartItem = start
        menu.addItem(start)
        sessionCaptureItems = ["Capture baseline", "Mark 2.4 GHz selected",
            "Mark Bluetooth selected", "Mark sleep", "Mark wake", "Capture another snapshot"]
            .enumerated().map { index, key in
                let item = command(key, #selector(captureDiagnosticMarker(_:)))
                item.tag = index
                menu.addItem(item)
                return item
            }
        let save = command("Save diagnostic session...", #selector(saveDiagnosticSession))
        sessionSaveItem = save
        menu.addItem(save)
        let discard = command("Discard diagnostic session", #selector(discardDiagnosticSession))
        sessionDiscardItem = discard
        menu.addItem(discard)
        updateSessionMenu()
        return menu
    }

    private func updateSessionMenu() {
        let active = AjazzSessionActive(diagnosticSession)
        let count = AjazzSessionCount(diagnosticSession)
        sessionStatusItem?.title = AppText.text("Snapshots") + ": \(count)/32"
        sessionStartItem?.isEnabled = !closing && !active && diagnosticSession != nil
        for item in sessionCaptureItems { item.isEnabled = !closing && active && count < 32 }
        sessionSaveItem?.isEnabled = !closing && active && count >= 2
        sessionDiscardItem?.isEnabled = !closing && active
    }

    @objc private func startDiagnosticSession() {
        guard !closing else { return }
        AjazzSessionStart(diagnosticSession)
        updateSessionMenu()
    }

    @objc private func captureDiagnosticMarker(_ sender: NSMenuItem) {
        guard (0...5).contains(sender.tag), !closing else { return }
        addSessionReport(diagnosticSnapshot(), marker: UInt32(sender.tag))
    }

    private func sessionMessage(_ key: String) {
        NSApp.activate(ignoringOtherApps: true)
        let alert = NSAlert()
        alert.messageText = AppText.text(key)
        alert.runModal()
    }

    private func addSessionReport(_ report: String, marker: UInt32) {
        guard !closing, AjazzSessionActive(diagnosticSession) else { return }
        let bytes = Array(report.utf8)
        let added = bytes.withUnsafeBufferPointer {
            AjazzSessionAdd(diagnosticSession, marker, $0.baseAddress, $0.count)
        }
        updateSessionMenu()
        sessionMessage(added ? "Snapshot added" : "Snapshot not added; wait a second or check session limits")
    }

    @objc private func discardDiagnosticSession() {
        guard !closing, AjazzSessionActive(diagnosticSession) else { return }
        NSApp.activate(ignoringOtherApps: true)
        let alert = NSAlert()
        alert.messageText = AppText.text("Discard all session snapshots?")
        alert.addButton(withTitle: AppText.text("Discard diagnostic session"))
        alert.addButton(withTitle: AppText.text("Close diagnostic report"))
        if alert.runModal() == .alertFirstButtonReturn && !closing {
            AjazzSessionClear(diagnosticSession)
            updateSessionMenu()
        }
    }

    @objc private func saveDiagnosticSession() {
        guard !closing, AjazzSessionCount(diagnosticSession) >= 2 else { return }
        NSApp.activate(ignoringOtherApps: true)
        let panel = NSSavePanel()
        panel.nameFieldStringValue = "ajazz-macos-diagnostic-session.zip"
        panel.allowedFileTypes = ["zip"]
        panel.message = AppText.text("Session may contain reply bytes. Review before sharing.")
        guard panel.runModal() == .OK, let url = panel.url, !closing else { return }
        if !url.path.withCString({ AjazzSessionSave(diagnosticSession, $0) }) {
            sessionMessage("Unable to save diagnostic report")
        }
    }

    private func updateDiagnosticMenu() {
        runDiagnosticItem?.isEnabled = !diagnosticRunning && !closing
        cancelDiagnosticItem?.isEnabled = diagnosticRunning && !closing &&
            diagnosticCancellation?.isCancelled == false
    }

    @objc private func cancelHIDDiagnostics() {
        guard diagnosticRunning, !closing, let token = diagnosticCancellation,
              !token.isCancelled else { return }
        token.cancel()
        // Keep single-flight until the supervisor confirms the child is reaped.
        renderStatus(displayedStatus)
    }

    private func appearanceMenu(_ title: String, key: String) -> NSMenuItem {
        let parent = NSMenuItem(title: AppText.text(title), action: nil, keyEquivalent: "")
        let menu = NSMenu()
        for color in TrayAppearance.choices {
            let item = command(color.capitalized, #selector(selectAppearance(_:)))
            item.representedObject = [key, color]
            item.state = TrayAppearance.choice(key) == color ? .on : .off
            if key == "ApplicationIconColor", let image = TrayAppearance.appIcon(color) {
                image.size = NSSize(width: 16, height: 16)
                item.image = image
            } else if key == "TrayIconColor" {
                item.image = TrayAppearance.image(level: 83, choice: color, mouseStyle: true)
            }
            menu.addItem(item)
        }
        parent.submenu = menu
        return parent
    }

    @objc private func selectAppearance(_ sender: NSMenuItem) {
        guard let value = sender.representedObject as? [String], value.count == 2,
              ["ApplicationIconColor", "TrayIconColor"].contains(value[0]),
              TrayAppearance.choices.contains(value[1]) else { return }
        UserDefaults.standard.set(value[1], forKey: value[0])
        if value[0] == "ApplicationIconColor" {
            NSApp.applicationIconImage = TrayAppearance.appIcon(value[1])
        }
        buildStatusMenu()
        renderStatus(displayedStatus)
    }

    @objc private func toggleTrayStyle() {
        UserDefaults.standard.set(!TrayAppearance.mouseStyle(), forKey: "MouseTrayIcon")
        buildStatusMenu()
        renderStatus(displayedStatus)
    }

    private func buildSettingsMenu() -> NSMenu {
        let menu = NSMenu(title: AppText.text("Settings"))
        menu.addItem(appearanceMenu("Application icon", key: "ApplicationIconColor"))
        menu.addItem(appearanceMenu("Tray icon color", key: "TrayIconColor"))
        let style = command("Mouse-shaped tray icon", #selector(toggleTrayStyle))
        style.state = TrayAppearance.mouseStyle() ? .on : .off
        menu.addItem(style)
        let notifications = NSMenuItem(title: AppText.text("Notifications"),
                                       action: nil, keyEquivalent: "")
        notifications.submenu = buildNotificationsMenu()
        menu.addItem(notifications)
        let interval = NSMenuItem(title: AppText.text("Refresh interval"),
                                  action: nil, keyEquivalent: "")
        interval.submenu = buildIntervalMenu()
        menu.addItem(interval)
        let auto = command("Auto-sync dock clock (5 min)",
                           #selector(toggleClockSync(_:)))
        auto.state = autoClockEnabled ? .on : .off
        menu.addItem(auto)
        let history = command("Record battery history", #selector(toggleBatteryHistory(_:)))
        history.state = historyEnabled ? .on : .off
        menu.addItem(history)
        let startup = command("Start at login", #selector(toggleLoginStartup(_:)))
        startupMenuItem = startup
        menu.addItem(startup)
        menu.addItem(command("Open Login Items settings...",
                              #selector(openLoginItemsSettings)))
        menu.addItem(.separator())
        let language = NSMenuItem(title: AppText.text("Language"),
                                  action: nil, keyEquivalent: "")
        language.submenu = buildLanguageMenu()
        menu.addItem(language)
        return menu
    }

    private func buildNotificationsMenu() -> NSMenu {
        let menu = NSMenu(title: AppText.text("Notifications"))
        let low = command("Low battery notifications",
                          #selector(toggleLowBatteryAlerts(_:)))
        low.state = lowAlertsEnabled ? .on : .off
        menu.addItem(low)
        let thresholds = NSMenuItem(
            title: AppText.text("Battery notification thresholds"),
            action: nil, keyEquivalent: "")
        let levels = NSMenu()
        for threshold in [50, 25, 10] {
            let item = NSMenuItem(
                title: AppText.format("Below %d%%", threshold),
                action: #selector(toggleBatteryThreshold(_:)), keyEquivalent: "")
            item.tag = threshold
            item.target = self
            item.state = thresholdEnabled(threshold) ? .on : .off
            levels.addItem(item)
        }
        thresholds.submenu = levels
        menu.addItem(thresholds)
        let disconnect = command("Notify on receiver disconnect",
                                  #selector(toggleDisconnectAlerts(_:)))
        disconnect.state = disconnectAlertsEnabled ? .on : .off
        menu.addItem(disconnect)
        return menu
    }

    private func buildIntervalMenu() -> NSMenu {
        let menu = NSMenu()
        intervalItems = []
        for seconds in [15, 30, 60, 120] {
            let item = NSMenuItem(
                title: AppText.format("%d seconds", seconds),
                action: #selector(changeInterval(_:)), keyEquivalent: "")
            item.tag = seconds
            item.target = self
            intervalItems.append(item)
            menu.addItem(item)
        }
        return menu
    }

    private func buildLanguageMenu() -> NSMenu {
        let menu = NSMenu()
        for (code, title) in [("en", "English"), ("ru", "Русский"),
                              ("uk", "Українська")] {
            let item = NSMenuItem(title: title,
                                  action: #selector(selectLanguage(_:)),
                                  keyEquivalent: "")
            item.target = self
            item.representedObject = code
            item.state = code == AppText.language ? .on : .off
            menu.addItem(item)
        }
        return menu
    }

    @objc private func selectLanguage(_ sender: NSMenuItem) {
        guard let code = sender.representedObject as? String else { return }
        AppText.choose(code)
        buildStatusMenu()
        configureTimer()
        renderStatus(displayedStatus)
        historyWindow?.applyLanguage()
        bluetoothWindow?.applyLanguage()
    }

    private func configureTimer() {
        timer?.invalidate()
        let seconds = UserDefaults.standard.integer(forKey: "PollSeconds")
        let interval = [15, 30, 60, 120].contains(seconds) ? seconds : 30
        timer = Timer.scheduledTimer(timeInterval: TimeInterval(interval), target: self,
                                     selector: #selector(refresh), userInfo: nil, repeats: true)
        intervalItems.forEach { $0.state = $0.tag == interval ? .on : .off }
    }

    @objc private func changeInterval(_ sender: NSMenuItem) {
        UserDefaults.standard.set(sender.tag, forKey: "PollSeconds")
        configureTimer()
        refresh()
    }

    private var historyEnabled: Bool {
        if UserDefaults.standard.object(forKey: "RecordBatteryHistory") == nil {
            return true
        }
        return UserDefaults.standard.bool(forKey: "RecordBatteryHistory")
    }

    @objc private func showBatteryHistory() {
        if historyWindow == nil {
            historyWindow = BatteryHistoryWindowController(file: batteryHistory.file)
        }
        historyWindow?.refresh()
        historyWindow?.showWindow(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    @objc private func openHistoryFolder() {
        NSWorkspace.shared.open(batteryHistory.directory)
    }

    @objc private func toggleBatteryHistory(_ sender: NSMenuItem) {
        let enabled = !historyEnabled
        UserDefaults.standard.set(enabled, forKey: "RecordBatteryHistory")
        sender.state = enabled ? .on : .off
    }

    private var lowAlertsEnabled: Bool {
        UserDefaults.standard.bool(forKey: "NotifyLowBattery")
    }

    private var disconnectAlertsEnabled: Bool {
        UserDefaults.standard.bool(forKey: "NotifyOnDisconnect")
    }

    private func thresholdEnabled(_ threshold: Int) -> Bool {
        let key = "AlertBelow\(threshold)"
        if UserDefaults.standard.object(forKey: key) == nil { return true }
        return UserDefaults.standard.bool(forKey: key)
    }

    private var selectedBatteryThresholds: Set<Int> {
        Set([50, 25, 10].filter { thresholdEnabled($0) })
    }

    @objc private func toggleBatteryThreshold(_ sender: NSMenuItem) {
        let enabled = !thresholdEnabled(sender.tag)
        UserDefaults.standard.set(enabled, forKey: "AlertBelow\(sender.tag)")
        sender.state = enabled ? .on : .off
    }

    @objc private func toggleLowBatteryAlerts(_ sender: NSMenuItem) {
        let enabled = !lowAlertsEnabled
        UserDefaults.standard.set(enabled, forKey: "NotifyLowBattery")
        sender.state = enabled ? .on : .off
        if enabled { BatteryLocalNotifications.requestPermission() }
    }

    @objc private func toggleDisconnectAlerts(_ sender: NSMenuItem) {
        let enabled = !disconnectAlertsEnabled
        UserDefaults.standard.set(enabled, forKey: "NotifyOnDisconnect")
        sender.state = enabled ? .on : .off
        if enabled { BatteryLocalNotifications.requestPermission() }
    }

    private var autoClockEnabled: Bool {
        if UserDefaults.standard.object(forKey: "AutomaticDockClockSync") == nil {
            return true
        }
        return UserDefaults.standard.bool(forKey: "AutomaticDockClockSync")
    }

    @objc private func toggleClockSync(_ sender: NSMenuItem) {
        let enabled = !autoClockEnabled
        UserDefaults.standard.set(enabled, forKey: "AutomaticDockClockSync")
        sender.state = enabled ? .on : .off
        if enabled { syncClockNow() }
    }

    private func diagnosticSnapshot() -> String {
        let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"]
            as? String ?? "unknown"
        let build = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "unknown"
        let last = ApexWorkerReply(sessionObservation.presentation(displayedStatus, at: Date()))
        let battery = last.percent.map { String($0) + "%" } ?? "unknown"
        let sample = sessionObservation.lastVerified.map {
            ISO8601DateFormatter().string(from: $0)
        } ?? "never"
        return "AJAZZ Battery Tray diagnostic report\n" +
            "Report schema: apple-menu-v1\n" +
            "Version: \(version) (\(build))\n" +
            "UTC: \(ISO8601DateFormatter().string(from: Date(timeIntervalSince1970: floor(Date().timeIntervalSince1970))))\n" +
            "macOS: \(ProcessInfo.processInfo.operatingSystemVersionString)\n" +
            "VID:PID: 3151:5007; usage FFFF:0002\n" +
            "Last ordinary status: \(last.state); battery: \(battery)\n" +
            "Last verified USB UTC (session): \(sample)\n" +
            "Polling active: \(polling); isolated: \(isolatedPolling)\n" +
            "Operational journal failed writes (process): \(journalFailedWrites)\n" +
            (bluetoothWindow?.diagnosticSummary ?? "Bluetooth discovery: not requested\n" +
                "Bluetooth manual 180F/2A19 pending: false\nBluetooth last manual read: not requested") + "\n" +
            "No serial numbers, device paths or Bluetooth addresses collected."
    }

    private func copyReport(_ report: String) {
        let clipboard = NSPasteboard.general
        clipboard.clearContents()
        if !clipboard.setString(report, forType: .string) {
            let alert = NSAlert()
            alert.messageText = AppText.text("Unable to copy diagnostic report")
            alert.informativeText = AppText.text("The macOS clipboard is unavailable.")
            alert.alertStyle = .warning
            alert.runModal()
        }
    }

    @objc private func copyDeviceReport() { copyReport(diagnosticSnapshot()) }

    private func reviewReport(_ report: String) {
        NSApp.activate(ignoringOtherApps: true)
        let alert = NSAlert()
        alert.messageText = AppText.text("AJAZZ APEX — Device diagnostics")
        let scroll = NSScrollView(frame: NSRect(x: 0, y: 0, width: 470, height: 260))
        let view = NSTextView(frame: scroll.bounds)
        view.string = report
        view.isEditable = false
        view.isSelectable = true
        view.isVerticallyResizable = true
        view.autoresizingMask = [.width]
        scroll.documentView = view
        scroll.hasVerticalScroller = true
        alert.accessoryView = scroll
        alert.addButton(withTitle: AppText.text("Copy diagnostic report"))
        alert.addButton(withTitle: AppText.text("Save diagnostic report..."))
        alert.addButton(withTitle: AppText.text("Close diagnostic report"))
        if AjazzSessionActive(diagnosticSession) {
            alert.addButton(withTitle: AppText.text("Add report to diagnostic session"))
        }
        let result = alert.runModal()
        if result == .alertFirstButtonReturn { copyReport(report) }
        if result == .alertSecondButtonReturn { saveReport(report) }
        if result.rawValue == NSApplication.ModalResponse.alertThirdButtonReturn.rawValue + 1 {
            addSessionReport(report, marker: 6)
        }
    }

    private func saveReport(_ report: String) {
        let panel = NSSavePanel()
        panel.nameFieldStringValue = "ajazz-macos-diagnostics.txt"
        guard panel.runModal() == .OK, let url = panel.url else { return }
        let bytes = Array(report.utf8)
        let saved = url.path.withCString { path in
            bytes.withUnsafeBufferPointer {
                AjazzWriteDiagnostic(path, $0.baseAddress, $0.count) == 0
            }
        }
        if !saved {
            let alert = NSAlert()
            alert.messageText = AppText.text("Unable to save diagnostic report")
            alert.runModal()
        }
    }

    @objc private func runHIDDiagnostics() {
        guard !polling, !diagnosticRunning, !closing else {
            let alert = NSAlert()
            alert.messageText = AppText.text("Diagnostic busy; try again after the current read")
            alert.runModal()
            return
        }
        NSApp.activate(ignoringOtherApps: true)
        let consent = NSAlert()
        consent.messageText = AppText.text("Run HID diagnostics...")
        consent.informativeText = AppText.text("HID diagnostic consent")
        consent.addButton(withTitle: AppText.text("Run HID diagnostics..."))
        consent.addButton(withTitle: AppText.text("Close diagnostic report"))
        guard consent.runModal() == .alertFirstButtonReturn,
              !polling, !diagnosticRunning, !closing else { return }
        diagnosticRunning = true
        let token = ApexWorkerCancellation()
        diagnosticCancellation = token
        let snapshot = diagnosticSnapshot()
        renderStatus(displayedStatus)
        DispatchQueue.global(qos: .utility).async { [weak self] in
            let started = ProcessInfo.processInfo.systemUptime
            let result = ApexBoundedWorker.read(mode: ApexBoundedWorker.traceMode,
                                                cancellation: token)
            let elapsed = ProcessInfo.processInfo.systemUptime - started
            DispatchQueue.main.async {
                self?.finishDiagnostic(snapshot, result, elapsed: elapsed)
            }
        }
    }

    private func finishDiagnostic(_ snapshot: String, _ result: ApexBoundedWorker.Result, elapsed: Double) {
        let cancellationRequested = diagnosticCancellation?.isCancelled == true
        diagnosticCancellation = nil
        if closing {
            diagnosticRunning = false
            NSApp.reply(toApplicationShouldTerminate: true)
            return
        }
        let detail: String
        switch result {
        case .trace(let text):
            if cancellationRequested {
                let partial = ApexBoundedWorker.traceResult(Data((text + "\n").utf8), failure: "cancelled")
                if case .partialTrace(_, let records) = partial {
                    detail = "INCOMPLETE: cancelled; no fresh battery claimed\n" + records
                } else {
                    detail = "INCOMPLETE: cancelled; no fresh battery claimed"
                }
            } else { detail = text }
        case .partialTrace(let reason, let text):
            detail = "INCOMPLETE: \(reason); no fresh battery claimed\n" + text
        case .cancelled: detail = "INCOMPLETE: cancelled; no fresh battery claimed"
        default: detail = "Diagnostic outcome: \(result)"
        }
        diagnosticRunning = false
        renderStatus(displayedStatus)
        let timing = String(format: "Elapsed ms: %.0f", elapsed * 1000)
        reviewReport(snapshot + "\n\nFresh bounded F7/05 trace:\n" + detail + "\n" + timing)
    }

    @objc private func showBluetoothBattery() {
        if bluetoothWindow == nil {
            bluetoothWindow = BluetoothBatteryWindowController()
        }
        bluetoothWindow?.showWindow(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    @objc private func showDiagnostics() {
        reviewReport(diagnosticSnapshot())
    }

    @objc private func syncClockNow() {
        manualClockSync = true
        refresh()
    }

    func menuWillOpen(_ menu: NSMenu) {
        renderStatus(displayedStatus)
    }

    @objc private func refresh() {
        if closing { return }
        if sessionObservation.presentation(displayedStatus, at: Date()) != displayedStatus {
            renderStatus(displayedStatus)
        }
        guard !polling, !diagnosticRunning, !closing else { return }
        polling = true
        let token = isolatedPolling ? ApexWorkerCancellation() : nil
        activeCancellation = token
        let manual = manualClockSync
        manualClockSync = false
        let automatic = autoClockEnabled
        let lastAttempt = lastClockAttempt
        let previouslyPresent = receiverWasPresent
        DispatchQueue.global(qos: .utility).async { [weak self] in
            let readStart = ProcessInfo.processInfo.systemUptime
            let value = Self.readForPoll(token)
            let readMs = AjazzElapsedMilliseconds(readStart, ProcessInfo.processInfo.systemUptime)
            let observedAt = Date()
            let elapsed = Date().timeIntervalSince(lastAttempt)
            let due = elapsed < 0 || elapsed >= 300
            let shouldSync = token?.isCancelled != true &&
                value.compatibleReceiverPresent == true && (manual ||
                (automatic && (due || !previouslyPresent)))
            let clockStart = ProcessInfo.processInfo.systemUptime
            let sent = shouldSync ? Self.clockForPoll(token) : false
            let clockMs = shouldSync ? AjazzElapsedMilliseconds(clockStart,
                ProcessInfo.processInfo.systemUptime) : -1
            DispatchQueue.main.async {
                self?.completePoll(value, observedAt: observedAt, manual: manual,
                                   attempted: shouldSync, sent: sent,
                                   readMs: readMs, clockMs: clockMs)
            }
        }
    }

    private static func readForPoll(_ token: ApexWorkerCancellation?) -> ApexBattery.Status {
        guard let token = token else { return ApexBattery.read() }
        switch ApexBoundedWorker.read(cancellation: token) {
        case .reply(let value): return value
        case .timeout: return .timedOut
        default: return .accessUnknown
        }
    }

    private static func clockForPoll(_ token: ApexWorkerCancellation?) -> Bool {
        guard let token = token else { return ApexBattery.syncClock() }
        if case .clock(let sent) = ApexBoundedWorker.read(
            mode: ApexBoundedWorker.clockMode, cancellation: token) { return sent }
        return false
    }

    private func completePoll(_ value: ApexBattery.Status, observedAt: Date, manual: Bool,
                              attempted: Bool, sent: Bool, readMs: Int64, clockMs: Int64) {
        activeCancellation = nil
        if closing {
            polling = false
            NSApp.reply(toApplicationShouldTerminate: true)
            return
        }
        // Retain an unserved explicit request after unknown discovery, but do
        // not create an immediate retry loop. Only a new queued request does so.
        let queued = manualClockSync
        if manual && value.compatibleReceiverPresent == nil { manualClockSync = true }
        if value == .timedOut && isolatedPolling {
            recordJournalEvent(AjazzEventIsolatedPollTimedOut, AjazzReasonTimeout, durationMs: readMs)
        }
        if attempted { recordClockResult(sent, durationMs: clockMs) }
        sessionObservation.observe(value, at: observedAt)
        update(value)
        if queued { refresh() }
    }

    private func recordClockResult(_ sent: Bool, durationMs: Int64) {
        lastClockAttempt = Date()
        lastClockSent = sent
        recordJournalEvent(sent ? AjazzEventDockClockSucceeded : AjazzEventDockClockFailed,
                           sent ? AjazzReasonNone : AjazzReasonUnsuccessful, durationMs: durationMs)
        updateClockStatus()
    }

    private func updateClockStatus() {
        guard let sent = lastClockSent else {
            clockItem.title = AppText.text("Dock clock: not yet synchronized")
            return
        }
        let stamp = DateFormatter.localizedString(
            from: lastClockAttempt, dateStyle: .none, timeStyle: .medium)
        clockItem.title = AppText.format(sent
            ? "Dock clock: command sent at %@"
            : "Dock clock: unable to send at %@", stamp)
    }

    private func update(_ status: ApexBattery.Status) {
        if historyEnabled { batteryHistory.record(status) }
        if let event = batteryAlerts.evaluate(
            status, notifyLow: lowAlertsEnabled,
            notifyDisconnect: disconnectAlertsEnabled,
            thresholds: selectedBatteryThresholds) {
            BatteryLocalNotifications.deliver(event)
        }
        if let present = status.compatibleReceiverPresent { receiverWasPresent = present }
        polling = false
        displayedStatus = status
        renderStatus(status)
    }

    private func renderStatus(_ observation: ApexBattery.Status) {
        let status = sessionObservation.presentation(observation, at: Date())
        switch status {
        case .battery(let level):
            statusItem.button?.title = "🔋\(level)%"
            detailItem.title = "AJAZZ APEX — \(level)% (2.4 GHz)"
        case .notConnected:
            statusItem.button?.title = "🔋—"
            detailItem.title = AppText.text("AJAZZ APEX receiver not found")
        case .timedOut:
            statusItem.button?.title = "🔋?"
            detailItem.title = AppText.text("HID read timed out")
        case .accessUnknown:
            statusItem.button?.title = "🔋?"
            detailItem.title = AppText.text("Cannot check USB receiver access")
        case .unsupportedCollection:
            statusItem.button?.title = "🔋?"
            detailItem.title = AppText.text("Receiver HID collection not supported")
        case .unavailable:
            statusItem.button?.title = "🔋?"
            detailItem.title = AppText.text(
                "Receiver found; battery status unavailable")
        }
        if let stamp = sessionObservation.lastVerified {
            if case .battery = status { } else {
                let text = DateFormatter.localizedString(from: stamp,
                    dateStyle: .short, timeStyle: .medium)
                detailItem.title += " · " + AppText.format("Last verified USB sample (session): %@", text)
            }
        }
        let color = TrayAppearance.choice("TrayIconColor")
        var level: Int?
        if case .battery(let percent) = status { level = percent }
        statusItem.button?.title = ""
        statusItem.button?.image = TrayAppearance.image(level: level, choice: color,
            mouseStyle: TrayAppearance.mouseStyle())
        if diagnosticRunning {
            detailItem.title = AppText.text(diagnosticCancellation?.isCancelled == true
                ? "Cancelling HID diagnostics..." : "Running HID diagnostics...")
        }
        updateDiagnosticMenu()
        statusItem.button?.toolTip = detailItem.title + " · " + AppText.text(color.capitalized)
    }

    private func refreshStartupMenu() {
        let service = SMAppService.mainApp
        startupMenuItem?.state = service.status == .enabled ? .on : .off
        startupMenuItem?.title = AppText.text(service.status == .requiresApproval
            ? "Start at login (approval needed)" : "Start at login")
    }

    @objc private func toggleLoginStartup(_ sender: NSMenuItem) {
        let service = SMAppService.mainApp
        do {
            if service.status == .enabled {
                try service.unregister()
            } else if service.status == .notRegistered {
                try service.register()
            }
        } catch {
            let alert = NSAlert()
            alert.messageText = AppText.text("Unable to change Start at Login")
            alert.informativeText = error.localizedDescription +
                "\n" + AppText.text("Install the app in Applications, then try again.")
            alert.alertStyle = .warning
            alert.runModal()
        }

        refreshStartupMenu()
        if service.status == .requiresApproval {
            SMAppService.openSystemSettingsLoginItems()
        }
    }

    @objc private func openLoginItemsSettings() {
        SMAppService.openSystemSettingsLoginItems()
        refreshStartupMenu()
    }

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        if diagnosticRunning, let token = diagnosticCancellation {
            closing = true
            timer?.invalidate()
            token.cancel()
            return .terminateLater
        }
        guard isolatedPolling, polling else { return .terminateNow }
        closing = true
        timer?.invalidate()
        activeCancellation?.cancel()
        return .terminateLater
    }

    @objc private func quit() { NSApp.terminate(nil) }
}

/// Replay the shared sanitized fixture through the decoder and actual history writer.
private func corpusFailure(_ stage: String, row: Int? = nil) -> Bool {
    // Only fixed stage names and synthetic row numbers; no paths or raw buffers.
    let location = row.map { " row=\($0)" } ?? ""
    print("FAIL: observation-corpus stage=\(stage)\(location)")
    return false
}

private func verifyHistoryRecovery() -> Bool {
    let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    let writer = BatteryHistoryWriter(directory: dir)
    defer { try? FileManager.default.removeItem(at: dir) }
    let header = "utc_timestamp,percent,state\r\n"
    let date = ISO8601DateFormatter().date(from: "2026-11-25T10:00:10Z")!
    let from = date.addingTimeInterval(-60)
    let imported = "2026-11-25T12:00:00.1234567+02:00,70,online"
    do {
        let absent = try BatteryHistoryReader.load(writer.file, from: from, through: date)
        guard absent.isEmpty else { return false }
        let original = header + imported + "\r\n2026-11-25T10:00:03Z,,unavailable"
        try original.write(to: writer.file, atomically: true, encoding: .utf8)
        let before = try BatteryHistoryReader.load(writer.file, from: from, through: date)
        guard before.map(\.state) == ["online", "unavailable"] else { return false }
        writer.record(.battery(69), at: date)
        let after = try BatteryHistoryReader.load(writer.file, from: from, through: date)
        guard after.map(\.percent) == [70, nil, 69] else { return false }

        let partial = try String(contentsOf: writer.file, encoding: .utf8) + "interrupted,row"
        try partial.write(to: writer.file, atomically: true, encoding: .utf8)
        writer.record(.notConnected, at: date.addingTimeInterval(1))
        let recovered = try BatteryHistoryReader.load(writer.file, from: from, through: date.addingTimeInterval(1))
        guard recovered.map(\.state) == ["online", "unavailable", "online", "disconnected"] else { return false }
        try Data([0xff, 0xfe, 0xff]).write(to: writer.file)
        do {
            _ = try BatteryHistoryReader.load(writer.file, from: from, through: date)
            return false
        } catch { return true }
    } catch { return false }
}

private func verifyCorpusHistory(_ status: ApexBattery.Status, percent: Int?,
                                 directory: URL, now: Date, row: Int) -> Bool {
    let writer = BatteryHistoryWriter(directory: directory)
    writer.record(status, at: now)
    guard let csv = try? String(contentsOf: writer.file, encoding: .utf8) else {
        return corpusFailure("history-read", row: row)
    }
    guard let line = csv.split(whereSeparator: \.isNewline).last,
          let sample = BatteryHistoryReader.parse(String(line)) else {
        return corpusFailure("history-row", row: row)
    }
    guard sample.percent == percent,
          sample.state == (percent == nil ? "unavailable" : "online"),
          sample.timestamp <= now, now.timeIntervalSince(sample.timestamp) < 1 else {
        return corpusFailure("history-observation", row: row)
    }
    return true
}

/// Replay the shared sanitized fixture through the decoder and actual history writer.
private func verifyObservationCorpus(_ path: String) -> Bool {
    guard let text = try? String(contentsOfFile: path, encoding: .utf8) else {
        return corpusFailure("fixture-read")
    }
    let rows = text.split(whereSeparator: \.isNewline).dropFirst()
    guard rows.count == 20 else { return corpusFailure("fixture-count") }
    let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer { try? FileManager.default.removeItem(at: root) }
    for (index, row) in rows.enumerated() {
        let number = index + 1
        let fields = row.split(separator: ",", omittingEmptySubsequences: false)
        guard fields.count == 5, fields[2].count.isMultiple(of: 2) else {
            return corpusFailure("fixture-layout", row: number)
        }
        let hex = Array(fields[2])
        var bytes: [UInt8] = []
        for offset in stride(from: 0, to: hex.count, by: 2) {
            guard let byte = UInt8(String(hex[offset...offset + 1]), radix: 16) else {
                return corpusFailure("fixture-hex", row: number)
            }
            bytes.append(byte)
        }
        let percent = ApexBattery.parse(bytes)
        guard (percent.map { String($0) } ?? "unknown") == String(fields[4]) else {
            return corpusFailure("decoder", row: number)
        }
        let value = percent.map(ApexBattery.Status.battery) ?? .unavailable
        // Exercise both sides of the whole-second formatting boundary.
        for (phase, fraction) in [0.001, 0.499, 0.9999].enumerated() {
            let now = Date(timeIntervalSince1970: 1_800_000_000 + fraction)
            let directory = root.appendingPathComponent("\(index)-\(phase)")
            guard verifyCorpusHistory(value, percent: percent, directory: directory,
                                      now: now, row: number) else { return false }
        }
        if percent == nil {
            let alerts = BatteryAlertPolicy()
            guard alerts.evaluate(.battery(83), notifyLow: true, notifyDisconnect: true) == nil,
                  alerts.evaluate(.notConnected, notifyLow: true, notifyDisconnect: true) == nil,
                  alerts.evaluate(value, notifyLow: true, notifyDisconnect: true) == nil,
                  alerts.evaluate(.notConnected, notifyLow: true, notifyDisconnect: true) == nil
            else { return corpusFailure("alerts", row: number) }
        }
    }
    print("PASS: 20 shared F7 observations, CSV and alert policy")
    return true
}

if CommandLine.arguments.contains("--internal-test-io-lease") {
    guard CommandLine.arguments.count == 2 else { exit(1) }
    let lease = AjazzAcquireIoLease()
    guard lease >= 0 else { exit(2) }
    AjazzReleaseIoLease(lease)
    exit(0)
} else if let worker = CommandLine.arguments.dropFirst().first(where: ApexBoundedWorker.isWorker) {
    guard CommandLine.arguments.count == 2 else { exit(1) }
    exit(ApexBoundedWorker.runChild(worker))
} else if CommandLine.arguments.contains("--self-test-bounded-poll") {
    guard CommandLine.arguments.count == 2 else { exit(1) }
    let passed = ApexBoundedWorker.selfTest() && AjazzDiagnosticExportSelfTest()
    print(passed ? "PASS: bounded worker IPC, rejection, timeout, cancellation and recovery" :
        "FAIL: bounded worker self-test")
    exit(passed ? 0 : 1)
} else if CommandLine.arguments.contains("--internal-poll-sample") {
    guard CommandLine.arguments.count == 2 else { exit(1) }
    // Fixed synthetic reply, without opening IOKit or starting the tray.
    print("{\"kind\":\"synthetic\",\"percent\":null,\"presence\":\"unknown\"}")
} else if CommandLine.arguments.contains("--help") || CommandLine.arguments.contains("-h") {
    print("AJAZZ Battery Tray for macOS (experimental 2.4 GHz/8K HID)")
    print("Usage: AJAZZBatteryTray [--help] [--diagnose] [--self-test]")
    print("Optional: --experimental-isolated-polling (session only).")
    print("Tray menu: sync dock time now or every five minutes.")
    print("Requires macOS 13+ and a compatible VID_3151:PID_5007 receiver.")
} else if CommandLine.arguments.contains("--self-test") {
    guard TrayAppearance.selfTest() else {
        print("FAIL: bundled appearance resources or rendered critical state")
        exit(1)
    }
    print("PASS: four bundled app icons and 36 appearance rendering cases")
    let originalLanguage = AppText.language
    AppText.choose("ru")
    let russianValid = AppText.text("Settings") == "Настройки" &&
        AppText.format("Below %d%%", 25) == "Ниже 25%"
    AppText.choose("uk")
    let ukrainianValid = AppText.text("Settings") == "Налаштування" &&
        AppText.format("%d seconds", 30) == "30 с"
    AppText.choose("en")
    let fallbackValid = AppText.text("Settings") == "Settings" &&
        AppText.normalize("other") == "en"
    AppText.choose(originalLanguage)
    let localizationValid = russianValid && ukrainianValid && fallbackValid
    let testDate = Calendar.current.date(from: DateComponents(
        year: 2026, month: 11, day: 6, hour: 9, minute: 57, second: 42))!
    let packet = ApexBattery.makeClockPayload(testDate)
    let clockValid = packet.count == 64 && packet[0] == 0x28 &&
        packet[7] == 0xD7 && packet[8] == 0x07 && packet[9] == 0xEA &&
        packet[10] == 11 && packet[11] == 6 && packet[12] == 9 &&
        packet[13] == 57 && packet[14] == 42 && packet[15] == 0
    var blocked = [UInt8](repeating: 0, count: 64)
    blocked[0] = 0x50
    let guardValid = ApexBattery.validClockFrame(packet) &&
        !ApexBattery.validClockFrame(blocked) &&
        !ApexBattery.validTelemetryFrame(blocked)
    let historyValid = !BatteryHistoryWriter.shouldRecord(
        previous: "70|online", current: "70|online", secondsSinceLast: 60) &&
        BatteryHistoryWriter.shouldRecord(
        previous: "70|online", current: "69|online", secondsSinceLast: 60) &&
        BatteryHistoryWriter.shouldRecord(
        previous: "70|online", current: "70|online", secondsSinceLast: 301) &&
        BatteryHistoryWriter.shouldRecord(
        previous: "70|online", current: "70|online", secondsSinceLast: -60)
    let chartValid = BatteryHistoryReader.parse(
        "2026-11-06T12:00:00Z,73,online")?.percent == 73 &&
        BatteryHistoryReader.parse(
            "2026-11-06T12:00:00Z,0,online")?.percent == 0 &&
        BatteryHistoryReader.parse(
            "2026-11-06T12:00:00Z,,disconnected")?.state == "disconnected" &&
        BatteryHistoryReader.parse(
            "2026-11-06T12:00:00Z,,unavailable")?.percent == nil &&
        BatteryHistoryReader.parse(
            "2026-11-06T12:00:00Z,,online") == nil &&
        BatteryHistoryReader.parse(
            "2026-11-06T12:00:00Z,1,disconnected") == nil &&
        BatteryHistoryReader.parse(
            "2026-11-06T12:00:00Z,101,online") == nil &&
        BatteryHistoryReader.parse(
            "2026-11-06T12:00:00Z,255,online") == nil &&
        BatteryHistoryReader.parse(
            "not-a-date,73,online") == nil
    let alerts = BatteryAlertPolicy()
    let alertTests = alerts.evaluate(
        .notConnected, notifyLow: true, notifyDisconnect: true) == nil &&
        alerts.evaluate(
            .battery(75), notifyLow: true, notifyDisconnect: true) == nil &&
        alerts.evaluate(
            .battery(50), notifyLow: true, notifyDisconnect: true) == nil &&
        alerts.evaluate(
            .battery(49), notifyLow: true, notifyDisconnect: true) == .lowBattery(49) &&
        alerts.evaluate(
            .battery(48), notifyLow: true, notifyDisconnect: true) == nil &&
        alerts.evaluate(
            .battery(25), notifyLow: true, notifyDisconnect: true) == nil &&
        alerts.evaluate(
            .battery(24), notifyLow: true, notifyDisconnect: true) == .lowBattery(24) &&
        alerts.evaluate(
            .battery(10), notifyLow: true, notifyDisconnect: true) == nil &&
        alerts.evaluate(
            .battery(9), notifyLow: true, notifyDisconnect: true) == .lowBattery(9) &&
        alerts.evaluate(
            .battery(8), notifyLow: true, notifyDisconnect: true) == nil &&
        alerts.evaluate(
            .unavailable, notifyLow: true, notifyDisconnect: true) == nil &&
        alerts.evaluate(
            .notConnected, notifyLow: true, notifyDisconnect: true) == nil &&
        alerts.evaluate(
            .notConnected, notifyLow: true, notifyDisconnect: true) == .receiverDisconnected
    let timeoutAlerts = BatteryAlertPolicy()
    let timeoutValid = ApexBattery.Status.timedOut.compatibleReceiverPresent == nil &&
        timeoutAlerts.evaluate(.battery(80), notifyLow: true, notifyDisconnect: true) == nil &&
        timeoutAlerts.evaluate(.notConnected, notifyLow: true, notifyDisconnect: true) == nil &&
        timeoutAlerts.evaluate(.timedOut, notifyLow: true, notifyDisconnect: true) == nil &&
        timeoutAlerts.evaluate(.notConnected, notifyLow: true, notifyDisconnect: true) == nil &&
        timeoutAlerts.evaluate(.notConnected, notifyLow: true, notifyDisconnect: true) == .receiverDisconnected
    let selectedAlerts = BatteryAlertPolicy()
    let selectedTests = selectedAlerts.evaluate(
        .battery(75), notifyLow: true, notifyDisconnect: true,
        thresholds: [25]) == nil &&
        selectedAlerts.evaluate(
            .battery(49), notifyLow: true, notifyDisconnect: true,
            thresholds: [25]) == nil &&
        selectedAlerts.evaluate(
            .battery(24), notifyLow: true, notifyDisconnect: true,
            thresholds: [25]) == .lowBattery(24) &&
        selectedAlerts.evaluate(
            .battery(9), notifyLow: true, notifyDisconnect: true,
            thresholds: [25]) == nil &&
        selectedAlerts.evaluate(
            .battery(30), notifyLow: true, notifyDisconnect: true,
            thresholds: [25]) == nil &&
        selectedAlerts.evaluate(
            .battery(24), notifyLow: true, notifyDisconnect: true,
            thresholds: [25]) == .lowBattery(24)
    let jumpAlerts = BatteryAlertPolicy()
    let jumpTests = jumpAlerts.evaluate(
        .battery(75), notifyLow: true, notifyDisconnect: true) == nil &&
        jumpAlerts.evaluate(
            .battery(9), notifyLow: true, notifyDisconnect: true) == .lowBattery(9) &&
        jumpAlerts.evaluate(
            .battery(9), notifyLow: true, notifyDisconnect: true) == nil
    let bluetoothValid = BluetoothBatteryPayload.parse(Data([0])) == 0 &&
        BluetoothBatteryPayload.parse(Data([100])) == 100 &&
        BluetoothBatteryPayload.parse(Data([101])) == nil &&
        BluetoothBatteryPayload.parse(Data([50, 0])) == nil &&
        BluetoothBatteryPayload.parse(nil) == nil &&
        BluetoothBatteryPayload.likelyAjazz("AJ179 APEX") &&
        BluetoothBatteryPayload.likelyAjazz("Ajazz mouse") &&
        !BluetoothBatteryPayload.likelyAjazz("Keyboard") &&
        BluetoothBatteryInspector().diagnosticSummary.contains("Bluetooth last manual read: not requested")
    let sharedFrameValid = ApexBattery.parse([5, 1, 0, 83, 1, 0, 1, 2, 0, 0]) == 83 &&
        ApexBattery.parse([1, 0, 83, 1, 0, 1, 3, 0, 0]) == 83 &&
        ApexBattery.parse([5, 0, 0, 83, 1, 0, 1, 2, 0, 0]) == nil &&
        ApexBattery.parse([0, 0, 83, 1, 0, 1, 1, 0, 0]) == nil
    let presenceValid = ApexBattery.Status.accessUnknown.compatibleReceiverPresent == nil &&
        ApexBattery.Status.unsupportedCollection.compatibleReceiverPresent == nil &&
        ApexBattery.Status.unavailable.compatibleReceiverPresent == true &&
        ApexBattery.Status.notConnected.compatibleReceiverPresent == false
    var observation = ApexSessionObservation()
    observation.observe(.battery(83), at: testDate)
    let ageValid = observation.presentation(.battery(83), at: testDate.addingTimeInterval(300)) == .battery(83) &&
        observation.presentation(.battery(83), at: testDate.addingTimeInterval(300.01)) == .unavailable &&
        observation.presentation(.battery(83), at: testDate.addingTimeInterval(-1)) == .unavailable &&
        ApexSessionObservation().presentation(.battery(83), at: testDate) == .unavailable &&
        observation.presentation(.timedOut, at: testDate) == .timedOut
    observation.observe(.timedOut, at: testDate.addingTimeInterval(30))
    let preserved = observation.lastVerified == testDate
    observation.observe(.notConnected, at: testDate.addingTimeInterval(60))
    let provenanceValid = preserved && observation.lastVerified == nil &&
        ApexBattery.noSampleStatus(matched: true, opened: false) == .accessUnknown &&
        ApexBattery.noSampleStatus(matched: true, opened: true) == .unavailable &&
        ApexBattery.noSampleStatus(matched: false, opened: false) == .unsupportedCollection
    let corpusValid = ProcessInfo.processInfo.environment["AJAZZ_TEST_CORPUS"]
        .map(verifyObservationCorpus) ?? true
    let legacyParserValid = ApexBattery.parse([5, 0, 0, 73]) == 73 &&
        ApexBattery.parse([0, 0, 73]) == 73 &&
        ApexBattery.parse([5, 0, 0, 0]) == nil &&
        ApexBattery.parse([5, 0, 0, 255]) == nil &&
        ApexBattery.parse([4, 0, 0, 30]) == nil
    // Stable synthetic group labels only; do not emit device data or raw reports.
    let checks: [(String, Bool)] = [
        ("observation-corpus", corpusValid), ("provenance", provenanceValid),
        ("sample-age", ageValid),
        ("shared-frame", sharedFrameValid), ("presence", presenceValid),
        ("localization", localizationValid), ("bluetooth-payload", bluetoothValid),
        ("alerts", alertTests), ("timeout-alerts", timeoutValid),
        ("selected-alerts", selectedTests), ("jump-alerts", jumpTests),
        ("history-recovery", verifyHistoryRecovery()), ("history-chart", chartValid), ("history-writer", historyValid),
        ("clock-payload", clockValid), ("clock-guard", guardValid),
        ("legacy-parser", legacyParserValid)
    ]
    for (name, passed) in checks {
        print("\(passed ? "PASS" : "FAIL"): self-test \(name)")
    }
    let valid = checks.allSatisfy { $0.1 }
    print(valid ? "PASS: HID report parser" : "FAIL: HID report parser")
    if !valid { exit(1) }
} else if CommandLine.arguments.contains("--diagnose") {
    switch ApexBattery.read() {
    case .battery(let level): print("PASS: battery \(level)%")
    case .notConnected: print("UNKNOWN: compatible receiver not found")
    case .accessUnknown: print("UNKNOWN: cannot access HID manager/device")
    case .timedOut: print("UNKNOWN: HID read timed out")
    case .unsupportedCollection: print("UNKNOWN: receiver HID collection not supported")
    case .unavailable: print("UNKNOWN: receiver found, no valid battery report")
    }
} else {
    if CommandLine.arguments.contains("--experimental-isolated-polling") && CommandLine.arguments.count != 2 { exit(1) }
    let application = NSApplication.shared
    let delegate = TrayController()
    application.delegate = delegate
    application.run()
}
