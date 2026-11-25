using AjazzBatteryTray;

internal static class HistoryRecoveryTests
{
    internal static void Run(Action<string, bool> check)
    {
        string dir = Directory.CreateTempSubdirectory("ajazz-history-").FullName;
        try
        {
            var now = DateTimeOffset.UtcNow.AddMinutes(-1);
            var history = new BatteryHistory("test.csv", dir);
            string path = Path.Combine(dir, history.FileName);
            check("Missing history is a readable empty series",
                history.TryReadRecent(out var absent) && absent.Count == 0);
            var first = new BatterySample(now.AddSeconds(-5), 70, "online");
            File.WriteAllText(path, BatteryHistoryCsv.Header + "\r\n" + BatteryHistoryCsv.Format(first));
            history.Record(now, 69, true);
            check("Append and first prune retain unterminated valid CSV row and new reading",
                history.ReadRecent().Select(x => x.Percent).SequenceEqual(new int?[] { 70, 69 }));
            File.AppendAllText(path, "interrupted,row");
            history.Record(now.AddSeconds(1), null, false);
            check("Torn tail cannot swallow next disconnect event",
                history.ReadRecent().Select(x => x.State).SequenceEqual(
                    new[] { "online", "online", "disconnected" }));
            using (File.Open(path, FileMode.Open, FileAccess.ReadWrite, FileShare.None))
                check("Busy history reports read failure", !history.TryReadRecent(out var busy) && busy.Count == 0);
            check("History refresh recovers after lock release",
                history.TryReadRecent(out var recovered) && recovered.Count == 3);
        }
        finally { Directory.Delete(dir, recursive: true); }
    }
}
