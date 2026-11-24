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
    public string StatusText => UiText.Get(Status switch
    {
        DeviceDashboardStatus.NotChecked => "Not checked",
        DeviceDashboardStatus.Disabled => "Monitoring disabled",
        DeviceDashboardStatus.Standby => "Standby (USB priority)",
        DeviceDashboardStatus.PresenceUnknown => "Receiver status unknown",
        DeviceDashboardStatus.Disconnected => "Disconnected",
        DeviceDashboardStatus.NoReply => "No valid reply",
        DeviceDashboardStatus.Fresh => "Fresh reading",
        DeviceDashboardStatus.ManualReading => "Manual reading",
        DeviceDashboardStatus.Cached => "Cached reading",
        DeviceDashboardStatus.Scheduled => "Last scheduled reading",
        _ => "unavailable"
    });

    /// <summary>Show measurement provenance without inventing a current sample.</summary>
    public string MenuStatus(DateTimeOffset? lastVerified = null)
    {
        string text = StatusText;
        if (Percent is int level && MeasuredAt is { } stamp &&
            Status is DeviceDashboardStatus.Fresh or DeviceDashboardStatus.ManualReading
                or DeviceDashboardStatus.Cached or DeviceDashboardStatus.Scheduled)
            return $"{level}% · {text} · {stamp.ToLocalTime():g}";
        return Status == DeviceDashboardStatus.NoReply
            ? UsbTrayStatus.WithLastVerified(text, lastVerified) : text;
    }

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
