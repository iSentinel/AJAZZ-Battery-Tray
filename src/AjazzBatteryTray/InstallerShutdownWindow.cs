using System.Threading;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Top-level hidden window for the Restart Manager close-app session messages.</summary>
internal sealed class InstallerShutdownWindow : NativeWindow, IDisposable
{
    private const int QueryEndSession = 0x0011;
    private const int EndSession = 0x0016;
    private const int CloseApp = 0x00000001;
    internal const string ProbeMode = "--internal-installer-lifecycle-probe";
    private readonly Action _exit;
    private bool _requested;

    internal InstallerShutdownWindow(Action exit)
    {
        _exit = exit;
        CreateHandle(new CreateParams
        {
            Caption = "AJAZZ Battery Tray",
            Style = unchecked((int)0x80000000) // WS_POPUP, hidden top-level window
        });
    }

    protected override void WndProc(ref Message message)
    {
        bool closeApp = (message.LParam.ToInt64() & CloseApp) != 0;
        if (closeApp && message.Msg == QueryEndSession)
        {
            message.Result = new IntPtr(1);
            return;
        }
        if (closeApp && message.Msg == EndSession)
        {
            message.Result = IntPtr.Zero;
            if (message.WParam != IntPtr.Zero && !_requested)
            {
                _requested = true;
                _exit();
            }
            return;
        }
        base.WndProc(ref message);
    }

    public void Dispose() => DestroyHandle();

    /// <summary>Bounded CI-only synthetic lifecycle; never creates the real tray or reads HID.</summary>
    internal static int RunProbe()
    {
        ApplicationConfiguration.Initialize();
        using ApplicationContext context = new();
        int result = 1;
        using InstallerShutdownWindow window = new(() =>
        {
            result = 0;
            context.ExitThread();
        });
        using EventWaitHandle ready = new(false, EventResetMode.ManualReset,
            @"Local\AJAZZBatteryTray_InstallerProbe_v1");
        using System.Windows.Forms.Timer deadline = new() { Interval = 120000 };
        deadline.Tick += (_, _) => context.ExitThread();
        deadline.Start();
        ready.Set();
        Application.Run(context);
        return result;
    }
}
