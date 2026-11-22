using System.Text.Json;

namespace AjazzBatteryTray;

/// <summary>Portable global UI preferences only, not hardware settings or network consent.</summary>
public sealed record PreferencesBackup(
    int SchemaVersion, int PollSeconds, string Language, bool NotificationsEnabled,
    bool AlertBelow50, bool AlertBelow25, bool AlertBelow10, bool RecordBatteryHistory,
    bool NotifyOnDisconnect, bool MultipleTrayIcons)
{
    public const int Schema = 1;
    public const int MaximumBytes = 8192;
    private static readonly string[] Fields = {
        nameof(SchemaVersion), nameof(PollSeconds), nameof(Language), nameof(NotificationsEnabled),
        nameof(AlertBelow50), nameof(AlertBelow25), nameof(AlertBelow10), nameof(RecordBatteryHistory),
        nameof(NotifyOnDisconnect), nameof(MultipleTrayIcons)
    };

    public static PreferencesBackup Capture(AppSettings settings) => new(
        Schema, settings.PollSeconds, settings.Language, settings.NotificationsEnabled,
        settings.AlertBelow50, settings.AlertBelow25, settings.AlertBelow10,
        settings.RecordBatteryHistory, settings.NotifyOnDisconnect, settings.MultipleTrayIcons);

    public byte[] Export()
    {
        Validate();
        return JsonSerializer.SerializeToUtf8Bytes(this, new JsonSerializerOptions { WriteIndented = true });
    }

    public static PreferencesBackup Parse(ReadOnlyMemory<byte> data)
    {
        if (data.Length is <= 0 or > MaximumBytes)
            throw new InvalidDataException("Invalid backup size.");
        using var document = JsonDocument.Parse(data, new JsonDocumentOptions { MaxDepth = 4 });
        if (document.RootElement.ValueKind != JsonValueKind.Object)
            throw new InvalidDataException("Expected backup object.");
        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (var property in document.RootElement.EnumerateObject())
            if (!Fields.Contains(property.Name, StringComparer.Ordinal) || !seen.Add(property.Name))
                throw new InvalidDataException("Unknown or duplicate backup field.");
        if (seen.Count != Fields.Length)
            throw new InvalidDataException("Backup has missing fields.");
        var result = JsonSerializer.Deserialize<PreferencesBackup>(data.Span)
            ?? throw new InvalidDataException("Invalid backup.");
        result.Validate();
        return result;
    }

    private void Validate()
    {
        if (SchemaVersion != Schema || !DevicePollSchedule.IsValidInterval(PollSeconds) ||
            Language is not ("en" or "ru" or "uk"))
            throw new InvalidDataException("Unsupported backup version or preference value.");
    }

    /// <summary>Apply only the allowlisted fields; restore the previous values on save failure.</summary>
    public bool TryRestore(AppSettings settings, Func<bool> persist)
    {
        Validate();
        var previous = Capture(settings);
        Apply(settings);
        try
        {
            if (persist()) return true;
        }
        catch (Exception)
        {
            // Persistence failure must not leave the in-memory preferences changed.
        }
        previous.Apply(settings);
        return false;
    }

    private void Apply(AppSettings settings)
    {
        settings.PollSeconds = PollSeconds;
        settings.Language = Language;
        settings.NotificationsEnabled = NotificationsEnabled;
        settings.AlertBelow50 = AlertBelow50;
        settings.AlertBelow25 = AlertBelow25;
        settings.AlertBelow10 = AlertBelow10;
        settings.RecordBatteryHistory = RecordBatteryHistory;
        settings.NotifyOnDisconnect = NotifyOnDisconnect;
        settings.MultipleTrayIcons = MultipleTrayIcons;
    }

    public static PreferencesBackup ReadFile(string path)
    {
        using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
        if (stream.Length is <= 0 or > MaximumBytes)
            throw new InvalidDataException("Invalid backup file size.");
        var data = new byte[(int)stream.Length];
        stream.ReadExactly(data);
        return Parse(data);
    }

    public void WriteNewFile(string path)
    {
        byte[] data = Export();
        using var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        stream.Write(data);
    }
}
