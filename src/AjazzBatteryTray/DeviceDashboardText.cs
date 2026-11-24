namespace AjazzBatteryTray;

/// <summary>Localized UI projection, separate from the shared data model.</summary>
public static class DeviceDashboardText
{
    public static string StatusText(this DeviceDashboardState state) => UiText.Get(state.Status switch
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
    public static string MenuStatus(this DeviceDashboardState state, DateTimeOffset? lastVerified = null)
    {
        string text = state.StatusText();
        if (state.Percent is int level && state.MeasuredAt is { } stamp &&
            state.Status is DeviceDashboardStatus.Fresh or DeviceDashboardStatus.ManualReading
                or DeviceDashboardStatus.Cached or DeviceDashboardStatus.Scheduled)
            return $"{level}% · {text} · {stamp.ToLocalTime():g}";
        return state.Status == DeviceDashboardStatus.NoReply && lastVerified is { } verified
            ? text + " · " + UiText.Format("Last verified {0}", verified.ToLocalTime().ToString("g")) : text;
    }
}
