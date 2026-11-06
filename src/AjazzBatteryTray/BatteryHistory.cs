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
        => previous is null || previous.State != sample.State ||
           previous.Percent != sample.Percent ||
           sample.Timestamp < previous.Timestamp ||
           sample.Timestamp - previous.Timestamp >= TimeSpan.FromMinutes(5);

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

    private BatterySample? _last;
    private DateTime _lastPrune = DateTime.MinValue;

    public BatteryHistory()
    {
        _last = ReadRecent().LastOrDefault();
    }

    public void Record(DateTimeOffset now, int? percent, bool receiverPresent)
    {
        BatterySample sample = new(now.ToUniversalTime(), percent,
            BatteryHistoryRules.State(receiverPresent, percent));
        if (!BatteryHistoryRules.ShouldRecord(_last, sample)) return;
        try
        {
            Directory.CreateDirectory(AppSettings.DirectoryPath);
            bool needsHeader = !File.Exists(FilePath);
            using (StreamWriter writer = new(FilePath, append: true))
            {
                if (needsHeader) writer.WriteLine(BatteryHistoryCsv.Header);
                writer.WriteLine(BatteryHistoryCsv.Format(sample));
            }

            _last = sample;
            if (_lastPrune.Date != now.UtcDateTime.Date) Prune(now);
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "Unable to save battery history", error);
        }
    }

    public IReadOnlyList<BatterySample> ReadRecent()
    {
        try
        {
            if (!File.Exists(FilePath)) return Array.Empty<BatterySample>();
            return BatteryHistoryRules.Retain(ReadFile(), DateTimeOffset.UtcNow);
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "Unable to read battery history", error);
            return Array.Empty<BatterySample>();
        }
    }

    private void Prune(DateTimeOffset now)
    {
        IReadOnlyList<BatterySample> points = BatteryHistoryRules.Retain(ReadFile(), now);
        string temporary = FilePath + ".tmp";
        File.WriteAllLines(temporary, new[] { BatteryHistoryCsv.Header }
            .Concat(points.Select(BatteryHistoryCsv.Format)));
        File.Move(temporary, FilePath, overwrite: true);
        _lastPrune = now.UtcDateTime;
    }

    private static IEnumerable<BatterySample> ReadFile()
        => File.ReadLines(FilePath)
            .Where(x => x != BatteryHistoryCsv.Header)
            .Select(BatteryHistoryCsv.Parse)
            .OfType<BatterySample>();
}
