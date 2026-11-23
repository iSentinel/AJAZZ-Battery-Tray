namespace AjazzBatteryTray;

/// <summary>Session-local receiver ordinals; no hardware identifiers are exported.</summary>
public sealed class SnapshotSessionSlots
{
    private readonly Dictionary<string, int> _apex = new(StringComparer.Ordinal);
    private string? _aulaIdentity;
    private int _aulaSlot = 1;
    private int _nextAulaSlot = 1;

    public int Apex(string identity)
    {
        if (_apex.TryGetValue(identity, out int existing)) return existing;
        if (_apex.Count >= LocalBatterySnapshot.MaximumDevices)
            throw new InvalidDataException("Snapshot slot limit exceeded.");
        int slot = _apex.Count + 1;
        _apex.Add(identity, slot);
        return slot;
    }

    /// <summary>Slot 1 is a non-bindable status placeholder; never reuse a retired slot.</summary>
    public int Aula(string? identity)
    {
        if (string.IsNullOrEmpty(identity))
        {
            _aulaIdentity = null;
            _aulaSlot = 1;
            return _aulaSlot;
        }
        if (StringComparer.Ordinal.Equals(_aulaIdentity, identity)) return _aulaSlot;
        if (_nextAulaSlot >= LocalBatterySnapshot.MaximumDevices)
            throw new InvalidDataException("AULA snapshot slot limit exceeded.");
        _aulaIdentity = identity;
        _aulaSlot = ++_nextAulaSlot;
        return _aulaSlot;
    }
}
