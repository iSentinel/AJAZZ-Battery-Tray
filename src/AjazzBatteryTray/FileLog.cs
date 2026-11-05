namespace AjazzBatteryTray;

/// <summary>Small local text log; no device serial numbers are stored.</summary>
public static class FileLog
{
    public static string LogPath => Path.Combine(AppSettings.DirectoryPath, "app.log");

    public static void Write(string level, string message, Exception? error = null)
    {
        try
        {
            Directory.CreateDirectory(AppSettings.DirectoryPath);
            string details = error is null ? "" : $" ({error.GetType().Name}: {error.Message})";
            string line = $"{DateTimeOffset.Now:yyyy-MM-dd HH:mm:ss zzz} [{level}] {message}{details}";
            File.AppendAllText(LogPath, line + Environment.NewLine);
        }
        catch
        {
            // Logging must never stop the tray application.
        }
    }
}
