using System.Drawing;

namespace AjazzBatteryTray;

/// <summary>Load only bundled application icon choices.</summary>
internal static class ApplicationIconAssets
{
    internal static Icon Load(string? color)
    {
        string choice = TrayColorRules.NormalizeAppIcon(color);
        string file = choice == "orange" ? "AppIcon.ico" : $"AppIcon-{choice}.ico";
        using Stream stream = typeof(ApplicationIconAssets).Assembly.GetManifestResourceStream(
            "AjazzBatteryTray.Assets." + file)
            ?? throw new InvalidOperationException("Missing embedded application icon.");
        using Icon icon = new(stream);
        return (Icon)icon.Clone();
    }
}
