namespace AjazzBatteryTray;

/// <summary>Value-type key for the pixels drawn by TrayIconFactory, not the tooltip.</summary>
public readonly record struct TrayIconRenderKey(bool Neutral, int? Level, bool Stale, int Background)
{
    public static TrayIconRenderKey Create(int? level, bool connected, bool stale,
        bool neutral = false, string? color = null)
    {
        if (neutral) return new(true, null, false, 0);
        bool numeric = connected && level.HasValue;
        return new(false, numeric ? level : null, numeric && stale,
            TrayColorRules.Resolve(level, connected, stale, color));
    }
}
