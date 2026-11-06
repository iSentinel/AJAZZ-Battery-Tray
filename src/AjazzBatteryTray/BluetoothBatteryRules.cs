namespace AjazzBatteryTray;

/// <summary>Safe validation of standard Bluetooth Battery Level data.</summary>
public static class BluetoothBatteryRules
{
    /// <summary>Recognizes likely AJAZZ pairing names, not a device identity.</summary>
    public static bool IsCandidateName(string? name)
    {
        if (string.IsNullOrWhiteSpace(name)) return false;
        string value = name.Trim();
        return value.Contains("AJAZZ", StringComparison.OrdinalIgnoreCase) ||
               value.Contains("AJ159", StringComparison.OrdinalIgnoreCase) ||
               value.Contains("AJ179", StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>Read one Battery Level byte (0-100), rejecting other frames.</summary>
    public static bool TryParseLevel(ReadOnlySpan<byte> data, out int level)
    {
        level = 0;
        if (data.Length != 1 || data[0] > 100) return false;
        level = data[0];
        return true;
    }
}
