namespace AjazzBatteryTray;

/// <summary>Session-only numeric observation for diagnostics, never live battery state.</summary>
internal sealed class UsbDiagnosticHistory
{
    private sealed record Observation(ushort? Revision, int? Verified,
        int? Unverified, DateTimeOffset At);

    private Observation? _last;

    internal void Observe(ushort? revision, int? verified, int? unverified,
        DateTimeOffset at)
    {
        if (verified is not (>= 0 and <= 100)) verified = null;
        if (unverified is not (>= 1 and <= 100)) unverified = null;
        if (verified.HasValue) unverified = null;
        if (!verified.HasValue && !unverified.HasValue) return;
        if (_last is not null && at < _last.At) return;
        _last = new(revision, verified, unverified, at);
    }

    internal string Format()
    {
        const string heading = "[Last numeric single-receiver USB observation — historical, not telemetry]\n";
        if (_last is not { } item) return heading + "never";
        return heading +
            $"UTC={item.At:O}; VID:PID=3151:5007; revision=" +
            (item.Revision.HasValue ? $"{item.Revision.Value:X4}" : "unknown") +
            $"; verified at observation={item.Verified?.ToString() ?? "unavailable"}; " +
            $"unverified field={item.Unverified?.ToString() ?? "unavailable"}; " +
            "historical=true; receiver identity not linked to Bluetooth";
    }
}
