namespace AjazzBatteryTray;

/// <summary>Reusable per-pass identity sets without stale retained keys.</summary>
internal sealed class InventoryFrameScratch
{
    private readonly HashSet<string> _seen = new(StringComparer.Ordinal);
    private readonly List<string> _missing = new();

    internal IEnumerable<string> Keys => _seen;

    /// <summary>Begin an independent inventory or icon reconciliation.</summary>
    internal void Begin()
    {
        _seen.Clear();
        _missing.Clear();
    }

    internal void Add(string key) => _seen.Add(key);

    internal bool Contains(string key) => _seen.Contains(key);

    /// <summary>Capture missing keys before callers mutate their source dictionary.</summary>
    internal IReadOnlyList<string> Missing(IEnumerable<string> current)
    {
        _missing.Clear();
        foreach (string key in current)
            if (!_seen.Contains(key)) _missing.Add(key);
        return _missing;
    }

    /// <summary>Release identity references, including after an exception.</summary>
    internal void End()
    {
        _seen.Clear();
        _missing.Clear();
    }
}
