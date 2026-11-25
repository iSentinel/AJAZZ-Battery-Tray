import AppKit
import CoreBluetooth
import Foundation

/// Validates Bluetooth SIG Battery Level values without inventing a reading.
enum BluetoothBatteryPayload {
    static func parse(_ data: Data?) -> Int? {
        guard let data = data, data.count == 1,
              let value = data.first, value <= 100 else { return nil }
        return Int(value)
    }

    static func likelyAjazz(_ name: String?) -> Bool {
        guard let name = name?.uppercased() else { return false }
        return name.contains("AJAZZ") || name.contains("AJ159") ||
               name.contains("AJ179")
    }
}

/// A manually triggered, read-only inspector for connected Bluetooth LE mice.
final class BluetoothBatteryInspector: NSObject,
    CBCentralManagerDelegate, CBPeripheralDelegate {

    var onDevices: (([String]) -> Void)?
    var onStatus: ((String) -> Void)?
    private var manager: CBCentralManager?
    private var devices: [CBPeripheral] = []
    private var selected: CBPeripheral?
    private var pending = false
    private var attempt: UInt = 0
    private var started = 0.0
    private var discovery = "not requested"
    private var lastRead = "not requested"

    /// Redacted session-only observations, never a request or device identity.
    var diagnosticSummary: String {
        "Bluetooth discovery: \(discovery)\n" +
        "Bluetooth manual 180F/2A19 pending: \(pending)\n" +
        "Bluetooth last manual read: \(lastRead)"
    }
    private let batteryService = CBUUID(string: "180F")
    private let batteryLevel = CBUUID(string: "2A19")

    /// Create a central manager only when the user explicitly requests it.
    func findConnected() {
        guard !pending else { return }
        if manager == nil {
            discovery = "checking access"
            onStatus?(AppText.text("Checking Bluetooth access..."))
            manager = CBCentralManager(delegate: self, queue: nil)
        } else if manager?.state == .poweredOn {
            listConnected()
        } else {
            discovery = "access unavailable"
            onStatus?(AppText.text("Bluetooth is not available or permission is denied."))
        }
    }

    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        if central.state == .poweredOn {
            if !pending { listConnected() }
        } else {
            discovery = "access unavailable; state=\(central.state.rawValue)"
            devices = []
            onDevices?([])
            if let device = selected {
                finish(AppText.text("Bluetooth is not available or permission is denied."), device, outcome: "access unavailable")
            }
            onStatus?(AppText.text("Enable Bluetooth and grant this app Bluetooth access."))
        }
    }

    private func listConnected() {
        guard let manager = manager else { return }
        let connected = manager.retrieveConnectedPeripherals(
            withServices: [batteryService])
        devices = connected.filter {
            BluetoothBatteryPayload.likelyAjazz($0.name)
        }
        discovery = "connected candidates=\(devices.count)"
        let labels = devices.enumerated().map { index, device in
            "\(device.name ?? "AJAZZ APEX") (connected #\(index + 1))"
        }
        onDevices?(labels)
        onStatus?(labels.isEmpty
            ? AppText.text("No connected AJAZZ mouse exposing Battery Service (180F).")
            : AppText.text("Select a connected AJAZZ mouse to read Battery Level."))
    }

    /// Connect only to the explicitly selected, already connected candidate.
    func readSelected(at index: Int) {
        guard !pending, index >= 0, index < devices.count,
              manager?.state == .poweredOn else { return }
        let device = devices[index]
        selected = device
        pending = true
        attempt &+= 1
        let generation = attempt
        started = ProcessInfo.processInfo.systemUptime
        onStatus?(AppText.text("Reading Battery Level from selected mouse..."))
        device.delegate = self
        manager?.connect(device)
        DispatchQueue.main.asyncAfter(deadline: .now() + 10) { [weak self] in
            guard let self = self, self.pending, self.selected === device,
                  self.attempt == generation else {
                return
            }
            self.finish(AppText.text("Battery Service timed out or is unavailable."), device, outcome: "timeout")
        }
    }

    func centralManager(_ central: CBCentralManager,
                        didConnect peripheral: CBPeripheral) {
        guard pending, selected === peripheral else { return }
        peripheral.discoverServices([batteryService])
    }

    func centralManager(_ central: CBCentralManager,
                        didFailToConnect peripheral: CBPeripheral,
                        error: Error?) {
        finish(AppText.text("Selected mouse could not be connected for a read."), peripheral, outcome: "connection failed")
    }

    func peripheral(_ peripheral: CBPeripheral,
                    didDiscoverServices error: Error?) {
        guard pending, selected === peripheral else { return }
        guard error == nil,
              let service = peripheral.services?.first(where: {
                  $0.uuid == batteryService
              }) else {
            finish(AppText.text("Standard Battery Service is not readable."), peripheral, outcome: "service unavailable")
            return
        }
        peripheral.discoverCharacteristics([batteryLevel], for: service)
    }

    func peripheral(_ peripheral: CBPeripheral,
                    didDiscoverCharacteristicsFor service: CBService,
                    error: Error?) {
        guard pending, selected === peripheral, service.uuid == batteryService else { return }
        guard error == nil,
              let level = service.characteristics?.first(where: {
                  $0.uuid == batteryLevel
              }) else {
            finish(AppText.text("Battery Level (2A19) is not exposed."), peripheral, outcome: "characteristic unavailable")
            return
        }
        peripheral.readValue(for: level)
    }

    func peripheral(_ peripheral: CBPeripheral,
                    didUpdateValueFor characteristic: CBCharacteristic,
                    error: Error?) {
        guard pending, selected === peripheral, characteristic.uuid == batteryLevel,
              characteristic.service?.uuid == batteryService else { return }
        let percent = error == nil
            ? BluetoothBatteryPayload.parse(characteristic.value) : nil
        let message = percent.map {
            AppText.format("Bluetooth battery: %d%% (experimental)", $0)
        } ??
                      AppText.text("No valid Battery Level was returned.")
        finish(message, peripheral, outcome: percent == nil ? "invalid reply" : "fresh GATT", percent: percent)
    }

    func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral,
                        error: Error?) {
        guard peripheral.state == .disconnected else { return }
        finish(AppText.text("Battery Service timed out or is unavailable."),
               peripheral, outcome: "disconnected")
    }

    private func finish(_ message: String, _ device: CBPeripheral, outcome: String,
                        percent: Int? = nil) {
        guard pending, selected === device else { return }
        pending = false
        selected = nil
        device.delegate = nil
        let elapsed = (ProcessInfo.processInfo.systemUptime - started) * 1000
        let level = percent.map { String($0) + "%" } ?? "unknown"
        lastRead = "outcome=\(outcome); battery=\(level); UTC=\(ISO8601DateFormatter().string(from: Date())); " +
            String(format: "elapsed_ms=%.0f", elapsed)
        manager?.cancelPeripheralConnection(device)
        onStatus?(message)
    }
}

/// Small native window. Does not automatically poll or save Bluetooth identities.
final class BluetoothBatteryWindowController: NSWindowController {
    private let inspector = BluetoothBatteryInspector()
    var diagnosticSummary: String { inspector.diagnosticSummary }
    private let selection = NSPopUpButton()
    private let status = NSTextField(labelWithString: "")
    private let readButton = NSButton(title: AppText.text("Read selected battery"),
                                      target: nil, action: nil)
    private var findButton: NSButton?
    private var introLabel: NSTextField?

    init() {
        let frame = NSRect(x: 0, y: 0, width: 560, height: 260)
        let window = NSWindow(contentRect: frame,
                              styleMask: [.titled, .closable],
                              backing: .buffered, defer: false)
        window.title = AppText.text("AJAZZ APEX — Bluetooth battery check")
        window.isReleasedWhenClosed = false
        super.init(window: window)
        setup()
        connectCallbacks()
    }

    required init?(coder: NSCoder) {
        fatalError("Create BluetoothBatteryWindowController directly")
    }

    private func setup() {
        guard let view = window?.contentView else { return }
        let intro = NSTextField(wrappingLabelWithString:
            AppText.text("Manual check of already connected AJAZZ Bluetooth mice.") +
            " " + AppText.text("No scanning, pairing, background polling or settings writes."))
        intro.frame = NSRect(x: 22, y: 174, width: 516, height: 58)
        view.addSubview(intro)
        introLabel = intro

        let find = NSButton(title: AppText.text("Find connected AJAZZ mice"), target: self,
                            action: #selector(findDevices))
        find.frame = NSRect(x: 20, y: 138, width: 240, height: 29)
        view.addSubview(find)
        findButton = find

        selection.frame = NSRect(x: 23, y: 97, width: 512, height: 28)
        selection.isEnabled = false
        view.addSubview(selection)

        readButton.frame = NSRect(x: 22, y: 55, width: 200, height: 30)
        readButton.target = self
        readButton.action = #selector(readSelected)
        readButton.isEnabled = false
        view.addSubview(readButton)

        status.frame = NSRect(x: 224, y: 34, width: 310, height: 52)
        status.stringValue = AppText.text("Choose Find to inspect connected mice.")
        view.addSubview(status)
    }

    /// Refresh an open inspector without repeating discovery or a GATT read.
    func applyLanguage() {
        window?.title = AppText.text("AJAZZ APEX — Bluetooth battery check")
        readButton.title = AppText.text("Read selected battery")
        findButton?.title = AppText.text("Find connected AJAZZ mice")
        introLabel?.stringValue = AppText.text(
            "Manual check of already connected AJAZZ Bluetooth mice.") +
            " " + AppText.text(
                "No scanning, pairing, background polling or settings writes.")
        if selection.numberOfItems == 0 {
            status.stringValue = AppText.text(
                "Choose Find to inspect connected mice.")
        }
    }

    private func connectCallbacks() {
        inspector.onDevices = { [weak self] names in
            self?.selection.removeAllItems()
            self?.selection.addItems(withTitles: names)
            self?.selection.isEnabled = !names.isEmpty
            self?.readButton.isEnabled = !names.isEmpty
        }
        inspector.onStatus = { [weak self] message in
            self?.status.stringValue = message
        }
    }

    @objc private func findDevices() {
        inspector.findConnected()
    }

    @objc private func readSelected() {
        inspector.readSelected(at: selection.indexOfSelectedItem)
    }
}
