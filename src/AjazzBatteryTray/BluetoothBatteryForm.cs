using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Manual Bluetooth inspector with optional, session-only tray fallback.</summary>
public sealed class BluetoothBatteryForm : Form
{
    private readonly ListBox _devices = new();
    private readonly CheckBox _showAll = new()
    {
        Text = "Show all paired Bluetooth devices (if mouse name is different)",
        AutoSize = true
    };
    private readonly Label _result = new();
    private readonly Label _instructions = new();
    private string _discoverySummary = "No Bluetooth lookup has run yet.";
    private readonly Button _copy = new() { Text = "Copy lookup summary" };
    private readonly Button _find = new() { Text = "Find paired Bluetooth devices" };
    private readonly Button _read = new() { Text = "Read selected battery" };
    private readonly Button _automatic = new() { AutoSize = true, Enabled = false };
    private readonly Button _remove = new() { AutoSize = true, Enabled = false };
    private readonly Action<BluetoothCandidate, BluetoothBatteryResult, DateTimeOffset> _enable;
    private readonly Action<BluetoothCandidate> _disable;
    private readonly Func<BluetoothCandidate, bool> _isEnabled;
    private BluetoothCandidate? _verified;
    private BluetoothBatteryResult? _verifiedResult;
    private DateTimeOffset _verifiedAt;

    public BluetoothBatteryForm(Action<BluetoothCandidate, BluetoothBatteryResult, DateTimeOffset> enable,
        Action<BluetoothCandidate> disable, Func<BluetoothCandidate, bool> isEnabled)
    {
        _enable = enable;
        _disable = disable;
        _isEnabled = isEnabled;
        Text = UiText.Get("AJAZZ — Experimental Bluetooth battery check");
        Size = new Size(900, 490);
        MinimumSize = new Size(780, 410);
        StartPosition = FormStartPosition.CenterScreen;
        BuildWindow();
    }

    private void BuildWindow()
    {
        _instructions.Dock = DockStyle.Top;
        _instructions.Height = 62;
        _instructions.Padding = new Padding(12);
        _devices.Dock = DockStyle.Fill;
        _result.Dock = DockStyle.Bottom;
        _result.Height = 104;
        _result.Padding = new Padding(10);
        _result.Text = UiText.Get("Choose Find to list already paired devices.");
        _find.Width = 270;
        _read.Width = 190;
        _copy.Width = 195;
        _read.Enabled = false;
        _devices.SelectedIndexChanged += (_, _) =>
        {
            _read.Enabled = _devices.SelectedItem is BluetoothCandidate &&
                            _find.Enabled;
            ClearVerifiedSelection();
        };

        FlowLayoutPanel consent = new() { Dock = DockStyle.Bottom, AutoSize = true, WrapContents = true };
        consent.Controls.Add(_automatic);
        consent.Controls.Add(_remove);
        _automatic.Click += (_, _) => EnableSelected();
        _remove.Click += (_, _) =>
        {
            if (_devices.SelectedItem is BluetoothCandidate selected) _disable(selected);
            ClearVerifiedSelection();
        };
        _showAll.Dock = DockStyle.Top;
        _showAll.Padding = new Padding(12, 3, 0, 4);
        FlowLayoutPanel buttons = new() { Dock = DockStyle.Bottom, Height = 44 };
        buttons.Controls.Add(_find);
        buttons.Controls.Add(_read);
        buttons.Controls.Add(_copy);
        _copy.Click += (_, _) => CopyLookupSummary();
        _find.Click += async (_, _) => await FindDevicesAsync();
        _read.Click += async (_, _) => await ReadSelectedAsync();
        Controls.Add(_devices);
        Controls.Add(consent);
        Controls.Add(buttons);
        Controls.Add(_result);
        Controls.Add(_showAll);
        Controls.Add(_instructions);
        ApplyLanguage();
    }

    /// <summary>Refresh captions without resetting BLE consent or selection.</summary>
    public void ApplyLanguage()
    {
        Text = UiText.Get("AJAZZ — Experimental Bluetooth battery check");
        _instructions.Text = UiText.Get(
            "Manual check of already paired Bluetooth LE and Classic mice.") +
            "\n" + UiText.Get(
                "No pairing or GATT writes. Automatic reads require opt-in.");
        _showAll.Text = UiText.Get(
            "Show all paired Bluetooth devices (if mouse name is different)");
        _find.Text = UiText.Get("Find paired Bluetooth devices");
        _read.Text = UiText.Get("Read selected battery");
        _copy.Text = UiText.Get("Copy lookup summary");
        _automatic.Text = UiText.Get("Enable selected BLE monitor (this session)");
        _remove.Text = UiText.Get("Disable selected BLE monitor");
        if (_devices.Items.Count == 0 && _verified is null)
            _result.Text = UiText.Get("Choose Find to list already paired devices.");
    }

    private async Task FindDevicesAsync()
    {
        ClearVerifiedSelection();
        SetBusy(true, UiText.Get("Checking paired Bluetooth LE and Classic devices..."));
        try
        {
            BluetoothDiscovery discovery = await BluetoothOperationTimeout.Run(
                BluetoothBatteryReader.FindPairedAsync(_showAll.Checked),
                TimeSpan.FromSeconds(20));
            _devices.Items.Clear();
            foreach (BluetoothCandidate item in discovery.Candidates)
                _devices.Items.Add(item);
            _discoverySummary = discovery.Summary +
                $" Displayed: {discovery.Candidates.Count}. " +
                $"Show all enabled: {_showAll.Checked}.";
            _result.Text = discovery.Candidates.Count == 0
                ? UiText.Get("No matching devices. Enable Show all and search again.") + "\n" +
                  _discoverySummary
                : UiText.Get("Select your mouse and click Read selected battery.") + "\n" +
                  _discoverySummary;
        }
        catch (TimeoutException)
        {
            _discoverySummary = UiText.Get("Bluetooth lookup timed out.");
            _result.Text = _discoverySummary + " " + UiText.Get("Wake the mouse and try again.");
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "BLE paired device inspection failed: " +
                error.GetType().Name);
            _discoverySummary = UiText.Format("Bluetooth lookup unavailable: {0}",
                error.GetType().Name);
            _result.Text = _discoverySummary;
        }
        finally
        {
            SetBusy(false);
        }
    }

    private async Task ReadSelectedAsync()
    {
        if (_devices.SelectedItem is not BluetoothCandidate selected) return;
        ClearVerifiedSelection();
        SetBusy(true, UiText.Get("Reading selected mouse's GATT Battery Service..."));
        try
        {
            var result = await BluetoothOperationTimeout.Run(
                BluetoothBatteryReader.ReadAsync(selected), TimeSpan.FromSeconds(15));
            _result.Text = result.Percent.HasValue
                ? $"{selected.DisplayName}: {result.Percent}% — {result.Status}"
                : result.Status + " " + UiText.Get("No battery percentage inferred.");
            if (result.IsFreshGatt && selected.IsLowEnergy)
            {
                _verified = selected;
                _verifiedResult = result;
                _verifiedAt = DateTimeOffset.UtcNow;
            }
        }
        catch (TimeoutException)
        {
            _result.Text = UiText.Get("Bluetooth Battery Service read timed out. Try waking the mouse.");
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "BLE battery query failed: " +
                error.GetType().Name);
            _result.Text = UiText.Get("Unable to read this paired mouse's Battery Service.");
        }
        finally
        {
            SetBusy(false);
        }
    }

    private void ClearVerifiedSelection()
    {
        _verified = null;
        _verifiedResult = null;
        UpdateConsentControls();
    }

    private void UpdateConsentControls()
    {
        var selected = _devices.SelectedItem as BluetoothCandidate;
        bool enabled = selected is not null && _isEnabled(selected);
        _automatic.Enabled = _find.Enabled && !enabled && _verified is not null &&
            _verified == selected && _verifiedResult?.IsFreshGatt == true;
        _remove.Enabled = _find.Enabled && enabled;
    }

    private void EnableSelected()
    {
        if (_verified is not { } candidate || _verifiedResult is not { IsFreshGatt: true } result ||
            candidate != _devices.SelectedItem as BluetoothCandidate) return;
        DateTimeOffset now = DateTimeOffset.UtcNow;
        if (now < _verifiedAt || now - _verifiedAt > TimeSpan.FromMinutes(1))
        {
            ClearVerifiedSelection();
            _result.Text = UiText.Get("Read selected battery again before enabling monitoring.");
            return;
        }
        _enable(candidate, result, _verifiedAt);
        ClearVerifiedSelection();
        _result.Text = UiText.Get("Bluetooth monitor enabled for this session; USB keeps priority.");
    }

    /// <summary>External opt-out invalidates prior consent evidence.</summary>
    public void DisableAutomatic() => ClearVerifiedSelection();

    public void RefreshConsent() => UpdateConsentControls();

    private void CopyLookupSummary()
    {
        try
        {
            Clipboard.SetText("AJAZZ Bluetooth lookup summary\n" +
                _discoverySummary + "\n" +
                "No Bluetooth addresses or Windows device IDs are included.");
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "Bluetooth clipboard unavailable: " +
                error.GetType().Name);
            _result.Text = UiText.Get("Windows clipboard is unavailable.");
        }
    }

    private void SetBusy(bool busy, string? message = null)
    {
        _find.Enabled = !busy;
        _read.Enabled = !busy && _devices.SelectedItem is BluetoothCandidate;
        _devices.Enabled = !busy;
        _showAll.Enabled = !busy;
        UpdateConsentControls();
        if (message is not null) _result.Text = message;
    }
}
