namespace AjazzBatteryTray;

/// <summary>Notifies once per selected low-battery level until recharged.</summary>
public sealed class AlertPolicy
{
    private static readonly int[] Levels = { 50, 25, 10 };
    private readonly HashSet<int> _notified = new();

    /// <summary>Returns the most urgent newly reached threshold, if any.</summary>
    public int? Evaluate(int percent, bool below50 = true,
        bool below25 = true, bool below10 = true)
    {
        if (percent is < 0 or > 100) return null;

        // Five points of hysteresis prevent repeated alerts near a limit.
        foreach (int level in Levels)
        {
            if (percent >= level + 5) _notified.Remove(level);
        }

        int? reached = null;
        foreach (int level in Levels.Reverse())
        {
            bool enabled = level switch
            {
                50 => below50,
                25 => below25,
                10 => below10,
                _ => false
            };
            if (enabled && percent < level && !_notified.Contains(level))
            {
                reached = level;
                break;
            }
        }

        if (!reached.HasValue) return null;

        // A jump to 9% needs one urgent alert, not three stale alerts.
        foreach (int level in Levels)
        {
            if (percent < level) _notified.Add(level);
        }
        return reached;
    }
}
