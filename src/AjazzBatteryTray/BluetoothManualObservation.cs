namespace AjazzBatteryTray;

/// <summary>Privacy-limited historical manual read, independent of monitor consent.</summary>
internal sealed record BluetoothManualObservation(
    string Model, bool IsLowEnergy, int? Percent, BluetoothBatterySource Source,
    DateTimeOffset CompletedAt)
{
    internal static BluetoothManualObservation Create(string name, bool lowEnergy,
        BluetoothBatteryResult result, DateTimeOffset completedAt)
    {
        string model = name.Trim().ToUpperInvariant() switch
        {
            "AJ179 APEX" => "AJ179 APEX",
            "AJ159 APEX" => "AJ159 APEX",
            _ => "paired endpoint (name omitted)"
        };
        bool valid = result.Percent is >= 0 and <= 100 &&
            (result.Source == BluetoothBatterySource.WindowsCached ||
             (lowEnergy && result.IsFreshGatt));
        return new(model, lowEnergy, valid ? result.Percent : null,
            valid ? result.Source : BluetoothBatterySource.Unavailable, completedAt);
    }

    internal string Format() =>
        $"{Model}; transport={(IsLowEnergy ? "BLE" : "Classic")}; " +
        $"battery={Percent?.ToString() ?? "unavailable"}; source={Source}; " +
        $"completed UTC={CompletedAt:O}; historical=true";
}
