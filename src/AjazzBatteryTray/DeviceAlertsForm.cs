using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Local notification settings for one monitored receiver or profile.</summary>
internal sealed class DeviceAlertsForm : Form
{
    private readonly CheckBox _inherit = new();
    private readonly CheckBox _below50 = new();
    private readonly CheckBox _below25 = new();
    private readonly CheckBox _below10 = new();
    private readonly CheckBox _disconnect = new();
    private readonly DeviceAlertPreferences _defaults;

    internal DeviceAlertPreferences? Choice => _inherit.Checked ? null :
        new(_below50.Checked, _below25.Checked, _below10.Checked, _disconnect.Checked);

    internal DeviceAlertsForm(string name, DeviceAlertPreferences defaults,
        DeviceAlertPreferences? current)
    {
        _defaults = defaults;
        Text = UiText.Get("Device notifications...");
        ClientSize = new Size(540, 340);
        MinimumSize = new Size(460, 340);
        StartPosition = FormStartPosition.CenterScreen;
        FlowLayoutPanel layout = new()
        {
            Dock = DockStyle.Fill, FlowDirection = FlowDirection.TopDown,
            WrapContents = false, AutoScroll = true, Padding = new Padding(12)
        };
        layout.Controls.Add(new Label { Text = name, AutoSize = true });
        Configure(_inherit, "Use global notification defaults", current is null);
        Configure(_below50, "Notify below 50%", false);
        Configure(_below25, "Notify below 25%", false);
        Configure(_below10, "Notify below 10%", false);
        Configure(_disconnect, "Notify on receiver disconnect", false);
        foreach (CheckBox check in new[] { _inherit, _below50, _below25, _below10, _disconnect })
            layout.Controls.Add(check);
        layout.Controls.Add(new Label
        {
            Text = UiText.Get("The global low-battery switch still applies."),
            AutoSize = true, MaximumSize = new Size(450, 0)
        });
        FlowLayoutPanel actions = new() { AutoSize = true };
        Button save = new() { Text = UiText.Get("Save"), AutoSize = true, DialogResult = DialogResult.OK };
        Button cancel = new() { Text = UiText.Get("Cancel"), AutoSize = true, DialogResult = DialogResult.Cancel };
        actions.Controls.Add(save);
        actions.Controls.Add(cancel);
        layout.Controls.Add(actions);
        Controls.Add(layout);
        AcceptButton = save;
        CancelButton = cancel;
        SetValues(current ?? defaults);
        _inherit.CheckedChanged += (_, _) =>
        {
            if (_inherit.Checked) SetValues(_defaults);
            UpdateEnabled();
        };
        UpdateEnabled();
    }

    private static void Configure(CheckBox check, string label, bool value)
    {
        check.Text = UiText.Get(label);
        check.AutoSize = true;
        check.Checked = value;
    }

    private void SetValues(DeviceAlertPreferences values)
    {
        _below50.Checked = values.Below50;
        _below25.Checked = values.Below25;
        _below10.Checked = values.Below10;
        _disconnect.Checked = values.NotifyOnDisconnect;
    }

    private void UpdateEnabled()
    {
        foreach (CheckBox check in new[] { _below50, _below25, _below10, _disconnect })
            check.Enabled = !_inherit.Checked;
    }
}
