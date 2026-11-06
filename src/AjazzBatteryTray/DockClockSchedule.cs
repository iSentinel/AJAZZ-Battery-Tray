namespace AjazzBatteryTray;

/// <summary>Resynchronizes on plug-in and periodically, without repeated writes.</summary>
public sealed class DockClockSchedule
{
    private readonly TimeSpan _interval = TimeSpan.FromMinutes(5);
    private DateTimeOffset? _lastAttempt;
    private bool _receiverWasPresent;

    /// <summary>Indicates when the next automatic clock update should run.</summary>
    public bool ShouldAttempt(DateTimeOffset now, bool enabled, bool receiverPresent)
    {
        if (!receiverPresent)
        {
            _receiverWasPresent = false;
            return false;
        }

        bool justConnected = !_receiverWasPresent;
        _receiverWasPresent = true;
        return enabled && (justConnected || !_lastAttempt.HasValue ||
                           now - _lastAttempt.Value >= _interval);
    }

    /// <summary>Records a send attempt even if it failed, preventing log spam.</summary>
    public void RecordAttempt(DateTimeOffset now)
    {
        _lastAttempt = now;
    }
}
