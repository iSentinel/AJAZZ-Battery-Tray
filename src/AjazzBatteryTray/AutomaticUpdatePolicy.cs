namespace AjazzBatteryTray;

/// <summary>Session scheduling only; no networking or persisted identifiers.</summary>
public sealed class AutomaticUpdatePolicy
{
    public const long InitialDelayMs = 60_000;
    public const long SuccessDelayMs = 24 * 60 * 60_000L;
    public const long FailureDelayMs = 60 * 60_000L;

    public sealed record Request(bool Experimental, long Generation);
    private Request? _pending;
    private long _generation;
    private long _due = long.MaxValue;
    private readonly HashSet<ReleaseVersion> _notified = new();
    public bool Enabled { get; private set; }
    public bool Experimental { get; private set; }

    public void Configure(bool enabled, bool experimental, long now)
    {
        if (Enabled == enabled && Experimental == experimental) return;
        Enabled = enabled;
        Experimental = experimental;
        _generation++;
        _due = enabled ? now + InitialDelayMs : long.MaxValue;
    }

    public Request? TryBegin(long now)
    {
        if (!Enabled || _pending is not null || now < _due) return null;
        _pending = new Request(Experimental, _generation);
        return _pending;
    }

    /// <summary>Return true only for a new notification from a current request.</summary>
    public bool Complete(Request request, bool success, ReleaseVersion? available, long now)
    {
        if (!ReferenceEquals(_pending, request)) return false;
        _pending = null;
        if (!Enabled || request.Generation != _generation) return false;
        _due = now + (success ? SuccessDelayMs : FailureDelayMs);
        return success && available is not null &&
            (Experimental || !available.Beta.HasValue) && _notified.Add(available);
    }
}
