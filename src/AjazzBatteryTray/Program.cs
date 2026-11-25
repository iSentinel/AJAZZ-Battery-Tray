using System.Threading;
using System.Windows.Forms;

namespace AjazzBatteryTray;

internal static class Program
{
    [STAThread]
    private static void Main(string[] args)
    {
        if (args.Length > 0)
        {
            Environment.ExitCode = args.Length == 1 ? args[0] switch
            {
                "--full-hid-worker" or "--full-hid-test-hang" or "--full-hid-test-success"
                    => FullHidCapture.RunWorker(args[0]),
                "--self-test-full-hid-watchdog" => FullHidCapture.SelfTest(true),
                "--self-test-full-hid-success" => FullHidCapture.SelfTest(false),
                _ => WindowsHidDiagnostics.Run(args)
            } : WindowsHidDiagnostics.Run(args);
            return;
        }
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
