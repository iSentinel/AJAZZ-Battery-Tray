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
    private let batteryService = CBUUID(string: "180F")
    private let batteryLevel = CBUUID(string: "2A19")

    /// Create a central manager only when the user explicitly requests it.
    func findConnected() {
        if manager == nil {
            onStatus?("Checking Bluetooth access...")
            manager = CBCentralManager(delegate: self, queue: nil)
        } else if manager?.state == .poweredOn {
            listConnected()
        } else {
            onStatus?("Bluetooth is not available or permission is denied.")
        }
    }

    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        if central.state == .poweredOn {
            listConnected()
        } else {
            devices = []
            onDevices?([])
            onStatus?("Enable Bluetooth and grant this app Bluetooth access.")
        }
    }

    private func listConnected() {
        guard let manager = manager else { return }
        let connected = manager.retrieveConnectedPeripherals(
            withServices: [batteryService])
        devices = connected.filter {
            BluetoothBatteryPayload.likelyAjazz($0.name)
        }
        let labels = devices.enumerated().map { index, device in
            "\(device.name ?? "AJAZZ APEX") (connected #\(index + 1))"
        }
        onDevices?(labels)
        onStatus?(labels.isEmpty
            ? "No connected AJAZZ mouse exposing Battery Service (180F)."
            : "Select a connected AJAZZ mouse to read Battery Level.")
    }

    /// Connect only to the explicitly selected, already connected candidate.
    func readSelected(at index: Int) {
        guard !pending, index >= 0, index < devices.count,
              manager?.state == .poweredOn else { return }
        let device = devices[index]
        selected = device
        pending = true
        onStatus?("Reading Battery Level from selected mouse...")
        device.delegate = self
        manager?.connect(device)
        DispatchQueue.main.asyncAfter(deadline: .now() + 10) { [weak self] in
            guard let self = self, self.pending, self.selected === device else {
                return
            }
            self.finish("Battery Service timed out or is unavailable.", device)
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
        finish("Selected mouse could not be connected for a read.", peripheral)
    }

    func peripheral(_ peripheral: CBPeripheral,
                    didDiscoverServices error: Error?) {
        guard pending, selected === peripheral else { return }
        guard error == nil,
              let service = peripheral.services?.first(where: {
                  $0.uuid == batteryService
              }) else {
            finish("Standard Battery Service is not readable.", peripheral)
            return
        }
        peripheral.discoverCharacteristics([batteryLevel], for: service)
    }

    func peripheral(_ peripheral: CBPeripheral,
                    didDiscoverCharacteristicsFor service: CBService,
                    error: Error?) {
        guard pending, selected === peripheral else { return }
        guard error == nil,
              let level = service.characteristics?.first(where: {
                  $0.uuid == batteryLevel
              }) else {
            finish("Battery Level (2A19) is not exposed.", peripheral)
            return
        }
        peripheral.readValue(for: level)
    }

    func peripheral(_ peripheral: CBPeripheral,
                    didUpdateValueFor characteristic: CBCharacteristic,
                    error: Error?) {
        guard pending, selected === peripheral else { return }
        let percent = error == nil
            ? BluetoothBatteryPayload.parse(characteristic.value) : nil
        let message = percent.map { "Bluetooth battery: \($0)% (experimental)" } ??
                      "No valid Battery Level was returned."
        finish(message, peripheral)
    }

    private func finish(_ message: String, _ device: CBPeripheral) {
        guard pending, selected === device else { return }
        pending = false
        selected = nil
        manager?.cancelPeripheralConnection(device)
        onStatus?(message)
    }
}

/// Small native window. Does not automatically poll or save Bluetooth identities.
final class BluetoothBatteryWindowController: NSWindowController {
    private let inspector = BluetoothBatteryInspector()
    private let selection = NSPopUpButton()
    private let status = NSTextField(labelWithString: "")
    private let readButton = NSButton(title: "Read selected battery",
                                      target: nil, action: nil)

    init() {
        let frame = NSRect(x: 0, y: 0, width: 560, height: 260)
        let window = NSWindow(contentRect: frame,
                              styleMask: [.titled, .closable],
                              backing: .buffered, defer: false)
        window.title = "AJAZZ APEX — Bluetooth battery check"
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
            "Manual check of already connected AJAZZ Bluetooth mice. " +
            "No scanning, pairing, background polling or settings writes.")
        intro.frame = NSRect(x: 22, y: 174, width: 516, height: 58)
        view.addSubview(intro)

        let find = NSButton(title: "Find connected AJAZZ mice", target: self,
                            action: #selector(findDevices))
        find.frame = NSRect(x: 20, y: 138, width: 240, height: 29)
        view.addSubview(find)

        selection.frame = NSRect(x: 23, y: 97, width: 512, height: 28)
        selection.isEnabled = false
        view.addSubview(selection)

        readButton.frame = NSRect(x: 22, y: 55, width: 200, height: 30)
        readButton.target = self
        readButton.action = #selector(readSelected)
        readButton.isEnabled = false
        view.addSubview(readButton)

        status.frame = NSRect(x: 224, y: 34, width: 310, height: 52)
        status.stringValue = "Choose Find to inspect connected mice."
        view.addSubview(status)
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
