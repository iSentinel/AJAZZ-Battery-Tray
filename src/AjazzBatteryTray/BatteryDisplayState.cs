namespace AjazzBatteryTray;

/// <summary>Identifies which transport the tray is displaying.</summary>
public enum BatteryTransport
{
    Usb24GHz,
    Bluetooth
}

/// <summary>Additional context when the USB reader has no validated charge.</summary>
public enum UsbReadIssue { None, NotChecked, InterfaceUnavailable, Busy, Timeout }

public static class UsbTrayStatus
{
    public static string Reason(bool presenceKnown, bool present, UsbReadIssue issue)
    {
        if (issue == UsbReadIssue.NotChecked) return UiText.Get("Not checked");
        if (issue == UsbReadIssue.Busy) return UiText.Get("HID interface busy");
        if (issue == UsbReadIssue.Timeout) return UiText.Get("HID read timed out");
        if (!presenceKnown) return UiText.Get("Receiver status unknown");
        if (!present) return UiText.Get("Receiver disconnected");
        return UiText.Get(issue == UsbReadIssue.InterfaceUnavailable
            ? "HID interface unavailable" : "Receiver present, no fresh charge");
    }

    public static string UnverifiedField(int percent) => UiText.Format("{0}% (unverified)", percent);

    public static string WithLastVerified(string status, DateTimeOffset? lastVerified)
        => lastVerified is { } stamp
            ? status + " · " + UiText.Format("Last verified {0}", stamp.ToLocalTime().ToString("g"))
            : status;
}

/// <summary>Bound the presentation of the last ordinary USB observation.</summary>
public static class ApexDisplayPolicy
{
    public static readonly TimeSpan ScheduledLifetime = DeviceDashboardState.MaximumScheduledAge;

    public static bool IsCurrent(bool known, bool present, bool scheduled,
        DateTimeOffset? measured, DateTimeOffset now)
        => known && present && measured is { } at && at <= now &&
            now - at <= (scheduled ? ScheduledLifetime : DeviceDashboardState.MaximumFreshAge);

    public static DeviceDashboardState Dashboard(string name, bool known, bool present,
        bool scheduled, int? percent, DateTimeOffset? measured, DateTimeOffset now)
        => DeviceDashboardState.FromPoll(name, "2.4 GHz", true, known, present,
            IsCurrent(known, present, scheduled, measured, now) && percent is >= 1 and <= 100
                ? percent : null, measured, scheduled: scheduled);

    /// <summary>Only a current, sampled, verified USB reading may mutate alert state.</summary>
    public static int? AlertPercent(bool known, bool present, bool scheduled,
        int? percent, DateTimeOffset? measured, DateTimeOffset now)
        => !scheduled && IsCurrent(known, present, false, measured, now) &&
            percent is >= 1 and <= 100 ? percent : null;

    /// <summary>Prefer fresh over retained scheduled readings, then unknown.</summary>
    public static int SelectionRank(DeviceDashboardState state)
        => state.Percent is >= 1 and <= 100
            ? state.Status switch
            {
                DeviceDashboardStatus.Fresh => 2,
                DeviceDashboardStatus.Scheduled => 1,
                _ => 0
            } : 0;

    /// <summary>Select a visible candidate without allowing an old primary to outrank fresh data.</summary>
    public static bool PreferCandidate(string key, int rank, bool present, bool hidden,
        string? bestKey, int bestRank, string? preferred)
    {
        if (!present || hidden) return false;
        if (bestKey is null || rank > bestRank) return true;
        if (rank < bestRank) return false;
        return key == preferred ||
            (bestKey != preferred && StringComparer.Ordinal.Compare(key, bestKey) < 0);
    }

    /// <summary>Report measurement provenance without exporting receiver identity.</summary>
    public static string DiagnosticSample(DateTimeOffset? measured, bool scheduled)
        => $"USB sample UTC: {measured?.ToUniversalTime().ToString("O") ?? "never"}; scheduled: {scheduled}";

    public static int? Unverified(bool known, bool present, bool scheduled,
        int? field, DateTimeOffset? measured, DateTimeOffset now)
        => !scheduled && IsCurrent(known, present, false, measured, now) &&
            field is >= 1 and <= 100 ? field : null;
}

/// <summary>Session-only display cache for one continuously observed USB receiver.</summary>
public sealed class ApexVerifiedDisplayCache
{
    private int? _percent;
    private DateTimeOffset? _measured;

    public void Observe(bool known, bool present, int? verified, DateTimeOffset measured)
    {
        if (!known || !present || (_measured is { } prior && measured < prior))
            Reset();
        if (known && present && verified is >= 1 and <= 100)
        {
            _percent = verified;
            _measured = measured;
        }
    }

    public void Reset()
    {
        _percent = null;
        _measured = null;
    }

    /// <summary>Never alter raw observations, history, alerts, or the strict API projection.</summary>
    public DeviceDashboardState Present(DeviceDashboardState observation, DateTimeOffset now,
        bool scheduled = false)
    {
        if (scheduled || observation.Status != DeviceDashboardStatus.NoReply ||
            _percent is not (>= 1 and <= 100) || _measured is not { } stamp ||
            stamp > now || now - stamp > DeviceDashboardState.MaximumFreshAge)
            return observation;
        return observation with { Status = DeviceDashboardStatus.Cached,
            Percent = _percent, MeasuredAt = stamp };
    }
}

/// <summary>Selects a battery source without merging distinct transports.</summary>
public sealed record BatteryDisplayState(BatteryTransport Source, int? Percent)
{
    public string SourceName => Source == BatteryTransport.Bluetooth
        ? "Bluetooth" : "2.4 GHz";

    public bool HasReading => Percent.HasValue;

    /// <summary>Unknown USB enumeration must never imply disconnection.</summary>
    public static bool SafeReceiverPresent(bool receiverPresent, bool known)
        => receiverPresent || !known;

    /// <summary>Only confirmed USB absence allows Bluetooth fallback.</summary>
    public static bool MayUseBluetooth(bool receiverPresent, bool known)
        => known && !receiverPresent;

    /// <summary>USB presence or uncertain enumeration takes priority.</summary>
    public static BatteryDisplayState Resolve(bool receiverPresent,
        int? usbPercent, bool bluetoothEnabled, int? bluetoothPercent,
        bool presenceKnown = true)
    {
        if (!presenceKnown)
            return new(BatteryTransport.Usb24GHz, null);

        if (receiverPresent)
            return new(BatteryTransport.Usb24GHz, usbPercent);

        if (bluetoothEnabled)
            return new(BatteryTransport.Bluetooth, bluetoothPercent);

        return new(BatteryTransport.Usb24GHz, null);
    }

    /// <summary>Select a primary icon without asserting physical identity.</summary>
    public static bool PreferIndependentBluetooth(bool visibleUsb, int? usbPercent,
        bool bluetoothEnabled, int? bluetoothPercent)
        => bluetoothEnabled && (!visibleUsb ||
            (!usbPercent.HasValue && bluetoothPercent.HasValue));

    /// <summary>Suppress USB-disconnect alerts during deliberate BLE fallback.</summary>
    public static bool NotifyReceiverDisconnect(bool eventDetected,
        bool bluetoothFallbackEnabled)
        => eventDetected && !bluetoothFallbackEnabled;
}
