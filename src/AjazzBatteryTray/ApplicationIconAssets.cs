using System.Drawing;

namespace AjazzBatteryTray;

/// <summary>Load only bundled application icon choices.</summary>
internal static class ApplicationIconAssets
{
    internal static Icon Load(string? color)
    {
        using Stream stream = Open(color);
        using Icon icon = new(stream);
        return (Icon)icon.Clone();
    }

    internal static void Export(string? color, string path)
    {
        using Stream resource = Open(color);
        using var output = new FileStream(path, FileMode.CreateNew, FileAccess.Write);
        resource.CopyTo(output);
    }

    private static Stream Open(string? color)
    {
        string choice = TrayColorRules.NormalizeAppIcon(color);
        string file = choice == "orange" ? "AppIcon.ico" : $"AppIcon-{choice}.ico";
        return typeof(ApplicationIconAssets).Assembly.GetManifestResourceStream(
            "AjazzBatteryTray.Assets." + file)
            ?? throw new InvalidOperationException("Missing embedded application icon.");
    }
}
