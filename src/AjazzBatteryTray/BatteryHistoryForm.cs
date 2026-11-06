using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Read local battery observations and inspect the charge trend.</summary>
public sealed class BatteryHistoryForm : Form
{
    private readonly BatteryHistory _history;
    private readonly BatteryGraphPanel _graph = new();
    private readonly Label _summary = new();
    private readonly ComboBox _range = new();
    private IReadOnlyList<BatterySample> _visible = Array.Empty<BatterySample>();

    public BatteryHistoryForm(BatteryHistory history)
    {
        _history = history;
        Text = "AJAZZ APEX — Battery history";
        MinimumSize = new Size(650, 390);
        Size = new Size(900, 510);
        StartPosition = FormStartPosition.CenterScreen;
        BuildWindow();
        RefreshData();
    }

    private void BuildWindow()
    {
        FlowLayoutPanel buttons = new()
        {
            Dock = DockStyle.Top, Height = 48, Padding = new Padding(10)
        };
        _range.DropDownStyle = ComboBoxStyle.DropDownList;
        _range.Width = 135;
        _range.Items.AddRange(new object[] { "Last 24 hours", "Last 7 days", "Last 30 days" });
        _range.SelectedIndex = 1;
        _range.SelectedIndexChanged += (_, _) => RefreshData();

        Button refresh = new() { Text = "Refresh", Width = 85 };
        refresh.Click += (_, _) => RefreshData();
        Button folder = new() { Text = "Open CSV folder", Width = 140 };
        folder.Click += (_, _) => OpenHistoryFolder();

        buttons.Controls.Add(_range);
        buttons.Controls.Add(refresh);
        buttons.Controls.Add(folder);
        _summary.Dock = DockStyle.Bottom;
        _summary.Height = 52;
        _summary.Padding = new Padding(14, 6, 14, 6);
        _summary.Font = new Font("Segoe UI", 9);
        _graph.Dock = DockStyle.Fill;
        Controls.Add(_graph);
        Controls.Add(_summary);
        Controls.Add(buttons);
    }

    public void RefreshData()
    {
        int days = _range.SelectedIndex switch { 0 => 1, 1 => 7, _ => 30 };
        DateTimeOffset cutoff = DateTimeOffset.UtcNow.AddDays(-days);
        _visible = _history.ReadRecent().Where(x => x.Timestamp >= cutoff).ToArray();
        _graph.Samples = _visible;
        _graph.Invalidate();
        UpdateSummary();
    }

    private void UpdateSummary()
    {
        BatterySample? latest = _visible.LastOrDefault();
        if (latest is null)
        {
            _summary.Text = "No observations yet. History is saved locally.";
            return;
        }

        int missing = _visible.Count(x => x.State == "disconnected");
        int unavailable = _visible.Count(x => x.State == "unavailable");
        int? min = _visible.Where(x => x.Percent.HasValue)
                           .Select(x => x.Percent).Min();
        string value = latest.Percent.HasValue ? $"{latest.Percent}%" : latest.State;
        string minimum = min.HasValue ? $"{min}%" : "—";
        _summary.Text = $"Latest: {value}  |  Minimum: {minimum}" +
            $"  |  Absent: {missing}  |  Unavailable: {unavailable}" +
            $"\nRecords: {_visible.Count}  |  Local CSV: battery-history.csv (last 30 days)";
    }

    private static void OpenHistoryFolder()
    {
        Directory.CreateDirectory(AppSettings.DirectoryPath);
        Process.Start(new ProcessStartInfo
        {
            FileName = AppSettings.DirectoryPath,
            UseShellExecute = true
        });
    }
}
