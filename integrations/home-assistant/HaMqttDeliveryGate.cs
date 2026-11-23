using System.Globalization;

namespace AjazzBatteryTray;

/// <summary>Optional transport gate: never advance without a QoS1 acknowledgment.</summary>
public static class HaMqttDeliveryGate
{
    public static async Task<bool> PublishAsync(IReadOnlyList<HaMqttMessage> plan,
        Func<HaMqttMessage, CancellationToken, Task<bool>> send,
        CancellationToken cancellationToken)
    {
        Validate(plan);
        ArgumentNullException.ThrowIfNull(send);
        foreach (var message in plan)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (!await send(message, cancellationToken).ConfigureAwait(false))
                return false;
        }
        return true;
    }

    private static void Validate(IReadOnlyList<HaMqttMessage> plan)
    {
        if (plan is not { Count: 2 } || plan.Any(x => x.Qos != 1))
            throw new InvalidDataException("Invalid MQTT publication plan.");
        var first = plan[0];
        var second = plan[1];
        bool offline = first is { TopicSuffix: "availability", Payload: "offline",
            Retain: true, ExpirySeconds: null } && second is { TopicSuffix: "battery",
            Payload: "", Retain: true, ExpirySeconds: null };
        bool fresh = first is { TopicSuffix: "battery", Retain: false } &&
            second is { TopicSuffix: "availability", Payload: "online", Retain: true } &&
            first.ExpirySeconds is >= 1 and <= HaMqttAvailabilityPolicy.FreshExpirySeconds &&
            second.ExpirySeconds == first.ExpirySeconds &&
            int.TryParse(first.Payload, NumberStyles.None, CultureInfo.InvariantCulture,
                out int percent) && percent is >= 0 and <= 100 &&
            first.Payload == percent.ToString(CultureInfo.InvariantCulture);
        if (!offline && !fresh)
            throw new InvalidDataException("Invalid MQTT publication ordering or payload.");
    }
}
