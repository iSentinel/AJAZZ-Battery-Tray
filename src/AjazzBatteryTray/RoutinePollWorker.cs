using System.Diagnostics;
using System.Text;
using System.Text.Json;

namespace AjazzBatteryTray;

/// <summary>Supervisor for the opt-in routine AJAZZ read and clock workers.</summary>
internal static class RoutinePollWorker
{
    private const string ReadMode = "--internal-routine-hid-worker";
    private const string ClockMode = "--internal-routine-clock-worker";
    private const string ClockSampleMode = "--internal-routine-clock-sample";
    private const string SampleMode = "--internal-routine-hid-sample";
    private const string HangMode = "--internal-routine-hid-hang";
    private const int MaxKeys = 128;
    private const int MaxReplyChars = 2 * 1024 * 1024;
    private const int ChildLimitSeconds = 12;
    private static int _active;

    internal static bool IsWorker(string mode) => mode is ReadMode or SampleMode or HangMode or ClockMode or ClockSampleMode;

    private static string[] ValidateKeys(string[]? keys)
    {
        if (keys is null || keys.Length > MaxKeys ||
            keys.Any(key => key == DeviceAliasRules.AulaSlot || !DeviceAliasRules.ValidKey(key)) ||
            keys.Distinct(StringComparer.Ordinal).Count() != keys.Length)
            throw new InvalidDataException("Invalid routine worker deferred keys");
        return keys;
    }

    private static void Stop(Process child)
    {
        try { child.Kill(entireProcessTree: true); }
        catch (InvalidOperationException) { /* Child already exited. */ }
        catch (System.ComponentModel.Win32Exception) { /* Child watchdog remains active. */ }
    }

    internal static Task<AjazzHidReader.Batch> ReadAsync(
        string[] deferred, CancellationToken closing, string mode = ReadMode)
        => InvokeAsync<AjazzHidReader.Batch>(deferred, closing, mode);

    internal static Task<bool> SyncClockAsync(CancellationToken closing)
        => InvokeAsync<bool>(Array.Empty<string>(), closing, ClockMode);

    private static async Task<T> InvokeAsync<T>(
        string[] deferred, CancellationToken closing, string mode)
    {
        ValidateKeys(deferred);
        closing.ThrowIfCancellationRequested();
        if (Interlocked.CompareExchange(ref _active, 1, 0) != 0)
            throw new InvalidOperationException("Routine HID worker already active");
        try { return await ExchangeAsync<T>(deferred, closing, mode).ConfigureAwait(false); }
        finally { Volatile.Write(ref _active, 0); }
    }

    private static async Task<T> ExchangeAsync<T>(
        string[] deferred, CancellationToken closing, string mode)
    {
        ProcessStartInfo start = new(Environment.ProcessPath!)
        {
            UseShellExecute = false, CreateNoWindow = true,
            RedirectStandardInput = true, RedirectStandardOutput = true,
            StandardOutputEncoding = Encoding.UTF8, StandardInputEncoding = new UTF8Encoding(false)
        };
        start.ArgumentList.Add(mode);
        using Process child = Process.Start(start) ?? throw new IOException("Worker start failed");
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(closing);
        deadline.CancelAfter(TimeSpan.FromSeconds(mode == HangMode ? 2 : 8));
        using var stop = deadline.Token.Register(() => Stop(child));
        Task<string> output = child.StandardOutput.ReadToEndAsync();
        try
        {
            await child.StandardInput.WriteLineAsync(JsonSerializer.Serialize(deferred))
                .ConfigureAwait(false);
            child.StandardInput.Close();
            await child.WaitForExitAsync().ConfigureAwait(false);
            return Decode<T>(await output.ConfigureAwait(false), child.ExitCode, deadline, closing);
        }
        catch (IOException) when (deadline.IsCancellationRequested)
        {
            closing.ThrowIfCancellationRequested();
            throw new TimeoutException();
        }
        finally
        {
            // Do not release the in-process gate until the child has actually exited.
            if (!child.HasExited) Stop(child);
            await child.WaitForExitAsync().ConfigureAwait(false);
        }
    }

    private static T Decode<T>(string body, int code,
        CancellationTokenSource deadline, CancellationToken closing)
    {
        closing.ThrowIfCancellationRequested();
        if (deadline.IsCancellationRequested || code == 124) throw new TimeoutException();
        if (code != 0) throw new IOException("Routine HID worker failed");
        if (body.Length > MaxReplyChars)
            throw new InvalidDataException("Oversized routine worker reply");
        T? result = JsonSerializer.Deserialize<T>(body);
        if (result is null) throw new InvalidDataException("Missing routine worker response");
        if (result is AjazzHidReader.Batch batch) ValidateBatch(batch);
        return result;
    }

    private static bool ValidReading(AjazzHidReader.Reading? reading)
        => reading is not null && reading.Details is not null &&
            Enum.IsDefined(reading.Issue) &&
            (reading.Percent is null || (reading.PresenceKnown && reading.ReceiverPresent &&
                reading.Percent is >= 1 and <= 100)) &&
            (reading.UnverifiedPercent is null || (reading.PresenceKnown && reading.ReceiverPresent &&
                reading.Percent is null && reading.Issue == UsbReadIssue.None &&
                reading.UnverifiedPercent is >= 1 and <= 100)) &&
            (reading.PresenceKnown || !reading.ReceiverPresent);

    private static void ValidateBatch(AjazzHidReader.Batch batch)
    {
        if (!ValidReading(batch.Summary) || batch.Receivers is null ||
            batch.Receivers.Count > MaxKeys)
            throw new InvalidDataException("Invalid routine worker inventory");
        if (batch.Summary.ReceiverPresent != (batch.Receivers.Count > 0) ||
            (!batch.Summary.PresenceKnown && batch.Receivers.Count != 0))
            throw new InvalidDataException("Inconsistent routine worker presence");

        HashSet<string> keys = new(StringComparer.Ordinal);
        foreach (var item in batch.Receivers)
        {
            if (item is null || item.Key == DeviceAliasRules.AulaSlot ||
                !DeviceAliasRules.ValidKey(item.Key) || !keys.Add(item.Key) ||
                !ValidReading(item.Reading) || !item.Reading.PresenceKnown ||
                !item.Reading.ReceiverPresent ||
                (item.Reading.UnverifiedPercent is not null && item.Revision != 2) ||
                (item.Sampled && item.MeasuredAt is null) ||
                (!item.Sampled && (item.MeasuredAt is not null ||
                    item.Reading.Percent is not null || item.Reading.UnverifiedPercent is not null || item.CompletedTick != 0)))
                throw new InvalidDataException("Invalid routine receiver observation");
        }
        var primary = AjazzHidReader.Primary(batch.Receivers)?.Reading;
        if (batch.Summary.Percent != primary?.Percent ||
            batch.Summary.UnverifiedPercent != primary?.UnverifiedPercent)
            throw new InvalidDataException("Inconsistent routine summary percentage");
    }

    internal static int RunWorker(string mode)
    {
        if (!Console.IsInputRedirected || !Console.IsOutputRedirected) return 1;
        using var watchdog = new System.Threading.Timer(_ => Environment.Exit(124),
            null, TimeSpan.FromSeconds(ChildLimitSeconds), Timeout.InfiniteTimeSpan);
        try
        {
            string? line = Console.ReadLine();
            if (line is null || line.Length > 10000) return 1;
            string[] deferred = ValidateKeys(JsonSerializer.Deserialize<string[]>(line));
            if (mode == HangMode) Thread.Sleep(Timeout.Infinite);
            using Stream output = Console.OpenStandardOutput();
            if (mode is ClockMode or ClockSampleMode)
            {
                if (deferred.Length != 0) return 1;
                bool sent = mode == ClockSampleMode ||
                    new AjazzHidReader().TrySyncDockClock(DateTime.Now);
                JsonSerializer.Serialize(output, sent);
            }
            else
            {
                AjazzHidReader.Batch batch = mode == SampleMode ? Sample(deferred) :
                    new AjazzHidReader().ReadAll(shouldSample: key => !deferred.Contains(key));
                JsonSerializer.Serialize(output, batch);
            }
            return 0;
        }
        catch (Exception) { return 1; }
    }

    private static AjazzHidReader.Batch Sample(string[] deferred)
    {
        string first = new('A', 64), second = new('B', 64);
        var skip = new AjazzHidReader.Reading(true, null, "Sampling not due");
        var unknown = new AjazzHidReader.Reading(true, null, "Synthetic unavailable");
        var valid = new AjazzHidReader.Reading(true, 83, "Synthetic only");
        var now = DateTimeOffset.UtcNow;
        var items = new[] { first, second }.Select(key => deferred.Contains(key)
            ? new AjazzHidReader.ReceiverReading(key, null, skip, Sampled: false)
            : new AjazzHidReader.ReceiverReading(key, 2, key == first ? valid : unknown,
                MeasuredAt: now, CompletedTick: Environment.TickCount64)).ToArray();
        return new AjazzHidReader.Batch(AjazzHidReader.Primary(items)!.Reading, items);
    }

    private static void VerifyReplyValidation()
    {
        var valid = Sample(Array.Empty<string>());
        ValidateBatch(valid);
        var first = valid.Receivers[0];
        var invalid = new[]
        {
            valid with { Summary = valid.Summary with { Percent = 0 } },
            valid with { Summary = valid.Summary with { Percent = 99 } },
            valid with { Summary = valid.Summary with { UnverifiedPercent = 100 } },
            valid with { Summary = valid.Summary with { Percent = null, UnverifiedPercent = 101 } },
            valid with { Summary = valid.Summary with { PresenceKnown = false } },
            valid with { Receivers = new[] { first, first } },
            valid with { Receivers = new[] { first with { Key = DeviceAliasRules.AulaSlot } } },
            valid with { Receivers = new[] { first with { MeasuredAt = null } } },
            valid with { Receivers = new[] { first with { Sampled = false } } },
            valid with { Receivers = new[] { first with { Reading = first.Reading with { Percent = 101 } } } },
            valid with { Receivers = new[] { first with { Reading = first.Reading with { ReceiverPresent = false } } } }
        };
        using var deadline = new CancellationTokenSource();
        foreach (var batch in invalid)
        {
            bool rejected = false;
            try { Decode<AjazzHidReader.Batch>(JsonSerializer.Serialize(batch), 0,
                    deadline, CancellationToken.None); }
            catch (InvalidDataException) { rejected = true; }
            if (!rejected) throw new InvalidDataException("Malformed routine reply accepted");
        }
    }

    private static async Task VerifyAsync()
    {
        VerifyReplyValidation();
        string first = new('A', 64), second = new('B', 64);
        var sample = await ReadAsync(new[] { second }, CancellationToken.None, SampleMode);
        if (sample.Summary.Percent != 83 || sample.Receivers.Count != 2 ||
            !sample.Receivers[0].Sampled || sample.Receivers[1].Sampled ||
            sample.Receivers[1].Reading.Percent is not null)
            throw new InvalidDataException("Deferred receiver round trip failed");

        Task<AjazzHidReader.Batch> blocked = ReadAsync(Array.Empty<string>(),
            CancellationToken.None, HangMode);
        bool rejected = false;
        try { await ReadAsync(new[] { first }, CancellationToken.None, SampleMode); }
        catch (InvalidOperationException) { rejected = true; }
        if (!rejected) throw new InvalidDataException("Concurrent worker not rejected");
        bool timedOut = false;
        try { await blocked; }
        catch (TimeoutException) { timedOut = true; }
        if (!timedOut) throw new InvalidDataException("Expected worker timeout");

        using var closing = new CancellationTokenSource(TimeSpan.FromMilliseconds(500));
        bool cancelled = false;
        try { await ReadAsync(Array.Empty<string>(), closing.Token, HangMode); }
        catch (OperationCanceledException) { cancelled = true; }
        if (!cancelled) throw new InvalidDataException("Expected cancellation");

        if (!await InvokeAsync<bool>(Array.Empty<string>(), CancellationToken.None, ClockSampleMode))
            throw new InvalidDataException("Synthetic clock result failed");

        var recovery = await ReadAsync(new[] { first }, CancellationToken.None, SampleMode);
        if (recovery.Receivers[0].Sampled || !recovery.Receivers[1].Sampled ||
            recovery.Summary.Percent is not null)
            throw new InvalidDataException("Recovery after timeout failed");
    }

    internal static int SelfTest()
    {
        try { VerifyAsync().GetAwaiter().GetResult(); return 0; }
        catch (Exception) { return 1; }
    }
}
