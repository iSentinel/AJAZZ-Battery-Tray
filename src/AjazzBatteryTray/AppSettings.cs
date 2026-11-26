using System.Text.Json;

namespace AjazzBatteryTray;

/// <summary>Per-user application preferences saved as readable JSON.</summary>
public sealed class AppSettings
{
    public int PollSeconds { get; set; } = 30;
    public bool AutomaticUpdateChecks { get; set; } = false;
    public bool ExperimentalUpdateChannel { get; set; } = false;
    public string Language { get; set; } = "en";
    public bool NotificationsEnabled { get; set; } = true;
    public bool AlertBelow50 { get; set; } = true;
    public bool AlertBelow25 { get; set; } = true;
    public bool AlertBelow10 { get; set; } = true;
    public bool RecordBatteryHistory { get; set; } = true;
    public bool NotifyOnDisconnect { get; set; } = false;
    public bool AutomaticDockClockSync { get; set; } = true;
    public bool MonitorAulaL99 { get; set; } = false;
    public string ApplicationIconColor { get; set; } = "orange";
    public string DefaultTrayColor { get; set; } = TrayColorRules.Default;
    public bool MouseTrayIcon { get; set; } = true;
    public bool MultipleTrayIcons { get; set; } = true;
    public bool ShowUnverifiedUsbCharge { get; set; } = false;
    // Local consent only; no raw endpoint IDs, names or saved battery levels.
    public HashSet<string> ConsentedBleEndpoints { get; set; } = new(StringComparer.Ordinal);
    public Dictionary<string, string> BleUsbLinks { get; set; } = new(StringComparer.Ordinal);
    // Absent key inherits the global sampling interval.
    public Dictionary<string, int> DevicePollIntervals { get; set; } = new(StringComparer.Ordinal);
    // Absent key inherits global thresholds; zero explicitly mutes this device.
    public Dictionary<string, int> DeviceAlertMasks { get; set; } = new(StringComparer.Ordinal);
    // Absence inherits global receiver disconnect preference; false mutes one device.
    public Dictionary<string, bool> DeviceDisconnectAlerts { get; set; } =
        new(StringComparer.Ordinal);
    public Dictionary<string, string> DeviceTrayColors { get; set; } = new(StringComparer.Ordinal);
    public HashSet<string> HiddenTrayDevices { get; set; } = new(StringComparer.Ordinal);
    public Dictionary<string, string> DeviceAliases { get; set; } = new(StringComparer.Ordinal);

    public static string DirectoryPath => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "AJAZZBatteryTray");

    private static string FilePath => Path.Combine(DirectoryPath, "settings.json");

    public static AppSettings Load()
    {
        try
        {
            if (File.Exists(FilePath))
            {
                AppSettings? result = JsonSerializer.Deserialize<AppSettings>(
                    File.ReadAllText(FilePath));
                if (result is not null)
                {
                    result.DevicePollIntervals = DevicePollSchedule.CleanOverrides(result.DevicePollIntervals);
                    result.DeviceAlertMasks = CleanDeviceAlertMasks(result.DeviceAlertMasks);
                    result.DeviceDisconnectAlerts =
                        CleanDeviceDisconnectAlerts(result.DeviceDisconnectAlerts);
                    result.ApplicationIconColor = TrayColorRules.NormalizeAppIcon(result.ApplicationIconColor);
                    result.DefaultTrayColor = TrayColorRules.Normalize(result.DefaultTrayColor);
                    result.DeviceTrayColors = TrayColorRules.Clean(result.DeviceTrayColors);
                    result.HiddenTrayDevices = TrayVisibilityRules.Clean(result.HiddenTrayDevices);
                    result.DeviceAliases = DeviceAliasRules.Clean(result.DeviceAliases);
                    result.ConsentedBleEndpoints = BleConsent.Clean(result.ConsentedBleEndpoints);
                    result.BleUsbLinks = TransportLinks.Clean(result.BleUsbLinks, result.ConsentedBleEndpoints);
                    result.Language = UiText.Normalize(result.Language);
                    result.PollSeconds = result.PollSeconds is 15 or 30 or 60 or 120
                        ? result.PollSeconds : 30;
                    return result;
                }
            }
        }
        catch (Exception error)
        {
            FileLog.Write(LogEvent.PreferencesReadFailed, error);
        }

        return new AppSettings();
    }

    public int EffectivePollInterval(string key)
        => DevicePollSchedule.ResolveInterval(PollSeconds,
            DeviceAliasRules.ValidKey(key) && DevicePollIntervals.TryGetValue(key, out int seconds)
                ? seconds : null);

    [System.Text.Json.Serialization.JsonIgnore]
    public int GlobalAlertMask => (AlertBelow50 ? 1 : 0) |
        (AlertBelow25 ? 2 : 0) | (AlertBelow10 ? 4 : 0);

    public int EffectiveAlertMask(string key)
    {
        if (!NotificationsEnabled) return 0;
        return DeviceAliasRules.ValidKey(key) &&
            DeviceAlertMasks.TryGetValue(key, out int mask) && mask is >= 0 and <= 7
            ? mask : GlobalAlertMask;
    }

    public bool EffectiveDisconnectAlert(string key)
        => DeviceAliasRules.ValidKey(key) &&
           DeviceDisconnectAlerts.TryGetValue(key, out bool enabled)
            ? enabled : NotifyOnDisconnect;

    public static Dictionary<string, bool> CleanDeviceDisconnectAlerts(
        Dictionary<string, bool>? values)
    {
        Dictionary<string, bool> clean = new(StringComparer.Ordinal);
        if (values is null) return clean;
        foreach (var pair in values)
            if (DeviceAliasRules.ValidKey(pair.Key))
                clean[pair.Key] = pair.Value;
        return clean;
    }

    public static Dictionary<string, int> CleanDeviceAlertMasks(Dictionary<string, int>? values)
    {
        Dictionary<string, int> clean = new(StringComparer.Ordinal);
        if (values is null) return clean;
        foreach (var pair in values)
            if (DeviceAliasRules.ValidKey(pair.Key) && pair.Value is >= 0 and <= 7)
                clean[pair.Key] = pair.Value;
        return clean;
    }

    public bool Save()
    {
        try
        {
            Directory.CreateDirectory(DirectoryPath);
            string temporary = FilePath + ".tmp";
            File.WriteAllText(temporary, JsonSerializer.Serialize(this,
                new JsonSerializerOptions { WriteIndented = true }));
            File.Move(temporary, FilePath, true);
            return true;
        }
        catch (Exception error)
        {
            FileLog.Write(LogEvent.PreferencesSaveFailed, error);
            return false;
        }
    }
}
