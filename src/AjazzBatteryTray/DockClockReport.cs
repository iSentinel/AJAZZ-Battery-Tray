namespace AjazzBatteryTray;

/// <summary>Builds the documented 0x28 HID feature report for a dock clock.</summary>
public static class DockClockReport
{
    /// <summary>Encodes the computer's local time; byte 0 is Windows HID report ID.</summary>
    public static byte[] Create(DateTime localTime, int length = 65)
    {
        if (length is < 65 or > 256)
        {
            throw new ArgumentOutOfRangeException(nameof(length));
        }

        byte[] report = new byte[length];
        report[1] = 0x28;
        report[8] = 0xD7;
        report[9] = (byte)(localTime.Year >> 8);
        report[10] = (byte)localTime.Year;
        report[11] = (byte)localTime.Month;
        report[12] = (byte)localTime.Day;
        report[13] = (byte)localTime.Hour;
        report[14] = (byte)localTime.Minute;
        report[15] = (byte)localTime.Second;
        return report;
    }
}
