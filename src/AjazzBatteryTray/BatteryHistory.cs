namespace AjazzBatteryTray;

/// <summary>Battery reading or receiver state at one UTC instant.</summary>
public sealed record BatterySample(DateTimeOffset Timestamp, int? Percent, string State);

/// <summary>Pure, hardware-independent rules for storing observations.</summary>
public static class BatteryHistoryRules
{
    public static string State(bool receiverPresent, int? percent)
        => percent.HasValue ? "online" :
           receiverPresent ? "unavailable" : "disconnected";

    public static bool ShouldRecord(BatterySample? previous, BatterySample sample)
        => ShouldRecord(previous, sample.Timestamp, sample.Percent, sample.State);

    public static bool ShouldRecord(BatterySample? previous, DateTimeOffset timestamp,
        int? percent, string state)
        => previous is null || previous.State != state || previous.Percent != percent ||
           timestamp < previous.Timestamp ||
           timestamp - previous.Timestamp >= TimeSpan.FromMinutes(5);

    /// <summary>Same final observation as Retain, without sorting or retaining every row.</summary>
    public static BatterySample? Latest(IEnumerable<BatterySample> samples, DateTimeOffset now)
    {
        BatterySample? latest = null;
        DateTimeOffset cutoff = now.AddDays(-30);
        foreach (var sample in samples)
            if (sample.Timestamp >= cutoff && sample.Timestamp <= now &&
                (latest is null || sample.Timestamp >= latest.Timestamp))
                latest = sample;
        return latest;
    }

    /// <summary>Keep a maximum of 30 days and 20,000 observations.</summary>
    public static IReadOnlyList<BatterySample> Retain(
        IEnumerable<BatterySample> samples, DateTimeOffset now)
        => samples.Where(x => x.Timestamp >= now.AddDays(-30) && x.Timestamp <= now)
                  .OrderBy(x => x.Timestamp).TakeLast(20000).ToArray();
}

/// <summary>Small, human-readable history stored on the user's computer.</summary>
public sealed class BatteryHistory
{

    public static string FilePath => Path.Combine(
        AppSettings.DirectoryPath, "battery-history.csv");

    private readonly string _filePath;
    public string FileName { get; }
    private BatterySample? _last;
    private bool _lastLoaded;
    private DateTime _lastPrune = DateTime.MinValue;

    public BatteryHistory(string fileName = "battery-history.csv")
        : this(fileName, AppSettings.DirectoryPath)
    {
    }

    internal BatteryHistory(string fileName, string directory)
    {
        FileName = Path.GetFileName(fileName);
        _filePath = Path.Combine(directory, FileName);
    }

    private void EnsureLastLoaded()
    {
        if (_lastLoaded) return;
        if (File.Exists(_filePath))
            _last = BatteryHistoryRules.Latest(ReadFile(), DateTimeOffset.UtcNow);
        _lastLoaded = true;
    }

    public void Record(DateTimeOffset now, int? percent, bool receiverPresent)
    {
        try
        {
            EnsureLastLoaded();
            DateTimeOffset timestamp = now.ToUniversalTime();
            string state = BatteryHistoryRules.State(receiverPresent, percent);
            if (!BatteryHistoryRules.ShouldRecord(_last, timestamp, percent, state)) return;
            BatterySample sample = new(timestamp, percent, state);
            Directory.CreateDirectory(Path.GetDirectoryName(_filePath)!);
            Append(sample);

            _last = sample;
            if (_lastPrune.Date != now.UtcDateTime.Date) Prune(now);
        }
        catch (Exception error)
        {
            FileLog.Write(LogEvent.HistorySaveFailed, error);
        }
    }

    private void Append(BatterySample sample)
    {
        using FileStream file = new(_filePath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.Read);
        bool empty = file.Length == 0;
        int lastByte = -1;
        if (!empty)
        {
            file.Seek(-1, SeekOrigin.End);
            lastByte = file.ReadByte();
        }

        using StreamWriter writer = new(file);
        if (empty) writer.WriteLine(BatteryHistoryCsv.Header);
        else if (lastByte != '\n' && lastByte != '\r') writer.WriteLine();
        writer.WriteLine(BatteryHistoryCsv.Format(sample));
    }

    public IReadOnlyList<BatterySample> ReadRecent()
    {
        TryReadRecent(out var samples);
        return samples;
    }

    internal bool TryReadRecent(out IReadOnlyList<BatterySample> samples)
    {
        samples = Array.Empty<BatterySample>();
        try
        {
            samples = BatteryHistoryRules.Retain(ReadFile(), DateTimeOffset.UtcNow);
            return true;
        }
        catch (FileNotFoundException) { return true; }
        catch (DirectoryNotFoundException) { return true; }
        catch (Exception error)
        {
            FileLog.Write(LogEvent.HistoryReadFailed, error);
            return false;
        }
    }

    private void Prune(DateTimeOffset now)
    {
        IReadOnlyList<BatterySample> points = BatteryHistoryRules.Retain(ReadFile(), now);
        string temporary = _filePath + ".tmp";
        File.WriteAllLines(temporary, new[] { BatteryHistoryCsv.Header }
            .Concat(points.Select(BatteryHistoryCsv.Format)));
        File.Move(temporary, _filePath, overwrite: true);
        _lastPrune = now.UtcDateTime;
    }

    private IEnumerable<BatterySample> ReadFile()
        => File.ReadLines(_filePath)
            .Where(x => x != BatteryHistoryCsv.Header)
            .Select(BatteryHistoryCsv.Parse)
            .OfType<BatterySample>();
}
