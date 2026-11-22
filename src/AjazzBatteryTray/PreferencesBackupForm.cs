using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Local export and validated preview; never changes active preferences.</summary>
internal sealed class PreferencesBackupForm : Form
{
    private readonly AppSettings _settings;
    private readonly TextBox _preview = new() { Multiline = true, ReadOnly = true,
        ScrollBars = ScrollBars.Vertical, Width = 450, Height = 270 };

    internal PreferencesBackupForm(AppSettings settings)
    {
        _settings = settings;
        Text = UiText.Get("Preferences backup...");
        StartPosition = FormStartPosition.CenterScreen;
        AutoSize = true;
        AutoSizeMode = AutoSizeMode.GrowAndShrink;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = MinimizeBox = false;
        var panel = new FlowLayoutPanel { AutoSize = true, Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.TopDown, WrapContents = false, Padding = new Padding(14) };
        panel.Controls.Add(new Label { AutoSize = true, MaximumSize = new Size(450, 0),
            Text = UiText.Get("Global preferences only. Preview does not apply settings.") });
        var export = new Button { AutoSize = true, Text = UiText.Get("Export preferences...") };
        export.Click += (_, _) => Export();
        var preview = new Button { AutoSize = true, Text = UiText.Get("Preview backup...") };
        preview.Click += (_, _) => Preview();
        var close = new Button { AutoSize = true, Text = UiText.Get("Close") };
        close.Click += (_, _) => Close();
        panel.Controls.AddRange(new Control[] { export, preview, _preview, close });
        Controls.Add(panel);
        ShowPreview(PreferencesBackup.Capture(settings));
    }

    private void Export()
    {
        using var dialog = new SaveFileDialog { Filter = "JSON (*.json)|*.json",
            FileName = "ajazz-preferences.json", DefaultExt = "json", AddExtension = true,
            RestoreDirectory = true, OverwritePrompt = true };
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        try
        {
            PreferencesBackup.Capture(_settings).WriteNewFile(dialog.FileName);
            MessageBox.Show(this, UiText.Get("Preferences exported."), Text);
        }
        catch (Exception)
        {
            MessageBox.Show(this, UiText.Get("Export failed. Select a new file name."), Text,
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private void Preview()
    {
        using var dialog = new OpenFileDialog { Filter = "JSON (*.json)|*.json",
            RestoreDirectory = true, CheckFileExists = true, Multiselect = false,
            DereferenceLinks = false };
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        try { ShowPreview(PreferencesBackup.ReadFile(dialog.FileName)); }
        catch (Exception)
        {
            _preview.Text = UiText.Get("Invalid or unsupported preferences backup.");
        }
    }

    private void ShowPreview(PreferencesBackup value)
    {
        string Format(string key, bool flag) => UiText.Get(key) + ": " +
            UiText.Get(flag ? "Enabled" : "Disabled");
        _preview.Lines = new[] {
            UiText.Get("Validated global preferences"),
            UiText.Get("Language") + ": " + value.Language,
            UiText.Get("Update interval") + ": " + value.PollSeconds + " s",
            Format("Low battery notifications", value.NotificationsEnabled),
            Format("Below 50%", value.AlertBelow50),
            Format("Below 25%", value.AlertBelow25),
            Format("Below 10%", value.AlertBelow10),
            Format("Record battery history", value.RecordBatteryHistory),
            Format("Notify on receiver disconnect", value.NotifyOnDisconnect),
            Format("Separate tray icons", value.MultipleTrayIcons),
            "",
            UiText.Get("No settings have been changed.")
        };
    }
}
