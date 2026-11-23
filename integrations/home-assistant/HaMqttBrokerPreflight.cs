namespace AjazzBatteryTray;

/// <summary>Ephemeral operator inputs; no broker connection or secret storage.</summary>
public sealed record HaMqttBrokerPreflight(
    bool ExplicitlyEnabled = false,
    string BrokerHost = "",
    int BrokerPort = 8883,
    bool UseTls = true,
    bool VerifyServerCertificate = true,
    bool UseMqtt5 = true,
    string TopicPrefix = "",
    bool CredentialsSuppliedForSession = false)
{
    /// <summary>Fail closed before any future optional network transport is invoked.</summary>
    public void Validate()
    {
        if (!ExplicitlyEnabled || !UseTls || !VerifyServerCertificate || !UseMqtt5 ||
            !CredentialsSuppliedForSession)
            throw new InvalidDataException("Explicit secure MQTT session required.");
        if (BrokerPort is < 1 or > 65535 || string.IsNullOrWhiteSpace(BrokerHost) ||
            BrokerHost.Length > 253 || BrokerHost.Any(char.IsWhiteSpace) ||
            BrokerHost != BrokerHost.Trim() ||
            BrokerHost.Contains("://", StringComparison.Ordinal) ||
            Uri.CheckHostName(BrokerHost) == UriHostNameType.Unknown)
            throw new InvalidDataException("Invalid broker endpoint.");
        if (!ValidTopicPrefix(TopicPrefix))
            throw new InvalidDataException("Invalid explicit topic prefix.");
    }

    private static bool ValidTopicPrefix(string value)
    {
        if (string.IsNullOrWhiteSpace(value) || value.Length is < 3 or > 96 ||
            value[0] == '/' || value[^1] == '/' ||
            value.Contains("//", StringComparison.Ordinal) ||
            value == "homeassistant" || value.StartsWith("homeassistant/", StringComparison.Ordinal))
            return false;
        return value.All(c => c is >= 'a' and <= 'z' or >= '0' and <= '9' or '/' or '_' or '-');
    }
}
