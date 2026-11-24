using System.Diagnostics;
using System.Text;
using System.Text.Json;

namespace AjazzBatteryTray;

/// <summary>Prototype for routine AJAZZ reads; not wired into the tray timer.</summary>
internal static class RoutinePollWorker
{
    private const string ReadMode = "--internal-routine-hid-worker";
    private const string SampleMode = "--internal-routine-hid-sample";
    private const string HangMode = "--internal-routine-hid-hang";
    private const int MaxKeys = 128;
    private const int ChildLimitSeconds = 12;
    private static int _active;

    internal static bool IsWorker(string mode) => mode is ReadMode or SampleMode or HangMode;

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

    internal static async Task<AjazzHidReader.Batch> ReadAsync(
        string[] deferred, CancellationToken closing, string mode = ReadMode)
    {
        ValidateKeys(deferred);
        closing.ThrowIfCancellationRequested();
        if (Interlocked.CompareExchange(ref _active, 1, 0) != 0)
            throw new InvalidOperationException("Routine HID worker already active");
        try { return await ExchangeAsync(deferred, closing, mode).ConfigureAwait(false); }
        finally { Volatile.Write(ref _active, 0); }
    }

    private static async Task<AjazzHidReader.Batch> ExchangeAsync(
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
            return Decode(await output.ConfigureAwait(false), child.ExitCode, deadline, closing);
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

    private static AjazzHidReader.Batch Decode(string body, int code,
        CancellationTokenSource deadline, CancellationToken closing)
    {
        closing.ThrowIfCancellationRequested();
        if (deadline.IsCancellationRequested || code == 124) throw new TimeoutException();
        if (code != 0) throw new IOException("Routine HID worker failed");
        return JsonSerializer.Deserialize<AjazzHidReader.Batch>(body)
            ?? throw new InvalidDataException("Missing routine worker response");
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
            AjazzHidReader.Batch batch = mode == SampleMode ? Sample(deferred) :
                new AjazzHidReader().ReadAll(shouldSample: key => !deferred.Contains(key));
            using Stream output = Console.OpenStandardOutput();
            JsonSerializer.Serialize(output, batch);
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

    private static async Task VerifyAsync()
    {
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
