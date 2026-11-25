namespace AjazzBatteryTray;

/// <summary>Presentation-only state, independent of hardware transport.</summary>
public enum DeviceDashboardStatus
{
    NotChecked,
    Disabled,
    Standby,
    PresenceUnknown,
    Disconnected,
    NoReply,
    Fresh,
    ManualReading,
    Cached,
    Scheduled
}

public sealed record DeviceDashboardState(string Name, string Transport,
    DeviceDashboardStatus Status, int? Percent, DateTimeOffset? MeasuredAt)
{
    public static readonly TimeSpan MaximumFreshAge = TimeSpan.FromMinutes(5);

    public static DeviceDashboardState FromPoll(string name, string transport,
        bool checkedOnce, bool presenceKnown, bool present, int? fresh,
        DateTimeOffset? measuredAt, int? cached = null,
        DateTimeOffset? cachedAt = null, bool scheduled = false)
    {
        if (!checkedOnce)
            return new(name, transport, DeviceDashboardStatus.NotChecked, null, null);
        if (!presenceKnown)
            return new(name, transport, DeviceDashboardStatus.PresenceUnknown, null, null);
        if (!present)
            return new(name, transport, DeviceDashboardStatus.Disconnected, null, null);
        if (fresh is >= 0 and <= 100)
            return new(name, transport, scheduled ? DeviceDashboardStatus.Scheduled :
                DeviceDashboardStatus.Fresh, fresh, measuredAt);
        if (cached is >= 0 and <= 100 && cachedAt.HasValue)
            return new(name, transport, DeviceDashboardStatus.Cached, cached, cachedAt);
        return new(name, transport, DeviceDashboardStatus.NoReply, null, null);
    }
}
