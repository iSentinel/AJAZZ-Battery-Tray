namespace AjazzBatteryTray;

/// <summary>Bounded matrix of existing battery query lengths and delays.</summary>
public static class ApexProtocolMatrix
{
    public static IReadOnlyList<(int Length, int DelayMs)> Build(int descriptorLength,
        bool fullCapture)
    {
        int[] delays = fullCapture ? new[] { 30, 100, 250 } : new[] { 30 };
        return delays.SelectMany(delay => new[] { descriptorLength, 65, 67 }
            .Distinct().Where(length => length is >= 65 and <= 256)
            .Select(length => (length, delay))).ToArray();
    }
    /// <summary>Explicit diagnostic only: pair the existing and bridge GET IDs.</summary>
    public static IReadOnlyList<(int Length, int DelayMs, byte ReportId)> CompareGetIds(
        int descriptorLength) => Build(descriptorLength, true)
            .SelectMany(probe => new byte[] { 0x05, 0x00 }
                .Select(id => (probe.Length, probe.DelayMs, id))).ToArray();
}
