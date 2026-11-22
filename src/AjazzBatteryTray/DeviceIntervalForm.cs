using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Choose a local sampling interval override; no hardware writes.</summary>
internal sealed class DeviceIntervalForm : Form
{
    private readonly ComboBox _choices = new() { DropDownStyle = ComboBoxStyle.DropDownList, Width = 280 };
    private static readonly int[] Seconds = { 15, 30, 60, 120 };
    public int? Interval => _choices.SelectedIndex <= 0 ? null : Seconds[_choices.SelectedIndex - 1];

    internal DeviceIntervalForm(string name, int? existing, int global)
    {
        Text = UiText.Get("Device polling interval...");
        ClientSize = new Size(455, 220);
        MinimumSize = new Size(400, 210);
        StartPosition = FormStartPosition.CenterScreen;
        var layout = new FlowLayoutPanel { Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.TopDown, WrapContents = false,
            AutoScroll = true, Padding = new Padding(12) };
        layout.Controls.Add(new Label { Text = name, AutoSize = true, MaximumSize = new Size(405, 0) });
        _choices.Items.Add(UiText.Format("Use global interval ({0} seconds)", global));
        foreach (int seconds in Seconds) _choices.Items.Add(UiText.Format("{0} seconds", seconds));
        _choices.SelectedIndex = existing is int value ? Array.IndexOf(Seconds, value) + 1 : 0;
        layout.Controls.Add(_choices);
        var actions = new FlowLayoutPanel { AutoSize = true, WrapContents = false };
        var save = new Button { Text = UiText.Get("Save"), AutoSize = true, DialogResult = DialogResult.OK };
        var cancel = new Button { Text = UiText.Get("Cancel"), AutoSize = true, DialogResult = DialogResult.Cancel };
        actions.Controls.AddRange(new Control[] { save, cancel });
        layout.Controls.Add(actions);
        AcceptButton = save;
        CancelButton = cancel;
        Controls.Add(layout);
    }
}
