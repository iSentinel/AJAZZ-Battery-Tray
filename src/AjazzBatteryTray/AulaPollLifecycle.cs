namespace AjazzBatteryTray;

/// <summary>UI-thread-only lifecycle for optional single-flight AULA polls.</summary>
public sealed class AulaPollLifecycle
{
    private long _version;
    private long? _active;
    private bool _closed;
    public bool Enabled { get; private set; }
    public bool IsBusy => _active.HasValue;
    public bool CanArm => Enabled && !_closed && !IsBusy;

    public void Configure(bool enabled)
    {
        if (_closed || Enabled == enabled) return;
        Enabled = enabled;
        _version++;
    }

    public long? TryBegin(bool manual)
    {
        if (_closed || IsBusy || (!manual && !Enabled)) return null;
        _active = ++_version;
        return _active;
    }

    public bool MayApply(long ticket) =>
        !_closed && _active == ticket && _version == ticket;

    /// <summary>Return the next delay only if automatic monitoring remains enabled.</summary>
    public int? Complete(long ticket, int normalDelay)
    {
        if (_active != ticket) return null;
        _active = null;
        if (!CanArm) return null;
        // Re-enable during an old read: discard the reply and promptly sample again.
        return ticket == _version ? normalDelay : 100;
    }

    public void Close()
    {
        _closed = true;
        Enabled = false;
        _version++;
    }
}
