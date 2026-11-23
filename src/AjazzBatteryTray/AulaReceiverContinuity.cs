namespace AjazzBatteryTray;

/// <summary>
/// Keep the last confirmed AULA identity across uncertain USB enumeration.
/// Never expose a cached reading for an unconfirmed receiver.
/// </summary>
public sealed class AulaReceiverContinuity
{
    private string? _confirmedKey;

    /// <summary>True when a confirmed change or absence must clear cached data.</summary>
    public bool MustReset(bool known, bool present, string? localKey)
    {
        // An ambiguous enumeration is not proof that a receiver was removed.
        if (!known) return false;
        if (!present || string.IsNullOrWhiteSpace(localKey))
        {
            _confirmedKey = null;
            return true;
        }

        if (_confirmedKey is null)
        {
            _confirmedKey = localKey;
            return false;
        }

        if (StringComparer.Ordinal.Equals(_confirmedKey, localKey)) return false;
        _confirmedKey = localKey;
        return true;
    }

    /// <summary>Explicit opt-out/identity reset clears the continuity guard.</summary>
    public void Reset() => _confirmedKey = null;
}
