using AjazzBatteryTray;
using System.Text.Json;

/// <summary>Tests operate only on a newly created temporary journal directory.</summary>
internal static class SafeLogTests
{
    private static readonly DateTimeOffset SampleTime =
        new(2026, 11, 25, 2, 0, 0, TimeSpan.FromHours(2));

    internal static void Run(Action<string, bool> check)
    {
        string directory = Path.Combine(Path.GetTempPath(), "ajazz-log-" + Guid.NewGuid());
        Directory.CreateDirectory(directory);
        try
        {
            Privacy(directory, check);
            Rotation(directory, check);
            InterruptedTail(directory, check);
            Refusal(directory, check);
        }
        finally { Directory.Delete(directory, recursive: true); }
    }

    private static bool Write(string directory, LogEvent code, Exception? error = null)
        => FileLog.TryWriteTo(directory, code, error, SampleTime, limit: 512);

    private static void Privacy(string directory, Action<string, bool> check)
    {
        string legacy = Path.Combine(directory, "app.log");
        File.WriteAllText(legacy, "legacy evidence");
        check("Structured log accepts closed event",
            Write(directory, LogEvent.HidReadFailed, new IOException("PRIVATE_CANARY")));
        string active = Path.Combine(directory, FileLog.ActiveName);
        string text = File.ReadAllText(active);
        using var parsed = JsonDocument.Parse(text);
        JsonElement row = parsed.RootElement;
        check("Structured log UTC schema and safe reason",
            row.GetProperty("schema").GetInt32() == 1 &&
            row.GetProperty("utc").GetString() == "2026-11-25T00:00:00.0000000+00:00" &&
            row.GetProperty("level").GetString() == "WARN" &&
            row.GetProperty("event").GetString() == "HidReadFailed" &&
            row.GetProperty("reason").GetString() == "io_error" &&
            row.EnumerateObject().Count() == 5);
        check("Structured log excludes raw exception canary",
            !text.Contains("PRIVATE_CANARY", StringComparison.Ordinal));
        check("Structured log preserves legacy file",
            File.ReadAllText(legacy) == "legacy evidence");
    }

    private static void Rotation(string directory, Action<string, bool> check)
    {
        bool writes = true;
        for (int i = 0; i < 40; i++)
            writes &= Write(directory, LogEvent.BatteryDisplayAvailable);
        string active = Path.Combine(directory, FileLog.ActiveName);
        string previous = Path.Combine(directory, FileLog.PreviousName);
        check("Structured log rotates both files within configured cap",
            writes && File.Exists(previous) &&
            new FileInfo(active).Length <= 512 && new FileInfo(previous).Length <= 512);
        bool valid = true;
        foreach (string line in File.ReadLines(active).Concat(File.ReadLines(previous)))
        {
            using var row = JsonDocument.Parse(line);
            valid &= row.RootElement.GetProperty("event").GetString() ==
                "BatteryDisplayAvailable";
        }
        check("Structured log rotation retains complete closed events", valid);
    }

    private static void InterruptedTail(string directory, Action<string, bool> check)
    {
        string active = Path.Combine(directory, FileLog.ActiveName);
        string previous = Path.Combine(directory, FileLog.PreviousName);
        File.WriteAllText(active, "{\"schema\":1");
        check("Structured log starts clean after interrupted tail",
            Write(directory, LogEvent.IsolatedPollTimedOut));
        using var row = JsonDocument.Parse(File.ReadAllText(active));
        check("Structured log retains interrupted prior generation",
            File.ReadAllText(previous) == "{\"schema\":1" &&
            row.RootElement.GetProperty("reason").GetString() == "timeout");
    }

    private static void Refusal(string directory, Action<string, bool> check)
    {
        string active = Path.Combine(directory, FileLog.ActiveName);
        byte[] original = File.ReadAllBytes(active);
        check("Structured log refuses unknown event without changing file",
            !Write(directory, (LogEvent)int.MaxValue) &&
            File.ReadAllBytes(active).SequenceEqual(original));
        using (var lease = new FileStream(Path.Combine(directory, FileLog.LeaseName),
                   FileMode.Open, FileAccess.Write, FileShare.None))
        {
            check("Structured log refuses contended writer without changing file",
                !Write(directory, LogEvent.PollFailed) &&
                File.ReadAllBytes(active).SequenceEqual(original));
        }
        string invalid = Path.Combine(directory, "not-a-directory");
        File.WriteAllText(invalid, "fixture");
        check("Structured log I/O failure remains nonfatal",
            !Write(invalid, LogEvent.PollFailed) && File.ReadAllText(invalid) == "fixture");
        File.WriteAllText(active, new string('x', 513));
        check("Structured log refuses unexpected oversized existing file",
            !Write(directory, LogEvent.PollFailed) && new FileInfo(active).Length == 513);
    }
}
