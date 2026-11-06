namespace AjazzBatteryTray;

/// <summary>Pure rules for a temporary, opt-in Bluetooth tray fallback.</summary>
public sealed class BluetoothAutoPolicy
{
    private static readonly TimeSpan ReadInterval = TimeSpan.FromSeconds(60);
    private static readonly TimeSpan FreshnessLimit = TimeSpan.FromSeconds(120);

    private DateTimeOffset? _lastAttempt;
    private DateTimeOffset? _lastReading;
    private DateTimeOffset? _lastSuccessfulRead;
    private int? _percent;

    public bool Enabled { get; private set; }
    public int ConsecutiveFailures { get; private set; }
    public DateTimeOffset? LastSuccessfulRead => _lastSuccessfulRead;
    public DateTimeOffset? LastAttempt => _lastAttempt;

    /// <summary>Reject replies from a device selection that has changed.</summary>
    public int Generation { get; private set; }

    /// <summary>Start only after a manual, valid, direct GATT battery read.</summary>
    public void Enable(int percent, DateTimeOffset now)
    {
        if (percent is < 0 or > 100)
            throw new ArgumentOutOfRangeException(nameof(percent));
        Generation++;
        Enabled = true;
        _percent = percent;
        _lastReading = now;
        _lastSuccessfulRead = now;
        ConsecutiveFailures = 0;
        _lastAttempt = now;
    }

    public void Disable()
    {
        Generation++;
        Enabled = false;
        _percent = null;
        _lastReading = null;
        _lastSuccessfulRead = null;
        ConsecutiveFailures = 0;
        _lastAttempt = null;
    }

    /// <summary>No automatic BLE requests while the USB receiver is present.</summary>
    public bool ShouldRead(bool receiverPresent, DateTimeOffset now)
        => Enabled && !receiverPresent &&
           (!_lastAttempt.HasValue ||
            now < _lastAttempt.Value ||
            now - _lastAttempt.Value >= ReadInterval);

    /// <summary>Save a direct GATT result or invalidate stale/failed data.</summary>
    public void RecordRead(BluetoothBatteryResult result, DateTimeOffset now)
    {
        if (!Enabled) return;
        _lastAttempt = now;
        if (Enabled && result.IsFreshGatt)
        {
            _percent = result.Percent;
            _lastReading = now;
            _lastSuccessfulRead = now;
            ConsecutiveFailures = 0;
        }
        else
        {
            _percent = null;
            _lastReading = null;
            ConsecutiveFailures++;
        }
    }

    /// <summary>Display a recent BLE percentage only without a USB receiver.</summary>
    public int? VisiblePercent(bool receiverPresent, DateTimeOffset now)
    {
        if (!Enabled || receiverPresent || !_lastReading.HasValue ||
            now < _lastReading.Value || now - _lastReading.Value > FreshnessLimit)
            return null;
        return _percent;
    }

    /// <summary>Human-readable status without device identifiers.</summary>
    public string StatusText(bool receiverPresent, bool polling, DateTimeOffset now)
    {
        if (!Enabled) return "Bluetooth fallback: off";
        if (receiverPresent) return "Bluetooth fallback: standby (USB primary)";
        if (polling) return "Bluetooth fallback: checking battery...";

        int? percent = VisiblePercent(false, now);
        if (percent.HasValue)
            return $"Bluetooth fallback: {percent}% (fresh GATT)";

        string last = LastSuccessfulRead?.ToLocalTime().ToString("HH:mm:ss")
            ?? "never";
        return $"Bluetooth fallback: unavailable ({ConsecutiveFailures} failed; " +
            $"last good {last})";
    }

}
