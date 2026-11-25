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

    def test_persistent_consent_is_local_and_fresh(self) -> None:
        """Restore only exact consent matches, never cached Windows charge."""
        code = (ROOT / 'src/AjazzBatteryTray/TrayAppContext.cs').read_text()
        self.assertIn('BleConsent.Key(candidate.DeviceId)', code)
        self.assertIn('!_settings.ConsentedBleEndpoints.Contains(key) || !_ble.Restore(key)', code)
        self.assertIn('candidate with { WindowsPercent = null }', code)
        self.assertIn('_settings.ConsentedBleEndpoints.Remove(key)', code)
        self.assertIn('_bleTimer.Tick += OnBleTimer', code)
        self.assertIn('_bleTimer.Dispose()', code)
        backup = (ROOT / 'src/AjazzBatteryTray/PreferencesBackup.cs').read_text()
        self.assertNotIn('ConsentedBleEndpoints', backup)



if __name__ == '__main__':
    unittest.main()
