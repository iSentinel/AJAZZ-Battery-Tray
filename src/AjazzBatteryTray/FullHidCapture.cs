using System.Diagnostics;
using System.Text;
using System.Text.Json;

namespace AjazzBatteryTray;

/// <summary>Keep a synchronous vendor diagnostic in a bounded child process.</summary>
internal static class FullHidCapture
{
    internal const int TimeoutSeconds = 40;
    internal const string Worker = "--internal-full-hid-worker";
    private const string SampleWorker = "--internal-full-hid-sample-worker";
    private const string TestWorker = "--internal-full-hid-test-worker";
    internal sealed record Result(string Inventory, string Summary, string Matrix);

    internal static async Task<Result> ReadAsync(CancellationToken closing,
        string mode = Worker)
    {
        ProcessStartInfo start = new(Environment.ProcessPath!)
        {
            UseShellExecute = false, CreateNoWindow = true,
            RedirectStandardOutput = true, StandardOutputEncoding = Encoding.UTF8
        };
        start.ArgumentList.Add(mode);
        closing.ThrowIfCancellationRequested();
        using Process child = Process.Start(start) ?? throw new IOException("Worker start failed");
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(closing);
        deadline.CancelAfter(TimeSpan.FromSeconds(mode == TestWorker ? 2 : TimeoutSeconds));
        using var stop = deadline.Token.Register(() =>
        {
            try { child.Kill(entireProcessTree: true); }
            catch (InvalidOperationException) { /* Process already exited. */ }
            catch (System.ComponentModel.Win32Exception) { /* Child also has a watchdog. */ }
        });
        Task<string> output = child.StandardOutput.ReadToEndAsync();
        await child.WaitForExitAsync().ConfigureAwait(false);
        string body = await output.ConfigureAwait(false);
        closing.ThrowIfCancellationRequested();
        if (deadline.IsCancellationRequested || child.ExitCode == 124) throw new TimeoutException();
        if (child.ExitCode != 0) throw new IOException("Capture worker failed");
        return JsonSerializer.Deserialize<Result>(body) ?? throw new InvalidDataException();
    }

    internal static int RunWorker(string mode)
    {
        if (!Console.IsOutputRedirected) return 1;
        // Also bound the child if its parent terminates during a native call.
        using var watchdog = new System.Threading.Timer(_ => Environment.Exit(124),
            null, TimeSpan.FromSeconds(TimeoutSeconds + 2), Timeout.InfiniteTimeSpan);
        if (mode == TestWorker) Thread.Sleep(Timeout.Infinite);
        try
        {
            using Stream output = Console.OpenStandardOutput();
            if (mode == SampleWorker)
            {
                JsonSerializer.Serialize(output, new Result("sample", "unverified", "HID — тест"));
                return 0;
            }
            string inventory = ExtendedDeviceDiagnostics.ReadInventory();
            var batch = new AjazzHidReader().ReadAll(captureProtocol: true);
            string summary = $"Fresh enumeration known={batch.Summary.PresenceKnown}; " +
                $"receiver count={batch.Receivers.Count}; first valid battery=" +
                (batch.Summary.Percent?.ToString() ?? "unavailable");
            string matrix = batch.Summary.Attempts is { } trace ? string.Join("\n", trace) : "No trace";
            JsonSerializer.Serialize(output, new Result(inventory, summary, matrix));
            return 0;
        }
        catch (Exception) { return 1; }
    }

    internal static int SelfTest()
    {
        try
        {
            Result sample = ReadAsync(CancellationToken.None, SampleWorker).GetAwaiter().GetResult();
            if (sample != new Result("sample", "unverified", "HID — тест")) return 1;
        }
        catch (Exception) { return 1; }
        try { ReadAsync(CancellationToken.None, TestWorker).GetAwaiter().GetResult(); }
        catch (TimeoutException) { return 124; }
        catch (Exception) { return 1; }
        return 1;
    }

    internal static bool IsWorker(string mode) => mode is Worker or TestWorker or SampleWorker;
}
