using System.Text.Json;

namespace AjazzBatteryTray;

public enum LocalBatterySource { ApexReceiver, AulaReceiver, Bluetooth }

/// <summary>Privacy-filtered session snapshot; no device names, paths or stable identifiers.</summary>
public sealed record LocalBatterySnapshot(int SchemaVersion, DateTimeOffset GeneratedAt,
    IReadOnlyList<LocalBatterySnapshot.Entry> Devices)
{
    public const int Schema = 1;
    // Random per active API store, absent from one-off copies.
    [System.Text.Json.Serialization.JsonIgnore(Condition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull)]
    public string? SessionEpoch { get; init; }
    public const int MaximumDevices = 64;
    public static readonly TimeSpan MaximumFreshAge = DeviceDashboardState.MaximumFreshAge;
    public static readonly TimeSpan MaximumCachedAge = TimeSpan.FromHours(24);

    public sealed record Input(LocalBatterySource Source, int SessionSlot, DeviceDashboardState State);
    public sealed record Entry(string Source, int SessionSlot, string Status,
        int? BatteryPercent, int? LastKnownPercent, DateTimeOffset? MeasuredAt);

    public static LocalBatterySnapshot Create(DateTimeOffset now, IEnumerable<Input> inputs)
    {
        now = now.ToUniversalTime();
        var rows = inputs.Take(MaximumDevices + 1).ToArray();
        if (rows.Length > MaximumDevices ||
            rows.GroupBy(x => (x.Source, x.SessionSlot)).Any(x => x.Count() != 1))
            throw new InvalidDataException("Invalid snapshot device set.");
        return new(Schema, now, Array.AsReadOnly(rows
            .OrderBy(x => x.Source).ThenBy(x => x.SessionSlot)
            .Select(x => Project(x, now)).ToArray()));
    }

    private static Entry Project(Input input, DateTimeOffset now)
    {
        if (input.SessionSlot is < 1 or > MaximumDevices)
            throw new InvalidDataException("Invalid session slot.");
        string source = input.Source switch
        {
            LocalBatterySource.ApexReceiver => "apex_receiver",
            LocalBatterySource.AulaReceiver => "aula_receiver",
            LocalBatterySource.Bluetooth => "bluetooth",
            _ => throw new InvalidDataException("Invalid source.")
        };
        var state = input.State;
        string status = StatusName(state.Status);
        bool sampled = state.Status is DeviceDashboardStatus.Fresh or
            DeviceDashboardStatus.Cached or DeviceDashboardStatus.Scheduled;
        if (!sampled)
            return new(source, input.SessionSlot, status, null, null, null);
        if (state.Percent is not (>= 0 and <= 100) || state.MeasuredAt is not { } measured ||
            !WithinRetention(status, measured, now))
            return new(source, input.SessionSlot, "unavailable", null, null, null);
        measured = measured.ToUniversalTime();
        bool fresh = state.Status == DeviceDashboardStatus.Fresh &&
            now - measured <= MaximumFreshAge;
        if (fresh)
            return new(source, input.SessionSlot, "fresh", state.Percent, null, measured);
        return new(source, input.SessionSlot, state.Status == DeviceDashboardStatus.Fresh ?
            "stale" : status, null, state.Percent, measured);
    }

    /// <summary>Keep scheduled observations bounded even without another publication.</summary>
    internal static bool WithinRetention(string status, DateTimeOffset measured, DateTimeOffset now)
        => measured <= now && now - measured <= (status == "scheduled"
            ? DeviceDashboardState.MaximumScheduledAge : MaximumCachedAge);

    private static string StatusName(DeviceDashboardStatus status) => status switch
    {
        DeviceDashboardStatus.NotChecked => "not_checked",
        DeviceDashboardStatus.Disabled => "disabled",
        DeviceDashboardStatus.Standby => "standby",
        DeviceDashboardStatus.PresenceUnknown => "presence_unknown",
        DeviceDashboardStatus.Disconnected => "disconnected",
        DeviceDashboardStatus.NoReply => "no_reply",
        DeviceDashboardStatus.Fresh => "fresh",
        DeviceDashboardStatus.ManualReading => "manual_only",
        DeviceDashboardStatus.Cached => "cached",
        DeviceDashboardStatus.Scheduled => "scheduled",
        _ => throw new InvalidDataException("Invalid status.")
    };

    public byte[] Export() => JsonSerializer.SerializeToUtf8Bytes(this,
        new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase });
}
