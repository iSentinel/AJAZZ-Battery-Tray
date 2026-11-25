using System.Diagnostics;
using System.Text;

namespace AjazzBatteryTray;

/// <summary>Explicit, bounded, local-only Windows 11 HID diagnostic capture.</summary>
internal static class WindowsHidDiagnostics
{
    private const int DefaultTimeout = 40;

    internal static int Run(string[] args)
    {
        if (args.Length == 1 && RoutinePollWorker.IsWorker(args[0]))
            return RoutinePollWorker.RunWorker(args[0]);
        if (args.Length == 1 && args[0] == "--self-test-routine-poll-worker")
            return RoutinePollWorker.SelfTest();
        if (args.Length == 1 && FullHidCapture.IsWorker(args[0]))
            return FullHidCapture.RunWorker(args[0]);
        if (args.Length == 1 && args[0] == "--self-test-full-hid-watchdog")
            return FullHidCapture.SelfTest();
        if (args.Length == 1 && args[0] == "--self-test-full-hid-parent-exit")
            return FullHidCapture.SelfTestParentExit();
        if (args.Length == 1 && args[0] == "--self-test-full-hid-start-gate")
            return FullHidCapture.SelfTestStartGate();
        if (args.Length == 2 && args[0] == "--hid-diag-worker")
            return Capture(args[1], false);
        if (args.Length == 2 && args[0] == "--hid-compare-worker")
            return CompareWorker(args[1]);
        if (args.Length == 2 && args[0] == "--hid-test-worker")
            return Capture(args[1], true);
        if (args.Length == 1 && args[0] is "-h" or "--help")
        {
            Console.WriteLine("Usage: AJAZZBatteryTray.exe --hid-diagnose --output PATH [--timeout 3..90]");
            Console.WriteLine("--hid-compare-get-ids --output PATH [--timeout 3..90] (diagnostic only)");
            Console.WriteLine("Exit: 0 verified, 2 inconclusive, 124 timeout, 1 error.");
            return 0;
        }
        return ParseAndRun(args);
    }

    private static int ParseAndRun(string[] args)
    {
        if (args.Length == 0 || args[0] is not
            ("--hid-diagnose" or "--hid-compare-get-ids" or "--self-test-hid-watchdog")) return 1;
        string? output = null;
        int timeout = args[0] == "--self-test-hid-watchdog" ? 1 : DefaultTimeout;
        for (int i = 1; i < args.Length; i++)
        {
            if (args[i] == "--output" && ++i < args.Length && output is null)
                output = args[i];
            else if (args[i] == "--timeout" && ++i < args.Length &&
                     args[0] is ("--hid-diagnose" or "--hid-compare-get-ids") &&
                     int.TryParse(args[i], out int seconds) &&
                     seconds is >= 3 and <= 90)
                timeout = seconds;
            else return 1;
        }
        if (string.IsNullOrWhiteSpace(output)) return 1;
        string worker = args[0] switch
        {
            "--hid-diagnose" => "--hid-diag-worker",
            "--hid-compare-get-ids" => "--hid-compare-worker",
            _ => "--hid-test-worker"
        };
        if (args[0] == "--hid-compare-get-ids")
        {
            // Reserve the tray singleton for the duration of the experiment.
            // The user must close the tray and official utility first.
            using Mutex exclusive = new(true, Program.TrayMutexName, out bool first);
            if (!first)
            {
                try
                {
                    using StreamWriter log = OpenNewLog(output);
                    log.WriteLine("FAIL: close AJAZZ Battery Tray before GET ID comparison");
                }
                catch (Exception) { /* Never overwrite an existing report. */ }
                return 1;
            }
            return SpawnBounded(output, worker, timeout);
        }
        return SpawnBounded(output, worker, timeout);
    }

    private static int CompareWorker(string path)
    {
        try
        {
            // Keep the singleton alive even if the supervising parent exits.
            using Mutex exclusive = Mutex.OpenExisting(Program.TrayMutexName);
            using var watchdog = new System.Threading.Timer(_ => Environment.Exit(124),
                null, TimeSpan.FromSeconds(92), Timeout.InfiniteTimeSpan);
            return Capture(path, false, true);
        }
        catch (Exception) { return 1; }
    }

    private static StreamWriter OpenNewLog(string path)
    {
        FileStream stream = new(path, FileMode.CreateNew, FileAccess.Write,
            FileShare.ReadWrite, 4096, FileOptions.WriteThrough);
        return new StreamWriter(stream, Encoding.UTF8) { AutoFlush = true };
    }

    private static void Append(string path, string message)
    {
        using StreamWriter writer = new(new FileStream(path, FileMode.Append,
            FileAccess.Write, FileShare.ReadWrite, 4096, FileOptions.WriteThrough));
        writer.WriteLine(message);
    }

    private static int SpawnBounded(string path, string mode, int seconds)
    {
        bool created = false;
        try
        {
            using (StreamWriter writer = OpenNewLog(path))
            {
                created = true;
                writer.WriteLine($"BEGIN: UTC={DateTimeOffset.UtcNow:O} timeout={seconds}s");
            }
            ProcessStartInfo info = new(Environment.ProcessPath!)
            {
                UseShellExecute = false, CreateNoWindow = true
            };
            info.ArgumentList.Add(mode);
            info.ArgumentList.Add(path);
            using Process? worker = Process.Start(info);
            if (worker is null) throw new InvalidOperationException("Process spawn failed");
            if (!worker.WaitForExit(seconds * 1000))
            {
                try { worker.Kill(entireProcessTree: true); }
                catch (InvalidOperationException) { /* Worker exited during timeout. */ }
                worker.WaitForExit(1000);
                Append(path, $"TIMEOUT: HID worker exceeded {seconds}s; no level claimed");
                return 124;
            }
            Append(path, $"END: worker exited {worker.ExitCode}");
            return worker.ExitCode;
        }
        catch (Exception error)
        {
            if (created)
            {
                try { Append(path, "FAIL: " + error.GetType().Name); }
                catch (Exception) { /* Output path may be unwritable. */ }
            }
            return 1;
        }
    }

    private static int Capture(string path, bool selfTest, bool compareGetIds = false)
    {
        try
        {
            using StreamWriter writer = new(new FileStream(path, FileMode.Append,
                FileAccess.Write, FileShare.ReadWrite, 4096, FileOptions.WriteThrough))
            { AutoFlush = true };
            writer.WriteLine("STEP: worker started (local-only, no serial numbers)");
            if (selfTest)
            {
                Thread.Sleep(6000);
                return 0;
            }
            if (compareGetIds)
                writer.WriteLine("MODE: experimental GET 05 versus GET 00; no battery claimed");
            AjazzHidReader.Batch batch = new AjazzHidReader().ReadAll(
                captureProtocol: true, progress: writer.WriteLine, redactRaw: true,
                compareGetIds: compareGetIds);
            foreach (string line in batch.Summary.Attempts ?? Array.Empty<string>())
                writer.WriteLine(line);
            if (compareGetIds)
            {
                writer.WriteLine("INCONCLUSIVE: experimental GET ID comparison; no battery claimed");
                return 2;
            }
            int? battery = batch.Summary.Percent;
            writer.WriteLine(battery.HasValue
                ? $"PASS: verified battery {battery}%"
                : "INCONCLUSIVE: no verified battery report");
            return battery.HasValue ? 0 : 2;
        }
        catch (Exception error)
        {
            try { Append(path, "FAIL: worker " + error.GetType().Name); }
            catch (Exception) { /* Do not leak sensitive paths. */ }
            return 1;
        }
    }
}
