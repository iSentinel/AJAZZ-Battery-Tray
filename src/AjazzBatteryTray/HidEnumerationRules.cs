namespace AjazzBatteryTray;

/// <summary>Recognizes the normal end of Windows SetupAPI enumeration.</summary>
public static class HidEnumerationRules
{
    // ERROR_NO_MORE_ITEMS is the only successful end-of-list result.
    public const int NoMoreItems = 259;
    public const int InsufficientBuffer = 122;

    /// <summary>Other Win32 errors mean presence is unknown, not absent.</summary>
    public static bool IsNormalEnd(int win32Error)
        => win32Error == NoMoreItems;

    /// <summary>A NULL detail buffer should report its required size.</summary>
    public static bool IsExpectedSizeQueryError(int win32Error)
        => win32Error == InsufficientBuffer;

    /// <summary>Reject corrupt or unreasonable interface-detail sizes.</summary>
    public static bool IsValidDetailSize(uint needed)
        => needed is >= 8 and <= 65536;
}
