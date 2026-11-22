using System.Text.Json;

namespace AjazzBatteryTray;

/// <summary>Per-user application preferences saved as readable JSON.</summary>
public sealed class AppSettings
{
    public int PollSeconds { get; set; } = 30;
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
