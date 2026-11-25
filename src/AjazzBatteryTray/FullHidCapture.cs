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
    private const string ParentHangWorker = "--internal-full-hid-parent-hang";
    private const string ParentWorker = "--internal-full-hid-parent-test";
    private const int StartToken = 0x41;
    internal sealed record Result(string Inventory, string Summary, string Matrix);

    internal static async Task<Result> ReadAsync(CancellationToken closing,
        string mode = Worker, Action<int>? started = null)
    {
        closing.ThrowIfCancellationRequested();
        using HidWorkerJob job = new();
        using Process child = StartWorker(mode);
        try
        {
            job.Assign(child);
            closing.ThrowIfCancellationRequested();
            child.StandardInput.BaseStream.WriteByte(StartToken);
            child.StandardInput.BaseStream.Flush();
            child.StandardInput.Close();
            started?.Invoke(child.Id);
            return await ReadAssignedAsync(child, job, closing, mode).ConfigureAwait(false);
        }
        finally
        {
            job.Dispose();
            if (!child.HasExited)
            {
                StopWorker(child);
                await child.WaitForExitAsync().ConfigureAwait(false);
            }
        }
    }

    private static Process StartWorker(string mode)
    {
        ProcessStartInfo start = new(Environment.ProcessPath!)
        {
            UseShellExecute = false, CreateNoWindow = true,
            RedirectStandardInput = true, RedirectStandardOutput = true,
            StandardInputEncoding = new UTF8Encoding(false),
            StandardOutputEncoding = Encoding.UTF8
        };
        start.ArgumentList.Add(mode);
        return Process.Start(start) ?? throw new IOException("Worker start failed");
    }

    private static async Task<Result> ReadAssignedAsync(Process child, HidWorkerJob job,
        CancellationToken closing, string mode)
    {
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(closing);
        deadline.CancelAfter(TimeSpan.FromSeconds(mode == TestWorker ? 2 : TimeoutSeconds));
        using var stop = deadline.Token.Register(() =>
        {
            job.Dispose();
            StopWorker(child);
        });
        Task<string> output = child.StandardOutput.ReadToEndAsync();
        await child.WaitForExitAsync().ConfigureAwait(false);
        string body = await output.ConfigureAwait(false);
        closing.ThrowIfCancellationRequested();
        if (deadline.IsCancellationRequested || child.ExitCode == 124) throw new TimeoutException();
        if (child.ExitCode != 0) throw new IOException("Capture worker failed");
        return JsonSerializer.Deserialize<Result>(body) ?? throw new InvalidDataException();
    }

    private static void StopWorker(Process child)
    {
        try { child.Kill(entireProcessTree: true); }
        catch (InvalidOperationException) { /* Process already exited. */ }
        catch (System.ComponentModel.Win32Exception) { /* Child also has a watchdog. */ }
    }

    internal static int RunWorker(string mode)
    {
        if (!Console.IsOutputRedirected || !Console.IsInputRedirected) return 1;
        // Also bound the child if its parent terminates during a native call.
        using var watchdog = new System.Threading.Timer(_ => Environment.Exit(124),
            null, TimeSpan.FromSeconds(TimeoutSeconds + 2), Timeout.InfiniteTimeSpan);
        try
        {
            if (mode == ParentWorker) return ParentExitSupervisor();
            using Stream input = Console.OpenStandardInput();
            if (input.ReadByte() != StartToken) return 1;
            if (mode is TestWorker or ParentHangWorker) Thread.Sleep(Timeout.Infinite);
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
                (batch.Summary.Percent?.ToString() ?? "unavailable") + "\n" +
                BatteryReportParser.DiagnosticUnverifiedField(batch.Summary.UnverifiedPercent);
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

    private static int ParentExitSupervisor()
    {
        using StreamWriter writer = new(Console.OpenStandardOutput(),
            new UTF8Encoding(false)) { AutoFlush = true };
        ReadAsync(CancellationToken.None, ParentHangWorker, pid => writer.WriteLine(pid))
            .GetAwaiter().GetResult();
        return 1;
    }

    internal static int SelfTestParentExit()
    {
        using Process parent = StartWorker(ParentWorker);
        try
        {
            parent.StandardInput.Close();
            string? line = parent.StandardOutput.ReadLineAsync()
                .WaitAsync(TimeSpan.FromSeconds(15)).GetAwaiter().GetResult();
            if (!int.TryParse(line, out int pid)) return 1;
            using Process child = Process.GetProcessById(pid);
            _ = child.SafeHandle;
            if (child.HasExited) return 1;
            parent.Kill();
            return parent.WaitForExit(5000) && child.WaitForExit(5000) ? 0 : 1;
        }
        catch (Exception) { return 1; }
        finally { if (!parent.HasExited) StopWorker(parent); }
    }

    internal static int SelfTestStartGate()
    {
        using Process child = StartWorker(SampleWorker);
        try
        {
            child.StandardInput.Close();
            return child.WaitForExit(5000) && child.ExitCode == 1 &&
                child.StandardOutput.ReadToEnd().Length == 0 ? 0 : 1;
        }
        finally { if (!child.HasExited) StopWorker(child); }
    }

    internal static bool IsWorker(string mode) =>
        mode is Worker or TestWorker or SampleWorker or ParentWorker or ParentHangWorker;
}
