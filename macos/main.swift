import AppKit
import Foundation
import IOKit.hid

/// A status-only HID poll. No pairing, firmware or profile write commands.
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
        guard report.count >= 4,
              report[0] == 0x05,
              report[1] == 0,
              report[2] == 0,
              (1...100).contains(Int(report[3])) else {
            return nil
        }
        return Int(report[3])
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
            if read == kIOReturnSuccess && actualLength >= 4,
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
    private var timer: Timer?
    private var polling = false

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

    @objc private func refresh() {
        guard !polling else { return }
        polling = true
        DispatchQueue.global(qos: .utility).async { [weak self] in
            let value = ApexBattery.read()
            DispatchQueue.main.async {
                self?.update(value)
            }
        }
    }

    private func update(_ status: ApexBattery.Status) {
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
    print("Usage: AJAZZBatteryTray [--help] [--diagnose]")
    print("Requires macOS 13+ and a compatible VID_3151:PID_5007 receiver.")
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
