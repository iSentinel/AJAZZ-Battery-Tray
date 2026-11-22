using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Local export, validated preview and explicit restore selection.</summary>
internal sealed class PreferencesBackupForm : Form
{
    private readonly AppSettings _settings;
    private readonly Button _restore = new() { AutoSize = true, Enabled = false };
    private PreferencesBackup? _selected;
    internal PreferencesBackup? SelectedBackup { get; private set; }
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
        _restore.Text = UiText.Get("Restore previewed preferences...");
        _restore.Click += (_, _) => ConfirmRestore();
        var close = new Button { AutoSize = true, Text = UiText.Get("Close") };
        close.Click += (_, _) => Close();
        panel.Controls.AddRange(new Control[] { export, preview, _preview, _restore, close });
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
        _selected = null;
        _restore.Enabled = false;
        try
        {
            _selected = PreferencesBackup.ReadFile(dialog.FileName);
            ShowPreview(_selected);
            _restore.Enabled = true;
        }
        catch (Exception)
        {
            _preview.Text = UiText.Get("Invalid or unsupported preferences backup.");
        }
    }

    private void ConfirmRestore()
    {
        if (_selected is null) return;
        if (MessageBox.Show(this, UiText.Get("Replace global preferences with the previewed values? Existing device settings and update consent are preserved. Notification preferences may resume already authorized checks."),
            Text, MessageBoxButtons.YesNo, MessageBoxIcon.Question,
            MessageBoxDefaultButton.Button2) != DialogResult.Yes) return;
        SelectedBackup = _selected;
        DialogResult = DialogResult.OK;
        Close();
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
            UiText.Format("Below {0}%", 50) + ": " + UiText.Get(value.AlertBelow50 ? "Enabled" : "Disabled"),
            UiText.Format("Below {0}%", 25) + ": " + UiText.Get(value.AlertBelow25 ? "Enabled" : "Disabled"),
            UiText.Format("Below {0}%", 10) + ": " + UiText.Get(value.AlertBelow10 ? "Enabled" : "Disabled"),
            Format("Record battery history", value.RecordBatteryHistory),
            Format("Notify on receiver disconnect", value.NotifyOnDisconnect),
            Format("Separate tray icons", value.MultipleTrayIcons),
            "",
            UiText.Get("No settings have been changed.")
        };
    }
}
