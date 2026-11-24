import AppKit
import Foundation
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

    static func read() -> Status {
        let lease = AjazzAcquireIoLease()
        guard lease >= 0 else { return .accessUnknown }
        defer { AjazzReleaseIoLease(lease) }
        let manager = IOHIDManagerCreate(kCFAllocatorDefault, IOOptionBits(kIOHIDOptionsTypeNone))
        let criteria: [String: Any] = [
            kIOHIDVendorIDKey as String: vendorID,
            kIOHIDProductIDKey as String: productID
        ]
        IOHIDManagerSetDeviceMatching(manager, criteria as CFDictionary)
        guard IOHIDManagerOpen(manager, IOOptionBits(kIOHIDOptionsTypeNone)) == kIOReturnSuccess else {
            return .accessUnknown
        }
        defer { IOHIDManagerClose(manager, IOOptionBits(kIOHIDOptionsTypeNone)) }

        guard let found = IOHIDManagerCopyDevices(manager) as? Set<IOHIDDevice>,
              !found.isEmpty else {
            return .notConnected
        }
        var matched = false
        var opened = false
        for device in found where matchesVendorUsage(device) {
            matched = true
            let result = poll(device)
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

    private static func poll(_ device: IOHIDDevice) -> (opened: Bool, percent: Int?) {
        guard IOHIDDeviceOpen(device, IOOptionBits(kIOHIDOptionsTypeNone)) == kIOReturnSuccess else {
            return (false, nil)
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
    private var closing = false
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

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        statusItem = NSStatusBar.system.statusItem(
            withLength: NSStatusItem.variableLength)
        statusItem.button?.title = "🔋?"
        buildStatusMenu()
        configureTimer()
        refresh()
    }

    private func command(_ key: String, _ action: Selector) -> NSMenuItem {
        let item = NSMenuItem(title: AppText.text(key),
                              action: action, keyEquivalent: "")
        item.target = self
        return item
    }

    private func buildStatusMenu() {
        statusMenu = NSMenu(title: "AJAZZ Battery Tray")
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
        menu.addItem(command("Device diagnostics...", #selector(showDiagnostics)))
        menu.addItem(command("Copy diagnostic report", #selector(copyDeviceReport)))
        menu.addItem(command("Open battery history folder...",
                              #selector(openHistoryFolder)))
        return menu
    }

    private func buildSettingsMenu() -> NSMenu {
        let menu = NSMenu(title: AppText.text("Settings"))
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

    @objc private func copyDeviceReport() {
        let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"]
            as? String ?? "unknown"
        let report = "AJAZZ Battery Tray diagnostic report\n" +
            "Version: \(version)\n" +
            "macOS: \(ProcessInfo.processInfo.operatingSystemVersionString)\n" +
            ApexBattery.diagnostics()
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

    @objc private func showBluetoothBattery() {
        if bluetoothWindow == nil {
            bluetoothWindow = BluetoothBatteryWindowController()
        }
        bluetoothWindow?.showWindow(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    @objc private func showDiagnostics() {
        let alert = NSAlert()
        alert.messageText = AppText.text("AJAZZ APEX — Device diagnostics")
        alert.informativeText = ApexBattery.diagnostics()
        alert.alertStyle = .informational
        alert.runModal()
    }

    @objc private func syncClockNow() {
        manualClockSync = true
        refresh()
    }

    @objc private func refresh() {
        guard !polling, !closing else { return }
        polling = true
        let token = isolatedPolling ? ApexWorkerCancellation() : nil
        activeCancellation = token
        let manual = manualClockSync
        manualClockSync = false
        let automatic = autoClockEnabled
        let lastAttempt = lastClockAttempt
        let previouslyPresent = receiverWasPresent
        DispatchQueue.global(qos: .utility).async { [weak self] in
            let value = Self.readForPoll(token)
            let observedAt = Date()
            let elapsed = Date().timeIntervalSince(lastAttempt)
            let due = elapsed < 0 || elapsed >= 300
            let shouldSync = token?.isCancelled != true &&
                value.compatibleReceiverPresent == true && (manual ||
                (automatic && (due || !previouslyPresent)))
            let sent = shouldSync ? Self.clockForPoll(token) : false
            DispatchQueue.main.async {
                self?.completePoll(value, observedAt: observedAt, manual: manual,
                                   attempted: shouldSync, sent: sent)
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
                              attempted: Bool, sent: Bool) {
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
        if attempted { recordClockResult(sent) }
        sessionObservation.observe(value, at: observedAt)
        update(value)
        if queued { refresh() }
    }

    private func recordClockResult(_ sent: Bool) {
        lastClockAttempt = Date()
        lastClockSent = sent
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

    private func renderStatus(_ status: ApexBattery.Status) {
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
        statusItem.button?.toolTip = detailItem.title
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
        guard isolatedPolling, polling else { return .terminateNow }
        closing = true
        timer?.invalidate()
        activeCancellation?.cancel()
        return .terminateLater
    }

    @objc private func quit() { NSApp.terminate(nil) }
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
    let passed = ApexBoundedWorker.selfTest()
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
        !BluetoothBatteryPayload.likelyAjazz("Keyboard")
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
    observation.observe(.timedOut, at: testDate.addingTimeInterval(30))
    let preserved = observation.lastVerified == testDate
    observation.observe(.notConnected, at: testDate.addingTimeInterval(60))
    let provenanceValid = preserved && observation.lastVerified == nil &&
        ApexBattery.noSampleStatus(matched: true, opened: false) == .accessUnknown &&
        ApexBattery.noSampleStatus(matched: true, opened: true) == .unavailable &&
        ApexBattery.noSampleStatus(matched: false, opened: false) == .unsupportedCollection
    let valid = provenanceValid && sharedFrameValid && presenceValid && localizationValid && bluetoothValid && alertTests && timeoutValid &&
                selectedTests && jumpTests &&
                chartValid && historyValid &&
                clockValid && guardValid &&
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
