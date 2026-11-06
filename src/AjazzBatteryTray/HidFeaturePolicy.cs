namespace AjazzBatteryTray;

/// <summary>Allow only the two verified AJAZZ 8K telemetry/clock write frames.</summary>
public static class HidFeaturePolicy
{
    /// <summary>Validate a Windows HID report before any SetFeature transfer.</summary>
    public static bool IsApproved(ReadOnlySpan<byte> report)
    {
        if (report.Length is < 65 or > 256 || report[0] != 0) return false;
        return report[1] switch
        {
            0xF7 => IsZero(report[2..]),
            0x28 => IsValidClock(report),
            _ => false
        };
    }

    private static bool IsValidClock(ReadOnlySpan<byte> report)
    {
        if (report[8] != 0xD7 || !IsZero(report.Slice(2, 6)) ||
            !IsZero(report[16..])) return false;
        int year = (report[9] << 8) | report[10];
        int month = report[11];
        int day = report[12];
        int hour = report[13];
        int minute = report[14];
        int second = report[15];

        if (year is < 2020 or > 2099 || month is < 1 or > 12)
            return false;
        return day >= 1 && day <= DateTime.DaysInMonth(year, month) &&
               hour < 24 && minute < 60 && second < 60;
    }

    private static bool IsZero(ReadOnlySpan<byte> data)
    {
        foreach (byte value in data)
            if (value != 0) return false;
        return true;
    }
}
