using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Selectable diagnostic report with local copy/save, no network operations.</summary>
internal sealed class DiagnosticReportForm : Form
{
    public DiagnosticReportForm(string report)
    {
        Text = UiText.Get("Extended device diagnostics");
        ClientSize = new Size(840, 560);
        MinimumSize = new Size(560, 360);
        StartPosition = FormStartPosition.CenterScreen;
        TextBox content = new()
        {
            Multiline = true, ReadOnly = true, ScrollBars = ScrollBars.Both,
            WordWrap = false, Dock = DockStyle.Fill,
            Font = new Font(FontFamily.GenericMonospace, 10),
            Text = report
        };
        FlowLayoutPanel buttons = new()
        {
            Dock = DockStyle.Bottom, AutoSize = true, Padding = new Padding(8)
        };
        Button copy = new() { Text = UiText.Get("Copy report"), AutoSize = true };
        copy.Click += (_, _) => Copy(report);
        Button save = new() { Text = UiText.Get("Save report..."), AutoSize = true };
        save.Click += (_, _) => Save(report);
        Button close = new() { Text = UiText.Get("Close"), AutoSize = true };
        close.Click += (_, _) => Close();
        buttons.Controls.AddRange(new Control[] { copy, save, close });
        Controls.Add(content);
        Controls.Add(buttons);
    }

    private void Copy(string report)
    {
        try { Clipboard.SetText(report); }
        catch (Exception)
        {
            MessageBox.Show(this, UiText.Get("The Windows clipboard is currently unavailable."),
                Text, MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }

    private void Save(string report)
    {
        using SaveFileDialog dialog = new()
        {
            FileName = "ajazz-diagnostics.txt", Filter = "Text (*.txt)|*.txt",
            DefaultExt = "txt", AddExtension = true, OverwritePrompt = true
        };
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        try { File.WriteAllText(dialog.FileName, report); }
        catch (Exception)
        {
            MessageBox.Show(this, UiText.Get("Unable to save diagnostic report."),
                Text, MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }
}
