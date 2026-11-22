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
    public bool MultipleTrayIcons { get; set; } = true;
    // Absent key inherits the global sampling interval.
    public Dictionary<string, int> DevicePollIntervals { get; set; } = new(StringComparer.Ordinal);
    // Absent key inherits global thresholds; zero explicitly mutes this device.
    public Dictionary<string, int> DeviceAlertMasks { get; set; } = new(StringComparer.Ordinal);
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
                    result.DeviceTrayColors = TrayColorRules.Clean(result.DeviceTrayColors);
                    result.HiddenTrayDevices = TrayVisibilityRules.Clean(result.HiddenTrayDevices);
                    result.DeviceAliases = DeviceAliasRules.Clean(result.DeviceAliases);
                    result.Language = UiText.Normalize(result.Language);
                    result.PollSeconds = result.PollSeconds is 15 or 30 or 60 or 120
                        ? result.PollSeconds : 30;
                    return result;
                }
            }
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "Could not read preferences", error);
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
            FileLog.Write("ERROR", "Could not save preferences", error);
            return false;
        }
    }
}
