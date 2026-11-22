using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Owns the tray menu, polling loop, preferences and notifications.</summary>
public sealed class TrayAppContext : ApplicationContext
{
    private readonly NotifyIcon _tray;
    private readonly System.Windows.Forms.Timer _timer;
    private readonly System.Windows.Forms.Timer _aulaTimer;
    private readonly DevicePollSchedule _usbSchedule = new();
    private readonly System.Windows.Forms.Timer _updateTimer = new() { Interval = 10000 };
    private readonly AutomaticUpdatePolicy _updatePolicy = new();
    private CancellationTokenSource? _updateRequestCancellation;
    private bool _manualUpdateDialog;
    private bool _automaticUpdateBusy;
    private bool _forcePoll;
    private readonly AjazzHidReader _reader = new();
    private readonly AulaL99Reader _aulaReader = new();
    private readonly AlertPolicy _aulaAlerts = new();
    private readonly BatteryHistory _aulaHistory = new("aula-l99-history.csv");
    private BatteryHistoryForm? _aulaHistoryWindow;
    private AulaL99Reading? _aulaLatest;
    private readonly AulaBatteryState _aulaBattery = new();
    private DateTimeOffset? _aulaLastReadAt;
    private bool _aulaBusy;
    private int _aulaGeneration;
    private bool _hostMetricsBusy;
    private bool _pnpPreviewBusy;
    private ToolStripMenuItem _aulaStatus = new();
    private readonly ReceiverMonitor _receivers = new();
    private readonly ConnectionAlertPolicy _aulaConnection = new();
    private readonly BatteryHistory _history = new();
    private BatteryHistoryForm? _historyWindow;
    private DeviceDashboardForm? _dashboard;
    private BluetoothBatteryForm? _bluetoothWindow;
    private sealed record BleSlot(BluetoothCandidate Candidate, int Number, AlertPolicy Alerts);
    private readonly BluetoothMultiSession _ble = new();
    private readonly Dictionary<string, BleSlot> _bleSlots = new(StringComparer.Ordinal);
    private int _bleSequence;
    private ToolStripMenuItem _bleDevicesMenu = new();
    private static string BleKey(BluetoothCandidate candidate) => candidate.DeviceId.ToUpperInvariant();
    private bool BleEnabled => _bleSlots.Count > 0;
    private string? PrimaryBleKey => _bleSlots.OrderBy(x => x.Value.Number).Select(x => x.Key).FirstOrDefault();
    private static string BleLabel(BleSlot slot) => $"AJAZZ — Bluetooth #{slot.Number}";
    private static string BleDisplayLabel(BleSlot slot)
        => $"{slot.Candidate.DisplayName} (BLE #{slot.Number})";
    private AjazzHidReader.Reading? _latestUsbReading;
    private DateTimeOffset? _latestUsbReadAt;
    private bool _diagnosticsBusy;
    private ToolStripMenuItem _bluetoothStatus = new();
    private ToolStripMenuItem _disableBluetooth = new();
    private ToolStripMenuItem _refreshBluetooth = new();
    private string _lastSource = "";
    private string _lastDevice = "AJAZZ APEX";
    private readonly DockClockSchedule _clockSchedule = new();
    private ToolStripMenuItem _clockStatus = new();
    private bool _manualClockSync;
    private DateTime? _lastClockUpdate;
    private bool _lastClockSucceeded;
    private readonly AppSettings _settings = AppSettings.Load();
    private ToolStripMenuItem _statusItem = new();
    private ToolStripMenuItem _devicesMenu = new();
    private ToolStripMenuItem _startupItem = new();
    private Icon? _icon;
    private int? _lastPercent;
    private bool _lastConnected;
    private bool _lastStale;
    private bool _busy;
    private bool _closing;

    public TrayAppContext()
    {
        UiText.SetLanguage(_settings.Language);
        _tray = new NotifyIcon { Text = "AJAZZ APEX: " + UiText.Get("Connecting...") };
        UpdateIcon(null, false);
        _tray.ContextMenuStrip = BuildMenu();
        _tray.Visible = true;
        _tray.DoubleClick += (_, _) => PollSoon();

        _timer = new System.Windows.Forms.Timer { Interval = 1000 };
        _timer.Tick += OnPollTimer;
        _aulaTimer = new System.Windows.Forms.Timer { Interval = 1000 };
        _aulaTimer.Tick += (_, _) => _ = PollAulaAsync();
        _timer.Start();
        if (_settings.MonitorAulaL99) _aulaTimer.Start();
        _updateTimer.Tick += (_, _) => _ = PollUpdatesAsync();
        ApplyUpdatePreferences();
        _updateTimer.Start();
    }

    private ContextMenuStrip BuildMenu()
    {
        ContextMenuStrip menu = new();
        _statusItem = new ToolStripMenuItem("AJAZZ APEX — " +
            UiText.Get("Connecting...")) { Enabled = false };
        menu.Items.Add(_statusItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(UiText.Get("Device Manager"), null, (_, _) => ShowDashboard());
        menu.Items.Add(UiText.Get("Refresh now"), null, (_, _) => PollSoon());
        _devicesMenu = new ToolStripMenuItem(UiText.Get("AJAZZ receivers"));
        _devicesMenu.DropDownOpening += (_, _) => _receivers.PopulateMenu(_devicesMenu, EditReceiverName, IsTrayVisible,
            ToggleTrayVisibility, state => EditTrayColor(state.Key, state.DisplayLabel),
            state => EditDeviceAlerts(state.Key, state.DisplayLabel),
            state => EditDeviceInterval(state.Key, state.DisplayLabel));
        _receivers.PopulateMenu(_devicesMenu, EditReceiverName, IsTrayVisible,
            ToggleTrayVisibility, state => EditTrayColor(state.Key, state.DisplayLabel),
            state => EditDeviceAlerts(state.Key, state.DisplayLabel),
            state => EditDeviceInterval(state.Key, state.DisplayLabel));
        menu.Items.Add(_devicesMenu);
        menu.Items.Add(UiText.Get("Legacy battery history..."), null,
            (_, _) => ShowHistory());
        menu.Items.Add(BuildBluetoothMenu());
        menu.Items.Add(BuildAulaMenu());
        menu.Items.Add(UiText.Get("Sync dock time now"), null,
            (_, _) => RequestClockSync());
        _clockStatus = new ToolStripMenuItem { Enabled = false };
        UpdateClockStatus();
        menu.Items.Add(_clockStatus);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(BuildSettingsMenu());
        menu.Items.Add(BuildDiagnosticsMenu());
        menu.Items.Add(UiText.Get("Check for updates..."), null, (_, _) =>
        {
            ShowManualUpdateCheck();
        });
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(UiText.Get("Verify downloaded release..."), null, (_, _) =>
        {
            if (_closing) return;
            using var dialog = new ArtifactVerificationForm();
            dialog.ShowDialog();
        });
        menu.Items.Add(UiText.Get("Exit"), null, (_, _) => ExitThread());
        return menu;
    }

    private string AulaName => DeviceAliasRules.DisplayName("AULA L99",
        _settings.DeviceAliases.GetValueOrDefault(DeviceAliasRules.AulaSlot));

    private void EditReceiverName(ReceiverMonitor.State state)
    {
        if (!EditLocalName(state.Key, state.Label)) return;
        state.Alias = _settings.DeviceAliases.GetValueOrDefault(state.Key);
        state.Window?.Dispose();
        state.Window = null;
        RefreshDeviceDisplay();
    }

    private void EditAulaName()
    {
        if (!EditLocalName(DeviceAliasRules.AulaSlot, "AULA L99")) return;
        _aulaHistoryWindow?.Dispose();
        _aulaHistoryWindow = null;
        UpdateAulaStatus();
        RefreshDeviceDisplay();
    }

    private bool EditLocalName(string key, string model)
    {
        if (_closing || !DeviceAliasRules.ValidKey(key)) return false;
        string? original = _settings.DeviceAliases.GetValueOrDefault(key);
        using var dialog = new DeviceAliasForm(model, original);
        if (dialog.ShowDialog() != DialogResult.OK || _closing) return false;
        if (dialog.Alias.Length == 0) _settings.DeviceAliases.Remove(key);
        else _settings.DeviceAliases[key] = dialog.Alias;
        if (_settings.Save()) return true;
        if (original is null) _settings.DeviceAliases.Remove(key);
        else _settings.DeviceAliases[key] = original;
        MessageBox.Show(UiText.Get("Unable to save local device name."),
            UiText.Get("Edit local name..."), MessageBoxButtons.OK, MessageBoxIcon.Warning);
        return false;
    }

    private bool IsTrayVisible(string key)
        => TrayVisibilityRules.IsVisible(_settings.HiddenTrayDevices, key);

    private void ToggleTrayVisibility(string key)
    {
        if (_closing || !DeviceAliasRules.ValidKey(key)) return;
        bool wasVisible = IsTrayVisible(key);
        if (wasVisible) _settings.HiddenTrayDevices.Add(key);
        else _settings.HiddenTrayDevices.Remove(key);
        if (!_settings.Save())
        {
            if (wasVisible) _settings.HiddenTrayDevices.Remove(key);
            else _settings.HiddenTrayDevices.Add(key);
            MessageBox.Show(UiText.Get("Unable to save device preference."),
                UiText.Get("Settings"), MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        RefreshDeviceDisplay();
    }

    private string DeviceColor(string key)
        => TrayColorRules.Normalize(_settings.DeviceTrayColors.GetValueOrDefault(key));

    private void EditTrayColor(string key, string name)
    {
        if (_closing || !DeviceAliasRules.ValidKey(key)) return;
        string? original = _settings.DeviceTrayColors.GetValueOrDefault(key);
        using var dialog = new TrayColorForm(name, DeviceColor(key));
        if (dialog.ShowDialog() != DialogResult.OK || _closing) return;
        if (dialog.Choice == TrayColorRules.Default) _settings.DeviceTrayColors.Remove(key);
        else _settings.DeviceTrayColors[key] = dialog.Choice;
        if (!_settings.Save())
        {
            if (original is null) _settings.DeviceTrayColors.Remove(key);
            else _settings.DeviceTrayColors[key] = original;
            MessageBox.Show(UiText.Get("Unable to save device preference."),
                UiText.Get("Settings"), MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        RefreshDeviceDisplay();
    }

    private void EditDeviceAlerts(string key, string name)
    {
        if (_closing || !DeviceAliasRules.ValidKey(key)) return;
        int? original = _settings.DeviceAlertMasks.TryGetValue(key, out int value) ? value : null;
        using var dialog = new DeviceAlertForm(name, original, _settings.GlobalAlertMask);
        if (dialog.ShowDialog() != DialogResult.OK || _closing) return;
        if (dialog.Mask is int mask) _settings.DeviceAlertMasks[key] = mask;
        else _settings.DeviceAlertMasks.Remove(key);
        if (!_settings.Save())
        {
            if (original is int old) _settings.DeviceAlertMasks[key] = old;
            else _settings.DeviceAlertMasks.Remove(key);
            MessageBox.Show(UiText.Get("Unable to save device preference."),
                UiText.Get("Settings"), MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private void EditDeviceInterval(string key, string name)
    {
        if (_closing || !DeviceAliasRules.ValidKey(key)) return;
        int? original = _settings.DevicePollIntervals.TryGetValue(key, out int value) ? value : null;
        using var dialog = new DeviceIntervalForm(name, original, _settings.PollSeconds);
        if (dialog.ShowDialog() != DialogResult.OK || _closing) return;
        if (dialog.Interval is int seconds) _settings.DevicePollIntervals[key] = seconds;
        else _settings.DevicePollIntervals.Remove(key);
        if (!_settings.Save())
        {
            if (original is int old) _settings.DevicePollIntervals[key] = old;
            else _settings.DevicePollIntervals.Remove(key);
            MessageBox.Show(UiText.Get("Unable to save device preference."),
                UiText.Get("Settings"), MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        if (key == DeviceAliasRules.AulaSlot)
        {
            if (_settings.MonitorAulaL99 && !_aulaBusy)
            {
                _aulaTimer.Stop();
                _aulaTimer.Interval = 100;
                _aulaTimer.Start();
            }
        }
        else PollSoon();
    }

    private void ShowDashboard()
    {
        if (_closing) return;
        if (_dashboard is null || _dashboard.IsDisposed)
            _dashboard = new DeviceDashboardForm(PollSoon,
                () => _ = ShowExtendedDiagnosticsAsync(),
                () => _ = ShowHostMetricsAsync());
        RefreshDashboard();
        _dashboard.Show();
        _dashboard.BringToFront();
    }

    private void RefreshDashboard()
    {
        if (_dashboard is not { IsDisposed: false }) return;
        List<DeviceDashboardForm.Entry> entries = new();
        foreach (var receiver in _receivers.Devices)
        {
            var reading = receiver.Reading;
            var item = DeviceDashboardState.FromPoll(receiver.DisplayLabel, "2.4 GHz",
                true, reading.PresenceKnown, receiver.Present, reading.Percent,
                receiver.MeasuredAt, scheduled: receiver.ScheduledSkip);
            entries.Add(new(item, () => ReceiverMonitor.ShowHistory(receiver), receiver.Key,
                () => EditReceiverName(receiver), IsTrayVisible(receiver.Key),
                () => ToggleTrayVisibility(receiver.Key),
                () => EditTrayColor(receiver.Key, receiver.DisplayLabel),
                () => EditDeviceAlerts(receiver.Key, receiver.DisplayLabel),
                () => EditDeviceInterval(receiver.Key, receiver.DisplayLabel)));
        }
        if (entries.Count == 0)
        {
            var reading = _latestUsbReading;
            entries.Add(new(DeviceDashboardState.FromPoll("AJAZZ APEX", "2.4 GHz",
                reading is not null, reading?.PresenceKnown == true,
                reading?.ReceiverPresent == true, reading?.Percent, _latestUsbReadAt)));
        }
        entries.Add(new(AulaDashboardState(), ShowAulaHistory, DeviceAliasRules.AulaSlot,
            EditAulaName, IsTrayVisible(DeviceAliasRules.AulaSlot),
            () => ToggleTrayVisibility(DeviceAliasRules.AulaSlot),
            () => EditTrayColor(DeviceAliasRules.AulaSlot, AulaName),
            () => EditDeviceAlerts(DeviceAliasRules.AulaSlot, AulaName),
            () => EditDeviceInterval(DeviceAliasRules.AulaSlot, AulaName)));
        foreach (var pair in _bleSlots.OrderBy(x => x.Value.Number))
            entries.Add(new(BluetoothDashboardState(pair.Key, pair.Value), Key: $"BLE:{pair.Value.Number}"));
        _dashboard.SetEntries(entries);
    }

    private DeviceDashboardState AulaDashboardState()
    {
        if (!_settings.MonitorAulaL99 && _aulaLatest is null)
            return new(AulaName, "2.4 GHz", DeviceDashboardStatus.Disabled, null, null);
        var state = DeviceDashboardState.FromPoll(AulaName, "2.4 GHz",
            _aulaLatest is not null, _aulaLatest?.PresenceKnown == true,
            _aulaLatest?.ReceiverPresent == true, _aulaLatest?.Percent,
            _aulaLastReadAt, AulaDisplayPercent(), _aulaBattery.LastGoodAt,
            scheduled: _settings.MonitorAulaL99);
        return !_settings.MonitorAulaL99 && state.Status == DeviceDashboardStatus.Fresh
            ? state with { Status = DeviceDashboardStatus.ManualReading } : state;
    }

    private DeviceDashboardState BluetoothDashboardState(string key, BleSlot slot)
    {
        string name = BleDisplayLabel(slot);
        const string transport = "Bluetooth";
        if (_latestUsbReading is not { PresenceKnown: true })
            return new(name, transport, DeviceDashboardStatus.PresenceUnknown, null, null);
        if (_latestUsbReading.ReceiverPresent)
            return new(name, transport, DeviceDashboardStatus.Standby, null, null);
        int? percent = _ble.VisiblePercent(key, true, false, DateTimeOffset.UtcNow);
        return new(name, transport, percent.HasValue
            ? DeviceDashboardStatus.Fresh : DeviceDashboardStatus.NoReply,
            percent, percent.HasValue ? _ble.LastSuccess(key) : null);
    }

    private ToolStripMenuItem BuildBluetoothMenu()
    {
        ToolStripMenuItem menu = new(UiText.Get("Bluetooth"));
        menu.DropDownItems.Add(UiText.Get("Check paired Bluetooth battery..."),
            null, (_, _) => ShowBluetoothBattery());
        _bluetoothStatus = new ToolStripMenuItem { Enabled = false };
        menu.DropDownItems.Add(_bluetoothStatus);
        _disableBluetooth = new ToolStripMenuItem(
            UiText.Get("Disable Bluetooth tray fallback"))
        {
            Enabled = BleEnabled
        };
        _disableBluetooth.Click += (_, _) => DisableAllBluetooth();
        menu.DropDownItems.Add(_disableBluetooth);
        _refreshBluetooth = new ToolStripMenuItem(
            UiText.Get("Refresh Bluetooth battery now"));
        _refreshBluetooth.Click += (_, _) => StartBluetoothPoll(
            _latestUsbReading?.ReceiverPresent ?? false, force: true);
        menu.DropDownItems.Add(_refreshBluetooth);
        _bleDevicesMenu = new ToolStripMenuItem(UiText.Get("Opted-in BLE devices"));
        _bleDevicesMenu.DropDownOpening += (_, _) => PopulateBleMenu();
        menu.DropDownItems.Add(_bleDevicesMenu);
        UpdateBluetoothStatus();
        return menu;
    }

    private ToolStripMenuItem BuildAulaMenu()
    {
        ToolStripMenuItem menu = new(UiText.Get("AULA L99 (experimental)"));
        menu.DropDownOpening += (_, _) => UpdateAulaStatus();
        _aulaStatus = new ToolStripMenuItem { Enabled = false };
        menu.DropDownItems.Add(_aulaStatus);
        menu.DropDownItems.Add(UiText.Get("Read AULA battery once"), null,
            (_, _) => _ = PollAulaAsync(manual: true));
        ToolStripMenuItem auto = new(
            UiText.Get("Monitor AULA automatically (experimental)"))
        {
            Checked = _settings.MonitorAulaL99, CheckOnClick = true
        };
        auto.CheckedChanged += (_, _) =>
        {
            _aulaGeneration++;
            _settings.MonitorAulaL99 = auto.Checked;
            _aulaLatest = null;
            _aulaLastReadAt = null;
            _aulaBattery.Reset();
            _settings.Save();
            _aulaTimer.Stop();
            if (auto.Checked) _ = PollAulaAsync(manual: true);
            UpdateAulaStatus();
            RefreshDeviceDisplay();
        };
        menu.DropDownItems.Add(auto);
        menu.DropDownItems.Add(UiText.Get("Edit local name..."), null,
            (_, _) => EditAulaName());
        ToolStripMenuItem visibility = new(UiText.Get("Show device in tray"));
        menu.DropDownOpening += (_, _) =>
            visibility.Checked = IsTrayVisible(DeviceAliasRules.AulaSlot);
        visibility.Click += (_, _) =>
        {
            ToggleTrayVisibility(DeviceAliasRules.AulaSlot);
            visibility.Checked = IsTrayVisible(DeviceAliasRules.AulaSlot);
        };
        menu.DropDownItems.Add(visibility);
        menu.DropDownItems.Add(UiText.Get("Tray icon color..."), null,
            (_, _) => EditTrayColor(DeviceAliasRules.AulaSlot, AulaName));
        menu.DropDownItems.Add(UiText.Get("Device battery alerts..."), null,
            (_, _) => EditDeviceAlerts(DeviceAliasRules.AulaSlot, AulaName));
        menu.DropDownItems.Add(UiText.Get("Device polling interval..."), null,
            (_, _) => EditDeviceInterval(DeviceAliasRules.AulaSlot, AulaName));
        menu.DropDownItems.Add(UiText.Get("AULA battery history..."), null,
            (_, _) => ShowAulaHistory());
        menu.DropDownItems.Add(UiText.Get("Copy AULA diagnostic summary"), null,
            (_, _) => CopyAulaSummary());
        menu.DropDownItems.Add(UiText.Get("System telemetry preview..."), null,
            (_, _) => _ = ShowHostMetricsAsync());
        UpdateAulaStatus();
        return menu;
    }

    /// <summary>Preview host readings without sending anything to the keyboard.</summary>
    private async Task ShowHostMetricsAsync()
    {
        if (_closing || _hostMetricsBusy) return;
        _hostMetricsBusy = true;
        try
        {
            var snapshot = await Task.Run(HostMetricsReader.ReadAsync);
            if (_closing) return;
            string Value(double? number, string unit) => number is double value
                ? $"{value:0.#}{unit}" : UiText.Get("unavailable");
            List<string> lines = new()
            {
                UiText.Get("Preview only — no keyboard data sent."),
                UiText.Format("Windows CPU load: {0}", Value(snapshot.WindowsCpuLoad, "%")),
                ""
            };
            foreach (var hardware in snapshot.Hardware)
            {
                lines.Add((hardware.IsGpu ? "GPU: " : "CPU: ") + hardware.Name);
                lines.Add(UiText.Format("Load: {0}; temperature: {1}",
                    Value(hardware.LoadPercent, "%"), Value(hardware.TemperatureC, " °C")));
                lines.Add("");
            }
            if (!snapshot.ProviderAvailable || snapshot.Hardware.Count == 0)
                lines.Add(UiText.Get("For GPU and temperature sensors, use a running LibreHardwareMonitor local web server at 127.0.0.1:8085."));
            MessageBox.Show(string.Join(Environment.NewLine, lines),
                UiText.Get("System telemetry preview..."), MessageBoxButtons.OK,
                MessageBoxIcon.Information);
        }
        finally { _hostMetricsBusy = false; }
    }

    private string AulaCacheReport()
        => $"Last successful battery: {_aulaBattery.LastGoodPercent?.ToString() ?? "unavailable"}; " +
           $"UTC: {_aulaBattery.LastGoodAt?.ToString("O") ?? "never"}; " +
           $"Consecutive no-reply polls: {_aulaBattery.ConsecutiveFailures}; " +
           $"Cache lifetime hours: {AulaBatteryState.CacheLifetime.TotalHours}; " +
           $"Display cache active: {_aulaLatest?.Percent is null && AulaDisplayPercent().HasValue}";

    private void CopyAulaSummary()
    {
        AulaL99Reading? state = _aulaLatest;
        string text = "AULA L99 2.4 GHz experimental battery check\n" +
            $"Version: {Application.ProductVersion}\n" +
            $"Automatic monitoring enabled: {_settings.MonitorAulaL99}\n" +
            $"Receiver present: {state?.ReceiverPresent.ToString() ?? "not checked"}\n" +
            $"Presence known: {state?.PresenceKnown.ToString() ?? "not checked"}\n" +
            $"Battery percentage: {state?.Percent?.ToString() ?? "unavailable"}\n" +
            $"Status: {state?.Details ?? "not checked"}\n" +
            $"Last read UTC: {_aulaLastReadAt?.ToString("O") ?? "never"}\n" +
            AulaCacheReport() + "\n" +
            "Model identity unverified (dongle IDs shared with S75 Pro).\n" +
            "No serial numbers or HID interface paths are included.";
        try { Clipboard.SetText(text); }
        catch (Exception error)
        {
            FileLog.Write("WARN", "AULA clipboard unavailable: " +
                error.GetType().Name);
        }
    }

    private void ShowAulaHistory()
    {
        if (_aulaHistoryWindow is null || _aulaHistoryWindow.IsDisposed)
            _aulaHistoryWindow = new BatteryHistoryForm(_aulaHistory, AulaName, estimateEnabled: true);
        _aulaHistoryWindow.RefreshData();
        _aulaHistoryWindow.Show();
        _aulaHistoryWindow.BringToFront();
    }

    private void UpdateAulaStatus()
    {
        if (_aulaBusy)
            _aulaStatus.Text = UiText.Get("AULA L99: checking battery...");
        else if (_aulaLatest is null)
            _aulaStatus.Text = UiText.Get("AULA L99: not checked");
        else if (!_aulaLatest.PresenceKnown)
            _aulaStatus.Text = UiText.Get("AULA L99: HID status unknown");
        else if (!_aulaLatest.ReceiverPresent)
            _aulaStatus.Text = UiText.Get("AULA L99: dongle not found");
        else if (_aulaLatest.Percent is int level)
            _aulaStatus.Text = UiText.Format(
                "AULA L99: last {0}% at {1} (unverified)", level,
                _aulaLastReadAt?.ToLocalTime().ToString("HH:mm:ss") ?? "—");
        else if (AulaDisplayPercent() is int cached)
            _aulaStatus.Text = UiText.Format(
                "AULA L99: cached {0}% at {1}; no fresh reply", cached,
                _aulaBattery.LastGoodAt?.ToLocalTime().ToString("g") ?? "—");
        else
            _aulaStatus.Text = UiText.Get("AULA L99: no valid battery reply");
        if (_settings.DeviceAliases.TryGetValue(DeviceAliasRules.AulaSlot, out string? alias))
            _aulaStatus.Text = alias + " — " + _aulaStatus.Text;
    }

    private int? AulaDisplayPercent()
        => _aulaBattery.DisplayPercent(_aulaLatest?.ReceiverPresent == true,
            _aulaLatest?.PresenceKnown == true, _aulaLatest?.Percent, DateTimeOffset.UtcNow);

    /// <summary>Run at most one explicit, battery-only dongle poll at a time.</summary>
    private async Task PollAulaAsync(bool manual = false)
    {
        if (_closing || _aulaBusy ||
            (!manual && !_settings.MonitorAulaL99)) return;
        _aulaTimer.Stop();
        _aulaBusy = true;
        int generation = _aulaGeneration;
        UpdateAulaStatus();
        try
        {
            AulaL99Reading result = await Task.Run(_aulaReader.ReadAsync);
            if (_closing || generation != _aulaGeneration) return;
            if (result.LocalKey != _aulaLatest?.LocalKey)
                _aulaBattery.Reset();
            _aulaLatest = result;
            _aulaLastReadAt = DateTimeOffset.UtcNow;
            _aulaBattery.Observe(result.ReceiverPresent, result.PresenceKnown,
                result.Percent, _aulaLastReadAt.Value);
            if (_settings.RecordBatteryHistory)
                _aulaHistory.Record(DateTimeOffset.UtcNow, result.Percent,
                    result.ReceiverPresent || !result.PresenceKnown);
            if (_settings.MonitorAulaL99)
            {
                if (result.PresenceKnown && _aulaConnection.Evaluate(
                        result.Percent.HasValue, result.ReceiverPresent) &&
                    _settings.NotifyOnDisconnect)
                    _tray.ShowBalloonTip(4000, AulaName,
                        UiText.Get("The 2.4 GHz receiver is no longer detected."),
                        ToolTipIcon.Warning);
                if (result.Percent is int percent) NotifyAulaBattery(percent);
            }
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "AULA monitoring failed: " +
                error.GetType().Name);
            if (!_closing && generation == _aulaGeneration)
            {
                _aulaLatest = new(false, null, "Unexpected read error", PresenceKnown: false);
                _aulaLastReadAt = DateTimeOffset.UtcNow;
            }
        }
        finally
        {
            _aulaBusy = false;
            if (!_closing)
            {
                if (_settings.MonitorAulaL99)
                {
                    _aulaTimer.Interval = _settings.EffectivePollInterval(DeviceAliasRules.AulaSlot) * 1000;
                    _aulaTimer.Start();
                }
                UpdateAulaStatus();
                RefreshDeviceDisplay();
            }
        }
    }

    private void NotifyAulaBattery(int percent)
    {
        int mask = _settings.EffectiveAlertMask(DeviceAliasRules.AulaSlot);
        int? threshold = _aulaAlerts.Evaluate(percent,
            (mask & 1) != 0, (mask & 2) != 0, (mask & 4) != 0);
        if (!threshold.HasValue) return;
        _tray.ShowBalloonTip(5000, AulaName + " — " + UiText.Get("Low battery notifications"),
            UiText.Format("Keyboard battery is {0}%; below {1}%.",
                percent, threshold), ToolTipIcon.Warning);
    }

    private ToolStripMenuItem BuildSettingsMenu()
    {
        ToolStripMenuItem menu = new(UiText.Get("Settings"));
        menu.DropDownItems.Add(BuildNotificationsMenu());
        menu.DropDownItems.Add(BuildIntervalMenu());
        menu.DropDownItems.Add(BuildClockSyncToggle());
        menu.DropDownItems.Add(BuildUpdateSettingsMenu());
        menu.DropDownItems.Add(UiText.Get("Preferences backup..."), null, (_, _) =>
        {
            if (_closing) return;
            using var dialog = new PreferencesBackupForm(_settings);
            dialog.ShowDialog();
        });
        menu.DropDownItems.Add(UiText.Get("Windows device names preview..."), null,
            (_, _) => _ = ShowPnpNamesAsync());
        ToolStripMenuItem multiple = new(UiText.Get("Separate tray icons"))
        {
            Checked = _settings.MultipleTrayIcons, CheckOnClick = true
        };
        multiple.CheckedChanged += (_, _) =>
        {
            _settings.MultipleTrayIcons = multiple.Checked;
            _settings.Save();
            RefreshDeviceDisplay();
        };
        menu.DropDownItems.Add(multiple);
        ToolStripMenuItem history = new(UiText.Get("Record battery history"))
        {
            Checked = _settings.RecordBatteryHistory, CheckOnClick = true
        };
        history.CheckedChanged += (_, _) =>
        {
            _settings.RecordBatteryHistory = history.Checked;
            _settings.Save();
        };
        menu.DropDownItems.Add(history);
        _startupItem = new ToolStripMenuItem();
        ConfigureStartupMenu();
        menu.DropDownItems.Add(_startupItem);
        menu.DropDownItems.Add(new ToolStripSeparator());
        menu.DropDownItems.Add(BuildLanguageMenu());
        return menu;
    }

    private ToolStripMenuItem BuildUpdateSettingsMenu()
    {
        var menu = new ToolStripMenuItem(UiText.Get("Update preferences"));
        var enabled = new ToolStripMenuItem(UiText.Get("Automatically check GitHub releases"));
        var stable = new ToolStripMenuItem(UiText.Get("Stable"));
        var beta = new ToolStripMenuItem(UiText.Get("Experimental (beta)"));
        void Refresh()
        {
            enabled.Checked = _settings.AutomaticUpdateChecks;
            stable.Checked = !_settings.ExperimentalUpdateChannel;
            beta.Checked = _settings.ExperimentalUpdateChannel;
        }
        enabled.Click += (_, _) =>
        {
            bool next = !_settings.AutomaticUpdateChecks;
            if (next && MessageBox.Show(UiText.Get("Allow daily GitHub release checks? No files will be downloaded."),
                UiText.Get("Update preferences"), MessageBoxButtons.YesNo, MessageBoxIcon.Question,
                MessageBoxDefaultButton.Button2) != DialogResult.Yes) return;
            SaveUpdatePreferences(next, _settings.ExperimentalUpdateChannel);
            Refresh();
        };
        stable.Click += (_, _) => { SaveUpdatePreferences(_settings.AutomaticUpdateChecks, false); Refresh(); };
        beta.Click += (_, _) => { SaveUpdatePreferences(_settings.AutomaticUpdateChecks, true); Refresh(); };
        menu.DropDownItems.AddRange(new ToolStripItem[] { enabled, new ToolStripSeparator(), stable, beta });
        Refresh();
        return menu;
    }

    private void SaveUpdatePreferences(bool enabled, bool experimental)
    {
        bool oldEnabled = _settings.AutomaticUpdateChecks;
        bool oldExperimental = _settings.ExperimentalUpdateChannel;
        _settings.AutomaticUpdateChecks = enabled;
        _settings.ExperimentalUpdateChannel = experimental;
        if (!_settings.Save())
        {
            // A failed save must not keep a revoked consent active this session.
            _settings.AutomaticUpdateChecks = oldEnabled && enabled;
            _settings.ExperimentalUpdateChannel = oldExperimental;
            ApplyUpdatePreferences();
            MessageBox.Show(UiText.Get(oldEnabled && !enabled
                ? "Automatic checks stopped for this session; disabling could not be saved."
                : "Unable to save device preference."),
                UiText.Get("Update preferences"), MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        ApplyUpdatePreferences();
    }

    private void ApplyUpdatePreferences()
    {
        bool active = _settings.AutomaticUpdateChecks && _settings.NotificationsEnabled;
        bool changed = _updatePolicy.Enabled != active ||
            _updatePolicy.Experimental != _settings.ExperimentalUpdateChannel;
        _updatePolicy.Configure(active,
            _settings.ExperimentalUpdateChannel, Environment.TickCount64);
        if (changed) _updateRequestCancellation?.Cancel();
    }

    private void ShowManualUpdateCheck()
    {
        if (_closing || _manualUpdateDialog) return;
        if (_automaticUpdateBusy)
        {
            MessageBox.Show(UiText.Get("A background update check is in progress."),
                UiText.Get("Check for updates..."), MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        _manualUpdateDialog = true;
        try
        {
            using var dialog = new UpdateCheckForm(_settings.ExperimentalUpdateChannel);
            dialog.ShowDialog();
        }
        finally { _manualUpdateDialog = false; }
    }

    private async Task PollUpdatesAsync()
    {
        if (_closing || _manualUpdateDialog || _automaticUpdateBusy || !_settings.NotificationsEnabled)
            return;
        var installed = ReleaseVersion.Parse(Application.ProductVersion.Split('+')[0]);
        if (installed is null) return;
        var request = _updatePolicy.TryBegin(Environment.TickCount64);
        if (request is null) return;
        _automaticUpdateBusy = true;
        using var cancel = new CancellationTokenSource();
        _updateRequestCancellation = cancel;
        bool success = false;
        UpdateClient.Candidate? candidate = null;
        try
        {
            candidate = await UpdateClient.CheckAsync(installed, request.Experimental, cancel.Token);
            success = true;
        }
        catch (Exception) { /* Keep battery polling independent of network failures. */ }
        finally
        {
            _updateRequestCancellation = null;
            _automaticUpdateBusy = false;
            bool notify = _updatePolicy.Complete(request, success,
                _settings.NotificationsEnabled ? candidate?.Version : null, Environment.TickCount64);
            if (notify && !_closing && _settings.NotificationsEnabled && candidate is not null)
                _tray.ShowBalloonTip(5000, "AJAZZ Battery Tray",
                    UiText.Format("Update available: {0}", candidate.Tag), ToolTipIcon.Info);
        }
    }

    private async Task ShowPnpNamesAsync()
    {
        if (_closing || _pnpPreviewBusy) return;
        _pnpPreviewBusy = true;
        try
        {
            var entries = await Task.Run(PnpNamePreview.Read);
            if (_closing) return;
            List<string> lines = new()
            {
                UiText.Get("Preview only — no Windows device names changed."),
                UiText.Get("Model names are provisional; confirm the receiver before applying."),
                ""
            };
            foreach (var entry in entries.Take(24))
            {
                lines.Add($"#{entry.Group} | {entry.Family} | rev. {entry.Revision?.ToString("X4") ?? "?"}");
                lines.Add(UiText.Get(entry.Role));
                lines.Add(UiText.Format("Current: {0}", entry.CurrentName));
                lines.Add(UiText.Format("Proposed: {0}", entry.ProposedName));
                lines.Add("");
            }
            if (entries.Count == 0)
                lines.Add(UiText.Get("No matching present USB receivers found."));
            if (entries.Count > 24)
                lines.Add(UiText.Get("Additional candidates omitted; no changes applied."));
            using Form preview = new()
            {
                Text = UiText.Get("Windows device names preview..."),
                Size = new Size(760, 560),
                MinimumSize = new Size(480, 300),
                StartPosition = FormStartPosition.CenterScreen
            };
            using TextBox content = new()
            {
                Dock = DockStyle.Fill, Multiline = true, ReadOnly = true,
                ScrollBars = ScrollBars.Both, WordWrap = false,
                Text = string.Join(Environment.NewLine, lines)
            };
            preview.Controls.Add(content);
            preview.ShowDialog();
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "PnP name preview failed: " + error.GetType().Name);
            if (!_closing)
                MessageBox.Show(UiText.Get("Unable to read Windows device names."),
                    UiText.Get("Windows device names preview..."),
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        finally { _pnpPreviewBusy = false; }
    }

    private ToolStripMenuItem BuildNotificationsMenu()
    {
        ToolStripMenuItem menu = new(UiText.Get("Notifications"));
        ToolStripMenuItem low = new(UiText.Get("Low battery notifications"))
        {
            Checked = _settings.NotificationsEnabled, CheckOnClick = true
        };
        low.CheckedChanged += (_, _) => SaveNotifications(low.Checked);
        menu.DropDownItems.Add(low);
        menu.DropDownItems.Add(BuildBatteryThresholdMenu());
        ToolStripMenuItem disconnect = new(UiText.Get("Notify on receiver disconnect"))
        {
            Checked = _settings.NotifyOnDisconnect, CheckOnClick = true
        };
        disconnect.CheckedChanged += (_, _) =>
        {
            _settings.NotifyOnDisconnect = disconnect.Checked;
            _settings.Save();
        };
        menu.DropDownItems.Add(disconnect);
        return menu;
    }

    private ToolStripMenuItem BuildLanguageMenu()
    {
        ToolStripMenuItem menu = new(UiText.Get("Language"));
        foreach (var (code, label) in new[]
        {
            ("en", "English"), ("ru", "Русский"), ("uk", "Українська")
        })
        {
            ToolStripMenuItem option = new(label)
            {
                Checked = _settings.Language == code
            };
            option.Click += (_, _) => ChangeLanguage(code);
            menu.DropDownItems.Add(option);
        }
        return menu;
    }

    private void ChangeLanguage(string code)
    {
        _settings.Language = UiText.Normalize(code);
        _settings.Save();
        UiText.SetLanguage(_settings.Language);
        ContextMenuStrip? previous = _tray.ContextMenuStrip;
        _tray.ContextMenuStrip = BuildMenu();
        RefreshDeviceDisplay();
        previous?.Dispose();
        _receivers.ApplyLanguage();
        if (_dashboard is { IsDisposed: false })
        {
            _dashboard.ApplyLanguage();
            RefreshDashboard();
        }
        _historyWindow?.ApplyLanguage();
        _aulaHistoryWindow?.ApplyLanguage();
        _bluetoothWindow?.ApplyLanguage();
    }

    private ToolStripMenuItem BuildDiagnosticsMenu()
    {
        ToolStripMenuItem menu = new(UiText.Get("Diagnostics"));
        menu.DropDownItems.Add(UiText.Get("Extended device diagnostics..."), null,
            (_, _) => _ = ShowExtendedDiagnosticsAsync());
        menu.DropDownItems.Add(UiText.Get("Full APEX comparison report..."), null,
            (_, _) => _ = ShowProtocolDiagnosticsAsync());
        menu.DropDownItems.Add(UiText.Get("Device diagnostics..."), null,
            (_, _) => ShowDiagnostics());
        menu.DropDownItems.Add(UiText.Get("Copy diagnostic report"), null,
            (_, _) => CopyDeviceReport());
        menu.DropDownItems.Add(UiText.Get("Copy Bluetooth monitor status"), null,
            (_, _) => CopyBluetoothStatus());
        menu.DropDownItems.Add(UiText.Get("Open log folder"), null,
            (_, _) => OpenLogFolder());
        return menu;
    }

    private ToolStripMenuItem BuildBatteryThresholdMenu()
    {
        ToolStripMenuItem menu = new(UiText.Get("Battery notification thresholds"));
        foreach (int threshold in new[] { 50, 25, 10 })
        {
            bool enabled = threshold switch
            {
                50 => _settings.AlertBelow50,
                25 => _settings.AlertBelow25,
                _ => _settings.AlertBelow10
            };
            ToolStripMenuItem option = new(UiText.Format("Below {0}%", threshold))
            {
                Checked = enabled, CheckOnClick = true
            };
            option.CheckedChanged += (_, _) =>
                SaveBatteryThreshold(threshold, option.Checked);
            menu.DropDownItems.Add(option);
        }
        return menu;
    }

    private void SaveBatteryThreshold(int threshold, bool enabled)
    {
        switch (threshold)
        {
            case 50: _settings.AlertBelow50 = enabled; break;
            case 25: _settings.AlertBelow25 = enabled; break;
            case 10: _settings.AlertBelow10 = enabled; break;
        }
        _settings.Save();
    }

    private ToolStripMenuItem BuildIntervalMenu()
    {
        ToolStripMenuItem menu = new(UiText.Get("Update interval"));
        foreach (int seconds in new[] { 15, 30, 60, 120 })
        {
            ToolStripMenuItem option = new(UiText.Format("{0} seconds", seconds))
            {
                Checked = _settings.PollSeconds == seconds,
                Tag = seconds
            };
            option.Click += (_, _) => ChangeInterval(seconds, menu);
            menu.DropDownItems.Add(option);
        }

        return menu;
    }

    private ToolStripMenuItem BuildClockSyncToggle()
    {
        ToolStripMenuItem option = new(UiText.Get("Auto-sync dock clock (5 min)"))
        {
            Checked = _settings.AutomaticDockClockSync,
            CheckOnClick = true
        };
        option.CheckedChanged += (_, _) =>
        {
            _settings.AutomaticDockClockSync = option.Checked;
            _settings.Save();
            if (option.Checked)
            {
                RequestClockSync();
            }
        };
        return option;
    }

    private void RequestClockSync()
    {
        _manualClockSync = true;
        PollSoon();
    }

    private void ShowHistory()
    {
        if (_historyWindow is null || _historyWindow.IsDisposed)
        {
            _historyWindow = new BatteryHistoryForm(_history);
        }
        _historyWindow.RefreshData();
        _historyWindow.Show();
        _historyWindow.BringToFront();
    }

    private void ShowBluetoothBattery()
    {
        if (_bluetoothWindow is null || _bluetoothWindow.IsDisposed)
        {
            _bluetoothWindow = new BluetoothBatteryForm(EnableBluetooth, DisableBluetooth, candidate => _bleSlots.ContainsKey(BleKey(candidate)));
            _bluetoothWindow.FormClosing += (_, e) =>
            {
                if (!_closing)
                {
                    e.Cancel = true;
                    _bluetoothWindow.Hide();
                }
            };
        }
        _bluetoothWindow.Show();
        _bluetoothWindow.BringToFront();
    }

    private void EnableBluetooth(BluetoothCandidate candidate, BluetoothBatteryResult result, DateTimeOffset readAt)
    {
        DateTimeOffset now = DateTimeOffset.UtcNow;
        if (_closing || !candidate.IsLowEnergy || string.IsNullOrWhiteSpace(candidate.DeviceId) ||
            now < readAt || now - readAt > TimeSpan.FromMinutes(1)) return;
        string key = BleKey(candidate);
        if (_bleSlots.ContainsKey(key)) return;
        _ble.ObserveUsbPresence(_latestUsbReading?.PresenceKnown == true, _latestUsbReading?.ReceiverPresent == true);
        if (!_ble.Enable(key, result, readAt)) return;
        _bleSlots[key] = new BleSlot(candidate, ++_bleSequence, new AlertPolicy());
        RefreshDeviceDisplay();
        PollSoon();
    }

    private void DisableBluetooth(BluetoothCandidate candidate) => DisableBluetoothKey(BleKey(candidate));

    private void DisableBluetoothKey(string key)
    {
        _ble.Disable(key);
        _bleSlots.Remove(key);
        _bluetoothWindow?.DisableAutomatic();
        RefreshDeviceDisplay();
    }

    private void DisableAllBluetooth()
    {
        _ble.DisableAll();
        _bleSlots.Clear();
        _bluetoothWindow?.DisableAutomatic();
        RefreshDeviceDisplay();
    }

    private void PopulateBleMenu()
    {
        foreach (ToolStripItem old in _bleDevicesMenu.DropDownItems.Cast<ToolStripItem>().ToArray()) old.Dispose();
        _bleDevicesMenu.DropDownItems.Clear();
        foreach (var pair in _bleSlots.OrderBy(x => x.Value.Number))
        {
            string key = pair.Key;
            var state = BluetoothDashboardState(key, pair.Value);
            string value = state.Percent is int level ? $"{level}%" : UiText.Get("unavailable");
            var item = new ToolStripMenuItem($"{BleDisplayLabel(pair.Value)}: {value}");
            var read = new ToolStripMenuItem(UiText.Get("Refresh Bluetooth battery now"))
            {
                Enabled = !_ble.IsBusy && _latestUsbReading is { PresenceKnown: true, ReceiverPresent: false }
            };
            read.Click += (_, _) => StartBluetoothPoll(false, force: true, key: key);
            item.DropDownItems.Add(read);
            item.DropDownItems.Add(UiText.Get("Disable selected BLE monitor"), null,
                (_, _) => DisableBluetoothKey(key));
            _bleDevicesMenu.DropDownItems.Add(item);
        }
        if (_bleDevicesMenu.DropDownItems.Count == 0)
            _bleDevicesMenu.DropDownItems.Add(new ToolStripMenuItem(UiText.Get("unavailable")) { Enabled = false });
    }

    private void UpdateBluetoothStatus()
    {
        bool known = _latestUsbReading?.PresenceKnown == true;
        bool present = _latestUsbReading?.ReceiverPresent == true;
        if (!BleEnabled) _bluetoothStatus.Text = UiText.Get("Bluetooth fallback: off");
        else if (!known) _bluetoothStatus.Text = UiText.Get("Bluetooth fallback: paused (receiver status unknown)");
        else if (present) _bluetoothStatus.Text = UiText.Get("Bluetooth fallback: standby (USB primary)");
        else if (_ble.IsBusy) _bluetoothStatus.Text = UiText.Get("Bluetooth fallback: checking battery...");
        else _bluetoothStatus.Text = UiText.Format("Bluetooth monitors: {0}", _bleSlots.Count);
        _disableBluetooth.Enabled = BleEnabled;
        _bleDevicesMenu.Enabled = BleEnabled;
        _refreshBluetooth.Enabled = !_closing && !_ble.IsBusy && BleEnabled && known && !present;
    }

    private string BleDiagnosticSummary()
    {
        DateTimeOffset now = DateTimeOffset.UtcNow;
        bool known = _latestUsbReading?.PresenceKnown == true;
        bool present = _latestUsbReading?.ReceiverPresent == true;
        return string.Join("\n", _bleSlots.OrderBy(x => x.Value.Number).Select(x =>
            $"{BleLabel(x.Value)}: battery={_ble.VisiblePercent(x.Key, known, present, now)?.ToString() ?? "unavailable"}; " +
            $"failures={_ble.Failures(x.Key)}; last attempt UTC={_ble.LastAttempt(x.Key)?.ToString("O") ?? "never"}; " +
            $"last success UTC={_ble.LastSuccess(x.Key)?.ToString("O") ?? "never"}"));
    }

    private void CopyBluetoothStatus()
    {
        string usb = _latestUsbReading is not { PresenceKnown: true } ? "unknown" :
            _latestUsbReading.ReceiverPresent ? "present" : "absent";
        string report = "AJAZZ Bluetooth monitor status\n" +
            $"App version: {Application.ProductVersion}\nUSB receiver: {usb}\n" +
            $"Opted-in devices: {_bleSlots.Count}\nGATT request pending: {_ble.IsBusy}\n" +
            BleDiagnosticSummary() + "\nNo Bluetooth addresses, serial numbers or device IDs are included.";
        try { Clipboard.SetText(report); }
        catch (Exception error)
        {
            FileLog.Write("WARN", "Bluetooth status clipboard unavailable: " + error.GetType().Name);
        }
    }

    // Explicit capture uses the same AJAZZ I/O exclusion as ordinary polling.
    private async Task ShowProtocolDiagnosticsAsync()
    {
        if (_closing) return;
        if (_busy || _diagnosticsBusy)
        {
            MessageBox.Show(UiText.Get("A poll or diagnostic is running. Try again."),
                "AJAZZ Battery Tray", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        if (MessageBox.Show(UiText.Get("Capture full vendor battery buffers locally? Close the official utility first. Review raw data before sharing."),
                "AJAZZ Battery Tray", MessageBoxButtons.YesNo, MessageBoxIcon.Warning)
            != DialogResult.Yes || _closing || _busy || _diagnosticsBusy) return;

        _busy = true;
        _diagnosticsBusy = true;
        _timer.Stop();
        try
        {
            var capture = await Task.Run(() =>
            {
                string inventory = ExtendedDeviceDiagnostics.ReadInventory();
                var batch = _reader.ReadAll(captureProtocol: true);
                return (Inventory: inventory, Batch: batch);
            });
            if (_closing) return;
            var batch = capture.Batch;
            string report = "AJAZZ APEX full comparison report (one capture)\n" +
                $"Version: {Application.ProductVersion}\nUTC: {DateTimeOffset.UtcNow:O}\n" +
                "Model labels are provisional. USB feature buffers are not USB wire captures.\n" +
                "Only the existing F7/05 query; no RTC or configuration writes.\n" +
                "Raw vendor bytes may contain undocumented data. Review before sharing.\n" +
                "Official application traffic is NOT acquired by this report.\n" +
                "All existing valid length/delay combinations attempted, including after success.\n" +
                $"Fresh enumeration known={batch.Summary.PresenceKnown}; receiver count={batch.Receivers.Count}; first valid battery={batch.Summary.Percent?.ToString() ?? "unavailable"}\n\n" +
                BuildExtendedReport(capture.Inventory) +
                "\n\n[Fresh APEX protocol matrix — full vendor buffers]\n" +
                (batch.Summary.Attempts is { } trace ? string.Join("\n", trace) : "No trace");
            using DiagnosticReportForm review = new(report);
            review.ShowDialog();
        }
        catch (Exception error)
        {
            if (!_closing)
                MessageBox.Show(UiText.Get("Unable to collect diagnostic report.") +
                    " (" + error.GetType().Name + ")", "AJAZZ Battery Tray",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        finally
        {
            _busy = false;
            _diagnosticsBusy = false;
            if (!_closing)
            {
                _timer.Interval = _forcePoll ? 100 : DiscoveryInterval();
                _timer.Start();
            }
        }
    }

    private async Task ShowExtendedDiagnosticsAsync()
    {
        if (_closing || _diagnosticsBusy) return;
        _diagnosticsBusy = true;
        try
        {
            string inventory = await Task.Run(ExtendedDeviceDiagnostics.ReadInventory);
            if (_closing) return;
            string report = BuildExtendedReport(inventory);
            if (!DiagnosticReportForm.PromptSave(report) && !_closing)
            {
                using DiagnosticReportForm review = new(report);
                review.ShowDialog();
            }
        }
        catch (Exception error)
        {
            if (!_closing)
                MessageBox.Show(UiText.Get("Unable to collect diagnostic report.") +
                    " (" + error.GetType().Name + ")", "AJAZZ Battery Tray",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
        finally { _diagnosticsBusy = false; }
    }

    private string BuildExtendedReport(string inventory)
    {
        var usb = _latestUsbReading;
        var aula = _aulaLatest;
        string attempts = usb?.Attempts is { Count: > 0 } trace
            ? string.Join(Environment.NewLine, trace) : "No completed poll trace.";
        return "AJAZZ Battery Tray extended diagnostic report" + Environment.NewLine +
            $"App version: {Application.ProductVersion}\n" +
            $"Windows: {Environment.OSVersion.VersionString}; OS architecture: {System.Runtime.InteropServices.RuntimeInformation.OSArchitecture}\n" +
            $"Report UTC: {DateTimeOffset.UtcNow:O}\n" +
            $"Refresh interval: {_settings.PollSeconds}s; auto dock clock: {_settings.AutomaticDockClockSync}\n\n" +
            inventory + "\n[AJAZZ last ordinary poll — not a fresh request]\n" +
            $"Completed UTC: {_latestUsbReadAt?.ToString("O") ?? "never"}\n" +
            $"Receiver present: {usb?.ReceiverPresent.ToString() ?? "unknown"}; presence known: {usb?.PresenceKnown.ToString() ?? "unknown"}\n" +
            $"Battery: {usb?.Percent?.ToString() ?? "unavailable"}; status: {usb?.Details ?? "not checked"}\n" +
            attempts + "\n\n[Independent AJAZZ receivers]\n" +
            string.Join("\n", _receivers.Devices.Select(x =>
                $"{x.Label}: present={x.Present}; presence known={x.Reading.PresenceKnown}; battery={x.Reading.Percent?.ToString() ?? "unavailable"}; interval={_settings.EffectivePollInterval(x.Key)}s; sampled UTC={x.MeasuredAt?.ToString("O") ?? "never"}; scheduled skip={x.ScheduledSkip}")) +
            $"\nSeparate tray icons: {_settings.MultipleTrayIcons}\n" +
            "\n[AULA L99 last measurement]\n" +
            $"Auto monitoring: {_settings.MonitorAulaL99}; interval={_settings.EffectivePollInterval(DeviceAliasRules.AulaSlot)}s; UTC: {_aulaLastReadAt?.ToString("O") ?? "never"}\n" +
            $"Receiver present: {aula?.ReceiverPresent.ToString() ?? "unknown"}; presence known: {aula?.PresenceKnown.ToString() ?? "unknown"}\n" +
            $"Battery: {aula?.Percent?.ToString() ?? "unavailable"}; status: {aula?.Details ?? "not checked"}\n" +
            AulaCacheReport() + "\n\n" +
            "[Bluetooth fallback state]\n" +
            $"Enabled: {BleEnabled}; displayed device: {_lastDevice}; source: {_lastSource}; displayed battery: {_lastPercent?.ToString() ?? "unknown"}\n" +
            $"Opted-in BLE devices: {_bleSlots.Count}; request pending: {_ble.IsBusy}\n" + BleDiagnosticSummary() + "\n" +
            "\nNo device paths, serial numbers, Bluetooth addresses, usernames, or raw report payloads are included.\n" +
            "Collection does not issue additional HID commands or scan Bluetooth devices.";
    }


    private static void CopyDeviceReport()
    {
        string report = "AJAZZ Battery Tray diagnostic report\n" +
            $"Version: {Application.ProductVersion}\n" +
            $"Windows: {Environment.OSVersion.VersionString}\n" +
            DeviceDiagnostics.Read();
        try
        {
            Clipboard.SetText(report);
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "Cannot copy diagnostics to clipboard", error);
            MessageBox.Show(UiText.Get("The Windows clipboard is currently unavailable."),
                "AJAZZ Battery Tray", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private static void ShowDiagnostics()
    {
        MessageBox.Show(DeviceDiagnostics.Read(), UiText.Get("AJAZZ APEX device diagnostics"),
            MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    private void ConfigureStartupMenu()
    {
        _startupItem.Text = UiText.Get("Start with Windows");
        _startupItem.CheckOnClick = false;
        _startupItem.Checked = StartupRegistration.IsEnabled();
        _startupItem.Click += (_, _) => ToggleStartup();
    }

    private void ToggleStartup()
    {
        try
        {
            bool enabled = !_startupItem.Checked;
            StartupRegistration.SetEnabled(enabled);
            _startupItem.Checked = enabled;
        }
        catch (Exception error)
        {
            FileLog.Write("ERROR", "Cannot change Windows startup", error);
            MessageBox.Show(error.Message, "AJAZZ Battery Tray",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private void SaveNotifications(bool enabled)
    {
        _settings.NotificationsEnabled = enabled;
        _settings.Save();
        ApplyUpdatePreferences();
    }

    private void ChangeInterval(int seconds, ToolStripMenuItem menu)
    {
        int previous = _settings.PollSeconds;
        _settings.PollSeconds = seconds;
        if (!_settings.Save())
        {
            _settings.PollSeconds = previous;
            MessageBox.Show(UiText.Get("Unable to save device preference."),
                UiText.Get("Settings"), MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        foreach (ToolStripMenuItem item in menu.DropDownItems)
        {
            item.Checked = item.Tag is int value && value == seconds;
        }

        PollSoon();
    }

    private int DiscoveryInterval()
        => Math.Min(_settings.PollSeconds, _settings.DevicePollIntervals
            .Where(x => x.Key != DeviceAliasRules.AulaSlot)
            .Select(x => DevicePollSchedule.NormalizeInterval(x.Value))
            .DefaultIfEmpty(_settings.PollSeconds).Min()) * 1000;

    private void PollSoon()
    {
        if (_closing) return;
        _forcePoll = true;
        if (_busy)
        {
            return;
        }

        _timer.Stop();
        _timer.Interval = 100;
        _timer.Start();
    }

    private async void OnPollTimer(object? sender, EventArgs args)
    {
        if (_busy || _closing)
        {
            return;
        }

        _busy = true;
        _timer.Stop();
        try
        {
            bool force = _forcePoll;
            _forcePoll = false;
            long nowTick = Environment.TickCount64;
            // Only immutable local keys cross to the background HID worker.
            var deferred = _receivers.Devices.Where(x => x.Present && x.Reading.PresenceKnown &&
                !_usbSchedule.IsDue(x.Key, nowTick, _settings.EffectivePollInterval(x.Key), force))
                .Select(x => x.Key).ToHashSet(StringComparer.Ordinal);
            bool manualClock = _manualClockSync;
            _manualClockSync = false;
            bool autoClock = _settings.AutomaticDockClockSync;
            var result = await Task.Run(() => QueryAndSync(deferred, manualClock, autoClock));
            if (!_closing)
            {
                _usbSchedule.Reconcile(result.Batch.Receivers.Select(x => x.Key),
                    result.Batch.Summary.PresenceKnown);
                foreach (var item in result.Batch.Receivers.Where(x => x.Sampled))
                    _usbSchedule.Complete(item.Key, item.CompletedTick);
                _latestUsbReadAt = DateTimeOffset.UtcNow;
                ApplyReading(result.Batch);
                ApplyClockResult(result.Attempted, result.Succeeded);
                StartBluetoothPoll(result.Batch.Summary.ReceiverPresent);
                if (force && _settings.MonitorAulaL99) _ = PollAulaAsync(manual: true);
            }
        }
        catch (Exception error)
        {
            FileLog.Write("ERROR", "Unexpected poll failure", error);
            if (!_closing)
            {
                _latestUsbReading = new AjazzHidReader.Reading(
                    false, null, "Unexpected error", PresenceKnown: false);
                _latestUsbReadAt = DateTimeOffset.UtcNow;
                ApplyReading(new AjazzHidReader.Batch(_latestUsbReading,
                    Array.Empty<AjazzHidReader.ReceiverReading>()));
            }
        }
        finally
        {
            _busy = false;
            if (!_closing)
            {
                _timer.Interval = _forcePoll ? 100 : DiscoveryInterval();
                _timer.Start();
            }
        }
    }

    private (AjazzHidReader.Batch Batch, bool Attempted, bool Succeeded)
        QueryAndSync(IReadOnlySet<string> deferred, bool manual, bool autoClock)
    {
        AjazzHidReader.Batch batch = _reader.ReadAll(shouldSample: key => !deferred.Contains(key));
        AjazzHidReader.Reading reading = batch.Summary;
        DateTimeOffset now = DateTimeOffset.UtcNow;
        bool automatic = _clockSchedule.ShouldAttempt(
            now, autoClock, reading.ReceiverPresent);
        if (!manual && !automatic)
        {
            return (batch, false, false);
        }

        if (!reading.ReceiverPresent)
        {
            return (batch, true, false);
        }

        bool sent = _reader.TrySyncDockClock(DateTime.Now);
        _clockSchedule.RecordAttempt(now);
        return (batch, true, sent);
    }

    private void StartBluetoothPoll(bool receiverPresent, bool force = false, string? key = null)
    {
        if (_closing || _latestUsbReading is not { PresenceKnown: true, ReceiverPresent: false }) return;
        var request = _ble.TryBegin(true, receiverPresent, DateTimeOffset.UtcNow,
            force ? key ?? PrimaryBleKey : null);
        if (request is null || !_bleSlots.TryGetValue(request.Key, out var slot)) return;
        UpdateBluetoothStatus();
        _ = PollBluetoothFallbackAsync(slot, request);
    }

    private async Task PollBluetoothFallbackAsync(BleSlot slot, BluetoothMultiSession.Request request)
    {
        BluetoothBatteryResult response;
        try
        {
            response = await BluetoothOperationTimeout.Run(
                BluetoothBatteryReader.ReadAsync(slot.Candidate), TimeSpan.FromSeconds(12));
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "Bluetooth fallback read failed: " + error.GetType().Name);
            response = new BluetoothBatteryResult(null, BluetoothBatterySource.Unavailable, "Read failed.");
        }
        if (_closing) return;
        bool known = _latestUsbReading?.PresenceKnown == true;
        bool present = _latestUsbReading?.ReceiverPresent == true;
        if (_ble.Complete(request, response, DateTimeOffset.UtcNow, known, present) &&
            response.IsFreshGatt && response.Percent is int percent)
            ShowLowBatteryAlert(slot, percent);
        RefreshDeviceDisplay();
        // Continue with another due device, not another read of the same slot.
        await Task.Yield();
        if (!_closing && known && !present) StartBluetoothPoll(false);
    }

    private void ApplyClockResult(bool attempted, bool succeeded)
    {
        if (!attempted)
        {
            return;
        }

        _lastClockUpdate = DateTime.Now;
        _lastClockSucceeded = succeeded;
        UpdateClockStatus();
        FileLog.Write(succeeded ? "INFO" : "WARN", _clockStatus.Text);
    }

    private void UpdateClockStatus()
    {
        _clockStatus.Text = !_lastClockUpdate.HasValue
            ? UiText.Get("Dock clock: not yet synchronized")
            : UiText.Format(_lastClockSucceeded
                ? "Dock clock: command sent at {0}"
                : "Dock clock: unable to send at {0}",
                _lastClockUpdate.Value.ToString("HH:mm:ss"));
    }

    private void ApplyReading(AjazzHidReader.Batch batch)
    {
        _ble.ObserveUsbPresence(batch.Summary.PresenceKnown, batch.Summary.ReceiverPresent);
        _receivers.Apply(batch, _settings, _tray, BleEnabled,
            DateTimeOffset.UtcNow);
        _latestUsbReading = batch.Summary.PresenceKnown && _receivers.SummaryState is { } primary
            ? primary.Reading with { Attempts = batch.Summary.Attempts,
                Details = primary.ScheduledSkip ? "Last scheduled battery reading" : primary.Reading.Details }
            : batch.Summary;
        UpdateTrayDisplay(_latestUsbReading);
    }

    /// <summary>Notify only for a fresh, currently selected battery source.</summary>
    private void ShowLowBatteryAlert(BleSlot slot, int percent)
    {
        int? level = slot.Alerts.Evaluate(percent,
            _settings.NotificationsEnabled && _settings.AlertBelow50,
            _settings.NotificationsEnabled && _settings.AlertBelow25,
            _settings.NotificationsEnabled && _settings.AlertBelow10);
        if (!level.HasValue) return;
        _tray.ShowBalloonTip(5000, UiText.Get("AJAZZ APEX: low battery"),
            UiText.Format("Mouse battery is {0}% ({1}); below {2}%.",
                percent, "Bluetooth #" + slot.Number, level),
            ToolTipIcon.Warning);
    }

    private void RefreshDeviceDisplay()
    {
        if (_closing) return;
        UpdateTrayDisplay(_latestUsbReading ??
            new AjazzHidReader.Reading(false, null, "Not checked", PresenceKnown: false));
    }

    /// <summary>Refresh only the tray: do not replay history or USB alerts.</summary>
    private void UpdateTrayDisplay(AjazzHidReader.Reading reading)
    {
        string? primaryBle = PrimaryBleKey;
        int? blePercent = primaryBle is not null
            ? _ble.VisiblePercent(primaryBle, reading.PresenceKnown,
                reading.ReceiverPresent, DateTimeOffset.UtcNow) : null;
        BatteryDisplayState display = BatteryDisplayState.Resolve(
            reading.ReceiverPresent, reading.Percent,
            BleEnabled, blePercent, reading.PresenceKnown);
        bool aulaPresent = _settings.MonitorAulaL99 &&
            _aulaLatest is { ReceiverPresent: true, PresenceKnown: true };
        bool showAula = aulaPresent && IsTrayVisible(DeviceAliasRules.AulaSlot);
        var receiver = _receivers.VisiblePrimary(_settings.MultipleTrayIcons,
            _settings.HiddenTrayDevices);
        int? aulaLevel = AulaDisplayPercent();
        bool aulaStale = _aulaLatest?.Percent is null && aulaLevel.HasValue;
        bool bluetoothPrimary = reading.PresenceKnown &&
            !reading.ReceiverPresent && BleEnabled;
        bool aulaIsPrimary = showAula && receiver is null && !bluetoothPrimary;
        bool neutral = receiver is null && !aulaIsPrimary && !bluetoothPrimary &&
            (reading.ReceiverPresent || aulaPresent);

        string device = bluetoothPrimary && primaryBle is not null ? BleLabel(_bleSlots[primaryBle]) :
            receiver?.Label ?? "AJAZZ APEX";
        int? displayPercent = receiver is not null && reading.PresenceKnown
            ? receiver.Reading.Percent : display.Percent;
        string source = display.SourceName;
        if (aulaIsPrimary)
        {
            device = "AULA L99";
            displayPercent = aulaLevel;
            source = "2.4 GHz";
        }
        if (neutral)
        {
            device = "Device Manager";
            source = "";
            displayPercent = null;
        }
        bool displayConnected = displayPercent.HasValue;
        bool stale = aulaIsPrimary && aulaStale;
        int? previousPercent = _lastPercent;
        if (displayConnected != _lastConnected ||
            previousPercent != displayPercent || source != _lastSource || device != _lastDevice || stale != _lastStale)
        {
            FileLog.Write("INFO", $"{device} {source} battery: " +
                (displayConnected ? $"{displayPercent}%" + (stale ? " (cached)" : "") : "unavailable"));
        }

        _lastPercent = displayPercent;
        _lastConnected = displayConnected;
        _lastSource = source;
        _lastDevice = device;
        _lastStale = stale;
        string displayName = bluetoothPrimary && primaryBle is not null ? BleDisplayLabel(_bleSlots[primaryBle]) :
            aulaIsPrimary ? AulaName : receiver?.DisplayLabel ?? device;
        string value = displayConnected ? $"{displayPercent}%" : UiText.Get("unavailable");
        if (stale) value += " (" + UiText.Get("cached") + ")";
        else if (displayConnected && !aulaIsPrimary && receiver?.ScheduledSkip == true)
            value += " (" + UiText.Get("Last scheduled reading") + ")";
        _statusItem.Text = neutral ? UiText.Get("Device Manager") : $"{displayName} — {source}: {value}";
        string tooltip = neutral ? UiText.Get("Device Manager") : $"{value} — {displayName} ({source})";
        _tray.Text = tooltip[..Math.Min(63, tooltip.Length)];
        string color = aulaIsPrimary ? DeviceColor(DeviceAliasRules.AulaSlot) :
            receiver is not null ? DeviceColor(receiver.Key) : TrayColorRules.Default;
        UpdateIcon(displayPercent, displayConnected, stale, neutral, color);
        if (_tray.ContextMenuStrip is { } menu)
            _receivers.RefreshIcons(_settings.MultipleTrayIcons, showAula,
                aulaLevel, aulaStale, aulaIsPrimary, menu, PollSoon, AulaName,
                receiver?.Key, _settings.HiddenTrayDevices, DeviceColor,
                BluetoothExtraIcons(reading, primaryBle));
        UpdateBluetoothStatus();
        RefreshDashboard();
    }

    private IReadOnlyList<(string Key, string Name, int? Percent)> BluetoothExtraIcons(
        AjazzHidReader.Reading reading, string? primary)
    {
        if (!reading.PresenceKnown || reading.ReceiverPresent)
            return Array.Empty<(string, string, int?)>();
        DateTimeOffset now = DateTimeOffset.UtcNow;
        return _bleSlots.Where(x => x.Key != primary).OrderBy(x => x.Value.Number)
            .Select(x => ($"BLE:{x.Value.Number}", BleDisplayLabel(x.Value),
                _ble.VisiblePercent(x.Key, true, false, now))).ToArray();
    }

    private void UpdateIcon(int? percent, bool connected, bool stale = false,
        bool neutral = false, string? color = null)
    {
        Icon next = TrayIconFactory.Create(percent, connected, stale, neutral, color);
        Icon? previous = _icon;
        _icon = next;
        _tray.Icon = next;
        previous?.Dispose();
    }

    private static void OpenLogFolder()
    {
        Directory.CreateDirectory(AppSettings.DirectoryPath);
        Process.Start(new ProcessStartInfo
        {
            FileName = AppSettings.DirectoryPath,
            UseShellExecute = true
        });
    }

    protected override void ExitThreadCore()
    {
        _closing = true;
        _updateTimer.Stop();
        _updateTimer.Dispose();
        _updatePolicy.Configure(false, _settings.ExperimentalUpdateChannel, Environment.TickCount64);
        _updateRequestCancellation?.Cancel();
        _timer.Stop();
        _timer.Dispose();
        _aulaTimer.Stop();
        _aulaTimer.Dispose();
        _ble.DisableAll();
        _bleSlots.Clear();
        _dashboard?.Close();
        _historyWindow?.Close();
        _aulaHistoryWindow?.Close();
        _bluetoothWindow?.Close();
        _receivers.Dispose();
        _tray.Visible = false;
        _tray.ContextMenuStrip?.Dispose();
        _tray.Dispose();
        _icon?.Dispose();
        FileLog.Write("INFO", "Application stopped");
        base.ExitThreadCore();
    }
}
