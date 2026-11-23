namespace AjazzBatteryTray;

/// <summary>Offline MQTT 5 message description; no network or broker calls.</summary>
public sealed record HaMqttMessage(string TopicSuffix, string Payload,
    bool Retain, int Qos, int? ExpirySeconds);

/// <summary>Only a session-bound fresh reading may mark a sensor online.</summary>
public static class HaMqttAvailabilityPolicy
{
    public const int FreshExpirySeconds = 300;

    /// <summary>Plan ordered retained messages for a future opt-in transport.</summary>
    private static int RemainingSeconds(HaSessionMapping mapping,
        LocalBatterySnapshot? snapshot, DateTimeOffset now)
    {
        if (snapshot is null) return 0;
        DateTimeOffset? measured = snapshot.Devices.FirstOrDefault(x =>
            x.Source == mapping.Source && x.SessionSlot == mapping.SessionSlot)?.MeasuredAt;
        if (measured is null) return 0;
        double sample = (LocalBatterySnapshot.MaximumFreshAge -
            (now - measured.Value)).TotalSeconds;
        double generation = (LocalBatterySnapshot.MaximumFreshAge -
            (now - snapshot.GeneratedAt)).TotalSeconds;
        return (int)Math.Clamp(Math.Floor(Math.Min(sample, generation)),
            0, FreshExpirySeconds);
    }

    public static IReadOnlyList<HaMqttMessage> Plan(
        HaSessionMapping mapping, LocalBatterySnapshot? snapshot, DateTimeOffset now)
    {
        var reading = mapping.Read(snapshot, now);
        int expiry = RemainingSeconds(mapping, snapshot, now);
        if (reading is { Available: true, BatteryPercent: int percent } &&
            percent is >= 0 and <= 100 && expiry > 0)
        {
            return new[]
            {
                // Publish the value before changing availability to online.
                new HaMqttMessage("battery", percent.ToString(
                    System.Globalization.CultureInfo.InvariantCulture),
                    true, 1, expiry),
                new HaMqttMessage("availability", "online", true, 1,
                    expiry)
            };
        }

        return new[]
        {
            // Offline first; the empty retained message clears any old value.
            new HaMqttMessage("availability", "offline", true, 1, null),
            new HaMqttMessage("battery", "", true, 1, null)
        };
    }
}
