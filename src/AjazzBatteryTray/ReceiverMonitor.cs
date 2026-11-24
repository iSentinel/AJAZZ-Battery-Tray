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
        internal DateTimeOffset? MeasuredAt { get; set; }
        internal DateTimeOffset? LastVerifiedAt { get; set; }
        internal bool ScheduledSkip { get; set; }
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

    private static readonly AjazzHidReader.Reading AbsentReading =
        new(false, null, "Receiver absent");
    private static readonly AjazzHidReader.Reading UnknownReading =
        new(false, null, "HID enumeration unavailable", PresenceKnown: false);
    private readonly Dictionary<string, State> _states = new();
    private readonly Dictionary<string, ExtraIcon> _icons = new();
    private InventoryFrameScratch? _receiverScratch;
    private InventoryFrameScratch? _iconScratch;
    internal IEnumerable<State> Devices => _states.Values;
    internal string? PrimaryKey { get; private set; }
    internal State? PrimaryState => PrimaryKey is not null &&
        _states.TryGetValue(PrimaryKey, out State? state) ? state : null;
    internal State? SummaryState { get; private set; }

    internal State? VisiblePrimary(bool multiple, IReadOnlySet<string> hidden)
    {
        string? preferred = multiple ? PrimaryKey : SummaryState?.Key;
        if (preferred is not null && _states.TryGetValue(preferred, out var primary) &&
            primary.Present && !hidden.Contains(preferred))
            return primary;
        State? first = null;
        foreach (var state in _states.Values)
        {
            if (!state.Present || hidden.Contains(state.Key)) continue;
            if (first is null || StringComparer.Ordinal.Compare(state.Key, first.Key) < 0)
                first = state;
        }
        return first;
    }

    internal void Apply(AjazzHidReader.Batch batch, AppSettings settings,
        NotifyIcon notifier, bool bluetoothEnabled, DateTimeOffset now)
    {
        if (!batch.Summary.PresenceKnown)
        {
            foreach (State state in _states.Values.Where(s => s.Present))
                state.Reading = UnknownReading;
            return;
        }

        var seen = _receiverScratch ??= new();
        seen.Begin();
        try
        {
            foreach (var item in batch.Receivers)
            {
                seen.Add(item.Key);
                State state = FindOrCreate(item);
                state.Alias = settings.DeviceAliases.GetValueOrDefault(item.Key);
                state.Present = true;
                state.ScheduledSkip = !item.Sampled;
                if (!item.Sampled) continue;
                state.Reading = item.Reading;
                state.MeasuredAt = item.MeasuredAt ?? now;
                if (item.Reading.Percent.HasValue) state.LastVerifiedAt = state.MeasuredAt;
                Record(state, settings, notifier, bluetoothEnabled, state.MeasuredAt.Value);
            }

            foreach (string missingKey in seen.Missing(_states.Keys))
            {
                State missing = _states[missingKey];
                missing.Present = false;
                missing.Reading = AbsentReading;
                missing.ScheduledSkip = false;
                missing.MeasuredAt = null;
                Record(missing, settings, notifier,
                    bluetoothEnabled && batch.Receivers.Count == 0, now);
            }

            PrimaryKey = ReceiverIdentity.SelectPrimary(PrimaryKey, seen.Keys);
            SummaryState = null;
            foreach (var item in batch.Receivers)
            {
                var state = _states[item.Key];
                SummaryState ??= state;
                if (!state.Reading.Percent.HasValue) continue;
                SummaryState = state;
                break;
            }
        }
        finally
        {
            seen.End();
        }
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
            settings.EffectiveDisconnectAlert(state.Key) && !bluetoothEnabled)
            notifier.ShowBalloonTip(4000, state.DisplayLabel,
                UiText.Get("The 2.4 GHz receiver is no longer detected."),
                ToolTipIcon.Warning);
        if (percent is not int level) return;
        int mask = settings.EffectiveAlertMask(state.Key);
        int? threshold = state.Alerts.Evaluate(level,
            (mask & 1) != 0, (mask & 2) != 0, (mask & 4) != 0);
        if (threshold.HasValue)
            notifier.ShowBalloonTip(5000, state.DisplayLabel,
                UiText.Format("Mouse battery is {0}% ({1}); below {2}%.",
                    level, "2.4 GHz", threshold), ToolTipIcon.Warning);
    }

    internal static string Status(State state)
        => state.Reading.Percent is int level ? $"{level}%" :
            UsbTrayStatus.WithLastVerified(
                UsbTrayStatus.Reason(state.Reading.PresenceKnown, state.Present, state.Reading.Issue),
                state.LastVerifiedAt);

    internal void PopulateMenu(ToolStripMenuItem menu, Action<State> edit,
        Func<string, bool> visible, Action<string> toggle,
        Action<State> editColor, Action<State> editAlerts, Action<State> editInterval)
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
            visibility.Click += (_, _) =>
            {
                toggle(state.Key);
                visibility.Checked = visible(state.Key);
            };
            item.DropDownItems.Add(visibility);
            item.DropDownItems.Add(UiText.Get("Tray icon color..."), null, (_, _) => editColor(state));
            item.DropDownItems.Add(UiText.Get("Device notifications..."), null, (_, _) => editAlerts(state));
            item.DropDownItems.Add(UiText.Get("Device polling interval..."), null, (_, _) => editInterval(state));
            menu.DropDownItems.Add(item);
        }
        if (menu.DropDownItems.Count == 0)
            menu.DropDownItems.Add(new ToolStripMenuItem(UiText.Get("unavailable")) { Enabled = false });
    }

    internal static void ShowHistory(State state)
    {
        if (state.Window is null || state.Window.IsDisposed)
            state.Window = new BatteryHistoryForm(state.History, state.DisplayLabel, estimateEnabled: true);
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
        string? visiblePrimaryKey, IReadOnlySet<string> hidden,
        Func<string, string> color,
        IReadOnlyList<(string Key, string Name, int? Percent)> bluetooth)
    {
        if (!enabled)
        {
            foreach (var icon in _icons.Values) icon.Dispose();
            _icons.Clear();
            return;
        }
        var wanted = _iconScratch ??= new();
        wanted.Begin();
        try
        {
            foreach (var pair in _states)
            {
                if (!pair.Value.Present || pair.Key == visiblePrimaryKey || hidden.Contains(pair.Key)) continue;
                wanted.Add(pair.Key);
                SetIcon(pair.Key, pair.Value.DisplayLabel, pair.Value.Reading.Percent, menu, refresh,
                    color: color(pair.Key), status: pair.Value.Reading.Percent.HasValue ? null : Status(pair.Value));
            }
            if (showAula && !aulaIsPrimary)
            {
                wanted.Add("AULA");
                SetIcon("AULA", aulaName, aulaLevel, menu, refresh, aulaStale,
                    color(DeviceAliasRules.AulaSlot));
            }
            foreach (var item in bluetooth)
            {
                wanted.Add(item.Key);
                SetIcon(item.Key, item.Name, item.Percent, menu, refresh);
            }

            foreach (string key in wanted.Missing(_icons.Keys))
            {
                _icons[key].Dispose();
                _icons.Remove(key);
            }
        }
        finally
        {
            wanted.End();
        }
    }

    private void SetIcon(string key, string name, int? level, ContextMenuStrip menu,
        Action refresh, bool stale = false, string? color = null, string? status = null)
    {
        if (!_icons.TryGetValue(key, out ExtraIcon? icon))
        {
            icon = new ExtraIcon(refresh);
            _icons.Add(key, icon);
        }
        icon.Update(name, level, menu, stale, color, status);
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
        private TrayIconRenderKey? _renderKey;

        internal ExtraIcon(Action refresh) => _tray.DoubleClick += (_, _) => refresh();

        internal void Update(string name, int? level, ContextMenuStrip menu, bool stale, string? color, string? status)
        {
            if (!ReferenceEquals(_tray.ContextMenuStrip, menu)) _tray.ContextMenuStrip = menu;
            string label = $"{(level.HasValue ? $"{level}%" : UiText.Get("unavailable"))} — {name}";
            if (status is not null) label = $"2.4 GHz · {status} — {name}";
            if (stale) label = UiText.Get("cached") + ": " + label;
            label = label[..Math.Min(63, label.Length)];
            if (_tray.Text != label) _tray.Text = label;
            var key = TrayIconRenderKey.Create(level, level.HasValue, stale, color: color);
            if (_icon is null || _renderKey != key)
            {
                Icon next = TrayIconFactory.Create(level, level.HasValue, stale, color: color);
                try { _tray.Icon = next; }
                catch { next.Dispose(); throw; }
                _icon?.Dispose();
                _icon = next;
                _renderKey = key;
            }
            if (!_tray.Visible) _tray.Visible = true;
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
