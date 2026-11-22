namespace AjazzBatteryTray;

/// <summary>Local icon palette. Warning and unavailable colors always take priority.</summary>
public static class TrayColorRules
{
    public const string Default = "green";
    public const int Gray = 0x6E7682;
    public const int Red = 0xDC3545;
    public const int Amber = 0xE19112;

    public static IReadOnlyList<string> Choices { get; } =
        Array.AsReadOnly(new[] { "green", "blue", "purple", "teal", "pink", "slate" });

    public static string Normalize(string? value)
        => value is not null && Choices.Contains(value, StringComparer.Ordinal)
            ? value : Default;

    public static Dictionary<string, string> Clean(Dictionary<string, string>? values)
    {
        Dictionary<string, string> result = new(StringComparer.Ordinal);
        if (values is null) return result;
        foreach (var pair in values)
        {
            string color = Normalize(pair.Value);
            if (DeviceAliasRules.ValidKey(pair.Key) && color != Default)
                result[pair.Key] = color;
        }
        return result;
    }

    public static int Resolve(int? level, bool connected, bool stale, string? color)
    {
        if (!connected || stale || level is null or < 0 or > 100) return Gray;
        if (level <= 10) return Red;
        if (level <= 20) return Amber;
        return Normalize(color) switch
        {
            "blue" => 0x2464C7,
            "purple" => 0x7844B3,
            "teal" => 0x087E8B,
            "pink" => 0xB83280,
            "slate" => 0x465B78,
            _ => 0x1B9767
        };
    }
}
