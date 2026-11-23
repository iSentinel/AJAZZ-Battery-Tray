namespace AjazzBatteryTray;

/// <summary>Pure, independent sampling deadlines; callers supply monotonic time.</summary>
public sealed class DevicePollSchedule
{
    private readonly Dictionary<string, long> _lastAttempt = new(StringComparer.Ordinal);
    private HashSet<string>? _presentScratch;
    private List<string>? _removedScratch;

    public static bool IsValidInterval(int seconds) => seconds is 15 or 30 or 60 or 120;

    public static int NormalizeInterval(int seconds) => IsValidInterval(seconds) ? seconds : 30;

    public static int ResolveInterval(int globalSeconds, int? customSeconds)
        => customSeconds is int value && IsValidInterval(value)
            ? value : NormalizeInterval(globalSeconds);

    /// <summary>USB discovery uses the shortest configured interval except AULA.</summary>
    public static int DiscoverySeconds(int globalSeconds, IReadOnlyDictionary<string, int> overrides)
    {
        int shortest = globalSeconds;
        foreach (var pair in overrides)
            if (pair.Key != DeviceAliasRules.AulaSlot)
                shortest = Math.Min(shortest, NormalizeInterval(pair.Value));
        return shortest;
    }

    public static Dictionary<string, int> CleanOverrides(Dictionary<string, int>? values)
    {
        Dictionary<string, int> clean = new(StringComparer.Ordinal);
        if (values is null) return clean;
        foreach (var pair in values)
            if (DeviceAliasRules.ValidKey(pair.Key) && IsValidInterval(pair.Value))
                clean[pair.Key] = pair.Value;
        return clean;
    }

    /// <summary>Unknown or reset receivers are immediately due; no catch-up bursts.</summary>
    public bool IsDue(string key, long nowMilliseconds, int seconds, bool force = false)
    {
        if (!DeviceAliasRules.ValidKey(key)) return false;
        if (force || !_lastAttempt.TryGetValue(key, out long last)) return true;
        if (nowMilliseconds < last) return true;
        return (decimal)nowMilliseconds - last >= NormalizeInterval(seconds) * 1000L;
    }

    /// <summary>Record completion of an actual attempt, including a failed read.</summary>
    public void Complete(string key, long nowMilliseconds)
    {
        if (DeviceAliasRules.ValidKey(key)) _lastAttempt[key] = nowMilliseconds;
    }

    public void Reset(string key) => _lastAttempt.Remove(key);

    /// <summary>Forget absent devices only after successful, complete discovery.</summary>
    public void Reconcile(IEnumerable<string> presentKeys, bool presenceKnown)
    {
        if (!presenceKnown || _lastAttempt.Count == 0) return;
        var present = _presentScratch ??= new(StringComparer.Ordinal);
        var removed = _removedScratch ??= new();
        present.Clear();
        removed.Clear();
        try
        {
            foreach (string key in presentKeys) present.Add(key);
            foreach (string key in _lastAttempt.Keys)
                if (!present.Contains(key)) removed.Add(key);
            foreach (string key in removed) _lastAttempt.Remove(key);
        }
        finally
        {
            // Never hold a scratch reference to a removed receiver identity.
            present.Clear();
            removed.Clear();
        }
    }
}
