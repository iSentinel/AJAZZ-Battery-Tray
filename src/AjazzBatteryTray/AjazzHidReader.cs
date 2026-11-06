using Microsoft.Win32.SafeHandles;

namespace AjazzBatteryTray;

/// <summary>Queries the shared AJAZZ APEX 8K receiver vendor collection.</summary>
public sealed class AjazzHidReader
{
    /// <summary>PresenceKnown is false when Windows could not enumerate USB.</summary>
    public sealed record Reading(bool ReceiverPresent, int? Percent,
        string Details, bool PresenceKnown = true);

    public Reading Read()
    {
        try
        {
            IReadOnlyList<string> paths = HidNative.FindAjazzPaths();
            foreach (string path in paths)
            {
                Reading? reading = QueryPath(path);
                if (reading?.Percent is not null)
                {
                    return reading;
                }
            }

            return paths.Count > 0
                ? new Reading(true, null, "Receiver found; mouse may be asleep")
                : new Reading(false, null, "Receiver not found");
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "HID read failed", error);
            return new Reading(false, null, "HID read error; see log",
                PresenceKnown: false);
        }
    }

    /// <summary>Sends only the documented dock RTC command to the matching HID collection.</summary>
    public bool TrySyncDockClock(DateTime localTime)
    {
        try
        {
            foreach (string path in HidNative.FindAjazzPaths())
            {
                using SafeFileHandle handle = HidNative.Open(path);
                if (handle.IsInvalid || !HidNative.TryGetCaps(handle, out var caps))
                {
                    continue;
                }

                if (caps.UsagePage != 0xFFFF || caps.Usage != 0x02 ||
                    caps.FeatureReportByteLength is < 65 or > 256)
                {
                    continue;
                }

                byte[] frame = DockClockReport.Create(
                    localTime, caps.FeatureReportByteLength);
                if (HidNative.SendApprovedFeature(handle, frame))
                {
                    return true;
                }
            }
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "Dock clock HID transfer failed", error);
        }

        return false;
    }

    private static Reading? QueryPath(string path)
    {
        using SafeFileHandle handle = HidNative.Open(path);
        if (handle.IsInvalid || !HidNative.TryGetCaps(handle, out var caps))
        {
            return null;
        }

        // Never probe other usage pages or collections.
        if (caps.UsagePage != 0xFFFF || caps.Usage != 0x02)
        {
            return null;
        }

        int[] lengths = { caps.FeatureReportByteLength, 65, 67 };
        foreach (int length in lengths.Distinct())
        {
            if (length is < 65 or > 256)
            {
                continue;
            }

            int? percent = PollBattery(handle, length);
            if (percent.HasValue)
            {
                return new Reading(true, percent, "2.4 GHz / 8K");
            }
        }

        return new Reading(true, null, "No valid battery status report");
    }

    private static int? PollBattery(SafeFileHandle handle, int length)
    {
        // 00 F7 00... is the receiver's documented zero-payload status poll.
        byte[] poll = new byte[length];
        poll[1] = 0xF7;
        if (!HidNative.SendApprovedFeature(handle, poll))
        {
            return null;
        }

        Thread.Sleep(30);
        byte[] response = new byte[length];
        response[0] = 0x05;
        return HidNative.HidD_GetFeature(handle, response, length)
            ? BatteryReportParser.ParseWindowsFeature(response) : null;
    }
}
