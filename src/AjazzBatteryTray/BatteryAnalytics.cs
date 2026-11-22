namespace AjazzBatteryTray;

/// <summary>Observed linear discharge trend, not capacity or battery health.</summary>
public sealed record BatteryDrainEstimate(double PercentPerHour, double HoursRemaining,
    TimeSpan ObservationSpan, int Observations, DateTimeOffset LastMeasurement);

public static class BatteryAnalytics
{
    private static readonly TimeSpan MaxGap = TimeSpan.FromMinutes(15);
    private static readonly TimeSpan MinSpan = TimeSpan.FromMinutes(30);

    /// <summary>Use only the latest contiguous, non-increasing online segment.</summary>
    public static BatteryDrainEstimate? EstimateDrain(
        IReadOnlyList<BatterySample> samples, DateTimeOffset now)
    {
        if (samples.Count < 3) return null;
        BatterySample end = samples[^1];
        if (!Valid(end) || now < end.Timestamp || now - end.Timestamp > MaxGap)
            return null;

        BatterySample start = end;
        int count = 1;
        for (int i = samples.Count - 2; i >= 0; i--)
        {
            BatterySample previous = samples[i];
            TimeSpan gap = start.Timestamp - previous.Timestamp;
            if (!Valid(previous) || gap <= TimeSpan.Zero || gap > MaxGap ||
                previous.Percent!.Value < start.Percent!.Value)
                break;
            start = previous;
            count++;
        }

        TimeSpan span = end.Timestamp - start.Timestamp;
        int decrease = start.Percent!.Value - end.Percent!.Value;
        if (count < 3 || span < MinSpan || decrease < 3) return null;
        double rate = decrease / span.TotalHours;
        return new(rate, end.Percent!.Value / rate, span, count, end.Timestamp);
    }

    private static bool Valid(BatterySample sample)
        => sample.State == "online" && sample.Percent is >= 0 and <= 100;
}
