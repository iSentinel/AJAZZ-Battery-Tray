namespace AjazzBatteryTray;

/// <summary>Value-type key for the pixels drawn by TrayIconFactory, not the tooltip.</summary>
public readonly record struct TrayIconRenderKey(bool Neutral, int? Level, bool Stale, int Background, bool Mouse = false, string? Brand = null, bool Unverified = false)
{
    public static TrayIconRenderKey Create(int? level, bool connected, bool stale,
        bool neutral = false, string? color = null, bool mouseStyle = false, string? brand = null, bool unverified = false)
    {
        if (neutral) return new(true, null, false, 0, Brand: TrayColorRules.NormalizeAppIcon(brand));
        int? numeric = TrayColorRules.NumericLevel(level, connected);
        bool mouse = TrayColorRules.ShowMouse(level, connected, stale || unverified, mouseStyle);
        return new(false, mouse ? null : numeric, numeric.HasValue && stale,
            TrayColorRules.Resolve(level, connected, stale || unverified, color), mouse,
            Unverified: numeric.HasValue && unverified);
    }
}
