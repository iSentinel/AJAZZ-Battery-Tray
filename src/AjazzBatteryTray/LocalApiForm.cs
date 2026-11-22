using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Explicit, session-only local API control. Closing this window stops the listener.</summary>
internal sealed class LocalApiForm : Form
{
    private readonly Action<LocalSnapshotStore> _activate;
    private readonly Action<LocalSnapshotStore> _deactivate;
    private LocalSnapshotStore? _store;
    private LocalApiServer? _server;
    private readonly Button _start = new() { AutoSize = true };
    private readonly Button _stop = new() { AutoSize = true, Enabled = false };
    private readonly Button _copy = new() { AutoSize = true, Enabled = false };
    private readonly TextBox _endpoint = new() { Width = 430, ReadOnly = true };
    private readonly Label _status = new() { AutoSize = true, MaximumSize = new Size(430, 0) };
    private bool _stopping;

    internal LocalApiForm(Action<LocalSnapshotStore> activate, Action<LocalSnapshotStore> deactivate)
    {
        _activate = activate;
        _deactivate = deactivate;
        Text = UiText.Get("Local battery API...");
        StartPosition = FormStartPosition.CenterScreen;
        AutoSize = true;
        AutoSizeMode = AutoSizeMode.GrowAndShrink;
        var panel = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.TopDown, WrapContents = false, Padding = new Padding(14) };
        panel.Controls.Add(new Label { AutoSize = true, MaximumSize = new Size(430, 0),
            Text = UiText.Get("Local PC only. Closing this window stops the API. No hardware commands.") });
        _start.Text = UiText.Get("Start local API");
        _stop.Text = UiText.Get("Stop local API");
        _copy.Text = UiText.Get("Copy API token");
        _start.Click += async (_, _) => await StartAsync();
        _stop.Click += async (_, _) => await StopAsync();
        _copy.Click += (_, _) => CopyToken();
        _status.Text = UiText.Get("Local API stopped.");
        panel.Controls.AddRange(new Control[] { _start, _stop, _endpoint, _copy, _status });
        Controls.Add(panel);
    }

    private async Task StartAsync()
    {
        if (_server is not null || _stopping) return;
        try
        {
            var store = new LocalSnapshotStore();
            _server = new LocalApiServer(store);
            _store = store;
            _activate(store);
            _endpoint.Text = _server.Endpoint;
            _status.Text = UiText.Get("Local API running. Keep this window open.");
            _start.Enabled = false;
            _stop.Enabled = _copy.Enabled = true;
        }
        catch (Exception)
        {
            await StopAsync();
            if (!IsDisposed)
                _status.Text = UiText.Get("Unable to start local API; port may be in use.");
        }
    }

    private void CopyToken()
    {
        if (_server is null) return;
        try { Clipboard.SetText(_server.Token); }
        catch (Exception) { _status.Text = UiText.Get("Unable to copy API token."); }
    }

    private async Task StopAsync()
    {
        if (_server is null || _stopping) return;
        _stopping = true;
        var server = _server;
        _server = null;
        if (_store is { } store) _deactivate(store);
        _store = null;
        _stop.Enabled = _copy.Enabled = false;
        _endpoint.Clear();
        try { await server.DisposeAsync(); }
        catch (Exception) { /* Listener was stopped before awaiting worker completion. */ }
        finally
        {
            _stopping = false;
            if (!IsDisposed)
            {
                _start.Enabled = true;
                _status.Text = UiText.Get("Local API stopped.");
            }
        }
    }

    protected override void OnFormClosing(FormClosingEventArgs e)
    {
        base.OnFormClosing(e);
        if (!e.Cancel) _ = StopAsync();
    }
}
