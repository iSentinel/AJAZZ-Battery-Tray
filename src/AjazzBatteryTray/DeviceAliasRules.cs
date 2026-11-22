namespace AjazzBatteryTray;

/// <summary>Local display names only; not device identity or Windows PnP names.</summary>
public static class DeviceAliasRules
{
    public const string AulaSlot = "AULA-L99";
    public const int MaxLength = 40;

    public static bool ValidKey(string? key)
        => key == AulaSlot || (key is { Length: 64 } &&
            key.All(c => c is >= '0' and <= '9' or >= 'A' and <= 'F'));

    public static bool TryNormalize(string? input, out string alias)
    {
        alias = (input ?? "").Trim();
        return alias.Length <= MaxLength && !alias.Any(c =>
            char.IsControl(c) || char.GetUnicodeCategory(c) ==
                System.Globalization.UnicodeCategory.Format);
    }

    public static Dictionary<string, string> Clean(Dictionary<string, string>? values)
    {
        Dictionary<string, string> clean = new(StringComparer.Ordinal);
        if (values is null) return clean;
        foreach (var pair in values)
            if (ValidKey(pair.Key) && TryNormalize(pair.Value, out string alias) &&
                alias.Length > 0)
                clean[pair.Key] = alias;
        return clean;
    }

    public static string DisplayName(string fallback, string? alias)
        => TryNormalize(alias, out string clean) && clean.Length != 0
            ? $"{clean} — {fallback}" : fallback;
}
