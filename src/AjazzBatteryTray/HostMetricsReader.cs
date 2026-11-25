using System.Runtime.InteropServices;

namespace AjazzBatteryTray;

public sealed record HostMetricsSnapshot(double? WindowsCpuLoad,
    IReadOnlyList<HostHardwareMetrics> Hardware, bool ProviderAvailable);

/// <summary>Manual host-only sensor read. No keyboard I/O or driver installation.</summary>
public static class HostMetricsReader
{
    private const int MaxProviderBytes = 2 * 1024 * 1024;
    private static readonly Uri Endpoint = new("http://127.0.0.1:8085/data.json");

    [StructLayout(LayoutKind.Sequential)]
    private struct FileTime
    {
        public uint Low;
        public uint High;
        public readonly ulong Value => ((ulong)High << 32) | Low;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetSystemTimes(out FileTime idle,
        out FileTime kernel, out FileTime user);

    public static async Task<HostMetricsSnapshot> ReadAsync()
    {
        Task<double?> cpu = SampleCpuAsync();
        var (hardware, available) = await ReadProviderAsync();
        return new HostMetricsSnapshot(await cpu, hardware, available);
    }

    private static (ulong Idle, ulong Kernel, ulong User)? ReadCpu()
        => GetSystemTimes(out var idle, out var kernel, out var user)
            ? (idle.Value, kernel.Value, user.Value) : null;

    private static async Task<double?> SampleCpuAsync()
    {
        try
        {
            var first = ReadCpu();
            await Task.Delay(400);
            var second = ReadCpu();
            if (first is not { } a || second is not { } b ||
                b.Idle < a.Idle || b.Kernel < a.Kernel || b.User < a.User)
                return null;
            return HostMetricsRules.CpuLoad(b.Idle - a.Idle,
                b.Kernel - a.Kernel, b.User - a.User);
        }
        catch { return null; }
    }

    private static async Task<(IReadOnlyList<HostHardwareMetrics>, bool)> ReadProviderAsync()
    {
        try
        {
            // The only network request is a local, user-initiated read.
            using HttpClientHandler handler = new()
            {
                UseProxy = false, AllowAutoRedirect = false, UseCookies = false
            };
            using HttpClient client = new(handler);
            using CancellationTokenSource timeout = new(TimeSpan.FromSeconds(3));
            using HttpResponseMessage response = await client.GetAsync(Endpoint,
                HttpCompletionOption.ResponseHeadersRead, timeout.Token);
            if (!response.IsSuccessStatusCode ||
                response.Content.Headers.ContentLength > MaxProviderBytes)
                return (Array.Empty<HostHardwareMetrics>(), false);
            using Stream stream = await response.Content.ReadAsStreamAsync(timeout.Token);
            using MemoryStream bytes = new();
            byte[] buffer = new byte[8192];
            while (true)
            {
                int count = await stream.ReadAsync(buffer.AsMemory(), timeout.Token);
                if (count == 0) break;
                if (bytes.Length + count > MaxProviderBytes)
                    return (Array.Empty<HostHardwareMetrics>(), false);
                bytes.Write(buffer, 0, count);
            }
            return (HostMetricsRules.ParseProvider(bytes.ToArray()), true);
        }
        catch (Exception error)
        {
            FileLog.Write(LogEvent.HostMetricsUnavailable, error);
            return (Array.Empty<HostHardwareMetrics>(), false);
        }
    }
}
