using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Local display name editor; empty value restores the detected label.</summary>
internal sealed class DeviceAliasForm : Form
{
    private readonly TextBox _name = new();
    internal string Alias { get; private set; } = "";

    internal DeviceAliasForm(string model, string? current)
    {
        Text = UiText.Get("Edit local name...");
        ClientSize = new Size(480, 190);
        MinimumSize = new Size(420, 220);
        StartPosition = FormStartPosition.CenterScreen;
        TableLayoutPanel layout = new()
        {
            Dock = DockStyle.Fill, Padding = new Padding(12), ColumnCount = 1,
            RowCount = 4
        };
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.Controls.Add(new Label { Text = model, AutoSize = true }, 0, 0);
        _name.Dock = DockStyle.Top;
        _name.MaxLength = DeviceAliasRules.MaxLength;
        _name.Text = current ?? "";
        layout.Controls.Add(_name, 0, 1);
        layout.Controls.Add(new Label
        {
            Text = UiText.Get("Local name only. Clear to restore the detected name."),
            Dock = DockStyle.Fill
        }, 0, 2);
        FlowLayoutPanel buttons = new() { Dock = DockStyle.Fill, AutoSize = true };
        Button save = new() { Text = UiText.Get("Save local name"), AutoSize = true };
        Button cancel = new() { Text = UiText.Get("Cancel"), DialogResult = DialogResult.Cancel,
            AutoSize = true };
        save.Click += (_, _) => SaveName();
        buttons.Controls.Add(save);
        buttons.Controls.Add(cancel);
        layout.Controls.Add(buttons, 0, 3);
        Controls.Add(layout);
        AcceptButton = save;
        CancelButton = cancel;
    }

    private void SaveName()
    {
        if (!DeviceAliasRules.TryNormalize(_name.Text, out string alias))
        {
            MessageBox.Show(this, UiText.Get("Invalid local device name."),
                Text, MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        Alias = alias;
        DialogResult = DialogResult.OK;
        Close();
    }
}
