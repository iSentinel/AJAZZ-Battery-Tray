using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

namespace AjazzBatteryTray;

/// <summary>Queries the shared AJAZZ APEX 8K receiver vendor collection.</summary>
public sealed class AjazzHidReader
{
    /// <summary>PresenceKnown is false when Windows could not enumerate USB.</summary>
    public sealed record Reading(bool ReceiverPresent, int? Percent,
        string Details, bool PresenceKnown = true,
        IReadOnlyList<string>? Attempts = null);

    /// <summary>One receiver, identified locally; never export Key.</summary>
    public sealed record ReceiverReading(string Key, ushort? Revision, Reading Reading);

    public sealed record Batch(Reading Summary, IReadOnlyList<ReceiverReading> Receivers);

    public Batch ReadAll()
    {
        List<string> attempts = new();
        List<ReceiverReading> receivers = new();
        try
        {
            IReadOnlyList<string> paths = HidNative.FindAjazzPaths();
            attempts.Add($"Matching MI_02 paths: {paths.Count}");
            foreach (string path in paths.Distinct(StringComparer.OrdinalIgnoreCase))
            {
                List<string> trace = new();
                Reading? reading = QueryPath(path, trace, out ushort? revision);
                if (reading is not null)
                {
                    receivers.Add(new ReceiverReading(ReceiverIdentity.LocalKey(path),
                        revision, reading with { Attempts = trace.ToArray() }));
                }
                attempts.AddRange(trace);
            }

            Reading summary = receivers.FirstOrDefault(x => x.Reading.Percent.HasValue)?.Reading
                ?? new Reading(paths.Count > 0, null, paths.Count > 0
                    ? "Receiver found; mouse may be asleep" : "Receiver not found");
            return new Batch(summary with { Attempts = attempts.ToArray() }, receivers);
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "HID read failed: " + error.GetType().Name);
            attempts.Add("Poll exception: " + error.GetType().Name);
            return new Batch(new Reading(false, null, "HID read error; see log",
                PresenceKnown: false, Attempts: attempts.ToArray()), Array.Empty<ReceiverReading>());
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

    private static Reading? QueryPath(string path, List<string> attempts, out ushort? revision)
    {
        revision = null;
        attempts.Add($"Interface: {DiagnosticHidIdentity.FromPath(path)}");
        using SafeFileHandle handle = HidNative.Open(path);
        if (handle.IsInvalid)
        {
            attempts.Add($"  Open failed: Win32 {Marshal.GetLastWin32Error()}");
            return null;
        }
        if (!HidNative.TryGetCaps(handle, out var caps))
        {
            attempts.Add("  HID capabilities unavailable");
            return null;
        }

        if (caps.UsagePage != 0xFFFF || caps.Usage != 0x02)
        {
            attempts.Add($"  Skipped collection: {caps.UsagePage:X4}:{caps.Usage:X4}");
            return null;
        }

        var attributes = HidNative.GetAttributes(handle);
        revision = attributes?.VersionNumber;
        attempts.Add($"  USB revision: {(revision.HasValue ? $"0x{revision:X4}" : "unknown")}");
        attempts.Add($"  Feature report size: {caps.FeatureReportByteLength}");
        int[] lengths = { caps.FeatureReportByteLength, 65, 67 };
        foreach (int length in lengths.Distinct())
        {
            if (length is < 65 or > 256) continue;
            int? percent = PollBattery(handle, length, attempts);
            if (percent.HasValue)
                return new Reading(true, percent, "2.4 GHz / 8K");
        }
        return new Reading(true, null, "No valid battery status report");
    }

    private static int? PollBattery(SafeFileHandle handle, int length,
        List<string> attempts)
    {
        // Existing zero-payload telemetry query only; diagnostics add no I/O.
        byte[] poll = new byte[length];
        poll[1] = 0xF7;
        if (!HidNative.SendApprovedFeature(handle, poll))
        {
            attempts.Add($"  SET F7 ({length} bytes): failed, Win32 {Marshal.GetLastWin32Error()}");
            return null;
        }

        Thread.Sleep(30);
        byte[] response = new byte[length];
        response[0] = 0x05;
        if (!HidNative.HidD_GetFeature(handle, response, length))
        {
            attempts.Add($"  SET F7 OK; GET 05 ({length} bytes): failed, Win32 {Marshal.GetLastWin32Error()}");
            return null;
        }

        int? percent = BatteryReportParser.ParseWindowsFeature(response);
        attempts.Add($"  SET F7 / GET 05 ({length} bytes): OK; " +
            $"header={DiagnosticHidIdentity.BatteryHeader(response)}; " +
            (percent.HasValue ? $"battery={percent}%" : "no valid battery"));
        return percent;
    }
}
