namespace AjazzBatteryTray;

/// <summary>Conservative, opt-in L99 2.4 GHz battery protocol rules.</summary>
public static class AulaL99Protocol
{
    public const int ReportLength = 33; // Windows HID report ID + 32-byte body.
    public const byte BatteryCommand = 0x20;

    /// <summary>Filter one known dongle interface; IDs are shared with S75 Pro.</summary>
    public static bool MatchesPath(string? path)
        => path is not null &&
           path.Contains("vid_05ac&pid_024f&mi_03",
               StringComparison.OrdinalIgnoreCase);

    /// <summary>Refuse keyboard collections and unexpected report lengths.</summary>
    public static bool MatchesCaps(int usagePage, int inputLength,
        int outputLength)
        => usagePage >= 0xff00 && inputLength == ReportLength &&
           outputLength == ReportLength;

    /// <summary>Make only the documented battery-status request.</summary>
    public static byte[] BatteryRequest()
    {
        byte[] report = new byte[ReportLength];
        report[1] = BatteryCommand;
        report[2] = 0x01;
        // Body byte 31 is an additive checksum of the previous 31 bytes.
        report[32] = 0x21;
        return report;
    }

    /// <summary>Allow only the battery query, never settings or reset commands.</summary>
    public static bool IsApprovedRequest(ReadOnlySpan<byte> report)
        => report.SequenceEqual(BatteryRequest());

    /// <summary>Accept only a matched battery reply, not sleep or stale traffic.</summary>
    public static int? ParseBatteryReply(ReadOnlySpan<byte> report)
    {
        ReadOnlySpan<byte> body = report.Length switch
        {
            ReportLength when report[0] == 0 => report[1..],
            32 => report,
            _ => ReadOnlySpan<byte>.Empty
        };
        if (body.Length != 32 || body[0] != BatteryCommand ||
            body[1] != 0x01 || body[2] != 0x00)
            return null;

        // Zero is "no reading" in the published L99 dongle implementation.
        int percent = body[3];
        return percent is >= 1 and <= 100 ? percent : null;
    }
}
