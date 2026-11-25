namespace AjazzBatteryTray;

/// <summary>Session-only scheduling for separately opted-in paired BLE devices.
/// Keys are local-only consent fingerprints; never include them in reports.
/// All methods must be called on the same UI thread.</summary>
public sealed class BluetoothMultiSession
{
    public sealed record Request(string Key, long Token);
    private sealed record Slot(long Generation, BluetoothAutoPolicy Policy);
    private readonly Dictionary<string, Slot> _slots = new(StringComparer.Ordinal);
    private long _sequence;
    private Request? _inFlight;
    private long _requestGeneration;
    private bool _requestInvalidated;
    private bool _usbBlocked;
    private readonly bool _independent;

    // The independent policy never infers USB/BLE identity from receiver presence.
    public BluetoothMultiSession(bool independent = false) => _independent = independent;

    private bool Blocked(bool known, bool present) => !_independent && (!known || present);

    public int Count => _slots.Count;
    public bool IsBusy => _inFlight is not null;

    /// <summary>Caller must establish paired LE identity and explicit owner consent.</summary>
    public bool Enable(string key, BluetoothBatteryResult reading, DateTimeOffset now)
    {
        if (string.IsNullOrWhiteSpace(key) || !reading.IsFreshGatt) return false;
        BluetoothAutoPolicy policy = new();
        policy.Enable(reading.Percent!.Value, now);
        if (_usbBlocked) policy.InvalidateForUsb();
        _slots[key] = new Slot(++_sequence, policy);
        return true;
    }

    /// <summary>Restore a previously consented paired endpoint, with no reading.</summary>
    public bool Restore(string key)
    {
        if (string.IsNullOrWhiteSpace(key) || _slots.ContainsKey(key)) return false;
        BluetoothAutoPolicy policy = new();
        policy.EnablePending();
        _slots[key] = new Slot(++_sequence, policy);
        return true;
    }

    public void Disable(string key) => _slots.Remove(key);
    public void DisableAll() => _slots.Clear();

    public DateTimeOffset? LastSuccess(string key)
        => _slots.TryGetValue(key, out Slot? slot) ? slot.Policy.LastSuccessfulRead : null;

    public DateTimeOffset? LastAttempt(string key)
        => _slots.TryGetValue(key, out Slot? slot) ? slot.Policy.LastAttempt : null;

    public void ObserveUsbPresence(bool known, bool present)
    {
        bool blocked = Blocked(known, present);
        if (blocked && !_usbBlocked)
        {
            foreach (Slot slot in _slots.Values) slot.Policy.InvalidateForUsb();
            if (IsBusy) _requestInvalidated = true;
        }
        _usbBlocked = blocked;
    }

    /// <summary>Global USB priority is conservative until physical association is verified.</summary>
    public Request? TryBegin(bool presenceKnown, bool usbPresent, DateTimeOffset now,
        string? forceKey = null)
    {
        if (Blocked(presenceKnown, usbPresent) || IsBusy) return null;
        KeyValuePair<string, Slot>? chosen = null;
        foreach (var pair in _slots)
        {
            bool due = forceKey is null
                ? pair.Value.Policy.ShouldRead(false, now)
                : pair.Key == forceKey && pair.Value.Policy.CanRefreshNow(false);
            if (!due) continue;
            if (chosen is not { } current)
            {
                chosen = pair;
                continue;
            }
            int ageOrder = Nullable.Compare(pair.Value.Policy.LastAttempt,
                current.Value.Policy.LastAttempt);
            if (ageOrder < 0 ||
                (ageOrder == 0 && pair.Value.Generation < current.Value.Generation))
                chosen = pair;
        }
        if (chosen is not { } next) return null;
        _requestInvalidated = false;
        _requestGeneration = next.Value.Generation;
        _inFlight = new Request(next.Key, ++_sequence);
        return _inFlight;
    }

    /// <summary>Release the one active request, but reject replies from removed/reselected slots.</summary>
    public bool Complete(Request request, BluetoothBatteryResult result,
        DateTimeOffset now, bool presenceKnown, bool usbPresent)
    {
        if (_inFlight != request) return false;
        _inFlight = null;
        if (_requestInvalidated || !_slots.TryGetValue(request.Key, out Slot? slot) ||
            slot.Generation != _requestGeneration || Blocked(presenceKnown, usbPresent))
            return false;
        slot.Policy.RecordRead(result, now);
        return true;
    }

    public int? VisiblePercent(string key, bool presenceKnown, bool usbPresent, DateTimeOffset now)
        => !Blocked(presenceKnown, usbPresent) && _slots.TryGetValue(key, out Slot? slot)
            ? slot.Policy.VisiblePercent(false, now) : null;

    public int? Failures(string key)
        => _slots.TryGetValue(key, out Slot? slot) ? slot.Policy.ConsecutiveFailures : null;
}
