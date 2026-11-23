using System.Text.RegularExpressions;

namespace AjazzBatteryTray;

/// <summary>Only known USB families and their primary HID input nodes are candidates.</summary>
public static class PnpNameRules
{
    private static readonly Regex RootPattern = new(
        @"^USB\\VID_(3151)&PID_(5007)\\[^\\]+$|^USB\\VID_(05AC)&PID_(024F)\\[^\\]+$",
        RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);

    private static readonly Regex ChildPattern = new(
        @"^HID\\VID_(3151)&PID_(5007)&MI_00(?:&COL[0-9A-F]{2})?\\[^\\]+$|^HID\\VID_(05AC)&PID_(024F)&MI_00(?:&COL[0-9A-F]{2})?\\[^\\]+$",
        RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);

    public static string? Family(string instance)
    {
        if (instance.Length > 512 ||
            (!RootPattern.IsMatch(instance) && !ChildPattern.IsMatch(instance)))
            return null;
        return instance.StartsWith(@"USB\VID_3151&PID_5007", StringComparison.OrdinalIgnoreCase) ||
               instance.StartsWith(@"HID\VID_3151&PID_5007", StringComparison.OrdinalIgnoreCase)
            ? "3151:5007" : "05AC:024F";
    }

    public static bool IsRoot(string instance) => RootPattern.IsMatch(instance);
    public static bool IsPrimaryHid(string instance) => ChildPattern.IsMatch(instance);

    public static ushort? Revision(string family, IEnumerable<string> hardwareIds)
    {
        if (family is not ("3151:5007" or "05AC:024F")) return null;
        string prefix = family == "3151:5007"
            ? @"USB\VID_3151&PID_5007&REV_" : @"USB\VID_05AC&PID_024F&REV_";
        var revisions = hardwareIds.Where(id => id.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)
            && id.Length == prefix.Length + 4)
            .Select(id => ushort.TryParse(id[prefix.Length..],
                System.Globalization.NumberStyles.AllowHexSpecifier, null, out ushort rev)
                ? (ushort?)rev : null).Where(rev => rev.HasValue).Distinct().ToArray();
        return revisions.Length == 1 ? revisions[0] : null;
    }

    public static string Model(string family, ushort? revision) => (family, revision) switch
    {
        ("3151:5007", 0x0300) => "AJAZZ AJ159 APEX",
        ("3151:5007", 0x0002) => "AJAZZ shared receiver (model unverified)",
        ("05AC:024F", 0x0136) => "AULA L99",
        ("3151:5007", _) => "AJAZZ receiver",
        ("05AC:024F", _) => "AULA candidate receiver",
        _ => "Unknown"
    };
}
