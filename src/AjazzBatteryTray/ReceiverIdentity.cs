using System.Security.Cryptography;
using System.Text;

namespace AjazzBatteryTray;

/// <summary>Local-only receiver key; never include it in reports or logs.</summary>
public static class ReceiverIdentity
{
    public static string LocalKey(string path)
        => Convert.ToHexString(SHA256.HashData(
            Encoding.UTF8.GetBytes(path.ToUpperInvariant())));

    /// <summary>Keep the same primary receiver while present, independent of battery replies.</summary>
    public static string? SelectPrimary(string? current, IEnumerable<string> keys)
    {
        string[] present = keys.Distinct(StringComparer.Ordinal)
            .OrderBy(x => x, StringComparer.Ordinal).ToArray();
        return current is not null && present.Contains(current, StringComparer.Ordinal)
            ? current : present.FirstOrDefault();
    }

    /// <summary>Provisional labels based on the owner's observed USB revisions.</summary>
    public static string Label(ushort? revision) => revision switch
    {
        0x0300 => "AJAZZ AJ159 (rev. 0300)",
        0x0002 => "AJAZZ AJ179 (rev. 0002)",
        ushort value => $"AJAZZ (rev. {value:X4})",
        _ => "AJAZZ (unknown revision)"
    };
}
