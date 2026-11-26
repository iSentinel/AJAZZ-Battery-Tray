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
        self.assertIn('bluetoothPrimary || linkedPrimary is not null ? null : receiver?.Key', code)
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


    def test_cache_presentation_remains_distinct(self) -> None:
        """Propagate cached status to dashboard and both icon paths."""
        root = ROOT / 'src/AjazzBatteryTray'
        code = (root / 'TrayAppContext.cs').read_text()
        self.assertIn('fresh, _ble.LastSuccess(key), cached, _ble.LastSuccess(key)', code)
        self.assertIn('stale = displayPercent.HasValue', code)
        self.assertIn('!fresh.HasValue && cached.HasValue', code)
        self.assertIn('retainCachedBle', code)
        extra = (root / 'ReceiverMonitor.cs').read_text()
        self.assertIn('stale: item.Stale', extra)
        self.assertIn('response.IsFreshGatt && response.Percent is int percent', code)

    def test_display_ages_without_ble_or_usb_poll_completion(self) -> None:
        """The existing independent timer refreshes presentation without new telemetry."""
        code = (ROOT / 'src/AjazzBatteryTray/TrayAppContext.cs').read_text()
        timer = code.split('private void OnBleTimer(', 1)[1].split(
            'private async Task RestoreBleConsentAsync(', 1)[0]
        self.assertIn('if (_closing) return;', timer)
        self.assertIn('else if (_latestUsbReading is not null || _aulaLatest is not null)', timer)
        self.assertIn('RefreshDeviceDisplay(publishSnapshot: false);', timer)
        self.assertNotIn('PollSoon()', timer)
        self.assertNotIn('ApplyReading(', timer)
        display = code.split('private void RefreshDeviceDisplay(', 1)[1].split(
            'private sealed record LinkedTrayDevice', 1)[0]
        self.assertIn('publishSnapshot);', display)
        self.assertIn('RefreshDashboard(publishSnapshot);', display)
        self.assertIn('if (!_diagnosticsBusy && _statusItem.Text != status)', display)
        dashboard = code.split('private void RefreshDashboard(', 1)[1].split(
            'private void PublishLocalSnapshot(', 1)[0]
        self.assertIn('if (publishSnapshot) PublishLocalSnapshot();', dashboard)
        self.assertIn('skipUnchanged: !publishSnapshot', dashboard)

    def test_explicit_links_project_single_icon(self) -> None:
        """Keep link consent explicit, independent telemetry and local preferences."""
        root = ROOT / 'src/AjazzBatteryTray'
        code = (root / 'TrayAppContext.cs').read_text()
        self.assertIn('TransportLinks.CanLink(', code)
        self.assertIn('same physical mouse. Continue?', code)
        self.assertIn('hiddenUsb.UnionWith(_settings.BleUsbLinks.Values)', code)
        self.assertIn('!_settings.BleUsbLinks.ContainsKey(x.Key)', code)
        self.assertIn('_settings.BleUsbLinks.Remove(key)', code)
        self.assertIn('TransportLinks.Select(usbValue,', code)
        self.assertIn('linked.Where(x => x != linkedPrimary)', code)
        self.assertNotIn('BleUsbLinks', (root / 'PreferencesBackup.cs').read_text())
        self.assertIn('wanted.Add(item.Key)', (root / 'ReceiverMonitor.cs').read_text())

    def test_sticky_linked_primary_keeps_other_icons(self) -> None:
        """A linked primary must not swallow an unrelated receiver or BLE icon."""
        code = (ROOT / 'src/AjazzBatteryTray/TrayAppContext.cs').read_text()
        self.assertIn('TransportLinks.SelectPrimary(_primaryLinkedUsbKey,', code)
        self.assertIn('if (linkedPrimary is not null) bluetoothPrimary = false;', code)
        self.assertIn('bluetoothPrimary || linkedPrimary is not null ? null : receiver?.Key', code)
        self.assertIn('BluetoothExtraIcons(bluetoothPrimary ? primaryBle : null)', code)


if __name__ == '__main__':
    unittest.main()
