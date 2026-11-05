using System.Drawing;
using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;

namespace AjazzBatteryTray;

/// <summary>Draws a crisp status icon without shipping external graphics.</summary>
public static class TrayIconFactory
{
    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool DestroyIcon(IntPtr icon);

    public static Icon Create(int? level, bool connected)
    {
        using Bitmap image = new(64, 64);
        using (Graphics graphics = Graphics.FromImage(image))
        {
            graphics.SmoothingMode = SmoothingMode.AntiAlias;
            graphics.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
            Color background = !connected ? Color.FromArgb(110, 118, 130) :
                level <= 10 ? Color.FromArgb(220, 53, 69) :
                level <= 20 ? Color.FromArgb(225, 145, 18) :
                Color.FromArgb(27, 151, 103);
            using Brush fill = new SolidBrush(background);
            graphics.FillEllipse(fill, 2, 2, 60, 60);
            string text = connected && level is not null ? level.ToString()! : "?";
            float size = text.Length >= 3 ? 25 : 33;
            using Font font = new("Segoe UI", size, FontStyle.Bold, GraphicsUnit.Pixel);
            using StringFormat alignment = new()
            {
                Alignment = StringAlignment.Center,
                LineAlignment = StringAlignment.Center
            };
            graphics.DrawString(text, font, Brushes.White,
                new RectangleF(1, -1, 62, 64), alignment);
        }

        IntPtr handle = image.GetHicon();
        try
        {
            return (Icon)Icon.FromHandle(handle).Clone();
        }
        finally
        {
            DestroyIcon(handle);
        }
    }
}
