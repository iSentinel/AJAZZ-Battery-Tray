namespace AjazzBatteryTray;

/// <summary>Where a Bluetooth battery reading originated.</summary>
public enum BluetoothBatterySource
{
    Unavailable,
    DirectGatt,
    WindowsCached
}

/// <summary>A battery result with a typed source, not a UI-message heuristic.</summary>
public sealed record BluetoothBatteryResult(
    int? Percent, BluetoothBatterySource Source, string Status)
{
    /// <summary>Only a validated direct GATT value is safe for live monitoring.</summary>
    public bool IsFreshGatt => Source == BluetoothBatterySource.DirectGatt &&
        Percent is >= 0 and <= 100;
}
