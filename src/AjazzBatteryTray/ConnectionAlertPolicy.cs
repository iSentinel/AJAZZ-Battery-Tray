namespace AjazzBatteryTray;

/// <summary>Alerts once after two absent polls, but only after a real connection.</summary>
public sealed class ConnectionAlertPolicy
{
    private bool _seenOnline;
    private bool _alerted;
    private int _missingPolls;

    /// <summary>Unknown discovery interrupts consecutive absence, not connection history.</summary>
    public void ObserveUnknown() => _missingPolls = 0;

    public bool Evaluate(bool connected, bool receiverPresent)
    {
        if (connected)
        {
            _seenOnline = true;
            _missingPolls = 0;
            _alerted = false;
            return false;
        }

        if (receiverPresent)
        {
            _missingPolls = 0;
            return false;
        }

        if (_missingPolls < 2) _missingPolls++;
        if (!_seenOnline || _alerted || _missingPolls < 2) return false;
        _alerted = true;
        return true;
    }
}
