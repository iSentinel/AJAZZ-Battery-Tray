namespace AjazzBatteryTray;

/// <summary>Decodes the AJAZZ receiver's Windows HID status feature report.</summary>
public static class BatteryReportParser
{
    /// <summary>
    /// Returns null for a sleeping mouse, malformed data or an unrecognized report.
    /// The receiver sends report ID 0x05, two zero bytes, then a percent (1..100).
    /// </summary>
    public static int? ParseWindowsFeature(ReadOnlySpan<byte> report)
    {
        if (report.Length < 4 || report[0] != 0x05)
        {
            return null;
        }

        if (report[1] != 0 || report[2] != 0)
        {
            return null;
        }

        int percent = report[3];
        return percent is >= 1 and <= 100 ? percent : null;
    }
}
