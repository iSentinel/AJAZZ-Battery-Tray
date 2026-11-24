using AjazzBatteryTray;
using System.Drawing;
using System.Windows.Forms;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        Application.SetHighDpiMode(HighDpiMode.PerMonitorV2);
        Application.EnableVisualStyles();
        foreach (string language in new[] { "en", "ru", "uk" })
        {
            UiText.SetLanguage(language);
            CheckDashboard();
            Console.WriteLine($"PASS: {language} minimum-size layout and device actions");
        }
    }

    private static void CheckDashboard()
    {
        string action = "";
        using var form = new DeviceDashboardForm(() => action = "refresh",
            () => action = "report", () => action = "telemetry");
        var receiver = new DeviceDashboardForm.Entry(
            new("Receiver", "2.4 GHz", DeviceDashboardStatus.Fresh, 72, DateTimeOffset.Now),
            () => action = "history", "usb", () => action = "rename");
        var bluetooth = new DeviceDashboardForm.Entry(
            new("BLE", "Bluetooth", DeviceDashboardStatus.NoReply, null, null), Key: "ble");
        form.Size = form.MinimumSize;
        form.Show();
        form.SetEntries(new[] { receiver, bluetooth });
        Application.DoEvents();
        var layout = form.Controls.OfType<TableLayoutPanel>().Single();
        var grid = layout.Controls.OfType<DataGridView>().Single();
        var panel = layout.Controls.OfType<FlowLayoutPanel>().Single();
        var buttons = panel.Controls.OfType<Button>().ToArray();
        Require(buttons.Length == 5 && buttons.All(b => panel.ClientRectangle.Contains(b.Bounds)),
            "Buttons must fit at minimum window size");
        Require(buttons.All(b => form.ClientRectangle.Contains(form.RectangleToClient(
            b.RectangleToScreen(b.ClientRectangle)))), "An action extends outside the window");
        Button Find(string key) => buttons.Single(b => b.Text.StartsWith(UiText.Get(key)));
        Find("Refresh now").PerformClick();
        Require(action == "refresh", "Refresh unavailable");
        Find("Battery history...").PerformClick();
        Require(action == "history", "Wrong history target");
        var settings = Find("Device settings");
        settings.PerformClick();
        Application.DoEvents();
        var menu = settings.ContextMenuStrip!;
        Require(menu.Visible && menu.Items.Count == 5, "Device menu unavailable");
        form.SetEntries(new[] { bluetooth, receiver });
        Require(grid.CurrentRow?.Index == 1, "Selection lost during polling");
        menu.Items[0].PerformClick();
        Require(action == "rename", "Wrong device after reordering");
        menu.Close();
        settings.PerformClick();
        form.SetEntries(new[] { bluetooth });
        Require(!menu.Visible && !settings.Enabled && !Find("Battery history...").Enabled,
            "Removed device still actionable");
        var diagnostics = Find("Diagnostics");
        diagnostics.PerformClick();
        var diagnosticMenu = diagnostics.ContextMenuStrip!;
        diagnosticMenu.Items[1].PerformClick();
        Require(action == "telemetry", "Telemetry command missing");
        diagnosticMenu.Close();
    }

    private static void Require(bool valid, string message)
    {
        if (!valid) throw new InvalidOperationException(message);
    }
}
