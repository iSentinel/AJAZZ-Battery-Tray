using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Local low-battery threshold override; no device operations.</summary>
internal sealed class DeviceAlertForm : Form
{
    private readonly CheckBox _inherit = new();
    private readonly CheckBox[] _thresholds = { new(), new(), new() };
    public int? Mask => _inherit.Checked ? null :
        (_thresholds[0].Checked ? 1 : 0) | (_thresholds[1].Checked ? 2 : 0) |
        (_thresholds[2].Checked ? 4 : 0);

    public DeviceAlertForm(string name, int? existing, int globalMask)
    {
        Text = UiText.Get("Device battery alerts...");
        ClientSize = new Size(440, 300);
        MinimumSize = new Size(360, 280);
        StartPosition = FormStartPosition.CenterScreen;
        var layout = new FlowLayoutPanel
        {
            Dock = DockStyle.Fill, FlowDirection = FlowDirection.TopDown,
            WrapContents = false, AutoScroll = true, Padding = new Padding(12)
        };
        layout.Controls.Add(new Label { Text = name, AutoSize = true, MaximumSize = new Size(390, 0) });
        _inherit.Text = UiText.Get("Use global alert thresholds");
        _inherit.AutoSize = true;
        _inherit.Checked = !existing.HasValue;
        layout.Controls.Add(_inherit);
        int[] levels = { 50, 25, 10 };
        for (int i = 0; i < levels.Length; i++)
        {
            var check = _thresholds[i];
            check.AutoSize = true;
            check.Text = UiText.Format("Below {0}%", levels[i]);
            check.Checked = ((existing ?? globalMask) & (1 << i)) != 0;
            layout.Controls.Add(check);
        }
        void RefreshEnabled()
        {
            foreach (var check in _thresholds) check.Enabled = !_inherit.Checked;
        }
        _inherit.CheckedChanged += (_, _) => RefreshEnabled();
        RefreshEnabled();
        layout.Controls.Add(new Label { Text = UiText.Get("Global notification switch still applies."),
            AutoSize = true, MaximumSize = new Size(390, 0) });
        var buttons = new FlowLayoutPanel { AutoSize = true, WrapContents = false };
        var ok = new Button { Text = UiText.Get("Save"), AutoSize = true, DialogResult = DialogResult.OK };
        var cancel = new Button { Text = UiText.Get("Cancel"), AutoSize = true, DialogResult = DialogResult.Cancel };
        buttons.Controls.AddRange(new Control[] { ok, cancel });
        layout.Controls.Add(buttons);
        AcceptButton = ok;
        CancelButton = cancel;
        Controls.Add(layout);
    }
}
