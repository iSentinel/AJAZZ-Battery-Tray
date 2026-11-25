using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Shows existing polling results; opening the window never issues HID requests.</summary>
internal sealed class DeviceDashboardForm : Form
{
    internal sealed record Entry(DeviceDashboardState State, Action? ShowHistory = null,
        string? Key = null, Action? EditName = null, bool? TrayVisible = null,
        Action? ToggleTray = null, Action? EditColor = null, Action? EditAlerts = null,
        Action? EditInterval = null, int? UnverifiedPercent = null);

    private readonly DataGridView _grid = new();
    private readonly Button _refresh = new();
    private readonly Button _history = new();
    private readonly Button _settings = new();
    private readonly Button _diagnostics = new();
    private readonly ContextMenuStrip _deviceMenu = new();
    private readonly ContextMenuStrip _diagnosticMenu = new();
    private readonly ToolStripMenuItem _rename = new();
    private readonly ToolStripMenuItem _visibility = new();
    private readonly ToolStripMenuItem _color = new();
    private readonly ToolStripMenuItem _alerts = new();
    private readonly ToolStripMenuItem _interval = new();
    private readonly ToolStripMenuItem _report = new();
    private readonly ToolStripMenuItem _telemetry = new();
    private readonly Button _close = new();
    private readonly Label _detail = new();
    private readonly Label _note = new();
    private bool _updatingRows;

    internal DeviceDashboardForm(Action refresh, Action diagnostics, Action telemetry)
    {
        Size = new Size(920, 470);
        MinimumSize = new Size(680, 350);
        StartPosition = FormStartPosition.CenterScreen;
        BuildLayout();
        _refresh.Click += (_, _) => refresh();
        _deviceMenu.Items.AddRange(new ToolStripItem[] { _rename, _visibility, _color, _alerts, _interval });
        _diagnosticMenu.Items.AddRange(new ToolStripItem[] { _report, _telemetry });
        AttachMenu(_settings, _deviceMenu);
        AttachMenu(_diagnostics, _diagnosticMenu);
        _report.Click += (_, _) => diagnostics();
        _telemetry.Click += (_, _) => telemetry();
        _history.Click += (_, _) => CurrentEntry()?.ShowHistory?.Invoke();
        _rename.Click += (_, _) => CurrentEntry()?.EditName?.Invoke();
        _visibility.Click += (_, _) => CurrentEntry()?.ToggleTray?.Invoke();
        _color.Click += (_, _) => CurrentEntry()?.EditColor?.Invoke();
        _alerts.Click += (_, _) => CurrentEntry()?.EditAlerts?.Invoke();
        _interval.Click += (_, _) => CurrentEntry()?.EditInterval?.Invoke();
        _close.Click += (_, _) => Close();
        CancelButton = _close;
        _grid.SelectionChanged += (_, _) => UpdateSelection();
        _grid.CellDoubleClick += (_, e) =>
        {
            if (e.RowIndex >= 0) CurrentEntry()?.ShowHistory?.Invoke();
        };
        ApplyLanguage();
    }

    private static void AttachMenu(Button button, ContextMenuStrip menu)
    {
        button.ContextMenuStrip = menu;
        button.AccessibleRole = AccessibleRole.ButtonDropDown;
        button.Click += (_, _) => menu.Show(button, new Point(0, button.Height));
        button.KeyDown += (_, e) =>
        {
            if (e.KeyCode != Keys.Down) return;
            e.SuppressKeyPress = true;
            button.PerformClick();
        };
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _deviceMenu.Dispose();
            _diagnosticMenu.Dispose();
        }
        base.Dispose(disposing);
    }

    private void BuildLayout()
    {
        TableLayoutPanel layout = new()
        {
            Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 4, Padding = new Padding(12)
        };
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        _note.AutoSize = true;
        _note.Margin = new Padding(3, 5, 3, 12);
        _detail.AutoSize = true;
        _detail.Margin = new Padding(3, 10, 3, 6);
        ConfigureGrid();
        _grid.TabIndex = 0;
        FlowLayoutPanel actions = new()
        {
            Dock = DockStyle.Fill, AutoSize = true, WrapContents = true, TabIndex = 1
        };
        foreach (Button button in new[] { _refresh, _history, _settings, _diagnostics, _close })
        {
            button.AutoSize = true;
            button.TabIndex = actions.Controls.Count;
            button.Padding = new Padding(6, 3, 6, 3);
            actions.Controls.Add(button);
        }
        layout.Controls.Add(_note, 0, 0);
        layout.Controls.Add(_grid, 0, 1);
        layout.Controls.Add(_detail, 0, 2);
        layout.Controls.Add(actions, 0, 3);
        Controls.Add(layout);
    }

    private void ConfigureGrid()
    {
        _grid.Dock = DockStyle.Fill;
        _grid.ReadOnly = true;
        _grid.AllowUserToAddRows = false;
        _grid.AllowUserToDeleteRows = false;
        _grid.AllowUserToResizeRows = false;
        _grid.MultiSelect = false;
        _grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
        _grid.RowHeadersVisible = false;
        _grid.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;
        _grid.BackgroundColor = SystemColors.Window;
        _grid.DefaultCellStyle.WrapMode = DataGridViewTriState.True;
        _grid.AutoSizeRowsMode = DataGridViewAutoSizeRowsMode.AllCells;
        _grid.BorderStyle = BorderStyle.FixedSingle;
        foreach (string name in new[] { "Device", "Transport", "Status", "Battery", "Tray preference", "Last measurement" })
        {
            int index = _grid.Columns.Add(name, name);
            _grid.Columns[index].SortMode = DataGridViewColumnSortMode.NotSortable;
            _grid.Columns[index].FillWeight = name == "Device" ? 165 :
                name == "Battery" ? 65 : 105;
        }
    }

    internal void ApplyLanguage()
    {
        Text = UiText.Get("Device Manager");
        _note.Text = UiText.Get("Live monitor — existing readings only; cached values are marked.");
        _refresh.Text = UiText.Get("Refresh now");
        _history.Text = UiText.Get("Battery history...");
        _rename.Text = UiText.Get("Edit local name...");
        _color.Text = UiText.Get("Tray icon color...");
        _alerts.Text = UiText.Get("Device notifications...");
        _interval.Text = UiText.Get("Device polling interval...");
        _settings.Text = UiText.Get("Device settings") + " ▾";
        _diagnostics.Text = UiText.Get("Diagnostics") + " ▾";
        _report.Text = UiText.Get("Collect full diagnostics...");
        _telemetry.Text = UiText.Get("System telemetry preview...");
        _close.Text = UiText.Get("Close");
        foreach (DataGridViewColumn column in _grid.Columns)
            column.HeaderText = UiText.Get(column.Name);
        UpdateSelection();
    }

    internal void SetEntries(IReadOnlyList<Entry> entries)
    {
        Entry? previous = CurrentEntry();
        _updatingRows = true;
        _grid.SuspendLayout();
        try
        {
            _grid.Rows.Clear();
            int selected = -1;
            foreach (Entry entry in entries)
            {
                var state = entry.State;
                int row = _grid.Rows.Add(state.Name, state.Transport,
                    EntryStatus(entry), FormatBattery(entry),
                    entry.TrayVisible is bool visible ? UiText.Get(visible ? "Allowed" : "Hidden") : "—",
                    state.MeasuredAt?.ToLocalTime().ToString("g") ?? "—");
                _grid.Rows[row].Tag = entry;
                _grid.Rows[row].Cells["Battery"].ToolTipText = HasUnverifiedField(entry)
                    ? UsbTrayStatus.UnverifiedField(entry.UnverifiedPercent!.Value)
                    : FormatBattery(entry);
                if (previous is not null && (previous.Key is not null
                    ? previous.Key == entry.Key
                    : entry.Key is null && previous.State.Name == state.Name &&
                      previous.State.Transport == state.Transport)) selected = row;
            }
            if (selected < 0 && _deviceMenu.Visible) _deviceMenu.Close();
            if (selected >= 0) _grid.CurrentCell = _grid.Rows[selected].Cells[0];
        }
        finally
        {
            _grid.ResumeLayout();
            _updatingRows = false;
        }
        UpdateSelection();
    }

    private static bool HasUnverifiedField(Entry entry)
        => entry.State.Status == DeviceDashboardStatus.NoReply &&
            entry.State.Percent is null && entry.UnverifiedPercent is >= 1 and <= 100;

    private static string EntryStatus(Entry entry)
        => HasUnverifiedField(entry) ? UiText.Get("Unverified charge field") : entry.State.StatusText();

    private static string FormatBattery(Entry entry)
        => entry.State.Percent is int level
            ? $"{level}%" + (entry.State.Status == DeviceDashboardStatus.Cached ? "*" : "")
            : HasUnverifiedField(entry) ? $"{entry.UnverifiedPercent}?" : "—";

    private Entry? CurrentEntry() => _grid.CurrentRow?.Tag as Entry;

    private void UpdateSelection()
    {
        if (_updatingRows) return;
        Entry? entry = CurrentEntry();
        _history.Enabled = entry?.ShowHistory is not null;
        _rename.Enabled = entry?.EditName is not null;
        _visibility.Enabled = entry?.ToggleTray is not null;
        _color.Enabled = entry?.EditColor is not null;
        _alerts.Enabled = entry?.EditAlerts is not null;
        _interval.Enabled = entry?.EditInterval is not null;
        _settings.Enabled = _rename.Enabled || _visibility.Enabled || _color.Enabled ||
            _alerts.Enabled || _interval.Enabled;
        _visibility.Text = UiText.Get(entry?.TrayVisible == true ? "Hide device in tray" : "Show device in tray");
        _detail.Text = entry is null ? UiText.Get("No device readings yet") :
            $"{entry.State.Name} — {EntryStatus(entry)}";
    }
}
