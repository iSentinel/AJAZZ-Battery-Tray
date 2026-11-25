using System.Globalization;
using System.Security;
using System.Text.Json;
using System.Threading;

namespace AjazzBatteryTray;

/// <summary>Closed operational events; no arbitrary text or device identifiers.</summary>
public enum LogEvent
{
    ApplicationStarted, ApplicationStopped, IsolatedPollingEnabled,
    HidReadFailed, DockClockTransferFailed, PreferencesReadFailed,
    PreferencesSaveFailed, AulaReadFailed, AulaQueryUnavailable,
    HistorySaveFailed, HistoryReadFailed, BleInspectionFailed,
    BleQueryFailed, BluetoothClipboardUnavailable, BlePairedLookupFailed,
    ClassicPairedLookupFailed, GattReadUnavailable, UsbInspectionFailed,
    HidCommandBlocked, HostMetricsUnavailable, AulaClipboardUnavailable,
    AulaMonitoringFailed, PnpPreviewFailed, BluetoothStatusClipboardUnavailable,
    DiagnosticsClipboardUnavailable, StartupChangeFailed, PollFailed,
    IsolatedPollTimedOut, IsolatedPollUnavailable, IsolatedClockUnavailable,
    BluetoothFallbackFailed, DockClockSucceeded, DockClockFailed,
    BatteryDisplayAvailable, BatteryDisplayCached, BatteryDisplayUnavailable
}

/// <summary>Bounded local JSONL operational journal; never exports exception text.</summary>
public static class FileLog
{
    internal const int MaxBytes = 256 * 1024;
    internal const string ActiveName = "app-events.jsonl";
    internal const string PreviousName = "app-events.previous.jsonl";
    internal const string LeaseName = "app-events.lock";
    private static long _failedWrites;

    public static string LogPath => Path.Combine(AppSettings.DirectoryPath, ActiveName);
    public static long FailedWrites => Interlocked.Read(ref _failedWrites);

    /// <summary>Best-effort logging; failed writes are counted, not retried blindly.</summary>
    public static void Write(LogEvent code, Exception? error = null)
    {
        if (!TryWriteTo(AppSettings.DirectoryPath, code, error, DateTimeOffset.UtcNow))
            Interlocked.Increment(ref _failedWrites);
    }

    internal static bool TryWriteTo(string directory, LogEvent code, Exception? error,
        DateTimeOffset timestamp, int limit = MaxBytes)
    {
        if (!Enum.IsDefined(code) || limit is < 128 or > MaxBytes) return false;
        try
        {
            byte[] payload = Encode(code, error, timestamp);
            if (payload.Length + 1 > limit) return false;
            Array.Resize(ref payload, payload.Length + 1);
            payload[^1] = (byte)'\n';
            Directory.CreateDirectory(directory);
            if ((File.GetAttributes(directory) & FileAttributes.ReparsePoint) != 0)
                return false;
            string leasePath = Path.Combine(directory, LeaseName);
            if (!SafeFile(leasePath)) return false;
            using var lease = new FileStream(leasePath, FileMode.OpenOrCreate,
                FileAccess.Write, FileShare.None);
            return Append(directory, payload, limit);
        }
        catch (Exception errorValue) when (errorValue is IOException or
            UnauthorizedAccessException or SecurityException or ArgumentException or
            NotSupportedException)
        {
            return false;
        }
    }

    private static bool Append(string directory, byte[] payload, int limit)
    {
        string active = Path.Combine(directory, ActiveName);
        string previous = Path.Combine(directory, PreviousName);
        if (!SafeFile(active) || !SafeFile(previous)) return false;
        long size = Size(active);
        if (size > limit || Size(previous) > limit) return false;
        if (size + payload.Length > limit || (size > 0 && !EndsWithLine(active)))
            File.Move(active, previous, overwrite: true);
        using var stream = new FileStream(active, FileMode.Append,
            FileAccess.Write, FileShare.Read);
        if (stream.Length + payload.Length > limit) return false;
        stream.Write(payload);
        return true;
    }

    // Preserve an interrupted tail in the previous generation, never append to it.
    private static bool EndsWithLine(string path)
    {
        using var stream = new FileStream(path, FileMode.Open, FileAccess.Read,
            FileShare.ReadWrite);
        if (stream.Length == 0) return true;
        stream.Seek(-1, SeekOrigin.End);
        return stream.ReadByte() == '\n';
    }

    private static long Size(string path) => File.Exists(path) ? new FileInfo(path).Length : 0;

    private static bool SafeFile(string path)
    {
        try
        {
            return (File.GetAttributes(path) &
                (FileAttributes.Directory | FileAttributes.ReparsePoint)) == 0;
        }
        catch (FileNotFoundException) { return true; }
        catch (DirectoryNotFoundException) { return true; }
    }

    private static byte[] Encode(LogEvent code, Exception? error, DateTimeOffset timestamp)
        => JsonSerializer.SerializeToUtf8Bytes(new
        {
            schema = 1,
            utc = timestamp.ToUniversalTime().ToString("O", CultureInfo.InvariantCulture),
            level = Severity(code),
            @event = code.ToString(),
            reason = Reason(code, error)
        });

    private static string Severity(LogEvent code) => code switch
    {
        LogEvent.ApplicationStarted or LogEvent.ApplicationStopped or
        LogEvent.IsolatedPollingEnabled or LogEvent.DockClockSucceeded or
        LogEvent.BatteryDisplayAvailable or LogEvent.BatteryDisplayCached or
        LogEvent.BatteryDisplayUnavailable or LogEvent.HostMetricsUnavailable => "INFO",
        LogEvent.PreferencesSaveFailed or LogEvent.StartupChangeFailed or
        LogEvent.PollFailed => "ERROR",
        _ => "WARN"
    };

    private static string Reason(LogEvent code, Exception? error) => error switch
    {
        null => code switch
        {
            LogEvent.IsolatedPollTimedOut => "timeout",
            LogEvent.HidCommandBlocked => "policy_denied",
            LogEvent.DockClockFailed => "unsuccessful",
            _ => "none"
        },
        UnauthorizedAccessException or SecurityException => "access_denied",
        TimeoutException => "timeout",
        OperationCanceledException => "cancelled",
        JsonException => "invalid_json",
        IOException => "io_error",
        ArgumentException => "invalid_argument",
        InvalidOperationException => "invalid_operation",
        NotSupportedException => "unsupported",
        _ => "unexpected_error"
    };
}
