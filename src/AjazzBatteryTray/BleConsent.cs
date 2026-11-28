using System.Security.Cryptography;
using System.Text;

namespace AjazzBatteryTray;

/// <summary>Local endpoint consent only; not an association with a USB device.</summary>
public static class BleConsent
{
    public const int MaximumDevices = 32;

    public static string Key(string deviceId) => Convert.ToHexString(
        SHA256.HashData(Encoding.UTF8.GetBytes("BLE-CONSENT:" + deviceId.ToUpperInvariant())));

    public static bool Valid(string? value) => value is { Length: 64 } &&
        value.All(c => c is >= '0' and <= '9' or >= 'A' and <= 'F');

    public static HashSet<string> Clean(IEnumerable<string>? values)
        => new((values ?? Array.Empty<string>()).Where(Valid)
            .Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal)
            .Take(MaximumDevices), StringComparer.Ordinal);
}
