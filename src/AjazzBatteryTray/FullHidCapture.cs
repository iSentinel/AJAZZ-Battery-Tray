using System.Diagnostics;
using System.Text;

namespace AjazzBatteryTray;

/// <summary>Isolates consented full HID capture; raw output stays in an anonymous pipe.</summary>
internal static class FullHidCapture
{
    internal const int TimeoutSeconds = 40;
    private const int StartToken = 0x41;
    internal sealed record Result(int ExitCode, string Report);

    internal static async Task<Result> RunAsync(string mode, int seconds,
        Action? onTimeout = null, Action<int>? onStarted = null)
    {
        using HidWorkerJob job = new();
        using Process worker = StartWorker(mode);
        try
        {
            // The child must not touch HID until it is assigned to a kill-on-close job.
            job.Assign(worker);
            worker.StandardInput.BaseStream.WriteByte(StartToken);
            worker.StandardInput.BaseStream.Flush();
            worker.StandardInput.Close();
            onStarted?.Invoke(worker.Id);
            Task<string> output = worker.StandardOutput.ReadToEndAsync();
            Task exit = worker.WaitForExitAsync();
            using CancellationTokenSource deadline = new();
            if (await Task.WhenAny(exit, Task.Delay(TimeSpan.FromSeconds(seconds), deadline.Token)) != exit)
            {
                onTimeout?.Invoke();
                job.Dispose();
                StopWorker(worker);
                // Do not permit another HID poll until process termination is confirmed.
                await exit;
                await output;
                return new(124, "");
            }
            deadline.Cancel();
            await exit;
            string report = await output;
            return new(worker.ExitCode, worker.ExitCode == 0 ? report : "");
        }
        finally
        {
            job.Dispose();
            if (!worker.HasExited)
            {
                StopWorker(worker);
                await worker.WaitForExitAsync();
            }
        }
    }

    private static Process StartWorker(string mode)
    {
        ProcessStartInfo info = new(Environment.ProcessPath!)
        {
            UseShellExecute = false, CreateNoWindow = true,
            RedirectStandardInput = true, RedirectStandardOutput = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardInputEncoding = new UTF8Encoding(false)
        };
        info.ArgumentList.Add(mode);
        return Process.Start(info)
            ?? throw new InvalidOperationException("Diagnostic worker did not start");
    }

    private static void StopWorker(Process worker)
    {
        try { worker.Kill(entireProcessTree: true); }
        catch (InvalidOperationException) { /* Already exited. */ }
        catch (System.ComponentModel.Win32Exception)
        {
            // A failed termination is not proof of exit. Caller keeps I/O exclusion.
        }
    }

    internal static int RunWorker(string mode)
    {
        if (!Console.IsInputRedirected || !Console.IsOutputRedirected) return 1;
        try
        {
            using Stream input = Console.OpenStandardInput();
            if (input.ReadByte() != StartToken) return 1;
            using StreamWriter writer = new(Console.OpenStandardOutput(),
                new UTF8Encoding(false)) { AutoFlush = true };
            if (mode == "--full-hid-test-hang")
            {
                writer.WriteLine("synthetic partial report");
                Thread.Sleep(30000);
                return 0;
            }
            if (mode == "--full-hid-test-success")
            {
                writer.WriteLine("synthetic complete report");
                return 0;
            }
            if (mode != "--full-hid-worker") return 1;
            WriteCapture(writer);
            return 0;
        }
        catch (Exception) { return 1; }
    }

    private static void WriteCapture(TextWriter writer)
    {
        string inventory = ExtendedDeviceDiagnostics.ReadInventory();
        var batch = new AjazzHidReader().ReadAll(captureProtocol: true);
        writer.WriteLine(inventory);
        writer.WriteLine($"Fresh enumeration known={batch.Summary.PresenceKnown}; " +
            $"receiver count={batch.Receivers.Count}; first valid battery=" +
            (batch.Summary.Percent?.ToString() ?? "unavailable"));
        writer.WriteLine("\n[Fresh APEX protocol matrix — full vendor buffers]");
        foreach (string line in batch.Summary.Attempts ?? Array.Empty<string>())
            writer.WriteLine(line);
    }

    internal static int SelfTest(bool hang)
    {
        string mode = hang ? "--full-hid-test-hang" : "--full-hid-test-success";
        Result result = RunAsync(mode, hang ? 2 : 20).GetAwaiter().GetResult();
        if (hang) return result.ExitCode == 124 && result.Report.Length == 0 ? 124 : 1;
        return result.ExitCode == 0 && result.Report.Trim() == "synthetic complete report" ? 0 : 1;
    }

    // Synthetic supervisor writes only a process ID, never raw device information.
    internal static int ParentExitSupervisor()
    {
        if (!Console.IsOutputRedirected) return 1;
        using StreamWriter writer = new(Console.OpenStandardOutput(),
            new UTF8Encoding(false)) { AutoFlush = true };
        return RunAsync("--full-hid-test-hang", 25, onStarted:
            pid => writer.WriteLine(pid)).GetAwaiter().GetResult().ExitCode;
    }

    internal static int SelfTestParentExit()
    {
        using Process parent = StartWorker("--full-hid-test-parent");
        try
        {
            parent.StandardInput.Close();
            string? line = parent.StandardOutput.ReadLineAsync()
                .WaitAsync(TimeSpan.FromSeconds(15)).GetAwaiter().GetResult();
            if (!int.TryParse(line, out int pid)) return 1;
            using Process child = Process.GetProcessById(pid);
            // Open a stable handle before the supervisor is killed.
            _ = child.SafeHandle;
            if (child.HasExited) return 1;
            parent.Kill();
            return parent.WaitForExit(5000) && child.WaitForExit(5000) ? 0 : 1;
        }
        finally
        {
            if (!parent.HasExited) StopWorker(parent);
        }
    }

}
