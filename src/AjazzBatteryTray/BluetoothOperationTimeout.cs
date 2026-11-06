namespace AjazzBatteryTray;

/// <summary>Sets a time bound for a user-triggered Bluetooth UI request.</summary>
public static class BluetoothOperationTimeout
{
    /// <summary>Return an explicit timeout instead of blocking the UI forever.</summary>
    public static Task<T> Run<T>(Task<T> operation, TimeSpan limit)
    {
        if (limit <= TimeSpan.Zero)
            throw new ArgumentOutOfRangeException(nameof(limit));
        return operation.WaitAsync(limit);
    }
}
