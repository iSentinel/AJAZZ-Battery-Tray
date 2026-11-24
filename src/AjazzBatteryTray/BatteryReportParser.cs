namespace AjazzBatteryTray;

/// <summary>Decodes the AJAZZ receiver's Windows HID status feature report.</summary>
public static class BatteryReportParser
{
    /// <summary>
    /// Recognize the shared GearHub F7 mouse status after the HID report ID.
    /// The response includes read/online flags and a mouse/keyboard slot.
    /// </summary>
    private static bool IsSharedF7Status(ReadOnlySpan<byte> report)
        => report.Length >= 10 && report[0] == 0x05 &&
            report[7] is 1 or 2 or 3;

    /// <summary>Only expose a mouse battery after all status gates pass.</summary>
    private static int? ParseSharedF7Mouse(ReadOnlySpan<byte> report)
    {
        if (report[7] == 1 || report[4] > 1 || report[1] != 1 || report[5] != 0 ||
            report[6] != 1 || report[9] != 0)
            return null;
        return report[3] is >= 1 and <= 100 ? report[3] : null;
    }

    /// <summary>Explain F7 rejection using visible flags, not a guessed level.</summary>
    private static string DescribeSharedF7Mouse(ReadOnlySpan<byte> report)
    {
        if (report[7] == 1) return "F7 keyboard-only slot; mouse battery unavailable";
        if (report[4] > 1) return "F7 invalid status flag; battery unverified";
        if (report[1] != 1) return "F7 mouse: reading unavailable; battery unverified";
        if (report[5] != 0) return "F7 mouse: offline; battery unverified";
        if (report[6] != 1) return "F7 mouse: cannot send; battery unverified";
        if (report[9] != 0) return "F7 mouse: RF boot active; battery unverified";
        if (report[3] == 0) return "F7 mouse: zero battery field; link/format unknown";
        if (report[3] > 100) return "F7 mouse: battery field out of range";
        return "accepted by gated F7 mouse parser";
    }

    /// <summary>Explain rejection without changing the legacy format.</summary>
    public static string DescribeWindowsFeature(ReadOnlySpan<byte> report)
    {
        if (report.Length < 4) return "short buffer";
        if (report[0] != 0x05) return "unexpected report ID";
        if (IsSharedF7Status(report))
            return DescribeSharedF7Mouse(report);
        if (report[1] != 0 || report[2] != 0) return "unexpected status prefix";
        if (report[3] == 0) return "zero battery field; link/format unknown";
        if (report[3] > 100) return "battery field out of range";
        return "accepted by existing parser";
    }

    /// <summary>
    /// Parse documented shared F7 mouse status or the older short reply.
    /// Reject zero, sleeping, RF boot and unavailable battery states.
    /// </summary>
    public static int? ParseWindowsFeature(ReadOnlySpan<byte> report)
    {
        if (report.Length < 4 || report[0] != 0x05) return null;
        if (IsSharedF7Status(report))
            return ParseSharedF7Mouse(report);
        if (report[1] != 0 || report[2] != 0) return null;
        return report[3] is >= 1 and <= 100 ? report[3] : null;
    }
}
