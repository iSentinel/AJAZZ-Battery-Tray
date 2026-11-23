using System.Text.Json;

namespace AjazzBatteryTray;

/// <summary>Validate the local wire format in the optional consumer, not the tray.</summary>
public static class HaSnapshotDecoder
{
    public const int MaximumBytes = 64 * 1024;

    public static LocalBatterySnapshot Decode(ReadOnlyMemory<byte> json)
    {
        if (json.Length == 0 || json.Length > MaximumBytes)
            throw new InvalidDataException("Invalid snapshot length.");
        try
        {
            using var doc = JsonDocument.Parse(json, new JsonDocumentOptions { MaxDepth = 8 });
            var root = Fields(doc.RootElement);
            if (root["schemaVersion"].GetInt32() != LocalBatterySnapshot.Schema)
                throw new InvalidDataException("Unsupported snapshot schema.");
            string? epoch = root["sessionEpoch"].GetString();
            if (epoch is not { Length: 32 } || !epoch.All(char.IsAsciiHexDigit))
                throw new InvalidDataException("Invalid session epoch.");
            var generated = Utc(root["generatedAt"]);
            var devices = root["devices"];
            if (devices.ValueKind != JsonValueKind.Array ||
                devices.GetArrayLength() > LocalBatterySnapshot.MaximumDevices)
                throw new InvalidDataException("Invalid device array.");
            var rows = new List<LocalBatterySnapshot.Entry>();
            var identities = new HashSet<(string, int)>();
            foreach (var item in devices.EnumerateArray())
            {
                var row = DecodeRow(item, generated);
                if (!identities.Add((row.Source, row.SessionSlot)))
                    throw new InvalidDataException("Duplicate session slot.");
                rows.Add(row);
            }
            return new(LocalBatterySnapshot.Schema, generated, rows.AsReadOnly())
                { SessionEpoch = epoch };
        }
        catch (Exception error) when (error is JsonException or InvalidOperationException
            or KeyNotFoundException or FormatException or OverflowException)
        {
            throw new InvalidDataException("Malformed snapshot.", error);
        }
    }

    private static LocalBatterySnapshot.Entry DecodeRow(JsonElement item, DateTimeOffset generated)
    {
        var fields = Fields(item);
        string source = fields["source"].GetString() ?? "";
        int slot = fields["sessionSlot"].GetInt32();
        string status = fields["status"].GetString() ?? "";
        int? battery = Percent(fields["batteryPercent"]);
        int? cached = Percent(fields["lastKnownPercent"]);
        var value = fields["measuredAt"];
        DateTimeOffset? measured = value.ValueKind == JsonValueKind.Null ? null : Utc(value);
        if (source is not ("apex_receiver" or "aula_receiver" or "bluetooth") ||
            slot is < 1 or > LocalBatterySnapshot.MaximumDevices ||
            measured > generated)
            throw new InvalidDataException("Invalid device identity or measurement time.");
        bool valid = status switch
        {
            "fresh" => battery.HasValue && !cached.HasValue && measured.HasValue,
            "cached" or "scheduled" or "stale" =>
                !battery.HasValue && cached.HasValue && measured.HasValue,
            "not_checked" or "disabled" or "standby" or "presence_unknown" or
            "disconnected" or "no_reply" or "manual_only" or "unavailable" =>
                !battery.HasValue && !cached.HasValue && !measured.HasValue,
            _ => false
        };
        if (!valid) throw new InvalidDataException("Contradictory device state.");
        return new(source, slot, status, battery, cached, measured);
    }

    private static Dictionary<string, JsonElement> Fields(JsonElement element)
    {
        if (element.ValueKind != JsonValueKind.Object)
            throw new InvalidDataException("Expected an object.");
        var fields = new Dictionary<string, JsonElement>(StringComparer.Ordinal);
        foreach (var field in element.EnumerateObject())
            if (!fields.TryAdd(field.Name, field.Value))
                throw new InvalidDataException("Duplicate JSON property.");
        return fields;
    }

    private static int? Percent(JsonElement value)
    {
        if (value.ValueKind == JsonValueKind.Null) return null;
        int percent = value.GetInt32();
        if (percent is < 0 or > 100) throw new InvalidDataException("Invalid percent.");
        return percent;
    }

    private static DateTimeOffset Utc(JsonElement value)
    {
        var result = value.GetDateTimeOffset();
        string? raw = value.GetString();
        if (result.Offset != TimeSpan.Zero || raw is null ||
            !(raw.EndsWith("Z", StringComparison.Ordinal) ||
              raw.EndsWith("+00:00", StringComparison.Ordinal)))
            throw new InvalidDataException("Expected explicit UTC timestamp.");
        return result;
    }
}
