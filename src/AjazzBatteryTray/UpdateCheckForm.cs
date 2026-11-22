using System.Drawing;
using System.Windows.Forms;
using System.Diagnostics;

namespace AjazzBatteryTray;

/// <summary>Explicit release lookup; nothing is downloaded or installed automatically.</summary>
internal sealed class UpdateCheckForm : Form
{
    private readonly CancellationTokenSource _cancel = new();
    private readonly ComboBox _channel = new() { DropDownStyle = ComboBoxStyle.DropDownList, Width = 220 };
    private readonly Label _result = new() { AutoSize = true, MaximumSize = new Size(460, 0) };
    private readonly Button _check = new() { AutoSize = true };
    private readonly Button _open = new() { AutoSize = true, Enabled = false };
    private string? _page;
    private bool _busy;

    internal UpdateCheckForm(bool experimental)
    {
        Text = UiText.Get("Check for updates...");
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        AutoSize = true;
        AutoSizeMode = AutoSizeMode.GrowAndShrink;
        var panel = new FlowLayoutPanel { FlowDirection = FlowDirection.TopDown,
            WrapContents = false, AutoSize = true, Dock = DockStyle.Fill, Padding = new Padding(14) };
        panel.Controls.Add(new Label { AutoSize = true,
            Text = UiText.Format("Installed version: {0}", Application.ProductVersion.Split('+')[0]) });
        panel.Controls.Add(new Label { AutoSize = true, Text = UiText.Get("Release channel") });
        _channel.Items.AddRange(new object[] { UiText.Get("Stable"), UiText.Get("Experimental (beta)") });
        _channel.SelectedIndex = experimental ? 1 : 0;
        panel.Controls.Add(_channel);
        _check.Text = UiText.Get("Check now");
        _check.Click += async (_, _) => await CheckAsync();
        panel.Controls.Add(_check);
        _result.Text = UiText.Get("No network request until you choose Check now.");
        panel.Controls.Add(_result);
        _open.Text = UiText.Get("Open release page");
        _open.Click += (_, _) => OpenRelease();
        panel.Controls.Add(_open);
        var close = new Button { Text = UiText.Get("Close"), AutoSize = true };
        close.Click += (_, _) => Close();
        panel.Controls.Add(close);
        Controls.Add(panel);
        _channel.SelectedIndexChanged += (_, _) => { _page = null; _open.Enabled = false;
            _result.Text = UiText.Get("No network request until you choose Check now."); };
    }

    private async Task CheckAsync()
    {
        if (_busy || IsDisposed) return;
        _busy = true;
        _check.Enabled = _channel.Enabled = _open.Enabled = false;
        _page = null;
        _result.Text = UiText.Get("Checking GitHub releases...");
        try
        {
            var installed = ReleaseVersion.Parse(Application.ProductVersion.Split('+')[0])
                ?? throw new InvalidDataException("Unsupported installed version.");
            var candidate = await UpdateClient.CheckAsync(installed, _channel.SelectedIndex == 1, _cancel.Token);
            if (IsDisposed || _cancel.IsCancellationRequested) return;
            _page = candidate?.Page;
            _result.Text = candidate is null ? UiText.Get("No newer release found in this channel.")
                : UiText.Format("Update available: {0}", candidate.Tag);
            _open.Enabled = _page is not null;
        }
        catch (Exception)
        {
            if (!IsDisposed && !_cancel.IsCancellationRequested)
                _result.Text = UiText.Get("Update check failed; try again later.");
        }
        finally
        {
            _busy = false;
            if (!IsDisposed && !_cancel.IsCancellationRequested)
                _check.Enabled = _channel.Enabled = true;
        }
    }

    private void OpenRelease()
    {
        if (_page is null) return;
        try { Process.Start(new ProcessStartInfo(_page) { UseShellExecute = true }); }
        catch (Exception) { _result.Text = UiText.Get("Unable to open release page."); }
    }

    protected override void OnFormClosed(FormClosedEventArgs e)
    {
        _cancel.Cancel();
        base.OnFormClosed(e);
    }
}
