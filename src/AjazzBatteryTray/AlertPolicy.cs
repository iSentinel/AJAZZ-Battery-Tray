namespace AjazzBatteryTray;

/// <summary>Limits low-battery alerts to one notification per threshold crossing.</summary>
public sealed class AlertPolicy
{
    private int? _lastThreshold;

    /// <summary>Returns the newly reached threshold, or null if no alert is needed.</summary>
    public int? Evaluate(int percent)
    {
        // Recharge above 25% to allow a new sequence of alerts.
        if (percent > 25)
        {
            _lastThreshold = null;
        }

        int? threshold = percent switch
        {
            <= 5 => 5,
            <= 10 => 10,
            <= 20 => 20,
            _ => null
        };

        if (threshold is null || (_lastThreshold is not null &&
                                   threshold.Value >= _lastThreshold.Value))
        {
            return null;
        }

        _lastThreshold = threshold;
        return threshold;
    }
}
