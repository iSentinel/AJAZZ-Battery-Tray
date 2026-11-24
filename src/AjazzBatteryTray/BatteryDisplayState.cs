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

    public static string WithLastVerified(string status, DateTimeOffset? lastVerified)
        => lastVerified is { } stamp
            ? status + " · " + UiText.Format("Last verified {0}", stamp.ToLocalTime().ToString("g"))
            : status;
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

    /// <summary>Suppress USB-disconnect alerts during deliberate BLE fallback.</summary>
    public static bool NotifyReceiverDisconnect(bool eventDetected,
        bool bluetoothFallbackEnabled)
        => eventDetected && !bluetoothFallbackEnabled;
}
