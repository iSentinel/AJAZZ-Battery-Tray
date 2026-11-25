"""Check the production independent BLE wiring without a Windows device."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class IndependentBleMonitorTests(unittest.TestCase):
    """Guard integration between scheduler and separate tray icons."""

    def test_production_scheduler(self) -> None:
        """The production session uses independent scheduling, not USB gating."""
        code = (ROOT / 'src/AjazzBatteryTray/TrayAppContext.cs').read_text()
        self.assertIn('BluetoothMultiSession _ble = new(independent: true)', code)
        poll = code.split('private void StartBluetoothPoll(', 1)[1].split(
            'private async Task PollBluetoothFallbackAsync(', 1)[0]
        self.assertNotIn('ReceiverPresent: false', poll)
        self.assertIn('_ble.TryBegin(', poll)

    def test_separate_icons_and_alerts(self) -> None:
        """An unrelated BLE device must neither hide nor silence USB."""
        code = (ROOT / 'src/AjazzBatteryTray/TrayAppContext.cs').read_text()
        self.assertIn('BluetoothExtraIcons(bluetoothPrimary ? primaryBle : null)', code)
        self.assertIn('bluetoothPrimary ? null : receiver?.Key', code)
        self.assertIn('_receivers.Apply(batch, _settings, _tray, false,', code)
        self.assertIn('BatteryDisplayState.PreferIndependentBluetooth(', code)


if __name__ == '__main__':
    unittest.main()
