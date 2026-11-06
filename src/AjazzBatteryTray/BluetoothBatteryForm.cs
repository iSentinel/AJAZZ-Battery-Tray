using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Opt-in inspector; does not join a device to the 2.4 GHz receiver.</summary>
public sealed class BluetoothBatteryForm : Form
{
    private readonly ListBox _devices = new();
    private readonly CheckBox _showAll = new()
    {
        Text = "Show all paired Bluetooth devices (if mouse name is different)",
        AutoSize = true
    };
    private readonly Label _result = new();
    private string _discoverySummary = "No Bluetooth lookup has run yet.";
    private readonly Button _copy = new() { Text = "Copy lookup summary" };
    private readonly Button _find = new() { Text = "Find paired Bluetooth devices" };
    private readonly Button _read = new() { Text = "Read selected battery" };
    private readonly CheckBox _automatic = new()
    {
        Text = "Use this mouse in tray when 2.4 GHz receiver is absent (this session)",
        AutoSize = true, Enabled = false
    };
    private readonly Action<BluetoothCandidate?, int?> _onAutoSelection;
    private BluetoothCandidate? _verified;
    private int? _verifiedPercent;

    public BluetoothBatteryForm(Action<BluetoothCandidate?, int?> onAutoSelection)
    {
        _onAutoSelection = onAutoSelection;
        Text = "AJAZZ — Experimental Bluetooth battery check";
        Size = new Size(760, 465);
        MinimumSize = new Size(670, 365);
        StartPosition = FormStartPosition.CenterScreen;
        BuildWindow();
    }

    private void BuildWindow()
    {
        Label instructions = new()
        {
            Dock = DockStyle.Top, Height = 62, Padding = new Padding(12),
            Text = "Manual check of already paired Bluetooth LE and Classic mice.\n" +
                   "No pairing, unpaired scans, background polling, or device writes."
        };
        _devices.Dock = DockStyle.Fill;
        _result.Dock = DockStyle.Bottom;
        _result.Height = 104;
        _result.Padding = new Padding(10);
        _result.Text = "Choose Find to list already paired devices.";
        _find.Width = 232;
        _read.Width = 165;
        _copy.Width = 160;
        _read.Enabled = false;
        _devices.SelectedIndexChanged += (_, _) =>
        {
            _read.Enabled = _devices.SelectedItem is BluetoothCandidate &&
                            _find.Enabled;
            ClearVerifiedSelection();
        };

        _automatic.Dock = DockStyle.Bottom;
        _automatic.Padding = new Padding(12, 3, 0, 4);
        _automatic.CheckedChanged += (_, _) => ToggleAutomatic();
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
        Controls.Add(_automatic);
        Controls.Add(buttons);
        Controls.Add(_result);
        Controls.Add(_showAll);
        Controls.Add(instructions);
    }

    private async Task FindDevicesAsync()
    {
        ClearVerifiedSelection();
        SetBusy(true, "Checking paired Bluetooth LE and Classic devices...");
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
                ? "No matching devices. Enable Show all and search again.\n" +
                  _discoverySummary
                : "Select your mouse and click Read selected battery.\n" +
                  _discoverySummary;
        }
        catch (TimeoutException)
        {
            _discoverySummary = "Bluetooth lookup timed out.";
            _result.Text = _discoverySummary + " Wake the mouse and try again.";
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "BLE paired device inspection failed: " +
                error.GetType().Name);
            _discoverySummary = "Bluetooth lookup unavailable: " +
                error.GetType().Name;
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
        SetBusy(true, "Reading selected mouse's GATT Battery Service...");
        try
        {
            var result = await BluetoothOperationTimeout.Run(
                BluetoothBatteryReader.ReadAsync(selected), TimeSpan.FromSeconds(15));
            _result.Text = result.Percent.HasValue
                ? $"{selected.DisplayName}: {result.Percent}% — {result.Status}"
                : result.Status + " No battery percentage inferred.";
            if (result.Percent.HasValue &&
                BluetoothAutoPolicy.IsDirectGatt(result.Status) &&
                selected.IsLowEnergy)
            {
                _verified = selected;
                _verifiedPercent = result.Percent.Value;
                _automatic.Enabled = true;
            }
        }
        catch (TimeoutException)
        {
            _result.Text = "Bluetooth Battery Service read timed out. Try waking the mouse.";
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "BLE battery query failed: " +
                error.GetType().Name);
            _result.Text = "Unable to read this paired mouse's Battery Service.";
        }
        finally
        {
            SetBusy(false);
        }
    }

    private void ClearVerifiedSelection()
    {
        if (_automatic.Checked)
        {
            _automatic.Checked = false;
        }
        _automatic.Enabled = false;
        _verified = null;
        _verifiedPercent = null;
    }

    private void ToggleAutomatic()
    {
        if (_automatic.Checked && _verified is not null &&
            _verifiedPercent.HasValue)
        {
            _onAutoSelection(_verified, _verifiedPercent);
            _result.Text = "Bluetooth tray fallback is enabled for this session. " +
                "It is used only when the 2.4 GHz receiver is absent.";
        }
        else
        {
            _onAutoSelection(null, null);
        }
    }

    /// <summary>Require a new fresh GATT read before enabling again.</summary>
    public void DisableAutomatic()
    {
        ClearVerifiedSelection();
    }

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
            _result.Text = "Windows clipboard is unavailable.";
        }
    }

    private void SetBusy(bool busy, string? message = null)
    {
        _find.Enabled = !busy;
        _read.Enabled = !busy && _devices.SelectedItem is BluetoothCandidate;
        _devices.Enabled = !busy;
        _showAll.Enabled = !busy;
        if (message is not null) _result.Text = message;
    }
}
