using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Independent Windows receiver state, history and notifications.</summary>
internal sealed class ReceiverMonitor : IDisposable
{
    internal sealed class State : IDisposable
    {
        internal string Key { get; }
        internal string Label { get; set; }
        internal string? Alias { get; set; }
        internal string DisplayLabel => DeviceAliasRules.DisplayName(Label, Alias);
        internal ushort? Revision { get; set; }
        internal BatteryHistory History { get; }
        internal AlertPolicy Alerts { get; } = new();
        internal ConnectionAlertPolicy Connection { get; } = new();
        internal AjazzHidReader.Reading Reading { get; set; }
        internal bool Present { get; set; } = true;
        internal BatteryHistoryForm? Window { get; set; }

        internal State(AjazzHidReader.ReceiverReading item, string label)
        {
            Key = item.Key;
            Label = label;
            Revision = item.Revision;
            Reading = item.Reading;
            History = new BatteryHistory("ajazz-" + item.Key + "-history.csv");
        }

        public void Dispose() => Window?.Dispose();
    }

    private readonly Dictionary<string, State> _states = new();
    private readonly Dictionary<string, ExtraIcon> _icons = new();
    internal IEnumerable<State> Devices => _states.Values;
    internal string? PrimaryKey { get; private set; }
    internal State? PrimaryState => PrimaryKey is not null &&
        _states.TryGetValue(PrimaryKey, out State? state) ? state : null;
    internal State? SummaryState { get; private set; }

    internal State? VisiblePrimary(bool multiple, IReadOnlySet<string> hidden)
    {
        string? key = TrayVisibilityRules.SelectMouse(
            multiple ? PrimaryKey : SummaryState?.Key,
            _states.Values.Where(s => s.Present).Select(s => s.Key), hidden);
        return key is not null ? _states[key] : null;
    }

    internal void Apply(AjazzHidReader.Batch batch, AppSettings settings,
        NotifyIcon notifier, bool bluetoothEnabled, DateTimeOffset now)
    {
        if (!batch.Summary.PresenceKnown)
        {
            foreach (State state in _states.Values.Where(s => s.Present))
                state.Reading = new(false, null, "HID enumeration unavailable",
                    PresenceKnown: false);
            return;
        }

        HashSet<string> seen = new();
        foreach (var item in batch.Receivers)
        {
            seen.Add(item.Key);
            State state = FindOrCreate(item);
            state.Alias = settings.DeviceAliases.GetValueOrDefault(item.Key);
            state.Present = true;
            state.Reading = item.Reading;
            Record(state, settings, notifier, bluetoothEnabled, now);
        }

        foreach (var pair in _states.Where(x => !seen.Contains(x.Key)))
        {
            pair.Value.Present = false;
            pair.Value.Reading = new(false, null, "Receiver absent");
            Record(pair.Value, settings, notifier,
                bluetoothEnabled && batch.Receivers.Count == 0, now);
        }

        PrimaryKey = ReceiverIdentity.SelectPrimary(PrimaryKey, seen);
        var summary = AjazzHidReader.Primary(batch.Receivers);
        SummaryState = summary is not null ? _states[summary.Key] : null;
    }

    private State FindOrCreate(AjazzHidReader.ReceiverReading item)
    {
        if (_states.TryGetValue(item.Key, out State? state))
        {
            if (!state.Revision.HasValue && item.Revision.HasValue)
            {
                state.Revision = item.Revision;
                state.Label = UniqueLabel(item.Revision);
                state.Window?.Dispose();
                state.Window = null;
            }
            return state;
        }
        state = new State(item, UniqueLabel(item.Revision));
        _states.Add(item.Key, state);
        return state;
    }

    private string UniqueLabel(ushort? revision)
    {
        string label = ReceiverIdentity.Label(revision);
        string unique = label;
        int index = 2;
        while (_states.Values.Any(x => x.Label == unique))
            unique = $"{label} #{index++}";
        return unique;
    }

    private static void Record(State state, AppSettings settings, NotifyIcon notifier,
        bool bluetoothEnabled, DateTimeOffset now)
    {
        int? percent = state.Reading.Percent;
        if (settings.RecordBatteryHistory)
            state.History.Record(now, percent, state.Present);
        if (state.Connection.Evaluate(percent.HasValue, state.Present) &&
            settings.NotifyOnDisconnect && !bluetoothEnabled)
            notifier.ShowBalloonTip(4000, state.DisplayLabel,
                UiText.Get("The 2.4 GHz receiver is no longer detected."),
                ToolTipIcon.Warning);
        if (percent is not int level) return;
        int? threshold = state.Alerts.Evaluate(level,
            settings.NotificationsEnabled && settings.AlertBelow50,
            settings.NotificationsEnabled && settings.AlertBelow25,
            settings.NotificationsEnabled && settings.AlertBelow10);
        if (threshold.HasValue)
            notifier.ShowBalloonTip(5000, state.DisplayLabel,
                UiText.Format("Mouse battery is {0}% ({1}); below {2}%.",
                    level, "2.4 GHz", threshold), ToolTipIcon.Warning);
    }

    internal static string Status(State state)
        => !state.Present ? UiText.Get("unavailable") :
            state.Reading.Percent is int level ? $"{level}%" : UiText.Get("unavailable");

    internal void PopulateMenu(ToolStripMenuItem menu, Action<State> edit,
        Func<string, bool> visible, Action<string> toggle)
    {
        foreach (ToolStripItem old in menu.DropDownItems.Cast<ToolStripItem>().ToArray())
            old.Dispose();
        menu.DropDownItems.Clear();
        foreach (State state in _states.Values)
        {
            ToolStripMenuItem item = new($"{state.DisplayLabel}: {Status(state)}");
            item.DropDownItems.Add(UiText.Get("Battery history..."), null,
                (_, _) => ShowHistory(state));
            item.DropDownItems.Add(UiText.Get("Edit local name..."), null, (_, _) => edit(state));
            ToolStripMenuItem visibility = new(UiText.Get("Show device in tray"))
            {
                Checked = visible(state.Key)
            };
            visibility.Click += (_, _) => toggle(state.Key);
            item.DropDownItems.Add(visibility);
            menu.DropDownItems.Add(item);
        }
        if (menu.DropDownItems.Count == 0)
            menu.DropDownItems.Add(new ToolStripMenuItem(UiText.Get("unavailable")) { Enabled = false });
    }

    internal static void ShowHistory(State state)
    {
        if (state.Window is null || state.Window.IsDisposed)
            state.Window = new BatteryHistoryForm(state.History, state.DisplayLabel);
        state.Window.RefreshData();
        state.Window.Show();
        state.Window.BringToFront();
    }

    internal void ApplyLanguage()
    {
        foreach (State state in _states.Values)
            if (state.Window is { IsDisposed: false }) state.Window.ApplyLanguage();
    }

    /// <summary>One shared menu; primary icon is owned by TrayAppContext.</summary>
    internal void RefreshIcons(bool enabled, bool showAula, int? aulaLevel, bool aulaStale,
        bool aulaIsPrimary, ContextMenuStrip menu, Action refresh, string aulaName,
        string? visiblePrimaryKey, IReadOnlySet<string> hidden)
    {
        HashSet<string> wanted = new();
        if (enabled)
        {
            foreach (var pair in _states)
            {
                if (!pair.Value.Present || pair.Key == visiblePrimaryKey || hidden.Contains(pair.Key)) continue;
                wanted.Add(pair.Key);
                SetIcon(pair.Key, pair.Value.DisplayLabel, pair.Value.Reading.Percent, menu, refresh);
            }
            if (showAula && !aulaIsPrimary)
            {
                wanted.Add("AULA");
                SetIcon("AULA", aulaName, aulaLevel, menu, refresh, aulaStale);
            }
        }

        foreach (string key in _icons.Keys.Where(x => !wanted.Contains(x)).ToArray())
        {
            _icons[key].Dispose();
            _icons.Remove(key);
        }
    }

    private void SetIcon(string key, string name, int? level, ContextMenuStrip menu,
        Action refresh, bool stale = false)
    {
        if (!_icons.TryGetValue(key, out ExtraIcon? icon))
        {
            icon = new ExtraIcon(refresh);
            _icons.Add(key, icon);
        }
        icon.Update(name, level, menu, stale);
    }

    public void Dispose()
    {
        foreach (ExtraIcon icon in _icons.Values) icon.Dispose();
        _icons.Clear();
        foreach (State state in _states.Values) state.Dispose();
        _states.Clear();
    }

    private sealed class ExtraIcon : IDisposable
    {
        private readonly NotifyIcon _tray = new();
        private Icon? _icon;
        private int? _last;
        private bool _stale;

        internal ExtraIcon(Action refresh) => _tray.DoubleClick += (_, _) => refresh();

        internal void Update(string name, int? level, ContextMenuStrip menu, bool stale)
        {
            _tray.ContextMenuStrip = menu;
            string label = $"{(level.HasValue ? $"{level}%" : UiText.Get("unavailable"))} — {name}";
            if (stale) label = UiText.Get("cached") + ": " + label;
            _tray.Text = label[..Math.Min(63, label.Length)];
            if (_icon is null || _last != level || _stale != stale)
            {
                Icon next = TrayIconFactory.Create(level, level.HasValue, stale);
                _tray.Icon = next;
                _icon?.Dispose();
                _icon = next;
                _last = level;
                _stale = stale;
            }
            _tray.Visible = true;
        }

        public void Dispose()
        {
            _tray.Visible = false;
            _tray.ContextMenuStrip = null;
            _tray.Dispose();
            _icon?.Dispose();
        }
    }
}
