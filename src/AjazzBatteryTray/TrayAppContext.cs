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
    private readonly AlertPolicy _alerts = new();
    private readonly ConnectionAlertPolicy _connectionAlerts = new();
    private readonly BatteryHistory _history = new();
    private BatteryHistoryForm? _historyWindow;
    private readonly DockClockSchedule _clockSchedule = new();
    private readonly ToolStripMenuItem _clockStatus = new();
    private bool _manualClockSync;
    private readonly AppSettings _settings = AppSettings.Load();
    private readonly ToolStripMenuItem _statusItem = new();
    private readonly ToolStripMenuItem _startupItem = new();
    private Icon? _icon;
    private int? _lastPercent;
    private bool _lastConnected;
    private bool _busy;
    private bool _closing;

    public TrayAppContext()
    {
        _tray = new NotifyIcon { Text = "AJAZZ APEX: connecting..." };
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
        _statusItem.Text = "AJAZZ APEX — connecting";
        _statusItem.Enabled = false;
        menu.Items.Add(_statusItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add("Refresh now", null, (_, _) => PollSoon());
        menu.Items.Add("Battery history...", null, (_, _) => ShowHistory());
        menu.Items.Add("Device diagnostics...", null, (_, _) => ShowDiagnostics());
        menu.Items.Add("Copy diagnostic report", null, (_, _) => CopyDeviceReport());
        menu.Items.Add(BuildIntervalMenu());
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add("Sync dock time now", null, (_, _) => RequestClockSync());
        menu.Items.Add(BuildClockSyncToggle());
        _clockStatus.Text = "Dock clock: not yet synchronized";
        _clockStatus.Enabled = false;
        menu.Items.Add(_clockStatus);
        ToolStripMenuItem notify = new("Low battery notifications")
        {
            Checked = _settings.NotificationsEnabled,
            CheckOnClick = true
        };
        notify.CheckedChanged += (_, _) => SaveNotifications(notify.Checked);
        menu.Items.Add(notify);
        ToolStripMenuItem disconnect = new("Notify on receiver disconnect")
        {
            Checked = _settings.NotifyOnDisconnect, CheckOnClick = true
        };
        disconnect.CheckedChanged += (_, _) =>
        {
            _settings.NotifyOnDisconnect = disconnect.Checked;
            _settings.Save();
        };
        menu.Items.Add(disconnect);
        ToolStripMenuItem history = new("Record battery history")
        {
            Checked = _settings.RecordBatteryHistory, CheckOnClick = true
        };
        history.CheckedChanged += (_, _) =>
        {
            _settings.RecordBatteryHistory = history.Checked;
            _settings.Save();
        };
        menu.Items.Add(history);
        ConfigureStartupMenu();
        menu.Items.Add(_startupItem);
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add("Open log folder", null, (_, _) => OpenLogFolder());
        menu.Items.Add("Exit", null, (_, _) => ExitThread());
        return menu;
    }

    private ToolStripMenuItem BuildIntervalMenu()
    {
        ToolStripMenuItem menu = new("Update interval");
        foreach (int seconds in new[] { 15, 30, 60, 120 })
        {
            ToolStripMenuItem option = new($"{seconds} seconds")
            {
                Checked = _settings.PollSeconds == seconds
            };
            option.Click += (_, _) => ChangeInterval(seconds, menu);
            menu.DropDownItems.Add(option);
        }

        return menu;
    }

    private ToolStripMenuItem BuildClockSyncToggle()
    {
        ToolStripMenuItem option = new("Auto-sync dock clock (5 min)")
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
            MessageBox.Show("The Windows clipboard is currently unavailable.",
                "AJAZZ Battery Tray", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private static void ShowDiagnostics()
    {
        MessageBox.Show(DeviceDiagnostics.Read(), "AJAZZ APEX device diagnostics",
            MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    private void ConfigureStartupMenu()
    {
        _startupItem.Text = "Start with Windows";
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
            item.Checked = item.Text == $"{seconds} seconds";
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
                ApplyReading(result.Reading);
                ApplyClockResult(result.Attempted, result.Succeeded);
            }
        }
        catch (Exception error)
        {
            FileLog.Write("ERROR", "Unexpected poll failure", error);
            if (!_closing)
            {
                ApplyReading(new AjazzHidReader.Reading(false, null, "Unexpected error"));
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

    private void ApplyClockResult(bool attempted, bool succeeded)
    {
        if (!attempted)
        {
            return;
        }

        string timestamp = DateTime.Now.ToString("HH:mm:ss");
        _clockStatus.Text = (succeeded
            ? "Dock clock: command sent at " : "Dock clock: unable to send at ") + timestamp;
        FileLog.Write(succeeded ? "INFO" : "WARN", _clockStatus.Text);
    }

    private void ApplyReading(AjazzHidReader.Reading reading)
    {
        bool connected = reading.Percent.HasValue;
        if (_settings.RecordBatteryHistory)
        {
            _history.Record(DateTimeOffset.UtcNow, reading.Percent, reading.ReceiverPresent);
        }

        if (_connectionAlerts.Evaluate(connected, reading.ReceiverPresent) &&
            _settings.NotifyOnDisconnect)
        {
            _tray.ShowBalloonTip(4000, "AJAZZ APEX disconnected",
                "The 2.4 GHz receiver is no longer detected.",
                ToolTipIcon.Warning);
        }
        int? previousPercent = _lastPercent;
        if (connected)
        {
            _lastPercent = reading.Percent;
            int? threshold = _settings.NotificationsEnabled
                ? _alerts.Evaluate(reading.Percent!.Value) : null;
            if (threshold.HasValue)
            {
                _tray.ShowBalloonTip(5000, "AJAZZ APEX: low battery",
                    $"Battery at {reading.Percent}%. Threshold: {threshold}%.",
                    ToolTipIcon.Warning);
            }
        }

        if (connected != _lastConnected ||
            (connected && previousPercent != reading.Percent))
        {
            FileLog.Write("INFO", reading.Details + (connected
                ? $"; battery {reading.Percent}%" : "; level unavailable"));
        }

        _lastConnected = connected;
        string value = connected ? $"{reading.Percent}%" : "unavailable";
        _statusItem.Text = $"AJAZZ APEX — {value}";
        string tooltip = $"AJAZZ APEX: {value} ({reading.Details})";
        _tray.Text = tooltip[..Math.Min(63, tooltip.Length)];
        UpdateIcon(reading.Percent, connected);
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
        _historyWindow?.Close();
        _tray.Visible = false;
        _tray.Dispose();
        _icon?.Dispose();
        FileLog.Write("INFO", "Application stopped");
        base.ExitThreadCore();
    }
}
