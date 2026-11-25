"""Source contract for redacted, independent manual GATT evidence."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AppleGattEvidenceTests(unittest.TestCase):
    """Validate structural boundaries; not real Bluetooth callback tests."""

    def test_modern_timeout_generation(self) -> None:
        """An old timeout must not finish a newer selection of the same mouse."""
        code = (ROOT / 'macos/BluetoothBattery.swift').read_text()
        self.assertIn('let generation = attempt', code)
        self.assertIn('self.attempt == generation', code)
        self.assertIn('guard !pending else { return }', code)

    def test_characteristic_and_service_scope(self) -> None:
        """Both readers accept only the selected 180F/2A19 reply."""
        swift = (ROOT / 'macos/BluetoothBattery.swift').read_text()
        legacy = (ROOT / 'macos/high-sierra/main.m').read_text()
        self.assertIn('characteristic.uuid == batteryLevel', swift)
        self.assertIn('characteristic.service?.uuid == batteryService', swift)
        self.assertIn('characteristic.UUID isEqual:[CBUUID UUIDWithString:@"2A19"]', legacy)
        self.assertIn('characteristic.service.UUID isEqual:[CBUUID UUIDWithString:@"180F"]', legacy)

    def test_passive_evidence_no_identity_or_new_request(self) -> None:
        """Expose only prior outcome, timestamps and count in passive report."""
        swift = (ROOT / 'macos/BluetoothBattery.swift').read_text()
        summary = swift.split('var diagnosticSummary: String {', 1)[1].split(
            'private let batteryService', 1)[0]
        self.assertIn('Bluetooth last manual read', summary)
        for forbidden in ('retrieveConnected', 'readValue', 'device.name',
                          'identifier', 'connect(', 'scanForPeripherals'):
            self.assertNotIn(forbidden, summary)
        modern = (ROOT / 'macos/main.swift').read_text()
        self.assertIn('bluetoothWindow?.diagnosticSummary', modern)
        legacy = (ROOT / 'macos/high-sierra/main.m').read_text()
        self.assertIn('self.bluetoothLastRead ?: @"not requested"', legacy)
        self.assertIn('elapsed_ms=%.0f', legacy)


if __name__ == '__main__':
    unittest.main()
