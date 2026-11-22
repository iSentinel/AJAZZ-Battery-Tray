using Microsoft.Win32.SafeHandles;

namespace AjazzBatteryTray;

/// <summary>One L99 dongle poll, independent from AJAZZ receiver state.</summary>
public sealed record AulaL99Reading(
    bool ReceiverPresent, int? Percent, string Details, bool PresenceKnown = true);

/// <summary>Opt-in battery-only polling of the known AULA L99 2.4 GHz interface.</summary>
public sealed class AulaL99Reader
{
    /// <summary>Only called for a manual read or when the user opted in.</summary>
    public async Task<AulaL99Reading> ReadAsync()
    {
        try
        {
            IReadOnlyList<string> paths = HidNative.FindAulaL99Paths();
            if (paths.Count == 0)
                return new(false, null, "2.4 GHz dongle not found");

            foreach (string path in paths)
            {
                int? level = await QueryPathAsync(path);
                if (level.HasValue)
                    return new(true, level, "Fresh 2.4 GHz battery reply");

                // One bounded retry using only the same approved battery query.
                await Task.Delay(150);
                level = await QueryPathAsync(path);
                if (level.HasValue)
                    return new(true, level, "Fresh 2.4 GHz battery reply after retry");
            }

            return new(true, null, "Receiver present; keyboard asleep or no valid reply");
        }
        catch (Exception error)
        {
            FileLog.Write("WARN", "AULA L99 read failed: " + error.GetType().Name);
            return new(false, null, "HID enumeration error", PresenceKnown: false);
        }
    }

    private static async Task<int?> QueryPathAsync(string path)
    {
        using SafeFileHandle handle = HidNative.OpenOverlapped(path);
        if (handle.IsInvalid || !HidNative.TryGetCaps(handle, out var caps) ||
            !AulaL99Protocol.MatchesCaps(caps.UsagePage,
                caps.InputReportByteLength, caps.OutputReportByteLength))
            return null;

        // No generic HID command API: this method can send battery query only.
        byte[] request = AulaL99Protocol.BatteryRequest();
        if (!AulaL99Protocol.IsApprovedRequest(request)) return null;
        try
        {
            using FileStream stream = new(handle, FileAccess.ReadWrite,
                AulaL99Protocol.ReportLength, isAsync: true);
            using CancellationTokenSource timeout = new(
                TimeSpan.FromMilliseconds(900));
            await stream.WriteAsync(request, timeout.Token);
            byte[] response = new byte[AulaL99Protocol.ReportLength];
            while (!timeout.IsCancellationRequested)
            {
                int count = await stream.ReadAsync(response, timeout.Token);
                if (count == 0) break;
                int? level = AulaL99Protocol.ParseBatteryReply(
                    response.AsSpan(0, count));
                if (level.HasValue) return level;
            }
        }
        catch (OperationCanceledException) { /* Sleeping keyboards do not answer. */ }
        catch (Exception error) when (error is IOException or UnauthorizedAccessException)
        {
            FileLog.Write("WARN", "AULA L99 battery query unavailable: " +
                error.GetType().Name);
        }
        return null;
    }
}
