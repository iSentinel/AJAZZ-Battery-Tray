namespace AjazzBatteryTray;

/// <summary>User-confirmed one-to-one local display association, not protocol identity.</summary>
public static class TransportLinks
{
    public static Dictionary<string, string> Clean(
        Dictionary<string, string>? links, IReadOnlySet<string> consent)
    {
        var result = new Dictionary<string, string>(StringComparer.Ordinal);
        if (links is null) return result;
        var used = new HashSet<string>(StringComparer.Ordinal);
        foreach (var pair in links.OrderBy(x => x.Key, StringComparer.Ordinal))
            if (BleConsent.Valid(pair.Key) && consent.Contains(pair.Key) &&
                BleConsent.Valid(pair.Value) && pair.Key != pair.Value && used.Add(pair.Value))
                result.Add(pair.Key, pair.Value);
        return result;
    }

    public static bool CanLink(IReadOnlyDictionary<string, string> links,
        IReadOnlySet<string> consent, string ble, string usb)
        => BleConsent.Valid(ble) && consent.Contains(ble) && BleConsent.Valid(usb) &&
            ble != usb && !links.ContainsKey(ble) && !links.Values.Contains(usb, StringComparer.Ordinal);

    public sealed record Display(int? Percent, bool Cached, bool Bluetooth);

    /// <summary>Choose a source without treating either transport's raw field as telemetry.</summary>
    public static Display Select(int? usb, int? ble, int? cached, int? scheduledUsb = null)
    {
        if (usb is >= 1 and <= 100) return new(usb, false, false);
        if (ble is >= 0 and <= 100) return new(ble, false, true);
        if (scheduledUsb is >= 1 and <= 100) return new(scheduledUsb, true, false);
        if (cached is >= 0 and <= 100) return new(cached, true, true);
        return new(null, false, false);
    }
}
