namespace AjazzBatteryTray;

/// <summary>Local tray visibility preferences do not change device monitoring.</summary>
public static class TrayVisibilityRules
{
    public static HashSet<string> Clean(IEnumerable<string>? hidden)
        => new((hidden ?? Array.Empty<string>()).Where(DeviceAliasRules.ValidKey),
            StringComparer.Ordinal);

    public static bool IsVisible(IReadOnlySet<string> hidden, string key)
        => !hidden.Contains(key);

    /// <summary>Prefer the existing primary when visible, otherwise choose a stable replacement.</summary>
    public static string? SelectMouse(string? preferred, IEnumerable<string> present,
        IReadOnlySet<string> hidden)
        => ReceiverIdentity.SelectPrimary(preferred, present.Where(key => IsVisible(hidden, key)));
}
