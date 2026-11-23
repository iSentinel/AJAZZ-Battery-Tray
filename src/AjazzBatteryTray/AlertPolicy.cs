namespace AjazzBatteryTray;

/// <summary>Notifies once per selected low-battery level until recharged.</summary>
public sealed class AlertPolicy
{
    private const int Below50 = 1;
    private const int Below25 = 2;
    private const int Below10 = 4;
    private int _notified;

    /// <summary>Returns the most urgent newly reached threshold, if any.</summary>
    public int? Evaluate(int percent, bool below50 = true,
        bool below25 = true, bool below10 = true)
    {
        if (percent is < 0 or > 100) return null;

        // Five points of hysteresis prevent repeated alerts near a limit.
        if (percent >= 55) _notified &= ~Below50;
        if (percent >= 30) _notified &= ~Below25;
        if (percent >= 15) _notified &= ~Below10;

        int crossed = (percent < 50 ? Below50 : 0) |
            (percent < 25 ? Below25 : 0) | (percent < 10 ? Below10 : 0);
        int enabled = (below50 ? Below50 : 0) | (below25 ? Below25 : 0) |
            (below10 ? Below10 : 0);
        int eligible = crossed & enabled & ~_notified;
        if (eligible == 0) return null;

        // Preserve the prior policy: a jump marks all crossed levels, even muted ones.
        _notified |= crossed;
        return (eligible & Below10) != 0 ? 10 :
            (eligible & Below25) != 0 ? 25 : 50;
    }
}
