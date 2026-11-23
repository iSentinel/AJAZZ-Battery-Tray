using System.Text.RegularExpressions;

namespace AjazzBatteryTray;

/// <summary>Extract only public USB descriptor identifiers, never instance IDs.</summary>
public static class DiagnosticHidIdentity
{
    private static readonly Regex Pattern = new(
        @"(?:^|#|\\)VID_([0-9A-F]{4})&PID_([0-9A-F]{4})(?=&|#|$)(?:&MI_([0-9A-F]{2})(?=&|#|$))?(?:&COL([0-9A-F]{2})(?=&|#|$))?",
        RegexOptions.IgnoreCase | RegexOptions.CultureInvariant,
        TimeSpan.FromMilliseconds(100));

    public static string? FromPath(string? path)
    {
        if (string.IsNullOrEmpty(path)) return null;
        Match match = Pattern.Match(path);
        if (!match.Success) return null;
        string vid = match.Groups[1].Value.ToUpperInvariant();
        string pid = match.Groups[2].Value.ToUpperInvariant();
        if (vid != "3151" &&
            !(vid == "05AC" && pid == "024F") &&
            !(vid == "0C45" && pid is "800A" or "FEFE"))
            return null;
        string mi = match.Groups[3].Success
            ? match.Groups[3].Value.ToUpperInvariant() : "--";
        string col = match.Groups[4].Success
            ? match.Groups[4].Value.ToUpperInvariant() : "--";
        return $"{vid}:{pid} MI_{mi} COL{col}";
    }

    /// <summary>Prefix-only diagnostic; redacts all remaining vendor bytes.</summary>
    public static string SafeFeaturePreview(ReadOnlySpan<byte> report)
    {
        int shown = Math.Min(8, report.Length);
        return $"{Convert.ToHexString(report[..shown])} " +
            $"({report.Length - shown} additional bytes redacted)";
    }

    /// <summary>Known AJAZZ battery status header only; never export payloads.</summary>
    public static string BatteryHeader(ReadOnlySpan<byte> report)
        => Convert.ToHexString(report[..Math.Min(4, report.Length)]);
}
