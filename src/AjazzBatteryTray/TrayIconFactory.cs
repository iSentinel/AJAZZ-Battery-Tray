using System.Drawing;
using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;

namespace AjazzBatteryTray;

/// <summary>Draws a crisp status icon without shipping external graphics.</summary>
public static class TrayIconFactory
{
    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool DestroyIcon(IntPtr icon);

    public static Icon Create(int? level, bool connected, bool stale = false, bool neutral = false, string? color = null, bool mouseStyle = false, string? brand = null)
    {
        if (neutral) return ApplicationIconAssets.Load(brand);
        using Bitmap image = new(64, 64);
        using (Graphics graphics = Graphics.FromImage(image))
        {
            graphics.SmoothingMode = SmoothingMode.AntiAlias;
            graphics.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
            Color background = Color.FromArgb(unchecked((int)0xFF000000) |
                TrayColorRules.Resolve(level, connected, stale, color));
            if (TrayColorRules.ShowMouse(level, connected, stale, mouseStyle))
                DrawMouse(graphics, background);
            else DrawNumber(graphics, background, TrayColorRules.NumericLevel(level, connected), stale);
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

    private static void DrawMouse(Graphics graphics, Color color)
    {
        using var shape = new GraphicsPath();
        shape.AddArc(9, 3, 46, 44, 180, 180);
        shape.AddLine(55, 25, 55, 36);
        shape.AddArc(9, 18, 46, 42, 0, 180);
        shape.CloseFigure();
        using var fill = new SolidBrush(color);
        using var border = new Pen(Color.FromArgb(235, 235, 235), 4);
        using var inner = new Pen(Color.FromArgb(35, 38, 42), 3);
        graphics.FillPath(fill, shape);
        graphics.DrawPath(border, shape);
        graphics.DrawLine(inner, 10, 28, 54, 28);
        graphics.DrawLine(inner, 32, 5, 32, 28);
        graphics.FillRectangle(Brushes.DimGray, 28, 10, 8, 13);
    }

    private static void DrawNumber(Graphics graphics, Color background, int? level, bool stale)
    {
            using Brush fill = new SolidBrush(background);
            graphics.FillEllipse(fill, 2, 2, 60, 60);
            using var border = new Pen(Color.FromArgb(230, 230, 230), 2);
            graphics.DrawEllipse(border, 2, 2, 60, 60);
            string text = level is not null ? level.ToString()! + "%" + (stale ? "*" : "") : "?";
            float size = text.Length >= 5 ? 17 : text.Length >= 4 ? 21 : text.Length >= 3 ? 27 : 33;
            using Font font = new("Segoe UI", size, FontStyle.Bold, GraphicsUnit.Pixel);
            using StringFormat alignment = new()
            {
                Alignment = StringAlignment.Center,
                LineAlignment = StringAlignment.Center
            };
            Brush foreground = background.GetBrightness() > 0.72f ? Brushes.Black : Brushes.White;
            graphics.DrawString(text, font, foreground,
                new RectangleF(1, -1, 62, 64), alignment);
    }
}
