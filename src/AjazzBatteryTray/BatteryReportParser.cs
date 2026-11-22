namespace AjazzBatteryTray;

/// <summary>Decodes the AJAZZ receiver's Windows HID status feature report.</summary>
public static class BatteryReportParser
{
    /// <summary>Explain rejection without changing the accepted wire format.</summary>
    public static string DescribeWindowsFeature(ReadOnlySpan<byte> report)
    {
        if (report.Length < 4) return "short buffer";
        if (report[0] != 0x05) return "unexpected report ID";
        if (report[1] != 0 || report[2] != 0) return "unexpected status prefix";
        if (report[3] == 0) return "zero battery field; link/format unknown";
        if (report[3] > 100) return "battery field out of range";
        return "accepted by existing parser";
    }

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
