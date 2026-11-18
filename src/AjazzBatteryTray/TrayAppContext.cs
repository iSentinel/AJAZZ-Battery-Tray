using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Owns the tray menu, polling loop, preferences and notifications.</summary>
public sealed class TrayAppContext : ApplicationContext
{
    private readonly NotifyIcon _tray;
    private readonly System.Windows.Forms.Timer _timer;
    private readonly AjazzHidReader _reader = new();
    private readonly AulaL99Reader _aulaReader = new();
    private readonly AlertPolicy _aulaAlerts = new();
    private readonly BatteryHistory _aulaHistory = new("aula-l99-history.csv");
    private BatteryHistoryForm? _aulaHistoryWindow;
    private AulaL99Reading? _aulaLatest;
    private bool _aulaBusy;
    private ToolStripMenuItem _aulaStatus = new();
    private readonly AlertPolicy _alerts = new();
    private readonly ConnectionAlertPolicy _connectionAlerts = new();
    private readonly BatteryHistory _history = new();
    private BatteryHistoryForm? _historyWindow;
    private BluetoothBatteryForm? _bluetoothWindow;
    private readonly BluetoothAutoPolicy _bluetoothPolicy = new();
    private BluetoothCandidate? _bluetoothSelection;
    private bool _bluetoothReadInFlight;
    private AjazzHidReader.Reading? _latestUsbReading;
    private ToolStripMenuItem _bluetoothStatus = new();
    private ToolStripMenuItem _disableBluetooth = new();
    private ToolStripMenuItem _refreshBluetooth = new();
    private string _lastSource = "";
    private readonly DockClockSchedule _clockSchedule = new();
    private ToolStripMenuItem _clockStatus = new();
    private bool _manualClockSync;
    private DateTime? _lastClockUpdate;
    private bool _lastClockSucceeded;
    private readonly AppSettings _settings = AppSettings.Load();
    private ToolStripMenuItem _statusItem = new();
    private ToolStripMenuItem _startupItem = new();
    private Icon? _icon;
    private int? _lastPercent;
    private bool _lastConnected;
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
        _timer.Start();
    }

    private ContextMenuStrip BuildMenu()
    {
        ContextMenuStrip menu = new();
        _statusItem = new ToolStripMenuItem("AJAZZ APEX — " +
            UiText.Get("Connecting...")) { Enabled = false };
        menu.Items.Add(_statusItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(UiText.Get("Refresh now"), null, (_, _) => PollSoon());
        menu.Items.Add(UiText.Get("Battery history..."), null,
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
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add(UiText.Get("Exit"), null, (_, _) => ExitThread());
        return menu;
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
            Enabled = _bluetoothSelection is not null
        };
        _disableBluetooth.Click += (_, _) => SelectBluetoothFallback(null, null);
        menu.DropDownItems.Add(_disableBluetooth);
        _refreshBluetooth = new ToolStripMenuItem(
            UiText.Get("Refresh Bluetooth battery now"));
        _refreshBluetooth.Click += (_, _) => StartBluetoothPoll(
            _latestUsbReading?.ReceiverPresent ?? false, force: true);
        menu.DropDownItems.Add(_refreshBluetooth);
        UpdateBluetoothStatus();
        return menu;
    }

    private ToolStripMenuItem BuildAulaMenu()
    {
        ToolStripMenuItem menu = new(UiText.Get("AULA L99 (experimental)"));
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
            _settings.MonitorAulaL99 = auto.Checked;
            _settings.Save();
            if (auto.Checked) _ = PollAulaAsync(manual: true);
        };
        menu.DropDownItems.Add(auto);
        menu.DropDownItems.Add(UiText.Get("AULA battery history..."), null,
            (_, _) => ShowAulaHistory());
        menu.DropDownItems.Add(UiText.Get("Copy AULA diagnostic summary"), null,
            (_, _) => CopyAulaSummary());
        UpdateAulaStatus();
        return menu;
    }

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
            _aulaHistoryWindow = new BatteryHistoryForm(_aulaHistory, "AULA L99");
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
                "AULA L99: {0}% (model unverified)", level);
        else
            _aulaStatus.Text = UiText.Get("AULA L99: no valid battery reply");
    }

    /// <summary>Run at most one explicit, battery-only dongle poll at a time.</summary>
    private async Task PollAulaAsync(bool manual = false)
    {
        if (_closing || _aulaBusy ||
            (!manual && !_settings.MonitorAulaL99)) return;
        _aulaBusy = true;
        UpdateAulaStatus();
        try
        {
            AulaL99Reading result = await Task.Run(_aulaReader.ReadAsync);
            if (_closing) return;
            _aulaLatest = result;
            if (_settings.RecordBatteryHistory)
                _aulaHistory.Record(DateTimeOffset.UtcNow, result.Percent,
                    result.ReceiverPresent || !result.PresenceKnown);
            if (_settings.MonitorAulaL99 && result.Percent is int percent)
                NotifyAulaBattery(percent);
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "AULA monitoring failed: " +
                error.GetType().Name);
        }
        finally
        {
            _aulaBusy = false;
            if (!_closing) UpdateAulaStatus();
        }
    }

    private void NotifyAulaBattery(int percent)
    {
        int? threshold = _aulaAlerts.Evaluate(percent,
            _settings.NotificationsEnabled && _settings.AlertBelow50,
            _settings.NotificationsEnabled && _settings.AlertBelow25,
            _settings.NotificationsEnabled && _settings.AlertBelow10);
        if (!threshold.HasValue) return;
        _tray.ShowBalloonTip(5000, UiText.Get("AULA L99: low battery"),
            UiText.Format("Keyboard battery is {0}%; below {1}%.",
                percent, threshold), ToolTipIcon.Warning);
    }

    private ToolStripMenuItem BuildSettingsMenu()
    {
        ToolStripMenuItem menu = new(UiText.Get("Settings"));
        menu.DropDownItems.Add(BuildNotificationsMenu());
        menu.DropDownItems.Add(BuildIntervalMenu());
        menu.DropDownItems.Add(BuildClockSyncToggle());
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
        _tray.ContextMenuStrip = BuildMenu();
        if (_latestUsbReading is not null) UpdateTrayDisplay(_latestUsbReading);
        _historyWindow?.ApplyLanguage();
        _aulaHistoryWindow?.ApplyLanguage();
        _bluetoothWindow?.ApplyLanguage();
    }

    private ToolStripMenuItem BuildDiagnosticsMenu()
    {
        ToolStripMenuItem menu = new(UiText.Get("Diagnostics"));
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
            _bluetoothWindow = new BluetoothBatteryForm(SelectBluetoothFallback);
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

    private void SelectBluetoothFallback(BluetoothCandidate? candidate, int? level)
    {
        if (candidate is not null && candidate.IsLowEnergy &&
            level is >= 0 and <= 100)
        {
            _bluetoothSelection = candidate;
            _bluetoothPolicy.Enable(level.Value, DateTimeOffset.UtcNow);
            _disableBluetooth.Enabled = true;
        }
        else
        {
            _bluetoothSelection = null;
            _bluetoothPolicy.Disable();
            _disableBluetooth.Enabled = false;
            _bluetoothWindow?.DisableAutomatic();
        }
        UpdateBluetoothStatus();
        PollSoon();
    }

    private void UpdateBluetoothStatus()
    {
        bool usbPresent = _latestUsbReading?.ReceiverPresent ?? false;
        bool presenceKnown = _latestUsbReading?.PresenceKnown ?? false;
        DateTimeOffset now = DateTimeOffset.UtcNow;
        if (!_bluetoothPolicy.Enabled)
            _bluetoothStatus.Text = UiText.Get("Bluetooth fallback: off");
        else if (!presenceKnown)
            _bluetoothStatus.Text = UiText.Get(
                "Bluetooth fallback: paused (receiver status unknown)");
        else if (usbPresent)
            _bluetoothStatus.Text = UiText.Get(
                "Bluetooth fallback: standby (USB primary)");
        else if (_bluetoothReadInFlight)
            _bluetoothStatus.Text = UiText.Get(
                "Bluetooth fallback: checking battery...");
        else if (_bluetoothPolicy.VisiblePercent(false, now) is int percent)
            _bluetoothStatus.Text = UiText.Format(
                "Bluetooth fallback: {0}% (fresh GATT)", percent);
        else
            _bluetoothStatus.Text = UiText.Format(
                "Bluetooth fallback: unavailable ({0} failed; last good {1})",
                _bluetoothPolicy.ConsecutiveFailures,
                _bluetoothPolicy.LastSuccessfulRead?.ToLocalTime()
                    .ToString("HH:mm:ss") ?? "never");
        _refreshBluetooth.Enabled = !_closing && !_bluetoothReadInFlight &&
            presenceKnown && _bluetoothSelection is not null &&
            _bluetoothPolicy.CanRefreshNow(usbPresent);
    }

    private void CopyBluetoothStatus()
    {
        string usb = _latestUsbReading is null ? "not checked" :
            !_latestUsbReading.PresenceKnown ? "unknown (HID error)" :
            _latestUsbReading.ReceiverPresent ? "present" : "absent";
        string last = _bluetoothPolicy.LastSuccessfulRead?.ToString("O") ?? "never";
        string attempt = _bluetoothPolicy.LastAttempt?.ToString("O") ?? "never";
        string report = "AJAZZ Bluetooth monitor status\n" +
            $"App version: {Application.ProductVersion}\n" +
            $"Auto fallback: {_bluetoothPolicy.Enabled}\n" +
            $"USB receiver: {usb}\n" +
            $"Displayed source: {_lastSource}\n" +
            $"Displayed percent: {_lastPercent?.ToString() ?? "unknown"}\n" +
            $"GATT request pending: {_bluetoothReadInFlight}\n" +
            $"Consecutive failed reads: {_bluetoothPolicy.ConsecutiveFailures}\n" +
            $"Automatic retry (minutes): " +
            $"{BluetoothAutoPolicy.RetryInterval(_bluetoothPolicy.ConsecutiveFailures).TotalMinutes}\n" +
            $"Last GATT attempt (UTC): {attempt}\n" +
            $"Last successful GATT (UTC): {last}\n" +
            "No Bluetooth addresses, serial numbers or device IDs are included.";
        try
        {
            Clipboard.SetText(report);
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "Bluetooth status clipboard unavailable: " +
                error.GetType().Name);
        }
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
    }

    private void ChangeInterval(int seconds, ToolStripMenuItem menu)
    {
        _settings.PollSeconds = seconds;
        _settings.Save();
        foreach (ToolStripMenuItem item in menu.DropDownItems)
        {
            item.Checked = item.Tag is int value && value == seconds;
        }

        PollSoon();
    }

    private void PollSoon()
    {
        if (_busy || _closing)
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
            var result = await Task.Run(QueryAndSync);
            if (!_closing)
            {
                _latestUsbReading = result.Reading;
                ApplyReading(result.Reading);
                ApplyClockResult(result.Attempted, result.Succeeded);
                StartBluetoothPoll(result.Reading.ReceiverPresent);
                _ = PollAulaAsync();
            }
        }
        catch (Exception error)
        {
            FileLog.Write("ERROR", "Unexpected poll failure", error);
            if (!_closing)
            {
                _latestUsbReading = new AjazzHidReader.Reading(
                    false, null, "Unexpected error", PresenceKnown: false);
                ApplyReading(_latestUsbReading);
            }
        }
        finally
        {
            _busy = false;
            if (!_closing)
            {
                _timer.Interval = _settings.PollSeconds * 1000;
                _timer.Start();
            }
        }
    }

    private (AjazzHidReader.Reading Reading, bool Attempted, bool Succeeded)
        QueryAndSync()
    {
        AjazzHidReader.Reading reading = _reader.Read();
        DateTimeOffset now = DateTimeOffset.UtcNow;
        bool manual = _manualClockSync;
        _manualClockSync = false;
        bool automatic = _clockSchedule.ShouldAttempt(
            now, _settings.AutomaticDockClockSync, reading.ReceiverPresent);
        if (!manual && !automatic)
        {
            return (reading, false, false);
        }

        if (!reading.ReceiverPresent)
        {
            return (reading, true, false);
        }

        bool sent = _reader.TrySyncDockClock(DateTime.Now);
        _clockSchedule.RecordAttempt(now);
        return (reading, true, sent);
    }

    private void StartBluetoothPoll(bool receiverPresent, bool force = false)
    {
        BluetoothCandidate? selected = _bluetoothSelection;
        if (_latestUsbReading is not { PresenceKnown: true }) return;
        if (_closing || _bluetoothReadInFlight || selected is null ||
            !_bluetoothPolicy.CanRefreshNow(receiverPresent) ||
            (!force && !_bluetoothPolicy.ShouldRead(receiverPresent,
                DateTimeOffset.UtcNow)))
            return;

        _bluetoothReadInFlight = true;
        UpdateBluetoothStatus();
        _ = PollBluetoothFallbackAsync(selected, _bluetoothPolicy.Generation);
    }

    private async Task PollBluetoothFallbackAsync(
        BluetoothCandidate selected, int generation)
    {
        BluetoothBatteryResult response;
        try
        {
            response = await BluetoothOperationTimeout.Run(
                BluetoothBatteryReader.ReadAsync(selected), TimeSpan.FromSeconds(12));
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "Bluetooth fallback read failed: " +
                error.GetType().Name);
            response = new BluetoothBatteryResult(null,
                BluetoothBatterySource.Unavailable, "Read failed.");
        }
        finally
        {
            _bluetoothReadInFlight = false;
            if (!_closing) UpdateBluetoothStatus();
        }

        if (!IsCurrentBluetoothRequest(selected, generation)) return;
        _bluetoothPolicy.RecordRead(response, DateTimeOffset.UtcNow);
        if (_latestUsbReading is { PresenceKnown: true, ReceiverPresent: false })
        {
            if (response.IsFreshGatt && response.Percent.HasValue)
                ShowLowBatteryAlert(response.Percent.Value, "Bluetooth");
        }
        if (_latestUsbReading is not null)
            UpdateTrayDisplay(_latestUsbReading);
    }

    private bool IsCurrentBluetoothRequest(
        BluetoothCandidate selected, int generation)
        => !_closing && _bluetoothSelection == selected &&
           _bluetoothPolicy.Enabled && _bluetoothPolicy.Generation == generation;

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

    private void ApplyReading(AjazzHidReader.Reading reading)
    {
        bool connected = reading.Percent.HasValue;
        if (_settings.RecordBatteryHistory)
        {
            _history.Record(DateTimeOffset.UtcNow, reading.Percent,
                BatteryDisplayState.SafeReceiverPresent(
                    reading.ReceiverPresent, reading.PresenceKnown));
        }

        bool receiverLost = _connectionAlerts.Evaluate(
            connected, BatteryDisplayState.SafeReceiverPresent(
                reading.ReceiverPresent, reading.PresenceKnown));
        if (_settings.NotifyOnDisconnect &&
            BatteryDisplayState.NotifyReceiverDisconnect(
                receiverLost, _bluetoothPolicy.Enabled))
        {
            _tray.ShowBalloonTip(4000, UiText.Get("AJAZZ APEX disconnected"),
                UiText.Get("The 2.4 GHz receiver is no longer detected."),
                ToolTipIcon.Warning);
        }
        if (connected)
            ShowLowBatteryAlert(reading.Percent!.Value, "2.4 GHz");

        UpdateTrayDisplay(reading);
    }

    /// <summary>Notify only for a fresh, currently selected battery source.</summary>
    private void ShowLowBatteryAlert(int percent, string source)
    {
        int? level = _alerts.Evaluate(percent,
            _settings.NotificationsEnabled && _settings.AlertBelow50,
            _settings.NotificationsEnabled && _settings.AlertBelow25,
            _settings.NotificationsEnabled && _settings.AlertBelow10);
        if (!level.HasValue) return;
        _tray.ShowBalloonTip(5000, UiText.Get("AJAZZ APEX: low battery"),
            UiText.Format("Mouse battery is {0}% ({1}); below {2}%.",
                percent, source, level),
            ToolTipIcon.Warning);
    }

    /// <summary>Refresh only the tray: do not replay history or USB alerts.</summary>
    private void UpdateTrayDisplay(AjazzHidReader.Reading reading)
    {
        int? blePercent = reading.PresenceKnown
            ? _bluetoothPolicy.VisiblePercent(
                reading.ReceiverPresent, DateTimeOffset.UtcNow) : null;
        BatteryDisplayState display = BatteryDisplayState.Resolve(
            reading.ReceiverPresent, reading.Percent,
            _bluetoothPolicy.Enabled, blePercent, reading.PresenceKnown);
        int? displayPercent = display.Percent;
        bool displayConnected = display.HasReading;
        string source = display.SourceName;
        int? previousPercent = _lastPercent;
        if (displayConnected != _lastConnected ||
            previousPercent != displayPercent || source != _lastSource)
        {
            FileLog.Write("INFO", $"{source} battery: " +
                (displayConnected ? $"{displayPercent}%" : "unavailable"));
        }

        _lastPercent = displayPercent;
        _lastConnected = displayConnected;
        _lastSource = source;
        string value = displayConnected ? $"{displayPercent}%" : UiText.Get("unavailable");
        _statusItem.Text = $"AJAZZ APEX — {source}: {value}";
        string tooltip = $"AJAZZ APEX: {source} {value}";
        _tray.Text = tooltip[..Math.Min(63, tooltip.Length)];
        UpdateIcon(displayPercent, displayConnected);
        UpdateBluetoothStatus();
    }

    private void UpdateIcon(int? percent, bool connected)
    {
        Icon next = TrayIconFactory.Create(percent, connected);
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
        _timer.Stop();
        _timer.Dispose();
        _bluetoothSelection = null;
        _bluetoothPolicy.Disable();
        _historyWindow?.Close();
        _aulaHistoryWindow?.Close();
        _bluetoothWindow?.Close();
        _tray.Visible = false;
        _tray.Dispose();
        _icon?.Dispose();
        FileLog.Write("INFO", "Application stopped");
        base.ExitThreadCore();
    }
}
