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
        save.Click += (_, _) => PromptSave(report, this);
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

    internal static bool PromptSave(string report, IWin32Window? owner = null)
    {
        using SaveFileDialog dialog = new()
        {
            FileName = $"ajazz-diagnostics-{DateTime.Now:yyyyMMdd-HHmmss}.txt",
            Filter = UiText.Get("Text files (*.txt)") + "|*.txt",
            DefaultExt = "txt", AddExtension = true, OverwritePrompt = true
        };
        if (dialog.ShowDialog(owner) != DialogResult.OK) return false;
        try
        {
            File.WriteAllText(dialog.FileName, report);
            return true;
        }
        catch (Exception)
        {
            MessageBox.Show(owner, UiText.Get("Unable to save diagnostic report."),
                "AJAZZ Battery Tray", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return false;
        }
    }
}
