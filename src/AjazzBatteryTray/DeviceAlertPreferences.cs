namespace AjazzBatteryTray;

/// <summary>Optional local override of the global notification defaults.</summary>
public sealed record DeviceAlertPreferences(
    bool Below50, bool Below25, bool Below10, bool NotifyOnDisconnect)
{
    public static DeviceAlertPreferences Defaults(AppSettings settings)
        => new(settings.AlertBelow50, settings.AlertBelow25, settings.AlertBelow10,
            settings.NotifyOnDisconnect);

    public static DeviceAlertPreferences Resolve(AppSettings settings, string key)
        => settings.DeviceAlerts.GetValueOrDefault(key) ?? Defaults(settings);

    public static Dictionary<string, DeviceAlertPreferences> Clean(
        Dictionary<string, DeviceAlertPreferences>? values)
    {
        Dictionary<string, DeviceAlertPreferences> result = new(StringComparer.Ordinal);
        if (values is null) return result;
        foreach (var pair in values)
            if (DeviceAliasRules.ValidKey(pair.Key) && pair.Value is not null)
                result[pair.Key] = pair.Value;
        return result;
    }

    public int? Evaluate(AlertPolicy policy, int level, bool globalEnabled)
        => policy.Evaluate(level, globalEnabled && Below50,
            globalEnabled && Below25, globalEnabled && Below10);
}
