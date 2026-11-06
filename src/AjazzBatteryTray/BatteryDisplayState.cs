namespace AjazzBatteryTray;

/// <summary>Identifies which transport the tray is displaying.</summary>
public enum BatteryTransport
{
    Usb24GHz,
    Bluetooth
}

/// <summary>Selects a battery source without merging distinct transports.</summary>
public sealed record BatteryDisplayState(BatteryTransport Source, int? Percent)
{
    public string SourceName => Source == BatteryTransport.Bluetooth
        ? "Bluetooth" : "2.4 GHz";

    public bool HasReading => Percent.HasValue;

    /// <summary>USB presence wins even while the USB mouse is asleep.</summary>
    public static BatteryDisplayState Resolve(bool receiverPresent,
        int? usbPercent, bool bluetoothEnabled, int? bluetoothPercent)
    {
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
