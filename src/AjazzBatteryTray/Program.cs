using System.Threading;
using System.Windows.Forms;

namespace AjazzBatteryTray;

internal static class Program
{
    internal const string TrayMutexName = "Local\\AJAZZBatteryTray_AJ179_APEX";

    [STAThread]
    private static void Main(string[] args)
    {
        bool isolated = args.Length == 1 && args[0] == "--experimental-isolated-polling";
        if (args.Length > 0 && !isolated)
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
        FileLog.Write(LogEvent.ApplicationStarted);
        Application.Run(new TrayAppContext(isolated));
    }
}
