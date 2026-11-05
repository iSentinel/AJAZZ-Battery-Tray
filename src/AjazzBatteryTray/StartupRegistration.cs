using Microsoft.Win32;

namespace AjazzBatteryTray;

/// <summary>Registers the application for the current Windows user.</summary>
public static class StartupRegistration
{
    private const string KeyPath = @"Software\Microsoft\Windows\CurrentVersion\Run";
    private const string EntryName = "AJAZZBatteryTray";

    public static bool IsEnabled()
    {
        using RegistryKey? key = Registry.CurrentUser.OpenSubKey(KeyPath);
        return key?.GetValue(EntryName) is string value &&
            string.Equals(value, $"\"{Application.ExecutablePath}\"",
                StringComparison.OrdinalIgnoreCase);
    }

    public static void SetEnabled(bool enabled)
    {
        using RegistryKey? key = Registry.CurrentUser.OpenSubKey(KeyPath, true);
        if (key is null)
        {
            throw new InvalidOperationException("Windows startup registry key not found.");
        }

        if (enabled)
        {
            key.SetValue(EntryName, $"\"{Application.ExecutablePath}\"");
        }
        else
        {
            key.DeleteValue(EntryName, false);
        }
    }
}
