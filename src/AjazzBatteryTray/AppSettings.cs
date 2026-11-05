using System.Text.Json;

namespace AjazzBatteryTray;

/// <summary>Per-user application preferences saved as readable JSON.</summary>
public sealed class AppSettings
{
    public int PollSeconds { get; set; } = 30;
    public bool NotificationsEnabled { get; set; } = true;

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

    public void Save()
    {
        try
        {
            Directory.CreateDirectory(DirectoryPath);
            string temporary = FilePath + ".tmp";
            File.WriteAllText(temporary, JsonSerializer.Serialize(this,
                new JsonSerializerOptions { WriteIndented = true }));
            File.Move(temporary, FilePath, true);
        }
        catch (Exception error)
        {
            FileLog.Write("ERROR", "Could not save preferences", error);
        }
    }
}
