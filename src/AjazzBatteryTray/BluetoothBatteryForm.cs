using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Opt-in inspector; does not join a device to the 2.4 GHz receiver.</summary>
public sealed class BluetoothBatteryForm : Form
{
    private readonly ListBox _devices = new();
    private readonly Label _result = new();
    private readonly Button _find = new() { Text = "Find paired AJAZZ BLE mice" };
    private readonly Button _read = new() { Text = "Read selected battery" };

    public BluetoothBatteryForm()
    {
        Text = "AJAZZ — Experimental Bluetooth battery check";
        Size = new Size(570, 340);
        MinimumSize = new Size(480, 280);
        StartPosition = FormStartPosition.CenterScreen;
        BuildWindow();
    }

    private void BuildWindow()
    {
        Label instructions = new()
        {
            Dock = DockStyle.Top, Height = 62, Padding = new Padding(12),
            Text = "Manual check of paired Bluetooth LE mice only.\n" +
                   "No pairing, background scanning, or device settings writes."
        };
        _devices.Dock = DockStyle.Fill;
        _result.Dock = DockStyle.Bottom;
        _result.Height = 66;
        _result.Padding = new Padding(10);
        _result.Text = "Choose Find to list already paired devices.";
        _find.Width = 215;
        _read.Width = 170;
        _read.Enabled = false;
        _devices.SelectedIndexChanged += (_, _) =>
            _read.Enabled = _devices.SelectedItem is BluetoothCandidate &&
                            _find.Enabled;

        FlowLayoutPanel buttons = new() { Dock = DockStyle.Bottom, Height = 44 };
        buttons.Controls.Add(_find);
        buttons.Controls.Add(_read);
        _find.Click += async (_, _) => await FindDevicesAsync();
        _read.Click += async (_, _) => await ReadSelectedAsync();
        Controls.Add(_devices);
        Controls.Add(buttons);
        Controls.Add(_result);
        Controls.Add(instructions);
    }

    private async Task FindDevicesAsync()
    {
        SetBusy(true, "Searching already-paired LE devices...");
        try
        {
            var candidates = await BluetoothBatteryReader.FindPairedAsync();
            _devices.Items.Clear();
            foreach (BluetoothCandidate device in candidates) _devices.Items.Add(device);
            _result.Text = candidates.Count == 0
                ? "No paired AJAZZ BLE candidates. Pair in Windows Settings first."
                : $"{candidates.Count} candidate(s). Select one to read Battery Level.";
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "BLE paired device inspection failed: " +
                error.GetType().Name);
            _result.Text = "Bluetooth inspection unavailable in this Windows session.";
        }
        finally
        {
            SetBusy(false);
        }
    }

    private async Task ReadSelectedAsync()
    {
        if (_devices.SelectedItem is not BluetoothCandidate selected) return;
        SetBusy(true, "Reading selected mouse's GATT Battery Service...");
        try
        {
            var result = await BluetoothBatteryReader.ReadAsync(selected);
            _result.Text = result.Percent.HasValue
                ? $"{selected.DisplayName}: {result.Percent}% (BLE experimental)"
                : result.Status + " No battery percentage inferred.";
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

    private void SetBusy(bool busy, string? message = null)
    {
        _find.Enabled = !busy;
        _read.Enabled = !busy && _devices.SelectedItem is BluetoothCandidate;
        _devices.Enabled = !busy;
        if (message is not null) _result.Text = message;
    }
}
