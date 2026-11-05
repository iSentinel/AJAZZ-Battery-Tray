using System.Threading;
using System.Windows.Forms;

namespace AjazzBatteryTray;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        using Mutex singleInstance = new(true, "Local\\AJAZZBatteryTray_AJ179_APEX", out bool first);
        if (!first)
        {
            MessageBox.Show("AJAZZ Battery Tray is already running.",
                "AJAZZ Battery Tray", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        ApplicationConfiguration.Initialize();
        FileLog.Write("INFO", "Application started");
        Application.Run(new TrayAppContext());
    }
}
