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
    private readonly Button _refresh = new();
    private readonly Button _folder = new();
    private IReadOnlyList<BatterySample> _visible = Array.Empty<BatterySample>();

    public BatteryHistoryForm(BatteryHistory history)
    {
        _history = history;
        Text = UiText.Get("AJAZZ APEX — Battery history");
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

        _refresh.Width = 115;
        _refresh.Click += (_, _) => RefreshData();
        _folder.Width = 175;
        _folder.Click += (_, _) => OpenHistoryFolder();

        buttons.Controls.Add(_range);
        buttons.Controls.Add(_refresh);
        buttons.Controls.Add(_folder);
        _summary.Dock = DockStyle.Bottom;
        _summary.Height = 52;
        _summary.Padding = new Padding(14, 6, 14, 6);
        _summary.Font = new Font("Segoe UI", 9);
        _graph.Dock = DockStyle.Fill;
        Controls.Add(_graph);
        Controls.Add(_summary);
        Controls.Add(buttons);
        ApplyLanguage();
    }

    /// <summary>Refresh captions without losing the chart or current range.</summary>
    public void ApplyLanguage()
    {
        Text = UiText.Get("AJAZZ APEX — Battery history");
        int selected = _range.SelectedIndex;
        _range.Items.Clear();
        foreach (string period in new[]
        {
            "Last 24 hours", "Last 7 days", "Last 30 days"
        }) _range.Items.Add(UiText.Get(period));
        _range.SelectedIndex = selected < 0 ? 1 : selected;
        _refresh.Text = UiText.Get("Refresh");
        _folder.Text = UiText.Get("Open CSV folder");
        UpdateSummary();
        _graph.Invalidate();
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
            _summary.Text = UiText.Get("No observations yet. History is saved locally.");
            return;
        }

        int missing = _visible.Count(x => x.State == "disconnected");
        int unavailable = _visible.Count(x => x.State == "unavailable");
        int? min = _visible.Where(x => x.Percent.HasValue)
                           .Select(x => x.Percent).Min();
        string value = latest.Percent.HasValue ? $"{latest.Percent}%" : latest.State;
        string minimum = min.HasValue ? $"{min}%" : "—";
        _summary.Text = UiText.Format(
            "Latest: {0}  |  Minimum: {1}  |  Absent: {2}  |  Unavailable: {3}",
            value, minimum, missing, unavailable) + "\n" +
            UiText.Format("Records: {0}  |  Local CSV: battery-history.csv (last 30 days)",
                _visible.Count);
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
