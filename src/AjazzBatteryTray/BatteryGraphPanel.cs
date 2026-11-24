using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace AjazzBatteryTray;

/// <summary>Draws battery readings without any third-party graphics library.</summary>
public sealed class BatteryGraphPanel : Panel
{
    public IReadOnlyList<BatterySample> Samples { get; set; } =
        Array.Empty<BatterySample>();

    internal DateTimeOffset PeriodEnd { get; set; } = DateTimeOffset.UtcNow;
    internal DateTimeOffset PeriodStart { get; set; } = DateTimeOffset.UtcNow.AddDays(-7);

    public BatteryGraphPanel()
    {
        DoubleBuffered = true;
        ResizeRedraw = true;
        BackColor = Color.White;
    }

    protected override void OnPaint(PaintEventArgs args)
    {
        base.OnPaint(args);
        Graphics graphics = args.Graphics;
        graphics.SmoothingMode = SmoothingMode.AntiAlias;
        Rectangle area = new(58, 22, Math.Max(1, Width - 82),
                             Math.Max(1, Height - 76));
        DrawGrid(graphics, area);
        DrawSeries(graphics, area);
    }

    private static void DrawGrid(Graphics graphics, Rectangle area)
    {
        using Pen grid = new(Color.FromArgb(221, 226, 231));
        using Brush label = new SolidBrush(Color.FromArgb(83, 94, 105));
        using Font font = new("Segoe UI", 9);
        for (int level = 0; level <= 100; level += 25)
        {
            int y = area.Bottom - (int)(area.Height * level / 100f);
            graphics.DrawLine(grid, area.Left, y, area.Right, y);
            graphics.DrawString($"{level}%", font, label, 13, y - 8);
        }
    }

    private void DrawSeries(Graphics graphics, Rectangle area)
    {
        DrawTimeLabels(graphics, area, PeriodStart, PeriodEnd);
        if (!Samples.Any(sample => sample.Percent.HasValue))
        {
            using Font font = new("Segoe UI", 11);
            graphics.DrawString(UiText.Get(Samples.Count == 0
                ? "No battery observations yet" : "No charge readings in this period"), font,
                Brushes.Gray, area.Left + 16, area.Top + 30);
            return;
        }

        double span = Math.Max(1, (PeriodEnd - PeriodStart).TotalSeconds);
        using Pen curve = new(Color.FromArgb(22, 127, 89), 2.4f);
        using Brush marker = new SolidBrush(Color.FromArgb(22, 127, 89));
        PointF? previous = null;
        DateTimeOffset previousTime = default;
        foreach (BatterySample sample in Samples)
        {
            if (!sample.Percent.HasValue)
            {
                previous = null;
                continue;
            }

            float x = area.Left + (float)(
                (sample.Timestamp - PeriodStart).TotalSeconds / span * area.Width);
            float y = area.Bottom - sample.Percent.Value / 100f * area.Height;
            PointF point = new(x, y);
            if (previous.HasValue &&
                sample.Timestamp - previousTime <= TimeSpan.FromMinutes(30))
                graphics.DrawLine(curve, previous.Value, point);

            graphics.FillEllipse(marker, x - 2.3f, y - 2.3f, 4.6f, 4.6f);
            previous = point;
            previousTime = sample.Timestamp;
        }

    }

    private void DrawTimeLabels(Graphics graphics, Rectangle area,
        DateTimeOffset start, DateTimeOffset end)
    {
        using Font font = new("Segoe UI", 9);
        using Brush brush = new SolidBrush(Color.FromArgb(83, 94, 105));
        double span = Math.Max(1, (end - start).TotalSeconds);
        for (int step = 0; step <= 4; step++)
        {
            DateTimeOffset moment = start.AddSeconds(span * step / 4);
            float x = area.Left + area.Width * step / 4f;
            string text = moment.LocalDateTime.ToString("dd MMM HH:mm");
            float width = graphics.MeasureString(text, font).Width;
            float left = Math.Clamp(x - width / 2, 0, Math.Max(0, ClientSize.Width - width));
            graphics.DrawString(text, font, brush, left, area.Bottom + 12);
        }
    }
}
