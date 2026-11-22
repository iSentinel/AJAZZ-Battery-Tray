using System.Drawing;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Select a local normal-charge color with warning examples.</summary>
internal sealed class TrayColorForm : Form
{
    private readonly ComboBox _choices = new();
    private readonly FlowLayoutPanel _preview = new();
    internal string Choice { get; private set; }

    internal TrayColorForm(string name, string current)
    {
        Choice = TrayColorRules.Normalize(current);
        Text = UiText.Get("Tray icon color...");
        ClientSize = new Size(510, 225);
        MinimumSize = new Size(440, 260);
        StartPosition = FormStartPosition.CenterScreen;
        TableLayoutPanel layout = new()
        {
            Dock = DockStyle.Fill, Padding = new Padding(12),
            ColumnCount = 1, RowCount = 5
        };
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        layout.Controls.Add(new Label { Text = name, AutoSize = true }, 0, 0);
        _choices.DropDownStyle = ComboBoxStyle.DropDownList;
        _choices.Dock = DockStyle.Top;
        foreach (string color in TrayColorRules.Choices)
            _choices.Items.Add(UiText.Get("Tray color " + color));
        _choices.SelectedIndex = Array.IndexOf(TrayColorRules.Choices.ToArray(), Choice);
        layout.Controls.Add(_choices, 0, 1);
        _preview.Dock = DockStyle.Fill;
        _preview.WrapContents = false;
        layout.Controls.Add(_preview, 0, 2);
        layout.Controls.Add(new Label
        {
            Text = UiText.Get("Warning and cached colors are unchanged."),
            AutoSize = true
        }, 0, 3);
        FlowLayoutPanel actions = new() { Dock = DockStyle.Fill, AutoSize = true };
        Button save = new() { Text = UiText.Get("Save"), DialogResult = DialogResult.OK, AutoSize = true };
        Button cancel = new() { Text = UiText.Get("Cancel"), DialogResult = DialogResult.Cancel, AutoSize = true };
        actions.Controls.Add(save);
        actions.Controls.Add(cancel);
        layout.Controls.Add(actions, 0, 4);
        Controls.Add(layout);
        AcceptButton = save;
        CancelButton = cancel;
        _choices.SelectedIndexChanged += (_, _) =>
        {
            if (_choices.SelectedIndex < 0) return;
            Choice = TrayColorRules.Choices[_choices.SelectedIndex];
            RefreshPreview();
        };
        RefreshPreview();
    }

    private void RefreshPreview()
    {
        foreach (Control old in _preview.Controls.Cast<Control>().ToArray())
        {
            if (old is PictureBox picture) picture.Image?.Dispose();
            old.Dispose();
        }
        _preview.Controls.Clear();
        foreach (var sample in new[] { (80, false), (15, false), (8, false), (80, true) })
        {
            using Icon icon = TrayIconFactory.Create(sample.Item1, true, sample.Item2, color: Choice);
            _preview.Controls.Add(new PictureBox
            {
                Width = 52, Height = 52, SizeMode = PictureBoxSizeMode.Zoom,
                Image = icon.ToBitmap(), Margin = new Padding(4, 10, 4, 4)
            });
        }
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
            foreach (PictureBox picture in _preview.Controls.OfType<PictureBox>())
                picture.Image?.Dispose();
        base.Dispose(disposing);
    }
}
