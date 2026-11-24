using System.Threading;
using System.Windows.Forms;

namespace AjazzBatteryTray;

internal static class Program
{
    internal const string TrayMutexName = "Local\\AJAZZBatteryTray_AJ179_APEX";

    [STAThread]
    private static void Main(string[] args)
    {
        if (args.Length > 0)
        {
            Environment.ExitCode = WindowsHidDiagnostics.Run(args);
            return;
        }
        using Mutex singleInstance = new(true, TrayMutexName, out bool first);
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
