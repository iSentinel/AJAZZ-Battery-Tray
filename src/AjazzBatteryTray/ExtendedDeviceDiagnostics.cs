using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

namespace AjazzBatteryTray;

/// <summary>Metadata-only inventory for troubleshooting receiver revisions.</summary>
public static class ExtendedDeviceDiagnostics
{
    public static string ReadInventory()
    {
        StringBuilder report = new();
        report.AppendLine("[HID inventory — descriptor access only]");
        report.AppendLine("Targets: AJAZZ VID 3151 (all PIDs), AULA candidate IDs 05AC:024F / 0C45:800A / 0C45:FEFE.");
        try
        {
            IReadOnlyList<string> paths = HidNative.FindDiagnosticPaths();
            report.AppendLine($"Candidate HID interfaces: {paths.Count}");
            for (int i = 0; i < paths.Count; i++)
                AppendInterface(report, paths[i], i + 1);
            if (paths.Count == 0)
                report.AppendLine("No matching present HID interfaces.");
        }
        catch (Exception error)
        {
            report.AppendLine("Inventory unavailable: " + error.GetType().Name);
        }

        report.AppendLine("Non-HID USB devices, firmware and serial numbers are not queried.");
        report.AppendLine("Unknown receiver IDs are listed, not polled.");
        return report.ToString();
    }

    private static void AppendInterface(StringBuilder report, string path, int index)
    {
        report.AppendLine($"#{index}: {DiagnosticHidIdentity.FromPath(path)}");
        try
        {
            using SafeFileHandle handle = HidNative.OpenMetadata(path);
            if (handle.IsInvalid)
            {
                report.AppendLine($"  Descriptor open failed: Win32 {Marshal.GetLastWin32Error()}");
                return;
            }

            var attributes = HidNative.GetAttributes(handle);
            report.AppendLine(attributes is { } a
                ? $"  Descriptor VID:PID: {a.VendorID:X4}:{a.ProductID:X4}; bcdDevice: 0x{a.VersionNumber:X4}"
                : "  USB attributes unavailable.");
            if (!HidNative.TryGetCaps(handle, out var caps))
            {
                report.AppendLine("  HID capabilities unavailable.");
                return;
            }

            report.AppendLine($"  Usage page: 0x{caps.UsagePage:X4}; usage: 0x{caps.Usage:X4}");
            report.AppendLine($"  Report bytes: input={caps.InputReportByteLength}; output={caps.OutputReportByteLength}; feature={caps.FeatureReportByteLength}");
            report.AppendLine($"  AJAZZ poll candidate: {path.Contains("vid_3151&pid_5007&mi_02", StringComparison.OrdinalIgnoreCase) && caps.UsagePage == 0xFFFF && caps.Usage == 2}");
            report.AppendLine($"  AULA poll candidate: {AulaL99Protocol.MatchesPath(path) && AulaL99Protocol.MatchesCaps(caps.UsagePage, caps.InputReportByteLength, caps.OutputReportByteLength)}");
        }
        catch (Exception error)
        {
            report.AppendLine("  Descriptor inspection failed: " + error.GetType().Name);
        }
    }
}
