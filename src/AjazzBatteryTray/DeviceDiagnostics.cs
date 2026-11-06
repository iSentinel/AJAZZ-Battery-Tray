using Microsoft.Win32.SafeHandles;

namespace AjazzBatteryTray;

/// <summary>Displays non-identifying USB receiver properties, without extra HID writes.</summary>
public static class DeviceDiagnostics
{
    public static string Read()
    {
        try
        {
            IReadOnlyList<string> paths = HidNative.FindAjazzPaths();
            int matched = 0;
            int featureLength = 0;
            foreach (string path in paths)
            {
                using SafeFileHandle handle = HidNative.Open(path);
                if (handle.IsInvalid || !HidNative.TryGetCaps(handle, out var caps))
                    continue;
                if (caps.UsagePage != 0xFFFF || caps.Usage != 0x02) continue;
                matched++;
                featureLength = caps.FeatureReportByteLength;
            }

            return $"USB VID:PID: 3151:5007\n" +
                   $"MI_02 interfaces: {paths.Count}\n" +
                   $"Matching vendor collections: {matched}\n" +
                   $"HID feature report length: {(matched == 0 ? "unknown" : featureLength + " bytes")}\n" +
                   "Firmware version: not queried (protocol unverified)\n" +
                   "DPI / polling rate: not queried (protocol unverified)\n" +
                   "Private USB paths and serial numbers are not shown.";
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "Unable to inspect USB receiver", error);
            return $"Receiver inspection unavailable: {error.GetType().Name}";
        }
    }
}
