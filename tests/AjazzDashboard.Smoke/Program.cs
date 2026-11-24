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
        CheckAppearanceResources();
        foreach (string language in new[] { "en", "ru", "uk" })
        {
            UiText.SetLanguage(language);
            CheckDashboard();
            Console.WriteLine($"PASS: {language} minimum-size layout and device actions");
            foreach (float factor in new[] { 1.25f, 1.5f, 2f })
                CheckScaledLayout(language, factor);
        }
    }

    private static void CheckAppearanceResources()
    {
        foreach (string color in TrayColorRules.AppIcons)
        {
            using Icon asset = ApplicationIconAssets.Load(color);
            using Icon normal = TrayIconFactory.Create(83, true, color: color, mouseStyle: true);
            using Icon critical = TrayIconFactory.Create(8, true, color: color, mouseStyle: true);
            using Bitmap pixels = critical.ToBitmap();
            Require(asset.Width > 0 && normal.Width == 64 && critical.Width == 64,
                "Missing appearance resource or incorrect icon size");
            Require(Enumerable.Range(0, pixels.Width).Any(x =>
                Enumerable.Range(0, pixels.Height).Any(y =>
                    pixels.GetPixel(x, y).R == 0xDC && pixels.GetPixel(x, y).G == 0x35 &&
                    pixels.GetPixel(x, y).B == 0x45)),
                "Critical icon must contain red fill");
        }
        CheckNumericGlyphBounds();
        CheckIconExport();
        Console.WriteLine("PASS: four embedded app icons and red critical rendering");
    }

    private static void CheckNumericGlyphBounds()
    {
        foreach (int level in new[] { 0, 8, 10, 15, 76, 99, 100 })
        foreach (bool stale in new[] { false, true })
        foreach (bool raw in new[] { false, true })
        {
            using Icon icon = TrayIconFactory.Create(level, true, stale, color: "black", unverified: raw);
            using Bitmap pixels = icon.ToBitmap();
            int ink = 0;
            for (int y = 5; y < 59; y++)
            for (int x = 5; x < 59; x++)
            {
                if (Math.Pow(x - 31.5, 2) + Math.Pow(y - 31.5, 2) > 27 * 27) continue;
                Color pixel = pixels.GetPixel(x, y);
                if (pixel.R < 248 || pixel.G < 248 || pixel.B < 248) continue;
                ink++;
                Require(x >= 9 && x <= 54 && y >= 14 && y <= 49,
                    $"Numeric ink outside safe region: {level}, cached={stale}, raw={raw}");
            }
            Require(ink > 0, $"No numeric glyph ink: {level}");
        }
        Console.WriteLine("PASS: 28 numeric icon ink bounds including AULA 76% and 100%");
    }

    private static void CheckIconExport()
    {
        string directory = Path.Combine(Path.GetTempPath(), "ajazz-icon-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        try
        {
            foreach (string color in TrayColorRules.AppIcons)
            {
                string path = Path.Combine(directory, color + ".ico");
                ApplicationIconAssets.Export(color, path);
                byte[] data = File.ReadAllBytes(path);
                using var loaded = new Icon(path);
                Require(loaded.Width > 0 && data.Length > 4, "Exported ICO invalid");
                bool rejected = false;
                try { ApplicationIconAssets.Export(color, path); }
                catch (IOException) { rejected = true; }
                Require(rejected && File.ReadAllBytes(path).SequenceEqual(data), "Icon export clobbered file");
            }
        }
        finally { Directory.Delete(directory, true); }
        Console.WriteLine("PASS: four ICO exports and existing-file protection");
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
        Require(form.CancelButton == Find("Close"), "Escape action must close the dashboard");
        CheckTabOrder(form, grid, buttons, hasDeviceActions: true);
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
        CheckTabOrder(form, grid, buttons, hasDeviceActions: false);
        var diagnostics = Find("Diagnostics");
        diagnostics.PerformClick();
        var diagnosticMenu = diagnostics.ContextMenuStrip!;
        diagnosticMenu.Items[1].PerformClick();
        Require(action == "telemetry", "Telemetry command missing");
        diagnosticMenu.Close();
    }

    private static void CheckTabOrder(Form form, DataGridView grid, Button[] buttons,
        bool hasDeviceActions)
    {
        var expected = hasDeviceActions ? buttons : new[] { buttons[0], buttons[3], buttons[4] };
        Control current = grid;
        grid.Select();
        foreach (Button next in expected)
        {
            Require(form.SelectNextControl(current, true, true, true, false),
                "Could not select next action");
            Require(form.ActiveControl == next, $"Incorrect keyboard order at {next.Text}");
            current = next;
        }
    }

    // Font and logical window scale stress, not a physical monitor DPI change.
    private static void CheckScaledLayout(string language, float factor)
    {
        using var form = new DeviceDashboardForm(() => { }, () => { }, () => { });
        using var font = new Font(form.Font.FontFamily, form.Font.Size * factor, form.Font.Style);
        var minimum = form.MinimumSize;
        form.Font = font;
        form.MinimumSize = new Size((int)Math.Ceiling(minimum.Width * factor),
            (int)Math.Ceiling(minimum.Height * factor));
        form.Size = form.MinimumSize;
        form.SetEntries(new[]
        {
            new DeviceDashboardForm.Entry(new("AJAZZ APEX", "2.4 GHz",
                DeviceDashboardStatus.Fresh, 72, DateTimeOffset.Now), () => { }, "usb", () => { }),
            new DeviceDashboardForm.Entry(new("AULA L99", "2.4 GHz",
                DeviceDashboardStatus.Cached, 93, DateTimeOffset.Now), Key: "aula")
        });
        form.Show();
        Application.DoEvents();
        var layout = form.Controls.OfType<TableLayoutPanel>().Single();
        var panel = layout.Controls.OfType<FlowLayoutPanel>().Single();
        var grid = layout.Controls.OfType<DataGridView>().Single();
        Require(panel.Controls.OfType<Button>().All(b => panel.ClientRectangle.Contains(b.Bounds)),
            $"Scaled actions clipped: {language} {factor}");
        Require(grid.ClientSize.Height >= grid.ColumnHeadersHeight + grid.Rows[0].Height,
            $"Scaled grid cannot display first row: {language} {factor}");
        Console.WriteLine($"PASS: {language} synthetic font/window scale {factor:P0}; not real DPI");
    }

    private static void Require(bool valid, string message)
    {
        if (!valid) throw new InvalidOperationException(message);
    }
}
