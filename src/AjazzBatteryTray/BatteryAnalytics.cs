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

    /// <summary>Sum observed percentage drops only across adjacent valid samples.
    /// This is not a full charge-cycle count or a measure of capacity/health.</summary>
    public static double ObservedDischargeEquivalent(IReadOnlyList<BatterySample> samples,
        DateTimeOffset now)
    {
        long points = 0;
        for (int i = 1; i < samples.Count; i++)
        {
            var previous = samples[i - 1];
            var current = samples[i];
            TimeSpan gap = current.Timestamp - previous.Timestamp;
            if (!Valid(previous) || !Valid(current) || current.Timestamp > now ||
                gap <= TimeSpan.Zero || gap > MaxGap)
                continue;
            points += Math.Max(0, previous.Percent!.Value - current.Percent!.Value);
        }
        return points / 100.0;
    }

    private static bool Valid(BatterySample sample)
        => sample.State == "online" && sample.Percent is >= 0 and <= 100;
}
