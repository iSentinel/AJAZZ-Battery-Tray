namespace AjazzBatteryTray;

/// <summary>Explicit API-activation binding; never infer durable HA entity identity.</summary>
public sealed record HaSessionMapping(string SessionEpoch, string Source, int SessionSlot)
{
    public sealed record Reading(bool Available, int? BatteryPercent, string Status);

    /// <summary>Select a specific row only after an external user confirmation.</summary>
    public static HaSessionMapping Bind(LocalBatterySnapshot snapshot, string source, int slot)
    {
        if (snapshot.SchemaVersion != LocalBatterySnapshot.Schema ||
            !ValidEpoch(snapshot.SessionEpoch) || !ValidSource(source) ||
            !ValidSlot(source, slot) ||
            snapshot.Devices.Count(x => x.Source == source && x.SessionSlot == slot) != 1)
            throw new InvalidDataException("No valid session mapping.");
        return new(snapshot.SessionEpoch!, source, slot);
    }

    public Reading Read(LocalBatterySnapshot? snapshot, DateTimeOffset now)
    {
        if (snapshot is null) return new(false, null, "no_snapshot");
        if (snapshot.SchemaVersion != LocalBatterySnapshot.Schema ||
            !ValidEpoch(SessionEpoch) || snapshot.SessionEpoch != SessionEpoch)
            return new(false, null, "mapping_required");
        if (snapshot.GeneratedAt > now ||
            now - snapshot.GeneratedAt > LocalBatterySnapshot.MaximumFreshAge)
            return new(false, null, "stale_snapshot");
        if (!ValidSource(Source) || !ValidSlot(Source, SessionSlot))
            return new(false, null, "mapping_required");
        var rows = snapshot.Devices.Where(x => x.Source == Source &&
            x.SessionSlot == SessionSlot).Take(2).ToArray();
        if (rows.Length != 1) return new(false, null, "mapping_unavailable");
        var row = rows[0];
        return row.Status == "fresh" && row.BatteryPercent is >= 0 and <= 100 &&
            row.MeasuredAt is { } measured && measured <= now && measured <= snapshot.GeneratedAt &&
            now - measured <= LocalBatterySnapshot.MaximumFreshAge
            ? new(true, row.BatteryPercent, "fresh")
            : new(false, null, "reading_unavailable");
    }

    private static bool ValidEpoch(string? value) =>
        value is { Length: 32 } && value.All(char.IsAsciiHexDigit);

    private static bool ValidSlot(string source, int slot) =>
        slot is >= 1 and <= LocalBatterySnapshot.MaximumDevices &&
        (source != "aula_receiver" || slot != 1);

    private static bool ValidSource(string value) =>
        value is "apex_receiver" or "aula_receiver" or "bluetooth";
}
