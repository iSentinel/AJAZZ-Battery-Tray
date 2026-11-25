namespace AjazzBatteryTray;

/// <summary>Existing F7 policy classification, not a hardware power-state claim.</summary>
public enum F7MouseGate
{
    KeyboardOnly, InvalidStatus, ReadUnavailable, Offline, CannotSend,
    RadioBoot, ZeroField, OutOfRange, Accepted
}

/// <summary>Separate the reported mouse field from eligibility for telemetry.</summary>
public readonly record struct F7MouseObservation(F7MouseGate Gate, int? ReportedField,
    int? VerifiedPercent, int? UnverifiedPercent);

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

    /// <summary>Classify existing policy gates in their original diagnostic order.</summary>
    private static F7MouseGate Gate(ReadOnlySpan<byte> report)
    {
        if (report[7] == 1) return F7MouseGate.KeyboardOnly;
        if (report[4] > 1) return F7MouseGate.InvalidStatus;
        if (report[1] != 1) return F7MouseGate.ReadUnavailable;
        if (report[5] != 0) return F7MouseGate.Offline;
        if (report[6] != 1) return F7MouseGate.CannotSend;
        if (report[9] != 0) return F7MouseGate.RadioBoot;
        if (report[3] == 0) return F7MouseGate.ZeroField;
        if (report[3] > 100) return F7MouseGate.OutOfRange;
        return F7MouseGate.Accepted;
    }

    /// <summary>Inspect a recognized numbered F7 reply without inferring freshness.</summary>
    public static F7MouseObservation? ObserveSharedF7(ReadOnlySpan<byte> report)
    {
        if (!IsSharedF7Status(report)) return null;
        var gate = Gate(report);
        int? field = report[7] != 1 && report[3] is >= 1 and <= 100 ? report[3] : null;
        bool provisional = gate == F7MouseGate.ReadUnavailable && report[7] == 2 &&
            report[1] == 0 && report[5] == 0 && report[6] == 1 && report[9] == 0;
        return new(gate, field, gate == F7MouseGate.Accepted ? field : null,
            provisional ? field : null);
    }

    /// <summary>Keep established diagnostic text stable for report consumers.</summary>
    private static string DescribeSharedF7Mouse(F7MouseGate gate) => gate switch
    {
        F7MouseGate.KeyboardOnly => "F7 keyboard-only slot; mouse battery unavailable",
        F7MouseGate.InvalidStatus => "F7 invalid status flag; battery unverified",
        F7MouseGate.ReadUnavailable => "F7 mouse: reading unavailable; battery unverified",
        F7MouseGate.Offline => "F7 mouse: offline; battery unverified",
        F7MouseGate.CannotSend => "F7 mouse: cannot send; battery unverified",
        F7MouseGate.RadioBoot => "F7 mouse: RF boot active; battery unverified",
        F7MouseGate.ZeroField => "F7 mouse: zero battery field; link/format unknown",
        F7MouseGate.OutOfRange => "F7 mouse: battery field out of range",
        _ => "accepted by gated F7 mouse parser"
    };

    /// <summary>Display-only observation; never use as validated charge or telemetry.</summary>
    public static int? UnverifiedMouseField(ReadOnlySpan<byte> report)
        => ObserveSharedF7(report)?.UnverifiedPercent;

    public static int? ConsistentUnverifiedField(int? first, int matching, int total)
        => total >= 2 && matching == total ? first : null;

    /// <summary>Stable diagnostic label; never imply a verified measurement.</summary>
    public static string DiagnosticUnverifiedField(int? value, bool sampled = true)
        => "unverified mouse field (not telemetry)=" +
            (sampled && value is >= 1 and <= 100
                ? value.Value.ToString(System.Globalization.CultureInfo.InvariantCulture)
                : "unavailable");

    /// <summary>Explain rejection without changing the legacy format.</summary>
    public static string DescribeWindowsFeature(ReadOnlySpan<byte> report)
    {
        if (report.Length < 4) return "short buffer";
        if (report[0] != 0x05) return "unexpected report ID";
        if (ObserveSharedF7(report) is { } observed)
            return DescribeSharedF7Mouse(observed.Gate);
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
        if (ObserveSharedF7(report) is { } observed)
            return observed.VerifiedPercent;
        if (report[1] != 0 || report[2] != 0) return null;
        return report[3] is >= 1 and <= 100 ? report[3] : null;
    }
}
