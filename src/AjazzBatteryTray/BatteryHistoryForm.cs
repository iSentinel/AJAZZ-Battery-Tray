using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Read local battery observations and inspect the charge trend.</summary>
public sealed class BatteryHistoryForm : Form
{
    private readonly BatteryHistory _history;
    private readonly string _deviceTitle;
    private readonly bool _estimateEnabled;
    private readonly Label _analytics = new();
    private readonly BatteryGraphPanel _graph = new();
    private readonly Label _summary = new();
    private readonly ComboBox _range = new();
    private readonly Button _refresh = new();
    private readonly Button _folder = new();
    private IReadOnlyList<BatterySample> _visible = Array.Empty<BatterySample>();

    public BatteryHistoryForm(BatteryHistory history,
        string deviceTitle = "AJAZZ APEX", bool estimateEnabled = false)
    {
        _history = history;
        _deviceTitle = deviceTitle;
        _estimateEnabled = estimateEnabled;
        Text = _deviceTitle + " — " + UiText.Get("Battery history");
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
        _range.SelectionChangeCommitted += (_, _) => RefreshData();

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
        _analytics.Dock = DockStyle.Bottom;
        _analytics.Height = 98;
        _analytics.Padding = new Padding(14, 6, 14, 6);
        _analytics.Visible = _estimateEnabled;
        _graph.Dock = DockStyle.Fill;
        Controls.Add(_graph);
        Controls.Add(_analytics);
        Controls.Add(_summary);
        Controls.Add(buttons);
        ApplyLanguage();
    }

    /// <summary>Refresh captions without losing the chart or current range.</summary>
    public void ApplyLanguage()
    {
        Text = _deviceTitle + " — " + UiText.Get("Battery history");
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
        DateTimeOffset now = DateTimeOffset.UtcNow;
        DateTimeOffset cutoff = now.AddDays(-days);
        _graph.ReadFailed = !_history.TryReadRecent(out var samples);
        _visible = samples.Where(x => x.Timestamp >= cutoff && x.Timestamp <= now).ToArray();
        _graph.PeriodStart = cutoff;
        _graph.PeriodEnd = now;
        _graph.Samples = _visible;
        _graph.Invalidate();
        UpdateSummary();
    }

    private void UpdateSummary()
    {
        _analytics.Visible = _estimateEnabled && !_graph.ReadFailed;
        if (_graph.ReadFailed)
        {
            _summary.Text = _history.FileName;
            return;
        }
        UpdateAnalytics();
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
        string value = latest.Percent.HasValue ? $"{latest.Percent}%" :
            UiText.Get(latest.State == "disconnected" ? "Disconnected" : "unavailable");
        string minimum = min.HasValue ? $"{min}%" : "—";
        _summary.Text = UiText.Format(
            "Latest: {0}  |  Minimum: {1}  |  Absent: {2}  |  Unavailable: {3}",
            value, minimum, missing, unavailable) + "\n" +
            UiText.Format("Records: {0}  |  Local CSV: {1} (last 30 days)",
                _visible.Count, _history.FileName);
    }

    private void UpdateAnalytics()
    {
        if (!_estimateEnabled) return;
        DateTimeOffset now = DateTimeOffset.UtcNow;
        var estimate = BatteryAnalytics.EstimateDrain(_visible, now);
        double? observed = BatteryAnalytics.ObservedDischargeEquivalent(_visible, now);
        string equivalent = observed is double value
            ? UiText.Format("Observed discharge equivalents: {0:N2} (selected range; not battery health).", value)
            : UiText.Get("Observed discharge: insufficient observations.");
        if (estimate is null)
        {
            _analytics.Text = UiText.Get("Runtime estimate unavailable: insufficient recent discharge observations.") + "\n" + equivalent;
            return;
        }
        _analytics.Text = UiText.Format("Observed drain: {0:N1} pp/hour | Estimated runtime: {1:N1} hours",
            estimate.PercentPerHour, estimate.HoursRemaining) + "\n" +
            UiText.Format("Based on {0} observations over {1:N0} minutes; last measurement {2}.",
                estimate.Observations, estimate.ObservationSpan.TotalMinutes,
                estimate.LastMeasurement.ToLocalTime().ToString("g")) + "\n" +
            UiText.Get("Linear estimate at the observed rate; usage and charging may change it.") + "\n" + equivalent;
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
