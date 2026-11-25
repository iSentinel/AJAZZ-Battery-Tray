namespace AjazzBatteryTray;

/// <summary>Transient reply loss must not turn a cached value into fresh telemetry.</summary>
public sealed class AulaBatteryState
{
    public static readonly TimeSpan CacheLifetime = TimeSpan.FromHours(24);
    public int? LastGoodPercent { get; private set; }
    public DateTimeOffset? LastGoodAt { get; private set; }
    public int ConsecutiveFailures { get; private set; }

    public void Observe(bool present, bool known, int? percent, DateTimeOffset now)
    {
        if (!known)
        {
            // Hide cache while presence is uncertain, but retain the last
            // confirmed sample until the same receiver is seen again.
            return;
        }
        if (!present)
        {
            Reset();
            return;
        }
        if (percent is >= 1 and <= 100)
        {
            LastGoodPercent = percent;
            LastGoodAt = now;
            ConsecutiveFailures = 0;
        }
        else if (ConsecutiveFailures < int.MaxValue)
            ConsecutiveFailures++;
    }

    /// <summary>Cache is display-only, bounded by age and confirmed receiver presence.</summary>
    public int? CachedPercent(bool present, bool known, DateTimeOffset now)
    {
        if (!known || !present) return null;
        if (LastGoodAt is not { } at || now < at || now - at >= CacheLifetime)
            return null;
        return LastGoodPercent;
    }

    /// <summary>Project AULA observations consistently for the dashboard and local API.</summary>
    public DeviceDashboardState Dashboard(string name, bool automatic, bool checkedOnce,
        bool known, bool present, int? fresh, DateTimeOffset? measuredAt, DateTimeOffset now)
    {
        const string transport = "2.4 GHz";
        if (!automatic && !checkedOnce)
            return new(name, transport, DeviceDashboardStatus.Disabled, null, null);
        if (fresh is not (>= 1 and <= 100) || measuredAt is not { } at ||
            at > now || now - at > DeviceDashboardState.MaximumFreshAge ||
            fresh != LastGoodPercent || at != LastGoodAt)
            fresh = null;
        int? cached = CachedPercent(present, known, now);
        var state = DeviceDashboardState.FromPoll(name, transport, checkedOnce,
            known, present, fresh, measuredAt, cached, LastGoodAt);
        return !automatic && state.Status == DeviceDashboardStatus.Fresh
            ? state with { Status = DeviceDashboardStatus.ManualReading } : state;
    }

    public void Reset()
    {
        LastGoodPercent = null;
        LastGoodAt = null;
        ConsecutiveFailures = 0;
    }
}
