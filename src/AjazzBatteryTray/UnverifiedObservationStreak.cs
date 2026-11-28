namespace AjazzBatteryTray;

/// <summary>Session-only evidence of repeated unverified ordinary poll fields.</summary>
public sealed class UnverifiedObservationStreak
{
    public int? Field { get; private set; }
    public DateTimeOffset? First { get; private set; }
    public DateTimeOffset? Last { get; private set; }
    public int Count { get; private set; }

    public void Observe(int? field, DateTimeOffset sampledAt)
    {
        if (field is not (>= 1 and <= 100))
        {
            Reset();
            return;
        }
        if (field == Field && Last == sampledAt) return;
        if (field != Field || Last is null || sampledAt < Last.Value)
        {
            Field = field;
            First = sampledAt;
            Count = 1;
        }
        else if (Count < int.MaxValue)
            Count++;
        Last = sampledAt;
    }

    public void Reset()
    {
        Field = null;
        First = Last = null;
        Count = 0;
    }

    public string DiagnosticText()
        => Field is not null && First is { } first && Last is { } last
            ? FormattableString.Invariant(
                $"field={Field}; consecutive ordinary samples={Count}; first UTC={first.UtcDateTime:O}; last UTC={last.UtcDateTime:O}; span seconds={(last - first).TotalSeconds:F1}; not telemetry")
            : "no consecutive unverified ordinary observations";
}
