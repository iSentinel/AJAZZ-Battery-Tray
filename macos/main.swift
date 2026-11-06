import AppKit
import Foundation
import IOKit.hid

/// Reads battery and can set only the dock's documented on-board clock.
enum ApexBattery {
    enum Status {
        case battery(Int)
        case notConnected
        case unavailable
    }

    private static let vendorID = 0x3151
    private static let productID = 0x5007
    private static let usagePage = 0xFFFF
    private static let usage = 0x02

    /// Decode a feature report returned for report ID 0x05.
    static func parse(_ report: [UInt8]) -> Int? {
        // macOS may return the report ID or strip it from an unnumbered reply.
        if report.count >= 4 && report[0] == 0x05 &&
           report[1] == 0 && report[2] == 0 &&
           (1...100).contains(Int(report[3])) {
            return Int(report[3])
        }
        if report.count >= 3 && report[0] == 0 && report[1] == 0 &&
           (1...100).contains(Int(report[2])) {
            return Int(report[2])
        }
        return nil
    }

    static func read() -> Status {
        let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
        let criteria: [String: Any] = [
            kIOHIDVendorIDKey as String: vendorID,
            kIOHIDProductIDKey as String: productID
        ]
        IOHIDManagerSetDeviceMatching(manager, criteria as CFDictionary)
        guard IOHIDManagerOpen(manager, IOOptionBits(kIOHIDOptionsTypeNone)) == kIOReturnSuccess else {
            return .unavailable
        }
        defer { IOHIDManagerClose(manager, IOOptionBits(kIOHIDOptionsTypeNone)) }

        guard let found = IOHIDManagerCopyDevices(manager) as? Set<IOHIDDevice>,
              !found.isEmpty else {
            return .notConnected
        }
        var attempted = false
        for device in found where matchesVendorUsage(device) {
            attempted = true
            if let value = poll(device) { return .battery(value) }
        }
        return attempted ? .unavailable : .notConnected
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

    private static func poll(_ device: IOHIDDevice) -> Int? {
        guard IOHIDDeviceOpen(device, IOOptionBits(kIOHIDOptionsTypeNone)) == kIOReturnSuccess else {
            return nil
        }
        defer { IOHIDDeviceClose(device, IOOptionBits(kIOHIDOptionsTypeNone)) }
        // Match the receiver's Windows request: report ID 0, first payload byte 0xF7.
        for count in [65, 67] {
            var request = [UInt8](repeating: 0, count: count)
            request[1] = 0xF7
            guard validTelemetryFrame(request) else { continue }
            let write = request.withUnsafeBufferPointer { data in
                IOHIDDeviceSetReport(device, kIOHIDReportTypeFeature, 0, data.baseAddress!, data.count)
            }
            guard write == kIOReturnSuccess else { continue }
            Thread.sleep(forTimeInterval: 0.03)
            var reply = [UInt8](repeating: 0, count: count)
            reply[0] = 0x05
            var actualLength: CFIndex = count
            let read = reply.withUnsafeMutableBufferPointer { data in
                IOHIDDeviceGetReport(device, kIOHIDReportTypeFeature, 5, data.baseAddress!, &actualLength)
            }
            if read == kIOReturnSuccess && actualLength >= 3,
               let percent = parse(Array(reply.prefix(Int(actualLength)))) {
                return percent
            }
        }
        return nil
    }
}

/// Native AppKit menu bar user interface, without a Dock window.
final class TrayController: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem!
    private var statusMenu: NSMenu!
    private var detailItem: NSMenuItem!
    private var clockItem: NSMenuItem!
    private var lastClockAttempt = Date.distantPast
    private var receiverWasPresent = false
    private var manualClockSync = false
    private var timer: Timer?
    private var polling = false
    private let batteryHistory = BatteryHistoryWriter()

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem.button?.title = "🔋?"
        statusItem.button?.toolTip = "AJAZZ APEX battery: checking"
        statusMenu = NSMenu(title: "AJAZZ Battery Tray")
        detailItem = NSMenuItem(title: "Checking 2.4 GHz receiver…", action: nil, keyEquivalent: "")
        detailItem.isEnabled = false
        statusMenu.addItem(detailItem)
        statusMenu.addItem(.separator())

        let refreshItem = NSMenuItem(title: "Refresh now", action: #selector(refresh), keyEquivalent: "r")
        refreshItem.target = self
        statusMenu.addItem(refreshItem)

        let diagnostics = NSMenuItem(title: "Device diagnostics...",
                                     action: #selector(showDiagnostics),
                                     keyEquivalent: "")
        diagnostics.target = self
        statusMenu.addItem(diagnostics)
        let openHistory = NSMenuItem(title: "Open battery history folder...",
                                     action: #selector(openHistoryFolder),
                                     keyEquivalent: "")
        openHistory.target = self
        statusMenu.addItem(openHistory)
        let recordHistory = NSMenuItem(title: "Record battery history",
                                       action: #selector(toggleBatteryHistory(_:)),
                                       keyEquivalent: "")
        recordHistory.target = self
        recordHistory.state = historyEnabled ? .on : .off
        statusMenu.addItem(recordHistory)

        let interval = NSMenuItem(title: "Refresh interval", action: nil, keyEquivalent: "")
        let subMenu = NSMenu()
        for seconds in [15, 30, 60, 120] {
            let item = NSMenuItem(title: "\(seconds) seconds", action: #selector(changeInterval(_:)), keyEquivalent: "")
            item.tag = seconds
            item.target = self
            subMenu.addItem(item)
        }
        interval.submenu = subMenu
        statusMenu.addItem(interval)
        statusMenu.addItem(.separator())

        let syncItem = NSMenuItem(title: "Sync dock time now",
                                  action: #selector(syncClockNow), keyEquivalent: "")
        syncItem.target = self
        statusMenu.addItem(syncItem)
        let automatic = NSMenuItem(title: "Auto-sync dock clock (5 min)",
                                   action: #selector(toggleClockSync(_:)), keyEquivalent: "")
        automatic.target = self
        automatic.state = autoClockEnabled ? .on : .off
        statusMenu.addItem(automatic)
        clockItem = NSMenuItem(title: "Dock clock: not yet synchronized",
                               action: nil, keyEquivalent: "")
        clockItem.isEnabled = false
        statusMenu.addItem(clockItem)
        statusMenu.addItem(.separator())

        let quit = NSMenuItem(title: "Quit AJAZZ Battery Tray", action: #selector(quit), keyEquivalent: "q")
        quit.target = self
        statusMenu.addItem(quit)
        statusItem.menu = statusMenu
        configureTimer()
        refresh()
    }

    private func configureTimer() {
        timer?.invalidate()
        let seconds = UserDefaults.standard.integer(forKey: "PollSeconds")
        let interval = [15, 30, 60, 120].contains(seconds) ? seconds : 30
        timer = Timer.scheduledTimer(timeInterval: TimeInterval(interval), target: self,
                                     selector: #selector(refresh), userInfo: nil, repeats: true)
        statusMenu.items
            .compactMap { $0.submenu }
            .flatMap { $0.items }
            .forEach { $0.state = $0.tag == interval ? .on : .off }
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

    @objc private func openHistoryFolder() {
        NSWorkspace.shared.open(batteryHistory.directory)
    }

    @objc private func toggleBatteryHistory(_ sender: NSMenuItem) {
        let enabled = !historyEnabled
        UserDefaults.standard.set(enabled, forKey: "RecordBatteryHistory")
        sender.state = enabled ? .on : .off
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

    @objc private func showDiagnostics() {
        let alert = NSAlert()
        alert.messageText = "AJAZZ APEX — Device diagnostics"
        alert.informativeText = ApexBattery.diagnostics()
        alert.alertStyle = .informational
        alert.runModal()
    }

    @objc private func syncClockNow() {
        manualClockSync = true
        refresh()
    }

    @objc private func refresh() {
        guard !polling else { return }
        polling = true
        let manual = manualClockSync
        manualClockSync = false
        let automatic = autoClockEnabled
        let lastAttempt = lastClockAttempt
        let previouslyPresent = receiverWasPresent
        DispatchQueue.global(qos: .utility).async { [weak self] in
            let value = ApexBattery.read()
            let present: Bool
            switch value {
            case .notConnected: present = false
            default: present = true
            }
            let due = Date().timeIntervalSince(lastAttempt) >= 300
            let shouldSync = present && (manual ||
                (automatic && (due || !previouslyPresent)))
            let sent = shouldSync ? ApexBattery.syncClock() : false
            DispatchQueue.main.async {
                self?.update(value)
                if shouldSync { self?.recordClockResult(sent) }
            }
        }
    }

    private func recordClockResult(_ sent: Bool) {
        lastClockAttempt = Date()
        let stamp = DateFormatter.localizedString(
            from: Date(), dateStyle: .none, timeStyle: .medium)
        clockItem.title = sent
            ? "Dock clock: command sent at " + stamp
            : "Dock clock: unable to send at " + stamp
    }

    private func update(_ status: ApexBattery.Status) {
        if historyEnabled { batteryHistory.record(status) }
        switch status {
        case .notConnected: receiverWasPresent = false
        default: receiverWasPresent = true
        }
        polling = false
        switch status {
        case .battery(let level):
            statusItem.button?.title = "🔋\(level)%"
            detailItem.title = "AJAZZ APEX — \(level)% (2.4 GHz)"
        case .notConnected:
            statusItem.button?.title = "🔋—"
            detailItem.title = "AJAZZ APEX receiver not found"
        case .unavailable:
            statusItem.button?.title = "🔋?"
            detailItem.title = "Receiver found; battery status unavailable"
        }
        statusItem.button?.toolTip = detailItem.title
    }

    @objc private func quit() { NSApp.terminate(nil) }
}

if CommandLine.arguments.contains("--help") || CommandLine.arguments.contains("-h") {
    print("AJAZZ Battery Tray for macOS (experimental 2.4 GHz/8K HID)")
    print("Usage: AJAZZBatteryTray [--help] [--diagnose] [--self-test]")
    print("Tray menu: sync dock time now or every five minutes.")
    print("Requires macOS 13+ and a compatible VID_3151:PID_5007 receiver.")
} else if CommandLine.arguments.contains("--self-test") {
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
        previous: "70|online", current: "70|online", secondsSinceLast: 301)
    let valid = historyValid && clockValid && guardValid &&
                ApexBattery.parse([5, 0, 0, 73]) == 73 &&
                ApexBattery.parse([0, 0, 73]) == 73 &&
                ApexBattery.parse([5, 0, 0, 0]) == nil &&
                ApexBattery.parse([5, 0, 0, 255]) == nil &&
                ApexBattery.parse([4, 0, 0, 30]) == nil
    print(valid ? "PASS: HID report parser" : "FAIL: HID report parser")
    if !valid { exit(1) }
} else if CommandLine.arguments.contains("--diagnose") {
    switch ApexBattery.read() {
    case .battery(let level): print("PASS: battery \(level)%")
    case .notConnected: print("UNKNOWN: compatible receiver not found")
    case .unavailable: print("UNKNOWN: receiver found, no valid battery report")
    }
} else {
    let application = NSApplication.shared
    let delegate = TrayController()
    application.delegate = delegate
    application.run()
}
