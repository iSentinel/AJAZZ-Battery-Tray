using System.Globalization;

namespace AjazzBatteryTray;

/// <summary>Validates and formats the existing local battery history CSV.</summary>
public static class BatteryHistoryCsv
{
    public const string Header = "utc_timestamp,percent,state";

    /// <summary>Write one normalized UTC observation without new fields.</summary>
    public static string Format(BatterySample sample)
        => $"{sample.Timestamp.ToUniversalTime():O}," +
           $"{sample.Percent?.ToString(CultureInfo.InvariantCulture) ?? ""}," +
           sample.State;

    /// <summary>Skip incomplete, inconsistent and malformed CSV rows.</summary>
    public static BatterySample? Parse(string row)
    {
        string[] parts = row.Split(',');
        if (parts.Length != 3 ||
            !DateTimeOffset.TryParse(parts[0], CultureInfo.InvariantCulture,
                DateTimeStyles.RoundtripKind, out DateTimeOffset timestamp))
            return null;

        int? percent = ParsePercent(parts[1]);
        if (parts[1].Length > 0 && !percent.HasValue) return null;
        if (parts[2] == "online" && percent.HasValue)
            return new BatterySample(timestamp.ToUniversalTime(), percent, "online");

        if (percent.HasValue ||
            parts[2] is not ("unavailable" or "disconnected"))
            return null;

        return new BatterySample(timestamp.ToUniversalTime(), null, parts[2]);
    }

    private static int? ParsePercent(string text)
    {
        if (text.Length == 0) return null;
        if (!int.TryParse(text, NumberStyles.None,
                CultureInfo.InvariantCulture, out int value)) return null;
        return value is >= 0 and <= 100 ? value : null;
    }
}
