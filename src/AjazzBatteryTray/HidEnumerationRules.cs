namespace AjazzBatteryTray;

/// <summary>Recognizes the normal end of Windows SetupAPI enumeration.</summary>
public static class HidEnumerationRules
{
    // ERROR_NO_MORE_ITEMS is the only successful end-of-list result.
    public const int NoMoreItems = 259;

    /// <summary>Other Win32 errors mean presence is unknown, not absent.</summary>
    public static bool IsNormalEnd(int win32Error)
        => win32Error == NoMoreItems;
}
