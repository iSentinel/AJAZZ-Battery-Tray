namespace AjazzBatteryTray;

/// <summary>Publish sanitized immutable snapshots on the UI thread; read without HID access.</summary>
public sealed class LocalSnapshotStore
{
    private LocalBatterySnapshot? _latest;

    public void Publish(DateTimeOffset now, IEnumerable<LocalBatterySnapshot.Input> inputs)
    {
        try
        {
            var snapshot = LocalBatterySnapshot.Create(now, inputs);
            Volatile.Write(ref _latest, snapshot);
        }
        catch
        {
            Clear();
            throw;
        }
    }

    public void Clear() => Volatile.Write(ref _latest, null);

    /// <summary>Re-evaluate freshness at read time without extending measurement timestamps.</summary>
    public LocalBatterySnapshot? Read(DateTimeOffset now)
    {
        var snapshot = Volatile.Read(ref _latest);
        if (snapshot is null || now < snapshot.GeneratedAt) return null;
        var entries = snapshot.Devices.Select(entry => Age(entry, now)).ToArray();
        return snapshot with { Devices = Array.AsReadOnly(entries) };
    }

    private static LocalBatterySnapshot.Entry Age(LocalBatterySnapshot.Entry entry, DateTimeOffset now)
    {
        if (entry.MeasuredAt is not { } measured) return entry;
        if (measured > now || now - measured > LocalBatterySnapshot.MaximumCachedAge)
            return entry with { Status = "unavailable", BatteryPercent = null,
                LastKnownPercent = null, MeasuredAt = null };
        if (entry.BatteryPercent.HasValue && now - measured > LocalBatterySnapshot.MaximumFreshAge)
            return entry with { Status = "stale", LastKnownPercent = entry.BatteryPercent,
                BatteryPercent = null };
        return entry;
    }
}
